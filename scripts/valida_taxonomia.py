from __future__ import annotations

import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.repository import DatabaseManager
from app.api.services.pierre_parser import PierreParser
from services.categorizer import SmartCategorizer
from utils.semantic import normalize_description


DB_PATH = ROOT / "fin_analytics.db"
RULES_PATH = ROOT / "taxonomy" / "rules.csv"


def _load_rules() -> list[dict[str, str]]:
    with RULES_PATH.open(mode="r", encoding="utf-8") as file_handle:
        reader = csv.DictReader(file_handle)
        return [row for row in reader if row.get("keyword")]
def main() -> None:
    raw_csv_path = ROOT / "data" / "raw" / "nubank" / "Extrato Pierre Processado.csv"

    with raw_csv_path.open("rb") as file_handle:
        raw_bytes = file_handle.read()

    raw_text = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            raw_text = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if raw_text is None:
        raw_text = raw_bytes.decode("utf-8", errors="replace")

    parser = PierreParser()
    categorizer = SmartCategorizer(RULES_PATH)
    parsed_rows = parser.parse(raw_text)

    db = DatabaseManager(DB_PATH)
    export_rows: list[dict[str, object]] = []

    with db._get_connection() as conn:
        cursor = conn.cursor()
        for row in parsed_rows:
            classified = categorizer.classify(row)
            cursor.execute(
                """
                UPDATE transactions
                SET macro_categoria = ?,
                    sub_categoria = ?,
                    subnatureza = ?,
                    natureza = ?,
                    perfil = ?,
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id_economico = ? AND origin = 'PIERRE'
                """,
                (
                    classified["macro"],
                    classified["sub"],
                    classified["sub"],
                    classified["natureza"].value,
                    classified["perfil"].value,
                    row["id_economico"],
                ),
            )

            export_rows.append(
                {
                    "source_line_no": row["source_line_no"],
                    "descricao": row["descricao_original"],
                    "categoria_origem": row.get("categoria_origem") or "",
                    "macro_categoria": classified["macro"],
                    "sub_categoria": classified["sub"],
                }
            )

        conn.commit()

        total = cursor.execute("SELECT COUNT(*) FROM transactions WHERE origin='PIERRE'").fetchone()[0]
        quarantine = cursor.execute(
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE origin='PIERRE'
              AND (COALESCE(macro_categoria, '') = 'OUTROS' OR COALESCE(sub_categoria, '') = 'INDEFINIDO')
            """
        ).fetchone()[0]
        classified = total - quarantine
        coverage = (classified / total * 100) if total else 0.0

    export_path = ROOT / "auditoria_taxonomia_v2.csv"
    with export_path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(
            file_handle,
            fieldnames=["source_line_no", "descricao", "categoria_origem", "macro_categoria", "sub_categoria"],
        )
        writer.writeheader()
        writer.writerows(export_rows)

    print("=== TAXONOMIA CALIBRADA ===")
    print(f"Total Pierre: {total}")
    print(f"Classificadas: {classified}")
    print(f"Quarentena: {quarantine}")
    print(f"Cobertura: {coverage:.4f}%")
    print(f"CSV exportado: {export_path}")


if __name__ == "__main__":
    main()