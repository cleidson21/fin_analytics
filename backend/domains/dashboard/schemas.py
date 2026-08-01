"""
schemas.py — Domínio Dashboard

DTOs de resposta para os endpoints de governança e futuros dashboards.

Sprint 4.4.3 — Governança:
  SyncStatusDTO    → estado atual de sync_state (por provider)
  SyncHistoryDTO   → entrada do histórico sync_history
  SyncHistoryListResponse → lista paginável com total

Sprint 4.4.4+ (a implementar):
  - schemas de cashflow Pierre
  - schemas de portfólio MyProfit

Regras:
  - Somente DTOs de saída (leitura)
  - Nenhuma regra de negócio
  - Nenhuma transformação além de serialização
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 4.4.3 — Governança
# ─────────────────────────────────────────────────────────────────────────────

class SyncStatusDTO(BaseModel):
    """Estado atual de sync_state para um provider."""
    provider: str
    last_success_sync: Optional[datetime]
    last_attempt: Optional[datetime]
    last_cursor: Optional[str]
    last_period: Optional[str]
    api_version: Optional[str]


class SyncHistoryDTO(BaseModel):
    """Entrada do histórico de sincronização (sync_history)."""
    id: int
    provider: str
    started_at: datetime
    finished_at: Optional[datetime]
    received: int
    inserted: int
    updated: int
    ignored: int
    status: Optional[str]      # SUCCESS | FAILED | PARTIAL
    error: Optional[str]


class SyncStatusListResponse(BaseModel):
    """Lista de status de todos os providers."""
    items: list[SyncStatusDTO]
    total: int


class SyncHistoryListResponse(BaseModel):
    """Lista paginável do histórico de sincronizações."""
    items: list[SyncHistoryDTO]
    total: int
    provider: Optional[str]    # None = todos os providers


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 4.4.4+ — Placeholders (a implementar)
# ─────────────────────────────────────────────────────────────────────────────

# TODO Sprint 4.4.4 — implementar schemas de cashflow Pierre
# TODO Sprint 4.5   — adicionar schemas de dashboard MyProfit
# TODO Sprint 4.6   — schemas de cruzamento analítico Pierre × MyProfit
