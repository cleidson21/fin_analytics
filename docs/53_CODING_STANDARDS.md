> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Padrões de Código — FIN Analytics

---

## Nomenclatura

| Tipo | Padrão | Exemplo |
|---|---|---|
| Classes | `PascalCase` | `TransactionRepository`, `SyncPierreUseCase` |
| Funções / métodos | `snake_case` | `get_by_id`, `calculate_hash` |
| Variáveis | `snake_case` | `transaction_date`, `user_id` |
| Constantes | `UPPER_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS = 3` |
| Arquivos | `snake_case.py` | `transaction_repository.py` |
| Tabelas SQL | `snake_case` (plural) | `transactions`, `user_portfolios` |
| Colunas SQL | `snake_case` | `transaction_date`, `created_at` |
| Interfaces (Ports) | `I` prefix | `ITransactionRepository`, `IPierreProvider` |
| ORM Models | `Model` suffix | `TransactionModel`, `UserModel` |
| Mappers | `Mapper` suffix | `PierreTransactionMapper` |
| Adapters | `Adapter` suffix | `PierreRestAdapter` |
| Use Cases | `UseCase` suffix | `SyncPierreAccountsUseCase` |
| Commands | `Command` suffix | `SyncPierreCommand` |
| Queries | `Query` suffix | `GetTransactionsQuery` |
| DTOs | `DTO` suffix | `TransactionResponseDTO` |
| Events | past tense | `TransactionImported`, `SyncFinished` |

---

## Imports

**Ordem obrigatória (isort):**
1. Standard library (`os`, `datetime`, `uuid`)
2. Third-party (`fastapi`, `sqlalchemy`, `pydantic`)
3. Internal — Domain
4. Internal — Application
5. Internal — Infrastructure

**Regra de dependência:**
```
# ✅ CORRETO — Application importa Domain
from domain.entities.transaction import Transaction

# ❌ ERRADO — Domain importa Infrastructure
from infrastructure.persistence.models import TransactionModel  # PROIBIDO

# ❌ ERRADO — Use Case importa SQLAlchemy
from sqlalchemy.orm import Session  # PROIBIDO EM USE CASES
```

---

## Typing Obrigatório

- Todo arquivo usa `from __future__ import annotations`
- Todas as funções públicas têm type hints completos
- Usar `Decimal` para valores monetários — nunca `float`
- Usar `UUID` (uuid.UUID) para IDs — nunca `str` para IDs
- Usar `date` e `datetime` — nunca `str` para datas em entidades
- Retornos opcionais: `X | None` (Python 3.10+)

---

## Docstrings

```python
def calculate_hash(external_id: str, provider: ProviderType, date: date, amount: Decimal) -> str:
    """
    Calcula o hash SHA256 para deduplicação de transações.

    Args:
        external_id: ID original do Provider.
        provider: Enum do Provider de origem.
        date: Data da transação.
        amount: Valor absoluto da transação.

    Returns:
        String hexadecimal SHA256 (64 chars).
    """
```

Obrigatório em:
- Todos os métodos públicos de Use Cases
- Todos os métodos de Ports (interfaces)
- Todos os Mappers
- Todas as funções utilitárias em `core/`

---

## Regras Absolutas de Arquitetura

### Nunca Fazer

| Proibição | Motivo |
|---|---|
| SQL raw fora de `infrastructure/persistence/repositories/` | Vazamento de infraestrutura |
| `Session` em Use Cases ou API | Viola separação de camadas |
| ORM Model retornado pela API | Viola encapsulamento |
| Provider retornando entidade Domain | Provider deve retornar `dict` bruto |
| `datetime.now()` em Use Cases | Impossibilita testes determinísticos |
| `os.environ` em Use Cases | Usar `ISecrets` |
| Import circular entre camadas | Viola dependências |
| `print()` em código de produção | Usar `ILogger` |
| Lógica de negócio em Router | Router apenas valida e delega |
| Lógica de negócio em Repository | Repository apenas persiste |

---

## Estrutura Padrão de um Use Case

```python
class SyncPierreAccountsUseCase:
    def __init__(
        self,
        pierre: IPierreProvider,
        uow: IUnitOfWork,
        clock: IClock,
        event_bus: IEventBus,
        logger: ILogger,
    ) -> None:
        self._pierre = pierre
        self._uow = uow
        self._clock = clock
        self._event_bus = event_bus
        self._logger = logger

    async def execute(self, command: SyncPierreCommand) -> SyncResultDTO:
        self._logger.info("SyncPierreAccounts started", user_id=str(command.user_id))
        try:
            raw = await self._pierre.get_accounts()
            accounts = PierreAccountMapper.to_canonical_list(raw)
            async with self._uow:
                for account in accounts:
                    await self._uow.accounts.upsert(account)
                await self._uow.commit()
            await self._event_bus.publish(SyncFinished(...))
            return SyncResultDTO(...)
        except PierreAuthError as e:
            await self._event_bus.publish(SyncFailed(...))
            raise ProviderError(...) from e
```

---

## Estrutura Padrão de um Mapper

```python
class PierreAccountMapper:
    @staticmethod
    def to_canonical(raw: dict) -> Account:
        """Converte dict bruto Pierre → Account canônica."""
        return Account(
            id=uuid4(),
            external_id=raw["accountId"],
            provider=ProviderType.PIERRE,
            name=raw["accountName"],
            type=PierreAccountMapper._map_type(raw["accountType"]),
            currency_code=raw["accountCurrencyCode"],
            balance=Decimal(str(raw.get("accountBalance", 0))),
        )

    @staticmethod
    def to_canonical_list(raw_list: list[dict]) -> list[Account]:
        return [PierreAccountMapper.to_canonical(r) for r in raw_list]

    @staticmethod
    def _map_type(pierre_type: str) -> AccountType:
        mapping = {
            "BANK": AccountType.BANK,
            "CREDIT": AccountType.CREDIT_CARD,
            "INVESTMENT": AccountType.INVESTMENT,
        }
        return mapping.get(pierre_type, AccountType.OTHER)
```
