import logging
import sqlite3
import uuid
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from services.categorizer import SmartCategorizer
from utils.semantic import normalize_description
from utils.transformers import generate_economic_id

logger = logging.getLogger(__name__)


def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _decimal_to_cents(value) -> int:
    decimal_value = _to_decimal(value)
    cents = (decimal_value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def _cents_to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return (Decimal(int(value)) / Decimal("100")).quantize(Decimal("0.01"))


def _source_value(source) -> str:
    return getattr(source, "value", source)


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
                self._apply_transaction_migrations(conn)

    def _apply_transaction_migrations(self, conn):
        def ensure_columns(table_name: str, columns: tuple[tuple[str, str], ...]):
            existing_columns = {
                row["name"]
                for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            }

            for column_name, column_type in columns:
                if column_name not in existing_columns:
                    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

        ensure_columns(
            "transactions",
            (
                ("origin", "TEXT"),
                ("domain", "TEXT"),
                ("import_run_id", "TEXT"),
                ("source_line_no", "INTEGER"),
                ("valor_cents", "INTEGER"),
                ("classificacao_fonte", "TEXT NOT NULL DEFAULT 'ETL'"),
            ),
        )
        ensure_columns(
            "staging_imports",
            (
                ("source_line_no", "INTEGER"),
                ("amount_cents", "INTEGER"),
            ),
        )
        ensure_columns(
            "dividends",
            (("valor_liquido_cents", "INTEGER"),),
        )

        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_staging_imports_run_line ON staging_imports(import_run_id, source_line_no)"
        )
        conn.commit()

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

    def create_import_run(self, raw_text: str, checksum: str) -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            existing = cursor.execute(
                "SELECT id FROM import_runs WHERE payload_checksum = ? ORDER BY created_at DESC LIMIT 1",
                (checksum,),
            ).fetchone()

            if existing is not None:
                return str(existing["id"])

            run_id = uuid.uuid4().hex
            cursor.execute(
                """
                INSERT INTO import_runs (id, raw_payload, payload_checksum)
                VALUES (?, ?, ?)
                """,
                (run_id, raw_text, checksum),
            )
            conn.commit()
            return run_id

    def insert_staging_items(self, run_id: str, items: list) -> list[dict]:
        if not items:
            return []

        inserted_items: list[dict] = []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for item in items:
                source_line_no = item.get("source_line_no")
                date_value = str(item.get("date", "")).strip()
                description = str(item.get("description", "")).strip()
                account = str(item.get("account", "")).strip()
                category_inferred = str(item.get("category_inferred", "")).strip()
                status = str(item.get("status", "PENDING")).strip().upper() or "PENDING"

                amount_decimal = _to_decimal(item.get("amount", 0))
                amount_cents = _decimal_to_cents(amount_decimal)
                staging_amount = None

                if source_line_no is None or not date_value or not description:
                    status = "ERROR"

                duplicate = cursor.execute(
                    """
                    SELECT 1
                    FROM staging_imports
                    WHERE import_run_id = ?
                      AND source_line_no = ?
                    LIMIT 1
                    """,
                    (run_id, source_line_no),
                ).fetchone()

                if duplicate is not None:
                    inserted_items.append(
                        {
                            "source_line_no": source_line_no,
                            "date": date_value,
                            "description": description,
                            "amount": amount_decimal,
                            "account": account,
                            "category_inferred": category_inferred,
                            "status": "DUPLICATE",
                        }
                    )
                    continue

                cursor.execute(
                    """
                    INSERT INTO staging_imports (
                        import_run_id, source_line_no, date, description, amount, amount_cents, account, category_inferred, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        source_line_no,
                        date_value,
                        description,
                        staging_amount,
                        amount_cents,
                        account,
                        category_inferred,
                        status,
                    ),
                )

                staging_id = cursor.lastrowid
                inserted_items.append(
                    {
                        "id": staging_id,
                        "source_line_no": source_line_no,
                        "import_run_id": run_id,
                        "date": date_value,
                        "description": description,
                        "amount": amount_decimal,
                        "account": account,
                        "category_inferred": category_inferred,
                        "status": status,
                    }
                )

            conn.commit()

        return inserted_items

    def process_staging_to_transactions(self, run_id: str) -> list[dict]:
        processed_preview: list[dict] = []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            staging_rows = cursor.execute(
                """
                SELECT id, import_run_id, source_line_no, date, description, amount, amount_cents, account, category_inferred, status
                FROM staging_imports
                WHERE import_run_id = ?
                ORDER BY id ASC
                """,
                (run_id,),
            ).fetchall()

            categorizer = SmartCategorizer(Path("taxonomy/rules.csv"))

            for row in staging_rows:
                row_status = str(row["status"] or "PENDING").upper()

                if row_status in {"DUPLICATE", "ERROR", "IMPORTED"}:
                    processed_preview.append(
                        {
                            "date": row["date"],
                            "description": row["description"],
                            "amount": _cents_to_decimal(row["amount_cents"] if row["amount_cents"] is not None else row["amount"]),
                            "status": row_status,
                        }
                    )
                    continue

                date_value = str(row["date"] or "").strip()
                description = str(row["description"] or "").strip()
                account = str(row["account"] or "").strip()

                if not date_value or not description:
                    cursor.execute(
                        "UPDATE staging_imports SET status = 'ERROR' WHERE id = ?",
                        (row["id"],),
                    )
                    processed_preview.append(
                        {
                            "date": date_value,
                            "description": description,
                            "amount": _cents_to_decimal(row["amount_cents"] if row["amount_cents"] is not None else row["amount"]),
                            "status": "ERROR",
                        }
                    )
                    continue

                description_normalized = normalize_description(description)
                try:
                    amount_cents = int(row["amount_cents"] if row["amount_cents"] is not None else _decimal_to_cents(row["amount"]))
                    amount_decimal = _cents_to_decimal(amount_cents)
                except Exception:
                    cursor.execute(
                        "UPDATE staging_imports SET status = 'ERROR' WHERE id = ?",
                        (row["id"],),
                    )
                    processed_preview.append(
                        {
                            "date": date_value,
                            "description": description,
                            "amount": row["amount"],
                            "status": "ERROR",
                        }
                    )
                    continue

                source = account.upper() if account else "PIERRE"
                transaction_id = generate_economic_id(
                    "MANUAL",
                    "PIERRE",
                    row["source_line_no"],
                    date_value,
                    description_normalized,
                    str(amount_decimal),
                    source,
                )
                transaction_payload = {
                    "id_economico": transaction_id,
                    "source": source,
                    "origin": "PIERRE",
                    "domain": "FINANCE",
                    "import_run_id": run_id,
                    "source_line_no": row["source_line_no"],
                    "data": date_value,
                    "descricao_original": description,
                    "descricao_normalizada": description_normalized,
                    "valor": amount_decimal,
                    "valor_cents": amount_cents,
                    "identificador_externo": None,
                    "categoria_origem": row["category_inferred"],
                }
                cat = categorizer.classify(transaction_payload)

                cursor.execute(
                    """
                    INSERT INTO transactions (
                        id_economico, source, origin, domain, import_run_id, source_line_no, data,
                        descricao_original, descricao_normalizada, valor, valor_cents, identificador_externo,
                        macro_categoria, sub_categoria, subnatureza, natureza, perfil, classificacao_fonte
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ETL')
                    ON CONFLICT(id_economico) DO UPDATE SET
                        origin = excluded.origin,
                        domain = excluded.domain,
                        import_run_id = excluded.import_run_id,
                        source_line_no = excluded.source_line_no,
                        -- Só atualiza classificação se a transação ainda não foi marcada como MANUAL
                        macro_categoria = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.macro_categoria ELSE excluded.macro_categoria END,
                        sub_categoria   = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.sub_categoria   ELSE excluded.sub_categoria   END,
                        subnatureza     = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.subnatureza     ELSE excluded.subnatureza     END,
                        natureza        = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.natureza        ELSE excluded.natureza        END,
                        perfil          = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.perfil          ELSE excluded.perfil          END,
                        atualizado_em = CURRENT_TIMESTAMP
                    """,
                    (
                        transaction_payload["id_economico"],
                        transaction_payload["source"],
                        transaction_payload["origin"],
                        transaction_payload["domain"],
                        transaction_payload["import_run_id"],
                        transaction_payload["source_line_no"],
                        transaction_payload["data"],
                        transaction_payload["descricao_original"],
                        transaction_payload["descricao_normalizada"],
                        amount_cents,
                        amount_cents,
                        transaction_payload["identificador_externo"],
                        cat["macro"],
                        cat["sub"],
                        cat["sub"],
                        cat["natureza"].value,
                        cat["perfil"].value,
                    ),
                )

                cursor.execute(
                    "UPDATE staging_imports SET status = 'IMPORTED' WHERE id = ?",
                    (row["id"],),
                )
                processed_preview.append(
                    {
                        "date": date_value,
                        "description": description,
                        "amount": amount_decimal,
                        "status": "IMPORTED",
                    }
                )

            conn.commit()

        return processed_preview

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
                source_value = _source_value(transaction.get("source"))
                origin_value = transaction.get("origin") or source_value
                domain_value = transaction.get("domain") or "FINANCE"
                source_line_no = transaction.get("source_line_no")

                cursor.execute(
                    """
                    INSERT INTO transactions (
                        id_economico, source, origin, domain, source_line_no, data, descricao_original, descricao_normalizada,
                        valor, valor_cents, identificador_externo, macro_categoria, sub_categoria, subnatureza, natureza, perfil,
                        classificacao_fonte
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ETL')
                    ON CONFLICT(id_economico) DO UPDATE SET
                        source = excluded.source,
                        origin = excluded.origin,
                        domain = excluded.domain,
                        source_line_no = excluded.source_line_no,
                        descricao_normalizada = excluded.descricao_normalizada,
                        -- Só atualiza classificação se a transação ainda não foi marcada como MANUAL
                        macro_categoria = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.macro_categoria ELSE excluded.macro_categoria END,
                        sub_categoria   = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.sub_categoria   ELSE excluded.sub_categoria   END,
                        subnatureza     = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.subnatureza     ELSE excluded.subnatureza     END,
                        natureza        = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.natureza        ELSE excluded.natureza        END,
                        perfil          = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.perfil          ELSE excluded.perfil          END,
                        atualizado_em = CURRENT_TIMESTAMP
                    """,
                    (
                        transaction["id_economico"],
                        source_value,
                        origin_value,
                        domain_value,
                        source_line_no,
                        transaction["data"].isoformat(),
                        transaction["descricao_original"],
                        transaction["descricao_normalizada"],
                        _decimal_to_cents(transaction["valor"]),
                        _decimal_to_cents(transaction["valor"]),
                        transaction["identificador_externo"],
                        cat["macro"],
                        cat["sub"],
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
                        _source_value(position["source"]),
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
                        data_pagamento, valor_liquido, valor_liquido_cents
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id_economico) DO UPDATE SET
                        source = excluded.source,
                        ticker = excluded.ticker,
                        tipo_evento = excluded.tipo_evento,
                        data_pagamento = excluded.data_pagamento,
                        valor_liquido = excluded.valor_liquido,
                        valor_liquido_cents = excluded.valor_liquido_cents,
                        atualizado_em = CURRENT_TIMESTAMP
                    """,
                    (
                        dividend["id_economico"],
                        _source_value(dividend["source"]),
                        dividend["ticker"],
                        dividend["tipo_evento"],
                        dividend["data_pagamento"].isoformat(),
                        _decimal_to_cents(dividend["valor_liquido"]),
                        _decimal_to_cents(dividend["valor_liquido"]),
                    ),
                )

                if existing is None:
                    inserted += 1
                else:
                    updated += 1

            conn.commit()

        return inserted, updated


    def upsert_portfolio_evolution(self, evos: list) -> tuple[int, int]:
        if not evos:
            return 0, 0

        inserted = 0
        updated = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for evo in evos:
                existing = cursor.execute(
                    "SELECT 1 FROM portfolio_evolution WHERE reference_month = ?",
                    (evo["reference_month"].isoformat(),),
                ).fetchone()

                cursor.execute(
                    """
                    INSERT INTO portfolio_evolution (
                        reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,
                        patrimonio_cents, compras_cents, vendas_cents, op_finalizadas_cents, proventos_cents,
                        ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,
                        ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,
                        sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(reference_month) DO UPDATE SET
                        rentabilidade_mensal_pct = excluded.rentabilidade_mensal_pct,
                        rentabilidade_acumulada_pct = excluded.rentabilidade_acumulada_pct,
                        patrimonio_cents = excluded.patrimonio_cents,
                        compras_cents = excluded.compras_cents,
                        vendas_cents = excluded.vendas_cents,
                        op_finalizadas_cents = excluded.op_finalizadas_cents,
                        proventos_cents = excluded.proventos_cents,
                        ibov_mensal_pct = excluded.ibov_mensal_pct,
                        ibov_acumulado_pct = excluded.ibov_acumulado_pct,
                        cdi_mensal_pct = excluded.cdi_mensal_pct,
                        cdi_acumulado_pct = excluded.cdi_acumulado_pct,
                        ipca_mensal_pct = excluded.ipca_mensal_pct,
                        ipca_acumulado_pct = excluded.ipca_acumulado_pct,
                        ifix_mensal_pct = excluded.ifix_mensal_pct,
                        ifix_acumulado_pct = excluded.ifix_acumulado_pct,
                        sp500_mensal_pct = excluded.sp500_mensal_pct,
                        sp500_acumulado_pct = excluded.sp500_acumulado_pct,
                        idiv_mensal_pct = excluded.idiv_mensal_pct,
                        idiv_acumulado_pct = excluded.idiv_acumulado_pct
                    """,
                    (
                        evo["reference_month"].isoformat(),
                        str(evo["rentabilidade_mensal_pct"]),
                        str(evo["rentabilidade_acumulada_pct"]),
                        evo["patrimonio_cents"],
                        evo["compras_cents"],
                        evo["vendas_cents"],
                        evo["op_finalizadas_cents"],
                        evo["proventos_cents"],
                        str(evo["ibov_mensal_pct"]),
                        str(evo["ibov_acumulado_pct"]),
                        str(evo["cdi_mensal_pct"]),
                        str(evo["cdi_acumulado_pct"]),
                        str(evo["ipca_mensal_pct"]),
                        str(evo["ipca_acumulado_pct"]),
                        str(evo["ifix_mensal_pct"]),
                        str(evo["ifix_acumulado_pct"]),
                        str(evo["sp500_mensal_pct"]),
                        str(evo["sp500_acumulado_pct"]),
                        str(evo["idiv_mensal_pct"]),
                        str(evo["idiv_acumulado_pct"]),
                    ),
                )

                if existing is None:
                    inserted += 1
                else:
                    updated += 1

            conn.commit()

        return inserted, updated