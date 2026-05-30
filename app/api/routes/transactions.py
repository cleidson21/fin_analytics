from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.transactions import ReclassificationRequest, TransactionItem, TransactionListResponse, TransactionSummary
from app.api.validators import validate_date
from database.queries import FinancialQueries


router = APIRouter()
queries = FinancialQueries()


@router.get("", response_model=TransactionListResponse)
def get_transactions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    start_date: str | None = Query(None, alias="startDate", description="Data inicial YYYY-MM-DD"),
    end_date: str | None = Query(None, alias="endDate", description="Data final YYYY-MM-DD"),
    account: str | None = Query(None, description="Conta/source a filtrar"),
    category: str | None = Query(None, description="Categoria/macro_categoria a filtrar"),
    natureza: str | None = Query(None, description="Natureza a filtrar"),
):
    """Retorna uma lista paginada de transações com filtros reais no servidor."""
    if start_date:
        validate_date(start_date)

    if end_date:
        validate_date(end_date)

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="startDate não pode ser maior que endDate")

    df, total = queries.get_transactions(
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date,
        account=account,
        category=category,
        natureza=natureza,
    )
    summary = queries.get_transactions_summary(
        start_date=start_date,
        end_date=end_date,
        account=account,
        category=category,
        natureza=natureza,
    )
    if df.empty:
        return TransactionListResponse(
            items=[],
            total=total,
            limit=limit,
            offset=offset,
            total_pages=0,
            summary=TransactionSummary(**summary),
        )

    records = df.to_dict(orient="records")
    items = [
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

    total_pages = queries.get_transactions_total_pages(total, limit)
    return TransactionListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        total_pages=total_pages,
        summary=TransactionSummary(**summary),
    )


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
