> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Endpoints REST — FIN Analytics

Padrão único adotado: **REST convencional** (`/recurso` no plural, sem prefixo `/tools/api/`).

Todos os endpoints abaixo pertencem à API do FIN Analytics. Endpoints legados do Pierre MCP (`/tools/api/get-*`) são referências de integração externa — não endpoints da nossa API.

---

## Autenticação

### POST /auth/login ✅ IMPLEMENTADO
- **Use Case:** UC-01: AuthenticateUser
- **Auth:** Pública
- **Body:** `{ "email": "str", "password": "str" }`
- **Response 200:** `AuthTokenDTO`
- **Response 401:** Credenciais inválidas
- **Response 403:** Usuário inativo

### POST /auth/refresh 🔲 Não Iniciado
- **Use Case:** UC-03: RefreshToken
- **Auth:** Pública (refresh token no body)
- **Body:** `{ "refresh_token": "str" }`
- **Response 200:** `AuthTokenDTO`
- **Response 401:** Token inválido ou expirado

---

## Desenvolvimento

### GET /dev/status ✅ IMPLEMENTADO
- **Use Case:** — (verificação direta de infra)
- **Auth:** Pública
- **Response 200:** `{ "database": "ok", "bootstrap": "ok", "admin_exists": true, "jwt": "ok" }`

---

## Contas Financeiras

### GET /accounts 🔲 Não Iniciado (Fase 2)
- **Use Case:** UC-11A: GetAccounts
- **Auth:** JWT obrigatório
- **Query params:** `type?`, `is_active?`, `provider?`
- **Response 200:** `list[AccountResponseDTO]`
- **Response 401:** Não autenticado

---

## Categorias

### GET /categories 🔲 Não Iniciado (Fase 3)
- **Use Case:** UC-11B: GetCategories
- **Auth:** JWT obrigatório
- **Query params:** `include_system?`, `include_user?`
- **Response 200:** `list[CategoryResponseDTO]`

---

## Transações

### GET /transactions 🔲 Não Iniciado (Fase 4)
- **Use Case:** UC-11: GetTransactions
- **Auth:** JWT obrigatório
- **Query params:** `start_date?`, `end_date?`, `account_ids?`, `category_ids?`, `provider?`, `direction?`, `min_amount?`, `max_amount?`, `search?`, `page`, `page_size`
- **Response 200:** `PaginatedResponseDTO<TransactionResponseDTO>`

### PATCH /transactions/{id}/category 🔲 Não Iniciado (Fase 4)
- **Use Case:** UC-19: UpdateCategory
- **Auth:** JWT obrigatório
- **Body:** `{ "category_id": "UUID" }`
- **Response 200:** `TransactionResponseDTO`
- **Response 404:** Transação não encontrada

---

## Providers (Integrações)

### POST /providers/connect 🔲 Não Iniciado (Fase 5)
- **Use Case:** UC-16: ConnectProvider
- **Auth:** JWT obrigatório
- **Body:** `{ "provider_type": "PIERRE|MYPROFIT|CSV|YFINANCE", "config": {} }`
- **Response 200:** `ProviderResponseDTO`

### GET /providers 🔲 Não Iniciado (Fase 5)
- **Use Case:** listagem simples
- **Auth:** JWT obrigatório
- **Response 200:** `list[ProviderResponseDTO]`

### DELETE /providers/{id} 🔲 Não Iniciado (Fase 5)
- **Use Case:** UC-17: DisconnectProvider
- **Auth:** JWT obrigatório
- **Query params:** `delete_data?` (boolean, default false)
- **Response 200:** `OperationResultDTO`

---

## Sincronização

### POST /sync/pierre 🔲 Não Iniciado (Fase 5)
- **Use Cases:** UC-04 (accounts) + UC-05 (transactions)
- **Auth:** JWT obrigatório
- **Body:** `SyncPierreCommand`
- **Response 200:** `SyncResultDTO`

### POST /sync/myprofit 🔲 Não Iniciado (Fase 7)
- **Use Case:** UC-06: SyncMyProfitPortfolio
- **Auth:** JWT obrigatório
- **Body:** `SyncMyProfitCommand`
- **Response 200:** `SyncResultDTO`

### POST /sync/quotes 🔲 Não Iniciado (Fase 7)
- **Use Case:** UC-07: SyncYFinanceQuotes
- **Auth:** JWT obrigatório
- **Body:** `RefreshQuotesCommand`
- **Response 200:** `SyncResultDTO`

---

## Importação CSV

### POST /import/csv 🔲 Não Iniciado (Fase 8)
- **Use Case:** UC-08: ImportCSV
- **Auth:** JWT obrigatório
- **Body:** `multipart/form-data` (file + csv_type + account_id? + confirm)
- **Response 200:** `ImportResultDTO`

---

## Portfólio e Dividendos

### GET /portfolio 🔲 Não Iniciado (Fase 6)
- **Use Case:** UC-12: GetPortfolio
- **Auth:** JWT obrigatório
- **Query params:** `portfolio_id?`, `asset_type?`, `include_zeroed?`
- **Response 200:** `PortfolioResponseDTO`

### GET /dividends 🔲 Não Iniciado (Fase 6)
- **Use Case:** UC-18: GetDividends
- **Auth:** JWT obrigatório
- **Query params:** `asset_id?`, `year?`, `type?`, `page`, `page_size`
- **Response 200:** `PaginatedResponseDTO<DividendResponseDTO>`

---

## IA

