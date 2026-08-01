"""
service.py — Domínio Dashboard

GovernanceService: somente leitura.

Responsabilidade: orquestrar chamadas ao GovernanceRepository e
converter os models SQLAlchemy nos DTOs de resposta (schemas.py).

Regras absolutas:
  - Nenhuma regra de negócio financeira
  - Nenhum cálculo ou agregação além de passagem direta
  - Nenhuma escrita em banco
  - Nenhuma chamada a APIs externas (Pierre, MyProfit)
  - Nenhum recálculo de sincronizações
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.dashboard.repository import GovernanceRepository
from backend.domains.dashboard.schemas import (
    SyncHistoryDTO,
    SyncHistoryListResponse,
    SyncStatusDTO,
    SyncStatusListResponse,
)
from backend.domains.pierre.models import SyncHistory, SyncState


def _to_status_dto(state: SyncState) -> SyncStatusDTO:
    """Converte um SyncState model em SyncStatusDTO."""
    return SyncStatusDTO(
        provider=state.provider,
        last_success_sync=state.last_success_sync,
        last_attempt=state.last_attempt,
        last_cursor=state.last_cursor,
        last_period=state.last_period,
        api_version=state.api_version,
    )


def _to_history_dto(record: SyncHistory) -> SyncHistoryDTO:
    """Converte um SyncHistory model em SyncHistoryDTO."""
    return SyncHistoryDTO(
        id=record.id,
        provider=record.provider,
        started_at=record.started_at,
        finished_at=record.finished_at,
        received=record.received,
        inserted=record.inserted,
        updated=record.updated,
        ignored=record.ignored,
        status=record.status,
        error=record.error,
    )


class GovernanceService:
    """
    Serviço de somente leitura para dados de governança.

    Converte models → DTOs. Nenhuma lógica de negócio.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = GovernanceRepository(session)

    async def get_all_sync_status(self) -> SyncStatusListResponse:
        """Retorna o estado atual de todos os providers."""
        states = await self._repo.get_all_sync_states()
        items = [_to_status_dto(s) for s in states]
        return SyncStatusListResponse(items=items, total=len(items))

    async def get_sync_status(self, provider: str) -> Optional[SyncStatusDTO]:
        """Retorna o estado atual de um provider específico."""
        state = await self._repo.get_sync_state(provider)
        if state is None:
            return None
        return _to_status_dto(state)

    async def get_sync_history(
        self,
        provider: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SyncHistoryListResponse:
        """
        Retorna histórico de sincronizações ordenado por finished_at DESC.

        Args:
            provider: filtra por provider ('pierre', 'myprofit') — None = todos
            limit:   máximo de registros
            offset:  paginação
        """
        records, total = await self._repo.get_history(
            provider=provider,
            limit=limit,
            offset=offset,
        )
        items = [_to_history_dto(r) for r in records]
        return SyncHistoryListResponse(
            items=items,
            total=total,
            provider=provider,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 4.4.4+ — Placeholders
# ─────────────────────────────────────────────────────────────────────────────

# TODO Sprint 4.4.4 — implementar visões Pierre (cashflow, contas, categorias)
# TODO Sprint 4.5   — visões MyProfit (patrimônio, posições, dividendos)
# TODO Sprint 4.6   — cruzamento analítico Pierre × MyProfit
