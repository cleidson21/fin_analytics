"""
repository.py — Domínio Dashboard

Camada de somente leitura sobre as tabelas de governança.

Consulta exclusivamente:
  - sync_state  → estado atual de cada provider
  - sync_history → histórico de sincronizações

Regras absolutas:
  - SOMENTE SELECT — nenhum INSERT, UPDATE ou DELETE
  - Nenhuma migration criada
  - Nenhuma coluna nova adicionada
  - Nenhuma tabela alterada
  - Nenhuma chamada a APIs externas
  - Não importar nada do domínio pierre diretamente (acessa as mesmas tabelas via shared models)
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.pierre.models import SyncHistory, SyncState


class GovernanceRepository:
    """
    Repositório de somente leitura para dados de governança.

    Consulta sync_state e sync_history sem qualquer efeito colateral.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ─────────────────────────────────────────────────────────────────────────
    # sync_state
    # ─────────────────────────────────────────────────────────────────────────

    async def get_all_sync_states(self) -> list[SyncState]:
        """Retorna o sync_state de todos os providers cadastrados."""
        result = await self._session.execute(
            select(SyncState).order_by(SyncState.provider)
        )
        return list(result.scalars().all())

    async def get_sync_state(self, provider: str) -> Optional[SyncState]:
        """Retorna o sync_state de um provider específico."""
        result = await self._session.execute(
            select(SyncState).where(SyncState.provider == provider)
        )
        return result.scalar_one_or_none()

    # ─────────────────────────────────────────────────────────────────────────
    # sync_history
    # ─────────────────────────────────────────────────────────────────────────

    async def get_history(
        self,
        provider: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SyncHistory], int]:
        """
        Retorna o histórico de sincronizações ordenado por finished_at DESC.

        Args:
            provider: filtra por provider se fornecido (ex: 'pierre')
            limit:  máximo de registros a retornar
            offset: paginação

        Returns:
            Tupla (registros, total_sem_paginacao)
        """
        # Query base
        base_q = select(SyncHistory)
        count_q = select(func.count(SyncHistory.id))

        if provider:
            base_q = base_q.where(SyncHistory.provider == provider)
            count_q = count_q.where(SyncHistory.provider == provider)

        # Ordenação: finished_at DESC (NULL vai ao final)
        base_q = base_q.order_by(
            SyncHistory.finished_at.desc().nulls_last(),
            SyncHistory.id.desc(),
        )
        base_q = base_q.offset(offset).limit(limit)

        result = await self._session.execute(base_q)
        count_result = await self._session.execute(count_q)

        records = list(result.scalars().all())
        total = count_result.scalar() or 0

        return records, total
