from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from backend.domain.enums.account_type import AccountType
from backend.domain.enums.currency_code import CurrencyCode
from backend.domain.enums.provider_type import ProviderType
from backend.application.dtos.institution_summary_dto import InstitutionSummaryDTO

class AccountResponseDTO(BaseModel):
    id: UUID
    external_id: Optional[str] = None
    provider: ProviderType
    name: str
    type: AccountType
    subtype: Optional[str] = None
    currency_code: CurrencyCode
    balance: Optional[Decimal] = None
    balance_updated_at: Optional[datetime] = None
    institution: Optional[InstitutionSummaryDTO] = None
    is_active: bool
