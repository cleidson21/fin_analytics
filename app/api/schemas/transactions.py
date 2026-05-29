from datetime import date
from decimal import Decimal

from pydantic import BaseModel


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
