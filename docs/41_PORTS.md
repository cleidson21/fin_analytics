> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Ports (Interfaces) — FIN Analytics

Ports são contratos (interfaces abstratas) que a camada Application define e que a camada Infrastructure implementa. A Application NUNCA importa implementações concretas — apenas Ports.

---

## Repository Ports

### ITransactionRepository
```
async def create(transaction: Transaction) -> Transaction
async def bulk_create(transactions: list[Transaction]) -> list[Transaction]
async def get_by_id(id: UUID) -> Transaction | None
async def get_by_hash(hash: str) -> Transaction | None
async def get_by_external_id(external_id: str, provider: ProviderType) -> Transaction | None
async def list(user_id: UUID, filters: TransactionFilters) -> PaginatedResult[Transaction]
async def update_category(id: UUID, category_id: UUID) -> Transaction
async def soft_delete(id: UUID) -> None
async def count_unclassified(user_id: UUID) -> int
async def get_active_subscriptions(user_id: UUID, start_date: date, end_date: date) -> list[Transaction]
async def get_active_installments(user_id: UUID) -> list[Transaction]
```

### IAccountRepository
```
async def create(account: Account) -> Account
async def get_by_id(id: UUID) -> Account | None
async def get_by_external_id(external_id: str, provider: ProviderType) -> Account | None
async def list(user_id: UUID, filters: AccountFilters) -> list[Account]
async def update_balance(id: UUID, balance: Decimal, updated_at: datetime) -> Account
async def upsert(account: Account) -> Account   # create or update by external_id+provider
```

### IPortfolioRepository
```
async def create(portfolio: Portfolio) -> Portfolio
async def get_by_id(id: UUID) -> Portfolio | None
async def list(user_id: UUID) -> list[Portfolio]
async def get_default(user_id: UUID) -> Portfolio
```

### IPositionRepository
```
async def create(position: Position) -> Position
async def bulk_create(positions: list[Position]) -> list[Position]
async def get_latest(asset_id: UUID, portfolio_id: UUID) -> Position | None
async def list(portfolio_id: UUID, filters: PositionFilters) -> list[Position]
async def update_price(asset_id: UUID, current_price: Decimal) -> None
```

### IDividendRepository
```
async def create(dividend: Dividend) -> Dividend
async def bulk_create(dividends: list[Dividend]) -> list[Dividend]
async def get_by_id(id: UUID) -> Dividend | None
async def list(user_id: UUID, filters: DividendFilters) -> PaginatedResult[Dividend]
async def sum_by_period(portfolio_id: UUID, date_range: DateRange) -> Decimal
```

### IAssetRepository
```
async def create(asset: Asset) -> Asset
async def get_by_id(id: UUID) -> Asset | None
async def get_by_ticker(ticker: str, exchange: str) -> Asset | None
async def list(filters: AssetFilters) -> list[Asset]
async def upsert(asset: Asset) -> Asset
async def update_price(id: UUID, price: Decimal) -> None
```

### ICategoryRepository
```
async def create(category: Category) -> Category
async def get_by_id(id: UUID) -> Category | None
async def get_by_slug(slug: str) -> Category | None
async def list(user_id: UUID, include_system: bool) -> list[Category]
async def get_or_create_by_slug(slug: str, name: str) -> Category
```

### IUserRepository
```
async def create(user: User) -> User
async def get_by_id(id: UUID) -> User | None
async def get_by_email(email: str) -> User | None
async def update(user: User) -> User
async def update_last_login(id: UUID, at: datetime) -> None
```

### IInstitutionRepository
```
async def get_by_code(code: str) -> Institution | None
async def get_or_create(code: str, name: str) -> Institution
async def list() -> list[Institution]
```

