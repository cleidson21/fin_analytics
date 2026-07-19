> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Queries — FIN Analytics

Queries representam intenções de leitura. Sempre somente-leitura. Nunca mutam estado.

---

## GetDashboardQuery

**Descrição:** Dados consolidados para a tela principal.

| Filtro | Tipo | Default | Descrição |
|---|---|---|---|
| `user_id` | UUID | obrigatório | |
| `period` | DateRange | últimos 30 dias | |
| `currency` | CurrencyCode | `BRL` | Moeda de consolidação |

**Retorno:** `DashboardDTO`
- saldo total por conta
- despesas do período
- receitas do período
- top 5 categorias de gasto
- variação do portfólio (%)
- dividendos do período
- alertas ativos

---

## GetTransactionsQuery

**Descrição:** Lista paginada de transações com filtros compostos.

| Filtro | Tipo | Default | Descrição |
|---|---|---|---|
| `user_id` | UUID | obrigatório | |
| `start_date` | date | — | |
| `end_date` | date | — | |
| `account_ids` | list[UUID] | — | Filtrar por contas |
| `category_ids` | list[UUID] | — | |
| `provider` | ProviderType | — | |
| `type` | TransactionType | — | |
| `direction` | MovementType | — | CREDIT/DEBIT |
| `min_amount` | Decimal | — | |
| `max_amount` | Decimal | — | |
| `search` | string | — | Busca em `description` |
| `is_recurring` | boolean | — | |
| `has_category` | boolean | — | |
| `page` | integer | 1 | |
| `page_size` | integer | 20 | Max 100 |
| `order_by` | string | `transaction_date` | |
| `order_dir` | string | `desc` | asc/desc |

**Retorno:** `PaginatedResponseDTO<TransactionResponseDTO>`

---

## GetPortfolioQuery

**Descrição:** Visão atual da carteira de investimentos.

| Filtro | Tipo | Default | Descrição |
|---|---|---|---|
| `user_id` | UUID | obrigatório | |
| `portfolio_id` | UUID | — | Se vazio, retorna todos |
| `asset_type` | AssetType | — | Filtrar por tipo |
| `include_zeroed` | boolean | false | Incluir posições zeradas |

**Retorno:** `PortfolioResponseDTO`
- total investido
- valor atual
- ganho/perda absoluto e percentual
- lista de posições por ativo
- alocação por tipo (%)

---

## GetDividendsQuery

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `asset_id` | UUID | — |
| `year` | integer | — |
| `type` | IncomeType | — |
| `page` | integer | 1 |
| `page_size` | integer | 20 |
| `order_by` | string | `ex_date` |
| `order_dir` | string | `desc` |

**Retorno:** `PaginatedResponseDTO<DividendResponseDTO>`

---

## GetCashFlowQuery

**Descrição:** Fluxo de caixa (receitas vs despesas) por período e agrupamento.

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `start_date` | date | início do mês |
| `end_date` | date | hoje |
| `group_by` | string | `month` (day/week/month/year) |
| `account_ids` | list[UUID] | — |
| `include_investment` | boolean | false |

**Retorno:** `CashFlowDTO` (lista de períodos com income, expense, net)

---

## GetAccountsQuery

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `type` | AccountType | — |
| `is_active` | boolean | true |
| `provider` | ProviderType | — |

**Retorno:** `list[AccountResponseDTO]`

---

## GetAlertsQuery

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `type` | string | — (spending_limit, payment_reminder) |
| `active_only` | boolean | true |

**Retorno:** `list[AlertDTO]`

---

## GetProvidersQuery

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `status` | ProviderStatus | — |

**Retorno:** `list[ProviderResponseDTO]`

---

## GetInsightsQuery

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `period` | DateRange | últimos 30 dias |
| `limit` | integer | 5 |

**Retorno:** `list[InsightDTO]`

---

## GetAssetHistoryQuery

**Descrição:** Histórico de preços de um ativo.

| Filtro | Tipo | Default |
|---|---|---|
| `ticker` | Ticker | obrigatório |
| `start_date` | date | 1 ano atrás |
| `end_date` | date | hoje |
| `interval` | string | `1d` (1d/1w/1mo) |

**Retorno:** `AssetHistoryDTO` (lista de OHLCV)

---

## GetCategoriesQuery

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `include_system` | boolean | true |
| `include_user` | boolean | true |

**Retorno:** `list[CategoryResponseDTO]` (hierárquico)

---

## Regras Gerais de Queries

1. Queries **nunca mutam estado**.
2. Resultados podem ser cacheados (TTL configurável por query).
3. Toda query retorna DTO — nunca entidade de domínio diretamente.
4. Paginação padrão: `page + page_size`. Retornar sempre `total`, `page`, `page_size`, `has_next`.
5. `order_by` aceita apenas campos declarados nos DTOs — nunca SQL bruto.
