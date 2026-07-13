# TRADE_DATABASE_SPEC

## 1. Finalidade da Tabela
A tabela `trades` é o catálogo unificado de todas as negociações de compra e venda de ativos (ações, FIIs, renda fixa, etc). Ela já engloba entradas manuais, notas de corretagem, importações MyProfit e deve englobar a nova ingestão da **Área do Investidor da B3 (CEI)**.

## 2. Estrutura Encontrada (Migration 004_investments.sql)
A tabela já foi criada previamente no projeto. Seu contrato atual é:

| Coluna | Tipo | Restrições | Motivo |
| :--- | :--- | :--- | :--- |
| `id` | `TEXT` | `PRIMARY KEY` | Identificador único universal (UUID ou Hash). |
| `broker_note_id` | `TEXT` | `REFERENCES broker_notes(id) ON DELETE SET NULL` | NULL para ingestões diretas da B3. |
| `asset_id` | `TEXT` | `NOT NULL REFERENCES assets(id)` | Vínculo obrigatório com o ticker. |
| `account_id` | `TEXT` | `NOT NULL REFERENCES accounts(id)` | Conta / Instituição financeira atrelada à negociação. |
| `type` | `TEXT` | `NOT NULL CHECK(type IN ('BUY','SELL'))` | Tipo de movimentação. |
| `trade_date` | `TEXT` | `NOT NULL` (ISO 8601) | Data da operação (`Data do Negócio` na B3). |
| `quantity` | `REAL` | `NOT NULL CHECK(quantity > 0)` | Quantidade negociada. |
| `unit_price` | `INTEGER` | `NOT NULL CHECK(unit_price >= 0)` | Preço unitário em centavos. |
| `gross_value` | `INTEGER` | `GENERATED ALWAYS (quantity * unit_price)` | Valor financeiro bruto. |
| `fees_allocated`| `INTEGER` | `NOT NULL DEFAULT 0` | Taxas. Zero para leitura cega do CEI. |
| `net_value` | `INTEGER` | `GENERATED ALWAYS` | Valor financeiro líquido (calculado pelo SQLite). |
| `source` | `TEXT` | `NOT NULL DEFAULT 'BROKER_NOTE' CHECK(source IN ('BROKER_NOTE','MANUAL','MYPROFIT_IMPORT','B3_API'))` | Origem do dado (usaremos `B3_API`). |
| `run_id` | `TEXT` | (Opcional) | ID da importação/auditoria. |
| `created_at` | `TEXT` | `NOT NULL DEFAULT now()` | Timestamp de criação. |

## 3. Índices e Uniques Existentes
- `idx_trades_asset` ON `trades(asset_id)`
- `idx_trades_account` ON `trades(account_id)`
- `idx_trades_date` ON `trades(trade_date)`
- `idx_trades_type` ON `trades(type)`

## 4. Consenso Arquitetural
A estrutura da tabela `trades` existente já contempla 100% dos requisitos mapeados para os eventos de negociação do `Exemplo_Negociacao_B3.xlsx`. O campo `source='B3_API'` já está perfeitamente previsto no `CHECK`.
