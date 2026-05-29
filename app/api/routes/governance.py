from decimal import Decimal

from fastapi import APIRouter

from app.api.schemas.governance import QuarantineTransaction
from database.queries import FinancialQueries


router = APIRouter()
queries = FinancialQueries()


@router.get("/quarantine", response_model=list[QuarantineTransaction])
def get_quarantine():
    """Retorna as transações pendentes de taxonomia (OUTROS/INDEFINIDO)."""
    df = queries.get_quarantine_transactions()
    if df.empty:
        return []

    df["data"] = df["data"].astype(str)
    records = df.to_dict(orient="records")

    for record in records:
        record["valor"] = Decimal(str(record["valor"]))

    return records