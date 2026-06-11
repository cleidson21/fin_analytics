"""
etl/normalizers/nubank_fatura.py

Normalizer para CSV de fatura do cartão de crédito Nubank.
Colunas esperadas: date, title, amount

Produz eventos do tipo INVOICE.
Nota: sem coluna "Identificador" (diferente do CSV de conta).
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

_REQUIRED_COLUMNS = {"date", "title", "amount"}
_SOURCE_ID = "NUBANK_FATURA"


class NubankFaturaNormalizer:
    """
    Normalizer para CSV da fatura do cartão Nubank.
    Formato: date, title, amount
    (colunas em inglês, sem Identificador)
    """

    @property
    def source_id(self) -> str:
        return _SOURCE_ID

    @property
    def accepted_extensions(self) -> list[str]:
        return [".csv"]

    def can_handle(self, file_name: str, raw_content: str) -> bool:
        """
        Detecta CSV de fatura Nubank.
        Critério: tem colunas 'date', 'title', 'amount' (inglês, sem Identificador).
        """
        if not file_name.lower().endswith(".csv"):
            return False
        try:
            sample = raw_content[:2048]
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.DictReader(StringIO(raw_content[:4096]), dialect=dialect)
            fieldnames = {f.lower().strip() for f in (reader.fieldnames or [])}
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

        # Normaliza fieldnames para lowercase para lidar com variações de capitalização
        fieldnames_raw = reader.fieldnames or []
        fieldnames_lower = {f.lower().strip(): f for f in fieldnames_raw}

        date_col   = fieldnames_lower.get("date")
        title_col  = fieldnames_lower.get("title")
        amount_col = fieldnames_lower.get("amount")

        if not (date_col and title_col and amount_col):
            logger.error(f"[{_SOURCE_ID}] Colunas obrigatórias ausentes.")
            return []

        for line_no, row in enumerate(reader, start=2):
            dt_str     = row.get(date_col, "").strip()
            title_str  = row.get(title_col, "").strip()
            amount_str = row.get(amount_col, "0").strip()

            # Fatura Nubank usa formato ISO: YYYY-MM-DD
            try:
                from datetime import datetime
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d").date() if dt_str else None
            except ValueError:
                # Fallback para formato BR
                from utils.transformers import parse_br_date
                dt_obj = parse_br_date(dt_str)

            amount = parse_br_currency(amount_str)

            if not dt_obj or amount is None or not title_str:
                logger.warning(f"[{_SOURCE_ID}:L{line_no}] Dados inválidos. Ignorando.")
                continue

            desc_norm = normalize_description(title_str)
            amount_cents = int(amount * 100)
            raw_line = ",".join(str(v) for v in row.values())

            semantic_id = make_semantic_id(
                _SOURCE_ID, EventType.INVOICE, dt_obj.isoformat(),
                amount_cents, desc_norm[:50],
            )
            # Cross-fingerprint: tenta casar com transação de pagamento de fatura
            # via data + valor absoluto + descrição normalizada
            cross_fp = make_cross_fingerprint(
                EventType.INVOICE, dt_obj.isoformat(),
                abs(amount_cents), desc_norm[:40],
            )

            events.append(build_raw_event(
                event_type=EventType.INVOICE,
                source=_SOURCE_ID,
                import_run_id=import_run_id,
                semantic_id=semantic_id,
                cross_fingerprint=cross_fp,
                event_date=dt_obj,
                amount_cents=amount_cents,
                external_id=None,
                source_line_no=line_no,
                raw_content=raw_line,
                metadata={
                    "title": title_str,
                    "descricao_normalizada": desc_norm,
                },
            ))

        logger.info(f"[{_SOURCE_ID}] {len(events)} eventos de fatura normalizados")
        return events
