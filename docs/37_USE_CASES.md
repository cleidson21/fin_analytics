> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Use Cases — FIN Analytics

Todos os casos de uso da camada Application. Cada UC orquestra entidades do domínio e providers via Ports — nunca diretamente.

Cada UC possui obrigatoriamente: Endpoint REST correspondente, Command ou Query tipada, e DTO de resposta.

---

## UC-01: AuthenticateUser ✅ IMPLEMENTADO

**Objetivo:** Autenticar um usuário com email/senha e retornar tokens JWT.

| | |
|---|---|
| **Entrada** | `AuthenticateUserCommand` (email, password) |
| **Saída** | `AuthTokenDTO` (access_token, refresh_token, token_type, expires_in, user) |
| **Endpoint** | `POST /auth/login` |
| **Pré-condições** | Usuário cadastrado e ativo (`is_active=True`) |
| **Pós-condições** | `last_login_at` atualizado. |
| **Entidades** | User |
| **Ports** | UserRepository, IPasswordHasher, IJWTService |
| **Eventos produzidos** | — |

---

## UC-03: RefreshToken 🔲 Não Iniciado

**Objetivo:** Renovar o access token usando o refresh token.

| | |
|---|---|
| **Entrada** | `RefreshTokenCommand` (refresh_token) |
| **Saída** | `AuthTokenDTO` |
| **Endpoint** | `POST /auth/refresh` |
| **Pré-condições** | Refresh token válido e não expirado |
| **Pós-condições** | Novo access token gerado. |
| **Entidades** | User |
| **Ports** | UserRepository, IJWTService, IClock |

---

## UC-11A: GetAccounts 🔲 Não Iniciado

**Objetivo:** Listar as contas financeiras do usuário autenticado.

| | |
|---|---|
| **Entrada** | `GetAccountsQuery` (user_id, type?, is_active?, provider?) |
| **Saída** | `list[AccountResponseDTO]` |
| **Endpoint** | `GET /accounts` |
| **Pré-condições** | Usuário autenticado (JWT) |
| **Entidades** | Account, Institution |
| **Ports** | AccountRepository |

---

## UC-11B: GetCategoriesSummary 🔲 Não Iniciado

**Objetivo:** Agrupar despesas por categoria em um período de tempo (Projeção analítica para a tela Categorias).

| | |
|---|---|
| **Entrada** | `GetCategoriesSummaryQuery` (user_id, month?) |
| **Saída** | `list[CategoryBreakdownDTO]` (category, total) |
| **Endpoint** | `GET /dashboard/categories` |
| **Pré-condições** | Usuário autenticado (JWT) |
| **Entidades** | Transaction, Category |
| **Ports** | TransactionRepository |

---

## UC-11: GetTransactions 🔲 Não Iniciado

**Objetivo:** Listar transações com filtros, paginação e ordenação.

| | |
|---|---|
| **Entrada** | `GetTransactionsQuery` (user_id, start_date?, end_date?, account_ids?, category_ids?, provider?, direction?, min_amount?, max_amount?, search?, page, page_size) |
| **Saída** | `PaginatedResponseDTO<TransactionResponseDTO>` |
| **Endpoint** | `GET /transactions` |
| **Entidades** | Transaction, Category, Account |
| **Ports** | TransactionRepository |

---

## UC-19: UpdateCategory 🔲 Não Iniciado

**Objetivo:** Atribuir manualmente uma categoria a uma transação.

| | |
|---|---|
| **Entrada** | `UpdateCategoryCommand` (user_id, transaction_id, category_id) |
| **Saída** | `TransactionResponseDTO` |
| **Endpoint** | `PATCH /transactions/{id}/category` |
| **Entidades** | Transaction, Category |
| **Ports** | TransactionRepository, CategoryRepository |
| **Eventos produzidos** | `CategoryClassified` |

---

## UC-16: ConnectProvider 🔲 Não Iniciado

**Objetivo:** Ativar a conexão de um Provider para o usuário.

| | |
|---|---|
| **Entrada** | `ConnectProviderCommand` (user_id, provider_type, config) |
| **Saída** | `ProviderResponseDTO` |
| **Endpoint** | `POST /providers/connect` |
| **Pós-condições** | Provider criado com `status=PENDING`. Teste de conexão disparado. |
| **Entidades** | Provider |
| **Ports** | ProviderRepository, PierreProvider / MyProfitProvider |

