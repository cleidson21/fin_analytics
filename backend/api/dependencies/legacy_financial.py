"""Authenticate first, then resolve the explicitly certified personal ledger."""

from fastapi import Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.services.local_ledger_scope import (
    CertifiedLedgerScope, DENIED, LedgerScopeDenied, resolve_scope,
)
from backend.database.session import SessionLocal
from backend.core.config import settings


def requested_capability(request: Request) -> str:
    # Authorization follows the server-resolved operation, never an encoded URL
    # spelling or a caller-supplied selector. Both import routes have this name.
    operation = request.scope["route"].name
    if operation == "import_pierre_data":
        return "import"
    if operation in {"classify_transaction", "rollback_to_event"}:
        return "governance.write"
    if operation in {"get_history", "get_global_audit_log"}:
        return "history"
    if request.method == "GET":
        return "read"
    raise LedgerScopeDenied(DENIED)


def require_certified_legacy_financial_scope(
    request: Request,
    current_user: UserResponseDTO = Depends(get_current_user),
):
    if not settings.LOCAL_LEDGER_ENABLED or settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=403, detail=DENIED)
    with SessionLocal() as db:
        try:
            # Explicit SQLite read transaction, shared with the guarded handler.
            db.execute(text("BEGIN"))
            cert = resolve_scope(db, current_user.id, requested_capability(request))
            yield CertifiedLedgerScope(db, cert)
        except (LedgerScopeDenied, OSError):
            db.rollback()
            raise HTTPException(status_code=403, detail=DENIED) from None
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(status_code=503, detail="Certificação financeira temporariamente indisponível") from None
