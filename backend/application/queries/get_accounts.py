from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from backend.domain.enums.account_type import AccountType
from backend.domain.enums.provider_type import ProviderType

@dataclass(frozen=True)
class GetAccountsQuery:
    user_id: UUID
    type: Optional[AccountType] = None
    is_active: Optional[bool] = None
    provider: Optional[ProviderType] = None
