from fastapi import APIRouter, Query, Depends, HTTPException
from backend.api.dependencies.legacy_financial import require_certified_legacy_financial_scope
from backend.application.services.local_ledger_scope import CertifiedLedgerScope
from typing import Optional
from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO

router = APIRouter(tags=["Pierre Installments"], prefix="/installments")

@router.get("")
async def get_installments(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    current_user: UserResponseDTO = Depends(get_current_user),
    scope: CertifiedLedgerScope = Depends(require_certified_legacy_financial_scope),
):
    # Provider-global aggregates are not demonstrably limited to the reviewed
    # account set. Keep the proxy closed until that payload contract is approved.
    raise HTTPException(status_code=403, detail="Parcelamentos indisponíveis: escopo das contas do provedor ainda não certificado")
