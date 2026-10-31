"""Run access is operational authorship, separately from financial ownership."""
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from backend.application.services.local_ledger_scope import DENIED, LedgerScopeDenied, resolve_scope
from backend.database.session import SessionLocal
from backend.domain.enums.provider_type import ProviderType
from backend.infrastructure.persistence.models.sync_log import SyncLogModel


def run_owner_values(user_id) -> tuple[str, str]:
    owner = UUID(str(user_id))
    return str(owner), owner.hex


def require_pierre_history(user_id) -> None:
    try:
        with SessionLocal() as db:
            db.execute(text("BEGIN"))
            resolve_scope(db, user_id, "history")
    except (LedgerScopeDenied, OSError):
        raise HTTPException(status_code=403, detail=DENIED) from None
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Certificação financeira temporariamente indisponível") from None


async def require_history_for_owned_pierre_runs(session, user_id) -> None:
    result = await session.execute(select(SyncLogModel.id).where(
        func.lower(SyncLogModel.user_id).in_(run_owner_values(user_id)),
        SyncLogModel.provider == ProviderType.PIERRE,
    ).limit(1))
    if result.first() is not None:
        require_pierre_history(user_id)


def require_owned_run(log, user_id) -> None:
    try:
        matches = log is not None and UUID(log.user_id) == UUID(str(user_id))
    except (ValueError, TypeError, AttributeError):
        matches = False
    if not matches:
        raise HTTPException(status_code=404, detail="Run não encontrado")
    if log.provider == ProviderType.PIERRE:
        require_pierre_history(user_id)
