from pydantic import BaseModel
from typing import Optional, List

class InstallmentItem(BaseModel):
    id: str
    description: str
    amount: float
    installment_number: int
    total_installments: int
    merchant_name: Optional[str] = None
    expected_date: str
    status: str

class InstallmentsDashboardDTO(BaseModel):
    month: str
    active_installments: int
    finished_installments: int
    global_estimated: float
    items: List[InstallmentItem]

class SubscriptionItem(BaseModel):
    id: str
    description: str
    amount: float
    category: str
    merchant_name: Optional[str] = None

class SubscriptionsDashboardDTO(BaseModel):
    month: str
    active_count: int
    monthly_total: float
    annual_projection: float
    items: List[SubscriptionItem]
