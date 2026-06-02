from __future__ import annotations

import sqlite3
from pathlib import Path
import re

DB_PATH = Path(__file__).resolve().parents[1] / "fin_analytics.db"

TERMS = ["Belezaren", "Cacau Show", "Casa Pronta"]
ZERO_PATTERN = re.compile(r"\b0\s*/\s*\d+\s*x?\b", re.IGNORECASE)


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        for term in TERMS:
            print(f"=== {term} ===")
            rows = conn.execute(
                """
                SELECT data, descricao_original, natureza, macro_categoria, valor, valor_cents
                FROM transactions
                WHERE descricao_original LIKE ?
                ORDER BY data ASC, descricao_original ASC
                """,
                (f"%{term}%",),
            ).fetchall()

            print(f"ROWS: {len(rows)}")
            for row in rows:
                print(
                    f"- {row['data']} | {row['natureza']} | {row['macro_categoria']} | "
                    f"{row['descricao_original']} | valor={row['valor']} | cents={row['valor_cents']}"
                )
            print()

        print("=== 0/X candidates (Python scan) ===")
        all_rows = conn.execute(
            """
            SELECT data, descricao_original, natureza, macro_categoria, valor
            FROM transactions
            ORDER BY data ASC, descricao_original ASC
            """
        ).fetchall()
        zero_matches = [row for row in all_rows if ZERO_PATTERN.search(row["descricao_original"] or "")]
        print(f"ROWS: {len(zero_matches)}")
        for row in zero_matches[:20]:
            print(
                f"- {row['data']} | {row['natureza']} | {row['macro_categoria']} | "
                f"{row['descricao_original']} | valor={row['valor']}"
            )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
