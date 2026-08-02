> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

> [!WARNING]
> **DOCUMENTO SUBSTITUÍDO — V3.1**
> Este documento reflete a sequência de implementação anterior (Fases 0–14).
> As Fases 0 e 1 permanecem válidas e concluídas.
> A partir da Fase 2, a sequência oficial foi **substituída** pelas Sprints 4.4–4.7 definidas em `60_ARCHITECTURE_REVISION_V31.md` e `09_ROADMAP.md`.
> Este arquivo é mantido apenas como referência histórica.

# Sequência de Implementação — FIN Analytics (HISTÓRICO)

Esta é a ordem oficial e obrigatória de implementação por **Vertical Slices**.

Cada fase entrega uma funcionalidade completamente utilizável e validável pelo usuário antes de iniciar a próxima.

**Regra permanente:** Uma fase somente pode ser considerada CONCLUÍDA após validação manual explícita do usuário no frontend-dev.

---

## ✅ Fase 0 — Infraestrutura Base (CONCLUÍDA)
```
[0.1] Projeto base (estrutura de pastas, pyproject.toml, .env)
[0.2] Database async (create_async_engine, async_sessionmaker, aiosqlite)
[0.3] Base declarativa SQLAlchemy
[0.4] Settings (pydantic-settings, DATABASE_URL, JWT_SECRET)
[0.5] DI Container (core/container.py)
[0.6] main.py (FastAPI + Lifespan + CORS + Swagger)
[0.7] GET /dev/status (verificação E2E do ambiente)
[0.8] frontend-dev (React + Vite — playground de validação)
[0.9] scripts/start_dev.ps1 e start_dev.sh
```

---

## ✅ Fase 1 — Vertical Slice: Autenticação (CONCLUÍDA)
```
Slice: Login Funcional End-to-End

[1.1] Domain
      └── User entity (domain/entities/user.py)
      └── UserRole enum

[1.2] Infrastructure
      └── UserModel (infrastructure/persistence/models/user.py)
      └── SQLAlchemyUserRepository implements IUserRepository

[1.3] Infrastructure — Security
      └── PasswordHasher (bcrypt)
      └── JWTService (access_token + refresh_token)

[1.4] Infrastructure — Bootstrap
      └── BootstrapAdmin (cria usuário admin na startup)

[1.5] Application
      └── AuthenticateUserUseCase (UC-01)
      └── AuthenticateUserCommand

[1.6] API
      └── POST /auth/login → UC-01

[1.7] frontend-dev
      └── Formulário de login (email + senha)
      └── Exibição de AuthTokenDTO (access_token, refresh_token, user, expires_in)
      └── Exibição de erros reais da API (sem alert(), sem mock)

DoD: ✅ VALIDADO PELO USUÁRIO
```

---

## 🔲 Fase 2 — Vertical Slice: Contas Financeiras

```
Slice: Listar Contas do Usuário

Pré-requisito: Fase 1 concluída.

[2.1] Domain
      └── Account entity (domain/entities/account.py)
      └── Institution entity (domain/entities/institution.py)
      └── AccountType enum (se ausente)

[2.2] Infrastructure
      └── AccountModel (infrastructure/persistence/models/account.py)
      └── InstitutionModel (infrastructure/persistence/models/institution.py)
      └── SQLAlchemyAccountRepository implements IAccountRepository
      └── SQLAlchemyInstitutionRepository implements IInstitutionRepository
      └── Tabelas criadas via Base.metadata.create_all (Lifespan)

[2.3] Application
      └── GetAccountsUseCase (UC-11A) → GetAccountsQuery
      └── GetAccountsQuery (user_id, type, is_active, provider)

[2.4] API
      └── GET /accounts → UC-11A (requer autenticação JWT)

[2.5] DI Container
      └── Registrar AccountRepository e InstitutionRepository

[2.6] Seed de Dados
      └── Criar contas manuais via endpoint (ou seed script para validação)

[2.7] frontend-dev
      └── Após login: botão "Listar Contas"
      └── Exibição da lista real de contas (nome, tipo, saldo, provider)
      └── Exibição de erro real se não autenticado (401)

DoD: EM VALIDAÇÃO PELO USUÁRIO
```

---

## 🔲 Fase 3 — Vertical Slice: Transações e Classificação (Substitui antigas VS-03 e VS-04)

