> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Estratégia de Testes — FIN Analytics

---

## Pirâmide de Testes

```
          [E2E]          ← Poucos, lentos, cobrem fluxos críticos
        [Integration]    ← Médios, testam integração entre camadas
      [Unit]             ← Muitos, rápidos, isolados com mocks
```

---

## Testes Unitários (`tests/unit/`)

**Escopo:** Uma classe ou função isolada, sem banco, sem HTTP, sem filesystem.
**Ferramenta:** `pytest` + `pytest-asyncio`
**Mocking:** `unittest.mock.AsyncMock` / `MagicMock`

### O que testar

| Componente | O que testar |
|---|---|
| **Value Objects** | Validações (Ticker inválido, Money negativo, etc.) |
| **Enums** | Todos os valores existem |
| **Mappers** | `dict` Pierre → Domain Entity (campo a campo) |
| **Use Cases** | Toda a lógica com todos os Ports mockados |
| **Command validation** | Campos obrigatórios, formatos, limites |
| **Hash deduplication** | `calculate_hash()` retorna mesmo hash para inputs iguais |
| **Security** | `verify_password`, `create_token`, `decode_token` |

### Padrão de Mock nos Use Cases

```python
# Padrão: criar mocks de todos os ports, injetar no Use Case
async def test_sync_pierre_accounts():
    mock_pierre = AsyncMock(spec=IPierreProvider)
    mock_accounts_repo = AsyncMock(spec=IAccountRepository)
    mock_uow = AsyncMock(spec=IUnitOfWork)
    mock_pierre.get_accounts.return_value = [{"accountId": "acc_1", ...}]

    use_case = SyncPierreAccountsUseCase(
        pierre=mock_pierre,
        uow=mock_uow,
    )
    result = await use_case.execute(SyncPierreCommand(user_id=uuid4()))
    assert result.created == 1
    mock_accounts_repo.upsert.assert_called_once()
```

---

## Testes de Integração (`tests/integration/`)

**Escopo:** Testar integração com banco de dados real (SQLite em memória).
**Ferramenta:** `pytest` + `pytest-asyncio` + `SQLite in-memory`
**Fixtures:** Banco limpo por teste (rollback ao final)

### O que testar

| Componente | O que testar |
|---|---|
| **Repositories** | CRUD real no banco (SQLite in-memory) |
| **Unit of Work** | Commit e rollback corretos |
| **Migrations** | `alembic upgrade head` funciona em banco limpo |
| **Use Cases com banco** | UC + Repository real + Provider mockado |

### Fixture Padrão de Banco

```python
@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
```

---

## Testes de Provider (`tests/integration/providers/`)

**Escopo:** Validar que os Mappers convertem corretamente payloads reais dos Providers.
**Ferramenta:** `pytest` com fixtures de JSON reais (gravados da API)

### O que testar

| Provider | O que testar |
|---|---|
| **PierreMapper** | Converter JSON `get_accounts` → `Account` canônico |
| **PierreMapper** | Converter JSON `get_transactions` → `Transaction` canônico |
| **MyProfitMapper** | Converter CSV de posições → `Position` canônico |
| **MyProfitMapper** | Converter CSV de proventos → `Dividend` canônico |
| **CsvMapper** | Múltiplos formatos de data e delimitador |

**Regra:** Nunca fazer chamadas reais ao Provider em testes automáticos. Usar fixtures de JSON gravados (arquivos `.json` em `tests/fixtures/pierre/`, `tests/fixtures/myprofit/`).

---

## Testes de API (`tests/integration/api/`)

**Escopo:** Testar os endpoints HTTP com `TestClient` do FastAPI.
**Ferramenta:** `pytest` + `httpx.AsyncClient` + banco in-memory

### O que testar

| Endpoint | Casos |
|---|---|
| `POST /auth/login` | Sucesso, senha errada, usuário inexistente |
| `POST /auth/refresh` | Token válido, expirado, revogado |
| `GET /transactions` | Autenticado, sem auth, filtros, paginação |
| `POST /import/csv` | Preview, confirmação, erros de formato |
| `POST /sync/pierre` | Provider ativo, inativo, erro de API |

---

## Testes E2E (`tests/e2e/`)

**Escopo:** Fluxo completo do usuário no sistema. Mínimos e focados nos fluxos críticos.

### Fluxos E2E Obrigatórios

1. **Login + Get Dashboard** (fluxo básico autenticado)
2. **Upload CSV + Classificação IA** (fluxo de importação)
3. **Sync Pierre + Ver Transações** (fluxo de sincronização)

---

## Factories e Fixtures

```
tests/
├── factories/
│   ├── user_factory.py         # Cria Users com defaults razoáveis
│   ├── transaction_factory.py
│   ├── account_factory.py
│   └── ...
├── fixtures/
│   ├── pierre/
│   │   ├── get_accounts.json
│   │   └── get_transactions.json
│   └── myprofit/
│       ├── positions.csv
│       └── dividends.csv
└── conftest.py                 # Fixtures compartilhadas (db, client, user autenticado)
```

---

## Cobertura Mínima Obrigatória

| Camada | Cobertura Mínima |
|---|---|
| Domain (entidades, VOs) | 95% |
| Mappers | 100% |
| Use Cases | 90% |
| Repositories | 80% |
| API Routers | 80% |
| Providers | 70% (fixtures) |

Usar `pytest-cov` para medir. Falha no CI se abaixo do mínimo.
