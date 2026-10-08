> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Infrastructure — FIN Analytics

---

## Estrutura de Pastas (Definitiva)

```
fin_analytics_v2/
├── backend/
│   ├── api/                        # Camada de API (FastAPI Routers)
│   │   ├── dependencies/           # Injeção de dependências (DI wiring)
│   │   ├── middleware/             # CORS, Auth, Logging, RateLimit
│   │   └── routers/                # Routers por recurso (auth, accounts, transactions...)
│   │
│   ├── application/                # Camada Application (Use Cases, Commands, Queries)
│   │   ├── commands/               # Command objects (imutáveis)
│   │   ├── queries/                # Query objects e filtros
│   │   ├── use_cases/              # Use Cases (orquestração)
│   │   └── ports/                  # Interfaces abstratas (ABC) dos Repositories e Providers
│   │
│   ├── domain/                     # Camada Domínio (entidades, value objects, enums)
│   │   ├── entities/               # Transaction, Account, Asset, Position, etc.
│   │   ├── value_objects/          # Money, Ticker, DateRange, etc.
│   │   └── enums/                  # TransactionType, AssetType, ProviderType, etc.
│   │
│   ├── infrastructure/             # Camada Infrastructure (implementações concretas)
│   │   ├── persistence/            # SQLAlchemy models + Repositories concretos
│   │   │   ├── models/             # ORM Models (mapeiam tabelas)
│   │   │   ├── repositories/       # Implementações de IXxxRepository
│   │   │   └── unit_of_work.py     # Unit of Work pattern
│   │   ├── cache/                  # ICache implementations
│   │   ├── storage/                # IStorage implementations
│   │   └── secrets/                # ISecrets (env-based)
│   │
│   ├── integrations/               # Provider Adapters
│   │   ├── pierre/                 # PierreRestAdapter + PierreMapper
│   │   ├── myprofit/               # MyProfitSessionAdapter + MyProfitMapper
│   │   ├── yfinance/               # YFinanceAdapter + YFinanceMapper
│   │   └── gemini/                 # GeminiAdapter
│   │
│   ├── core/
│   │   ├── config.py               # Settings (pydantic-settings)
│   │   ├── security.py             # JWT, hashing
│   │   ├── logging.py              # Logger configurado
│   │   └── container.py            # DI Container (wiring Ports → Implementations)
│   │
│   └── database/
│       ├── engine.py               # SQLAlchemy engine
│       ├── session.py              # Session factory
│       ├── base.py                 # Base declarativa
│       └── migrations/             # Alembic migrations
│
├── frontend/                       # Frontend (futura implementação)
│
├── frontend-dev/                   # Frontend Dev (React + Vite)
│   ├── src/                        # Playground UI
│   └── package.json
│
├── scripts/                        # Scripts operacionais
│   ├── start_dev.ps1               # Inicializar ambiente de dev em Powershell (Backend + Frontend)
│   ├── start_dev.sh                # Inicializar ambiente de dev em Bash (Backend + Frontend)
│   ├── start_mcp.ps1               # Inicializar MCP Pierre
│   ├── reset_database.py           # Reset para testes
│   └── backup.py                   # Backup manual
│
├── tests/                          # Testes (espelha estrutura do backend)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── docs/                           # Documentação oficial
```

---

## Responsabilidades por Camada

### Domain
- **Contém:** Entidades, Value Objects, Enums, Regras de Negócio
- **Nunca depende de:** Application, Infrastructure, API, Providers, banco de dados, HTTP
- **Nunca importa:** SQLAlchemy, FastAPI, httpx, requests, pydantic (exceto base para VOs)

### Application
- **Contém:** Use Cases, Commands, Queries, Ports (interfaces), DTOs, Eventos
- **Depende de:** Domain (entidades e VOs)
- **Nunca depende de:** Infrastructure concreta, FastAPI, SQLAlchemy, HTTP clients
- **Conhece os Ports:** Importa as interfaces — nunca as implementações

### Infrastructure
- **Contém:** SQLAlchemy Models, Repository implementations, Cache, Storage, Secrets, Security (JWT, Hasher)
- **Implementa:** Todos os Repository, Security e Infrastructure Ports definidos em Application
- **Depende de:** Application (Ports), Domain (entidades)
- **Nunca é importada por:** Domain ou Application diretamente

### API (Routers)
- **Contém:** FastAPI routers, request/response schemas Pydantic, middlewares
- **Schema lifecycle:** `backend.main` é inerte para DDL. Alembic é a autoridade exclusiva para evolução do schema e deve ser executado explicitamente antes do runtime; import/startup não cria nem repara tabelas.
- **Depende de:** Application (Commands, Queries, Use Cases via DI)
- **Nunca importa:** Infrastructure diretamente (apenas via DI Container)
- **Nunca retorna:** Entidades do Domain — apenas DTOs

### Integrations (Providers)
- **Contém:** Adapters HTTP/Session para Pierre, MyProfit, YFinance, Gemini + Mappers
- **Implementa:** Provider Ports definidos em Application
- **Retorna:** `dict` bruto para os Mappers — nunca entidades Domain
- **Mappers:** Convertem `dict` Provider → Entidade Domain Canônica

### DI Container (`core/container.py`)
- **Responsabilidade única:** fazer o wiring entre Ports e Implementações
- **É o único arquivo** que conhece tanto Application (Ports) quanto Infrastructure (implementações)
- **Nunca contém lógica de negócio**
