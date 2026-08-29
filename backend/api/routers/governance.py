from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, Query, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from datetime import datetime

from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.database import get_db_session
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.use_cases.governance import (
    GetGovernanceDashboardUseCase,
    GetGovernanceImportsUseCase,
    UploadImportUseCase
)
from backend.application.use_cases.confirm_myprofit_ativos import ConfirmMyProfitAtivosSyncUseCase
from backend.infrastructure.persistence.models.sync_log import SyncLogModel, SyncStatus
from backend.infrastructure.persistence.models.wealth.position_snapshot import PositionSnapshotModel
from backend.infrastructure.persistence.models.wealth.asset import AssetModel

router = APIRouter(prefix="/governance", tags=["Governance"])


class ConfirmImportRequest(BaseModel):
    account_id: str
    reference_date: str  # YYYY-MM-DD


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_governance_dashboard(
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    use_case = GetGovernanceDashboardUseCase(session)
    return await use_case.execute()


# ---------------------------------------------------------------------------
# Imports — lista e detalhe
# ---------------------------------------------------------------------------

@router.get("/imports", response_model=Dict[str, Any])
async def get_governance_imports(
    limit: int = Query(10),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    use_case = GetGovernanceImportsUseCase(session)
    return await use_case.execute(limit=limit)


@router.get("/imports/{run_id}", response_model=Dict[str, Any])
async def get_import_detail(
    run_id: str,
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna detalhes de uma importação específica."""
    result = await session.execute(
        select(SyncLogModel).where(SyncLogModel.id == run_id)
    )
    log = result.scalar_one_or_none()

    if log is None:
        raise HTTPException(status_code=404, detail="Run não encontrado")

    metadata = log.provider_metadata or {}
    parse_report = metadata.get("parse_report", {})
    staging_rows = metadata.get("staging_rows", [])

    return {
        "id": log.id,
        "source_type": metadata.get("source_type", log.provider.value if log.provider else ""),
        "file_name": metadata.get("filename", ""),
        "checksum": "",
        "started_at": log.start_time.isoformat() if log.start_time else "",
        "finished_at": log.end_time.isoformat() if log.end_time else None,
        "status": log.status.value if log.status else "UNKNOWN",
        "rows_read": parse_report.get("total_rows", len(staging_rows)),
        "rows_inserted": log.transactions_synced or 0,
        "rows_updated": 0,
        "rows_failed": 0,
        "created_by": log.user_id or "",
        "error_log": _build_error_log(parse_report),
        "preview_summary": None,
        # Campos extras para a UI de confirmação
        "account_id": metadata.get("confirmed_account_id"),
        "reference_date": metadata.get("confirmed_reference_date"),
        "report": metadata.get("confirmation_report"),
    }


def _build_error_log(parse_report: dict) -> Optional[str]:
    """Monta o JSON de log de erros/warnings para a UI."""
    if not parse_report:
        return None
    errors = parse_report.get("errors", [])
    warnings = parse_report.get("warnings", [])
    if not errors and not warnings:
        return None
    import json
    return json.dumps({
        "errors": errors,
        "warnings": warnings,
        "required_columns": parse_report.get("required_columns", []),
        "optional_columns": parse_report.get("optional_columns", []),
        "missing_columns": parse_report.get("missing_columns", []),
        "ignored_columns": parse_report.get("ignored_columns", []),
    })


@router.get("/imports/{run_id}/staging-items", response_model=Dict[str, Any])
async def get_staging_items(
    run_id: str,
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Retorna os itens de staging de uma importação (preview das linhas)."""
    result = await session.execute(
        select(SyncLogModel).where(SyncLogModel.id == run_id)
    )
    log = result.scalar_one_or_none()

    if log is None:
        raise HTTPException(status_code=404, detail="Run não encontrado")

    metadata = log.provider_metadata or {}
    staging_rows = metadata.get("staging_rows", [])
    source_type = metadata.get("source_type", "")

    items = []
    for i, row in enumerate(staging_rows):
        ticker = row.get("ticker", "")
        qty = row.get("quantity")
        sector = str(row.get("sector") or "").upper()
        is_rdb = sector == "RDB"
        is_valid = bool(ticker and (qty is not None or is_rdb))
        
        items.append({
            "source_line_no": i + 2,  # +2 porque linha 1 é header
            "ticker": ticker,
            "quantity": qty,
            "avg_price": row.get("avg_price"),
            "sector": row.get("sector"),
            "validation_status": "VALID" if is_valid else "ERROR",
            "validation_message": None if is_valid else "Ticker ou quantidade inválidos",
        })

    return {
        "run_id": run_id,
        "file_type": source_type,
        "items": items,
        "total": len(items),
    }


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@router.post("/imports/upload")
async def upload_import(
    source_type: str = Form(...),
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    if not file and not raw_text:
        raise HTTPException(status_code=400, detail="É necessário enviar um arquivo ou texto.")

    try:
        content = await file.read() if file else raw_text.encode('utf-8')
        filename = file.filename if file else "Pasted_Text"

        use_case = UploadImportUseCase(session)
        result = await use_case.execute(
            user_id=current_user.id,
            source_type=source_type,
            file_content=content,
            filename=filename
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Confirm
# ---------------------------------------------------------------------------

@router.post("/imports/{run_id}/confirm", response_model=Dict[str, Any])
async def confirm_import(
    run_id: str,
    body: ConfirmImportRequest,
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Confirma e persiste uma importação MYPROFIT_ATIVOS.
    Requer account_id e reference_date (YYYY-MM-DD).
    """
    try:
        use_case = ConfirmMyProfitAtivosSyncUseCase(session)
        report = await use_case.execute(
            run_id=run_id,
            account_id=body.account_id,
            reference_date=body.reference_date,
        )

        # Persiste account_id e reference_date no metadata para exibição futura
        result = await session.execute(select(SyncLogModel).where(SyncLogModel.id == run_id))
        log = result.scalar_one_or_none()
        if log and log.provider_metadata:
            meta = dict(log.provider_metadata)
            meta["confirmed_account_id"] = body.account_id
            meta["confirmed_reference_date"] = body.reference_date
            meta["confirmation_report"] = report
            log.provider_metadata = meta
            await session.commit()

        return {"success": True, "report": report}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno ao confirmar importação: {str(e)}")


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

@router.post("/imports/{run_id}/rollback", response_model=Dict[str, Any])
async def rollback_import(
    run_id: str,
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Marca uma importação como CANCELLED sem reverter dados já persistidos."""
    result = await session.execute(select(SyncLogModel).where(SyncLogModel.id == run_id))
    log = result.scalar_one_or_none()

    if log is None:
        raise HTTPException(status_code=404, detail="Run não encontrado")

    log.status = SyncStatus.FAILED
    log.end_time = datetime.utcnow()
    await session.commit()

    return {"success": True, "message": "Importação descartada."}


# ---------------------------------------------------------------------------
# Positions — leitura dos position_snapshots
# ---------------------------------------------------------------------------

@router.get("/positions", response_model=Dict[str, Any])
async def get_positions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    ticker: Optional[str] = Query(None),
    classe_ativo: Optional[str] = Query(None),
    snapshot_date: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Lista posições (position_snapshots) com join em assets.
    Suporta filtros: ticker, classe_ativo, snapshot_date, account_id.
    """
    from sqlalchemy import func

    # Query com join em AssetModel
    stmt = (
        select(PositionSnapshotModel, AssetModel)
        .join(AssetModel, PositionSnapshotModel.asset_id == AssetModel.id)
    )

    if ticker:
        stmt = stmt.where(AssetModel.ticker.ilike(f"%{ticker}%"))
    if classe_ativo:
        stmt = stmt.where(AssetModel.asset_class.ilike(f"%{classe_ativo}%"))
    if snapshot_date:
        stmt = stmt.where(PositionSnapshotModel.reference_date == snapshot_date)
    if account_id:
        stmt = stmt.where(PositionSnapshotModel.account_id == account_id)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginação
    stmt = stmt.order_by(
        PositionSnapshotModel.reference_date.desc(),
        AssetModel.ticker
    ).limit(limit).offset(offset)

    result = await session.execute(stmt)
    rows = result.all()

    data = []
    for snap, asset in rows:
        data.append({
            "id": snap.id,
            "ticker": asset.ticker,
            "nome": asset.name or asset.ticker,
            "classe_ativo": asset.asset_class,
            "setor": asset.sector,
            "quantidade": float(snap.quantity) if snap.quantity is not None else None,
            "preco_medio": float(snap.avg_price) if snap.avg_price is not None else None,
            "valor_investido": float(snap.quantity * snap.avg_price) if snap.quantity is not None and snap.avg_price is not None else None,
            "valor_atual": float(snap.current_value) if snap.current_value is not None else None,
            "snapshot_date": snap.reference_date,
            "data_snapshot": snap.reference_date,
            "account_id": snap.account_id,
            "is_manual": bool(snap.is_manual),
            "run_id": snap.run_id,
            "source_type": snap.source_type,
            "observacao": None,
        })

    return {"data": data, "total": total, "limit": limit, "offset": offset}


@router.put("/positions/{ticker}/{snapshot_date}", response_model=Dict[str, Any])
async def update_position(
    ticker: str,
    snapshot_date: str,
    body: Dict[str, Any],
    account_id: Optional[str] = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Atualiza manualmente uma posição (is_manual = 1).
    Apenas quantidade e observação podem ser editadas manualmente.
    """
    asset_result = await session.execute(
        select(AssetModel).where(AssetModel.ticker == ticker)
    )
    asset = asset_result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Ativo '{ticker}' não encontrado.")

    snap_stmt = select(PositionSnapshotModel).where(
        PositionSnapshotModel.asset_id == asset.id,
        PositionSnapshotModel.reference_date == snapshot_date,
    )
    if account_id:
        snap_stmt = snap_stmt.where(PositionSnapshotModel.account_id == account_id)

    snap_result = await session.execute(snap_stmt)
    snap = snap_result.scalar_one_or_none()

    if not snap:
        raise HTTPException(status_code=404, detail="Posição não encontrada.")

    if "quantidade" in body and body["quantidade"] is not None:
        from decimal import Decimal
        snap.quantity = Decimal(str(body["quantidade"]))
    snap.is_manual = 1
    snap.updated_at = datetime.utcnow()
    await session.commit()

    return {"success": True, "message": "Posição atualizada com is_manual=1."}
