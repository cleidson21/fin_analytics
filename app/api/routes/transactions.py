from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.transactions import ReclassificationRequest, TransactionItem
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
            id=r["id"],
            date=r["data"],
            description=r["description"],
            category=r["category"],
            natureza=r["natureza"],
            subnatureza=r["subnatureza"],
            account=r["account"],
            amount=r["amount"],
        )
        for r in records
    ]


@router.patch("/{transaction_id}/reclassify")
def reclassify_transaction(transaction_id: str, req: ReclassificationRequest):
    """Permite corrigir a taxonomia de um registo."""
    updated = queries.update_transaction_category(
        transaction_id=transaction_id,
        macro_categoria=req.macro_categoria,
        natureza=req.natureza,
        subnatureza=req.subnatureza,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    return {
        "status": "success",
        "message": f"Transação {transaction_id} reclassificada para {req.macro_categoria}",
    }
