# 3. Pipelines de Importação e Motores Analíticos

Este documento cobre as **Etapas 4, 5 e 6** e os **Entregáveis 6 e 7** do FinAnalytics V3.

---

## 1. O Pipeline de Importação Definitivo

A arquitetura orientada a eventos obriga que a ingestão de dados seja assíncrona, robusta e idempotente. 

### 1.1 Ingestão Bancária (Nubank Ledger)
1. **Source**: Extrato CSV (NU_...) ou OFX.
2. **Fingerprint**: Criação de Hash SHA-256 combinando `(Data, Valor, Descrição Original)` para servir como `Transaction.id`. Impede duplicação.
3. **Normalização**: Roda o Motor de Classificação (veja Seção 2) sobre a `Descrição Original`.
4. **Conciliação**: Verifica se a transação faz par com outra para formar um `Transfer` (ex: Saída do Nubank e Entrada na NuInvest no mesmo dia e valor).
5. **Commit**: Grava em `TRANSACTIONS`.

### 1.2 Ingestão de Crédito (Cartão)
1. **Source**: CSV da Fatura.
2. **Identificação da Fatura**: Verifica o `closing_date` e cria/atualiza a `INVOICE`.
3. **Detecção de Parcelas**: Se a string contiver regex `Parcela (\d+)/(\d+)`, busca um `INSTALLMENT_PLAN` associado ao valor total e Merchant. Se não existir, projeta retroativamente as parcelas.
4. **Commit**: Associa as linhas como `INVOICE_ITEMS`.

### 1.3 Ingestão de Corretagem (B3 / Broker Notes)
1. **Source**: PDFs das Notas de Negociação ou API B3.
2. **Extração Base**: Salva a "Capa" da nota em `BROKER_NOTES` (data, número da nota, soma das taxas de liquidação e corretagem).
3. **Extração de Linhas**: Para cada ação comprada/vendida, cria um `TRADE` lincado à nota.
4. **Trigger do Motor Financeiro**: O novo `TRADE` notifica a `Position Engine` para reprocessar o Preço Médio a partir daquela data.

---

## 2. O Motor de Classificação de IA (Classification Engine)

Para libertar o sistema do Pierre, o motor processa as strings cruas em um pipeline estilo *Chain of Responsibility*.

1. **Camada 1: Regex Engine**
   * Avalia a tabela `classification_rules` ordenada por prioridade.
   * Se casar (ex: `(?i)Transferência enviada pelo Pix - (.*)`), resolve e encerra.
2. **Camada 2: Merchant Exact Match**
   * Faz `SELECT id FROM merchants WHERE normalized_name = CLEAN(string)`.
3. **Camada 3: Embeddings Vector Search (pgvector)**
   * Transforma a string crua em vetor.
   * Roda similaridade de cosseno contra `learning_examples.embedding`. Se similaridade > 0.90, classifica e encerra.
4. **Camada 4: LLM Zero-Shot (GPT-4o-mini / Claude 3 Haiku)**
   * Envia a string para API LLM.
   * *Feedback Loop*: O retorno do LLM é automaticamente salvo na tabela `learning_examples` e `classification_rules` para que **o LLM nunca seja chamado para a mesma string duas vezes**, reduzindo o custo da API para zero no longo prazo.
5. **Fallback**: Categoria genérica "A Classificar".

---

## 3. O Motor Financeiro Definitivo (Financial Engine)

O coração do V3 é o recalculo sob demanda. Nenhuma média é salva crua sem base factual. O motor lê os `TRADES` e `CORPORATE_ACTIONS` cronologicamente.

### 3.1 Preço Médio de Aquisição (Cost Basis Engine)
Para uma ação (ex: BBAS3):
1. Pega saldo anterior = 0, PM = 0.
2. Dia 1: Compra 10 cotas @ R$ 20. Taxas Rateadas = R$ 1. 
   * `PM = ((10*20)+1)/10 = 20,10`
3. Dia 2: Compra 5 cotas @ R$ 30. Taxas Rateadas = R$ 1.
   * `PM = ((10*20,10) + (5*30)+1) / 15 = 23,46`
4. Dia 3: Vende 5 cotas. PM **não muda**. Apenas baixa a Qtd para 10. *Gera Ganho de Capital realizado.*

### 3.2 TWR (Time-Weighted Return)
Avalia a habilidade da carteira, ignorando saques e aportes. Tratado como cota de fundo:
* `Cota inicial = R$ 1,00`
* Todo dia, `Variação % Carteira = (Total Hoje - Aportes Hoje + Saques Hoje) / Total Ontem - 1`.
* `Cota Hoje = Cota Ontem * (1 + Variação % Carteira)`.

### 3.3 MWR (Money-Weighted Return / TIR)
Avalia se o tempo dos aportes foi bom (TIR - Taxa Interna de Retorno).
* Fórmula do Excel (XIRR) rodando nos fluxos de `TRADES` e saldo atual.

### 3.4 Métricas Avançadas
* **Alpha**: `Retorno_Anualizado_Carteira - Retorno_Anualizado_IBOV`.
* **Beta**: `Cov(Diários_Carteira, Diários_IBOV) / Var(Diários_IBOV)`.
* **Sharpe**: `(Retorno_Carteira - Selic) / Desvio_Padrão_Diário_Anualizado`.
* **Sortino**: Mesma fórmula do Sharpe, mas usando o *Downside Deviation* (apenas a volatilidade de retornos negativos). Punições de alta não contam contra a carteira.
* **Max Drawdown**: A maior queda percentual entre um pico histórico e o fundo subsequente. `Min(P_t / P_max - 1)`.

### 3.5 Rendimentos (DY e YOC)
* **Dividend Yield**: `Soma(Dividends de 12m) / (Qtd_Atual * Preço_Fechamento_Ontem_yfinance)`.
* **Yield On Cost**: `Soma(Dividends de 12m) / (Qtd_Atual * Preço_Médio_Engine)`.

### Atualização e Armazenamento
Os cálculos pesados (TWR, Sharpe, Beta) não rodam ao abrir o app. Eles são empacotados por um **CRON Job noturno** que insere uma linha em `portfolio_snapshots` contendo todas essas métricas materializadas, garantindo que a consulta da dashboard retorne em < 50ms.
