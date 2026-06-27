# DATA SOURCES CATALOG & RECONCILIATION MATRIX

Este documento estabelece o mapeamento absoluto de todas as fontes de dados (inputs) aceitas pelo FinAnalytics V3, derivado exclusivamente da análise física dos arquivos de amostra (`samples/`). Nenhuma outra fonte fictícia foi considerada.

---

## 1. INVENTÁRIO DAS FONTES (DATA SOURCES)

### 1.1 Exemplo_Ativos_Myprofit.csv
* **Origem:** Agregador MyProfit
* **Instituição:** Múltiplas (Consolidado)
* **Formato:** CSV Tabular
* **Tipo:** Posição de Carteira (Snapshot)
* **Periodicidade:** Sob demanda
* **Emissão parcial:** Não (representa a carteira global no instante).
* **Emissão repetida:** Sim, para a mesma data.
* **Chave Natural:** Ativo + Data Base (implícita do momento de extração).
* **Grau de confiabilidade:** Alto (porém derivado do input prévio).
* **Informações Exclusivas:** Preço Médio consolidado, Ganho (R$ e %), % Patrimônio.
* **Informações Redundantes:** Quantidade (em relação à B3).
* **Possíveis Cruzamentos:** B3 Ativos (para auditar saldo real), Notas de Negociação (para auditar Preço Médio).
* **Limitações:** Não provê fluxo histórico transacional da compra do ativo.

### 1.2 Exemplo_Evolucao_carteira_Myprofit.csv
* **Origem:** Agregador MyProfit
* **Formato:** CSV Tabular
* **Tipo:** Snapshot de Rentabilidade (Evolução)
* **Periodicidade:** Mensal
* **Emissão repetida:** Sim.
* **Chave Natural:** Mês/Ano (ex: Out-2022).
* **Grau de confiabilidade:** Médio (Cálculo derivado).
* **Informações Exclusivas:** Benchmark (IBOV Mensal, CDI, IPCA), Compras/Vendas agregadas por mês.
* **Limitações:** Valores agregados; sem granularidade de ativos específicos.

### 1.3 Exemplo_Proventos_Myprofit.csv
* **Origem:** Agregador MyProfit
* **Formato:** CSV Tabular
* **Tipo:** Transacional (Dividendos/JCP)
* **Periodicidade:** Mensal/Sob demanda
* **Chave Natural:** Ativo + Data pgto + Valor
* **Grau de confiabilidade:** Alto.
* **Informações Exclusivas:** Data COM, Yield on Cost (YOC), Dividend Yield (DY).
* **Possíveis Cruzamentos:** Extrato Conta Corrente (para conciliar o recebimento efetivo).

### 1.4 Exemplo_Extrato_Conta_Nubank.csv
* **Origem:** Banco (Nubank)
* **Formato:** CSV Tabular
* **Tipo:** Transacional (Conta Corrente)
* **Periodicidade:** Customizável (Mensal/Diário)
* **Chave Natural:** `Identificador` (UUID único, ex: `6814f05f-3836-454f...`)
* **Grau de confiabilidade:** Oficial (Absoluto).
* **Informações Exclusivas:** Saldo em espécie, PIX efetivos, UUID da transação.
* **Cruzamentos:** O centro da reconciliação. Cruza com Pierre, Pagamentos de Fatura, Depósitos de Proventos e Custos de Corretagem.

### 1.5 Exemplo_Extrato_Fatura_Nubank.csv
* **Origem:** Administradora de Cartão (Nubank)
* **Formato:** CSV Tabular
* **Tipo:** Transacional (Crédito)
* **Periodicidade:** Fechamento de Fatura (Mensal)
* **Chave Natural:** Data + Descrição + Valor (sem UUID nativo forte no CSV exportado).
* **Grau de confiabilidade:** Oficial (Absoluto).
* **Cruzamentos:** Consolidado Pierre; Pagamento via Extrato da Conta.

### 1.6 Exemplo_Ativos_B3.csv
* **Origem:** Área do Investidor (B3)
* **Formato:** XLSX (Identificado incorretamente pela extensão original como CSV).
* **Tipo:** Posição de Custódia (Snapshot)
* **Chave Natural:** Ativo + Instituição + Data
* **Grau de confiabilidade:** Oficial (Custódia Absoluta).
* **Informações Exclusivas:** Quantidade liquidada na bolsa.
* **Cruzamentos:** MyProfit (para reconciliar saldo em custódia vs saldo teórico).

### 1.7 Exemplo_Extrato_Pierre.txt
* **Origem:** App Pierre (Gestor de finanças)
* **Formato:** TXT visualmente tabular
* **Tipo:** Transacional classificado.
* **Chave Natural:** Data + Valor + Conta + Descrição (alta suscetibilidade a colisão).
* **Grau de confiabilidade:** Médio (Heurística de terceiro).
* **Informações Exclusivas:** Categoria humana (ex: "Alimentação", "Transporte").
* **Limitações:** Estrutura frágil para ingestão; necessitará de regex avançado para parse.
* **Cruzamentos:** Extratos do Nubank (Conta e Fatura).

### 1.8 Exemplo_Nota_Negociacao_Nubank.pdf
* **Origem:** Corretora
* **Formato:** PDF
* **Tipo:** Transacional (Mercado de Capitais)
* **Chave Natural:** Número da Nota + Data do Pregão + Corretora
* **Grau de confiabilidade:** Oficial (Absoluto).
* **Informações Exclusivas:** Emolumentos, Taxa de Liquidação, Preço de Execução unitário exato.
* **Cruzamentos:** Extrato Nubank (Saída financeira D+2) e MyProfit Ativos (Atualização do Preço Médio).

---

