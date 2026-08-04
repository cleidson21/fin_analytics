> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

<<<<<<< HEAD
> [!CAUTION]
> **DOCUMENTO OBSOLETO — V3.1**
> Os DTOs definidos aqui foram projetados para um pipeline complexo que não existe mais na V3.1.
> Os contratos (schemas) agora vivem em `backend/domains/<domínio>/schemas.py` por domínio.
> Este arquivo é mantido apenas como referência histórica. Não implementar.

# DTOs — FIN Analytics (OBSOLETO)
=======
# DTOs — FIN Analytics
>>>>>>> 021d439dcbb06040c0005dbd27456a26c9f1d7e9

DTOs (Data Transfer Objects) trafegam entre camadas. Nunca contêm lógica. Nunca referenciam entidades do Provider.

---

## AuthTokenDTO (Response)
```
access_token: str
refresh_token: str
token_type: str       # "Bearer"
expires_in: int       # segundos
user: UserResponseDTO
```

---

## UserResponseDTO (Response)
```
id: UUID
email: str
name: str
role: UserRole
is_active: bool
is_verified: bool
created_at: datetime
last_login_at: datetime | None
```

---

## AccountResponseDTO (Response)
```
id: UUID
external_id: str | None
provider: ProviderType
name: str
type: AccountType
subtype: str | None
currency_code: CurrencyCode
balance: Decimal | None
balance_updated_at: datetime | None
institution: InstitutionSummaryDTO | None
is_active: bool
```

## InstitutionSummaryDTO (Internal)
```
id: UUID
name: str
code: str
logo_url: str | None
```

---

## TransactionResponseDTO (Response)
```
id: UUID
external_id: str | None
provider: ProviderType
account_id: UUID
account_name: str        # denormalizado para display
amount: Decimal
direction: MovementType
currency_code: CurrencyCode
description: str
category: CategorySummaryDTO | None
type: TransactionType
status: TransactionStatus
transaction_date: date
posted_date: date | None
is_recurring: bool
installment_count: int | None
installment_current: int | None
tags: list[TagDTO]
```

## CategorySummaryDTO (Internal)
```
id: UUID
name: str
slug: str
icon: str | None
color: str | None
```

## TagDTO (Response)
```
id: UUID
name: str
color: str | None
```

---

## AssetResponseDTO (Response)
```
id: UUID
ticker: str
exchange: str
name: str
type: AssetType
currency_code: CurrencyCode
sector: str | None
```

---

## PositionResponseDTO (Response)
```
id: UUID
asset: AssetResponseDTO
quantity: Decimal
avg_cost: Decimal
current_price: Decimal | None
current_value: Decimal | None
total_invested: Decimal
gain_loss: Decimal | None
gain_loss_pct: Decimal | None
snapshot_date: date
provider: ProviderType
```

---

## PortfolioResponseDTO (Response)
```
id: UUID
name: str
currency_code: CurrencyCode
total_invested: Decimal
current_value: Decimal | None
gain_loss: Decimal | None
gain_loss_pct: Decimal | None
positions: list[PositionResponseDTO]
allocation_by_type: dict[AssetType, Decimal]  # percentual
last_updated_at: datetime | None
```

---

## DividendResponseDTO (Response)
```
id: UUID
asset: AssetResponseDTO
type: IncomeType
amount_per_unit: Decimal
quantity: Decimal
gross_amount: Decimal
net_amount: Decimal | None
ir_withheld: Decimal | None
ex_date: date
payment_date: date | None
currency_code: CurrencyCode
provider: ProviderType
```

---

## DashboardDTO (Response)
```
period: DateRangeDTO
total_balance: Decimal
balance_by_account: list[AccountBalanceSummaryDTO]
total_income: Decimal
total_expense: Decimal
net_cash_flow: Decimal
top_categories: list[CategorySpendingDTO]
portfolio_summary: PortfolioSummaryDTO | None
dividends_received: Decimal
alerts_count: int
last_sync_at: datetime | None
```

## DateRangeDTO (Internal)
```
start: date
end: date
```

## AccountBalanceSummaryDTO (Internal)
```
account_id: UUID
account_name: str
balance: Decimal
currency_code: CurrencyCode
```

