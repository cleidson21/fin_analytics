# Modelo Definitivo do Domínio Financeiro (Final Domain Model V3)

Este documento representa a fundação arquitetônica de dados para o FinAnalytics V3. Projetado para suportar os próximos 10 anos de operação sem legados, ignorando dependências de serviços terceiros (Pierre/MyProfit), garantindo um Ledger puro e cálculos dinâmicos de investimentos.

---

## Arquitetura em Diagrama de Domínio (Mermaid)

```mermaid
erDiagram
    %% CORE IDENTITIES %%
    USER ||--o{ ACCOUNT : owns
    INSTITUTION ||--o{ ACCOUNT : hosts
    ACCOUNT {
        uuid id PK
        string name
        enum type "CHECKING | BROKERAGE | CREDIT"
        uuid institution_id FK
    }

    %% CASHFLOW (LEDGER) %%
    ACCOUNT ||--o{ TRANSACTION : registers
    CATEGORY ||--o{ TRANSACTION : categorizes
    MERCHANT ||--o{ TRANSACTION : processed_by
    TRANSACTION {
        uuid id PK
        date date
        decimal amount
        string original_description
        enum type "IN | OUT"
        uuid category_id FK
        uuid merchant_id FK
        uuid internal_transfer_id "Self-reference"
    }

    %% CREDIT CARD %%
    ACCOUNT ||--o{ CREDIT_CARD : linked_to
    CREDIT_CARD ||--o{ INVOICE : generates
    INVOICE ||--o{ INVOICE_ITEM : contains
    INSTALLMENT_PLAN ||--o{ INSTALLMENT : splits_into
    INSTALLMENT_PLAN ||--o{ INVOICE_ITEM : maps_to
    
    INVOICE {
        uuid id PK
        date due_date
        date closing_date
        decimal total_amount
        enum status "OPEN | CLOSED | PAID"
    }
    
    INVOICE_ITEM {
        uuid id PK
        string description
        decimal amount
        date date
        uuid installment_id FK
        uuid merchant_id FK
    }

    %% INVESTMENTS & WEALTH %%
    ASSET {
        uuid id PK
        string ticker
        enum asset_class "STOCK | FII | BDR | RDB | CRYPTO"
        string sector
    }

    BROKER_NOTE {
        uuid id PK
        uuid account_id FK
        date note_date
        string note_number
        decimal total_brokerage_fee
        decimal total_b3_fees
        decimal taxes
    }

    TRADE {
        uuid id PK
        uuid broker_note_id FK
        uuid asset_id FK
        enum type "BUY | SELL"
        int quantity
        decimal unit_price
        decimal total_trade_value
    }

    CORPORATE_ACTION {
        uuid id PK
        uuid asset_id FK
        date ex_date
        enum type "SPLIT | REVERSE_SPLIT | BONUS"
        decimal ratio
    }

    DIVIDEND {
        uuid id PK
        uuid asset_id FK
        date ex_date
        date payment_date
        decimal value_per_share
        decimal total_amount
        enum type "DIVIDEND | JCP | AMORTIZATION"
    }

    BROKER_NOTE ||--o{ TRADE : groups
    ASSET ||--o{ TRADE : traded_as
    ASSET ||--o{ CORPORATE_ACTION : suffers
    ASSET ||--o{ DIVIDEND : yields
```

---

## Descrição dos Contextos Delimitados (Bounded Contexts)

### 1. Contexto de Ledger (Core Finance)
Garante a integridade financeira por meio da imutabilidade.
* A entidade `TRANSACTION` é o coração do sistema. Representa qualquer saída ou entrada de dinheiro na conta `CHECKING`.
* As tabelas `MERCHANT` e `CATEGORY` pertencem a um sub-motor de IA/Classificação que limpa e entende dados automaticamente no momento da ingestão (via webhook, OFX ou CSV do banco), matando a necessidade do "Pierre".
* O campo `internal_transfer_id` anula contabilidade duplicada quando o usuário transfere da conta Nubank para a conta NuInvest. O saldo patrimonial geral não é afetado.

### 2. Contexto de Crédito (Credit Management)
Lida com dinheiro tomado emprestado.
* O cartão gera faturas mensais (`INVOICE`).
* Compras geram despesas pontuais (`INVOICE_ITEM`).
* Compras parceladas geram um `INSTALLMENT_PLAN`, que se desdobra em N `INSTALLMENTS`, alocados inteligentemente em `INVOICES` futuras, permitindo previsibilidade total do passivo financeiro em D+30, D+60.

### 3. Contexto de Mercado (Wealth Trading & Asset)
Garante exatidão matemática do imposto de renda e rentabilidade real, matando o MyProfit.
* Trabalha 100% com dados puros da B3: A `BROKER_NOTE` (Nota de Corretagem) registra o "Ato da Negociação", contendo a matemática das taxas macro.
* O `TRADE` guarda o detalhe (Comprei 10 VALE3 a R$ 70). O backend usa essas duas tabelas, aliadas as `CORPORATE_ACTIONS`, para construir as tabelas agregadas e visões (Materialized Views) do **Preço Médio** no decorrer do tempo.
* O componente de `yfinance` agirá externamente como um serviço, preenchendo as tabelas de `MARKET_DATA` que não foram diagramadas acima por serem *Time Series* acopladas diretamente à tabela `ASSET`.

## Princípios de Ouro do Domínio V3
1. **Nada de Saldos Estáticos Corrigidos a Mão:** Saldos de banco e médias de preço são **derivados** de um somatório imutável de eventos (`Transations` e `Trades`).
2. **Total Independência (Zero Vendor Lock-in):** A abstração está a nível de liquidação B3 e Extrato Brasileiro. O sistema será imune à descontinuidade de plataformas como MyProfit, StatusInvest, Trademap ou Pierre.
3. **Auditabilidade Total:** Uma transação será rastreável desde a nota de corretagem em PDF original até a cota de rentabilidade TWR no dashboard final.
