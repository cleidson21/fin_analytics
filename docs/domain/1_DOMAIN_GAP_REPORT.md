# Relatório de Lacunas do Domínio (Domain Gap Report)

Este documento analisa as lacunas do domínio financeiro atual do sistema, identificando entidades implícitas, informações perdidas na importação atual de fontes externas (Pierre e MyProfit) e tabelas necessárias para garantir a independência dessas plataformas.

## 1. Entidades que Existem Implicitamente

A partir da análise dos dados importados e dos extratos brutos (Nubank), as seguintes entidades já existem na realidade financeira, mas não estão modeladas adequadamente como primeira classe:

* **Conta (Account)**: Contas Correntes, Contas de Investimento, RDBs.
* **Transação (Transaction)**: Transferências (PIX), Pagamentos, Resgates, Aplicações.
* **Contraparte (Counterparty/Merchant)**: Quem envia ou recebe o dinheiro (ex: KAIZEN GAMING, Shopee, Pessoas Físicas no PIX).
* **Fatura de Cartão (Credit Card Invoice)**: O agrupamento mensal de despesas.
* **Item de Fatura (Invoice Item) & Parcelamento (Installment Plan)**: Despesas fracionadas (ex: Parcela 6/6, 3/3).
* **Ativo Financeiro (Asset)**: Ações, FIIs, Renda Fixa (Tesouro, RDB), BDRs, Cripto.
* **Nota de Corretagem (Broker Note)**: O documento oficial de liquidação na bolsa que agrupa várias negociações.
* **Negociação (Trade/Execution)**: A compra ou venda específica de um ativo em um momento no tempo com quantidade e preço.
* **Provento (Dividend/Corporate Action)**: Rendimentos, JCP, Amortizações recebidos por posse de ativos.
* **Snapshot de Posição (Asset Position Snapshot)**: O estado da carteira em um mês/dia específico.

## 2. Informações Perdidas na Importação Atual

Ao depender do Pierre e MyProfit, os seguintes dados valiosos não são capturados em sua granularidade original:

* **Taxas B3 e Corretagem**: O MyProfit consolida o "Total investido", ocultando o custo exato de emolumentos, taxa de liquidação e ISS presentes nas Notas de Corretagem.
* **Temporalidade Intradiária (Execution Time)**: O MyProfit agrupa compras do dia no preço médio, perdendo a granularidade da execução da ordem (Trade).
* **Vínculo Transação-Fatura**: No Pierre, o pagamento da fatura do Nubank aparece como um débito único. O detalhe granular do que compõe a fatura (os itens e parcelas) fica oculto.
* **Estrutura de Parcelamentos**: Transações como "Parcela 2/4" perdem o contexto de que pertencem a um plano de parcelamento (Installment Plan) maior, impedindo a projeção de fluxo de caixa futuro.
* **Identificadores Únicos Originais**: O UUID das transações do extrato original (ex: `6814f05f-...`) é perdido, dificultando conciliação idempotente.

## 3. Tabelas que Obrigatoriamente Precisam Existir

Para absorver o domínio completo, o banco de dados deve evoluir para conter as seguintes tabelas (Core):

**Banking & Cashflow**
* `accounts`, `institutions`
* `transactions` (Tabela imutável de fluxo de caixa)
* `categories`, `merchants`

**Credit Card**
* `credit_cards`, `invoices`, `invoice_items`
* `installment_plans`, `installments`

**Wealth & Investments**
* `assets`, `asset_prices` (Market Data)
* `broker_notes`, `trades`
* `corporate_actions` (Dividendos, Splits, Bonificações)
* `portfolio_snapshots` (Posição e rentabilidade histórica)

## 4. Tabelas Atuais Incorretas e Incompletas

Embora eu não tenha acesso direto ao DDL atual, baseando-me nos arquivos exportados, as prováveis abordagens atuais estão incorretas pois:

* **Tabelas "Flat" de Ativos**: Uma tabela que armazene "Ações" e "Preço Médio" como estado mutável está incorreta. O preço médio deve ser um **cálculo derivado** do histórico de `trades`, e não uma coluna estática.
* **Tabelas de "Evolução"**: Inserir manualmente a evolução (IBOV, CDI) está incorreto. A evolução deve ser calculada on-the-fly ou por snapshots diários automatizados cruzando saldo de cotas vs `yfinance`.
* **Tabelas de Extrato (Entrada/Saída)**: Separar entradas e saídas em lógicas diferentes ou usar descrições "sujas" como chave de categorização.

## 5. Informações Exclusivas: Pierre x MyProfit x Banco

### O que o Pierre possui que o banco não armazena?
* **Categoria Normalizada**: O banco (Nubank) envia apenas a descrição crua da maquininha ou contraparte do PIX. O Pierre possui o mapeamento semântico (ex: "Lj Cacau Show" -> "Supermercado/Alimentação").
* **Merchant Normalizado**: Limpeza de caracteres especiais e códigos de adquirentes ("Shopee *Lumilojaoficia 5/10" -> "Shopee").

### O que o MyProfit possui que o banco não armazena?
* **Cálculos de Rentabilidade e Patrimônio**: Preço médio, Lucro/Prejuízo, YOC, Dividend Yield, % da Carteira, Benchmark (CDI, IBOV, IFIX, S&P 500) acumulado.
* **Histórico Consolidado de Proventos**: Agrupamento de dividendos recebidos no tempo contra a posição acionária.

### O que o Banco/Corretora possui que Pierre/MyProfit ignoram?
* Extratos crus com UUIDs idempotentes.
* Detalhe completo das Notas de Corretagem em PDF (incluindo número da nota, taxas da CBLC e corretagem, impostos IRRF retidos na fonte).
* Detalhamento de Faturas de Cartão de Crédito em CSV.

## 6. Cálculos do MyProfit e Reprodução Interna

**O MyProfit realiza os seguintes cálculos:**
* **Posição Atual**: Qtd * Preço Atual
* **Total Investido (Preço Médio)**: Soma (Qtd * Preço Compra + Custos) / Qtd Total
* **Ganho Absoluto e %**: Posição Atual - Total Investido
* **YOC (Yield on Cost)**: Dividendos Anualizados / Preço Médio de Aquisição
* **DY (Dividend Yield)**: Dividendos Anualizados / Preço Atual
* **Evolução Acumulada da Carteira e Benchmarks**: TWR (Time-Weighted Return).

**Poderiam ser reproduzidos internamente?**
**SIM. 100% reproduzíveis.**
Com acesso ao `yfinance` para histórico de cotações, e processando internamente as Notas de Corretagem (para formar o preço médio real), todos esses cálculos podem ser feitos em backend Python/Pandas ou via SQL Aggregations. O sistema será auto-suficiente.

## 7. Dependências Externas que Podem ser Eliminadas

1. **Pierre**: Pode ser eliminado substituindo-o por um pipeline interno de normalização (Regex -> Regras de Negócio -> Embeddings -> LLM Fallback).
2. **MyProfit**: Pode ser eliminado importando diretamente as Notas de Corretagem (parse de PDF ou importação de CSV da B3) e calculando o preço médio e rentabilidade no backend com cotações do `yfinance`.
