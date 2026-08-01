"""
router.py — Domínio Pierre

Endpoints FastAPI da Sprint 4.4.2:
  POST /api/v1/pierre/sync         → dispara sincronização
  GET  /api/v1/pierre/sync/status  → estado atual do sync_state

Nenhum endpoint adicional nesta sprint.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.pierre.schemas import SyncResultResponse, SyncStatusResponse
from backend.domains.pierre.service import PierreSyncService, SyncMode
from backend.domains.shared.db import get_session

router = APIRouter(prefix="/api/v1/pierre", tags=["pierre"])


def _get_service(session: AsyncSession = Depends(get_session)) -> PierreSyncService:
    """Dependency: constrói o PierreSyncService com as credenciais do ambiente."""
    api_key = os.getenv("PIERRE_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PIERRE_API_KEY não configurada no ambiente.",
        )
    environment = os.getenv("ENVIRONMENT", "production")
    return PierreSyncService(session=session, api_key=api_key, environment=environment)


@router.post(
    "/sync",
    response_model=SyncResultResponse,
    summary="Sincronizar dados Pierre",
    description=(
        "Executa o pipeline de sincronização Pierre.\n\n"
        "Modos:\n"
        "- **PROD**: chama a API Pierre, JSON em memória\n"
        "- **DEV**: chama a API Pierre, salva JSON bruto em exports/pierre/raw/\n"
        "- **REPLAY**: reprocessa um arquivo JSON salvo (não chama a API)\n\n"
        "A operação é **idempotente**: executar duas vezes com o mesmo payload "
        "resulta em zero duplicações."
    ),
)
async def sync_pierre(
    mode: SyncMode = Query(default=SyncMode.PROD, description="Modo de sincronização"),
    start_date: str = Query(default="2024-01-01", description="Data de início YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="Data de fim YYYY-MM-DD (padrão: hoje)"),
    replay_file: Optional[str] = Query(default=None, description="Caminho do arquivo JSON para modo REPLAY"),
    service: PierreSyncService = Depends(_get_service),
) -> SyncResultResponse:
    """
    POST /api/v1/pierre/sync

    Dispara a sincronização Pierre no modo especificado.
    Retorna os contadores de registros processados e o status da operação.
    """
    return await service.sync(
        mode=mode,
        start_date=start_date,
        end_date=end_date,
        replay_file=replay_file,
    )


@router.get(
    "/sync/status",
    response_model=Optional[SyncStatusResponse],
    summary="Status da sincronização Pierre",
    description=(
        "Retorna o estado atual de sync_state para o provider Pierre.\n\n"
        "Retorna `null` se nunca houve sincronização."
    ),
)
async def get_sync_status(
    service: PierreSyncService = Depends(_get_service),
) -> Optional[SyncStatusResponse]:
    """
    GET /api/v1/pierre/sync/status

    Retorna last_success_sync, last_attempt, last_period do sync_state Pierre.
    """
    return await service.get_status()
