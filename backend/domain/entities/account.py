from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from backend.domain.enums.account_type import AccountType
from backend.domain.enums.currency_code import CurrencyCode
from backend.domain.enums.provider_type import ProviderType

@dataclass
class Account:
    id: UUID
    user_id: UUID
    external_id: str | None
    provider: ProviderType
    institution_id: UUID | None
    name: str
    type: AccountType
    subtype: str | None
    currency_code: CurrencyCode
    balance: Decimal | None
    balance_updated_at: datetime | None
    is_active: bool
    provider_code: str | None
    provider_metadata: dict | None
    created_at: datetime
    updated_at: datetime
