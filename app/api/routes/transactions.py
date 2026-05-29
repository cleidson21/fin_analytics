from fastapi import APIRouter, Query

from app.api.schemas.transactions import TransactionItem
from app.core.formatters import format_money
from database.queries import FinancialQueries


router = APIRouter()
queries = FinancialQueries()


@router.get("", response_model=list[TransactionItem])
def get_transactions(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    """Retorna uma lista paginada de transações."""
    df = queries.get_transactions(limit=limit, offset=offset)
    if df.empty:
        return []

    records = df.to_dict(orient="records")
    return [
        TransactionItem(
            date=r["data"],
            description=r["description"],
            category=r["category"],
            account=r["account"],
            amount=format_money(r["amount"]),
        )
        for r in records
    ]
