import logging
import sqlite3
import uuid
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from services.categorizer import SmartCategorizer
from utils.semantic import normalize_description
from utils.transformers import generate_economic_id

logger = logging.getLogger(__name__)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


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


import math
def _cents_to_decimal(value) -> Decimal:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return Decimal("0.00")
    return (Decimal(int(value)) / Decimal("100")).quantize(Decimal("0.01"))


def _source_value(source) -> str:
    return getattr(source, "value", source)


from database.config import DATABASE_PATH

class DatabaseManager:
    def __init__(self, db_path: Path = DATABASE_PATH):
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
        ensure_columns(
            "import_runs",
            (
                ("rollback_timestamp", "TIMESTAMP"),
                ("rollback_reason", "TEXT"),
                ("rollback_user", "TEXT"),
            ),
        )

        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_staging_imports_run_line ON staging_imports(import_run_id, source_line_no)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_import_run ON transactions(import_run_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_source ON transactions(source)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_classificacao ON transactions(classificacao_fonte)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_staging_imports_run_status ON staging_imports(import_run_id, status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_dividends_ticker ON dividends(ticker)"
        )

        # ── Sprint 4.4: colunas de rastreabilidade raw_event ──
        ensure_columns("transactions", (("raw_event_id", "TEXT"),))
        ensure_columns("positions",    (("raw_event_id", "TEXT"),))
        ensure_columns("dividends",    (("raw_event_id", "TEXT"),))
        ensure_columns("import_runs",  (("pipeline_version", "TEXT DEFAULT 'legacy'"),))

        # ── Sprint 4.5: coluna status em event_links ──
        ensure_columns("event_links",  (("status", "TEXT NOT NULL DEFAULT 'AUTO_CONFIRMED'"),))

        # ── Sprint 4.4: tabelas do pipeline ETL unificado ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_events (
                id                TEXT PRIMARY KEY,
                import_run_id     TEXT NOT NULL,
                source            TEXT NOT NULL,
                event_type        TEXT NOT NULL,
                source_line_no    INTEGER,
                raw_content       TEXT,
                event_date        DATE,
                reference_month   DATE,
                amount_cents      INTEGER,
                currency          TEXT NOT NULL DEFAULT 'BRL',
                semantic_id       TEXT NOT NULL,
                cross_fingerprint TEXT,
                external_id       TEXT,
                metadata          TEXT,
                pipeline_status   TEXT NOT NULL DEFAULT 'RAW',
                match_status      TEXT NOT NULL DEFAULT 'NEW',
                promoted_entity_id TEXT,
                promoted_table    TEXT,
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_links (
                id              TEXT PRIMARY KEY,
                event_id_a      TEXT NOT NULL,
                event_id_b      TEXT NOT NULL,
                link_type       TEXT NOT NULL,
                confidence      REAL NOT NULL DEFAULT 1.0,
                match_method    TEXT NOT NULL DEFAULT 'EXACT',
                status          TEXT NOT NULL DEFAULT 'AUTO_CONFIRMED',
                confirmed_by    TEXT,
                confirmed_at    TIMESTAMP,
                notes           TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id_a) REFERENCES raw_events(id) ON DELETE CASCADE,
                FOREIGN KEY(event_id_b) REFERENCES raw_events(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reconciliation_hints (
                id          TEXT PRIMARY KEY,
                pattern_a   TEXT NOT NULL,
                source_a    TEXT NOT NULL,
                pattern_b   TEXT NOT NULL,
                source_b    TEXT NOT NULL,
                link_type   TEXT NOT NULL,
                confidence  REAL NOT NULL DEFAULT 0.8,
                active      INTEGER NOT NULL DEFAULT 1,
                confirmed_by TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_events_run ON raw_events(import_run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_events_semantic ON raw_events(semantic_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_events_cross_fp ON raw_events(cross_fingerprint)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_events_type_status ON raw_events(event_type, pipeline_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_events_source ON raw_events(source)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_events_semantic_source ON raw_events(semantic_id, source)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_event_links_a ON event_links(event_id_a)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_event_links_b ON event_links(event_id_b)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reconciliation_hints_active ON reconciliation_hints(active, source_a, source_b)")

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

    def create_import_run(
        self,
        source_type: str,
        file_name: str,
        checksum: str,
        status: str = "PENDING",
        created_by: str | None = None
    ) -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()

            run_id = uuid.uuid4().hex
            cursor.execute(
                """
                INSERT INTO import_runs (id, source_type, file_name, checksum, status, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, source_type, file_name, checksum, status, created_by),
            )
            conn.commit()
            return run_id

    def create_import_artifact(
        self,
        import_run_id: str,
        artifact_type: str,
        storage_path: str,
        sha256: str,
        size_bytes: int,
        mime_type: str | None = None
    ) -> str:
        artifact_id = uuid.uuid4().hex
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO import_artifacts (id, import_run_id, artifact_type, storage_path, sha256, size_bytes, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (artifact_id, import_run_id, artifact_type, storage_path, sha256, size_bytes, mime_type),
            )
            conn.commit()
        return artifact_id

    def update_import_run_status(self, run_id: str, status: str):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE import_runs SET status = ? WHERE id = ?",
                (status, run_id),
            )
            conn.commit()

    def update_import_run_metrics(
        self,
        run_id: str,
        status: str,
        rows_read: int,
        rows_inserted: int,
        rows_failed: int,
        error_log: str | None = None,
        preview_summary: str | None = None
    ):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE import_runs 
                SET status = ?, finished_at = CURRENT_TIMESTAMP, rows_read = ?, rows_inserted = ?, rows_failed = ?, error_log = ?, preview_summary = ?
                WHERE id = ?
                """,
                (status, rows_read, rows_inserted, rows_failed, error_log, preview_summary, run_id),
            )
            conn.commit()

    def insert_staging_items(self, run_id: str, items: list) -> list[dict]:
        if not items:
            return []

        inserted_items: list[dict] = []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # ── 1. Bulk-check duplicatas: 1 query para todos os source_line_no já presentes ──
            existing_rows = cursor.execute(
                "SELECT source_line_no FROM staging_imports WHERE import_run_id = ?",
                (run_id,),
            ).fetchall()
            existing_line_nos: set[int] = {row["source_line_no"] for row in existing_rows}

            # ── 2. Separar duplicatas de novos registros ──
            rows_to_insert: list[tuple] = []

            for item in items:
                source_line_no = item.get("source_line_no")
                date_value = str(item.get("date", "")).strip()
                description = str(item.get("description", "")).strip()
                account = str(item.get("account", "")).strip()
                category_inferred = str(item.get("category_inferred", "")).strip()
                status = str(item.get("status", "PENDING")).strip().upper() or "PENDING"

                amount_decimal = _to_decimal(item.get("amount", 0))
                amount_cents = _decimal_to_cents(amount_decimal)

                if source_line_no is None or not date_value or not description:
                    status = "ERROR"

                if source_line_no in existing_line_nos:
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

                # Marca como visto para evitar duplicatas dentro do próprio batch
                existing_line_nos.add(source_line_no)

                rows_to_insert.append((
                    run_id,
                    source_line_no,
                    date_value,
                    description,
                    None,         # amount (legacy REAL — não usado, cents é o canônico)
                    amount_cents,
                    account,
                    category_inferred,
                    status,
                ))
                inserted_items.append(
                    {
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

            # ── 3. Bulk insert com executemany ──
            if rows_to_insert:
                cursor.executemany(
                    """
                    INSERT INTO staging_imports (
                        import_run_id, source_line_no, date, description, amount, amount_cents, account, category_inferred, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows_to_insert,
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
                        str(amount_decimal),
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

    def insert_wealth_staging_items(self, run_id: str, file_type: str, items: list[dict]):
        if not items:
            return
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if file_type == "POSICOES":
                cursor.executemany(
                    """
                    INSERT INTO staging_positions (
                        import_run_id, source_line_no, validation_status, validation_message,
                        ticker, data_snapshot, source, quantidade, preco_medio, total_investido,
                        preco_atual, total_atual, ganho
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run_id, item.get("source_line_no"), item.get("validation_status", "PENDING"), item.get("validation_message"),
                            item.get("ticker"), item.get("data_snapshot"), item.get("source", "MYPROFIT"),
                            item.get("quantidade"), item.get("preco_medio"), item.get("total_investido"),
                            item.get("preco_atual"), item.get("total_atual"), item.get("ganho")
                        )
                        for item in items
                    ]
                )
            elif file_type == "PROVENTOS":
                cursor.executemany(
                    """
                    INSERT INTO staging_dividends (
                        import_run_id, source_line_no, validation_status, validation_message,
                        id_economico, source, ticker, tipo_evento, data_pagamento, valor_liquido, valor_liquido_cents
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run_id, item.get("source_line_no"), item.get("validation_status", "PENDING"), item.get("validation_message"),
                            item.get("id_economico", f"MP-{item.get('ticker')}-{item.get('data_pagamento')}"), item.get("source", "MYPROFIT"), item.get("ticker"), item.get("tipo_evento"),
                            item.get("data_pagamento"), item.get("valor_liquido"), item.get("valor_liquido_cents")
                        )
                        for item in items
                    ]
                )
            elif file_type == "EVOLUCAO":
                cursor.executemany(
                    """
                    INSERT INTO staging_portfolio_evolution (
                        import_run_id, source_line_no, validation_status, validation_message,
                        reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,
                        patrimonio_cents, compras_cents, vendas_cents, proventos_cents,
                        ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,
                        ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,
                        sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run_id, item.get("source_line_no"), item.get("validation_status", "PENDING"), item.get("validation_message"),
                            item.get("reference_month"), item.get("rentabilidade_mensal_pct"), item.get("rentabilidade_acumulada_pct"),
                            item.get("patrimonio_cents"), item.get("compras_cents"), item.get("vendas_cents"), item.get("proventos_cents"),
                            item.get("ibov_mensal_pct"), item.get("ibov_acumulado_pct"), item.get("cdi_mensal_pct"), item.get("cdi_acumulado_pct"),
                            item.get("ipca_mensal_pct"), item.get("ipca_acumulado_pct"), item.get("ifix_mensal_pct"), item.get("ifix_acumulado_pct"),
                            item.get("sp500_mensal_pct"), item.get("sp500_acumulado_pct"), item.get("idiv_mensal_pct"), item.get("idiv_acumulado_pct")
                        )
                        for item in items
                    ]
                )
            
            conn.commit()

    def mark_staging_conflicts(self, run_id: str, file_type: str) -> dict:
        """Classifica os itens do staging com a política: UNCHANGED | UPDATE | VALID."""
        counts = {"unchanged": 0, "update": 0, "conflicts": 0}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if file_type == "POSICOES":
                # Chave econômica: (ticker, data_snapshot)
                # UNCHANGED: chave + todos os campos de valor idênticos
                cursor.execute(
                    """
                    UPDATE staging_positions
                    SET validation_status = 'UNCHANGED', validation_message = 'Posição idêntica já existe (sem alteração)'
                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR')
                    AND EXISTS (
                        SELECT 1 FROM positions p 
                        WHERE p.ticker = staging_positions.ticker 
                        AND p.data_snapshot = staging_positions.data_snapshot
                        AND ROUND(CAST(p.quantidade AS REAL), 4) = ROUND(CAST(staging_positions.quantidade AS REAL), 4)
                        AND ROUND(CAST(p.preco_medio AS REAL), 4) = ROUND(CAST(staging_positions.preco_medio AS REAL), 4)
                        AND ROUND(CAST(p.total_atual AS REAL), 2) = ROUND(CAST(staging_positions.total_atual AS REAL), 2)
                    )
                    """,
                    (run_id,)
                )
                counts["unchanged"] = cursor.rowcount
                
                # UPDATE: chave existe mas dados mudaram
                cursor.execute(
                    """
                    UPDATE staging_positions
                    SET validation_status = 'UPDATE', validation_message = 'Posição atualizada (dados alterados)'
                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR', 'UNCHANGED')
                    AND EXISTS (
                        SELECT 1 FROM positions p 
                        WHERE p.ticker = staging_positions.ticker 
                        AND p.data_snapshot = staging_positions.data_snapshot
                    )
                    """,
                    (run_id,)
                )
                counts["update"] = cursor.rowcount

                # VALID: tudo que sobrou como PENDING
                cursor.execute(
                    """
                    UPDATE staging_positions
                    SET validation_status = 'VALID', validation_message = 'Novo registro a ser importado'
                    WHERE import_run_id = ? AND validation_status = 'PENDING'
                    """,
                    (run_id,)
                )

            elif file_type == "PROVENTOS":
                # Chave econômica: (ticker, data_pagamento)
                # UNCHANGED: chave + valor idêntico
                cursor.execute(
                    """
                    UPDATE staging_dividends
                    SET validation_status = 'UNCHANGED', validation_message = 'Dividendo idêntico já existe (sem alteração)'
                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR')
                    AND EXISTS (
                        SELECT 1 FROM dividends d 
                        WHERE d.ticker = staging_dividends.ticker 
                        AND d.data_pagamento = staging_dividends.data_pagamento
                        AND d.valor_liquido_cents = staging_dividends.valor_liquido_cents
                    )
                    """,
                    (run_id,)
                )
                counts["unchanged"] = cursor.rowcount

                # UPDATE: mesmo ticker+data mas valor diferente (correção de provento)
                cursor.execute(
                    """
                    UPDATE staging_dividends
                    SET validation_status = 'UPDATE', validation_message = 'Provento corrigido (valor alterado)'
                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR', 'UNCHANGED')
                    AND EXISTS (
                        SELECT 1 FROM dividends d 
                        WHERE d.ticker = staging_dividends.ticker 
                        AND d.data_pagamento = staging_dividends.data_pagamento
                    )
                    """,
                    (run_id,)
                )
                counts["update"] = cursor.rowcount

                # VALID: tudo que sobrou como PENDING
                cursor.execute(
                    """
                    UPDATE staging_dividends
                    SET validation_status = 'VALID', validation_message = 'Novo provento a ser importado'
                    WHERE import_run_id = ? AND validation_status = 'PENDING'
                    """,
                    (run_id,)
                )

            elif file_type == "EVOLUCAO":
                # Chave econômica: (reference_month)
                # UNCHANGED: mês + todos os campos financeiros e de benchmark idênticos
                cursor.execute(
                    """
                    UPDATE staging_portfolio_evolution
                    SET validation_status = 'UNCHANGED', validation_message = 'Mês idêntico já registrado (sem alteração)'
                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR')
                    AND EXISTS (
                        SELECT 1 FROM portfolio_evolution pe
                        WHERE pe.reference_month = staging_portfolio_evolution.reference_month
                        AND pe.patrimonio_cents = staging_portfolio_evolution.patrimonio_cents
                        AND pe.rentabilidade_mensal_pct = staging_portfolio_evolution.rentabilidade_mensal_pct
                        AND pe.cdi_mensal_pct = staging_portfolio_evolution.cdi_mensal_pct
                        AND pe.ibov_mensal_pct = staging_portfolio_evolution.ibov_mensal_pct
                        AND pe.ifix_mensal_pct = staging_portfolio_evolution.ifix_mensal_pct
                        AND pe.sp500_mensal_pct = staging_portfolio_evolution.sp500_mensal_pct
                        AND pe.idiv_mensal_pct = staging_portfolio_evolution.idiv_mensal_pct
                    )
                    """,
                    (run_id,)
                )
                counts["unchanged"] = cursor.rowcount

                # UPDATE: mês existe mas dados mudaram (rebalanceamento retroativo)
                cursor.execute(
                    """
                    UPDATE staging_portfolio_evolution
                    SET validation_status = 'UPDATE', validation_message = 'Evolução atualizada (dados alterados)'
                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR', 'UNCHANGED')
                    AND EXISTS (
                        SELECT 1 FROM portfolio_evolution pe
                        WHERE pe.reference_month = staging_portfolio_evolution.reference_month
                    )
                    """,
                    (run_id,)
                )
                counts["update"] = cursor.rowcount
                
                # VALID: tudo que sobrou como PENDING
                cursor.execute(
                    """
                    UPDATE staging_portfolio_evolution
                    SET validation_status = 'VALID', validation_message = 'Novo mês a ser importado'
                    WHERE import_run_id = ? AND validation_status = 'PENDING'
                    """,
                    (run_id,)
                )
                
            conn.commit()
        return counts

    def rollback_import_run(self, run_id: str, user: str = "api_user", reason: str = "Revertido pelo usuário") -> bool:
        """Deleta os itens e marca a run como ROLLED_BACK, registrando log."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT status FROM import_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            if not row or row["status"] in ("CANCELLED", "FAILED", "ROLLED_BACK"):
                return False
                
            # Remover das tabelas oficiais (caso a importação já tenha sido efetivada)
            cursor.execute("DELETE FROM transactions WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM positions WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM dividends WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM portfolio_evolution WHERE import_run_id = ?", (run_id,))

            # Remover do staging
            cursor.execute("DELETE FROM staging_imports WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM staging_positions WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM staging_dividends WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM staging_portfolio_evolution WHERE import_run_id = ?", (run_id,))
            
            cursor.execute(
                """
                UPDATE import_runs 
                SET status = 'ROLLED_BACK',
                    rollback_timestamp = CURRENT_TIMESTAMP,
                    rollback_user = ?,
                    rollback_reason = ?,
                    rows_inserted = 0,
                    rows_updated = 0
                WHERE id = ?
                """, 
                (user, reason, run_id)
            )
            conn.commit()
            return True

    def lock_import_run_for_confirmation(self, run_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE import_runs SET status = 'PROCESSING_CONFIRMATION' WHERE id = ? AND status = 'AWAITING_CONFIRMATION'",
                (run_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def promote_all_wealth_staging(self, run_id: str) -> dict:
        imported = 0
        updated = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # ─── POSICOES ───
            # INSERT novos (VALID/WARNING)
            cursor.execute(
                """
                INSERT OR IGNORE INTO positions (
                    ticker, data_snapshot, source, quantidade, preco_medio, total_investido,
                    preco_atual, total_atual, ganho, import_run_id, source_line_no
                )
                SELECT ticker, data_snapshot, source, quantidade, preco_medio, total_investido,
                       preco_atual, total_atual, ganho, import_run_id, source_line_no
                FROM staging_positions
                WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')
                """,
                (run_id,)
            )
            cursor.execute("UPDATE staging_positions SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')", (run_id,))

            # UPSERT atualizações (UPDATE)
            cursor.execute(
                """
                INSERT OR REPLACE INTO positions (
                    ticker, data_snapshot, source, quantidade, preco_medio, total_investido,
                    preco_atual, total_atual, ganho, import_run_id, source_line_no
                )
                SELECT ticker, data_snapshot, source, quantidade, preco_medio, total_investido,
                       preco_atual, total_atual, ganho, import_run_id, source_line_no
                FROM staging_positions
                WHERE import_run_id = ? AND validation_status = 'UPDATE'
                """,
                (run_id,)
            )
            cursor.execute("UPDATE staging_positions SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status = 'UPDATE'", (run_id,))

            # ─── PROVENTOS ───
            cursor.execute(
                """
                INSERT OR IGNORE INTO dividends (
                    id_economico, source, ticker, tipo_evento, data_pagamento, valor_liquido, valor_liquido_cents, import_run_id, source_line_no
                )
                SELECT id_economico, source, ticker, tipo_evento, data_pagamento, valor_liquido, valor_liquido_cents, import_run_id, source_line_no
                FROM staging_dividends
                WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')
                """,
                (run_id,)
            )
            cursor.execute("UPDATE staging_dividends SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')", (run_id,))

            # UPSERT proventos corrigidos
            cursor.execute(
                """
                INSERT OR REPLACE INTO dividends (
                    id_economico, source, ticker, tipo_evento, data_pagamento, valor_liquido, valor_liquido_cents, import_run_id, source_line_no
                )
                SELECT id_economico, source, ticker, tipo_evento, data_pagamento, valor_liquido, valor_liquido_cents, import_run_id, source_line_no
                FROM staging_dividends
                WHERE import_run_id = ? AND validation_status = 'UPDATE'
                """,
                (run_id,)
            )
            cursor.execute("UPDATE staging_dividends SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status = 'UPDATE'", (run_id,))

            # ─── EVOLUCAO ───
            cursor.execute(
                """
                INSERT OR IGNORE INTO portfolio_evolution (
                    reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,
                    patrimonio_cents, compras_cents, vendas_cents, proventos_cents,
                    ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,
                    ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,
                    sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,
                    import_run_id, source_line_no
                )
                SELECT reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,
                       patrimonio_cents, compras_cents, vendas_cents, proventos_cents,
                       ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,
                       ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,
                       sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,
                       import_run_id, source_line_no
                FROM staging_portfolio_evolution
                WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')
                """,
                (run_id,)
            )
            cursor.execute("UPDATE staging_portfolio_evolution SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')", (run_id,))

            # UPSERT evolução atualizada
            cursor.execute(
                """
                INSERT OR REPLACE INTO portfolio_evolution (
                    reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,
                    patrimonio_cents, compras_cents, vendas_cents, proventos_cents,
                    ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,
                    ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,
                    sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,
                    import_run_id, source_line_no
                )
                SELECT reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,
                       patrimonio_cents, compras_cents, vendas_cents, proventos_cents,
                       ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,
                       ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,
                       sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,
                       import_run_id, source_line_no
                FROM staging_portfolio_evolution
                WHERE import_run_id = ? AND validation_status = 'UPDATE'
                """,
                (run_id,)
            )
            cursor.execute("UPDATE staging_portfolio_evolution SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status = 'UPDATE'", (run_id,))

            # ─── Contagens finais ───
            cursor.execute("SELECT COUNT(*) FROM staging_positions WHERE import_run_id = ? AND validation_status = 'IMPORTED'", (run_id,))
            imported += cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM staging_dividends WHERE import_run_id = ? AND validation_status = 'IMPORTED'", (run_id,))
            imported += cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM staging_portfolio_evolution WHERE import_run_id = ? AND validation_status = 'IMPORTED'", (run_id,))
            imported += cursor.fetchone()[0]

            cursor.execute(
                "UPDATE import_runs SET status = 'CONFIRMED', finished_at = CURRENT_TIMESTAMP, rows_inserted = ? WHERE id = ?",
                (imported, run_id)
            )
            conn.commit()
            
        return {"inserted": imported}

    def upsert_transactions(self, transactions: list, categorizer) -> tuple[int, int]:
        if not transactions:
            return 0, 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # ── 1. Pré-computa todas as linhas (categorização é CPU-bound, não I/O) ──
            rows: list[tuple] = []
            ids: list[str] = []
            for transaction in transactions:
                cat = categorizer.classify(transaction)
                source_value = _source_value(transaction.get("source"))
                origin_value = transaction.get("origin") or source_value
                domain_value = transaction.get("domain") or "FINANCE"
                valor_cents = _decimal_to_cents(transaction["valor"])
                ids.append(transaction["id_economico"])
                rows.append((
                    transaction["id_economico"],
                    source_value,
                    origin_value,
                    domain_value,
                    transaction.get("source_line_no"),
                    transaction["data"].isoformat(),
                    transaction["descricao_original"],
                    transaction["descricao_normalizada"],
                    valor_cents,
                    valor_cents,
                    transaction["identificador_externo"],
                    cat["macro"],
                    cat["sub"],
                    cat["sub"],
                    cat["natureza"].value,
                    cat["perfil"].value,
                ))

            # ── 2. 1 query para saber quantos já existem (insert vs update count) ──
            placeholders = ",".join("?" * len(ids))
            existing_ids: set[str] = {
                row[0]
                for row in cursor.execute(
                    f"SELECT id_economico FROM transactions WHERE id_economico IN ({placeholders})",
                    ids,
                ).fetchall()
            }
            inserted = len(ids) - len(existing_ids)
            updated = len(existing_ids)

            # ── 3. Bulk upsert ──
            cursor.executemany(
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
                    macro_categoria = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.macro_categoria ELSE excluded.macro_categoria END,
                    sub_categoria   = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.sub_categoria   ELSE excluded.sub_categoria   END,
                    subnatureza     = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.subnatureza     ELSE excluded.subnatureza     END,
                    natureza        = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.natureza        ELSE excluded.natureza        END,
                    perfil          = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.perfil          ELSE excluded.perfil          END,
                    atualizado_em = CURRENT_TIMESTAMP
                """,
                rows,
            )
            conn.commit()

        return inserted, updated

    def upsert_positions(self, positions: list) -> tuple[int, int]:
        if not positions:
            return 0, 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # ── 1. Pré-computa todas as linhas ──
            rows: list[tuple] = []
            keys: list[tuple] = []
            for position in positions:
                snapshot_iso = position["data_snapshot"].isoformat()
                keys.append((position["ticker"], snapshot_iso))
                rows.append((
                    position["ticker"],
                    snapshot_iso,
                    _source_value(position["source"]),
                    str(position["quantidade"]),
                    str(position["preco_medio"]),
                    str(position["total_investido"]),
                    str(position["preco_atual"]),
                    str(position["total_atual"]),
                    str(position["ganho"]),
                    position.get("import_run_id"),
                    position.get("source_line_no"),
                ))

            # ── 2. 1 query para contar existentes ──
            if keys:
                existing_count = cursor.execute(
                    f"SELECT COUNT(*) FROM positions WHERE (ticker, data_snapshot) IN ({','.join('(?,?)' for _ in keys)})",
                    [val for k in keys for val in k],
                ).fetchone()[0]
            else:
                existing_count = 0
            inserted = len(rows) - existing_count
            updated = existing_count

            # ── 3. Bulk upsert ──
            cursor.executemany(
                """
                INSERT INTO positions (
                    ticker, data_snapshot, source, quantidade, preco_medio,
                    total_investido, preco_atual, total_atual, ganho,
                    import_run_id, source_line_no
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, data_snapshot) DO UPDATE SET
                    source = excluded.source,
                    quantidade = excluded.quantidade,
                    preco_medio = excluded.preco_medio,
                    total_investido = excluded.total_investido,
                    preco_atual = excluded.preco_atual,
                    total_atual = excluded.total_atual,
                    ganho = excluded.ganho,
                    import_run_id = excluded.import_run_id,
                    source_line_no = excluded.source_line_no,
                    atualizado_em = CURRENT_TIMESTAMP
                """,
                rows,
            )
            conn.commit()

        return inserted, updated

    def upsert_dividends(self, dividends: list) -> tuple[int, int]:
        if not dividends:
            return 0, 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # ── 1. Pré-computa todas as linhas ──
            rows: list[tuple] = []
            ids: list[str] = []
            for dividend in dividends:
                ids.append(dividend["id_economico"])
                vliq_cents = _decimal_to_cents(dividend["valor_liquido"])
                rows.append((
                    dividend["id_economico"],
                    _source_value(dividend["source"]),
                    dividend["ticker"],
                    dividend["tipo_evento"],
                    dividend["data_pagamento"].isoformat(),
                    vliq_cents,
                    vliq_cents,
                    dividend.get("import_run_id"),
                    dividend.get("source_line_no"),
                ))

            # ── 2. 1 query para contar existentes ──
            placeholders = ",".join("?" * len(ids))
            existing_ids: set[str] = {
                row[0]
                for row in cursor.execute(
                    f"SELECT id_economico FROM dividends WHERE id_economico IN ({placeholders})",
                    ids,
                ).fetchall()
            }
            inserted = len(ids) - len(existing_ids)
            updated = len(existing_ids)

            # ── 3. Bulk upsert ──
            cursor.executemany(
                """
                INSERT INTO dividends (
                    id_economico, source, ticker, tipo_evento,
                    data_pagamento, valor_liquido, valor_liquido_cents,
                    import_run_id, source_line_no
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_economico) DO UPDATE SET
                    source = excluded.source,
                    ticker = excluded.ticker,
                    tipo_evento = excluded.tipo_evento,
                    data_pagamento = excluded.data_pagamento,
                    valor_liquido = excluded.valor_liquido,
                    valor_liquido_cents = excluded.valor_liquido_cents,
                    import_run_id = excluded.import_run_id,
                    source_line_no = excluded.source_line_no,
                    atualizado_em = CURRENT_TIMESTAMP
                """,
                rows,
            )
            conn.commit()

        return inserted, updated


    def upsert_portfolio_evolution(self, evos: list) -> tuple[int, int]:
        if not evos:
            return 0, 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # ── 1. Pré-computa todas as linhas ──
            rows: list[tuple] = []
            months: list[str] = []
            for evo in evos:
                month_iso = evo["reference_month"].isoformat()
                months.append(month_iso)
                rows.append((
                    month_iso,
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
                    evo.get("import_run_id"),
                    evo.get("source_line_no"),
                ))

            # ── 2. 1 query para contar existentes ──
            placeholders = ",".join("?" * len(months))
            existing_count = cursor.execute(
                f"SELECT COUNT(*) FROM portfolio_evolution WHERE reference_month IN ({placeholders})",
                months,
            ).fetchone()[0]
            inserted = len(rows) - existing_count
            updated = existing_count

            # ── 3. Bulk upsert ──
            cursor.executemany(
                """
                INSERT INTO portfolio_evolution (
                    reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,
                    patrimonio_cents, compras_cents, vendas_cents, op_finalizadas_cents, proventos_cents,
                    ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,
                    ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,
                    sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,
                    import_run_id, source_line_no
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    idiv_acumulado_pct = excluded.idiv_acumulado_pct,
                    import_run_id = excluded.import_run_id,
                    source_line_no = excluded.source_line_no
                """,
                rows,
            )
            conn.commit()

        return inserted, updated

    # ─────────────────────────────────────────────────────────────────────────────
    # Sprint 4.4 — ETL Inteligente
    # ─────────────────────────────────────────────────────────────────────────────

    def insert_raw_events(self, events: list[dict]):
        """Insere ou atualiza RawFinancialEvents em batch."""
        if not events:
            return
        
        with self._get_connection() as conn:
            import json
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO raw_events (
                    id, import_run_id, source, event_type, source_line_no, raw_content,
                    event_date, reference_month, amount_cents, currency,
                    semantic_id, cross_fingerprint, external_id, metadata,
                    pipeline_status, match_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(semantic_id, source) DO UPDATE SET
                    pipeline_status = excluded.pipeline_status,
                    match_status = excluded.match_status,
                    cross_fingerprint = excluded.cross_fingerprint,
                    metadata = excluded.metadata
                """,
                [
                    (
                        e["id"], e["import_run_id"], e["source"], e["event_type"],
                        e.get("source_line_no"), e.get("raw_content"),
                        e.get("event_date"), e.get("reference_month"),
                        e.get("amount_cents"), e.get("currency", "BRL"),
                        e["semantic_id"], e.get("cross_fingerprint"),
                        e.get("external_id"), json.dumps(e.get("metadata", {})),
                        e["pipeline_status"], e["match_status"],
                    )
                    for e in events
                ]
            )
            conn.commit()

    def create_event_links(self, links: list[tuple]):
        """
        Insere event links.
        links = [(id, event_id_a, event_id_b, link_type, confidence, match_method, status, notes), ...]
        """
        if not links:
            return
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO event_links (
                    id, event_id_a, event_id_b, link_type, confidence, match_method, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO NOTHING
                """,
                links
            )
            conn.commit()

    def get_active_hints(self) -> list[dict]:
        """Retorna todas as dicas de reconciliação ativas."""
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            return cursor.execute("SELECT * FROM reconciliation_hints WHERE active = 1").fetchall()

    def promote_raw_events(self, run_id: str) -> dict:
        """
        Promove eventos do import_run_id de CLASSIFIED para as tabelas finais.
        Retorna dicionário com contagens.
        """
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            # Busca eventos classificados do run
            raw_events = cursor.execute(
                """
                SELECT * FROM raw_events 
                WHERE import_run_id = ? 
                  AND pipeline_status = 'CLASSIFIED' 
                  AND match_status != 'DUPLICATE'
                  AND id NOT IN (SELECT event_id_a FROM event_links WHERE status = 'SUGGESTED')
                  AND id NOT IN (SELECT event_id_b FROM event_links WHERE status = 'SUGGESTED')
                """,
                (run_id,)
            ).fetchall()
            
            if not raw_events:
                return {"inserted": 0, "errors": 0}
                
            inserted_tx = 0
            inserted_pos = 0
            inserted_div = 0
            inserted_evo = 0
            
            import json
            for event in raw_events:
                meta = json.loads(event.get("metadata") or "{}")
                
                try:
                    if event["event_type"] in ("TRANSACTION", "INVOICE"):
                        amount_dec = _cents_to_decimal(event["amount_cents"]) if event["amount_cents"] is not None else 0
                        
                        id_economico = meta.get("id_economico")
                        if not id_economico:
                            id_economico = generate_economic_id(
                                "MANUAL", event["source"], event["source_line_no"],
                                event["event_date"], meta.get("descricao_normalizada", ""),
                                str(amount_dec), event["source"]
                            )
                            
                        cursor.execute(
                            """
                            INSERT INTO transactions (
                                id_economico, source, origin, import_run_id, source_line_no, data,
                                descricao_original, descricao_normalizada, valor, valor_cents, identificador_externo,
                                macro_categoria, sub_categoria, subnatureza, natureza, perfil, classificacao_fonte, raw_event_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(id_economico) DO UPDATE SET
                                raw_event_id = excluded.raw_event_id,
                                import_run_id = excluded.import_run_id,
                                macro_categoria = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.macro_categoria ELSE excluded.macro_categoria END,
                                sub_categoria   = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.sub_categoria   ELSE excluded.sub_categoria   END,
                                subnatureza     = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.subnatureza     ELSE excluded.subnatureza     END,
                                natureza        = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.natureza        ELSE excluded.natureza        END,
                                perfil          = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.perfil          ELSE excluded.perfil          END,
                                atualizado_em = CURRENT_TIMESTAMP
                            """,
                            (
                                id_economico, event["source"], meta.get("origin", "ETL"), run_id, event["source_line_no"], event["event_date"],
                                meta.get("descricao_original", ""), meta.get("descricao_normalizada", ""),
                                str(amount_dec), event["amount_cents"], event["external_id"],
                                meta.get("macro_categoria", "OUTROS"), meta.get("sub_categoria", "INDEFINIDO"),
                                meta.get("sub_categoria", "INDEFINIDO"), meta.get("natureza", "INDEFINIDO"),
                                "INDEFINIDO", meta.get("classificacao_fonte", "ETL"), event["id"]
                            )
                        )
                        inserted_tx += 1
                        
                    elif event["event_type"] == "DIVIDEND":
                        amount_dec = _cents_to_decimal(event["amount_cents"]) if event["amount_cents"] is not None else 0
                        cursor.execute(
                            """
                            INSERT INTO dividends (
                                id_economico, source, ticker, tipo_evento, data_pagamento, 
                                valor_liquido, valor_liquido_cents, import_run_id, source_line_no, raw_event_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(ticker, data_pagamento, valor_liquido_cents) DO UPDATE SET
                                raw_event_id = excluded.raw_event_id,
                                import_run_id = excluded.import_run_id,
                                atualizado_em = CURRENT_TIMESTAMP
                            """,
                            (
                                event["external_id"], event["source"], meta.get("ticker"), meta.get("tipo_evento"), event["event_date"],
                                str(amount_dec), event["amount_cents"], run_id, event["source_line_no"], event["id"]
                            )
                        )
                        inserted_div += 1
                        
                    elif event["event_type"] == "POSITION":
                        cursor.execute(
                            """
                            INSERT INTO positions (
                                ticker, data_snapshot, source, quantidade, preco_medio, total_investido,
                                preco_atual, total_atual, ganho, import_run_id, source_line_no, raw_event_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(ticker, data_snapshot) DO UPDATE SET
                                raw_event_id = excluded.raw_event_id,
                                import_run_id = excluded.import_run_id,
                                atualizado_em = CURRENT_TIMESTAMP
                            """,
                            (
                                meta.get("ticker"), meta.get("data_snapshot"), event["source"], meta.get("quantidade"), meta.get("preco_medio"), meta.get("total_investido"),
                                meta.get("preco_atual"), meta.get("total_atual"), meta.get("ganho"), run_id, event["source_line_no"], event["id"]
                            )
                        )
                        inserted_pos += 1
                        
                    elif event["event_type"] == "PORTFOLIO_EVO":
                        cursor.execute(
                            """
                            INSERT INTO portfolio_evolution (
                                reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,
                                patrimonio_cents, compras_cents, vendas_cents, op_finalizadas_cents, proventos_cents,
                                ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,
                                ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,
                                sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,
                                import_run_id, source_line_no
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(reference_month) DO UPDATE SET
                                import_run_id = excluded.import_run_id,
                                patrimonio_cents = excluded.patrimonio_cents,
                                compras_cents = excluded.compras_cents,
                                vendas_cents = excluded.vendas_cents,
                                op_finalizadas_cents = excluded.op_finalizadas_cents,
                                proventos_cents = excluded.proventos_cents
                            """,
                            (
                                meta.get("reference_month"), meta.get("rentabilidade_mensal_pct"), meta.get("rentabilidade_acumulada_pct"),
                                meta.get("patrimonio_cents"), meta.get("compras_cents"), meta.get("vendas_cents"), meta.get("op_finalizadas_cents"), meta.get("proventos_cents"),
                                meta.get("ibov_mensal_pct"), meta.get("ibov_acumulado_pct"), meta.get("cdi_mensal_pct"), meta.get("cdi_acumulado_pct"),
                                meta.get("ipca_mensal_pct"), meta.get("ipca_acumulado_pct"), meta.get("ifix_mensal_pct"), meta.get("ifix_acumulado_pct"),
                                meta.get("sp500_mensal_pct"), meta.get("sp500_acumulado_pct"), meta.get("idiv_mensal_pct"), meta.get("idiv_acumulado_pct"),
                                run_id, event["source_line_no"]
                            )
                        )
                        inserted_evo += 1
                        
                    cursor.execute("UPDATE raw_events SET pipeline_status = 'PROMOTED' WHERE id = ?", (event["id"],))
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Erro ao promover evento {event['id']}: {e}")
            
            conn.commit()
            return {
                "inserted": inserted_tx + inserted_pos + inserted_div + inserted_evo,
                "tx": inserted_tx,
                "pos": inserted_pos,
                "div": inserted_div,
                "evo": inserted_evo,
                "errors": 0
            }

    def get_user_by_username(self, username: str) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            user = cursor.execute(
                "SELECT id, username, email, password_hash, role, active FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            if user:
                return dict(user)
            return None

    def create_user(self, username: str, email: str, password_hash: str, role: str = 'VIEWER') -> str:
        import uuid
        user_id = uuid.uuid4().hex
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, username, email, password_hash, role, active)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (user_id, username, email, password_hash, role)
            )
            conn.commit()
            return user_id

    def create_audit_log(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        field_changes: str = None,
        changed_by: str = None,
        cursor = None
    ) -> str:
        import uuid
        log_id = uuid.uuid4().hex
        
        def _execute(cur):
            cur.execute(
                """
                INSERT INTO audit_log (id, entity_type, entity_id, action, field_changes, changed_by)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (log_id, entity_type, entity_id, action, field_changes, changed_by)
            )
            
        if cursor:
            _execute(cursor)
            return log_id
            
        with self._get_connection() as conn:
            cur = conn.cursor()
            _execute(cur)
            conn.commit()
            return log_id

    def vacuum_database(self) -> dict:
        import os
        size_before = os.path.getsize(self.db_path)
        with self._get_connection() as conn:
            conn.isolation_level = None
            conn.execute("VACUUM")
            conn.isolation_level = ""
        size_after = os.path.getsize(self.db_path)
        return {"size_before_bytes": size_before, "size_after_bytes": size_after}

    def analyze_database(self) -> bool:
        with self._get_connection() as conn:
            conn.isolation_level = None
            conn.execute("ANALYZE")
            conn.isolation_level = ""
            return True

    def _dict_factory(self, cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def update_transaction(self, id_economico: str, updates: dict, changed_by: str = None) -> bool:
        import json
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            
            # 1. Fetch current
            cursor.execute("SELECT * FROM transactions WHERE id_economico = ?", (id_economico,))
            old_record = cursor.fetchone()
            if not old_record:
                return False
                
            # 2. Prepare changes
            field_changes = {}
            set_clauses = []
            params = []
            for k, v in updates.items():
                if v is not None and k in old_record and old_record[k] != v:
                    field_changes[k] = {"old": old_record[k], "new": v}
                    set_clauses.append(f"{k} = ?")
                    params.append(v)
                    
            if not field_changes:
                return True # Nothing to update
                
            # 3. Apply changes
            params.append(id_economico)
            cursor.execute(f"UPDATE transactions SET {', '.join(set_clauses)} WHERE id_economico = ?", params)
            
            # 4. Audit
            self.create_audit_log("TRANSACTION", id_economico, "UPDATE", json.dumps(field_changes), changed_by, cursor=cursor)
            conn.commit()
            return True

    def update_position(self, ticker: str, data_snapshot: str, updates: dict, changed_by: str = None) -> bool:
        import json
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM positions WHERE ticker = ? AND data_snapshot = ?", (ticker, data_snapshot))
            old_record = cursor.fetchone()
            if not old_record:
                return False
                
            field_changes = {}
            set_clauses = []
            params = []
            for k, v in updates.items():
                if v is not None and k in old_record and old_record[k] != v:
                    field_changes[k] = {"old": old_record[k], "new": v}
                    set_clauses.append(f"{k} = ?")
                    params.append(v)
                    
            if not field_changes:
                return True
                
            params.extend([ticker, data_snapshot])
            cursor.execute(f"UPDATE positions SET {', '.join(set_clauses)} WHERE ticker = ? AND data_snapshot = ?", params)
            
            entity_id = f"{ticker}|{data_snapshot}"
            self.create_audit_log("POSITION", entity_id, "UPDATE", json.dumps(field_changes), changed_by, cursor=cursor)
            conn.commit()
            return True

    def update_dividend(self, id_economico: str, updates: dict, changed_by: str = None) -> bool:
        import json
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM dividends WHERE id_economico = ?", (id_economico,))
            old_record = cursor.fetchone()
            if not old_record:
                return False
                
            field_changes = {}
            set_clauses = []
            params = []
            for k, v in updates.items():
                if v is not None and k in old_record and old_record[k] != v:
                    field_changes[k] = {"old": old_record[k], "new": v}
                    set_clauses.append(f"{k} = ?")
                    params.append(v)
                    
            if not field_changes:
                return True
                
            params.append(id_economico)
            cursor.execute(f"UPDATE dividends SET {', '.join(set_clauses)} WHERE id_economico = ?", params)
            
            self.create_audit_log("DIVIDEND", id_economico, "UPDATE", json.dumps(field_changes), changed_by, cursor=cursor)
            conn.commit()
            return True

    def merge_categories(self, source_category: str, target_category: str, changed_by: str = None) -> int:
        import json
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE macro_categoria = ? OR sub_categoria = ?", (source_category, source_category))
            count = cursor.fetchone()[0]
            
            if count == 0:
                return 0
                
            # Update macro
            cursor.execute("UPDATE transactions SET macro_categoria = ? WHERE macro_categoria = ?", (target_category, source_category))
            # Update sub
            cursor.execute("UPDATE transactions SET sub_categoria = ? WHERE sub_categoria = ?", (target_category, source_category))
            
            field_changes = {"categoria": {"old": source_category, "new": target_category}, "affected_rows": count}
            self.create_audit_log("CATEGORY", source_category, "MERGE", json.dumps(field_changes), changed_by, cursor=cursor)
            
            conn.commit()
            return count

    def get_orphans_count(self) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Transactions that do not match import_runs (orphan)
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE import_run_id IS NOT NULL AND import_run_id NOT IN (SELECT id FROM import_runs)")
            count = cursor.fetchone()[0]
            
            return {
                "orphan_count": count,
                "type": "transaction",
                "table": "transactions"
            }

    def update_event_link_status(self, link_id: str, status: str) -> None:
        with self._get_connection() as conn:
            conn.execute("UPDATE event_links SET status = ? WHERE id = ?", (status, link_id))
            conn.commit()
            
    def get_run_ids_for_link(self, link_id: str) -> list[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT a.import_run_id as a_run, b.import_run_id as b_run 
                FROM event_links el
                JOIN raw_events a ON el.event_id_a = a.id
                JOIN raw_events b ON el.event_id_b = b.id
                WHERE el.id = ?
            """
            row = cursor.execute(query, (link_id,)).fetchone()
            if row:
                runs = {row[0], row[1]}
                return [r for r in runs if r]
            return []

    # ─────────────────────────────────────────────────────────────────────────────
    # Sprint 4.7 — Memória Financeira (Rules & Learning)
    # ─────────────────────────────────────────────────────────────────────────────

    def get_active_rules(self) -> list[dict]:
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            return cursor.execute("SELECT * FROM rules WHERE status = 'ACTIVE'").fetchall()

    def upsert_rule(self, rule_type: str, pattern: str, action: str, reason: str = None) -> str:
        """
        Creates a new rule or supersedes an existing identical one.
        Returns the ID of the active rule.
        """
        import uuid
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            # Check if an active rule with same pattern exists
            existing = cursor.execute(
                "SELECT id, version, hit_count, miss_count, action FROM rules WHERE rule_type = ? AND pattern = ? AND active = 1",
                (rule_type, pattern)
            ).fetchone()
            
            new_id = str(uuid.uuid4())
            version = 1
            
            if existing:
                if existing['action'] == action:
                    return existing['id']  # Nothing changed
                
                cursor.execute("UPDATE rules SET active = 0, superseded_by = ? WHERE id = ?", (new_id, existing['id']))
                version = existing['version'] + 1
                
            cursor.execute(
                """
                INSERT INTO rules (id, rule_type, pattern, action, reason, version)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (new_id, rule_type, pattern, action, reason, version)
            )
            conn.commit()
            return new_id

    def record_rule_feedback(self, rule_id: str, is_hit: bool) -> None:
        """Updates evidence_count, hit_count, miss_count, confidence_score and status."""
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            # Buscamos o estado atual
            current = cursor.execute("SELECT hit_count, miss_count, evidence_count, status FROM rules WHERE id = ?", (rule_id,)).fetchone()
            if not current:
                return
                
            hit_count = current['hit_count'] + (1 if is_hit else 0)
            miss_count = current['miss_count'] + (0 if is_hit else 1)
            evidence_count = current['evidence_count'] + 1
            confidence_score = float(hit_count) / float(evidence_count)
            
            current_status = current['status']
            new_status = current_status
            
            # State Machine:
            if current_status == 'OBSERVING':
                if evidence_count >= 3 and confidence_score >= 0.8:
                    new_status = 'ACTIVE'
            elif current_status == 'ACTIVE':
                if confidence_score < 0.3:
                    new_status = 'QUARANTINED'
            elif current_status == 'QUARANTINED':
                # Recuperação
                if confidence_score >= 0.4:  # Margem para voltar ao ACTIVE
                    new_status = 'ACTIVE'
            
            if new_status != current_status:
                cursor.execute(
                    """
                    UPDATE rules 
                    SET hit_count = ?, miss_count = ?, evidence_count = ?, confidence_score = ?, 
                        last_used = CURRENT_TIMESTAMP, status = ?, status_changed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """, (hit_count, miss_count, evidence_count, confidence_score, new_status, rule_id)
                )
            else:
                cursor.execute(
                    """
                    UPDATE rules 
                    SET hit_count = ?, miss_count = ?, evidence_count = ?, confidence_score = ?, 
                        last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """, (hit_count, miss_count, evidence_count, confidence_score, rule_id)
                )
            conn.commit()

    # ─────────────────────────────────────────────────────────────────────────────
    # Sprint 4.8 — Governança da Memória Financeira
    # ─────────────────────────────────────────────────────────────────────────────

    def get_learning_metrics(self) -> dict:
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            stats = cursor.execute("""
                SELECT 
                    COUNT(*) as total_rules,
                    SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_rules,
                    SUM(CASE WHEN status = 'OBSERVING' THEN 1 ELSE 0 END) as observing_rules,
                    SUM(CASE WHEN status = 'QUARANTINED' THEN 1 ELSE 0 END) as quarantined_rules,
                    SUM(CASE WHEN status = 'RETIRED' THEN 1 ELSE 0 END) as retired_rules,
                    SUM(hit_count) as total_hits,
                    SUM(miss_count) as total_misses
                FROM rules
            """).fetchone()
            
            if not stats:
                return {}
                
            total_hits = stats['total_hits'] or 0
            total_misses = stats['total_misses'] or 0
            
            health_score = 0
            if total_hits + total_misses > 0:
                health_score = (total_hits / (total_hits + total_misses)) * 100
                
            stats['memory_health_score'] = round(health_score, 2)
            
            return stats

    def get_rules_audit(self, limit: int = 100, offset: int = 0, status: str = None) -> list[dict]:
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            query = "SELECT * FROM rules"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
                
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            return cursor.execute(query, params).fetchall()

    def get_top_rules(self, limit: int = 20) -> list[dict]:
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            return cursor.execute("""
                SELECT * FROM rules 
                WHERE status IN ('ACTIVE', 'OBSERVING')
                ORDER BY hit_count DESC, confidence_score DESC 
                LIMIT ?
            """, (limit,)).fetchall()

    def get_problematic_rules(self, limit: int = 20) -> list[dict]:
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            return cursor.execute("""
                SELECT * FROM rules 
                WHERE miss_count > 0
                ORDER BY miss_count DESC 
                LIMIT ?
            """, (limit,)).fetchall()