---

## UC-17: DisconnectProvider 🔲 Não Iniciado

**Objetivo:** Desativar e opcionalmente apagar dados de um Provider.

| | |
|---|---|
| **Entrada** | `DisconnectProviderCommand` (user_id, provider_id, delete_data) |
| **Saída** | `OperationResultDTO` |
| **Endpoint** | `DELETE /providers/{id}` |
| **Pós-condições** | Provider `status=INACTIVE`. Dados apagados (soft delete) se `delete_data=True`. |
| **Entidades** | Provider, Account, Transaction (soft delete) |
| **Eventos produzidos** | `ProviderDisconnected` |

---

## UC-04: SyncPierreAccounts 🔲 Não Iniciado

**Objetivo:** Buscar todas as contas financeiras do usuário via Pierre e sincronizar com o domínio.

| | |
|---|---|
| **Entrada** | `SyncPierreCommand` (user_id) |
| **Saída** | `SyncResultDTO` (created, updated, skipped, errors) |
| **Endpoint** | `POST /sync/pierre` (resources=["accounts"]) |
| **Pré-condições** | Provider Pierre ACTIVE. API Key válida. |
| **Pós-condições** | Accounts criadas/atualizadas. Institutions criadas/referenciadas. `last_sync_at` atualizado. |
| **Entidades** | Account, Institution, Provider |
| **Ports** | AccountRepository, InstitutionRepository, ProviderRepository, PierreProvider, IClock |
| **Eventos produzidos** | `SyncStarted`, `SyncFinished` ou `SyncFailed` |

---

## UC-05: SyncPierreTransactions 🔲 Não Iniciado

**Objetivo:** Buscar transações do Pierre para todas as contas ativas e sincronizar.

| | |
|---|---|
| **Entrada** | `SyncPierreCommand` (user_id, date_range?) |
| **Saída** | `SyncResultDTO` |
| **Endpoint** | `POST /sync/pierre` (resources=["transactions"]) |
| **Pré-condições** | Accounts sincronizadas (UC-04). Provider ACTIVE. |
| **Pós-condições** | Transactions criadas (sem duplicatas via hash). Categories mapeadas ou marcadas para classificação. |
| **Entidades** | Transaction, Account, Category, Provider |
| **Ports** | TransactionRepository, AccountRepository, CategoryRepository, ProviderRepository, PierreProvider, IClock |
| **Eventos produzidos** | `TransactionImported`, `SyncStarted`, `SyncFinished` |

---

## UC-12: GetPortfolio 🔲 Não Iniciado

**Objetivo:** Retornar a visão atual da carteira de investimentos do usuário.

| | |
|---|---|
| **Entrada** | `GetPortfolioQuery` (user_id, portfolio_id?) |
| **Saída** | `PortfolioResponseDTO` |
| **Endpoint** | `GET /portfolio` |
| **Entidades** | Position, Asset, Portfolio, Dividend |
| **Ports** | PositionRepository, AssetRepository, DividendRepository |

---

## UC-18: GetDividends 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `GetDividendsQuery` (user_id, asset_id?, year?, type?, page, page_size) |
| **Saída** | `PaginatedResponseDTO<DividendResponseDTO>` |
| **Endpoint** | `GET /dividends` |
| **Entidades** | Dividend, Asset, Portfolio |
| **Ports** | DividendRepository |

---

## UC-06: SyncMyProfitPortfolio 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `SyncMyProfitCommand` (user_id) |
| **Saída** | `SyncResultDTO` |
| **Endpoint** | `POST /sync/myprofit` |
| **Pré-condições** | Provider MyProfit ACTIVE. Sessão válida (cookies). |
| **Pós-condições** | Assets criados. Positions (snapshots) criadas. Dividends criados. |
| **Entidades** | Asset, Position, Dividend, Portfolio, Provider |
| **Ports** | AssetRepository, PositionRepository, DividendRepository, PortfolioRepository, ProviderRepository, MyProfitProvider, IClock |
| **Eventos produzidos** | `PortfolioUpdated`, `DividendReceived`, `SyncStarted`, `SyncFinished` |

---

