from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List
from datetime import datetime

from app.schemas.dashboard import PacingComparison, PacingV2, DashboardSummary
from app.services.core_finance.cashflow import CashflowService
from app.core.dependencies import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def get_current_month() -> str:
    return datetime.now().strftime("%Y-%m")

@router.get("/pacing", response_model=PacingComparison)
def get_expense_pacing(
    month: str = Query(..., description="Filtro de mês YYYY-MM"),
    db: Session = Depends(get_db)
):
    """Retorna o Ritmo de Gastos inteligente (MoM) para o frontend."""
    cashflow_service = CashflowService(db)
    return cashflow_service.get_expense_pacing(month)

@router.get("/pacing-v2", response_model=PacingV2)
def get_pacing_v2(
    month: Optional[str] = Query(None, description="Filtro opcional de mês YYYY-MM"),
    db: Session = Depends(get_db)
):
    valid_month = month if month else get_current_month()
    cashflow_service = CashflowService(db)
    return cashflow_service.get_pacing_v2(valid_month)

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    month: Optional[str] = Query(None, description="Filtro opcional de mês YYYY-MM"),
    db: Session = Depends(get_db)
):
    # This will be fully implemented when Wealth is ready.
    # For BE-02A we return basic Cashflow info.
    valid_month = month if month else get_current_month()
    year, month_number = map(int, valid_month.split("-"))
    
    cashflow_service = CashflowService(db)
    expenses = cashflow_service._get_expenses_sum(year, month_number)
    income = cashflow_service._get_income_sum(year, month_number)
    
    return DashboardSummary(
        net_worth="R$ 0,00", # Requires Wealth
        income=cashflow_service._format_money(income),
        expenses=cashflow_service._format_money(expenses),
        balance=cashflow_service._format_money(income - expenses)
    )