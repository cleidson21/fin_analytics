from decimal import Decimal
import hashlib

from fastapi import APIRouter

from app.api.schemas.governance import (
    ImportStatusResponse,
    PierreImportPreview,
    PierreImportRequest,
    PierreImportResponse,
    QuarantineTransaction,
)
from app.api.services.pierre_parser import PierreParser
from database.repository import DatabaseManager
from database.queries import FinancialQueries


router = APIRouter()
queries = FinancialQueries()
repository = DatabaseManager()
parser = PierreParser()


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


@router.get("/import-status", response_model=ImportStatusResponse)
def get_import_status():
    """Retorna o estado operacional da importação do Pierre."""
    return queries.get_import_status()


@router.post("/import-pierre", response_model=PierreImportResponse)
def import_pierre(payload: PierreImportRequest):
    raw_text = payload.raw_text or ""
    checksum = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    run_id = repository.create_import_run(raw_text, checksum)
    staged_items = parser.parse(raw_text)
    repository.insert_staging_items(run_id, staged_items)
    processed_preview = repository.process_staging_to_transactions(run_id)

    preview_items = [
        {
            "date": str(item.get("date", "")),
            "description": str(item.get("description", "")),
            "amount": Decimal(str(item.get("amount", 0))),
            "status": str(item.get("status", "PENDING")),
        }
        for item in processed_preview[:5]
    ]

    return PierreImportResponse(
        run_id=run_id,
        preview=PierreImportPreview(items=preview_items),
    )