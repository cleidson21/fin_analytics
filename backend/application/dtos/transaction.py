from datetime import date
from decimal import Decimal
from typing import Optional, Dict
from uuid import UUID
from pydantic import BaseModel

class CategorySummaryDTO(BaseModel):
    id: UUID
    name: str
    slug: str
    icon: Optional[str] = None
    color: Optional[str] = None

class TransactionResponseDTO(BaseModel):
    id: UUID
    external_id: Optional[str] = None
    provider: str
    account_id: UUID
    account_name: str
    amount: Decimal
    direction: str
    currency_code: str
    description: str
    category: Optional[CategorySummaryDTO] = None
    type: str
    status: str
    transaction_date: date
    posted_date: Optional[date] = None
    is_recurring: bool
    installment_count: Optional[int] = None
    installment_current: Optional[int] = None
    tags: list = []

class UpdateTransactionCategoryDTO(BaseModel):
    macro_categoria: str
    natureza: str
    subnatureza: str

class CategoryBreakdownDTO(BaseModel):
    category: str
    total: Decimal

class KpiItemDTO(BaseModel):
    current: float
    previous: float
    delta_pct: float

class DashboardSummaryV2DTO(BaseModel):
    month: str
    receitas: KpiItemDTO
    despesas: KpiItemDTO
    saldo_liquido: KpiItemDTO
    patrimonio: KpiItemDTO
