from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.services.pierre_parser import PierreParser
from database.repository import DatabaseManager
from parsers.myprofit import parse_dividends, parse_positions, parse_evolution
from services.categorizer import SmartCategorizer


DB_PATH = ROOT / "fin_analytics.db"
PIERRE_PATH = ROOT / "Extrato_Pierre_Auditado.csv"
MYPROFIT_DIR = ROOT / "data" / "raw" / "myprofit"


def _read_text(path: Path) -> str:
    raw_bytes = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue

    return raw_bytes.decode("utf-8", errors="replace")


def _count_rows(path: Path) -> int:
    text = _read_text(path)
    sample = text[:4096]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    return sum(1 for _ in reader)


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    db = DatabaseManager(DB_PATH)
    categorizer = SmartCategorizer(ROOT / "taxonomy" / "rules.csv")
    pierre_parser = PierreParser()

    pierre_text = _read_text(PIERRE_PATH)
    pierre_items = pierre_parser.parse(pierre_text)
    pierre_total_rows = _count_rows(PIERRE_PATH)
    pierre_inserted, pierre_updated = db.upsert_transactions(pierre_items, categorizer)
    pierre_rejected = max(pierre_total_rows - len(pierre_items), 0)

    positions_path = MYPROFIT_DIR / "tableExport.csv"
    dividends_path = MYPROFIT_DIR / "proventos.csv"
    evolution_path = MYPROFIT_DIR / "Evolucao_carteira.csv"

    positions = parse_positions(positions_path, date.today())
    dividends = parse_dividends(dividends_path)
    evos = parse_evolution(evolution_path) if evolution_path.exists() else []

    positions_inserted, positions_updated = db.upsert_positions(positions)
    dividends_inserted, dividends_updated = db.upsert_dividends(dividends)
    evos_inserted, evos_updated = db.upsert_portfolio_evolution(evos)

    positions_total_rows = _count_rows(positions_path) if positions_path.exists() else 0
    dividends_total_rows = _count_rows(dividends_path) if dividends_path.exists() else 0
    evos_total_rows = _count_rows(evolution_path) if evolution_path.exists() else 0
    myprofit_rejected = max(positions_total_rows - len(positions), 0) + max(dividends_total_rows - len(dividends), 0) + max(evos_total_rows - len(evos), 0)

    print("=== CARGA ZERO ===")
    print(f"Pierre carregado: {len(pierre_items)} transacoes")
    print(f"Pierre rejeitadas: {pierre_rejected}")
    print(f"Pierre source_line_no gravado: {'sim' if pierre_items and all('source_line_no' in item for item in pierre_items) else 'nao'}")
    print(f"MyProfit carregado: {len(positions)} posicoes, {len(dividends)} dividendos e {len(evos)} evoluções")
    print(f"MyProfit rejeitadas: {myprofit_rejected}")
    print(f"DB inserted/updated Pierre: {pierre_inserted}/{pierre_updated}")
    print(f"DB inserted/updated MyProfit posicoes: {positions_inserted}/{positions_updated}")
    print(f"DB inserted/updated MyProfit dividendos: {dividends_inserted}/{dividends_updated}")
    print(f"DB inserted/updated MyProfit evolucao: {evos_inserted}/{evos_updated}")


if __name__ == "__main__":
    main()