## 2. CLASSIFICAÇÃO DAS FONTES

### Bancária
* Extrato Conta Nubank
* Extrato Pierre

### Cartão
* Extrato Fatura Nubank

### Investimentos
* Ativos MyProfit
* Evolução Carteira MyProfit
* Proventos MyProfit
* Ativos B3

### OCR / Não-Tabulares
* Nota de Negociação Nubank (PDF)
* Extrato Pierre (TXT Visual)

---

## 3. MATRIZ DE CONFIABILIDADE E PRECEDÊNCIA

Quando duas fontes afirmam dados divergentes, a matriz abaixo define quem vence o conflito (Source of Truth):

| Fonte | Nível de Confiabilidade | Papel / Escopo | Risco de Duplicidade / Sobrescrita |
|---|---|---|---|
| **Nota de Negociação (B3/Corretora)** | ★★★★★ | Financeiro Oficial | Nenhuma (É a origem do universo de investimentos. Nunca deve ser sobrescrita). |
| **Ativos B3** | ★★★★★ | Custódia Oficial | Pode ser importada repetidas vezes; reflete apenas o estado atual (snapshot). Vence em litígio de saldo. |
| **Extrato Conta Nubank** | ★★★★★ | Financeiro Oficial | Baseado em UUID forte. Não duplica se o ID for mapeado. Vence litígios financeiros. |
| **Extrato Fatura Nubank** | ★★★★★ | Financeiro Oficial | Risco médio de duplicação pela ausência de UUID (reconciliar por Data+Valor). |
| **Proventos MyProfit** | ★★★★☆ | Agregador (Informativo) | Alta fidelidade, mas não substitui a confirmação do depósito na Conta Nubank. |
| **Ativos MyProfit** | ★★★★☆ | Agregador (Informativo) | Suscetível a erros humanos prévios no input da plataforma deles. |
| **Evolução MyProfit** | ★★★☆☆ | Agregador (Informativo) | Puramente estatístico/comparativo. |
| **Extrato Pierre** | ★★★☆☆ | Heurístico | Auxílio em classificação. Perde conflito para o Nubank caso a transação divirja. |

---

## 4. MATRIZ DE DUPLICIDADE (RECONCILIAÇÃO)

Documentos que cobrem o mesmo evento em estágios diferentes:

### 4.1 Ciclo de Compras/Despesas
1. Extrato de Fatura Nubank (Lançamento do gasto individual).
2. Extrato Pierre (Mesmo gasto, com a categoria associada).
3. Extrato Conta Nubank (O pagamento total consolidado da fatura no fim do mês).

### 4.2 Ciclo de Investimentos (Ações/FIIs)
1. Nota de Negociação (Ato da compra na Bolsa).
2. Extrato Conta Nubank (O débito na conta em D+2 correspondente à nota).
3. Ativos B3 e Ativos MyProfit (A quantidade em custódia que aumentou em decorrência do passo 1).
4. Extrato Pierre (Vê o débito da conta do passo 2 e marca como "Investimentos").

### 4.3 Ciclo de Proventos
1. Proventos MyProfit (Anúncio do JCP/Dividendo e Data Ex).
2. Extrato Conta Nubank (Depósito efetivo em espécie do provento no D+0).
3. Extrato Pierre (Enxerga o crédito e classifica como "Rendimentos").

**Diretriz de Reconciliação:** O sistema deverá processar a *Origem Oficial* primeiro, e quando ingerir o *Pierre*, apenas usá-lo para "enriquecer" (UPDATE na coluna categoria) os registros já consolidados, sem gerar duplicatas.

---

## 5. MATRIZ DE DEPENDÊNCIAS

Ordem lógica ideal de processamento de importações:
1. **Conta Corrente e Faturas:** Alimentam as engrenagens básicas (`transactions`, `invoices`, `credit_cards`).
2. **Notas de Corretagem:** Alimentam os ledgers de investimentos.
3. **Pierre:** Aplicado **por último** como enriquecedor de dados sobre os hashes do passo 1.
4. **MyProfit e B3:** Aplicados para conciliação de saldos e dashboards comparativos.

---

## 6. MATRIZ DE APRENDIZADO DA IA

### 6.1 Como a IA substituirá agregadores de terceiros:
**Uso do Pierre como Training Set (Professor):**
O *Extrato Pierre* fornece a categorização que o usuário já aprovou no passado (Target) em contrapartida às strings enigmáticas do *Extrato Conta Nubank* (Feature).
* *Exemplo de Treino:* Feature `Transferência enviada pelo Pix - Maria...` -> Target `Categoria: Alimentação`.
Quando o Pierre for desativado, o modelo da OpenAI carregará esse peso.

**Correções Contínuas (Feedback Loop):**
* IA sugere: Categoria `Alimentação`
* Usuário altera no UI: Para `Saúde` (em um evento de emergência).
* A Engine de Governança deve capturar esse PUT no `transactions` e engatilhar um Fine-Tuning/Embedding.

---

## 7. GOVERNANÇA E RISCOS IDENTIFICADOS

* **Risco - Encoding B3:** O arquivo do B3 é nomeado como `.csv`, mas a análise binária atesta ser um Zip/XLSX (`[Content_Types].xml`). Requererá parse `openpyxl` ou equivalente.
* **Risco - Fragilidade Pierre:** Arquivo posicional txt visual (`💰`). Um eventual erro de espaçamento pode deslocar arrays na conversão.
* **Oportunidade - Nubank UUIDs:** O extrato do Nubank possui coluna `Identificador` com UUIDs nativos, isso facilita 100% a proteção contra duplicidades. Em importações recorrentes, deve ser adotado como `id` absoluto ou via coluna `external_uuid`.
