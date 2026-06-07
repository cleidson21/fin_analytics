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
        """Deleta os itens do staging e marca a run como CANCELLED, registrando log do rollback."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT status FROM import_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            if not row or row["status"] in ("SUCCESS", "CONFIRMED", "CANCELLED", "FAILED"):
                return False
                
            # Staging items are deleted via ON DELETE CASCADE if we deleted the run,
            # but we want to keep the run for audit purposes.
            # So we manually delete staging rows.
            cursor.execute("DELETE FROM staging_imports WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM staging_positions WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM staging_dividends WHERE import_run_id = ?", (run_id,))
            cursor.execute("DELETE FROM staging_portfolio_evolution WHERE import_run_id = ?", (run_id,))
            cursor.execute(
                """
                UPDATE import_runs 
                SET status = 'CANCELLED',
                    rollback_timestamp = CURRENT_TIMESTAMP,
                    rollback_user = ?,
                    rollback_reason = ?
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
                        position.get("import_run_id"),
                        position.get("source_line_no"),
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
                    (
                        dividend["id_economico"],
                        _source_value(dividend["source"]),
                        dividend["ticker"],
                        dividend["tipo_evento"],
                        dividend["data_pagamento"].isoformat(),
                        _decimal_to_cents(dividend["valor_liquido"]),
                        _decimal_to_cents(dividend["valor_liquido"]),
                        dividend.get("import_run_id"),
                        dividend.get("source_line_no"),
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
                        evo.get("import_run_id"),
                        evo.get("source_line_no"),
                    ),
                )

                if existing is None:
                    inserted += 1
                else:
                    updated += 1

            conn.commit()

        return inserted, updated

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
