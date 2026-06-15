# 1. Domínio Definitivo & Bounded Contexts

Este documento detalha o resultado da **Etapa 1 (Auditoria)** e **Etapa 2 (Domínio Definitivo)** da reconstrução FinAnalytics V3.

---

## 1. Auditoria Final dos Documentos

Após cruzar os documentos iniciais com a base de dados em `arquivos_base`, os seguintes conflitos e redundâncias foram resolvidos:
* **Conflito**: O MyProfit mistura conceito de "Proventos" (dividendos em dinheiro) com "Desdobramentos" (eventos corporativos) no mesmo cálculo de rentabilidade de forma opaca.
  * **Resolução**: Separação estrita. `DIVIDENDS` gera fluxo de caixa/retorno, `CORPORATE_ACTIONS` altera histórico de cotas. São entidades distintas.
* **Redundância**: Nubank envia pagamentos de fatura como débito e os itens da fatura também em CSV separado. Se ambos entrarem na conta corrente, o gasto dobra.
  * **Resolução**: A transação de pagamento no `Ledger` (Cashflow) liquida uma `Invoice` (Credit). Os `Invoice Items` não são fluxo de caixa direto, pertencem à fatura.
* **Inconsistência**: Pierre agrupa sub-categorias de forma rasa.
  * **Resolução**: Introdução da entidade hierárquica `CATEGORY`, permitindo agregações de Analytics sem sujar a taxonomia.

---

## 2. Bounded Contexts Definitivos

A arquitetura do FinAnalytics V3 é dividida nos seguintes contextos delimitados (Bounded Contexts), garantindo baixo acoplamento e alta coesão:

### 2.1 Identity & Access
* **Responsabilidade**: Gerenciar quem acessa o sistema e o escopo multi-tenant.
* **Entidades**: `User`, `Tenant`, `Role`, `Session`.

### 2.2 Banking & Institutions
* **Responsabilidade**: Cadastro de fontes pagadoras/recebedoras e contas físicas.
* **Entidades**: `Institution` (Nubank, B3, XP), `Account` (Corrente, Corretora, Cartão).

### 2.3 Cashflow (Ledger)
* **Responsabilidade**: Livro razão imutável. Registro de onde o dinheiro veio e para onde foi.
* **Entidades**: `Transaction`, `Transfer` (ponte entre transações), `Category`, `Merchant`.
* **Regra Ouro**: Event Sourcing. Errou? Cria-se transação compensatória.

### 2.4 Credit Management
* **Responsabilidade**: Lidar com antecipação de consumo e passivos (cartões).
* **Entidades**: `Credit_Card`, `Invoice` (fatura mensal), `Invoice_Item`, `Installment_Plan` (a compra macro), `Installment` (a parcela).

### 2.5 Investments (Wealth)
* **Responsabilidade**: Lidar com a posse de ativos e registros de liquidação da bolsa.
* **Entidades**: `Asset`, `Broker_Note` (Nota de Corretagem), `Trade` (Ordem executada), `Corporate_Action`, `Dividend`.

### 2.6 Market Data
* **Responsabilidade**: Dados externos não pertencentes ao usuário, importados do mercado para precificação.
* **Entidades**: `Asset_Price` (time series do yfinance), `Benchmark_Price` (CDI, IBOV).

### 2.7 Governance & Compliance
* **Responsabilidade**: Rastreabilidade técnica do sistema. Quem alterou, qual arquivo gerou os dados, logs de erro.
* **Entidades**: `Import_Run`, `Import_Artifact` (O arquivo raw do Nubank/B3), `Audit_Log`, `Data_Correction`.

### 2.8 AI & Classification Engine
* **Responsabilidade**: Classificação semântica automática, processamento NLP de strings cruas.
* **Entidades**: `Classification_Rule` (Regex/Match exato), `Learning_Example` (Base vetorial para Embeddings), `AI_Prompt`, `AI_Run` (histórico de inferências), `Classification_Feedback` (quando usuário corrige a IA).

### 2.9 Analytics & Snapshots
* **Responsabilidade**: Visualizações de alta performance. Agregações para BI e gráficos.
* **Entidades**: `Asset_Position` (A posição consolidada agora), `Portfolio_Snapshot` (Fechamento do dia/mês), `Benchmark_Snapshot`.