```
Slice: Sincronização local, Classificação, Filtros e Projeções Analíticas

Pré-requisito: Fase 2 concluída.

[3.1] Domain
      └── Transaction entity (domain/entities/transaction.py)
      └── Category entity (domain/entities/category.py)
      └── Tag entity (domain/entities/tag.py)

[3.2] Infrastructure
      └── TransactionModel (infrastructure/persistence/models/transaction.py)
      └── CategoryModel (infrastructure/persistence/models/category.py)
      └── TagModel (infrastructure/persistence/models/tag.py)
      └── SQLAlchemyTransactionRepository implements ITransactionRepository
      └── SQLAlchemyCategoryRepository implements ICategoryRepository
      └── Seed para validação temporária (transações baseadas nas contas da Fase 2)

[3.3] Application
      └── GetTransactionsUseCase → GetTransactionsQuery
      └── GetTransactionDetailsUseCase → GetTransactionDetailsQuery
      └── GetCategoriesSummaryUseCase → GetCategoriesSummaryQuery (Projeção Analítica)
      └── GetCategoryTransactionsUseCase → GetCategoryTransactionsQuery
      └── UpdateCategoryUseCase → UpdateCategoryCommand

[3.4] API
      └── GET /transactions (requer JWT)
      └── GET /transactions/{id} (requer JWT)
      └── GET /categories (requer JWT)
      └── GET /dashboard/categories (Projeção Analítica - requer JWT)
      └── PATCH /transactions/{id}/category (requer JWT)

[3.5] frontend-dev
      └── Suporte à tela "Transações" (listagem, filtros, paginação)
      └── Suporte à tela "Categorias" (agrupamento analítico, Pie Chart)
      └── Reutilização integral do layout, adaptando apenas hooks e chamadas REST.

DoD: EM VALIDAÇÃO PELO USUÁRIO
```

---

## 🔲 Fase 4 — Vertical Slice: Assinaturas e Parcelamentos (VS-04)

```
Slice: Gerenciamento de despesas recorrentes e compras parceladas

Pré-requisito: Fase 3 concluída.

[4.1] Domain
      └── Adicionar campos em Transaction (is_recurring, current_installment, total_installments)

[4.2] Application
      └── GetSubscriptionsSummaryUseCase (UC-20) → GetSubscriptionsSummaryQuery
      └── GetInstallmentsSummaryUseCase (UC-21) → GetInstallmentsSummaryQuery

[4.3] API
      └── GET /dashboard/subscriptions → UC-20 (requer JWT)
      └── GET /dashboard/installments → UC-21 (requer JWT)

[4.4] frontend-dev
      └── Validação integral das telas /subscriptions e /installments.

DoD: EM VALIDAÇÃO PELO USUÁRIO
```

---

## 🔲 Fase 5 — Vertical Slice: Integração Pierre (Banking)

```
Slice: Sincronizar Contas e Transações via Pierre

Pré-requisito: Fase 4 concluída.

[5.1] Infrastructure
      └── ProviderModel (infrastructure/persistence/models/provider.py)
      └── SQLAlchemyProviderRepository implements IProviderRepository

[5.2] Integrations
      └── PierreRestAdapter implements IPierreProvider
      └── PierreMapper: to_canonical(Account, Transaction)

[5.3] Application
      └── ConnectProviderUseCase (UC-16) → ConnectProviderCommand
      └── SyncPierreAccountsUseCase (UC-04) → SyncPierreCommand
      └── SyncPierreTransactionsUseCase (UC-05) → SyncPierreCommand

[5.4] API
      └── POST /providers/connect → UC-16
      └── POST /sync/pierre → UC-04 + UC-05
      └── GET /providers → listar providers ativos

[5.5] frontend-dev
      └── Botão "Sincronizar Pierre"
      └── Exibição de SyncResultDTO (created, updated, skipped, errors)
      └── Contas e transações aparecem após sync

DoD: EM VALIDAÇÃO PELO USUÁRIO
```

---

## 🔲 Fase 6 — Vertical Slice: Investimentos

```
Slice: Carteira de Investimentos

Pré-requisito: Fase 4 concluída.

[6.1] Domain
      └── Asset, Portfolio, Position, Dividend entities

[6.2] Infrastructure
      └── AssetModel, PortfolioModel, PositionModel, DividendModel
      └── Repositories correspondentes

[6.3] Application
      └── GetPortfolioUseCase (UC-12) → GetPortfolioQuery
      └── GetDividendsUseCase (UC-18) → GetDividendsQuery

[6.4] API
      └── GET /portfolio → UC-12
      └── GET /dividends → UC-18

[6.5] frontend-dev
      └── Tabela de posições com gain/loss
      └── Lista de dividendos recebidos

DoD: EM VALIDAÇÃO PELO USUÁRIO
```

