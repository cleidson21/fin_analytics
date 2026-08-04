> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela.

<<<<<<< HEAD
> [!CAUTION]
> **DOCUMENTO OBSOLETO — V3.1**
> As entidades de domínio definidas aqui foram construídas sob premissas inválidas (UUIDs artificiais, hashes, purchase_id calculado, category_id como FK).
> A modelagem oficial vigente está em `60_ARCHITECTURE_REVISION_V31.md`, seção 6.
> Este arquivo é mantido apenas como referência histórica. Não implementar.

# Domínio Canônico — FIN Analytics (OBSOLETO)
=======
# Domínio Canônico — FIN Analytics
>>>>>>> 021d439dcbb06040c0005dbd27456a26c9f1d7e9

## Propósito
Este documento define o **Domínio Canônico completo** do FIN Analytics. É o único contrato que o sistema conhece internamente. Pierre, MyProfit, CSV, YFinance e Manual são apenas adaptadores externos — todos devem converter seus dados para este domínio antes de entrar no sistema.

---

## Revisão Pré-Sprint: Inconsistências Encontradas

| Documento Antigo | Problema |
|---|---|
| `11_INTEGRATIONS.md` | Afirmava que Pierre possui Webhooks e Investimentos — **FALSO** conforme OpenAPI real |
| `12_CANONICAL_MODEL.md` | Não documentava `Tag`, `User`, `Currency`, `SpendingLimit` |
| `02_DOMAIN_MODEL.md` | Muito vago — sem campos, tipos ou regras |
| `21_PROVIDER_MODELS.md` | Schemas gerados sem campos (todos "Nenhum campo documentado") |

Todos corrigidos nesta Sprint. `11_INTEGRATIONS.md` atualizado via `ADR-009`.

---

## Entidades Canônicas

### 1. Transaction

**Finalidade:** Representa qualquer movimentação financeira — débito, crédito, parcelamento, transferência — ocorrida em qualquer conta conectada.

| Campo | Tipo | Obrigatório | Nullable | Descrição | Exemplo |
|---|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | Identificador interno gerado pelo FIN Analytics | `a1b2c3d4-...` |
| `external_id` | string | ❌ | ✅ | ID original do Provider. Nunca sobrescrever. | `txn_abc123` |
| `provider` | ProviderType | ✅ | ❌ | Qual Provider originou esta transação | `PIERRE` |
| `account_id` | UUID (FK Account) | ✅ | ❌ | Conta à qual esta transação pertence | |
| `amount` | Decimal(12,2) | ✅ | ❌ | Valor absoluto da transação | `150.00` |
| `direction` | MovementType | ✅ | ❌ | CREDIT ou DEBIT | `DEBIT` |
| `currency_code` | CurrencyCode | ✅ | ❌ | Código ISO 4217 | `BRL` |
| `description` | string | ✅ | ❌ | Descrição legível da transação | `Netflix` |
| `original_description` | string | ❌ | ✅ | Descrição bruta do banco, sem tratamento | |
| `category_id` | UUID (FK Category) | ❌ | ✅ | Categoria atribuída | |
| `type` | TransactionType | ✅ | ❌ | PURCHASE, TRANSFER, INCOME, etc. | `PURCHASE` |
| `status` | TransactionStatus | ✅ | ❌ | PENDING, CONFIRMED, CANCELLED | `CONFIRMED` |
| `transaction_date` | date | ✅ | ❌ | Data real da transação | `2024-07-01` |
| `posted_date` | date | ❌ | ✅ | Data em que apareceu no extrato | |
| `is_recurring` | boolean | ✅ | ❌ | Indica assinatura ou débito fixo | `false` |
| `purchase_id` | UUID | ❌ | ✅ | ID para agrupamento de parcelas (Installments) | `b2c3d4e5-...` |
| `installment_count` | integer | ❌ | ✅ | Total de parcelas (se parcelado) | `12` |
| `installment_current` | integer | ❌ | ✅ | Parcela atual | `3` |
| `tags` | list[Tag] | ❌ | ✅ | Etiquetas do usuário | |
| `provider_metadata` | JSON | ❌ | ✅ | Dados adicionais do Provider não mapeáveis | |
| `hash` | string | ✅ | ❌ | SHA256 para deduplicação | |
| `created_at` | datetime | ✅ | ❌ | Gerado internamente | |
| `updated_at` | datetime | ✅ | ❌ | Gerado internamente | |
| `deleted_at` | datetime | ❌ | ✅ | Soft delete | |

