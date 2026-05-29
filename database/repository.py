import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: Path = Path("fin_analytics.db")):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        schema_path = Path("database/schema.sql")
        if schema_path.exists():
            with self._get_connection() as conn:
                with open(schema_path, "r", encoding="utf-8") as file_handle:
                    conn.executescript(file_handle.read())

    def register_etl_run(self, source: str, file_name: str, rows_read: int, checksum: str = "") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO etl_runs (source, file_name, rows_read, rows_inserted, rows_updated, checksum)
                VALUES (?, ?, ?, 0, 0, ?)
                """,
                (source, file_name, rows_read, checksum),
            )
            conn.commit()
            return cursor.lastrowid

    def update_etl_run_metrics(self, run_id: int, inserted: int, updated: int):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE etl_runs
                SET rows_inserted = ?, rows_updated = ?
                WHERE id = ?
                """,
                (inserted, updated, run_id),
            )
            conn.commit()

    def upsert_transactions(self, transactions: list, categorizer) -> tuple[int, int]:
        if not transactions:
            return 0, 0

        inserted = 0
        updated = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for transaction in transactions:
                existing = cursor.execute(
                    "SELECT 1 FROM transactions WHERE id_economico = ?",
                    (transaction["id_economico"],),
                ).fetchone()

                cat = categorizer.classify(transaction)

                cursor.execute(
                    """
                    INSERT INTO transactions (
                        id_economico, source, data, descricao_original, descricao_normalizada,
                        valor, identificador_externo, macro_categoria, sub_categoria, natureza, perfil
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id_economico) DO UPDATE SET
                        macro_categoria = excluded.macro_categoria,
                        sub_categoria = excluded.sub_categoria,
                        natureza = excluded.natureza,
                        perfil = excluded.perfil,
                        descricao_normalizada = excluded.descricao_normalizada,
                        atualizado_em = CURRENT_TIMESTAMP
                    """,
                    (
                        transaction["id_economico"],
                        transaction["source"].value,
                        transaction["data"].isoformat(),
                        transaction["descricao_original"],
                        transaction["descricao_normalizada"],
                        str(transaction["valor"]),
                        transaction["identificador_externo"],
                        cat["macro"],
                        cat["sub"],
                        cat["natureza"].value,
                        cat["perfil"].value,
                    ),
                )

                if existing is None:
                    inserted += 1
                else:
                    updated += 1

            conn.commit()

        return inserted, updated

    def upsert_positions(self, positions: list) -> tuple[int, int]:
        if not positions:
            return 0, 0

        inserted = 0
        updated = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for position in positions:
                existing = cursor.execute(
                    "SELECT 1 FROM positions WHERE ticker = ? AND data_snapshot = ?",
                    (position["ticker"], position["data_snapshot"].isoformat()),
                ).fetchone()

                cursor.execute(
                    """
                    INSERT INTO positions (
                        ticker, data_snapshot, source, quantidade, preco_medio,
                        total_investido, preco_atual, total_atual, ganho
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ticker, data_snapshot) DO UPDATE SET
                        source = excluded.source,
                        quantidade = excluded.quantidade,
                        preco_medio = excluded.preco_medio,
                        total_investido = excluded.total_investido,
                        preco_atual = excluded.preco_atual,
                        total_atual = excluded.total_atual,
                        ganho = excluded.ganho,
                        atualizado_em = CURRENT_TIMESTAMP
                    """,
                    (
                        position["ticker"],
                        position["data_snapshot"].isoformat(),
                        position["source"].value,
                        str(position["quantidade"]),
                        str(position["preco_medio"]),
                        str(position["total_investido"]),
                        str(position["preco_atual"]),
                        str(position["total_atual"]),
                        str(position["ganho"]),
                    ),
                )

                if existing is None:
                    inserted += 1
                else:
                    updated += 1

            conn.commit()

        return inserted, updated

    def upsert_dividends(self, dividends: list) -> tuple[int, int]:
        if not dividends:
            return 0, 0

        inserted = 0
        updated = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for dividend in dividends:
                existing = cursor.execute(
                    "SELECT 1 FROM dividends WHERE id_economico = ?",
                    (dividend["id_economico"],),
                ).fetchone()

                cursor.execute(
                    """
                    INSERT INTO dividends (
                        id_economico, source, ticker, tipo_evento,
                        data_pagamento, valor_liquido
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id_economico) DO UPDATE SET
                        source = excluded.source,
                        ticker = excluded.ticker,
                        tipo_evento = excluded.tipo_evento,
                        data_pagamento = excluded.data_pagamento,
                        valor_liquido = excluded.valor_liquido,
                        atualizado_em = CURRENT_TIMESTAMP
                    """,
                    (
                        dividend["id_economico"],
                        dividend["source"].value,
                        dividend["ticker"],
                        dividend["tipo_evento"],
                        dividend["data_pagamento"].isoformat(),
                        str(dividend["valor_liquido"]),
                    ),
                )

                if existing is None:
                    inserted += 1
                else:
                    updated += 1

            conn.commit()

        return inserted, updated