### POST /classify 🔲 Não Iniciado (Fase 9)
- **Use Case:** UC-09: ClassifyTransaction
- **Auth:** JWT obrigatório
- **Body:** `ClassifyTransactionCommand`
- **Response 200:** `ClassificationResultDTO`

### GET /insights 🔲 Não Iniciado (Fase 9)
- **Use Case:** UC-14: GenerateInsights
- **Auth:** JWT obrigatório
- **Query params:** `period?`, `limit?`
- **Response 200:** `list[InsightDTO]`

---

## Dashboard e Analytics

### GET /dashboard 🔲 Não Iniciado (Fase 10)
- **Use Case:** UC-10: GetDashboard
- **Auth:** JWT obrigatório
- **Query params:** `period?`, `currency?`
- **Response 200:** `DashboardDTO`

### GET /dashboard/summary-v2 🔲 Não Iniciado (Fase 10)
- **Use Case:** UC-10B: GetDashboardSummaryV2
- **Auth:** JWT obrigatório
- **Query params:** `month`
- **Response 200:** `DashboardSummaryV2DTO`

### GET /dashboard/pacing-v2 🔲 Não Iniciado (Fase 10)
- **Use Case:** UC-10C: GetDashboardPacing
- **Auth:** JWT obrigatório
- **Query params:** `month`
- **Response 200:** `PacingV2DTO`

### GET /dashboard/heatmap 🔲 Não Iniciado (Fase 10)
- **Use Case:** UC-10D: GetDashboardHeatmap
- **Auth:** JWT obrigatório
- **Query params:** `month`
- **Response 200:** `list[HeatmapDayDTO]`

### GET /dashboard/subscriptions 🔲 Não Iniciado (Fase 4)
- **Use Case:** UC-20: GetSubscriptionsSummary
- **Auth:** JWT obrigatório
- **Query params:** `month?`
- **Response 200:** `SubscriptionsSummaryDTO`

### GET /dashboard/installments 🔲 Não Iniciado (Fase 4)
- **Use Case:** UC-21: GetInstallmentsSummary
- **Auth:** JWT obrigatório
- **Query params:** `month?`
- **Response 200:** `InstallmentsSummaryDTO`

### GET /cashflow 🔲 Não Iniciado (Fase 10)
- **Use Case:** UC-13: GetCashFlow
- **Auth:** JWT obrigatório
- **Query params:** `start_date?`, `end_date?`, `group_by?`, `account_ids?`
- **Response 200:** `CashFlowDTO`

### GET /alerts 🔲 Não Iniciado (Fase 10)
- **Use Case:** UC-15: GetAlerts
- **Auth:** JWT obrigatório
- **Query params:** `type?`, `active_only?`
- **Response 200:** `list[AlertDTO]`

---

## Governança e Metas

### GET /governance/audit 🔲 Não Iniciado (Fase 12)
- **Use Case:** UC-22: GetAuditSummary
- **Auth:** JWT obrigatório
- **Response 200:** `list[AuditRunDTO]`

### GET /governance/database/health 🔲 Não Iniciado (Fase 12)
- **Use Case:** UC-23: GetDatabaseHealth
- **Auth:** JWT obrigatório
- **Response 200:** `DatabaseHealthDTO`

### GET /goals 🔲 Não Iniciado (Fase 13)
- **Use Case:** UC-24: GetGoals
- **Auth:** JWT obrigatório
- **Response 200:** `list[GoalDTO]`

### GET /profile 🔲 Não Iniciado (Fase 14)
- **Use Case:** UC-25: GetProfile
- **Auth:** JWT obrigatório
- **Response 200:** `ProfileDTO`

---

## Admin

### POST /admin/backup 🔲 Não Iniciado (Fase 11)
- **Use Case:** UC-20: BackupDatabase
- **Auth:** JWT obrigatório (role=ADMIN)
- **Body:** `BackupDatabaseCommand`
- **Response 200:** `BackupResultDTO`

---

## Matriz UC ↔ Endpoint

| Endpoint | Use Case | Fase | Status |
|---|---|---|---|
| POST /auth/login | UC-01 | 1 | ✅ |
| POST /auth/refresh | UC-03 | 1 | 🔲 |
| GET /dev/status | — | 0 | ✅ |
| GET /accounts | UC-11A | 2 | 🔲 |
| GET /categories | UC-11B | 3 | 🔲 |
| GET /transactions | UC-11 | 4 | 🔲 |
| PATCH /transactions/{id}/category | UC-19 | 4 | 🔲 |
| POST /providers/connect | UC-16 | 5 | 🔲 |
| GET /providers | — | 5 | 🔲 |
| DELETE /providers/{id} | UC-17 | 5 | 🔲 |
| POST /sync/pierre | UC-04 + UC-05 | 5 | 🔲 |
| POST /sync/myprofit | UC-06 | 7 | 🔲 |
| POST /sync/quotes | UC-07 | 7 | 🔲 |
| POST /import/csv | UC-08 | 8 | 🔲 |
| GET /portfolio | UC-12 | 6 | 🔲 |
| GET /dividends | UC-18 | 6 | 🔲 |
| POST /classify | UC-09 | 9 | 🔲 |
| GET /insights | UC-14 | 9 | 🔲 |
| GET /dashboard | UC-10 | 10 | 🔲 |
| GET /cashflow | UC-13 | 10 | 🔲 |
| GET /alerts | UC-15 | 10 | 🔲 |
| POST /admin/backup | UC-20 | 11 | 🔲 |