**Regras:**
- `id` é sempre gerado internamente (UUID v4).
- `hash` é calculado a partir de `external_id + provider + transaction_date + amount`. Usado para deduplicação.
- Transações **nunca são apagadas fisicamente** — apenas `deleted_at` é preenchido.
- `amount` sempre positivo. `direction` define o sentido.
- `purchase_id` deve ser gerado pelo sistema para agrupar todas as parcelas (transaction_date diferentes) de uma mesma compra parcelada.
- **Invariantes:** Se `installment_count` > 0, então `installment_current` é obrigatório e `installment_current <= installment_count`. Se `is_recurring == True`, normalmente a transação não possui `installment_count`.

---

### 2. Account

**Finalidade:** Representa qualquer conta financeira — corrente, poupança, cartão de crédito, investimento, carteira digital.

| Campo | Tipo | Obrigatório | Nullable | Descrição | Exemplo |
|---|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | Identificador interno | |
| `external_id` | string | ❌ | ✅ | ID no Provider | `acc_123456789` |
| `provider` | ProviderType | ✅ | ❌ | Provider de origem | `PIERRE` |
| `institution_id` | UUID (FK Institution) | ❌ | ✅ | Instituição financeira | |
| `name` | string | ✅ | ❌ | Nome amigável | `Nubank Conta` |
| `type` | AccountType | ✅ | ❌ | BANK, CREDIT_CARD, INVESTMENT, LOAN, WALLET | `BANK` |
| `subtype` | string | ❌ | ✅ | Detalhe de tipo (ex: CHECKING_ACCOUNT) | |
| `currency_code` | CurrencyCode | ✅ | ❌ | Moeda principal | `BRL` |
| `balance` | Decimal(12,2) | ❌ | ✅ | Saldo atual (snapshot) | `1500.50` |
| `balance_updated_at` | datetime | ❌ | ✅ | Quando o saldo foi atualizado | |
| `is_active` | boolean | ✅ | ❌ | Conta ativa ou arquivada | `true` |
| `provider_code` | string | ❌ | ✅ | Código banco/provedor (ex: NUBANK) | |
| `provider_metadata` | JSON | ❌ | ✅ | Dados extras do Provider | |
| `created_at` | datetime | ✅ | ❌ | | |
| `updated_at` | datetime | ✅ | ❌ | | |

---

### 3. Asset

**Finalidade:** Representa qualquer ativo financeiro — ação, FII, ETF, CDB, Tesouro, cripto, fundo.

| Campo | Tipo | Obrigatório | Nullable | Descrição | Exemplo |
|---|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | Identificador interno | |
| `ticker` | Ticker | ✅ | ❌ | Símbolo do ativo | `PETR4` |
| `name` | string | ✅ | ❌ | Nome completo | `Petrobras PN` |
| `type` | AssetType | ✅ | ❌ | STOCK, FII, ETF, BOND, CRYPTO, FUND, OTHER | `STOCK` |
| `currency_code` | CurrencyCode | ✅ | ❌ | Moeda de negociação | `BRL` |
| `isin` | string | ❌ | ✅ | Código ISIN internacional | |
| `cnpj` | string | ❌ | ✅ | CNPJ do fundo/ativo | |
| `exchange` | string | ❌ | ✅ | Bolsa de valores | `B3` |
| `sector` | string | ❌ | ✅ | Setor econômico | `Petróleo` |
| `provider_metadata` | JSON | ❌ | ✅ | Dados extras (YFinance, B3) | |
| `created_at` | datetime | ✅ | ❌ | | |
| `updated_at` | datetime | ✅ | ❌ | | |

