from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict
from uuid import UUID, uuid4

from backend.domain.enums.provider_type import ProviderType
from backend.domain.enums.transaction_type import TransactionType
from backend.domain.enums.transaction_status import TransactionStatus
from backend.domain.enums.movement_type import MovementType

@dataclass(kw_only=True)
class Transaction:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID
    provider: ProviderType
    account_id: UUID
    amount: Decimal
    direction: MovementType
    currency_code: str
    description: str
    type: TransactionType
    status: TransactionStatus
    transaction_date: date
    is_recurring: bool
    hash: str
    
    external_id: Optional[str] = None
    original_description: Optional[str] = None
    category_id: Optional[UUID] = None
    posted_date: Optional[date] = None
    installment_count: Optional[int] = None
    installment_current: Optional[int] = None
    purchase_id: Optional[UUID] = None
    provider_metadata: Optional[Dict] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    def __post_init__(self):
        """Valida invariantes de parcelamento.
        - `installment_current` nunca pode ser maior que `installment_count`.
        - Ambos podem ser `None` (caso não seja parcelamento).
        """
        if (self.installment_count is not None and self.installment_current is not None):
            if self.installment_current > self.installment_count:
                raise ValueError("installment_current cannot exceed installment_count")
