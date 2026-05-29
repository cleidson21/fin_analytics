import csv
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

from models.core import CanonicalEvent, CanonicalPosition, Source
from utils.transformers import generate_economic_id, parse_br_currency, parse_br_date

logger = logging.getLogger(__name__)

COLUMN_ALIASES = {
    "ativo": ["Ativo", "Ticker", "Código", "Papel"],
    "quantidade": ["Qtd", "Quantidade", "Cotas"],
    "preco_medio": ["Preço médio", "PM"],
    "total_investido": ["Total investido", "Valor Pago"],
    "preco_atual": ["Preço atual", "Cotação"],
    "total_atual": ["Total atual", "Saldo Atual"],
    "ganho": ["Ganho", "Lucro/Prejuízo"],
    "recebido": ["Recebido", "Valor Liquido", "Líquido"],
    "data_pgto": ["Data pgto.", "Pagamento", "Data Pagamento"],
}


def _get_col(row: dict, alias_key: str) -> str:
    """Busca o valor na linha usando o mapa de aliases."""
    for alias in COLUMN_ALIASES.get(alias_key, []):
        if alias in row:
            return row[alias]
    return ""


def parse_positions(file_path: Path, snapshot_date: date) -> list[CanonicalPosition]:
    """Lê tableExport.csv e converte para CanonicalPosition."""
    positions: list[CanonicalPosition] = []

    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)

        for row_num, row in enumerate(reader, start=2):
            ticker = _get_col(row, "ativo").strip()
            ticker_upper = ticker.upper()
            if not ticker or ticker_upper.startswith("TOTAL") or "ATIVOS" in ticker_upper:
                continue

            quantidade = parse_br_currency(_get_col(row, "quantidade"))
            if quantidade is None:
                continue

            positions.append(
                {
                    "source": Source.MYPROFIT,
                    "data_snapshot": snapshot_date,
                    "ticker": ticker,
                    "quantidade": quantidade,
                    "preco_medio": parse_br_currency(_get_col(row, "preco_medio")) or Decimal("0"),
                    "total_investido": parse_br_currency(_get_col(row, "total_investido")) or Decimal("0"),
                    "preco_atual": parse_br_currency(_get_col(row, "preco_atual")) or Decimal("0"),
                    "total_atual": parse_br_currency(_get_col(row, "total_atual")) or Decimal("0"),
                    "ganho": parse_br_currency(_get_col(row, "ganho")) or Decimal("0"),
                }
            )

    logger.info(f"Sucesso: {file_path.name} ({len(positions)} posições extraídas)")
    return positions


def parse_dividends(file_path: Path) -> list[CanonicalEvent]:
    """Lê proventos.csv e converte para CanonicalEvent."""
    events: list[CanonicalEvent] = []

    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)

        for row_num, row in enumerate(reader, start=2):
            ticker = _get_col(row, "ativo").strip()
            dt_str = _get_col(row, "data_pgto")
            valor_str = _get_col(row, "recebido")

            if not ticker or not dt_str:
                continue

            dt_obj = parse_br_date(dt_str)
            valor_dec = parse_br_currency(valor_str)

            if not dt_obj or valor_dec is None:
                logger.error(f"[{file_path.name}:{row_num}] Falha crítica nos dados (Data/Valor). Ignorando.")
                continue

            tipo_evento = "DIVIDENDO"
            id_economico = generate_economic_id(ticker, dt_obj, valor_dec, tipo_evento)

            events.append(
                {
                    "id_economico": id_economico,
                    "source": Source.MYPROFIT,
                    "tipo_evento": tipo_evento,
                    "ticker": ticker,
                    "data_pagamento": dt_obj,
                    "valor_liquido": valor_dec,
                }
            )

    return events