**Origem:** MyProfit (scraping B3), YFinance (preços), CSV (importação manual).
**Pierre não possui Asset.**

---

### 4. Position

**Finalidade:** Representa a posição atual de um ativo na carteira de um usuário em um dado momento.

| Campo | Tipo | Obrigatório | Nullable | Descrição | Exemplo |
|---|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | | |
| `asset_id` | UUID (FK Asset) | ✅ | ❌ | Ativo em questão | |
| `portfolio_id` | UUID (FK Portfolio) | ✅ | ❌ | Carteira | |
| `quantity` | Decimal(12,6) | ✅ | ❌ | Quantidade de cotas/ações | `100.000` |
| `avg_cost` | Decimal(12,4) | ✅ | ❌ | Preço médio de compra | `28.50` |
| `current_price` | Decimal(12,4) | ❌ | ✅ | Preço atual (snapshot) | `32.10` |
| `current_value` | Decimal(12,2) | ❌ | ✅ | Valor total atual | `3210.00` |
| `total_invested` | Decimal(12,2) | ✅ | ❌ | Total investido historicamente | `2850.00` |
| `gain_loss` | Decimal(12,2) | ❌ | ✅ | P&L absoluto | `360.00` |
| `gain_loss_pct` | Decimal(8,4) | ❌ | ✅ | P&L percentual | `12.63` |
| `provider` | ProviderType | ✅ | ❌ | Quem informou esta posição | `MYPROFIT` |
| `snapshot_date` | date | ✅ | ❌ | Data de referência | `2024-07-01` |
| `created_at` | datetime | ✅ | ❌ | | |
| `updated_at` | datetime | ✅ | ❌ | | |

---

### 5. Portfolio

**Finalidade:** Agrupamento lógico de posições. Um usuário pode ter múltiplas carteiras (ex: BR, EUA, cripto).

| Campo | Tipo | Obrigatório | Nullable | Descrição |
|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | |
| `user_id` | UUID (FK User) | ✅ | ❌ | |
| `name` | string | ✅ | ❌ | Ex: "Carteira Brasil" |
| `description` | string | ❌ | ✅ | |
| `currency_code` | CurrencyCode | ✅ | ❌ | Moeda base |
| `is_active` | boolean | ✅ | ❌ | |
| `created_at` | datetime | ✅ | ❌ | |
| `updated_at` | datetime | ✅ | ❌ | |

---

### 6. Dividend

**Finalidade:** Representa proventos distribuídos por ativos — dividendos, JCP, aluguéis de FII.

| Campo | Tipo | Obrigatório | Nullable | Descrição | Exemplo |
|---|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | | |
| `asset_id` | UUID (FK Asset) | ✅ | ❌ | | |
| `portfolio_id` | UUID (FK Portfolio) | ✅ | ❌ | | |
| `type` | IncomeType | ✅ | ❌ | DIVIDEND, JCP, RENT, INTEREST | `DIVIDEND` |
| `amount_per_unit` | Decimal(12,6) | ✅ | ❌ | Valor por cota | `0.45` |
| `quantity` | Decimal(12,6) | ✅ | ❌ | Quantidade de cotas na data-com | `100` |
| `gross_amount` | Decimal(12,2) | ✅ | ❌ | Total bruto | `45.00` |
| `net_amount` | Decimal(12,2) | ❌ | ✅ | Total líquido pós IR | `38.25` |
| `ir_withheld` | Decimal(12,2) | ❌ | ✅ | IR retido na fonte | `6.75` |
| `ex_date` | date | ✅ | ❌ | Data-com | `2024-06-28` |
| `payment_date` | date | ❌ | ✅ | Data de pagamento | `2024-07-15` |
| `currency_code` | CurrencyCode | ✅ | ❌ | | `BRL` |
| `provider` | ProviderType | ✅ | ❌ | | `MYPROFIT` |
| `external_id` | string | ❌ | ✅ | ID original no Provider | |
| `created_at` | datetime | ✅ | ❌ | | |

---

### 7. Institution

**Finalidade:** Banco, corretora, fintech ou emissora que origina contas ou ativos.

