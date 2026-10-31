"""
Sprint 2 — Read Models
Expõe os dados persistidos no SQLite para o Frontend.
Nenhuma regra de negócio. Apenas leitura.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from backend.api.dependencies.legacy_financial import require_certified_legacy_financial_scope
from backend.application.services.local_ledger_scope import CertifiedLedgerScope
from backend.domains.pierre.service import (
    AccountService,
    TransactionService,
    CategoryService,
)
from backend.database.session import SessionLocal
from backend.domains.pierre.models import Account, Category, Transaction

router = APIRouter(
    tags=["Read Models"],
    dependencies=[Depends(require_certified_legacy_financial_scope)],
)


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
    transaction_count: int = 0

    class Config:
        from_attributes = True


class DashboardOut(BaseModel):
    total_accounts: int
    total_categories: int
    total_transactions: int
    total_amount: Decimal


# ──────────────────────────────── Endpoints ─────────────────────────────────

@router.get("/accounts", response_model=List[AccountOut])
def list_accounts(scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope)):
    return [AccountOut.model_validate(row) for row in scope.db.query(Account).all()]


@router.get("/transactions", response_model=List[TransactionOut])
def list_transactions(scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope)):
    return [TransactionOut.model_validate(row) for row in scope.db.query(Transaction).all()]


@router.get("/categories", response_model=List[CategoryOut])
def list_categories(scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope)):
    from sqlalchemy import func
    # Categories are RAW labels, not account FKs; both historical Pierre writers
    # used the same private label catalog even when their provider casing differed.
    counts = {name: count for name, count in scope.db.query(
        Transaction.category, func.count()
    ).group_by(Transaction.category).all()}
    return [CategoryOut.model_validate(row).model_copy(update={
        "transaction_count": counts.get(row.name, 0)
    }) for row in scope.db.query(Category).all()]


@router.get("/dashboard", response_model=DashboardOut)
def dashboard_summary(scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope)):
    accounts = scope.db.query(Account).all()
    categories = scope.db.query(Category).all()

    # Total amount calculated in-process from already-fetched transactions
    db = scope.db
    try:
        from sqlalchemy import func
        total_tx = db.query(func.count(Transaction.external_id)).scalar() or 0
        total_amount = db.query(func.sum(Transaction.amount)).scalar() or Decimal("0")
    finally:
        db.close()

    return DashboardOut(
        total_accounts=len(accounts),
        total_categories=len(categories),
        total_transactions=total_tx,
        total_amount=Decimal(str(total_amount)),
    )

