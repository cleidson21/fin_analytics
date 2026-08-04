"""
Sprint 2 — Read Models
Expõe os dados persistidos no SQLite para o Frontend.
Nenhuma regra de negócio. Apenas leitura.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from backend.domains.pierre.service import (
    AccountService,
    TransactionService,
    CategoryService,
)
from backend.database.session import SessionLocal
from backend.domains.pierre.models import Transaction

router = APIRouter(tags=["Read Models"])


# ──────────────────────────── Response Schemas ──────────────────────────────

class AccountOut(BaseModel):
    provider: str
    external_id: str
    name: str
    type: str
    subtype: Optional[str] = None
    bank: Optional[str] = None
    connector: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionOut(BaseModel):
    provider: str
    external_id: str
    account_external_id: str
    description: str
    original_description: Optional[str] = None
    category: Optional[str] = None
    original_category: Optional[str] = None
    amount: Decimal
    currency: str
    date: datetime
    status: str
    type: str
    merchant_name: Optional[str] = None
    manual_transaction: bool

    class Config:
        from_attributes = True


class CategoryOut(BaseModel):
    provider: str
    name: str
    normalized_name: Optional[str] = None

    class Config:
        from_attributes = True


class DashboardOut(BaseModel):
    total_accounts: int
    total_categories: int
    total_transactions: int
    total_amount: Decimal


# ──────────────────────────────── Endpoints ─────────────────────────────────

@router.get("/accounts", response_model=List[AccountOut])
def list_accounts():
    service = AccountService()
    return service.list_all()


@router.get("/transactions", response_model=List[TransactionOut])
def list_transactions():
    service = TransactionService()
    return service.list_all()


@router.get("/categories", response_model=List[CategoryOut])
def list_categories():
    service = CategoryService()
    return service.list_all()


@router.get("/dashboard", response_model=DashboardOut)
def dashboard_summary():
    account_service = AccountService()
    transaction_service = TransactionService()
    category_service = CategoryService()

    accounts = account_service.list_all()
    categories = category_service.list_all()

    # Total amount calculated in-process from already-fetched transactions
    with SessionLocal() as db:
        from sqlalchemy import func
        total_tx = db.query(func.count(Transaction.external_id)).scalar() or 0
        total_amount = db.query(func.sum(Transaction.amount)).scalar() or Decimal("0")

    return DashboardOut(
        total_accounts=len(accounts),
        total_categories=len(categories),
        total_transactions=total_tx,
        total_amount=Decimal(str(total_amount)),
    )
