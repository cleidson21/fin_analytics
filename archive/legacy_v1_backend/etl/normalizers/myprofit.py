"""
etl/normalizers/myprofit.py

Normalizer para os 3 CSVs do MyProfit:
  - tableExport.csv → POSITION events
  - proventos.csv   → DIVIDEND events
  - evolução*.csv   → PORTFOLIO_EVO events

A detecção do tipo é feita por can_handle() via análise de colunas.
"""
from __future__ import annotations

import csv
import json
import logging
from decimal import Decimal
from io import StringIO

from etl.base import EventNormalizer, build_raw_event, make_cross_fingerprint, make_semantic_id
from models.core import EventType, RawFinancialEvent
from utils.transformers import parse_br_currency, parse_br_date

logger = logging.getLogger(__name__)

_SOURCE_ID = "MYPROFIT"

# Aliases por tipo de coluna (idênticos ao parser legado)
_COLUMN_ALIASES = {
    "ativo":           ["Ativo", "Ticker", "Código", "Papel"],
    "quantidade":      ["Qtd", "Quantidade", "Cotas"],
    "preco_medio":     ["Preço médio", "PM"],
    "total_investido": ["Total investido", "Valor Pago"],
    "preco_atual":     ["Preço atual", "Cotação"],
    "total_atual":     ["Total atual", "Saldo Atual"],
    "ganho":           ["Ganho", "Lucro/Prejuízo"],
    "recebido":        ["Recebido", "Valor Liquido", "Líquido"],
    "data_pgto":       ["Data pgto.", "Pagamento", "Data Pagamento"],
}

_MONTH_MAP = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}


def _get_col(row: dict, alias_key: str) -> str:
    for alias in _COLUMN_ALIASES.get(alias_key, []):
        if alias in row:
            return str(row[alias]).strip()
    return ""


def _detect_myprofit_type(fieldnames: set[str]) -> str | None:
    """Retorna 'POSITION' | 'DIVIDEND' | 'PORTFOLIO_EVO' | None."""
    # POSITION: tem Preço médio e Preço atual
    if any(a in fieldnames for a in _COLUMN_ALIASES["preco_medio"]) and \
       any(a in fieldnames for a in _COLUMN_ALIASES["preco_atual"]):
        return "POSITION"
    # DIVIDEND: tem "Data pgto." + "Recebido"
    if any(a in fieldnames for a in _COLUMN_ALIASES["data_pgto"]) and \
       any(a in fieldnames for a in _COLUMN_ALIASES["recebido"]):
        return "DIVIDEND"
    # PORTFOLIO_EVO: tem "% Mensal" e "Patrimônio"
    if "% Mensal" in fieldnames and "Patrimônio" in fieldnames:
        return "PORTFOLIO_EVO"
    return None


def _parse_myprofit_month(val: str):
    """Converte 'jan-24' → date(2024, 1, 1)."""
    from datetime import date
    if not val:
        return None
    val = val.strip().lower()
    parts = val.split("-")
    if len(parts) == 2:
        m_str, y_str = parts
        m = _MONTH_MAP.get(m_str)
        if m and y_str.isdigit():
            year = int(y_str)
            year = 2000 + year if year < 100 else year
            return date(year, m, 1)
    return None


