from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.api.dependencies.legacy_financial import require_certified_legacy_financial_scope
from backend.domains.pierre.pipeline import PierreImportPipeline
from backend.application.services.local_ledger_scope import CertifiedLedgerScope, LedgerScopeDenied

router = APIRouter(
    prefix="/pierre", tags=["Pierre Integration"],
    dependencies=[Depends(require_certified_legacy_financial_scope)],
)

class ImportRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@router.post("/import")
async def import_pierre_data(
    request: ImportRequest,
    scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope),
):
    try:
        pipeline = PierreImportPipeline(scope)
        result = await pipeline.run(start_date=request.start_date, end_date=request.end_date)
        
        return {"success": True, **result}
    except LedgerScopeDenied:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail="Importação recusada: dados incompletos ou inconsistentes") from None
    except Exception:
        raise HTTPException(status_code=502, detail="Importação não concluída; nenhuma gravação financeira foi confirmada") from None