### IProviderRepository
```
async def create(provider: Provider) -> Provider
async def get_by_id(id: UUID) -> Provider | None
async def get_by_user_and_type(user_id: UUID, type: ProviderType) -> Provider | None
async def list(user_id: UUID) -> list[Provider]
async def update_status(id: UUID, status: ProviderStatus) -> Provider
async def update_sync(id: UUID, sync_status: SyncStatus, last_sync_at: datetime) -> Provider
```

---

## Provider Ports

### IPierreProvider
```
get_accounts() -> list[dict]              # Raw Pierre JSON
get_balance() -> dict
get_balance_by_account(account_id: str) -> dict
get_transactions(params: PierreTransactionParams) -> list[dict]
get_installments(params: DateRangeParams) -> list[dict]
get_bills(account_id: str | None) -> list[dict]
get_bill_summary(params: BillSummaryParams) -> dict
manual_update() -> dict
get_open_finance_connection_flow() -> dict
test_connection() -> bool
```

> **Nota:** Todos os retornos são `dict` brutos (JSON Pierre). O Mapper converte para Canônico.

### IMyProfitProvider
```
authenticate(session_cookies: dict) -> bool
get_positions() -> list[dict]
get_dividends(params: DividendParams) -> list[dict]
get_portfolio_summary() -> dict
export_csv(resource: str) -> bytes
test_connection() -> bool
```

### IYFinanceProvider
```
get_quote(ticker: str) -> dict
get_quotes(tickers: list[str]) -> list[dict]
get_history(ticker: str, period: str, interval: str) -> list[dict]
get_asset_info(ticker: str) -> dict
```

### IGeminiProvider
```
classify_transaction(description: str, amount: Decimal, categories: list[str]) -> str
generate_insights(context: str) -> str
chat(messages: list[dict]) -> str
```

### INotificationProvider
```
send_email(to: str, subject: str, body: str) -> bool
send_whatsapp(to: str, message: str) -> bool
```

---

## Infrastructure Ports

### IPasswordHasher
```
hash_password(password: str) -> str
verify_password(plain_password: str, hashed_password: str) -> bool
```

### IJWTService
```
create_access_token(user_id: str) -> str
create_refresh_token(user_id: str) -> str
decode_token(token: str) -> dict
verify_token(token: str) -> dict
```

### ICache
```
get(key: str) -> Any | None
set(key: str, value: Any, ttl_seconds: int) -> None
delete(key: str) -> None
exists(key: str) -> bool
```

### ILogger
```
debug(message: str, **kwargs) -> None
info(message: str, **kwargs) -> None
warning(message: str, **kwargs) -> None
error(message: str, **kwargs) -> None
critical(message: str, **kwargs) -> None
```

### IStorage
```
save(path: str, content: bytes) -> str   # returns final path
load(path: str) -> bytes
delete(path: str) -> None
exists(path: str) -> bool
```

### ISecrets
```
get(key: str) -> str | None
```
> **Regra:** Apenas `ISecrets` pode acessar API Keys, senhas e tokens. Nunca acessar via os.environ diretamente nos Use Cases.

### IClock
```
now() -> datetime
today() -> date
utcnow() -> datetime
```
> **Regra:** Use Cases nunca chamam `datetime.now()` diretamente — sempre via `IClock`. Facilita testes unitários.

### IEventBus
```
publish(event: DomainEvent) -> None
subscribe(event_type: type, handler: Callable) -> None
```

### IScheduler
```
schedule(job_id: str, cron: str, command: Command) -> None
cancel(job_id: str) -> None
list_jobs() -> list[ScheduledJobDTO]
```

---

## Regra Geral de Ports

1. A Application define Ports como **classes abstratas (ABC)**.
2. A Infrastructure implementa os Ports como **classes concretas**.
3. O wiring (bind interface → implementação) ocorre no **Container de DI** — nunca nos Use Cases.
4. Um Provider Port nunca retorna entidade de domínio — retorna `dict` bruto para que o Mapper converta.
5. Repository Ports nunca recebem SQL ou queries — apenas objetos do domínio e filtros tipados.
