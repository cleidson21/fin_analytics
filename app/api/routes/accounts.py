from fastapi import APIRouter

from app.api.schemas.transactions import AccountSummary
from app.core.formatters import format_money
from database.queries import FinancialQueries


router = APIRouter()
queries = FinancialQueries()


@router.get("/summary", response_model=list[AccountSummary])
def get_accounts_summary():
    """Retorna o saldo agregado por instituição/conta."""
    records = queries.get_accounts_summary()
    if not records:
        return []

    return [
        AccountSummary(
            institution=r["institution"],
            balance=format_money(r["balance"]),
        )
        for r in records
    ]
