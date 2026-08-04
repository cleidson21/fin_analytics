from dataclasses import dataclass
from typing import Optional
from datetime import date

@dataclass
class ProviderTransactionDTO:
    id: str
    account_id: str
    amount: float
    direction: str
    description: str
    transaction_date: date
    type: Optional[str] = None
    status: Optional[str] = None
    original_description: Optional[str] = None
    category: Optional[str] = None
    posted_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    currency_code: Optional[str] = None
    
    def effective_installment_count(self) -> Optional[int]:
        return None
        
    def effective_installment_current(self) -> Optional[int]:
        return None
        
    def effective_purchase_id(self) -> Optional[str]:
        return None

@dataclass
class ProviderAccountDTO:
    id: str
    name: str
    type: str
    currency_code: str
    status: str