## CategorySpendingDTO (Internal)
```
category_id: UUID
category_name: str
total: Decimal
percentage: Decimal
```

## CategoryBreakdownDTO (Response)
```
category: str
total: Decimal
```

## PortfolioSummaryDTO (Internal)
```
total_invested: Decimal
current_value: Decimal
gain_loss_pct: Decimal
```

---

## CashFlowDTO (Response)
```
period: DateRangeDTO
group_by: str
items: list[CashFlowPeriodDTO]
totals: CashFlowTotalsDTO
```

## CashFlowPeriodDTO (Internal)
```
label: str          # "Jan 2024", "2024-01-15", etc.
income: Decimal
expense: Decimal
net: Decimal
```

## CashFlowTotalsDTO (Internal)
```
total_income: Decimal
total_expense: Decimal
total_net: Decimal
```

---

## PaginatedResponseDTO<T> (Generic Response)
```
data: list[T]
total: int
page: int
page_size: int
has_next: bool
has_prev: bool
```

---

## SyncResultDTO (Response)
```
provider: ProviderType
resource: str
started_at: datetime
finished_at: datetime
created: int
updated: int
skipped: int
errors: list[SyncErrorDTO]
status: SyncStatus
```

## SyncErrorDTO (Internal)
```
external_id: str | None
message: str
details: dict | None
```

---

## ImportResultDTO (Response)
```
csv_type: str
total_rows: int
imported: int
skipped: int
errors: list[ImportErrorDTO]
preview: list[TransactionResponseDTO]   # somente quando confirm=False
```

## ImportErrorDTO (Internal)
```
row: int
message: str
raw_data: dict
```

---

## ProviderResponseDTO (Response)
```
id: UUID
type: ProviderType
status: ProviderStatus
last_sync_at: datetime | None
sync_status: SyncStatus | None
error_message: str | None
created_at: datetime
```

---

## AlertDTO (Response)
```
id: str
type: str            # "spending_limit" | "payment_reminder"
title: str
message: str
severity: str        # "info" | "warning" | "critical"
created_at: datetime
metadata: dict | None
```

---

## InsightDTO (Response)
```
id: UUID
title: str
content: str
type: str            # "tip" | "alert" | "analysis"
confidence: Decimal  # 0.0 a 1.0
generated_at: datetime
period: DateRangeDTO | None
```

---

## CategoryResponseDTO (Response)
```
id: UUID
name: str
slug: str
parent_id: UUID | None
icon: str | None
color: str | None
is_system: bool
children: list[CategoryResponseDTO]  # hierárquico
```

---

## OperationResultDTO (Response)
```
success: bool
message: str
details: dict | None
```

---

## SubscriptionsSummaryDTO (Response)
```
month: str
active_count: int
monthly_total: Decimal
annual_projection: Decimal
average_per_service: Decimal
items: list[SubscriptionItemDTO]
```

## SubscriptionItemDTO (Internal)
```
original_name: str
date: str
amount: Decimal
```

---

## InstallmentsSummaryDTO (Response)
```
month: str
active_installments: int
finished_installments: int
global_estimated: Decimal
global_paid: Decimal
global_remaining: Decimal
last_installment_date: str | None
items: list[InstallmentItemDTO]
```

## InstallmentItemDTO (Internal)
```
purchase_id: UUID | str
base_name: str
original_name: str
date: str
installment_amount: Decimal
current_installment: int
first_installment_found: int
total_installments: int      # Frontend alias para installment_count
total_estimated: Decimal
already_paid: Decimal
remaining: Decimal
projected_end_date: str | None
is_active: bool
```

---

## Regras Gerais de DTOs

1. DTOs nunca importam entidades do Provider.
2. DTOs de Request validam seus próprios campos (Pydantic v2).
3. DTOs de Response nunca expõem campos internos como `hashed_password`, `deleted_at`.
4. DTOs de Internal existem apenas dentro da Application — nunca chegam ao Router.
5. Todos os campos monetários usam `Decimal` — nunca `float`.
6. Todos os campos de data seguem ISO 8601.