## UC-07: SyncYFinanceQuotes 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `RefreshQuotesCommand` (user_id, tickers?) |
| **Saída** | `SyncResultDTO` |
| **Endpoint** | `POST /sync/quotes` |
| **Pré-condições** | Assets existentes com ticker. |
| **Pós-condições** | `Position.current_price` e `current_value` atualizados. |
| **Entidades** | Asset, Position |
| **Ports** | AssetRepository, PositionRepository, YFinanceProvider, IClock |
## UC-20: GetSubscriptionsSummary 🔲 Não Iniciado

**Objetivo:** Agrupar assinaturas e projetar gasto anual/mensal.

| | |
|---|---|
| **Entrada** | `GetSubscriptionsSummaryQuery` (user_id, month?) |
| **Saída** | `SubscriptionsSummaryDTO` |
| **Endpoint** | `GET /dashboard/subscriptions` |
| **Entidades** | Transaction (`is_recurring=True`) |
| **Ports** | TransactionRepository |

---

## UC-21: GetInstallmentsSummary 🔲 Não Iniciado

**Objetivo:** Retornar o progresso de parcelamentos ativos de cartões.

| | |
|---|---|
| **Entrada** | `GetInstallmentsSummaryQuery` (user_id, month?) |
| **Saída** | `InstallmentsSummaryDTO` |
| **Endpoint** | `GET /dashboard/installments` |
| **Entidades** | Transaction (com total_installments) |
| **Ports** | TransactionRepository |

---

## UC-22: GetAuditSummary 🔲 Não Iniciado

**Objetivo:** Extrair logs de auditoria de sincronizações de Providers.

| | |
|---|---|
| **Entrada** | `GetAuditSummaryQuery` (status_filter?) |
| **Saída** | `list[AuditRunDTO]` |
| **Endpoint** | `GET /governance/audit` |
| **Entidades** | AuditRun |
| **Ports** | AuditRepository |

---

## UC-23: GetDatabaseHealth 🔲 Não Iniciado

**Objetivo:** Verificar integridade, tamanho e tabelas do banco de dados (SQLite).

| | |
|---|---|
| **Entrada** | `GetDatabaseHealthQuery` () |
| **Saída** | `DatabaseHealthDTO` |
| **Endpoint** | `GET /governance/database/health` |
| **Entidades** | N/A |
| **Ports** | IDatabaseHealthPort |

---

## UC-24: GetGoals 🔲 Não Iniciado

**Objetivo:** Listar metas e orçamentos do usuário.

| | |
|---|---|
| **Entrada** | `GetGoalsQuery` (user_id) |
| **Saída** | `list[GoalDTO]` |
| **Endpoint** | `GET /goals` |
| **Entidades** | Goal |
| **Ports** | GoalRepository |

---

## UC-25: GetProfile 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `GetProfileQuery` (user_id) |
| **Saída** | `ProfileDTO` |
| **Endpoint** | `GET /profile` |
| **Entidades** | User, Profile |
| **Ports** | UserRepository |

---

## UC-26: UpdateProfile 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `UpdateProfileCommand` (user_id, preferences) |
| **Saída** | `ProfileDTO` |
| **Endpoint** | `PATCH /profile` |
| **Entidades** | Profile |
| **Ports** | UserRepository |

---

## UC-08: ImportCSV 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `ImportCsvCommand` (user_id, file_bytes, csv_type, account_id?, confirm) |
| **Saída** | `ImportResultDTO` (total, imported, skipped, errors, preview) |
| **Endpoint** | `POST /import/csv` |
| **Pré-condições** | Arquivo válido. Encoding detectável. Headers reconhecíveis. |
| **Pós-condições** | Transactions ou Dividends criados com `provider=CSV`. Hash deduplicação aplicado. |
| **Entidades** | Transaction, Dividend, Category, Account |
| **Ports** | TransactionRepository, DividendRepository, AccountRepository, CategoryRepository, IClock |
| **Eventos produzidos** | `TransactionImported` ou `DividendReceived` |

---