---

## 🔲 Fase 7 — Vertical Slice: Integração MyProfit + YFinance

```
Pré-requisito: Fase 6 concluída.

[7.1] MyProfitSessionAdapter implements IMyProfitProvider
[7.2] MyProfitMapper (Position, Dividend)
[7.3] YFinanceAdapter implements IYFinanceProvider
[7.4] SyncMyProfitPortfolioUseCase (UC-06)
[7.5] SyncYFinanceQuotesUseCase (UC-07)
[7.6] API: POST /sync/myprofit, POST /sync/quotes

DoD: EM VALIDAÇÃO PELO USUÁRIO
```

---

## 🔲 Fase 8 — Vertical Slice: Importação CSV

```
Pré-requisito: Fase 4 concluída.

[8.1] CsvParser (detect encoding, delimiter, headers)
[8.2] CsvMapper (Transaction, Dividend)
[8.3] ImportCsvUseCase (UC-08) → ImportCsvCommand
[8.4] API: POST /import/csv (preview + confirm)
[8.5] frontend-dev: upload de arquivo + preview + confirmação

DoD: EM VALIDAÇÃO PELO USUÁRIO
```

---

## 🔲 Fase 9 — Vertical Slice: Classificação por IA

```
Pré-requisito: Fase 4 concluída.

[9.1] GeminiAdapter implements IGeminiProvider
[9.2] ClassifyTransactionUseCase (UC-09) → ClassifyTransactionCommand
[9.3] GenerateInsightsUseCase (UC-14) → GenerateInsightsCommand
[9.4] API: POST /classify, GET /insights
[9.5] frontend-dev: botão "Classificar automaticamente"

DoD: EM VALIDAÇÃO PELO USUÁRIO
```

---

## 🔲 Fase 10 — Vertical Slice: Dashboard

```
Pré-requisito: TODAS as fases anteriores concluídas.

[10.1] GetDashboardUseCase (UC-10) → GetDashboardQuery
[10.2] GetCashFlowUseCase (UC-13) → GetCashFlowQuery
[10.3] GetAlertsUseCase (UC-15) → GetAlertsQuery
[10.4] API: GET /dashboard, GET /cashflow, GET /alerts
[10.5] Cache (ICache) para dashboard
[10.6] frontend-dev: visão consolidada com saldo, fluxo de caixa, top categorias, alertas

DoD: EM VALIDAÇÃO PELO USUÁRIO
```

---

## 🔲 Fase 11 — Frontend Definitivo

```
Pré-requisito: Todas as fases anteriores concluídas e validadas.

[11.1] Setup React/Next.js (projeto frontend/)
[11.2] Autenticação (login, refresh token, logout)
[11.3] Dashboard
[11.4] Transações
[11.5] Portfólio
[11.6] Dividendos
[11.7] Import CSV
[11.8] Configurações de Provider
```

## 🔲 Fase 12 — Vertical Slice: Governança e Auditoria

```
Pré-requisito: TODAS as fases anteriores concluídas.

[12.1] Setup Audit Entities (AuditRun, AuditRollback) e Repository
[12.2] GetAuditSummaryUseCase (UC-22)
[12.3] GetDatabaseHealthUseCase (UC-23)
[12.4] API: GET /governance/audit, GET /governance/database/*
[12.5] frontend-dev: painel completo de saúde de banco e auditoria de syncs.
```

---

## 🔲 Fase 13 — Vertical Slice: Metas e Orçamentos

```
Pré-requisito: Fase 3 concluída.

[13.1] Setup Goal Entity e Repository
[13.2] GetGoalsUseCase (UC-24)
[13.3] API: GET /goals
[13.4] frontend-dev: tela /goals
```

---

## 🔲 Fase 14 — Vertical Slice: Configurações e Perfil

```
Pré-requisito: Fase 1 concluída.

[14.1] Setup Profile Preferences
[14.2] GetProfileUseCase (UC-25), UpdateProfileUseCase (UC-26)
[14.3] API: GET /profile, PATCH /profile
[14.4] frontend-dev: telas /settings e /profile
```

---

## Regra de Ouro

> Uma fase somente avança para a próxima quando:
> 1. Backend compilando sem erros
> 2. Swagger funcionando e endpoint respondendo
> 3. frontend-dev consumindo API real (zero mocks)
> 4. Usuário executou o fluxo manualmente e aprovou explicitamente
>
> **Status válidos:** 🔲 Não Iniciado | 🔄 Em Andamento | 🧪 EM VALIDAÇÃO PELO USUÁRIO | ✅ Concluída
