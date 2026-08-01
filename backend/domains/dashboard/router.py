"""
router.py — Domínio Dashboard

Endpoints FastAPI da Sprint 4.4.3 (Governança):
  GET /api/v1/dashboard/sync/status   → estado atual de cada provider
  GET /api/v1/dashboard/sync/history  → histórico de sincronizações

Endpoints futuros (não implementar nesta sprint):
  GET /api/v1/dashboard/cashflow      → Sprint 4.4.4
  GET /api/v1/dashboard/portfolio     → Sprint 4.5
  GET /api/v1/dashboard/consolidated  → Sprint 4.6
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.dashboard.schemas import (
    SyncHistoryListResponse,
    SyncStatusListResponse,
)
from backend.domains.dashboard.service import GovernanceService
from backend.domains.shared.db import get_session

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def _get_governance_service(
    session: AsyncSession = Depends(get_session),
) -> GovernanceService:
    """Dependency: cria GovernanceService com sessão injetada."""
    return GovernanceService(session)


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 4.4.3 — Governança
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/sync/status",
    response_model=SyncStatusListResponse,
    summary="Status de sincronização por provider",
    description=(
        "Retorna o estado atual de `sync_state` para todos os providers "
        "registrados no banco.\n\n"
        "Campos retornados por provider:\n"
        "- `last_success_sync`: data/hora da última sincronização bem-sucedida\n"
        "- `last_attempt`: data/hora da última tentativa (sucesso ou falha)\n"
        "- `last_period`: período consultado na última sync\n"
        "- `api_version`: versão da API usada\n\n"
        "**Somente leitura.** Não dispara nenhuma sincronização."
    ),
)
async def get_sync_status(
    service: GovernanceService = Depends(_get_governance_service),
) -> SyncStatusListResponse:
    """
    GET /api/v1/dashboard/sync/status

    Retorna estado atual de sync_state para todos os providers.
    """
    return await service.get_all_sync_status()


@router.get(
    "/sync/history",
    response_model=SyncHistoryListResponse,
    summary="Histórico de sincronizações",
    description=(
        "Retorna o histórico completo de execuções de sincronização, "
        "ordenado por `finished_at DESC`.\n\n"
        "Parâmetros:\n"
        "- `provider`: filtra por provider (`pierre`, `myprofit`). "
        "Omitir retorna todos.\n"
        "- `limit`: máximo de registros (padrão: 50)\n"
        "- `offset`: paginação\n\n"
        "**Somente leitura.** Não altera nenhuma tabela."
    ),
)
async def get_sync_history(
    provider: Optional[str] = Query(
        default=None,
        description="Filtrar por provider: 'pierre' | 'myprofit'. Omitir = todos.",
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Máximo de registros"),
    offset: int = Query(default=0, ge=0, description="Offset para paginação"),
    service: GovernanceService = Depends(_get_governance_service),
) -> SyncHistoryListResponse:
    """
    GET /api/v1/dashboard/sync/history

    Retorna histórico de sincronizações (sync_history), ordenado por finished_at DESC.
    """
    return await service.get_sync_history(
        provider=provider,
        limit=limit,
        offset=offset,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 4.4.4+ — Placeholders (não implementar aqui)
# ─────────────────────────────────────────────────────────────────────────────

# TODO Sprint 4.4.4 — GET /api/v1/dashboard/cashflow
# TODO Sprint 4.5   — GET /api/v1/dashboard/portfolio
# TODO Sprint 4.6   — GET /api/v1/dashboard/consolidated
