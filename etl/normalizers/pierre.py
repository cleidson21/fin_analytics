"""
etl/normalizers/pierre.py

Normalizer para o extrato Pierre (CSV/TXT).
Reutiliza a lógica do PierreParser legado e adapta para RawFinancialEvent.

Produz eventos do tipo TRANSACTION.
"""
from __future__ import annotations

import csv
import logging
import re
from io import StringIO

from etl.base import EventNormalizer, build_raw_event, make_cross_fingerprint, make_semantic_id
from models.core import EventType, RawFinancialEvent
from utils.semantic import normalize_description
from utils.transformers import generate_economic_id, parse_br_currency, parse_br_date

logger = logging.getLogger(__name__)

_SOURCE_ID = "PIERRE"
_PIERRE_COLUMNS = {"Data", "Descrição", "Valor"}
_PIERRE_COLUMNS_ALT = {"Data", "Descricao", "Valor"}  # sem acento


class PierreNormalizer:
    """
    Normalizer para o extrato Pierre (CSV exportado do app Pierre).
    Fallback: aceita qualquer CSV que tenha Data, Descrição/Descricao e Valor.
    """

    @property
    def source_id(self) -> str:
        return _SOURCE_ID

    @property
    def accepted_extensions(self) -> list[str]:
        return [".csv", ".txt"]

    def can_handle(self, file_name: str, raw_content: str) -> bool:
        ext = file_name.lower().rsplit(".", 1)[-1]
        if ext not in ("csv", "txt"):
            return False
        try:
            sample = raw_content[:2048]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";,")
            except csv.Error:
                dialect = csv.excel

            reader = csv.DictReader(StringIO(raw_content[:4096]), dialect=dialect)
            fieldnames = set(reader.fieldnames or [])
            return _PIERRE_COLUMNS.issubset(fieldnames) or _PIERRE_COLUMNS_ALT.issubset(fieldnames)
        except Exception:
            return False

    def normalize(
        self,
        raw_content: str | bytes,
        import_run_id: str,
    ) -> list[RawFinancialEvent]:
        if isinstance(raw_content, bytes):
            raw_content = raw_content.decode("utf-8-sig")

        raw_content = raw_content.replace("\r\n", "\n").replace("\r", "\n")
        events: list[RawFinancialEvent] = []

        try:
            dialect = csv.Sniffer().sniff(raw_content[:4096], delimiters=";,")
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(StringIO(raw_content), dialect=dialect)

        for line_no, row in enumerate(reader, start=1):
            dt_str = (row.get("Data") or "").strip()
            desc   = (row.get("Descrição") or row.get("Descricao") or "").strip()
            val_str = (row.get("Valor") or "0").strip()
            account = (row.get("Conta") or "PIERRE").strip()

            dt_obj = parse_br_date(dt_str)
            amount = parse_br_currency(val_str)

            if not dt_obj or amount is None or not desc:
                logger.warning(f"[{_SOURCE_ID}:L{line_no}] Dados inválidos. Ignorando.")
                continue

            # Limpa emojis da descrição
            desc_clean = re.sub(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]", "", desc)
            desc_clean = re.sub(r"\s+", " ", desc_clean).strip()
            desc_norm  = normalize_description(desc_clean)
            source_val = account.upper() if account else "PIERRE"
            amount_cents = int(amount.quantize(__import__("decimal").Decimal("0.01")) * 100)

            # Fingerprint compatível com o id_economico gerado pelo PierreParser legado
            id_economico = generate_economic_id(
                "MANUAL", "PIERRE", line_no,
                dt_obj.isoformat(), desc_norm,
                str(amount.quantize(__import__("decimal").Decimal("0.01"))),
                source_val,
            )

            semantic_id = make_semantic_id(
                _SOURCE_ID, EventType.TRANSACTION, id_economico,
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
                external_id=id_economico,  # compatível com id_economico legado
                source_line_no=line_no,
                raw_content=",".join(str(v) for v in row.values()),
                metadata={
                    "id_economico": id_economico,
                    "descricao_original": desc_clean,
                    "descricao_normalizada": desc_norm,
                    "source": source_val,
                    "origin": "PIERRE",
                    "domain": "FINANCE",
                    "categoria_origem": row.get("Categoria", ""),
                    "account": account,
                },
            ))

        logger.info(f"[{_SOURCE_ID}] {len(events)} eventos normalizados")
        return events