class MyProfitNormalizer:
    """
    Normalizer unificado para os 3 formatos de arquivo do MyProfit.
    Detecta automaticamente o tipo por análise de colunas.
    """

    @property
    def source_id(self) -> str:
        return _SOURCE_ID

    @property
    def accepted_extensions(self) -> list[str]:
        return [".csv"]

    def can_handle(self, file_name: str, raw_content: str) -> bool:
        if not file_name.lower().endswith(".csv"):
            return False
        try:
            sample = raw_content[:2048]
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.DictReader(StringIO(raw_content[:4096]), dialect=dialect)
            fieldnames = set(reader.fieldnames or [])
            return _detect_myprofit_type(fieldnames) is not None
        except Exception:
            return False

    def normalize(
        self,
        raw_content: str | bytes,
        import_run_id: str,
        snapshot_date=None,  # opcional para POSITION
    ) -> list[RawFinancialEvent]:
        if isinstance(raw_content, bytes):
            raw_content = raw_content.decode("utf-8-sig")

        try:
            dialect = csv.Sniffer().sniff(raw_content[:2048])
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(StringIO(raw_content), dialect=dialect)
        fieldnames = set(reader.fieldnames or [])
        myprofit_type = _detect_myprofit_type(fieldnames)

        if myprofit_type == "POSITION":
            return self._normalize_positions(reader, import_run_id, snapshot_date)
        elif myprofit_type == "DIVIDEND":
            return self._normalize_dividends(reader, import_run_id)
        elif myprofit_type == "PORTFOLIO_EVO":
            return self._normalize_evolution(reader, import_run_id)
        else:
            logger.error(f"[{_SOURCE_ID}] Tipo de arquivo não reconhecido. Colunas: {fieldnames}")
            return []

    def _normalize_positions(self, reader, import_run_id: str, snapshot_date) -> list[RawFinancialEvent]:
        events = []
        for line_no, row in enumerate(reader, start=2):
            ticker = _get_col(row, "ativo").upper()
            if not ticker or ticker.startswith("TOTAL") or "ATIVOS" in ticker:
                continue

            quantidade = parse_br_currency(_get_col(row, "quantidade"))
            if quantidade is None:
                continue

            preco_medio     = parse_br_currency(_get_col(row, "preco_medio")) or Decimal("0")
            total_investido = parse_br_currency(_get_col(row, "total_investido")) or Decimal("0")
            preco_atual     = parse_br_currency(_get_col(row, "preco_atual")) or Decimal("0")
            total_atual     = parse_br_currency(_get_col(row, "total_atual")) or Decimal("0")
            ganho           = parse_br_currency(_get_col(row, "ganho")) or Decimal("0")

            date_str = snapshot_date.isoformat() if snapshot_date else "0000-00-00"
            total_atual_cents = int(total_atual * 100)

            semantic_id = make_semantic_id(
                _SOURCE_ID, EventType.POSITION, ticker, date_str,
            )
            cross_fp = make_cross_fingerprint(
                EventType.POSITION, ticker, date_str,
            )

            events.append(build_raw_event(
                event_type=EventType.POSITION,
                source=_SOURCE_ID,
                import_run_id=import_run_id,
                semantic_id=semantic_id,
                cross_fingerprint=cross_fp,
                event_date=snapshot_date,
                amount_cents=total_atual_cents,
                source_line_no=line_no,
                raw_content=",".join(str(v) for v in row.values()),
                metadata={
                    "ticker": ticker,
                    "quantidade": str(quantidade),
                    "preco_medio": str(preco_medio),
                    "total_investido": str(total_investido),
                    "preco_atual": str(preco_atual),
                    "total_atual": str(total_atual),
                    "ganho": str(ganho),
                    "data_snapshot": date_str,
                },
            ))

        logger.info(f"[{_SOURCE_ID}/POSITION] {len(events)} posições normalizadas")
        return events

    def _normalize_dividends(self, reader, import_run_id: str) -> list[RawFinancialEvent]:
        from utils.transformers import generate_economic_id
        events = []
        for line_no, row in enumerate(reader, start=2):
            ticker  = _get_col(row, "ativo").upper().strip()
            dt_str  = _get_col(row, "data_pgto")
            val_str = _get_col(row, "recebido")

            if not ticker or not dt_str:
                continue

            dt_obj = parse_br_date(dt_str)
            valor  = parse_br_currency(val_str)

            if not dt_obj or valor is None:
                logger.error(f"[{_SOURCE_ID}/DIVIDEND:L{line_no}] Data/Valor inválidos.")
                continue

            tipo_evento = "DIVIDENDO"
            amount_cents = int(valor * 100)
            id_economico = generate_economic_id(ticker, dt_obj, valor, tipo_evento)

            semantic_id = make_semantic_id(
                _SOURCE_ID, EventType.DIVIDEND, id_economico,
            )
            cross_fp = make_cross_fingerprint(
                EventType.DIVIDEND, dt_obj.isoformat(),
                abs(amount_cents), ticker,
            )

            events.append(build_raw_event(
                event_type=EventType.DIVIDEND,
                source=_SOURCE_ID,
                import_run_id=import_run_id,
                semantic_id=semantic_id,
                cross_fingerprint=cross_fp,
                event_date=dt_obj,
                amount_cents=amount_cents,
                external_id=id_economico,
                source_line_no=line_no,
                raw_content=",".join(str(v) for v in row.values()),
                metadata={
                    "ticker": ticker,
                    "tipo_evento": tipo_evento,
                    "id_economico": id_economico,
                    "valor_liquido": str(valor),
                },
            ))

        logger.info(f"[{_SOURCE_ID}/DIVIDEND] {len(events)} proventos normalizados")
        return events

    def _normalize_evolution(self, reader, import_run_id: str) -> list[RawFinancialEvent]:
        events = []
        for line_no, row in enumerate(reader, start=2):
            dt_str = row.get("Data", "")
            if not dt_str or dt_str.count(",") > 5:
                continue

            dt_obj = _parse_myprofit_month(dt_str)
            if not dt_obj:
                continue

            patrimonio = parse_br_currency(row.get("Patrimônio")) or Decimal("0")
            patrimonio_cents = int(patrimonio * 100)

            semantic_id = make_semantic_id(
                _SOURCE_ID, EventType.PORTFOLIO_EVO, dt_obj.isoformat(),
            )
            cross_fp = make_cross_fingerprint(
                EventType.PORTFOLIO_EVO, dt_obj.isoformat(),
            )

            meta = {
                "reference_month": dt_obj.isoformat(),
                "rentabilidade_mensal_pct": str(parse_br_currency(row.get("% Mensal")) or 0),
                "rentabilidade_acumulada_pct": str(parse_br_currency(row.get("% Acumulada")) or 0),
                "patrimonio_cents": patrimonio_cents,
                "compras_cents": int((parse_br_currency(row.get("Compras")) or Decimal("0")) * 100),
                "vendas_cents": int((parse_br_currency(row.get("Vendas")) or Decimal("0")) * 100),
                "op_finalizadas_cents": int((parse_br_currency(row.get("Op. Finalizadas")) or Decimal("0")) * 100),
                "proventos_cents": int((parse_br_currency(row.get("Proventos")) or Decimal("0")) * 100),
                "ibov_mensal_pct": str(parse_br_currency(row.get("IBOV Mensal")) or 0),
                "ibov_acumulado_pct": str(parse_br_currency(row.get("IBOV Acumulado")) or 0),
                "cdi_mensal_pct": str(parse_br_currency(row.get("CDI Mensal")) or 0),
                "cdi_acumulado_pct": str(parse_br_currency(row.get("CDI Acumulado")) or 0),
                "ipca_mensal_pct": str(parse_br_currency(row.get("IPCA Mensal")) or 0),
                "ipca_acumulado_pct": str(parse_br_currency(row.get("IPCA Acumulado")) or 0),
                "ifix_mensal_pct": str(parse_br_currency(row.get("IFIX Mensal")) or 0),
                "ifix_acumulado_pct": str(parse_br_currency(row.get("IFIX Acumulado")) or 0),
                "sp500_mensal_pct": str(parse_br_currency(row.get("S&P Mensal")) or 0),
                "sp500_acumulado_pct": str(parse_br_currency(row.get("S&P Acumulado")) or 0),
                "idiv_mensal_pct": str(parse_br_currency(row.get("IDIV Mensal")) or 0),
                "idiv_acumulado_pct": str(parse_br_currency(row.get("IDIV Acumulado")) or 0),
            }

            events.append(build_raw_event(
                event_type=EventType.PORTFOLIO_EVO,
                source=_SOURCE_ID,
                import_run_id=import_run_id,
                semantic_id=semantic_id,
                cross_fingerprint=cross_fp,
                event_date=None,
                reference_month=dt_obj,
                amount_cents=patrimonio_cents,
                source_line_no=line_no,
                raw_content=",".join(str(v) for v in row.values()),
                metadata=meta,
            ))

        logger.info(f"[{_SOURCE_ID}/PORTFOLIO_EVO] {len(events)} meses normalizados")
        return events
