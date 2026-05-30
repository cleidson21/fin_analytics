from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TransactionItem(BaseModel):
    id: str
    date: date
    description: str
    category: str
    natureza: str
    subnatureza: str
    account: str
    amount: Decimal


class ReclassificationRequest(BaseModel):
    macro_categoria: str
    natureza: str | None = None
    subnatureza: str | None = None


class AccountSummary(BaseModel):
    institution: str
    balance: Decimal


class TransactionSummary(BaseModel):
    income: float
    expense: float
    balance: float


class TransactionListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[TransactionItem]
    total: int
    limit: int
    offset: int
    total_pages: int = Field(alias="totalPages")
    summary: TransactionSummary
