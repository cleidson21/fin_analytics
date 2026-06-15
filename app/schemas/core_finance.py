from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# --- Domain DTOs ---

class CategoryBase(BaseModel):
    name: str
    category_type: str
    parent_id: Optional[str] = None

class SubscriptionBase(BaseModel):
    name: str
    category_id: str
    expected_amount_cents: int
    billing_cycle: str = 'MONTHLY'
    active: int = 1

class GoalBase(BaseModel):
    category_id: str
    limit_cents: int
    severity_level: str = 'WARNING'
    active: int = 1

class TransactionBase(BaseModel):
    id_economico: str
    source: str
    import_run_id: str
    data: date
    descricao_original: str
    descricao_normalizada: str
    valor: float
    natureza: str
    perfil: str

# --- Request DTOs ---

class CategoryCreate(CategoryBase):
    pass

class SubscriptionCreate(SubscriptionBase):
    pass

class GoalCreate(GoalBase):
    pass

class TransactionCreate(TransactionBase):
    category_id: Optional[str] = None
    subnatureza: str = 'INDEFINIDO'

# --- Response DTOs ---

class CategoryResponse(CategoryBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class SubscriptionResponse(SubscriptionBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class GoalResponse(GoalBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class TransactionResponse(TransactionBase):
    category_id: Optional[str]
    criado_em: datetime
    class Config:
        from_attributes = True
