from app.core.observability import transaction_scope, query_scope
import logging
import pandas as pd
from math import ceil
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
from database.config import DATABASE_PATH as DATABASE_PATH

class FinancialRepository:

    def __init__(self, db_path: Path=DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def _init_db(self):
        schema_path = Path('database/schema.sql')
        if schema_path.exists():
            with self._get_connection() as conn:
                with open(schema_path, 'r', encoding='utf-8') as file_handle:
                    conn.executescript(file_handle.read())
                self._apply_transaction_migrations(conn)

    def _apply_transaction_migrations(self, conn):

        def ensure_columns(table_name: str, columns: tuple[tuple[str, str], ...]):
            existing_columns = {row['name'] for row in conn.execute(f'PRAGMA table_info({table_name})').fetchall()}
            for column_name, column_type in columns:
                if column_name not in existing_columns:
                    conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
        ensure_columns('transactions', (('origin', 'TEXT'), ('domain', 'TEXT'), ('import_run_id', 'TEXT'), ('source_line_no', 'INTEGER'), ('valor_cents', 'INTEGER'), ('classificacao_fonte', "TEXT NOT NULL DEFAULT 'ETL'")))
        ensure_columns('staging_imports', (('source_line_no', 'INTEGER'), ('amount_cents', 'INTEGER')))
        ensure_columns('dividends', (('valor_liquido_cents', 'INTEGER'),))
        ensure_columns('import_runs', (('rollback_timestamp', 'TIMESTAMP'), ('rollback_reason', 'TEXT'), ('rollback_user', 'TEXT')))
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_staging_imports_run_line ON staging_imports(import_run_id, source_line_no)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_import_run ON transactions(import_run_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_source ON transactions(source)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_classificacao ON transactions(classificacao_fonte)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_staging_imports_run_status ON staging_imports(import_run_id, status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_dividends_ticker ON dividends(ticker)')
        ensure_columns('transactions', (('raw_event_id', 'TEXT'),))
        ensure_columns('positions', (('raw_event_id', 'TEXT'),))
        ensure_columns('dividends', (('raw_event_id', 'TEXT'),))
        ensure_columns('import_runs', (('pipeline_version', "TEXT DEFAULT 'legacy'"),))
        ensure_columns('event_links', (('status', "TEXT NOT NULL DEFAULT 'AUTO_CONFIRMED'"),))
        conn.execute("\n            CREATE TABLE IF NOT EXISTS raw_events (\n                id                TEXT PRIMARY KEY,\n                import_run_id     TEXT NOT NULL,\n                source            TEXT NOT NULL,\n                event_type        TEXT NOT NULL,\n                source_line_no    INTEGER,\n                raw_content       TEXT,\n                event_date        DATE,\n                reference_month   DATE,\n                amount_cents      INTEGER,\n                currency          TEXT NOT NULL DEFAULT 'BRL',\n                semantic_id       TEXT NOT NULL,\n                cross_fingerprint TEXT,\n                external_id       TEXT,\n                metadata          TEXT,\n                pipeline_status   TEXT NOT NULL DEFAULT 'RAW',\n                match_status      TEXT NOT NULL DEFAULT 'NEW',\n                promoted_entity_id TEXT,\n                promoted_table    TEXT,\n                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE\n            )\n        ")
        conn.execute("\n            CREATE TABLE IF NOT EXISTS event_links (\n                id              TEXT PRIMARY KEY,\n                event_id_a      TEXT NOT NULL,\n                event_id_b      TEXT NOT NULL,\n                link_type       TEXT NOT NULL,\n                confidence      REAL NOT NULL DEFAULT 1.0,\n                match_method    TEXT NOT NULL DEFAULT 'EXACT',\n                status          TEXT NOT NULL DEFAULT 'AUTO_CONFIRMED',\n                confirmed_by    TEXT,\n                confirmed_at    TIMESTAMP,\n                notes           TEXT,\n                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                FOREIGN KEY(event_id_a) REFERENCES raw_events(id) ON DELETE CASCADE,\n                FOREIGN KEY(event_id_b) REFERENCES raw_events(id) ON DELETE CASCADE\n            )\n        ")
        conn.execute('\n            CREATE TABLE IF NOT EXISTS reconciliation_hints (\n                id          TEXT PRIMARY KEY,\n                pattern_a   TEXT NOT NULL,\n                source_a    TEXT NOT NULL,\n                pattern_b   TEXT NOT NULL,\n                source_b    TEXT NOT NULL,\n                link_type   TEXT NOT NULL,\n                confidence  REAL NOT NULL DEFAULT 0.8,\n                active      INTEGER NOT NULL DEFAULT 1,\n                confirmed_by TEXT,\n                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n            )\n        ')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_raw_events_run ON raw_events(import_run_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_raw_events_semantic ON raw_events(semantic_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_raw_events_cross_fp ON raw_events(cross_fingerprint)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_raw_events_type_status ON raw_events(event_type, pipeline_status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_raw_events_source ON raw_events(source)')
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_events_semantic_source ON raw_events(semantic_id, source)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_event_links_a ON event_links(event_id_a)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_event_links_b ON event_links(event_id_b)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_reconciliation_hints_active ON reconciliation_hints(active, source_a, source_b)')
        conn.commit()

    def upsert_transactions(self, transactions: list, categorizer) -> tuple[int, int]:
        if not transactions:
            return (0, 0)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            rows: list[tuple] = []
            ids: list[str] = []
            for transaction in transactions:
                cat = categorizer.classify(transaction)
                source_value = _source_value(transaction.get('source'))
                origin_value = transaction.get('origin') or source_value
                domain_value = transaction.get('domain') or 'FINANCE'
                valor_cents = _decimal_to_cents(transaction['valor'])
                ids.append(transaction['id_economico'])
                rows.append((transaction['id_economico'], source_value, origin_value, domain_value, transaction.get('source_line_no'), transaction['data'].isoformat(), transaction['descricao_original'], transaction['descricao_normalizada'], valor_cents, valor_cents, transaction['identificador_externo'], cat['macro'], cat['sub'], cat['sub'], cat['natureza'].value, cat['perfil'].value))
            placeholders = ','.join('?' * len(ids))
            existing_ids: set[str] = {row[0] for row in cursor.execute(f'SELECT id_economico FROM transactions WHERE id_economico IN ({placeholders})', ids).fetchall()}
            inserted = len(ids) - len(existing_ids)
            updated = len(existing_ids)
            cursor.executemany("\n                INSERT INTO transactions (\n                    id_economico, source, origin, domain, source_line_no, data, descricao_original, descricao_normalizada,\n                    valor, valor_cents, identificador_externo, macro_categoria, sub_categoria, subnatureza, natureza, perfil,\n                    classificacao_fonte\n                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ETL')\n                ON CONFLICT(id_economico) DO UPDATE SET\n                    source = excluded.source,\n                    origin = excluded.origin,\n                    domain = excluded.domain,\n                    source_line_no = excluded.source_line_no,\n                    descricao_normalizada = excluded.descricao_normalizada,\n                    macro_categoria = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.macro_categoria ELSE excluded.macro_categoria END,\n                    sub_categoria   = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.sub_categoria   ELSE excluded.sub_categoria   END,\n                    subnatureza     = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.subnatureza     ELSE excluded.subnatureza     END,\n                    natureza        = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.natureza        ELSE excluded.natureza        END,\n                    perfil          = CASE WHEN transactions.classificacao_fonte = 'MANUAL' THEN transactions.perfil          ELSE excluded.perfil          END,\n                    atualizado_em = CURRENT_TIMESTAMP\n                ", rows)
            conn.commit()
        return (inserted, updated)

    def upsert_positions(self, positions: list) -> tuple[int, int]:
        if not positions:
            return (0, 0)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            rows: list[tuple] = []
            keys: list[tuple] = []
            for position in positions:
                snapshot_iso = position['data_snapshot'].isoformat()
                keys.append((position['ticker'], snapshot_iso))
                rows.append((position['ticker'], snapshot_iso, _source_value(position['source']), str(position['quantidade']), str(position['preco_medio']), str(position['total_investido']), str(position['preco_atual']), str(position['total_atual']), str(position['ganho']), position.get('import_run_id'), position.get('source_line_no')))
            if keys:
                existing_count = cursor.execute(f"SELECT COUNT(*) FROM positions WHERE (ticker, data_snapshot) IN ({','.join(('(?,?)' for _ in keys))})", [val for k in keys for val in k]).fetchone()[0]
            else:
                existing_count = 0
            inserted = len(rows) - existing_count
            updated = existing_count
            cursor.executemany('\n                INSERT INTO positions (\n                    ticker, data_snapshot, source, quantidade, preco_medio,\n                    total_investido, preco_atual, total_atual, ganho,\n                    import_run_id, source_line_no\n                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                ON CONFLICT(ticker, data_snapshot) DO UPDATE SET\n                    source = excluded.source,\n                    quantidade = excluded.quantidade,\n                    preco_medio = excluded.preco_medio,\n                    total_investido = excluded.total_investido,\n                    preco_atual = excluded.preco_atual,\n                    total_atual = excluded.total_atual,\n                    ganho = excluded.ganho,\n                    import_run_id = excluded.import_run_id,\n                    source_line_no = excluded.source_line_no,\n                    atualizado_em = CURRENT_TIMESTAMP\n                ', rows)
            conn.commit()
        return (inserted, updated)

    def upsert_dividends(self, dividends: list) -> tuple[int, int]:
        if not dividends:
            return (0, 0)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            rows: list[tuple] = []
            ids: list[str] = []
            for dividend in dividends:
                ids.append(dividend['id_economico'])
                vliq_cents = _decimal_to_cents(dividend['valor_liquido'])
                rows.append((dividend['id_economico'], _source_value(dividend['source']), dividend['ticker'], dividend['tipo_evento'], dividend['data_pagamento'].isoformat(), vliq_cents, vliq_cents, dividend.get('import_run_id'), dividend.get('source_line_no')))
            placeholders = ','.join('?' * len(ids))
            existing_ids: set[str] = {row[0] for row in cursor.execute(f'SELECT id_economico FROM dividends WHERE id_economico IN ({placeholders})', ids).fetchall()}
            inserted = len(ids) - len(existing_ids)
            updated = len(existing_ids)
            cursor.executemany('\n                INSERT INTO dividends (\n                    id_economico, source, ticker, tipo_evento,\n                    data_pagamento, valor_liquido, valor_liquido_cents,\n                    import_run_id, source_line_no\n                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n                ON CONFLICT(id_economico) DO UPDATE SET\n                    source = excluded.source,\n                    ticker = excluded.ticker,\n                    tipo_evento = excluded.tipo_evento,\n                    data_pagamento = excluded.data_pagamento,\n                    valor_liquido = excluded.valor_liquido,\n                    valor_liquido_cents = excluded.valor_liquido_cents,\n                    import_run_id = excluded.import_run_id,\n                    source_line_no = excluded.source_line_no,\n                    atualizado_em = CURRENT_TIMESTAMP\n                ', rows)
            conn.commit()
        return (inserted, updated)

    def upsert_portfolio_evolution(self, evos: list) -> tuple[int, int]:
        if not evos:
            return (0, 0)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            rows: list[tuple] = []
            months: list[str] = []
            for evo in evos:
                month_iso = evo['reference_month'].isoformat()
                months.append(month_iso)
                rows.append((month_iso, str(evo['rentabilidade_mensal_pct']), str(evo['rentabilidade_acumulada_pct']), evo['patrimonio_cents'], evo['compras_cents'], evo['vendas_cents'], evo['op_finalizadas_cents'], evo['proventos_cents'], str(evo['ibov_mensal_pct']), str(evo['ibov_acumulado_pct']), str(evo['cdi_mensal_pct']), str(evo['cdi_acumulado_pct']), str(evo['ipca_mensal_pct']), str(evo['ipca_acumulado_pct']), str(evo['ifix_mensal_pct']), str(evo['ifix_acumulado_pct']), str(evo['sp500_mensal_pct']), str(evo['sp500_acumulado_pct']), str(evo['idiv_mensal_pct']), str(evo['idiv_acumulado_pct']), evo.get('import_run_id'), evo.get('source_line_no')))
            placeholders = ','.join('?' * len(months))
            existing_count = cursor.execute(f'SELECT COUNT(*) FROM portfolio_evolution WHERE reference_month IN ({placeholders})', months).fetchone()[0]
            inserted = len(rows) - existing_count
            updated = existing_count
            cursor.executemany('\n                INSERT INTO portfolio_evolution (\n                    reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,\n                    patrimonio_cents, compras_cents, vendas_cents, op_finalizadas_cents, proventos_cents,\n                    ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,\n                    ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,\n                    sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct,\n                    import_run_id, source_line_no\n                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                ON CONFLICT(reference_month) DO UPDATE SET\n                    rentabilidade_mensal_pct = excluded.rentabilidade_mensal_pct,\n                    rentabilidade_acumulada_pct = excluded.rentabilidade_acumulada_pct,\n                    patrimonio_cents = excluded.patrimonio_cents,\n                    compras_cents = excluded.compras_cents,\n                    vendas_cents = excluded.vendas_cents,\n                    op_finalizadas_cents = excluded.op_finalizadas_cents,\n                    proventos_cents = excluded.proventos_cents,\n                    ibov_mensal_pct = excluded.ibov_mensal_pct,\n                    ibov_acumulado_pct = excluded.ibov_acumulado_pct,\n                    cdi_mensal_pct = excluded.cdi_mensal_pct,\n                    cdi_acumulado_pct = excluded.cdi_acumulado_pct,\n                    ipca_mensal_pct = excluded.ipca_mensal_pct,\n                    ipca_acumulado_pct = excluded.ipca_acumulado_pct,\n                    ifix_mensal_pct = excluded.ifix_mensal_pct,\n                    ifix_acumulado_pct = excluded.ifix_acumulado_pct,\n                    sp500_mensal_pct = excluded.sp500_mensal_pct,\n                    sp500_acumulado_pct = excluded.sp500_acumulado_pct,\n                    idiv_mensal_pct = excluded.idiv_mensal_pct,\n                    idiv_acumulado_pct = excluded.idiv_acumulado_pct,\n                    import_run_id = excluded.import_run_id,\n                    source_line_no = excluded.source_line_no\n                ', rows)
            conn.commit()
        return (inserted, updated)

    def get_user_by_username(self, username: str) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            user = cursor.execute('SELECT id, username, email, password_hash, role, active FROM users WHERE username = ?', (username,)).fetchone()
            if user:
                return dict(user)
            return None

    def create_user(self, username: str, email: str, password_hash: str, role: str='VIEWER') -> str:
        import uuid
        user_id = uuid.uuid4().hex
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('\n                INSERT INTO users (id, username, email, password_hash, role, active)\n                VALUES (?, ?, ?, ?, ?, 1)\n                ', (user_id, username, email, password_hash, role))
            conn.commit()
            return user_id

    def vacuum_database(self) -> dict:
        import os
        size_before = os.path.getsize(self.db_path)
        with self._get_connection() as conn:
            conn.isolation_level = None
            conn.execute('VACUUM')
            conn.isolation_level = ''
        size_after = os.path.getsize(self.db_path)
        return {'size_before_bytes': size_before, 'size_after_bytes': size_after}

    def analyze_database(self) -> bool:
        with self._get_connection() as conn:
            conn.isolation_level = None
            conn.execute('ANALYZE')
            conn.isolation_level = ''
            return True

    def _dict_factory(self, cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def update_transaction(self, id_economico: str, updates: dict, changed_by: str=None) -> bool:
        import json
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM transactions WHERE id_economico = ?', (id_economico,))
            old_record = cursor.fetchone()
            if not old_record:
                return False
            field_changes = {}
            set_clauses = []
            params = []
            for k, v in updates.items():
                if v is not None and k in old_record and (old_record[k] != v):
                    field_changes[k] = {'old': old_record[k], 'new': v}
                    set_clauses.append(f'{k} = ?')
                    params.append(v)
            if not field_changes:
                return True
            params.append(id_economico)
            cursor.execute(f"UPDATE transactions SET {', '.join(set_clauses)} WHERE id_economico = ?", params)
            self.create_audit_log('TRANSACTION', id_economico, 'UPDATE', json.dumps(field_changes), changed_by, cursor=cursor)
            conn.commit()
            return True

    def update_position(self, ticker: str, data_snapshot: str, updates: dict, changed_by: str=None) -> bool:
        import json
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM positions WHERE ticker = ? AND data_snapshot = ?', (ticker, data_snapshot))
            old_record = cursor.fetchone()
            if not old_record:
                return False
            field_changes = {}
            set_clauses = []
            params = []
            for k, v in updates.items():
                if v is not None and k in old_record and (old_record[k] != v):
                    field_changes[k] = {'old': old_record[k], 'new': v}
                    set_clauses.append(f'{k} = ?')
                    params.append(v)
            if not field_changes:
                return True
            params.extend([ticker, data_snapshot])
            cursor.execute(f"UPDATE positions SET {', '.join(set_clauses)} WHERE ticker = ? AND data_snapshot = ?", params)
            entity_id = f'{ticker}|{data_snapshot}'
            self.create_audit_log('POSITION', entity_id, 'UPDATE', json.dumps(field_changes), changed_by, cursor=cursor)
            conn.commit()
            return True

    def update_dividend(self, id_economico: str, updates: dict, changed_by: str=None) -> bool:
        import json
        with self._get_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM dividends WHERE id_economico = ?', (id_economico,))
            old_record = cursor.fetchone()
            if not old_record:
                return False
            field_changes = {}
            set_clauses = []
            params = []
            for k, v in updates.items():
                if v is not None and k in old_record and (old_record[k] != v):
                    field_changes[k] = {'old': old_record[k], 'new': v}
                    set_clauses.append(f'{k} = ?')
                    params.append(v)
            if not field_changes:
                return True
            params.append(id_economico)
            cursor.execute(f"UPDATE dividends SET {', '.join(set_clauses)} WHERE id_economico = ?", params)
            self.create_audit_log('DIVIDEND', id_economico, 'UPDATE', json.dumps(field_changes), changed_by, cursor=cursor)
            conn.commit()
            return True

    def merge_categories(self, source_category: str, target_category: str, changed_by: str=None) -> int:
        import json
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE macro_categoria = ? OR sub_categoria = ?', (source_category, source_category))
            count = cursor.fetchone()[0]
            if count == 0:
                return 0
            cursor.execute('UPDATE transactions SET macro_categoria = ? WHERE macro_categoria = ?', (target_category, source_category))
            cursor.execute('UPDATE transactions SET sub_categoria = ? WHERE sub_categoria = ?', (target_category, source_category))
            field_changes = {'categoria': {'old': source_category, 'new': target_category}, 'affected_rows': count}
            self.create_audit_log('CATEGORY', source_category, 'MERGE', json.dumps(field_changes), changed_by, cursor=cursor)
            conn.commit()
            return count
    def get_quarantine_transactions(self) -> pd.DataFrame:
        """Puxa o lixo/ruído que precisa de novas regras no rules.csv."""
        query = "\n            SELECT data, descricao_original, valor_cents as valor_cents, identificador_externo\n            FROM transactions\n            WHERE macro_categoria = 'OUTROS'\n               OR sub_categoria = 'INDEFINIDO'\n            ORDER BY data DESC\n        "
        df = self._read_dataframe(query, ['valor_cents'])
        if 'valor_cents' in df.columns:
            df['valor'] = df['valor_cents'].apply(_cents_to_decimal)
            df.drop(columns=['valor_cents'], inplace=True)
        return df

    def get_dashboard_metrics(self) -> dict:
        """Busca KPIs globais para o Dashboard de Governança."""
        query = "\n            SELECT\n                COUNT(id) as total_runs,\n                SUM(CASE WHEN status = 'CONFIRMED' THEN 1 ELSE 0 END) as confirmed_runs,\n                SUM(CASE WHEN status IN ('PENDING', 'AWAITING_CONFIRMATION', 'PROCESSING', 'PROCESSING_CONFIRMATION') THEN 1 ELSE 0 END) as pending_runs,\n                COALESCE(SUM(rows_inserted), 0) as lines_inserted,\n                COALESCE(SUM(rows_updated), 0) as lines_updated,\n                COALESCE(SUM(rows_failed), 0) as lines_failed,\n                MAX(started_at) as last_import\n            FROM import_runs\n            WHERE source_type != 'LEGACY'\n        "
        with self._get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query).fetchone()
            if not row:
                return {'total_runs': 0, 'confirmed_runs': 0, 'pending_runs': 0, 'lines_inserted': 0, 'lines_updated': 0, 'lines_failed': 0, 'last_import': None}
            return {'total_runs': row['total_runs'] or 0, 'confirmed_runs': row['confirmed_runs'] or 0, 'pending_runs': row['pending_runs'] or 0, 'lines_inserted': row['lines_inserted'] or 0, 'lines_updated': row['lines_updated'] or 0, 'lines_failed': row['lines_failed'] or 0, 'last_import': row['last_import']}

    def get_admin_positions(self, limit: int=50, offset: int=0, ticker: str=None, snapshot_date: str=None, classe_ativo: str=None) -> tuple[list, int]:
        where_clauses = ['1=1']
        params = []
        if ticker:
            where_clauses.append('ticker LIKE ?')
            params.append(f'%{ticker}%')
        if snapshot_date:
            where_clauses.append('data_snapshot = ?')
            params.append(snapshot_date)
        if classe_ativo:
            where_clauses.append('classe_ativo = ?')
            params.append(classe_ativo)
        where_str = ' AND '.join(where_clauses)
        count_query = f'SELECT COUNT(*) FROM positions WHERE {where_str}'
        query = f'SELECT ticker, data_snapshot, quantidade, preco_medio, total_atual as valor_total, classe_ativo, observacao FROM positions WHERE {where_str} ORDER BY data_snapshot DESC, ticker ASC LIMIT ? OFFSET ?'
        with self._get_connection() as conn:
            cursor = conn.cursor()
            total = cursor.execute(count_query, params).fetchone()[0]
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            items = []
            for row in cursor.execute(query, params + [limit, offset]).fetchall():
                d = dict(row)
                d['snapshot_date'] = d.pop('data_snapshot')
                d['preco_medio'] = _cents_to_decimal(d.get('preco_medio'))
                d['valor_total'] = _cents_to_decimal(d.get('valor_total'))
                items.append(d)
            return (items, total)

    def get_admin_dividends(self, limit: int=50, offset: int=0, ticker: str=None, start_date: str=None, end_date: str=None, tipo_evento: str=None) -> tuple[list, int]:
        where_clauses = ['1=1']
        params = []
        if ticker:
            where_clauses.append('ticker LIKE ?')
            params.append(f'%{ticker}%')
        if start_date:
            where_clauses.append('data_pagamento >= ?')
            params.append(start_date)
        if end_date:
            where_clauses.append('data_pagamento <= ?')
            params.append(end_date)
        if tipo_evento:
            where_clauses.append('tipo_evento = ?')
            params.append(tipo_evento)
        where_str = ' AND '.join(where_clauses)
        count_query = f'SELECT COUNT(*) FROM dividends WHERE {where_str}'
        query = f'SELECT id_economico, ticker, tipo_evento, valor_liquido_cents as valor, data_pagamento, observacao FROM dividends WHERE {where_str} ORDER BY data_pagamento DESC LIMIT ? OFFSET ?'
        with self._get_connection() as conn:
            cursor = conn.cursor()
            total = cursor.execute(count_query, params).fetchone()[0]
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            items = []
            for row in cursor.execute(query, params + [limit, offset]).fetchall():
                d = dict(row)
                d['valor'] = _cents_to_decimal(d.get('valor'))
                items.append(d)
            return (items, total)

    def get_admin_categories(self, limit: int=50, offset: int=0) -> tuple[list, int]:
        count_query = "SELECT COUNT(DISTINCT macro_categoria) FROM transactions WHERE macro_categoria IS NOT NULL AND macro_categoria != ''"
        query = "SELECT macro_categoria as categoria, COUNT(*) as quantidade_transacoes FROM transactions WHERE macro_categoria IS NOT NULL AND macro_categoria != '' GROUP BY macro_categoria ORDER BY quantidade_transacoes DESC LIMIT ? OFFSET ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            total = cursor.execute(count_query).fetchone()[0]
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            items = [dict(row) for row in cursor.execute(query, [limit, offset]).fetchall()]
            return (items, total)


    def rollback_financial_data(self, run_id: str):
        with self._get_connection() as conn, transaction_scope(conn, "rollback_financial_data"):
            cursor = conn.cursor()
            cursor.execute('DELETE FROM positions WHERE import_run_id = ?', (run_id,))
            cursor.execute('DELETE FROM dividends WHERE import_run_id = ?', (run_id,))
            cursor.execute('DELETE FROM portfolio_evolution WHERE import_run_id = ?', (run_id,))
            cursor.execute('DELETE FROM transactions WHERE import_run_id = ?', (run_id,))
            conn.commit()
    



    def _build_transaction_filters(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        account: str | None = None,
        category: str | None = None,
        natureza: str | None = None,
    ) -> tuple[str, list[object]]:
        where_clauses: list[str] = []
        params: list[object] = []

        if start_date:
            where_clauses.append("data >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("data <= ?")
            params.append(end_date)

        if account:
            where_clauses.append("source = ?")
            params.append(account)

        if category:
            where_clauses.append("macro_categoria = ?")
            params.append(category)

        if natureza:
            where_clauses.append("natureza = ?")
            params.append(natureza)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return where_sql, params

    def _read_dataframe(self, query: str, numeric_columns: list[str]) -> pd.DataFrame:
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)

        for column in numeric_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column])

        return df

    def get_transactions(
        self,
        limit: int = 50,
        offset: int = 0,
        start_date: str | None = None,
        end_date: str | None = None,
        account: str | None = None,
        category: str | None = None,
        natureza: str | None = None,
    ) -> tuple[list[dict], int]:
        where_sql, params = self._build_transaction_filters(
            start_date=start_date,
            end_date=end_date,
            account=account,
            category=category,
            natureza=natureza,
        )

        count_query = f"SELECT COUNT(*) as total FROM transactions {where_sql}"
        items_query = f"""
            SELECT
                id_economico as id,
                data,
                descricao_original as description,
                macro_categoria as category,
                natureza,
                subnatureza,
                source as account,
                valor_cents as amount_cents
            FROM transactions
            {where_sql}
            ORDER BY data DESC, id_economico DESC
            LIMIT ? OFFSET ?
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()
            total = cursor.execute(count_query, params).fetchone()[0]

            items_params = [*params, limit, offset]
            rows = cursor.execute(items_query, items_params).fetchall()

        items = [
            {
                "id": row["id"],
                "data": row["data"],
                "description": row["description"],
                "category": row["category"],
                "natureza": row["natureza"],
                "subnatureza": row["subnatureza"],
                "account": row["account"],
                "amount": _cents_to_decimal(row["amount_cents"]),
            }
            for row in rows
        ]
        return items, total

    def get_transactions_summary(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        account: str | None = None,
        category: str | None = None,
        natureza: str | None = None,
    ) -> dict[str, float]:
        where_sql, params = self._build_transaction_filters(
            start_date=start_date,
            end_date=end_date,
            account=account,
            category=category,
            natureza=natureza,
        )

        query = f"""
            SELECT
                COALESCE(SUM(CASE WHEN natureza = 'INCOME' THEN ABS(valor_cents) ELSE 0 END), 0) as income_cents,
                COALESCE(SUM(CASE WHEN natureza = 'EXPENSE' THEN ABS(valor_cents) ELSE 0 END), 0) as expense_cents,
                COALESCE(SUM(CASE WHEN natureza = 'INCOME' THEN ABS(valor_cents) ELSE 0 END), 0)
                - COALESCE(SUM(CASE WHEN natureza = 'EXPENSE' THEN ABS(valor_cents) ELSE 0 END), 0) as balance_cents
            FROM transactions
            {where_sql}
        """

        with self._get_connection() as conn:
            row = conn.cursor().execute(query, params).fetchone()

        if not row or row["income_cents"] is None:
            return {"income": Decimal("0.00"), "expense": Decimal("0.00"), "balance": Decimal("0.00")}

        return {
            "income": _cents_to_decimal(row["income_cents"] or 0),
            "expense": _cents_to_decimal(row["expense_cents"] or 0),
            "balance": _cents_to_decimal(row["balance_cents"] or 0),
        }

    def get_transactions_total_pages(self, total: int, limit: int) -> int:
        return ceil(total / limit) if total else 0

    def update_transaction_category(
        self,
        transaction_id: str,
        macro_categoria: str,
        natureza: str | None = None,
        subnatureza: str | None = None,
    ) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            current = cursor.execute(
                """
                SELECT macro_categoria, sub_categoria, subnatureza, natureza, perfil,
                       source_line_no, origin
                FROM transactions
                WHERE id_economico = ?
                """,
                (transaction_id,),
            ).fetchone()

            if current is None:
                return False

            natureza_final = natureza or current["natureza"]
            subnatureza_final = subnatureza or current["subnatureza"] or current["sub_categoria"]
            perfil_final = current["perfil"]

            cursor.execute(
                """
                UPDATE transactions
                SET macro_categoria = ?,
                    sub_categoria = ?,
                    subnatureza = ?,
                    natureza = ?,
                    classificacao_fonte = 'MANUAL',
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id_economico = ?
                """,
                (macro_categoria, subnatureza_final, subnatureza_final, natureza_final, transaction_id),
            )


            conn.commit()
            return cursor.rowcount > 0

    def get_accounts_summary(self) -> list[dict]:
        query = "SELECT source as institution, SUM(valor_cents) as balance_cents FROM transactions GROUP BY source ORDER BY balance_cents DESC"
        with self._get_connection() as conn:
            rows = conn.cursor().execute(query).fetchall()

        return [
            {"institution": row["institution"], "balance": _cents_to_decimal(row["balance_cents"])}
            for row in rows
        ]

    def get_account_catalog(self) -> list[str]:
        query = "SELECT DISTINCT source as account FROM transactions ORDER BY account ASC"
        with self._get_connection() as conn:
            rows = conn.cursor().execute(query).fetchall()
        return [row["account"] for row in rows]

    def get_cashflow_summary(self, month: str | None = None) -> pd.DataFrame:
        """Retorna Receitas e Gastos. Se 'month' for passado (ex: '2026-04'), filtra por esse mês."""
        query = """
            SELECT natureza, SUM(valor_cents) as total_cents
            FROM transactions
            WHERE natureza IN ('INCOME', 'EXPENSE')
        """
        params: list[str] = []
        if month:
            query += " AND strftime('%Y-%m', data) = ?"
            params.append(month)

        query += " GROUP BY natureza"

        with self._get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)

        if "total_cents" in df.columns:
            df["total"] = df["total_cents"].apply(_cents_to_decimal)
            df.drop(columns=["total_cents"], inplace=True)

        return df

    def get_expenses_by_category(self, month: str | None = None) -> pd.DataFrame:
        """Agrupa os gastos por Macro Categoria para o gráfico de barras/pizza."""
        query = """
            SELECT macro_categoria, ABS(SUM(valor_cents)) as total_cents
            FROM transactions
            WHERE natureza = 'EXPENSE' AND perfil != 'IGNORADO'
        """
        params: list[str] = []
        if month:
            query += " AND strftime('%Y-%m', data) = ?"
            params.append(month)

        query += " GROUP BY macro_categoria ORDER BY total_cents DESC"
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn, params=params)
        if "total_cents" in df.columns:
            df["total"] = df["total_cents"].apply(_cents_to_decimal)
            df.drop(columns=["total_cents"], inplace=True)

        return df

    def get_current_net_worth(self):
        """Calcula o Patrimônio Total atual com base no snapshot mais recente."""
        query = """
            SELECT SUM(total_atual) as net_worth
            FROM positions
            WHERE data_snapshot = (SELECT MAX(data_snapshot) FROM positions)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()[0]
            from decimal import Decimal
            return Decimal(str(result)) if result is not None else Decimal("0")

    def get_portfolio_allocation(self) -> pd.DataFrame:
        query = """
            SELECT classe_ativo as asset_class, SUM(total_atual) as current_total 
            FROM positions 
            WHERE data_snapshot = (SELECT MAX(data_snapshot) FROM positions)
            GROUP BY classe_ativo
        """
        with self._get_connection() as conn:
            return pd.read_sql(query, conn)

    def get_net_worth_history(self) -> pd.DataFrame:
        query = """
            SELECT 
                strftime('%Y-%m', reference_month) as month, 
                (patrimonio_cents / 100.0) as net_worth 
            FROM portfolio_evolution 
            ORDER BY reference_month ASC
        """
        with self._get_connection() as conn:
            return pd.read_sql(query, conn)

    def get_detailed_positions(self) -> pd.DataFrame:
        query = """
            WITH latest AS (
                SELECT MAX(data_snapshot) as max_data FROM positions
            ),
            totals AS (
                SELECT SUM(total_atual) as sum_total 
                FROM positions 
                WHERE data_snapshot = (SELECT max_data FROM latest)
            )
            SELECT 
                ticker, 
                classe_ativo as asset_class, 
                '' as asset_subclass, 
                quantidade, 
                preco_medio, 
                total_investido as valor_investido, 
                total_atual as valor_atual, 
                ganho, 
                (total_atual * 100.0 / (SELECT sum_total FROM totals)) as peso_percentual
            FROM positions
            WHERE data_snapshot = (SELECT max_data FROM latest)
            ORDER BY peso_percentual DESC
        """
        with self._get_connection() as conn:
            return pd.read_sql(query, conn)

    def get_dividend_history(self) -> pd.DataFrame:
        query = """
            SELECT 
                strftime('%Y-%m', data_pagamento) as month, 
                SUM(valor_liquido) as amount_received,
                SUM(CASE WHEN tipo_evento = 'DIVIDENDO' THEN valor_liquido ELSE 0 END) as amount_dividend,
                SUM(CASE WHEN tipo_evento = 'JCP' THEN valor_liquido ELSE 0 END) as amount_jcp,
                SUM(CASE WHEN tipo_evento = 'RENDIMENTO' THEN valor_liquido ELSE 0 END) as amount_rendimento
            FROM dividends 
            GROUP BY strftime('%Y-%m', data_pagamento)
            ORDER BY month ASC
        """
        with self._get_connection() as conn:
            import pandas as pd
            return pd.read_sql(query, conn)

    def get_daily_expenses(self, month: str):
        query = "SELECT data, SUM(valor) as total FROM transactions WHERE natureza = 'EXPENSE' AND data LIKE ? GROUP BY data ORDER BY data ASC"
        with self._get_connection() as conn:
            import pandas as pd
            return pd.read_sql_query(query, conn, params=(f"{month}-%",))

    def get_portfolio_evolution_summary(self) -> dict:
        query = """
            SELECT 
                patrimonio_cents, 
                rentabilidade_acumulada_pct,
                proventos_cents,
                compras_cents,
                vendas_cents,
                ibov_acumulado_pct,
                cdi_acumulado_pct
            FROM portfolio_evolution 
            ORDER BY reference_month DESC 
            LIMIT 1
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            if not row:
                return {
                    "patrimonio_atual": 0.0,
                    "rentabilidade_acumulada": 0.0,
                    "proventos_totais": 0.0,
                    "compras_totais": 0.0,
                    "vendas_totais": 0.0,
                    "ibov_acumulado_pct": 0.0,
                    "cdi_acumulado_pct": 0.0
                }
            return {
                "patrimonio_atual": float(row["patrimonio_cents"]) / 100.0,
                "rentabilidade_acumulada": float(row["rentabilidade_acumulada_pct"]),
                "proventos_totais": float(row["proventos_cents"]) / 100.0,
                "compras_totais": float(row["compras_cents"]) / 100.0,
                "vendas_totais": float(row["vendas_cents"]) / 100.0,
                "ibov_acumulado_pct": float(row["ibov_acumulado_pct"]),
                "cdi_acumulado_pct": float(row["cdi_acumulado_pct"])
            }

    def get_dividends_by_asset(self):
        query = "SELECT ticker, SUM(valor_liquido) as total_recebido, COUNT(id_economico) as quantidade_eventos, MIN(data_pagamento) as primeiro_recebimento, MAX(data_pagamento) as ultimo_recebimento FROM dividends GROUP BY ticker ORDER BY total_recebido DESC"
        with self._get_connection() as conn:
            import pandas as pd
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                df['total_recebido_value'] = df['total_recebido']
            return df

    def get_asset_position(self, ticker: str) -> dict:
        query = "SELECT * FROM positions WHERE ticker = ? AND data_snapshot = (SELECT MAX(data_snapshot) FROM positions)"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (ticker,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Posição não encontrada para {ticker}")
            return dict(row)
