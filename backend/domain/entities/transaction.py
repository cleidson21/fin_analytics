from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict
from uuid import UUID, uuid4

@dataclass(kw_only=True)
class Transaction:
    id: UUID = field(default_factory=uuid4)
    provider: str
    account_id: UUID
    amount: Decimal
    direction: str  # 'CREDIT' or 'DEBIT'
    currency_code: str
    description: str
    type: str  # 'PURCHASE', 'TRANSFER', etc.
    status: str  # 'PENDING', 'CONFIRMED', 'CANCELLED'
    transaction_date: date
    is_recurring: bool
    hash: str
    
    external_id: Optional[str] = None
    original_description: Optional[str] = None
    category_id: Optional[UUID] = None
    posted_date: Optional[date] = None
    installment_count: Optional[int] = None
    installment_current: Optional[int] = None
    provider_metadata: Optional[Dict] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
