from fastapi import APIRouter

from app.api.schemas.transactions import AccountSummary
from app.core.formatters import format_money
from database.queries import FinancialQueries


router = APIRouter()
queries = FinancialQueries()


@router.get("/summary", response_model=list[AccountSummary])
def get_accounts_summary():
    """Retorna o saldo agregado por instituição/conta."""
    df = queries.get_accounts_summary()
    if df.empty:
        return []

    records = df.to_dict(orient="records")
    return [
        AccountSummary(
            institution=r["institution"],
            balance=format_money(r["balance"]),
        )
        for r in records
    ]
