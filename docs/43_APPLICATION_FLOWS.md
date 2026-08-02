> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Fluxos da Aplicação — FIN Analytics

---

## Fluxo 1: Login (AuthenticateUser)

```
[Frontend]
    |
    POST /api/v1/auth/login
    { email, password }
    |
[API Router]
    |
    AuthenticateUserCommand(email, password)
    |
[Use Case: AuthenticateUser]
    |---> IUserRepository.get_by_email(email)
    |         -> User ou None (404)
    |---> verify_password(password, user.hashed_password)
    |         -> False → 401 Unauthorized
    |---> ISecrets.get("JWT_SECRET")
    |---> generate_access_token(user)
    |---> generate_refresh_token(user)
    |---> IUserRepository.update_last_login(user.id)
    |
    return AuthTokenDTO
    |
[API Router]
    |
    200 { access_token, refresh_token, ... }
```

---

## Fluxo 2: Sincronização Pierre (Completa)

```
[Trigger: manual / scheduler]
    |
    SyncPierreCommand(user_id)
    |
[Use Case: SyncPierreAccounts]
    |---> IProviderRepository.get_by_user_and_type(user_id, PIERRE)
    |         -> Provider.status == ACTIVE?
    |---> ISecrets.get("PIERRE_API_KEY")
    |---> IPierreProvider.get_accounts()
    |         -> list[dict] (raw Pierre JSON)
    |---> PierreAccountMapper.to_canonical(raw) -> list[Account]
    |---> for each account:
    |         IAccountRepository.upsert(account)
    |         IInstitutionRepository.get_or_create(provider_code)
    |---> IProviderRepository.update_sync(PIERRE, SUCCESS, now)
    |---> IEventBus.publish(SyncFinished)
    |
[Use Case: SyncPierreTransactions]
    |---> IAccountRepository.list(user_id, provider=PIERRE)
    |---> IPierreProvider.get_transactions(params)
    |         -> list[dict]
    |---> PierreTransactionMapper.to_canonical(raw) -> list[Transaction]
    |---> for each transaction:
    |         hash = calculate_hash(tx)
    |         existing = ITransactionRepository.get_by_hash(hash)
    |         if existing: skip (++skipped)
    |         else: ITransactionRepository.create(tx) (++created)
    |         if tx.category_id is None: enqueue ClassifyTransactionCommand
    |---> IEventBus.publish(TransactionImported)
    |---> IEventBus.publish(SyncFinished)
```

---

## Fluxo 3: Sincronização MyProfit

```
[Trigger: manual / scheduler]
    |
    SyncMyProfitCommand(user_id)
    |
[Use Case: SyncMyProfitPortfolio]
    |---> IProviderRepository.get_by_user_and_type(user_id, MYPROFIT)
    |---> ISecrets.get("MYPROFIT_SESSION_COOKIES")
    |---> IMyProfitProvider.authenticate(cookies)
    |         -> sessão expirada? -> IEventBus.publish(SyncFailed)
    |                              -> notificar usuário para reautenticar
    |---> IMyProfitProvider.get_positions()
    |         -> list[dict]
    |---> MyProfitPositionMapper.to_canonical(raw) -> list[Position, Asset]
    |---> for each asset: IAssetRepository.upsert(asset)
    |---> IPortfolioRepository.get_default(user_id)
    |---> for each position: IPositionRepository.create(position)  # sempre cria novo snapshot
    |---> IMyProfitProvider.get_dividends(params)
    |---> MyProfitDividendMapper.to_canonical(raw) -> list[Dividend]
    |---> for each dividend:
    |         existing = IDividendRepository.get_by_hash(hash)
    |         if not existing: IDividendRepository.create(dividend)
    |---> IEventBus.publish(PortfolioUpdated)
    |---> IEventBus.publish(DividendReceived)
    |---> IEventBus.publish(SyncFinished)
```

---

## Fluxo 4: Atualização de Cotações (YFinance)

```
[Trigger: scheduler 30min / manual]
    |
    RefreshQuotesCommand(user_id)
    |
[Use Case: SyncYFinanceQuotes]
    |---> IPositionRepository.list(portfolio_id, active_only=True)
    |---> tickers = [p.asset.ticker for p in positions]
    |---> IYFinanceProvider.get_quotes(tickers)
    |         -> list[dict]
    |---> for each quote:
    |         IAssetRepository.update_price(asset_id, price)
    |         IPositionRepository.update_price(asset_id, price)
    |---> IEventBus.publish(PortfolioUpdated)
```

---

## Fluxo 5: Importação CSV

```
[Frontend]
    |
    POST /api/v1/import/csv
    { file, csv_type, confirm=false }
    |
[Use Case: ImportCSV] (PREVIEW MODE)
    |---> parse_csv(file_bytes, encoding, delimiter)
    |---> validate_headers(rows, csv_type)
    |         -> headers inválidos? -> 422 com lista de erros
    |---> CsvMapper.to_canonical(rows) -> list[Transaction | Dividend]
    |         -> erros por linha: acumular em errors[]
    |---> return ImportResultDTO(preview=first_10, total, errors)
    |
[Frontend] exibe preview → usuário confirma
    |
    POST /api/v1/import/csv
    { file, csv_type, confirm=true }
    |
[Use Case: ImportCSV] (PERSIST MODE)
    |---> repeat parsing + mapping
    |---> for each entity:
    |         hash check -> skip se duplicado
    |         create
    |---> IEventBus.publish(TransactionImported)
    |---> return ImportResultDTO(imported, skipped, errors)
```

---

## Fluxo 6: Pipeline de Classificação IA

```
[Trigger: evento TransactionImported / comando manual]
    |
    ClassifyTransactionCommand(transaction_ids=[...])
    |
[Use Case: ClassifyTransaction]
    |---> ICategoryRepository.list(user_id, include_system=True)
    |         -> list[Category] com names
    |---> for each transaction_id:
    |         tx = ITransactionRepository.get_by_id(id)
    |         if tx.category_id is not None and not override: skip
    |         category_name = IGeminiProvider.classify_transaction(
    |             description=tx.description,
    |             amount=tx.amount,
    |             categories=[c.name for c in categories]
    |         )
    |         category = ICategoryRepository.get_or_create_by_slug(
    |             slug=slugify(category_name),
    |             name=category_name
    |         )
    |         ITransactionRepository.update_category(tx.id, category.id)
    |         IEventBus.publish(CategoryClassified(method="ai"))
    |---> return ClassificationResultDTO
```

---

## Fluxo 7: Dashboard

```
[Frontend]
    |
    GET /api/v1/dashboard?period=last_30_days
    |
[Use Case: GetDashboard]
    |---> ICache.get("dashboard:{user_id}:{period}")
    |         -> cache hit? return cached DashboardDTO
    |
    |---> IAccountRepository.list(user_id, is_active=True)
    |---> ITransactionRepository.list(user_id, filters=period)
    |---> IPositionRepository.list(portfolio_id)       # latest snapshot
    |---> IDividendRepository.sum_by_period(portfolio_id, period)
    |
    |---> calculate totals, categories, cash_flow
    |---> build DashboardDTO
    |
    |---> ICache.set("dashboard:{user_id}:{period}", dto, ttl=300)
    |
    return DashboardDTO
```
