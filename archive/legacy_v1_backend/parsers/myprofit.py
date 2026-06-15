import csv
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

from models.core import CanonicalEvent, CanonicalPosition, CanonicalPortfolioEvolution, Source
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


MONTH_MAP = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
}


def parse_myprofit_month_year(val: str) -> date | None:
    if not val:
        return None
    val = val.strip().lower()
    parts = val.split("-")
    if len(parts) == 2:
        m_str, y_str = parts
        m = MONTH_MAP.get(m_str)
        if m and y_str.isdigit():
            return date(int(y_str), m, 1)
    return None


def parse_evolution(file_path: Path) -> list[CanonicalPortfolioEvolution]:
    evos: list[CanonicalPortfolioEvolution] = []
    
    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)

        for row_num, row in enumerate(reader, start=2):
            dt_str = row.get("Data", "")
            # Pula linhas vazias (ex: a última linha cheia de vírgulas)
            if not dt_str or dt_str.count(",") > 5:
                continue

            dt_obj = parse_myprofit_month_year(dt_str)
            if not dt_obj:
                continue

            rent_mensal = parse_br_currency(row.get("% Mensal")) or Decimal("0")
            rent_acumulada = parse_br_currency(row.get("% Acumulada")) or Decimal("0")
            patrimonio = parse_br_currency(row.get("Patrimônio")) or Decimal("0")
            compras = parse_br_currency(row.get("Compras")) or Decimal("0")
            vendas = parse_br_currency(row.get("Vendas")) or Decimal("0")
            op_finalizadas = parse_br_currency(row.get("Op. Finalizadas")) or Decimal("0")
            proventos = parse_br_currency(row.get("Proventos")) or Decimal("0")
            
            ibov_mensal = parse_br_currency(row.get("IBOV Mensal")) or Decimal("0")
            ibov_acum = parse_br_currency(row.get("IBOV Acumulado")) or Decimal("0")
            cdi_mensal = parse_br_currency(row.get("CDI Mensal")) or Decimal("0")
            cdi_acum = parse_br_currency(row.get("CDI Acumulado")) or Decimal("0")
            ipca_mensal = parse_br_currency(row.get("IPCA Mensal")) or Decimal("0")
            ipca_acum = parse_br_currency(row.get("IPCA Acumulado")) or Decimal("0")
            ifix_mensal = parse_br_currency(row.get("IFIX Mensal")) or Decimal("0")
            ifix_acum = parse_br_currency(row.get("IFIX Acumulado")) or Decimal("0")
            sp500_mensal = parse_br_currency(row.get("S&P Mensal")) or Decimal("0")
            sp500_acum = parse_br_currency(row.get("S&P Acumulado")) or Decimal("0")
            idiv_mensal = parse_br_currency(row.get("IDIV Mensal")) or Decimal("0")
            idiv_acum = parse_br_currency(row.get("IDIV Acumulado")) or Decimal("0")

            evos.append(
                {
                    "source": Source.MYPROFIT,
                    "reference_month": dt_obj,
                    "rentabilidade_mensal_pct": rent_mensal,
                    "rentabilidade_acumulada_pct": rent_acumulada,
                    "patrimonio_cents": int(patrimonio * 100),
                    "compras_cents": int(compras * 100),
                    "vendas_cents": int(vendas * 100),
                    "op_finalizadas_cents": int(op_finalizadas * 100),
                    "proventos_cents": int(proventos * 100),
                    "ibov_mensal_pct": ibov_mensal,
                    "ibov_acumulado_pct": ibov_acum,
                    "cdi_mensal_pct": cdi_mensal,
                    "cdi_acumulado_pct": cdi_acum,
                    "ipca_mensal_pct": ipca_mensal,
                    "ipca_acumulado_pct": ipca_acum,
                    "ifix_mensal_pct": ifix_mensal,
                    "ifix_acumulado_pct": ifix_acum,
                    "sp500_mensal_pct": sp500_mensal,
                    "sp500_acumulado_pct": sp500_acum,
                    "idiv_mensal_pct": idiv_mensal,
                    "idiv_acumulado_pct": idiv_acum,
                }
            )

    logger.info(f"Sucesso: {file_path.name} ({len(evos)} meses extraídos)")
    return evos