| Campo | Tipo | Obrigatório | Nullable | Descrição | Exemplo |
|---|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | | |
| `name` | string | ✅ | ❌ | Nome oficial | `Nubank` |
| `code` | string | ✅ | ❌ | Código identificador | `NUBANK` |
| `type` | string | ❌ | ✅ | BANK, BROKER, FINTECH | `BANK` |
| `country` | string | ✅ | ❌ | ISO 3166-1 alpha-2 | `BR` |
| `logo_url` | string | ❌ | ✅ | | |
| `created_at` | datetime | ✅ | ❌ | | |

---

### 8. Category

**Finalidade:** Classificação das transações (alimentação, transporte, lazer, etc.)

| Campo | Tipo | Obrigatório | Nullable | Descrição |
|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | |
| `name` | string | ✅ | ❌ | Nome exibido |
| `slug` | string | ✅ | ❌ | Identificador único (ex: `food`) |
| `parent_id` | UUID (FK Category) | ❌ | ✅ | Categoria pai (hierarquia) |
| `icon` | string | ❌ | ✅ | Emoji ou ícone |
| `color` | string | ❌ | ✅ | Cor HEX |
| `is_system` | boolean | ✅ | ❌ | Se é padrão do sistema ou criada pelo usuário |
| `created_at` | datetime | ✅ | ❌ | |

---

### 9. Currency

**Finalidade:** Tabela de moedas suportadas.

| Campo | Tipo | Obrigatório | Nullable | Descrição |
|---|---|---|---|---|
| `code` | CurrencyCode (PK) | ✅ | ❌ | ISO 4217 (BRL, USD, EUR) |
| `name` | string | ✅ | ❌ | Nome completo |
| `symbol` | string | ✅ | ❌ | Símbolo (R$, $) |
| `decimal_places` | integer | ✅ | ❌ | Casas decimais padrão |

---

### 10. Tag

**Finalidade:** Etiqueta livre definida pelo usuário para organizar transações.

| Campo | Tipo | Obrigatório | Nullable | Descrição |
|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | |
| `user_id` | UUID (FK User) | ✅ | ❌ | |
| `name` | string | ✅ | ❌ | |
| `color` | string | ❌ | ✅ | HEX |
| `created_at` | datetime | ✅ | ❌ | |

---

### 11. User

**Finalidade:** Representa o usuário autenticado no sistema.

| Campo | Tipo | Obrigatório | Nullable | Descrição |
|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | |
| `email` | string | ✅ | ❌ | Único |
| `name` | string | ✅ | ❌ | |
| `hashed_password` | string | ✅ | ❌ | bcrypt |
| `is_active` | boolean | ✅ | ❌ | |
| `is_verified` | boolean | ✅ | ❌ | |
| `role` | UserRole | ✅ | ❌ | ADMIN, VIEWER |
| `created_at` | datetime | ✅ | ❌ | |
| `last_login_at` | datetime | ❌ | ✅ | |

---

### 12. Provider

**Finalidade:** Representa a conexão de um usuário a um Provider externo.

| Campo | Tipo | Obrigatório | Nullable | Descrição |
|---|---|---|---|---|
| `id` | UUID | ✅ | ❌ | |
| `user_id` | UUID (FK User) | ✅ | ❌ | |
| `type` | ProviderType | ✅ | ❌ | PIERRE, MYPROFIT, CSV, YFINANCE, MANUAL |
| `status` | ProviderStatus | ✅ | ❌ | ACTIVE, INACTIVE, ERROR, PENDING |
| `last_sync_at` | datetime | ❌ | ✅ | |
| `sync_status` | SyncStatus | ❌ | ✅ | IDLE, RUNNING, SUCCESS, FAILED |
| `config` | JSON | ❌ | ✅ | Configuração específica (sem credenciais) |
| `error_message` | string | ❌ | ✅ | Último erro de sincronização |
| `created_at` | datetime | ✅ | ❌ | |
| `updated_at` | datetime | ✅ | ❌ | |

> **NUNCA** armazenar API Keys, senhas ou tokens no campo `config`. Usar `.env` e secrets manager.
