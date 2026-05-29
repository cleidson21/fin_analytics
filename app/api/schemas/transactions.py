from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TransactionItem(BaseModel):
    date: date
    description: str
    category: str
    account: str
    amount: Decimal


class AccountSummary(BaseModel):
    institution: str
    balance: Decimal
