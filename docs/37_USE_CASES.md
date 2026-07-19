> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Use Cases — FIN Analytics

Todos os casos de uso da camada Application. Cada UC orquestra entidades do domínio e providers via Ports — nunca diretamente.

---

## UC-01: AuthenticateUser

**Objetivo:** Autenticar um usuário com email/senha e retornar tokens JWT.

| | |
|---|---|
| **Entrada** | `email: str`, `password: str` |
| **Saída** | `AuthTokenDTO` (access_token, refresh_token, expires_in) |
| **Pré-condições** | Usuário cadastrado e ativo (`is_active=True`, `is_verified=True`) |
| **Pós-condições** | `last_login_at` atualizado. Refresh token persistido. |
| **Entidades** | User |
| **Ports** | UserRepository, Clock, Secrets |
| **Eventos produzidos** | — |



---

## UC-03: RefreshToken

**Objetivo:** Renovar o access token usando o refresh token.

| | |
|---|---|
| **Entrada** | `refresh_token: str` |
| **Saída** | `AuthTokenDTO` |
| **Pré-condições** | Refresh token válido e não expirado |
| **Pós-condições** | Novo access token gerado. Refresh token rotacionado. |
| **Entidades** | User |
| **Ports** | UserRepository, Secrets, Clock |

---

## UC-04: SyncPierreAccounts

**Objetivo:** Buscar todas as contas financeiras do usuário via Pierre e sincronizar com o domínio.

| | |
|---|---|
| **Entrada** | `SyncPierreCommand` (user_id) |
| **Saída** | `SyncResultDTO` (created, updated, skipped, errors) |
| **Pré-condições** | Provider Pierre ACTIVE. API Key válida. |
| **Pós-condições** | Accounts criadas/atualizadas. Institutions criadas/referenciadas. `last_sync_at` atualizado. |
| **Entidades** | Account, Institution, Provider |
| **Ports** | AccountRepository, InstitutionRepository, ProviderRepository, PierreProvider, Clock |
| **Eventos produzidos** | `SyncStarted`, `SyncFinished` ou `SyncFailed` |

---

## UC-05: SyncPierreTransactions

**Objetivo:** Buscar transações do Pierre para todas as contas ativas e sincronizar.

| | |
|---|---|
| **Entrada** | `SyncPierreCommand` (user_id, date_range opcional) |
| **Saída** | `SyncResultDTO` |
| **Pré-condições** | Accounts sincronizadas (UC-04). Provider ACTIVE. |
| **Pós-condições** | Transactions criadas (sem duplicatas via hash). Categories mapeadas ou marcadas para classificação. |
| **Entidades** | Transaction, Account, Category, Provider |
| **Ports** | TransactionRepository, AccountRepository, CategoryRepository, ProviderRepository, PierreProvider, Clock |
| **Eventos produzidos** | `TransactionImported`, `SyncStarted`, `SyncFinished` |

---

## UC-06: SyncMyProfitPortfolio

**Objetivo:** Extrair posições e dividendos do MyProfit e sincronizar a carteira.

| | |
|---|---|
| **Entrada** | `SyncMyProfitCommand` (user_id) |
| **Saída** | `SyncResultDTO` |
| **Pré-condições** | Provider MyProfit ACTIVE. Sessão válida (cookies). |
| **Pós-condições** | Assets criados. Positions (snapshots) criadas. Dividends criados. |
| **Entidades** | Asset, Position, Dividend, Portfolio, Provider |
| **Ports** | AssetRepository, PositionRepository, DividendRepository, PortfolioRepository, ProviderRepository, MyProfitProvider, Clock |
| **Eventos produzidos** | `PortfolioUpdated`, `DividendReceived`, `SyncStarted`, `SyncFinished` |

---

## UC-07: SyncYFinanceQuotes

**Objetivo:** Atualizar cotações atuais dos ativos da carteira via YFinance.

| | |
|---|---|
| **Entrada** | `RefreshQuotesCommand` (user_id, tickers opcional) |
| **Saída** | `SyncResultDTO` |
| **Pré-condições** | Assets existentes com ticker. Mercado aberto (opcional). |
| **Pós-condições** | `Position.current_price` e `current_value` atualizados. |
| **Entidades** | Asset, Position |
| **Ports** | AssetRepository, PositionRepository, YFinanceProvider, Clock |
| **Eventos produzidos** | `PortfolioUpdated` |

---

## UC-08: ImportCSV

**Objetivo:** Importar transações ou dividendos via arquivo CSV enviado pelo usuário.

| | |
|---|---|
| **Entrada** | `ImportCsvCommand` (user_id, file_bytes, csv_type) |
| **Saída** | `ImportResultDTO` (total, imported, skipped, errors, preview) |
| **Pré-condições** | Arquivo válido. Encoding detectável. Headers reconhecíveis. |
| **Pós-condições** | Transactions ou Dividends criados com `provider=CSV`. Hash deduplicação aplicado. |
| **Entidades** | Transaction, Dividend, Category, Account |
| **Ports** | TransactionRepository, DividendRepository, AccountRepository, CategoryRepository, Clock |
| **Eventos produzidos** | `TransactionImported` ou `DividendReceived` |

