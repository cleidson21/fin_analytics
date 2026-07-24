> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Queries — FIN Analytics

Queries representam intenções de leitura. Sempre somente-leitura. Nunca mutam estado.

Cada Query possui obrigatoriamente: Use Case Handler correspondente e Endpoint REST.

---

## GetAccountsQuery → UC-11A / GET /accounts

**Descrição:** Lista contas financeiras ativas do usuário.

| Filtro | Tipo | Default | Descrição |
|---|---|---|---|
| `user_id` | UUID | obrigatório | |
| `type` | AccountType | — | BANK, CREDIT_CARD, INVESTMENT, LOAN, WALLET |
| `is_active` | boolean | true | |
| `provider` | ProviderType | — | |

**Retorno:** `list[AccountResponseDTO]`

---

## GetCategoriesSummaryQuery → UC-11B / GET /dashboard/categories

**Descrição:** Lista hierárquica/soma de despesas por categoria no mês (Projeção a partir de transações).

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `month` | string | mês atual (YYYY-MM) |

**Retorno:** `list[CategoryBreakdownDTO]`

---

## GetTransactionsQuery → UC-11 / GET /transactions

**Descrição:** Lista paginada de transações com filtros compostos.

| Filtro | Tipo | Default | Descrição |
|---|---|---|---|
| `user_id` | UUID | obrigatório | |
| `start_date` | date | — | |
| `end_date` | date | — | |
| `account_ids` | list[UUID] | — | Filtrar por contas |
| `category_ids` | list[UUID] | — | |
| `provider` | ProviderType | — | |
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

## GetPortfolioQuery → UC-12 / GET /portfolio

**Descrição:** Visão atual da carteira de investimentos.

| Filtro | Tipo | Default | Descrição |
|---|---|---|---|
| `user_id` | UUID | obrigatório | |
| `portfolio_id` | UUID | — | Se vazio, retorna todos |
| `asset_type` | AssetType | — | Filtrar por tipo |
| `include_zeroed` | boolean | false | Incluir posições zeradas |

**Retorno:** `PortfolioResponseDTO`

---

## GetDividendsQuery → UC-18 / GET /dividends

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

## GetDashboardQuery → UC-10 / GET /dashboard

**Descrição:** Dados consolidados para a tela principal.

| Filtro | Tipo | Default | Descrição |
|---|---|---|---|
| `user_id` | UUID | obrigatório | |
| `period` | DateRange | últimos 30 dias | |
| `currency` | CurrencyCode | `BRL` | Moeda de consolidação |

**Retorno:** `DashboardDTO`

---

## GetCashFlowQuery → UC-13 / GET /cashflow

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

## GetAlertsQuery → UC-15 / GET /alerts

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `type` | string | — (spending_limit, payment_reminder) |
| `active_only` | boolean | true |

**Retorno:** `list[AlertDTO]`

---

## GetProvidersQuery → GET /providers

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `status` | ProviderStatus | — |

**Retorno:** `list[ProviderResponseDTO]`

---

## GetInsightsQuery → UC-14 / GET /insights

| Filtro | Tipo | Default |
|---|---|---|
| `user_id` | UUID | obrigatório |
| `period` | DateRange | últimos 30 dias |
| `limit` | integer | 5 |

**Retorno:** `list[InsightDTO]`

---

## GetAssetHistoryQuery → (Fase futura)

**Descrição:** Histórico de preços de um ativo.

| Filtro | Tipo | Default |
|---|---|---|
| `ticker` | Ticker | obrigatório |
| `start_date` | date | 1 ano atrás |
| `end_date` | date | hoje |
| `interval` | string | `1d` (1d/1w/1mo) |

**Retorno:** `AssetHistoryDTO` (lista de OHLCV)

---

## Matriz Query → Handler → Endpoint → Fase

| Query | UC Handler | Endpoint | Fase |
|---|---|---|---|
| GetAccountsQuery | UC-11A | GET /accounts | 2 |
| GetCategoriesSummaryQuery | UC-11B | GET /dashboard/categories | 3 |
| GetTransactionsQuery | UC-11 | GET /transactions | 3 |
| GetPortfolioQuery | UC-12 | GET /portfolio | 6 |
| GetDividendsQuery | UC-18 | GET /dividends | 6 |
| GetDashboardQuery | UC-10 | GET /dashboard | 10 |
| GetCashFlowQuery | UC-13 | GET /cashflow | 10 |
| GetAlertsQuery | UC-15 | GET /alerts | 10 |
| GetProvidersQuery | — | GET /providers | 5 |
| GetInsightsQuery | UC-14 | GET /insights | 9 |

---

## Regras Gerais de Queries

1. Queries **nunca mutam estado**.
2. Resultados podem ser cacheados (TTL configurável por query).
3. Toda query retorna DTO — nunca entidade de domínio diretamente.
4. Paginação padrão: `page + page_size`. Retornar sempre `total`, `page`, `page_size`, `has_next`.
5. `order_by` aceita apenas campos declarados nos DTOs — nunca SQL bruto.
6. Toda Query possui um UC Handler correspondente documentado em `37_USE_CASES.md`.
