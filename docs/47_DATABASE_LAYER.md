> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Camada de Banco de Dados — FIN Analytics

---

## Stack

| Componente | Tecnologia | Versão mínima |
|---|---|---|
| ORM | SQLAlchemy | 2.x (async) via create_async_engine |
| Migrations | Alembic | 1.x |
| Banco (dev/prod inicial) | SQLite 3 | 3.35+ |
| Banco (futuro prod) | PostgreSQL | 15+ |
| Driver async SQLite | aiosqlite | — |

---

## Responsabilidades

| Componente | Quem cria | Quem fecha | Quem faz commit | Quem faz rollback |
|---|---|---|---|---|
| **Engine** | `database/engine.py` (1x na startup) | Shutdown da aplicação | — | — |
| **Session** | `Unit of Work` (por request/operação) | `Unit of Work` | `Unit of Work` | `Unit of Work` |
| **Repository** | DI Container (injetado no Use Case) | — | ❌ NUNCA | ❌ NUNCA |
| **Use Case** | DI Container | — | ❌ NUNCA | ❌ NUNCA |
| **API Router** | — | — | ❌ NUNCA | ❌ NUNCA |

> [!IMPORTANT]
> **Regra de Ouro:** Apenas o `Unit of Work` faz `commit` e `rollback`. Repositories e Use Cases nunca tocam em transações diretamente.

---

## Unit of Work Pattern

O `UnitOfWork` é o guardião da transação. Ele:
1. Abre a Session
2. Injeta nos Repositories
3. Faz commit após sucesso
4. Faz rollback em exceção
5. Fecha a Session

```
# Pseudocódigo do contrato:

class IUnitOfWork(ABC):
    transactions: ITransactionRepository
    accounts: IAccountRepository
    positions: IPositionRepository
    ...

    async def __aenter__(self) -> "IUnitOfWork": ...
    async def __aexit__(self, *args) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
```

*Nota: Implementações concretas de UnitOfWork utilizam `async_sessionmaker` injetando `AsyncSession`.*

**Uso nos Use Cases:**
```
# Use Case recebe IUnitOfWork via DI
async with self.uow:
    account = await self.uow.accounts.get_by_id(id)
    account.balance = new_balance
    await self.uow.commit()
```

---

## SQLAlchemy Models (ORM)

- Ficam em `infrastructure/persistence/models/`
- **São completamente separados das Entidades do Domain**
- Mapeiam 1:1 com as tabelas do banco
- Nunca saem da camada Infrastructure
- O Repository converte Model → Domain Entity antes de retornar

### Convenção de Nomenclatura

| Domain Entity | ORM Model | Tabela |
|---|---|---|
| `Transaction` | `TransactionModel` | `transactions` |
| `Account` | `AccountModel` | `accounts` |
| `Asset` | `AssetModel` | `assets` |
| `Position` | `PositionModel` | `positions` |
| `Dividend` | `DividendModel` | `dividends` |
| `Portfolio` | `PortfolioModel` | `portfolios` |
| `Institution` | `InstitutionModel` | `institutions` |
| `Category` | `CategoryModel` | `categories` |
| `User` | `UserModel` | `users` |
| `Provider` | `ProviderModel` | `providers` |
| `Tag` | `TagModel` | `tags` |

---

## Alembic (Migrations)

- **Toda alteração de schema nasce como migration** — nunca via `CREATE TABLE` manual
- Localização: `backend/database/migrations/`
- `env.py` importa `Base.metadata` do `backend/database/base.py`
- Convenção de nomes: `YYYYMMDD_HHMM_descricao_curta.py`
- Nunca fazer downgrade em produção sem backup prévio

### Sequência de Migration Padrão

```
1. Alterar ORM Model em infrastructure/persistence/models/
2. alembic revision --autogenerate -m "descricao"
3. Revisar o arquivo gerado (nunca confiar 100% no autogenerate)
4. alembic upgrade head
5. Verificar schema com PRAGMA table_info (SQLite)
```

---

## Configuração do Engine (SQLite)

```
# Configurações obrigatórias para produção em SQLite
PRAGMA foreign_keys = ON
PRAGMA journal_mode = WAL
PRAGMA synchronous = NORMAL
PRAGMA busy_timeout = 5000
```

---

## Índices Obrigatórios

| Tabela | Colunas Indexadas | Motivo |
|---|---|---|
| `transactions` | `user_id, transaction_date` | Filtros de dashboard |
| `transactions` | `hash` (UNIQUE) | Deduplicação |
| `transactions` | `external_id, provider` (UNIQUE) | Upsert |
| `transactions` | `category_id` | Filtros por categoria |
| `accounts` | `external_id, provider` (UNIQUE) | Upsert |
| `positions` | `asset_id, portfolio_id, snapshot_date` | Latest snapshot |
| `dividends` | `asset_id, ex_date` | Filtros |
| `users` | `email` (UNIQUE) | Login |
| `assets` | `ticker, exchange` (UNIQUE) | Lookup |

---

## Regras de Acesso ao Banco

1. **Nunca** usar SQL raw fora de `infrastructure/persistence/repositories/`
2. **Nunca** importar `Session` em Use Cases, API Routers ou Domain
3. **Nunca** retornar ORM Models fora da camada Infrastructure
4. **Sempre** converter `ORM Model → Domain Entity` no Repository antes de retornar
5. **Sempre** usar `async with uow:` nos Use Cases — nunca gerenciar sessão manualmente