---

## UC-09: ClassifyTransaction

**Objetivo:** Classificar automaticamente transações sem categoria via IA.

| | |
|---|---|
| **Entrada** | `ClassifyTransactionCommand` (transaction_ids lista, ou "all unclassified") |
| **Saída** | `ClassificationResultDTO` (classified, failed, suggestions) |
| **Pré-condições** | Transações com `category_id=NULL`. GeminiProvider configurado. |
| **Pós-condições** | `category_id` preenchido nas transactions classificadas. |
| **Entidades** | Transaction, Category |
| **Ports** | TransactionRepository, CategoryRepository, GeminiProvider |
| **Eventos produzidos** | `CategoryClassified` |

---

## UC-10: GetDashboard

**Objetivo:** Gerar visão consolidada financeira para a tela principal.

| | |
|---|---|
| **Entrada** | `GetDashboardQuery` (user_id, period, currency) |
| **Saída** | `DashboardDTO` |
| **Pré-condições** | Dados sincronizados |
| **Entidades** | Account, Transaction, Position, Dividend |
| **Ports** | AccountRepository, TransactionRepository, PositionRepository, DividendRepository, Cache |

---

## UC-11: GetTransactions

**Objetivo:** Listar transações com filtros, paginação e ordenação.

| | |
|---|---|
| **Entrada** | `GetTransactionsQuery` |
| **Saída** | `PaginatedResponseDTO<TransactionResponseDTO>` |
| **Entidades** | Transaction, Category, Account |
| **Ports** | TransactionRepository |

---

## UC-12: GetPortfolio

**Objetivo:** Retornar a visão atual da carteira de investimentos do usuário.

| | |
|---|---|
| **Entrada** | `GetPortfolioQuery` (user_id, portfolio_id opcional) |
| **Saída** | `PortfolioResponseDTO` |
| **Entidades** | Position, Asset, Portfolio, Dividend |
| **Ports** | PositionRepository, AssetRepository, DividendRepository |

---

## UC-13: GetCashFlow

**Objetivo:** Calcular fluxo de caixa (receitas vs despesas) por período.

| | |
|---|---|
| **Entrada** | `GetCashFlowQuery` (user_id, date_range, groupBy) |
| **Saída** | `CashFlowDTO` |
| **Entidades** | Transaction, Account |
| **Ports** | TransactionRepository |

---

## UC-14: GenerateInsights

**Objetivo:** Gerar análises e recomendações personalizadas via IA.

| | |
|---|---|
| **Entrada** | `GenerateInsightsCommand` (user_id, context) |
| **Saída** | `InsightDTO` |
| **Pré-condições** | Dados financeiros disponíveis. GeminiProvider configurado. |
| **Entidades** | Transaction, Position, Dividend, Account |
| **Ports** | TransactionRepository, PositionRepository, GeminiProvider |
| **Eventos produzidos** | `InsightGenerated` |

---

## UC-15: GetAlerts

**Objetivo:** Listar alertas ativos (spending limits, payment reminders, etc.)

| | |
|---|---|
| **Entrada** | `GetAlertsQuery` (user_id) |
| **Saída** | `list[AlertDTO]` |
| **Entidades** | Transaction (para spending limits) |
| **Ports** | TransactionRepository, Cache |

---

## UC-16: ConnectProvider

**Objetivo:** Ativar a conexão de um Provider para o usuário.

| | |
|---|---|
| **Entrada** | `ConnectProviderCommand` (user_id, provider_type, config) |
| **Saída** | `ProviderResponseDTO` |
| **Pós-condições** | Provider criado com `status=PENDING`. Teste de conexão disparado. |
| **Entidades** | Provider |
| **Ports** | ProviderRepository, PierreProvider / MyProfitProvider (para teste) |

---

## UC-17: DisconnectProvider

**Objetivo:** Desativar e opcionalmente apagar dados de um Provider.

| | |
|---|---|
| **Entrada** | `DisconnectProviderCommand` (user_id, provider_id, delete_data) |
| **Saída** | `OperationResultDTO` |
| **Pós-condições** | Provider `status=INACTIVE`. Dados apagados (soft delete) se `delete_data=True`. |
| **Entidades** | Provider, Account, Transaction (soft delete) |
| **Eventos produzidos** | `ProviderDisconnected` |

---

## UC-18: GetDividends

| **Entrada** | `GetDividendsQuery` |
| **Saída** | `PaginatedResponseDTO<DividendResponseDTO>` |
| **Entidades** | Dividend, Asset, Portfolio |
| **Ports** | DividendRepository |

---

## UC-19: UpdateCategory

| **Entrada** | `UpdateCategoryCommand` (transaction_id, category_id, user_id) |
| **Saída** | `TransactionResponseDTO` |
| **Entidades** | Transaction, Category |
| **Ports** | TransactionRepository, CategoryRepository |
| **Eventos produzidos** | `CategoryClassified` |

---

## UC-20: BackupDatabase

| **Entrada** | `BackupDatabaseCommand` (user_id, destination) |
| **Saída** | `BackupResultDTO` |
| **Ports** | Storage, Clock, Logger |
| **Eventos produzidos** | `BackupCreated` |
