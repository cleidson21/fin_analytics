from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, Query, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.ledger_import_history import (
    require_history_for_owned_pierre_runs, require_owned_run, require_pierre_history,
)
from backend.domain.enums.provider_type import ProviderType
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
    reference_date: Optional[str] = None  # YYYY-MM-DD


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_governance_dashboard(
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    await require_history_for_owned_pierre_runs(session, current_user.id)
    use_case = GetGovernanceDashboardUseCase(session)
    return await use_case.execute(user_id=current_user.id)


# ---------------------------------------------------------------------------
# Imports — lista e detalhe
# ---------------------------------------------------------------------------

@router.get("/imports", response_model=Dict[str, Any])
async def get_governance_imports(
    limit: int = Query(10),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    await require_history_for_owned_pierre_runs(session, current_user.id)
    use_case = GetGovernanceImportsUseCase(session)
    return await use_case.execute(user_id=current_user.id, limit=limit)


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
    require_owned_run(log, current_user.id)

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
    require_owned_run(log, current_user.id)

    if log is None:
        raise HTTPException(status_code=404, detail="Run não encontrado")

    metadata = log.provider_metadata or {}
    staging_rows = metadata.get("staging_rows", [])
    source_type = metadata.get("source_type", "")

    items = []
    for i, row in enumerate(staging_rows):
        if source_type == "MYPROFIT_ATIVOS":
            ticker = row.get("ticker", "")
            qty = row.get("quantity")
            sector = str(row.get("sector") or "").upper()
            is_rdb = sector == "RDB"
            is_valid = bool(ticker and (qty is not None or is_rdb))
            
            items.append({
                "source_line_no": i + 2,
                "ticker": ticker,
                "quantity": qty,
                "avg_price": row.get("avg_price"),
                "sector": row.get("sector"),
                "validation_status": "VALID" if is_valid else "ERROR",
                "validation_message": None if is_valid else "Ticker ou quantidade inválidos",
            })
        elif source_type == "MYPROFIT_EVOLUCAO":
            ref = row.get("reference_month")
            patr = row.get("patrimonio")
            is_valid = bool(ref and patr is not None)
            
            items.append({
                "source_line_no": i + 2,
                "ticker": ref,
                "quantity": None,
                "avg_price": patr,
                "sector": None,
                "validation_status": "VALID" if is_valid else "ERROR",
                "validation_message": None if is_valid else "Mês de referência ou patrimônio ausente",
            })
        elif source_type == "MYPROFIT_PROVENTOS":
            ativo = row.get("ativo")
            recebido = row.get("recebido")
            data_pgto = row.get("data_pgto")
            is_valid = bool(ativo and recebido is not None and data_pgto)
            
            items.append({
                "source_line_no": i + 2,
                "ticker": f"{ativo} ({row.get('tipo', '')})",
                "quantity": row.get("cotas"),
                "avg_price": recebido,
                "sector": None,
                "validation_status": "VALID" if is_valid else "ERROR",
                "validation_message": None if is_valid else "Campos obrigatórios ausentes",
            })
        else:
            items.append({
                "source_line_no": i + 2,
                "ticker": "Desconhecido",
                "validation_status": "ERROR",
                "validation_message": f"Tipo {source_type} não formatado para UI"
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
    if source_type.upper() == "PIERRE":
        require_pierre_history(current_user.id)
        raise HTTPException(status_code=422, detail="Use a importação Pierre certificada, não o upload genérico")
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
        # Descobre o tipo primeiro
        result = await session.execute(select(SyncLogModel).where(SyncLogModel.id == run_id))
        log = result.scalar_one_or_none()
        require_owned_run(log, current_user.id)
        if not log:
            raise ValueError(f"Importação {run_id} não encontrada")
            
        source_type = log.provider.value

        if source_type == "MYPROFIT_ATIVOS":
            if not body.reference_date:
                raise ValueError("Data de referência é obrigatória para MYPROFIT_ATIVOS.")
            use_case = ConfirmMyProfitAtivosSyncUseCase(session)
            report = await use_case.execute(
                run_id=run_id,
                account_id=body.account_id,
                reference_date=body.reference_date,
            )
        elif source_type == "MYPROFIT_EVOLUCAO":
            from backend.application.use_cases.confirm_myprofit_evolucao import ConfirmMyProfitEvolucaoSyncUseCase
            use_case = ConfirmMyProfitEvolucaoSyncUseCase(session)
            report = await use_case.execute(
                run_id=run_id,
                account_id=body.account_id,
            )
        elif source_type == "MYPROFIT_PROVENTOS":
            from backend.application.use_cases.confirm_myprofit_proventos import ConfirmMyProfitProventosSyncUseCase
            use_case = ConfirmMyProfitProventosSyncUseCase(session)
            report = await use_case.execute(
                run_id=run_id,
                account_id=body.account_id,
            )
        else:
            raise ValueError(f"Não há fluxo de confirmação para o tipo {source_type}")

        # Persiste account_id e reference_date no metadata para exibição futura
        if log.provider_metadata:
            meta = dict(log.provider_metadata)
            meta["confirmed_account_id"] = body.account_id
            if source_type == "MYPROFIT_ATIVOS":
                meta["confirmed_reference_date"] = body.reference_date
            meta["confirmation_report"] = report
            log.provider_metadata = meta
            await session.commit()

        return {"success": True, "report": report}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
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
    require_owned_run(log, current_user.id)
    if log.provider == ProviderType.PIERRE:
        raise HTTPException(status_code=409, detail="Reversão financeira Pierre não está disponível; o histórico foi preservado")

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

    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    }


# ---------------------------------------------------------------------------
# Evolution — leitura dos portfolio_snapshots
# ---------------------------------------------------------------------------

@router.get("/data/evolution", response_model=Dict[str, Any])
async def get_evolution_data(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    account_id: Optional[str] = Query(None),
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Lista evolução patrimonial (portfolio_snapshots).
    """
    from sqlalchemy import func
    from backend.infrastructure.persistence.models.wealth.portfolio_snapshot import PortfolioSnapshotModel

    stmt = select(PortfolioSnapshotModel)

    if account_id:
        stmt = stmt.where(PortfolioSnapshotModel.account_id == account_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(
        PortfolioSnapshotModel.reference_month.desc()
    ).limit(limit).offset(offset)

    result = await session.execute(stmt)
    rows = result.scalars().all()

    data = []
    for snap in rows:
        data.append({
            "account_id": snap.account_id,
            "reference_month": snap.reference_month,
            "patrimonio": float(snap.patrimonio) if snap.patrimonio is not None else None,
            "pct_mensal": float(snap.pct_mensal) if snap.pct_mensal is not None else None,
            "pct_acumulada": float(snap.pct_acumulada) if snap.pct_acumulada is not None else None,
            "compras": float(snap.compras) if snap.compras is not None else None,
            "vendas": float(snap.vendas) if snap.vendas is not None else None,
            "op_finalizadas": float(snap.op_finalizadas) if snap.op_finalizadas is not None else None,
            "proventos": float(snap.proventos) if snap.proventos is not None else None,
            "ibov_mensal": float(snap.ibov_mensal) if snap.ibov_mensal is not None else None,
            "ibov_acumulado": float(snap.ibov_acumulado) if snap.ibov_acumulado is not None else None,
            "cdi_mensal": float(snap.cdi_mensal) if snap.cdi_mensal is not None else None,
            "cdi_acumulado": float(snap.cdi_acumulado) if snap.cdi_acumulado is not None else None,
            "ipca_mensal": float(snap.ipca_mensal) if snap.ipca_mensal is not None else None,
            "ipca_acumulado": float(snap.ipca_acumulado) if snap.ipca_acumulado is not None else None,
            "ifix_mensal": float(snap.ifix_mensal) if snap.ifix_mensal is not None else None,
            "ifix_acumulado": float(snap.ifix_acumulado) if snap.ifix_acumulado is not None else None,
            "sp_mensal": float(snap.sp_mensal) if snap.sp_mensal is not None else None,
            "sp_acumulado": float(snap.sp_acumulado) if snap.sp_acumulado is not None else None,
            "idiv_mensal": float(snap.idiv_mensal) if snap.idiv_mensal is not None else None,
            "idiv_acumulado": float(snap.idiv_acumulado) if snap.idiv_acumulado is not None else None,
        })

    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/dividends", response_model=Dict[str, Any])
async def get_governance_proventos(
    account_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ticker: Optional[str] = None,
    tipo_evento: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: UserResponseDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    from backend.infrastructure.persistence.models.wealth.income_event import IncomeEventModel
    from backend.infrastructure.persistence.models.wealth.asset import AssetModel
    from datetime import datetime
    
    stmt = select(IncomeEventModel, AssetModel.ticker).join(
        AssetModel, IncomeEventModel.asset_id == AssetModel.id
    )

    if account_id:
        stmt = stmt.where(IncomeEventModel.account_id == account_id)
    if ticker:
        stmt = stmt.where(AssetModel.ticker.ilike(f"%{ticker}%"))
    if tipo_evento:
        stmt = stmt.where(IncomeEventModel.event_type.ilike(f"%{tipo_evento}%"))
    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").date()
            stmt = stmt.where(IncomeEventModel.payment_date >= sd)
        except ValueError:
            pass
    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").date()
            stmt = stmt.where(IncomeEventModel.payment_date <= ed)
        except ValueError:
            pass

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(
        IncomeEventModel.payment_date.desc()
    ).limit(limit).offset(offset)

    result = await session.execute(stmt)
    rows = result.all()

    data = []
    for snap, ticker_val in rows:
        data.append({
            "id": snap.id,
            "account_id": snap.account_id,
            "asset_id": snap.asset_id,
            "ticker": ticker_val,
            "tipo_evento": snap.event_type,
            "data_pagamento": snap.payment_date.isoformat() if snap.payment_date else None,
            "ex_date": snap.ex_date.isoformat() if snap.ex_date else None,
            "quantity": float(snap.quantity) if snap.quantity is not None else None,
            "value_per_unit": float(snap.value_per_unit) if snap.value_per_unit is not None else None,
            "valor": float(snap.gross_amount) if snap.gross_amount is not None else None,
            "yoc": float(snap.yoc) if snap.yoc is not None else None,
            "dy": float(snap.dy) if snap.dy is not None else None,
        })

    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    }


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
