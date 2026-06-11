"""
etl/matcher.py — EventMatcher

Responsável por detectar duplicatas e correspondências cross-source nos eventos.
Opera em 3 níveis de fingerprint:
  1. semantic_id + source → DUPLICATE (intra-source, bloqueante)
  2. cross_fingerprint    → CROSS_SOURCE_MATCH (same event, different source)
  3. fuzzy window ±3 days, ±1% amount → candidate for RECONCILED

Não persiste dados — retorna os eventos com match_status atualizado.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from models.core import MatchStatus, RawFinancialEvent

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    event: RawFinancialEvent
    conflicting_event_id: str | None = None  # raw_events.id de um evento conflitante


class EventMatcher:
    """
    Classifica eventos quanto ao seu status de duplicação.

    Recebe os eventos normalizados do import atual mais um snapshot dos
    semantic_ids e cross_fingerprints já existentes na base.

    Usage:
        matcher = EventMatcher()
        results = matcher.match(
            new_events=events,
            existing_semantic_ids={...},     # set de (semantic_id, source) do DB
            existing_cross_fps={...},        # dict cross_fp → raw_event_id do DB
        )
    """

    def match(
        self,
        new_events: list[RawFinancialEvent],
        existing_semantic_ids: set[tuple[str, str]],   # {(semantic_id, source), ...}
        existing_cross_fps: dict[str, str],             # {cross_fp: raw_event_id}
    ) -> list[MatchResult]:
        """
        Classifica cada evento como NEW, DUPLICATE ou CROSS_SOURCE_MATCH.

        Returns:
            list[MatchResult] com events modificados in-place (match_status atualizado).
        """
        results: list[MatchResult] = []
        # Rastreia semantic_ids do lote atual para detectar duplicatas intra-batch
        batch_semantic_ids: set[tuple[str, str]] = set()
        batch_cross_fps: dict[str, str] = {}

        for event in new_events:
            key = (event["semantic_id"], event["source"])

            # ── Nível 1: DUPLICATE intra-source ───────────────────
            if key in existing_semantic_ids or key in batch_semantic_ids:
                event["match_status"] = MatchStatus.DUPLICATE.value
                results.append(MatchResult(event=event))
                logger.debug(f"DUPLICATE: {event['semantic_id']} [{event['source']}]")
                continue

            # ── Nível 2: CROSS_SOURCE_MATCH ────────────────────────
            cross_fp = event.get("cross_fingerprint")
            conflicting_id: str | None = None

            if cross_fp:
                # Checar no DB
                if cross_fp in existing_cross_fps:
                    existing_id = existing_cross_fps[cross_fp]
                    event["match_status"] = MatchStatus.CROSS_SOURCE_MATCH.value
                    conflicting_id = existing_id
                    logger.info(
                        f"CROSS_SOURCE_MATCH: {event['source']} cross_fp={cross_fp[:16]}… "
                        f"↔ existing raw_event {existing_id}"
                    )
                # Checar no próprio lote (dois arquivos distintos no mesmo import)
                elif cross_fp in batch_cross_fps:
                    event["match_status"] = MatchStatus.CROSS_SOURCE_MATCH.value
                    conflicting_id = batch_cross_fps[cross_fp]
                    logger.info(f"CROSS_SOURCE_MATCH intra-batch: cross_fp={cross_fp[:16]}…")

            # ── Nível 0: NEW ────────────────────────────────────────
            if event["match_status"] == MatchStatus.NEW.value:
                pass  # Já está NEW por padrão

            # Registra para próximas iterações do lote
            batch_semantic_ids.add(key)
            if cross_fp:
                batch_cross_fps.setdefault(cross_fp, event["id"])

            results.append(MatchResult(event=event, conflicting_event_id=conflicting_id))

        new_count  = sum(1 for r in results if r.event["match_status"] == MatchStatus.NEW.value)
        dup_count  = sum(1 for r in results if r.event["match_status"] == MatchStatus.DUPLICATE.value)
        cross_count = sum(1 for r in results if r.event["match_status"] == MatchStatus.CROSS_SOURCE_MATCH.value)
        logger.info(f"[Matcher] NEW={new_count} | DUPLICATE={dup_count} | CROSS_SOURCE={cross_count}")

        return results

    @staticmethod
    def load_existing_from_db(conn, import_run_id: str | None = None) -> tuple[set, dict]:
        """
        Carrega semantic_ids e cross_fingerprints existentes no DB.
        Se import_run_id for None, carrega todos (para detecção cross-run).

        Returns:
            (existing_semantic_ids: set[tuple], existing_cross_fps: dict[str, str])
        """
        if import_run_id:
            rows_semantic = conn.execute(
                "SELECT semantic_id, source FROM raw_events WHERE import_run_id = ?",
                (import_run_id,),
            ).fetchall()
            rows_cross = conn.execute(
                "SELECT cross_fingerprint, id FROM raw_events WHERE cross_fingerprint IS NOT NULL AND import_run_id != ?",
                (import_run_id,),
            ).fetchall()
        else:
            rows_semantic = conn.execute(
                "SELECT semantic_id, source FROM raw_events"
            ).fetchall()
            rows_cross = conn.execute(
                "SELECT cross_fingerprint, id FROM raw_events WHERE cross_fingerprint IS NOT NULL"
            ).fetchall()

        existing_semantic_ids = {(row[0], row[1]) for row in rows_semantic}
        existing_cross_fps    = {row[0]: row[1] for row in rows_cross if row[0]}

        return existing_semantic_ids, existing_cross_fps
