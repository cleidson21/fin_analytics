"""
etl/normalizers/nubank_conta.py

Normalizer para CSV do extrato de conta corrente Nubank.
Colunas esperadas: Data, Valor, Identificador, Descrição

Produz eventos do tipo TRANSACTION.
"""
from __future__ import annotations

import csv
import logging
from io import StringIO

from etl.base import EventNormalizer, build_raw_event, make_cross_fingerprint, make_semantic_id
from models.core import EventType, RawFinancialEvent
from utils.semantic import normalize_description
from utils.transformers import parse_br_currency, parse_br_date

logger = logging.getLogger(__name__)

_REQUIRED_COLUMNS = {"Data", "Valor", "Identificador", "Descrição"}
_SOURCE_ID = "NUBANK_CONTA"


class NubankContaNormalizer:
    """
    Normalizer para CSV do extrato de conta corrente Nubank.
    Formato: Data, Valor, Identificador, Descrição
    """

    @property
    def source_id(self) -> str:
        return _SOURCE_ID

    @property
    def accepted_extensions(self) -> list[str]:
        return [".csv"]

    def can_handle(self, file_name: str, raw_content: str) -> bool:
        """
        Detecta se o arquivo é um CSV de conta Nubank.
        Critério: tem as 4 colunas obrigatórias E tem 'Identificador' (fatura não tem).
        """
        if not file_name.lower().endswith(".csv"):
            return False
        try:
            sample = raw_content[:2048]
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.DictReader(StringIO(raw_content[:4096]), dialect=dialect)
            fieldnames = set(reader.fieldnames or [])
            return _REQUIRED_COLUMNS.issubset(fieldnames)
        except Exception:
            return False

    def normalize(
        self,
        raw_content: str | bytes,
        import_run_id: str,
    ) -> list[RawFinancialEvent]:
        if isinstance(raw_content, bytes):
            raw_content = raw_content.decode("utf-8-sig")

        events: list[RawFinancialEvent] = []

        try:
            dialect = csv.Sniffer().sniff(raw_content[:2048])
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(StringIO(raw_content), dialect=dialect)
        fieldnames = set(reader.fieldnames or [])

        if not _REQUIRED_COLUMNS.issubset(fieldnames):
            logger.error(f"[{_SOURCE_ID}] Colunas obrigatórias ausentes: {_REQUIRED_COLUMNS - fieldnames}")
            return []

        for line_no, row in enumerate(reader, start=2):
            dt_str = row.get("Data", "").strip()
            valor_str = row.get("Valor", "0").strip()
            desc_str = row.get("Descrição", "").strip()
            ext_id = row.get("Identificador", "").strip()

            dt_obj = parse_br_date(dt_str)
            amount = parse_br_currency(valor_str)

            if not dt_obj or amount is None:
                logger.warning(f"[{_SOURCE_ID}:L{line_no}] Data ou valor inválidos. Ignorando.")
                continue

            desc_norm = normalize_description(desc_str)
            amount_cents = int(amount * 100)
            raw_line = ",".join(str(v) for v in row.values())

            semantic_id = make_semantic_id(
                _SOURCE_ID, EventType.TRANSACTION, dt_obj.isoformat(),
                amount_cents, ext_id or desc_norm,
            )
            cross_fp = make_cross_fingerprint(
                EventType.TRANSACTION, dt_obj.isoformat(),
                abs(amount_cents), desc_norm[:40],
            )

            events.append(build_raw_event(
                event_type=EventType.TRANSACTION,
                source=_SOURCE_ID,
                import_run_id=import_run_id,
                semantic_id=semantic_id,
                cross_fingerprint=cross_fp,
                event_date=dt_obj,
                amount_cents=amount_cents,
                external_id=ext_id or None,
                source_line_no=line_no,
                raw_content=raw_line,
                metadata={
                    "descricao_original": desc_str,
                    "descricao_normalizada": desc_norm,
                    "identificador_externo": ext_id,
                },
            ))

        logger.info(f"[{_SOURCE_ID}] {len(events)} eventos normalizados")
        return events
