> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Sequência de Implementação — FIN Analytics

Esta é a ordem oficial e obrigatória de implementação. Nenhuma fase pode ser iniciada sem que a anterior esteja concluída e com todos os critérios da Definition of Done atendidos.

---

## Fase 2 — Autenticação e Usuários

```
[2.1] Domain
      └── User entity (domain/entities/user.py)
      └── UserRole enum
      └── RefreshToken entity

[2.2] Infrastructure — ORM Models
      └── UserModel (infrastructure/persistence/models/user.py)
      └── RefreshTokenModel

[2.3] Infrastructure — Migrations
      └── alembic revision: create_users_table
      └── alembic revision: create_refresh_tokens_table

[2.4] Infrastructure — Repositories
      └── SQLAlchemyUserRepository implements IUserRepository

[2.5] Infrastructure — Security
      └── core/security.py: hash_password, verify_password, create_token, decode_token

[2.6] Application — Use Cases
      └── AuthenticateUserUseCase (UC-01)
      └── RefreshTokenUseCase (UC-03)

[2.7] API — Routers
      └── api/routers/auth.py: POST /login, POST /refresh, POST /logout
      └── api/routers/users.py: GET /users/me

[2.8] Testes
      └── unit: security functions, use cases mockados
      └── integration: UserRepository, AuthUseCase + banco real
      └── api: login, refresh, me
```

---

## Fase 3 — Modelos SQLAlchemy do Domínio

```
[3.1] ORM Models (infrastructure/persistence/models/)
      └── AccountModel
      └── InstitutionModel
      └── TransactionModel
      └── CategoryModel
      └── TagModel

[3.2] Migrations
      └── create_accounts_table
      └── create_institutions_table
      └── create_transactions_table
      └── create_categories_table
      └── create_tags_table

[3.3] Seed de Categorias Padrão
      └── scripts/seed_categories.py
```

---

## Fase 4 — Repositórios Base

```
[4.1] Unit of Work
      └── infrastructure/persistence/unit_of_work.py

[4.2] Repositories concretos (um por Model)
      └── SQLAlchemyAccountRepository
      └── SQLAlchemyTransactionRepository
      └── SQLAlchemyCategoryRepository

[4.3] Testes de integração de todos os repositórios
```

---

## Fase 5 — Pierre Connector (Banking)

```
[5.1] ORM Models restantes
      └── ProviderModel

[5.2] PierreRestAdapter implements IPierreProvider
      └── integrations/pierre/adapter.py

[5.3] PierreMapper
      └── integrations/pierre/mapper.py
      └── to_canonical(Account, Transaction, Bill)

[5.4] Use Cases
      └── SyncPierreAccountsUseCase (UC-04)
      └── SyncPierreTransactionsUseCase (UC-05)
      └── ConnectProviderUseCase (UC-16)

[5.5] API Routers
      └── api/routers/sync.py: POST /sync/pierre
      └── api/routers/accounts.py: GET /accounts
      └── api/routers/transactions.py: GET /transactions

[5.6] Testes
      └── Mapper: fixtures JSON Pierre
      └── Use Cases: Providers mockados
      └── API: banco in-memory
```

---

## Fase 6 — Domain de Investimentos + ORM

```
[6.1] ORM Models
      └── AssetModel
      └── PortfolioModel
      └── PositionModel
      └── DividendModel

[6.2] Migrations

[6.3] Repositories
      └── SQLAlchemyAssetRepository
      └── SQLAlchemyPortfolioRepository
      └── SQLAlchemyPositionRepository
      └── SQLAlchemyDividendRepository
```

---

## Fase 7 — MyProfit + YFinance Connectors

```
[7.1] MyProfitSessionAdapter implements IMyProfitProvider
[7.2] MyProfitMapper (Position, Dividend)
[7.3] YFinanceAdapter implements IYFinanceProvider
[7.4] Use Cases: SyncMyProfitPortfolioUseCase, SyncYFinanceQuotesUseCase
[7.5] API: GET /portfolio, GET /dividends
[7.6] Testes
```

---

## Fase 8 — Import CSV

```
[8.1] CsvParser (detect encoding, delimiter, headers)
[8.2] CsvMapper (Transaction, Dividend)
[8.3] ImportCsvUseCase (UC-08)
[8.4] API: POST /import/csv (preview + confirm)
[8.5] Testes: múltiplos formatos CSV
```

---

## Fase 9 — IA (Gemini)

```
[9.1] GeminiAdapter implements IGeminiProvider
[9.2] ClassifyTransactionUseCase (UC-09)
[9.3] GenerateInsightsUseCase (UC-14)
[9.4] API: POST /classify, GET /insights
[9.5] Testes: Gemini mockado
```

---

## Fase 10 — Dashboard e Analytics

```
[10.1] GetDashboardUseCase (UC-10)
[10.2] GetCashFlowUseCase (UC-13)
[10.3] GetAlertsUseCase (UC-15)
[10.4] API: GET /dashboard, GET /cashflow, GET /alerts
[10.5] Cache para dashboard (ICache)
[10.6] Testes E2E dos fluxos críticos
```

---

## Fase 11 — Frontend

```
[11.1] Setup (React/Next.js)
[11.2] Autenticação
[11.3] Dashboard
[11.4] Transações
[11.5] Portfólio
[11.6] Dividendos
[11.7] Import CSV
[11.8] Configurações de Provider
```