## UC-09: ClassifyTransaction 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `ClassifyTransactionCommand` (user_id, transaction_ids?, override?) |
| **Saída** | `ClassificationResultDTO` |
| **Endpoint** | `POST /classify` |
| **Pré-condições** | Transações com `category_id=NULL`. GeminiProvider configurado. |
| **Pós-condições** | `category_id` preenchido nas transactions classificadas. |
| **Entidades** | Transaction, Category |
| **Ports** | TransactionRepository, CategoryRepository, GeminiProvider |
| **Eventos produzidos** | `CategoryClassified` |

---

## UC-14: GenerateInsights 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `GenerateInsightsCommand` (user_id, period?, context?) |
| **Saída** | `list[InsightDTO]` |
| **Endpoint** | `GET /insights` |
| **Pré-condições** | Dados financeiros disponíveis. GeminiProvider configurado. |
| **Entidades** | Transaction, Position, Dividend, Account |
| **Ports** | TransactionRepository, PositionRepository, GeminiProvider |
| **Eventos produzidos** | `InsightGenerated` |

---

## UC-10: GetDashboard 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `GetDashboardQuery` (user_id, period?, currency?) |
| **Saída** | `DashboardDTO` |
| **Endpoint** | `GET /dashboard` |
| **Pré-condições** | Dados sincronizados (Fases 2–7 concluídas) |
| **Entidades** | Account, Transaction, Position, Dividend |
| **Ports** | AccountRepository, TransactionRepository, PositionRepository, DividendRepository, ICache |

---

## UC-13: GetCashFlow 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `GetCashFlowQuery` (user_id, start_date?, end_date?, group_by?, account_ids?) |
| **Saída** | `CashFlowDTO` |
| **Endpoint** | `GET /cashflow` |
| **Entidades** | Transaction, Account |
| **Ports** | TransactionRepository |

---

## UC-15: GetAlerts 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `GetAlertsQuery` (user_id, type?, active_only?) |
| **Saída** | `list[AlertDTO]` |
| **Endpoint** | `GET /alerts` |
| **Entidades** | Transaction |
| **Ports** | TransactionRepository, ICache |

---

## UC-20: BackupDatabase 🔲 Não Iniciado

| | |
|---|---|
| **Entrada** | `BackupDatabaseCommand` (user_id, destination?) |
| **Saída** | `BackupResultDTO` |
| **Endpoint** | `POST /admin/backup` |
| **Ports** | IStorage, IClock, ILogger |
| **Eventos produzidos** | `BackupCreated` |

---

## Mapeamento UC → Fase de Implementação

| Use Case | Fase | Status |
|---|---|---|
| UC-01: AuthenticateUser | Fase 1 | ✅ Concluído |
| UC-03: RefreshToken | Fase 1 | 🔲 Não Iniciado |
| UC-11A: GetAccounts | Fase 2 | 🔲 Não Iniciado |
| UC-11B: GetCategoriesSummary | Fase 3 | 🔲 Não Iniciado |
| UC-11: GetTransactions | Fase 3 | 🔲 Não Iniciado |
| UC-19: UpdateCategory | Fase 3 | 🔲 Não Iniciado |
| UC-16: ConnectProvider | Fase 5 | 🔲 Não Iniciado |
| UC-04: SyncPierreAccounts | Fase 5 | 🔲 Não Iniciado |
| UC-05: SyncPierreTransactions | Fase 5 | 🔲 Não Iniciado |
| UC-12: GetPortfolio | Fase 6 | 🔲 Não Iniciado |
| UC-18: GetDividends | Fase 6 | 🔲 Não Iniciado |
| UC-06: SyncMyProfitPortfolio | Fase 7 | 🔲 Não Iniciado |
| UC-07: SyncYFinanceQuotes | Fase 7 | 🔲 Não Iniciado |
| UC-08: ImportCSV | Fase 8 | 🔲 Não Iniciado |
| UC-09: ClassifyTransaction | Fase 9 | 🔲 Não Iniciado |
| UC-14: GenerateInsights | Fase 9 | 🔲 Não Iniciado |
| UC-10: GetDashboard | Fase 10 | 🔲 Não Iniciado |
| UC-13: GetCashFlow | Fase 10 | 🔲 Não Iniciado |
| UC-15: GetAlerts | Fase 10 | 🔲 Não Iniciado |
| UC-17: DisconnectProvider | Fase 5 | 🔲 Não Iniciado |
| UC-20: BackupDatabase | Fase 11 | 🔲 Não Iniciado |
