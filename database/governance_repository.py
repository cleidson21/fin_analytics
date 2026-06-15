from app.core.observability import transaction_scope, query_scope
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
        return Decimal('0')
    return Decimal(str(value))

def _decimal_to_cents(value) -> int:
    decimal_value = _to_decimal(value)
    cents = (decimal_value * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return int(cents)
import math

def _cents_to_decimal(value) -> Decimal:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return Decimal('0.00')
    return (Decimal(int(value)) / Decimal('100')).quantize(Decimal('0.01'))

def _source_value(source) -> str:
    return getattr(source, 'value', source)
from database.config import GOVERNANCE_DB_PATH as DATABASE_PATH

class GovernanceRepository:

    def __init__(self, db_path: Path=DATABASE_PATH):
        self.db_path = db_path
        pass

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def register_etl_run(self, source: str, file_name: str, rows_read: int, checksum: str='') -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('\n                INSERT INTO etl_runs (source, file_name, rows_read, rows_inserted, rows_updated, checksum)\n                VALUES (?, ?, ?, 0, 0, ?)\n                ', (source, file_name, rows_read, checksum))
            conn.commit()
            return cursor.lastrowid

    def update_etl_run_metrics(self, run_id: int, inserted: int, updated: int):
        with self._get_connection() as conn:
            conn.execute('\n                UPDATE etl_runs\n                SET rows_inserted = ?, rows_updated = ?\n                WHERE id = ?\n                ', (inserted, updated, run_id))
            conn.commit()

    def create_import_run(self, source_type: str, file_name: str, checksum: str, status: str='PENDING', created_by: str | None=None) -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            run_id = uuid.uuid4().hex
            cursor.execute('\n                INSERT INTO import_runs (id, source_type, file_name, checksum, status, created_by)\n                VALUES (?, ?, ?, ?, ?, ?)\n                ', (run_id, source_type, file_name, checksum, status, created_by))
            conn.commit()
            return run_id

    def create_import_artifact(self, import_run_id: str, artifact_type: str, storage_path: str, sha256: str, size_bytes: int, mime_type: str | None=None) -> str:
        artifact_id = uuid.uuid4().hex
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('\n                INSERT INTO import_artifacts (id, import_run_id, artifact_type, storage_path, sha256, size_bytes, mime_type)\n                VALUES (?, ?, ?, ?, ?, ?, ?)\n                ', (artifact_id, import_run_id, artifact_type, storage_path, sha256, size_bytes, mime_type))
            conn.commit()
        return artifact_id

    def update_import_run_status(self, run_id: str, status: str):
        with self._get_connection() as conn, transaction_scope(conn, "update_import_run_status"):
            conn.execute('UPDATE import_runs SET status = ? WHERE id = ?', (status, run_id))
            conn.commit()

    def update_import_run_metrics(self, run_id: str, status: str, rows_read: int, rows_inserted: int, rows_failed: int, error_log: str | None=None, preview_summary: str | None=None):
        with self._get_connection() as conn:
            conn.execute('\n                UPDATE import_runs \n                SET status = ?, finished_at = CURRENT_TIMESTAMP, rows_read = ?, rows_inserted = ?, rows_failed = ?, error_log = ?, preview_summary = ?\n                WHERE id = ?\n                ', (status, rows_read, rows_inserted, rows_failed, error_log, preview_summary, run_id))
            conn.commit()

    def insert_staging_items(self, run_id: str, items: list) -> list[dict]:
        if not items:
            return []
        inserted_items: list[dict] = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            existing_rows = cursor.execute('SELECT source_line_no FROM staging_imports WHERE import_run_id = ?', (run_id,)).fetchall()
            existing_line_nos: set[int] = {row['source_line_no'] for row in existing_rows}
            rows_to_insert: list[tuple] = []
            for item in items:
                source_line_no = item.get('source_line_no')
                date_value = str(item.get('date', '')).strip()
                description = str(item.get('description', '')).strip()
                account = str(item.get('account', '')).strip()
                category_inferred = str(item.get('category_inferred', '')).strip()
                status = str(item.get('status', 'PENDING')).strip().upper() or 'PENDING'
                amount_decimal = _to_decimal(item.get('amount', 0))
                amount_cents = _decimal_to_cents(amount_decimal)
                if source_line_no is None or not date_value or (not description):
                    status = 'ERROR'
                if source_line_no in existing_line_nos:
                    inserted_items.append({'source_line_no': source_line_no, 'date': date_value, 'description': description, 'amount': amount_decimal, 'account': account, 'category_inferred': category_inferred, 'status': 'DUPLICATE'})
                    continue
                existing_line_nos.add(source_line_no)
                rows_to_insert.append((run_id, source_line_no, date_value, description, None, amount_cents, account, category_inferred, status))
                inserted_items.append({'source_line_no': source_line_no, 'import_run_id': run_id, 'date': date_value, 'description': description, 'amount': amount_decimal, 'account': account, 'category_inferred': category_inferred, 'status': status})
            if rows_to_insert:
                cursor.executemany('\n                    INSERT INTO staging_imports (\n                        import_run_id, source_line_no, date, description, amount, amount_cents, account, category_inferred, status\n                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n                    ', rows_to_insert)
            conn.commit()
        return inserted_items

    def process_staging_to_transactions(self, run_id: str) -> list[dict]:
        processed_preview: list[dict] = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            staging_rows = cursor.execute('\n                SELECT id, import_run_id, source_line_no, date, description, amount, amount_cents, account, category_inferred, status\n                FROM staging_imports\n                WHERE import_run_id = ?\n                ORDER BY id ASC\n                ', (run_id,)).fetchall()
            categorizer = SmartCategorizer(Path('taxonomy/rules.csv'))
            for row in staging_rows:
                row_status = str(row['status'] or 'PENDING').upper()
                if row_status in {'DUPLICATE', 'ERROR', 'IMPORTED'}:
                    processed_preview.append({'date': row['date'], 'description': row['description'], 'amount': _cents_to_decimal(row['amount_cents'] if row['amount_cents'] is not None else row['amount']), 'status': row_status})
                    continue
                date_value = str(row['date'] or '').strip()
                description = str(row['description'] or '').strip()
                account = str(row['account'] or '').strip()
                if not date_value or not description:
                    cursor.execute("UPDATE staging_imports SET status = 'ERROR' WHERE id = ?", (row['id'],))
                    processed_preview.append({'date': date_value, 'description': description, 'amount': _cents_to_decimal(row['amount_cents'] if row['amount_cents'] is not None else row['amount']), 'status': 'ERROR'})
                    continue
                description_normalized = normalize_description(description)
                try:
                    amount_cents = int(row['amount_cents'] if row['amount_cents'] is not None else _decimal_to_cents(row['amount']))
                    amount_decimal = _cents_to_decimal(amount_cents)
                except Exception:
                    cursor.execute("UPDATE staging_imports SET status = 'ERROR' WHERE id = ?", (row['id'],))
                    processed_preview.append({'date': date_value, 'description': description, 'amount': row['amount'], 'status': 'ERROR'})
                    continue
                source = account.upper() if account else 'PIERRE'
                transaction_id = generate_economic_id('MANUAL', 'PIERRE', row['source_line_no'], date_value, description_normalized, str(amount_decimal), source)
                transaction_payload = {'id_economico': transaction_id, 'source': source, 'origin': 'PIERRE', 'domain': 'FINANCE', 'import_run_id': run_id, 'source_line_no': row['source_line_no'], 'data': date_value, 'descricao_original': description, 'descricao_normalizada': description_normalized, 'valor': amount_decimal, 'valor_cents': amount_cents, 'identificador_externo': None, 'categoria_origem': row['category_inferred']}
                cat = categorizer.classify(transaction_payload)
                cursor.execute("\n                    INSERT INTO transactions (\n                        id_economico, source, origin, domain, import_run_id, source_line_no, data,\n                        descricao_original, descricao_normalizada, valor, valor_cents, identificador_externo,\n                        macro_categoria, sub_categoria, subnatureza, natureza, perfil, classificacao_fonte\n                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ETL')\n                    ON CONFLICT(id_economico) DO UPDATE SET\n                        origin = excluded.origin,\n                        domain = excluded.domain,\n                        import_run_id = excluded.import_run_id,\n                        source_line_no = excluded.source_line_no,\n                        -- Só atualiza classificação se a transação ainda não foi marcada como MANUAL\n                        macro_categoria = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.macro_categoria ELSE excluded.macro_categoria END,\n                        sub_categoria   = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.sub_categoria   ELSE excluded.sub_categoria   END,\n                        subnatureza     = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.subnatureza     ELSE excluded.subnatureza     END,\n                        natureza        = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.natureza        ELSE excluded.natureza        END,\n                        perfil          = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.perfil          ELSE excluded.perfil          END,\n                        atualizado_em = CURRENT_TIMESTAMP\n                    ", (transaction_payload['id_economico'], transaction_payload['source'], transaction_payload['origin'], transaction_payload['domain'], transaction_payload['import_run_id'], transaction_payload['source_line_no'], transaction_payload['data'], transaction_payload['descricao_original'], transaction_payload['descricao_normalizada'], str(amount_decimal), amount_cents, transaction_payload['identificador_externo'], cat['macro'], cat['sub'], cat['sub'], cat['natureza'].value, cat['perfil'].value))
                cursor.execute("UPDATE staging_imports SET status = 'IMPORTED' WHERE id = ?", (row['id'],))
                processed_preview.append({'date': date_value, 'description': description, 'amount': amount_decimal, 'status': 'IMPORTED'})
            conn.commit()
        return processed_preview

    def insert_wealth_staging_items(self, run_id: str, file_type: str, items: list[dict]):
        if not items:
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if file_type == 'POSICOES':
                cursor.executemany('\n                    INSERT INTO staging_positions (\n                        import_run_id, source_line_no, validation_status, validation_message,\n                        ticker, data_snapshot, source, quantidade, preco_medio, total_investido,\n                        preco_atual, total_atual, ganho\n                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                    ', [(run_id, item.get('source_line_no'), item.get('validation_status', 'PENDING'), item.get('validation_message'), item.get('ticker'), item.get('data_snapshot'), item.get('source', 'MYPROFIT'), item.get('quantidade'), item.get('preco_medio'), item.get('total_investido'), item.get('preco_atual'), item.get('total_atual'), item.get('ganho')) for item in items])
            elif file_type == 'PROVENTOS':
                cursor.executemany('\n                    INSERT INTO staging_dividends (\n                        import_run_id, source_line_no, validation_status, validation_message,\n                        id_economico, source, ticker, tipo_evento, data_pagamento, valor_liquido, valor_liquido_cents\n                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                    ', [(run_id, item.get('source_line_no'), item.get('validation_status', 'PENDING'), item.get('validation_message'), item.get('id_economico', f"MP-{item.get('ticker')}-{item.get('data_pagamento')}"), item.get('source', 'MYPROFIT'), item.get('ticker'), item.get('tipo_evento'), item.get('data_pagamento'), item.get('valor_liquido'), item.get('valor_liquido_cents')) for item in items])
            elif file_type == 'EVOLUCAO':
                cursor.executemany('\n                    INSERT INTO staging_portfolio_evolution (\n                        import_run_id, source_line_no, validation_status, validation_message,\n                        reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,\n                        patrimonio_cents, compras_cents, vendas_cents, proventos_cents,\n                        ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,\n                        ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,\n                        sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct\n                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                    ', [(run_id, item.get('source_line_no'), item.get('validation_status', 'PENDING'), item.get('validation_message'), item.get('reference_month'), item.get('rentabilidade_mensal_pct'), item.get('rentabilidade_acumulada_pct'), item.get('patrimonio_cents'), item.get('compras_cents'), item.get('vendas_cents'), item.get('proventos_cents'), item.get('ibov_mensal_pct'), item.get('ibov_acumulado_pct'), item.get('cdi_mensal_pct'), item.get('cdi_acumulado_pct'), item.get('ipca_mensal_pct'), item.get('ipca_acumulado_pct'), item.get('ifix_mensal_pct'), item.get('ifix_acumulado_pct'), item.get('sp500_mensal_pct'), item.get('sp500_acumulado_pct'), item.get('idiv_mensal_pct'), item.get('idiv_acumulado_pct')) for item in items])
            conn.commit()

    def mark_staging_conflicts(self, run_id: str, file_type: str) -> dict:
        """Classifica os itens do staging com a política: UNCHANGED | UPDATE | VALID."""
        counts = {'unchanged': 0, 'update': 0, 'conflicts': 0}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if file_type == 'POSICOES':
                cursor.execute("\n                    UPDATE staging_positions\n                    SET validation_status = 'UNCHANGED', validation_message = 'Posição idêntica já existe (sem alteração)'\n                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR')\n                    AND EXISTS (\n                        SELECT 1 FROM positions p \n                        WHERE p.ticker = staging_positions.ticker \n                        AND p.data_snapshot = staging_positions.data_snapshot\n                        AND ROUND(CAST(p.quantidade AS REAL), 4) = ROUND(CAST(staging_positions.quantidade AS REAL), 4)\n                        AND ROUND(CAST(p.preco_medio AS REAL), 4) = ROUND(CAST(staging_positions.preco_medio AS REAL), 4)\n                        AND ROUND(CAST(p.total_atual AS REAL), 2) = ROUND(CAST(staging_positions.total_atual AS REAL), 2)\n                    )\n                    ", (run_id,))
                counts['unchanged'] = cursor.rowcount
                cursor.execute("\n                    UPDATE staging_positions\n                    SET validation_status = 'UPDATE', validation_message = 'Posição atualizada (dados alterados)'\n                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR', 'UNCHANGED')\n                    AND EXISTS (\n                        SELECT 1 FROM positions p \n                        WHERE p.ticker = staging_positions.ticker \n                        AND p.data_snapshot = staging_positions.data_snapshot\n                    )\n                    ", (run_id,))
                counts['update'] = cursor.rowcount
                cursor.execute("\n                    UPDATE staging_positions\n                    SET validation_status = 'VALID', validation_message = 'Novo registro a ser importado'\n                    WHERE import_run_id = ? AND validation_status = 'PENDING'\n                    ", (run_id,))
            elif file_type == 'PROVENTOS':
                cursor.execute("\n                    UPDATE staging_dividends\n                    SET validation_status = 'UNCHANGED', validation_message = 'Dividendo idêntico já existe (sem alteração)'\n                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR')\n                    AND EXISTS (\n                        SELECT 1 FROM dividends d \n                        WHERE d.ticker = staging_dividends.ticker \n                        AND d.data_pagamento = staging_dividends.data_pagamento\n                        AND d.valor_liquido_cents = staging_dividends.valor_liquido_cents\n                    )\n                    ", (run_id,))
                counts['unchanged'] = cursor.rowcount
                cursor.execute("\n                    UPDATE staging_dividends\n                    SET validation_status = 'UPDATE', validation_message = 'Provento corrigido (valor alterado)'\n                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR', 'UNCHANGED')\n                    AND EXISTS (\n                        SELECT 1 FROM dividends d \n                        WHERE d.ticker = staging_dividends.ticker \n                        AND d.data_pagamento = staging_dividends.data_pagamento\n                    )\n                    ", (run_id,))
                counts['update'] = cursor.rowcount
                cursor.execute("\n                    UPDATE staging_dividends\n                    SET validation_status = 'VALID', validation_message = 'Novo provento a ser importado'\n                    WHERE import_run_id = ? AND validation_status = 'PENDING'\n                    ", (run_id,))
            elif file_type == 'EVOLUCAO':
                cursor.execute("\n                    UPDATE staging_portfolio_evolution\n                    SET validation_status = 'UNCHANGED', validation_message = 'Mês idêntico já registrado (sem alteração)'\n                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR')\n                    AND EXISTS (\n                        SELECT 1 FROM portfolio_evolution pe\n                        WHERE pe.reference_month = staging_portfolio_evolution.reference_month\n                        AND pe.patrimonio_cents = staging_portfolio_evolution.patrimonio_cents\n                        AND pe.rentabilidade_mensal_pct = staging_portfolio_evolution.rentabilidade_mensal_pct\n                        AND pe.cdi_mensal_pct = staging_portfolio_evolution.cdi_mensal_pct\n                        AND pe.ibov_mensal_pct = staging_portfolio_evolution.ibov_mensal_pct\n                        AND pe.ifix_mensal_pct = staging_portfolio_evolution.ifix_mensal_pct\n                        AND pe.sp500_mensal_pct = staging_portfolio_evolution.sp500_mensal_pct\n                        AND pe.idiv_mensal_pct = staging_portfolio_evolution.idiv_mensal_pct\n                    )\n                    ", (run_id,))
                counts['unchanged'] = cursor.rowcount
                cursor.execute("\n                    UPDATE staging_portfolio_evolution\n                    SET validation_status = 'UPDATE', validation_message = 'Evolução atualizada (dados alterados)'\n                    WHERE import_run_id = ? AND validation_status NOT IN ('ERROR', 'UNCHANGED')\n                    AND EXISTS (\n                        SELECT 1 FROM portfolio_evolution pe\n                        WHERE pe.reference_month = staging_portfolio_evolution.reference_month\n                    )\n                    ", (run_id,))
                counts['update'] = cursor.rowcount
                cursor.execute("\n                    UPDATE staging_portfolio_evolution\n                    SET validation_status = 'VALID', validation_message = 'Novo mês a ser importado'\n                    WHERE import_run_id = ? AND validation_status = 'PENDING'\n                    ", (run_id,))
            conn.commit()
        return counts

    def rollback_import_run(self, run_id: str, user: str='api_user', reason: str='Revertido pelo usuário') -> bool:
        """Deleta os itens e marca a run como ROLLED_BACK, registrando log."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM import_runs WHERE id = ?', (run_id,))
            row = cursor.fetchone()
            if not row or row['status'] in ('CANCELLED', 'FAILED', 'ROLLED_BACK'):
                return False
            cursor.execute('DELETE FROM transactions WHERE import_run_id = ?', (run_id,))
            cursor.execute('DELETE FROM positions WHERE import_run_id = ?', (run_id,))
            cursor.execute('DELETE FROM dividends WHERE import_run_id = ?', (run_id,))
            cursor.execute('DELETE FROM portfolio_evolution WHERE import_run_id = ?', (run_id,))
            cursor.execute('DELETE FROM staging_imports WHERE import_run_id = ?', (run_id,))
            cursor.execute('DELETE FROM staging_positions WHERE import_run_id = ?', (run_id,))
            cursor.execute('DELETE FROM staging_dividends WHERE import_run_id = ?', (run_id,))
            cursor.execute('DELETE FROM staging_portfolio_evolution WHERE import_run_id = ?', (run_id,))
            cursor.execute("\n                UPDATE import_runs \n                SET status = 'ROLLED_BACK',\n                    rollback_timestamp = CURRENT_TIMESTAMP,\n                    rollback_user = ?,\n                    rollback_reason = ?,\n                    rows_inserted = 0,\n                    rows_updated = 0\n                WHERE id = ?\n                ", (user, reason, run_id))
            conn.commit()
            return True

    def lock_import_run_for_confirmation(self, run_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE import_runs SET status = 'PROCESSING_CONFIRMATION' WHERE id = ? AND status = 'AWAITING_CONFIRMATION'", (run_id,))
            conn.commit()
            return cursor.rowcount > 0

    def promote_all_wealth_staging(self, run_id: str) -> dict:
        imported = 0
        updated = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("\n                INSERT OR IGNORE INTO positions (\n                    ticker, data_snapshot, source, quantidade, preco_medio, total_investido,\n                    preco_atual, total_atual, ganho, import_run_id, source_line_no\n                )\n                SELECT ticker, data_snapshot, source, quantidade, preco_medio, total_investido,\n                       preco_atual, total_atual, ganho, import_run_id, source_line_no\n                FROM staging_positions\n                WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')\n                ", (run_id,))
            cursor.execute("UPDATE staging_positions SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')", (run_id,))
            cursor.execute("\n                INSERT OR REPLACE INTO positions (\n                    ticker, data_snapshot, source, quantidade, preco_medio, total_investido,\n                    preco_atual, total_atual, ganho, import_run_id, source_line_no\n                )\n                SELECT ticker, data_snapshot, source, quantidade, preco_medio, total_investido,\n                       preco_atual, total_atual, ganho, import_run_id, source_line_no\n                FROM staging_positions\n                WHERE import_run_id = ? AND validation_status = 'UPDATE'\n                ", (run_id,))
            cursor.execute("UPDATE staging_positions SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status = 'UPDATE'", (run_id,))
            cursor.execute("\n                INSERT OR IGNORE INTO dividends (\n                    id_economico, source, ticker, tipo_evento, data_pagamento, valor_liquido, valor_liquido_cents, import_run_id, source_line_no\n                )\n                SELECT id_economico, source, ticker, tipo_evento, data_pagamento, valor_liquido, valor_liquido_cents, import_run_id, source_line_no\n                FROM staging_dividends\n                WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')\n                ", (run_id,))
            cursor.execute("UPDATE staging_dividends SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')", (run_id,))
            cursor.execute("\n                INSERT OR REPLACE INTO dividends (\n                    id_economico, source, ticker, tipo_evento, data_pagamento, valor_liquido, valor_liquido_cents, import_run_id, source_line_no\n                )\n                SELECT id_economico, source, ticker, tipo_evento, data_pagamento, valor_liquido, valor_liquido_cents, import_run_id, source_line_no\n                FROM staging_dividends\n                WHERE import_run_id = ? AND validation_status = 'UPDATE'\n                ", (run_id,))
            cursor.execute("UPDATE staging_dividends SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status = 'UPDATE'", (run_id,))
            cursor.execute("\n                INSERT OR IGNORE INTO portfolio_evolution (\n                    reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,\n                    patrimonio_cents, compras_cents, vendas_cents, proventos_cents,\n                    ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,\n                    ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,\n                    sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,\n                    import_run_id, source_line_no\n                )\n                SELECT reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,\n                       patrimonio_cents, compras_cents, vendas_cents, proventos_cents,\n                       ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,\n                       ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,\n                       sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,\n                       import_run_id, source_line_no\n                FROM staging_portfolio_evolution\n                WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')\n                ", (run_id,))
            cursor.execute("UPDATE staging_portfolio_evolution SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status IN ('VALID', 'WARNING')", (run_id,))
            cursor.execute("\n                INSERT OR REPLACE INTO portfolio_evolution (\n                    reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,\n                    patrimonio_cents, compras_cents, vendas_cents, proventos_cents,\n                    ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,\n                    ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,\n                    sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,\n                    import_run_id, source_line_no\n                )\n                SELECT reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,\n                       patrimonio_cents, compras_cents, vendas_cents, proventos_cents,\n                       ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,\n                       ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,\n                       sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,\n                       import_run_id, source_line_no\n                FROM staging_portfolio_evolution\n                WHERE import_run_id = ? AND validation_status = 'UPDATE'\n                ", (run_id,))
            cursor.execute("UPDATE staging_portfolio_evolution SET validation_status = 'IMPORTED' WHERE import_run_id = ? AND validation_status = 'UPDATE'", (run_id,))
            cursor.execute("SELECT COUNT(*) FROM staging_positions WHERE import_run_id = ? AND validation_status = 'IMPORTED'", (run_id,))
            imported += cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM staging_dividends WHERE import_run_id = ? AND validation_status = 'IMPORTED'", (run_id,))
            imported += cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM staging_portfolio_evolution WHERE import_run_id = ? AND validation_status = 'IMPORTED'", (run_id,))
            imported += cursor.fetchone()[0]
            cursor.execute("UPDATE import_runs SET status = 'CONFIRMED', finished_at = CURRENT_TIMESTAMP, rows_inserted = ? WHERE id = ?", (imported, run_id))
            conn.commit()
        return {'inserted': imported}

    def insert_raw_events(self, events: list[dict]):
        """Insere ou atualiza RawFinancialEvents em batch."""
        if not events:
            return
        with self._get_connection() as conn:
            import json
            cursor = conn.cursor()
            cursor.executemany('\n                INSERT INTO raw_events (\n                    id, import_run_id, source, event_type, source_line_no, raw_content,\n                    event_date, reference_month, amount_cents, currency,\n                    semantic_id, cross_fingerprint, external_id, metadata,\n                    pipeline_status, match_status\n                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                ON CONFLICT(semantic_id, source) DO UPDATE SET\n                    pipeline_status = excluded.pipeline_status,\n                    match_status = excluded.match_status,\n                    cross_fingerprint = excluded.cross_fingerprint,\n                    metadata = excluded.metadata\n                ', [(e['id'], e['import_run_id'], e['source'], e['event_type'], e.get('source_line_no'), e.get('raw_content'), e.get('event_date'), e.get('reference_month'), e.get('amount_cents'), e.get('currency', 'BRL'), e['semantic_id'], e.get('cross_fingerprint'), e.get('external_id'), json.dumps(e.get('metadata', {})), e['pipeline_status'], e['match_status']) for e in events])
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
            cursor.executemany('\n                INSERT INTO event_links (\n                    id, event_id_a, event_id_b, link_type, confidence, match_method, status, notes\n                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n                ON CONFLICT(id) DO NOTHING\n                ', links)
            conn.commit()

    def get_active_hints(self) -> list[dict]:
        """Retorna todas as dicas de reconciliação ativas."""
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            return cursor.execute('SELECT * FROM reconciliation_hints WHERE active = 1').fetchall()

    def promote_raw_events(self, run_id: str) -> dict:
        """
        Promove eventos do import_run_id de CLASSIFIED para as tabelas finais.
        Retorna dicionário com contagens.
        """
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            raw_events = cursor.execute("\n                SELECT * FROM raw_events \n                WHERE import_run_id = ? \n                  AND pipeline_status = 'CLASSIFIED' \n                  AND match_status != 'DUPLICATE'\n                  AND id NOT IN (SELECT event_id_a FROM event_links WHERE status = 'SUGGESTED')\n                  AND id NOT IN (SELECT event_id_b FROM event_links WHERE status = 'SUGGESTED')\n                ", (run_id,)).fetchall()
            if not raw_events:
                return {'inserted': 0, 'errors': 0}
            inserted_tx = 0
            inserted_pos = 0
            inserted_div = 0
            inserted_evo = 0
            import json
            for event in raw_events:
                meta = json.loads(event.get('metadata') or '{}')
                try:
                    if event['event_type'] in ('TRANSACTION', 'INVOICE'):
                        amount_dec = _cents_to_decimal(event['amount_cents']) if event['amount_cents'] is not None else 0
                        id_economico = meta.get('id_economico')
                        if not id_economico:
                            id_economico = generate_economic_id('MANUAL', event['source'], event['source_line_no'], event['event_date'], meta.get('descricao_normalizada', ''), str(amount_dec), event['source'])
                        cursor.execute("\n                            INSERT INTO transactions (\n                                id_economico, source, origin, import_run_id, source_line_no, data,\n                                descricao_original, descricao_normalizada, valor, valor_cents, identificador_externo,\n                                macro_categoria, sub_categoria, subnatureza, natureza, perfil, classificacao_fonte, raw_event_id\n                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                            ON CONFLICT(id_economico) DO UPDATE SET\n                                raw_event_id = excluded.raw_event_id,\n                                import_run_id = excluded.import_run_id,\n                                macro_categoria = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.macro_categoria ELSE excluded.macro_categoria END,\n                                sub_categoria   = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.sub_categoria   ELSE excluded.sub_categoria   END,\n                                subnatureza     = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.subnatureza     ELSE excluded.subnatureza     END,\n                                natureza        = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.natureza        ELSE excluded.natureza        END,\n                                perfil          = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.perfil          ELSE excluded.perfil          END,\n                                atualizado_em = CURRENT_TIMESTAMP\n                            ", (id_economico, event['source'], meta.get('origin', 'ETL'), run_id, event['source_line_no'], event['event_date'], meta.get('descricao_original', ''), meta.get('descricao_normalizada', ''), str(amount_dec), event['amount_cents'], event['external_id'], meta.get('macro_categoria', 'OUTROS'), meta.get('sub_categoria', 'INDEFINIDO'), meta.get('sub_categoria', 'INDEFINIDO'), meta.get('natureza', 'INDEFINIDO'), 'INDEFINIDO', meta.get('classificacao_fonte', 'ETL'), event['id']))
                        inserted_tx += 1
                    elif event['event_type'] == 'DIVIDEND':
                        amount_dec = _cents_to_decimal(event['amount_cents']) if event['amount_cents'] is not None else 0
                        cursor.execute('\n                            INSERT INTO dividends (\n                                id_economico, source, ticker, tipo_evento, data_pagamento, \n                                valor_liquido, valor_liquido_cents, import_run_id, source_line_no, raw_event_id\n                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                            ON CONFLICT(ticker, data_pagamento, valor_liquido_cents) DO UPDATE SET\n                                raw_event_id = excluded.raw_event_id,\n                                import_run_id = excluded.import_run_id,\n                                atualizado_em = CURRENT_TIMESTAMP\n                            ', (event['external_id'], event['source'], meta.get('ticker'), meta.get('tipo_evento'), event['event_date'], str(amount_dec), event['amount_cents'], run_id, event['source_line_no'], event['id']))
                        inserted_div += 1
                    elif event['event_type'] == 'POSITION':
                        cursor.execute('\n                            INSERT INTO positions (\n                                ticker, data_snapshot, source, quantidade, preco_medio, total_investido,\n                                preco_atual, total_atual, ganho, import_run_id, source_line_no, raw_event_id\n                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                            ON CONFLICT(ticker, data_snapshot) DO UPDATE SET\n                                raw_event_id = excluded.raw_event_id,\n                                import_run_id = excluded.import_run_id,\n                                atualizado_em = CURRENT_TIMESTAMP\n                            ', (meta.get('ticker'), meta.get('data_snapshot'), event['source'], meta.get('quantidade'), meta.get('preco_medio'), meta.get('total_investido'), meta.get('preco_atual'), meta.get('total_atual'), meta.get('ganho'), run_id, event['source_line_no'], event['id']))
                        inserted_pos += 1
                    elif event['event_type'] == 'PORTFOLIO_EVO':
                        cursor.execute('\n                            INSERT INTO portfolio_evolution (\n                                reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,\n                                patrimonio_cents, compras_cents, vendas_cents, op_finalizadas_cents, proventos_cents,\n                                ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,\n                                ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,\n                                sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,\n                                import_run_id, source_line_no\n                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                            ON CONFLICT(reference_month) DO UPDATE SET\n                                import_run_id = excluded.import_run_id,\n                                patrimonio_cents = excluded.patrimonio_cents,\n                                compras_cents = excluded.compras_cents,\n                                vendas_cents = excluded.vendas_cents,\n                                op_finalizadas_cents = excluded.op_finalizadas_cents,\n                                proventos_cents = excluded.proventos_cents\n                            ', (meta.get('reference_month'), meta.get('rentabilidade_mensal_pct'), meta.get('rentabilidade_acumulada_pct'), meta.get('patrimonio_cents'), meta.get('compras_cents'), meta.get('vendas_cents'), meta.get('op_finalizadas_cents'), meta.get('proventos_cents'), meta.get('ibov_mensal_pct'), meta.get('ibov_acumulado_pct'), meta.get('cdi_mensal_pct'), meta.get('cdi_acumulado_pct'), meta.get('ipca_mensal_pct'), meta.get('ipca_acumulado_pct'), meta.get('ifix_mensal_pct'), meta.get('ifix_acumulado_pct'), meta.get('sp500_mensal_pct'), meta.get('sp500_acumulado_pct'), meta.get('idiv_mensal_pct'), meta.get('idiv_acumulado_pct'), run_id, event['source_line_no']))
                        inserted_evo += 1
                    cursor.execute("UPDATE raw_events SET pipeline_status = 'PROMOTED' WHERE id = ?", (event['id'],))
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Erro ao promover evento {event['id']}: {e}")
            conn.commit()
            return {'inserted': inserted_tx + inserted_pos + inserted_div + inserted_evo, 'tx': inserted_tx, 'pos': inserted_pos, 'div': inserted_div, 'evo': inserted_evo, 'errors': 0}

    def create_audit_log(self, entity_type: str, entity_id: str, action: str, field_changes: str=None, changed_by: str=None, cursor=None) -> str:
        import uuid
        log_id = uuid.uuid4().hex

        def _execute(cur):
            cur.execute('\n                INSERT INTO governance_audit_log (id, entity_type, entity_id, action, field_changes, changed_by)\n                VALUES (?, ?, ?, ?, ?, ?)\n                ', (log_id, entity_type, entity_id, action, field_changes, changed_by))
        if cursor:
            _execute(cursor)
            return log_id
        with self._get_connection() as conn:
            cur = conn.cursor()
            _execute(cur)
            conn.commit()
            return log_id

    def get_orphans_count(self) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE import_run_id IS NOT NULL AND import_run_id NOT IN (SELECT id FROM import_runs)')
            count = cursor.fetchone()[0]
            return {'orphan_count': count, 'type': 'transaction', 'table': 'transactions'}

    def update_event_link_status(self, link_id: str, status: str) -> None:
        with self._get_connection() as conn:
            conn.execute('UPDATE event_links SET status = ? WHERE id = ?', (status, link_id))
            conn.commit()

    def get_run_ids_for_link(self, link_id: str) -> list[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = '\n                SELECT a.import_run_id as a_run, b.import_run_id as b_run \n                FROM event_links el\n                JOIN raw_events a ON el.event_id_a = a.id\n                JOIN raw_events b ON el.event_id_b = b.id\n                WHERE el.id = ?\n            '
            row = cursor.execute(query, (link_id,)).fetchone()
            if row:
                runs = {row[0], row[1]}
                return [r for r in runs if r]
            return []

    def get_active_rules(self) -> list[dict]:
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            return cursor.execute("SELECT * FROM governance_rules WHERE status = 'ACTIVE'").fetchall()

    def upsert_rule(self, rule_type: str, pattern: str, action: str, reason: str=None) -> str:
        """
        Creates a new rule or supersedes an existing identical one.
        Returns the ID of the active rule.
        """
        import uuid
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            existing = cursor.execute('SELECT id, version, hit_count, miss_count, action FROM governance_rules WHERE rule_type = ? AND pattern = ? AND active = 1', (rule_type, pattern)).fetchone()
            new_id = str(uuid.uuid4())
            version = 1
            if existing:
                if existing['action'] == action:
                    return existing['id']
                cursor.execute('UPDATE governance_rules SET active = 0, superseded_by = ? WHERE id = ?', (new_id, existing['id']))
                version = existing['version'] + 1
            cursor.execute('\n                INSERT INTO governance_rules (id, rule_type, pattern, action, reason, version)\n                VALUES (?, ?, ?, ?, ?, ?)\n                ', (new_id, rule_type, pattern, action, reason, version))
            conn.commit()
            return new_id

    def record_rule_feedback(self, rule_id: str, is_hit: bool) -> None:
        """Updates evidence_count, hit_count, miss_count, confidence_score and status."""
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            current = cursor.execute('SELECT hit_count, miss_count, evidence_count, status FROM governance_rules WHERE id = ?', (rule_id,)).fetchone()
            if not current:
                return
            hit_count = current['hit_count'] + (1 if is_hit else 0)
            miss_count = current['miss_count'] + (0 if is_hit else 1)
            evidence_count = current['evidence_count'] + 1
            confidence_score = float(hit_count) / float(evidence_count)
            current_status = current['status']
            new_status = current_status
            if current_status == 'OBSERVING':
                if evidence_count >= 3 and confidence_score >= 0.8:
                    new_status = 'ACTIVE'
            elif current_status == 'ACTIVE':
                if confidence_score < 0.3:
                    new_status = 'QUARANTINED'
            elif current_status == 'QUARANTINED':
                if confidence_score >= 0.4:
                    new_status = 'ACTIVE'
            if new_status != current_status:
                cursor.execute('\n                    UPDATE governance_rules \n                    SET hit_count = ?, miss_count = ?, evidence_count = ?, confidence_score = ?, \n                        last_used = CURRENT_TIMESTAMP, status = ?, status_changed_at = CURRENT_TIMESTAMP\n                    WHERE id = ?\n                    ', (hit_count, miss_count, evidence_count, confidence_score, new_status, rule_id))
            else:
                cursor.execute('\n                    UPDATE governance_rules \n                    SET hit_count = ?, miss_count = ?, evidence_count = ?, confidence_score = ?, \n                        last_used = CURRENT_TIMESTAMP\n                    WHERE id = ?\n                    ', (hit_count, miss_count, evidence_count, confidence_score, rule_id))
            conn.commit()

    def get_learning_metrics(self) -> dict:
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            stats = cursor.execute("\n                SELECT \n                    COUNT(*) as total_rules,\n                    SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_rules,\n                    SUM(CASE WHEN status = 'OBSERVING' THEN 1 ELSE 0 END) as observing_rules,\n                    SUM(CASE WHEN status = 'QUARANTINED' THEN 1 ELSE 0 END) as quarantined_rules,\n                    SUM(CASE WHEN status = 'RETIRED' THEN 1 ELSE 0 END) as retired_rules,\n                    SUM(hit_count) as total_hits,\n                    SUM(miss_count) as total_misses\n                FROM governance_rules\n            ").fetchone()
            if not stats:
                return {}
            total_hits = stats['total_hits'] or 0
            total_misses = stats['total_misses'] or 0
            health_score = 0
            if total_hits + total_misses > 0:
                health_score = total_hits / (total_hits + total_misses) * 100
            stats['memory_health_score'] = round(health_score, 2)
            return stats

    def get_rules_audit(self, limit: int=100, offset: int=0, status: str=None) -> list[dict]:
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            query = 'SELECT * FROM governance_rules'
            params = []
            if status:
                query += ' WHERE status = ?'
                params.append(status)
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            return cursor.execute(query, params).fetchall()

    def get_top_rules(self, limit: int=20) -> list[dict]:
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            return cursor.execute("\n                SELECT * FROM governance_rules \n                WHERE status IN ('ACTIVE', 'OBSERVING')\n                ORDER BY hit_count DESC, confidence_score DESC \n                LIMIT ?\n            ", (limit,)).fetchall()

    def get_problematic_rules(self, limit: int=20) -> list[dict]:
        with self._get_connection() as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            return cursor.execute('\n                SELECT * FROM governance_rules \n                WHERE miss_count > 0\n                ORDER BY miss_count DESC \n                LIMIT ?\n            ', (limit,)).fetchall()
    def get_audit_runs(self, status_filter: str='ALL') -> list:
        query = 'SELECT id, file_name, source_type, started_at, status, created_by, rows_read, rows_inserted, rows_updated, rows_failed FROM import_runs'
        params = []
        if status_filter != 'ALL':
            if status_filter == 'CONFIRMED':
                query += " WHERE status = 'CONFIRMED'"
            elif status_filter == 'PENDING':
                query += " WHERE status IN ('PENDING', 'AWAITING_CONFIRMATION', 'PROCESSING_CONFIRMATION')"
            elif status_filter == 'ROLLBACK':
                query += " WHERE status = 'CANCELLED'"
            elif status_filter == 'ERROR':
                query += " WHERE status = 'FAILED'"
        query += ' ORDER BY started_at DESC'
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            return [dict(row) for row in cursor.execute(query, params).fetchall()]

    def get_audit_rollbacks(self) -> list:
        query = "SELECT id, file_name, rollback_timestamp, rollback_user, rollback_reason, started_at FROM import_runs WHERE status = 'CANCELLED' ORDER BY rollback_timestamp DESC"
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            return [dict(row) for row in cursor.execute(query).fetchall()]

    def get_prompt_version_exists(self, name: str, version: int) -> bool:
        with self._get_connection() as conn:
            row = conn.execute("SELECT 1 FROM governance_prompt_versions WHERE name = ? AND version = ?", (name, version)).fetchone()
            return bool(row)

    def insert_prompt_version(self, id: str, name: str, version: int, content: str, active: int, notes: str):
        with self._get_connection() as conn, transaction_scope(conn, "insert_prompt_version"):
            conn.execute(
                "INSERT INTO governance_prompt_versions (id, name, version, content, active, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (id, name, version, content, active, notes)
            )
            conn.commit()

    def get_all_prompts(self, active_only: bool = False) -> list:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM governance_prompt_versions"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY name, version DESC"
            rows = conn.execute(query).fetchall()
            return [dict(r) for r in rows]

    def get_prompt_by_id(self, prompt_id: str):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM governance_prompt_versions WHERE id = ?", (prompt_id,)).fetchone()
            return dict(row) if row else None
            
    def activate_prompt_version(self, prompt_id: str) -> bool:
        with self._get_connection() as conn:
            row = conn.execute("SELECT name FROM governance_prompt_versions WHERE id = ?", (prompt_id,)).fetchone()
            if not row:
                return False
            prompt_name = row[0]
            conn.execute("UPDATE governance_prompt_versions SET active = 0 WHERE name = ?", (prompt_name,))
            conn.execute("UPDATE governance_prompt_versions SET active = 1 WHERE id = ?", (prompt_id,))
            conn.commit()
            return True

    def get_import_status(self) -> dict[str, object]:
        query_last = "\n            SELECT source_line_no, descricao_original\n            FROM transactions\n            WHERE origin = 'PIERRE'\n              AND source_line_no IS NOT NULL\n            ORDER BY source_line_no DESC\n            LIMIT 3\n        "
        query_next = "\n            SELECT COALESCE(MAX(source_line_no), 0) + 1 AS next_line\n            FROM transactions\n            WHERE origin = 'PIERRE'\n              AND source_line_no IS NOT NULL\n        "
        with self._get_connection() as conn:
            cursor = conn.cursor()
            last_rows = cursor.execute(query_last).fetchall()
            next_row = cursor.execute(query_next).fetchone()
        last_items = [{'source_line_no': int(row['source_line_no']), 'description': row['descricao_original']} for row in last_rows]
        next_line = int(next_row['next_line']) if next_row and next_row['next_line'] is not None else 1
        return {'last_items': last_items, 'next_line': next_line}

    def get_import_runs(self, limit: int=50, offset: int=0) -> list[dict]:
        """Busca o histórico de importações recentes."""
        query = '\n            SELECT \n                id, source_type, file_name, checksum, CAST(started_at AS TEXT) as started_at, CAST(finished_at AS TEXT) as finished_at, \n                status, rows_read, rows_inserted, rows_updated, rows_failed, created_by\n            FROM import_runs\n            ORDER BY started_at DESC\n            LIMIT ? OFFSET ?\n        '
        with self._get_connection() as conn:
            rows = conn.cursor().execute(query, [limit, offset]).fetchall()
        return [dict(row) for row in rows]

    def get_import_run_by_id(self, run_id: str) -> dict | None:
        """Busca os detalhes de uma importação específica, incluindo error_log e preview_summary."""
        query = '\n            SELECT \n                id, source_type, file_name, checksum, started_at, finished_at, \n                status, rows_read, rows_inserted, rows_updated, rows_failed, created_by, error_log, preview_summary\n            FROM import_runs\n            WHERE id = ?\n        '
        with self._get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (run_id,)).fetchone()
            return dict(row)

    def get_wealth_staging_items(self, run_id: str) -> dict:
        import json
        run = self.get_import_run_by_id(run_id)
        if not run:
            return {'file_type': 'UNKNOWN', 'items': []}
        file_type = 'UNKNOWN'
        if run.get('preview_summary'):
            try:
                summary = json.loads(run['preview_summary'])
                file_type = summary.get('file_type', 'UNKNOWN')
            except:
                pass
        items = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if file_type == 'POSICOES':
                cursor.execute('SELECT source_line_no, ticker, validation_status, validation_message FROM staging_positions WHERE import_run_id = ? ORDER BY source_line_no ASC', (run_id,))
                items = [dict(r) for r in cursor.fetchall()]
            elif file_type == 'PROVENTOS':
                cursor.execute('SELECT source_line_no, ticker, validation_status, validation_message FROM staging_dividends WHERE import_run_id = ? ORDER BY source_line_no ASC', (run_id,))
                items = [dict(r) for r in cursor.fetchall()]
            elif file_type == 'EVOLUCAO':
                cursor.execute('SELECT source_line_no, reference_month as ticker, validation_status, validation_message FROM staging_portfolio_evolution WHERE import_run_id = ? ORDER BY source_line_no ASC', (run_id,))
                items = [dict(r) for r in cursor.fetchall()]
            elif run.get('source_type') == 'PIERRE':
                cursor.execute('SELECT source_line_no, description as ticker, status as validation_status, NULL as validation_message FROM staging_imports WHERE import_run_id = ? ORDER BY source_line_no ASC', (run_id,))
                items = [dict(r) for r in cursor.fetchall()]
        return {'run_id': run_id, 'file_type': file_type, 'items': items}

    def get_audit_logs(self, entity_type: str=None, action: str=None, changed_by: str=None, start_date: str=None, end_date: str=None, limit: int=100, offset: int=0) -> list:
        query = 'SELECT id, entity_type, entity_id, action, field_changes, changed_by, created_at FROM audit_log WHERE 1=1'
        params = []
        if entity_type:
            query += ' AND entity_type = ?'
            params.append(entity_type)
        if action:
            query += ' AND action = ?'
            params.append(action)
        if changed_by:
            query += ' AND changed_by = ?'
            params.append(changed_by)
        if start_date:
            query += ' AND created_at >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND created_at <= ?'
            params.append(end_date)
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            return [dict(row) for row in cursor.execute(query, params).fetchall()]

    def get_audit_log_by_id(self, log_id: str) -> dict:
        query = 'SELECT id, entity_type, entity_id, action, field_changes, changed_by, created_at FROM audit_log WHERE id = ?'
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            row = cursor.execute(query, (log_id,)).fetchone()
            if row:
                return dict(row)
            return None

    def get_reconciliation_inbox(self) -> dict:
        import json
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            suggestions_query = "\n                SELECT el.*, \n                       a.source as a_source, a.event_type as a_type, a.amount_cents as a_amount, a.event_date as a_date, a.metadata as a_meta,\n                       b.source as b_source, b.event_type as b_type, b.amount_cents as b_amount, b.event_date as b_date, b.metadata as b_meta\n                FROM event_links el\n                LEFT JOIN raw_events a ON el.event_id_a = a.id\n                LEFT JOIN raw_events b ON el.event_id_b = b.id\n                WHERE el.status = 'SUGGESTED'\n            "
            suggestions_raw = cursor.execute(suggestions_query).fetchall()
            suggestions = []
            for row in suggestions_raw:
                d = dict(row)
                d['event_a'] = {'id': d['event_id_a'], 'source': d['a_source'], 'event_type': d['a_type'], 'event_date': d['a_date'], 'amount_cents': d['a_amount'], 'metadata': json.loads(d['a_meta'] or '{}') if d['a_meta'] else {}}
                d['event_b'] = {'id': d['event_id_b'], 'source': d['b_source'], 'event_type': d['b_type'], 'event_date': d['b_date'], 'amount_cents': d['b_amount'], 'metadata': json.loads(d['b_meta'] or '{}') if d['b_meta'] else {}}
                for k in ['a_source', 'a_type', 'a_amount', 'a_date', 'a_meta', 'b_source', 'b_type', 'b_amount', 'b_date', 'b_meta']:
                    d.pop(k, None)
                suggestions.append(d)
            orphans_query = "\n                SELECT id, source, event_type, amount_cents, event_date, metadata\n                FROM raw_events\n                WHERE pipeline_status = 'PROMOTED'\n                  AND id NOT IN (SELECT event_id_a FROM event_links)\n                  AND id NOT IN (SELECT event_id_b FROM event_links)\n                ORDER BY event_date DESC\n                LIMIT 100\n            "
            orphans_raw = cursor.execute(orphans_query).fetchall()
            orphans = []
            for r in orphans_raw:
                od = dict(r)
                od['metadata'] = json.loads(od['metadata'] or '{}') if od['metadata'] else {}
                orphans.append(od)
            return {'suggestions': suggestions, 'orphans': orphans}


    def rollback_governance_data(self, run_id: str):
        with self._get_connection() as conn:
            conn.execute('DELETE FROM import_runs WHERE id = ?', (run_id,))
            conn.commit()
    
    def get_import_artifact_content(self, run_id: str):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT raw_content FROM import_artifacts WHERE import_run_id = ?", (run_id,)).fetchone()
            return dict(row)['raw_content'] if row else None

    def update_import_pipeline_version(self, run_id: str, version: str):
        with self._get_connection() as conn:
            conn.execute("UPDATE import_runs SET pipeline_version = ? WHERE id = ?", (version, run_id))
            conn.commit()

    def get_all_event_links(self):
        with self._get_connection() as conn:
            rows = conn.execute("SELECT event_id_a, event_id_b FROM event_links").fetchall()
            return [(r[0], r[1]) for r in rows]
