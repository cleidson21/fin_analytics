"""
etl/base.py — Contrato base do pipeline ETL v2.

Define o Protocol EventNormalizer que cada adaptador de fonte deve implementar,
e funções utilitárias de construção de eventos e fingerprints.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable

from models.core import EventType, MatchStatus, PipelineStatus, RawFinancialEvent


# ─────────────────────────────────────────────────────────────────────────────
# Fingerprints
# ─────────────────────────────────────────────────────────────────────────────

def make_semantic_id(*parts: object) -> str:
    """
    Fingerprint determinístico intra-source.
    Inclui o campo 'source' → garante que mesmo evento de fontes diferentes
    gera IDs distintos.
    Exemplo: make_semantic_id("NUBANK_CONTA", "TRANSACTION", "2024-03-15", 8743, "abc123")
    """
    raw = "|".join(str(p).strip() for p in parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def make_cross_fingerprint(*parts: object) -> str:
    """
    Fingerprint cross-source (sem o campo 'source').
    Permite detectar que o mesmo evento foi reportado por fontes distintas.
    Exemplo: make_cross_fingerprint("DIVIDEND", "2024-03-15", 8743, "VGIR11")
    """
    raw = "|".join(str(p).strip() for p in parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Construtor de RawFinancialEvent
# ─────────────────────────────────────────────────────────────────────────────

def build_raw_event(
    *,
    event_type: EventType,
    source: str,
    import_run_id: str,
    semantic_id: str,
    cross_fingerprint: str | None = None,
    event_date: date | None = None,
    reference_month: date | None = None,
    amount_cents: int | None = None,
    external_id: str | None = None,
    metadata: dict | None = None,
    source_line_no: int | None = None,
    raw_content: str | None = None,
) -> RawFinancialEvent:
    """
    Constrói um RawFinancialEvent com valores padrão para campos opcionais.
    Garante que 'id' é sempre um UUID v4 único.
    """
    return RawFinancialEvent(
        id=str(uuid.uuid4()),
        event_type=event_type,
        source=source,
        import_run_id=import_run_id,
        source_line_no=source_line_no,
        raw_content=raw_content,
        event_date=event_date,
        reference_month=reference_month,
        amount_cents=amount_cents,
        currency="BRL",
        semantic_id=semantic_id,
        cross_fingerprint=cross_fingerprint,
        external_id=external_id,
        metadata=metadata or {},
        pipeline_status=PipelineStatus.NORMALIZED.value,
        match_status=MatchStatus.NEW.value,
        promoted_entity_id=None,
        promoted_table=None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Protocol EventNormalizer
# ─────────────────────────────────────────────────────────────────────────────

@runtime_checkable
class EventNormalizer(Protocol):
    """
    Contrato que cada adaptador de fonte deve implementar.
    O pipeline chama can_handle() para detectar a fonte e depois normalize().
    """

    @property
    def source_id(self) -> str:
        """Identificador único da fonte. Ex: 'NUBANK_CONTA'"""
        ...

    @property
    def accepted_extensions(self) -> list[str]:
        """Ex: ['.csv'], ['.txt'], ['.pdf']"""
        ...

    def can_handle(self, file_name: str, raw_content: str) -> bool:
        """
        Retorna True se este normalizer é capaz de processar o arquivo/texto dado.
        Usado pelo pipeline para auto-detectar a fonte.
        """
        ...

    def normalize(
        self,
        raw_content: str | bytes,
        import_run_id: str,
    ) -> list[RawFinancialEvent]:
        """
        Converte o conteúdo bruto para uma lista de RawFinancialEvent normalizados.
        Cada evento deve ter pipeline_status = NORMALIZED ao sair.
        """
        ...
