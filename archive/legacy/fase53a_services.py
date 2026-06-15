import os

fin_service = """from database.financial_repository import FinancialRepository

class FinancialService:
    def __init__(self):
        self.repo = FinancialRepository()

    def get_database_path(self):
        return self.repo.db_path

    def vacuum_database(self):
        return self.repo.vacuum_database()

    def analyze_database(self):
        return self.repo.analyze_database()

    def get_admin_metrics(self):
        summary = {}
        with self.repo._get_connection() as conn:
            cursor = conn.cursor()
            summary['total_transactions'] = cursor.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
            summary['total_positions'] = cursor.execute('SELECT COUNT(*) FROM positions').fetchone()[0]
            summary['total_dividends'] = cursor.execute('SELECT COUNT(*) FROM dividends').fetchone()[0]
            summary['total_evolutions'] = cursor.execute('SELECT COUNT(*) FROM portfolio_evolution').fetchone()[0]
        return summary

    def get_table_counts(self):
        fin_tables = ['transactions', 'positions', 'dividends', 'portfolio_evolution']
        results = []
        with self.repo._get_connection() as conn:
            cursor = conn.cursor()
            for t in fin_tables:
                try:
                    count = cursor.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
                    results.append({'table_name': t, 'row_count': count, 'status': 'OK' if count < 1000000 else 'WARNING'})
                except:
                    results.append({'table_name': t, 'row_count': 0, 'status': 'ERROR'})
        return results

    def get_integrity_metrics(self):
        integrity = {}
        with self.repo._get_connection() as conn:
            cursor = conn.cursor()
            run_ids = cursor.execute('SELECT DISTINCT import_run_id FROM transactions WHERE import_run_id IS NOT NULL').fetchall()
            integrity['fin_run_ids'] = set([r[0] for r in run_ids])
            integrity['duplicate_transactions_suspects'] = cursor.execute('SELECT COUNT(*) FROM (SELECT data, descricao_original, valor_cents, COUNT(*) as c FROM transactions GROUP BY data, descricao_original, valor_cents HAVING c > 1)').fetchone()[0]
        return integrity
"""

gov_service = """from database.governance_repository import GovernanceRepository

class GovernanceService:
    def __init__(self):
        self.repo = GovernanceRepository()

    def get_learning_metrics(self):
        return self.repo.get_learning_metrics()

    def get_top_rules(self, limit: int):
        return self.repo.get_top_rules(limit=limit)

    def get_problematic_rules(self, limit: int):
        return self.repo.get_problematic_rules(limit=limit)

    def get_rules_audit(self, limit: int, offset: int, status: str = None):
        return self.repo.get_rules_audit(limit=limit, offset=offset, status=status)

    def get_prompt_version_exists(self, name: str, version: int):
        return self.repo.get_prompt_version_exists(name, version)

    def insert_prompt_version(self, id: str, name: str, version: int, content: str, active: int, notes: str):
        return self.repo.insert_prompt_version(id, name, version, content, active, notes)

    def get_all_prompts(self, active_only: bool = False):
        return self.repo.get_all_prompts(active_only)

    def get_prompt_by_id(self, prompt_id: str):
        return self.repo.get_prompt_by_id(prompt_id)

    def activate_prompt_version(self, prompt_id: str):
        return self.repo.activate_prompt_version(prompt_id)

    def get_audit_runs(self, status_filter: str = "ALL"):
        return self.repo.get_audit_runs(status_filter)

    def get_audit_rollbacks(self):
        return self.repo.get_audit_rollbacks()

    def get_database_path(self):
        return self.repo.db_path

    def vacuum_database(self):
        with self.repo._get_connection() as conn:
            conn.execute("VACUUM")

    def analyze_database(self):
        with self.repo._get_connection() as conn:
            conn.execute("ANALYZE")

    def get_admin_metrics(self):
        summary = {}
        with self.repo._get_connection() as conn:
            cursor = conn.cursor()
            summary['total_import_runs'] = cursor.execute('SELECT COUNT(*) FROM import_runs').fetchone()[0]
            summary['runs_confirmed'] = cursor.execute("SELECT COUNT(*) FROM import_runs WHERE status = 'CONFIRMED'").fetchone()[0]
            summary['runs_pending'] = cursor.execute("SELECT COUNT(*) FROM import_runs WHERE status IN ('PENDING', 'AWAITING_CONFIRMATION')").fetchone()[0]
        return summary

    def get_table_counts(self):
        gov_tables = ['import_runs', 'staging_imports', 'staging_positions', 'staging_dividends', 'staging_portfolio_evolution', 'governance_rules', 'governance_prompt_versions']
        results = []
        with self.repo._get_connection() as conn:
            cursor = conn.cursor()
            for t in gov_tables:
                try:
                    count = cursor.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
                    results.append({'table_name': t, 'row_count': count, 'status': 'OK' if count < 1000000 else 'WARNING'})
                except:
                    results.append({'table_name': t, 'row_count': 0, 'status': 'ERROR'})
        return results

    def get_integrity_metrics(self):
        integrity = {}
        with self.repo._get_connection() as conn:
            cursor = conn.cursor()
            integrity['pending_staging'] = cursor.execute("SELECT COUNT(*) FROM staging_imports WHERE status = 'PENDING'").fetchone()[0]
            integrity['gov_run_ids'] = set([r[0] for r in cursor.execute('SELECT id FROM import_runs').fetchall()])
        return integrity
"""

import_service = """from database.financial_repository import FinancialRepository
from database.governance_repository import GovernanceRepository

class ImportService:
    def __init__(self):
        self.fin_repo = FinancialRepository()
        self.gov_repo = GovernanceRepository()

    def rollback_import_run(self, run_id: str):
        self.fin_repo.rollback_financial_data(run_id)
        self.gov_repo.rollback_governance_data(run_id)

    # We will pass through all governance.py methods related to imports that need dual access
    # but to avoid over-engineering we just export both repos for governance methods that don't need dual
    # Actually, governance.py uses a ton of gov_repo methods. We can just expose them.
    def get_import_runs(self, *args, **kwargs): return self.gov_repo.get_import_runs(*args, **kwargs)
    def get_import_run_by_id(self, *args, **kwargs): return self.gov_repo.get_import_run_by_id(*args, **kwargs)
    def get_import_status(self, *args, **kwargs): return self.gov_repo.get_import_status(*args, **kwargs)
    def update_import_run_status(self, *args, **kwargs): return self.gov_repo.update_import_run_status(*args, **kwargs)
    def update_import_run_metrics(self, *args, **kwargs): return self.gov_repo.update_import_run_metrics(*args, **kwargs)
    def lock_import_run_for_confirmation(self, *args, **kwargs): return self.gov_repo.lock_import_run_for_confirmation(*args, **kwargs)
    def mark_staging_conflicts(self, *args, **kwargs): return self.gov_repo.mark_staging_conflicts(*args, **kwargs)
    def process_staging_to_transactions(self, *args, **kwargs): return self.gov_repo.process_staging_to_transactions(*args, **kwargs)
    def get_active_hints(self, *args, **kwargs): return self.gov_repo.get_active_hints(*args, **kwargs)
    def create_event_links(self, *args, **kwargs): return self.gov_repo.create_event_links(*args, **kwargs)
    def promote_all_wealth_staging(self, *args, **kwargs): return self.gov_repo.promote_all_wealth_staging(*args, **kwargs)
    def promote_raw_events(self, *args, **kwargs): return self.gov_repo.promote_raw_events(*args, **kwargs)
    def get_orphans_count(self, *args, **kwargs): return self.gov_repo.get_orphans_count(*args, **kwargs)
    def update_event_link_status(self, *args, **kwargs): return self.gov_repo.update_event_link_status(*args, **kwargs)
    def get_run_ids_for_link(self, *args, **kwargs): return self.gov_repo.get_run_ids_for_link(*args, **kwargs)
    def get_wealth_staging_items(self, *args, **kwargs): return self.gov_repo.get_wealth_staging_items(*args, **kwargs)
    def get_audit_logs(self, *args, **kwargs): return self.gov_repo.get_audit_logs(*args, **kwargs)
    def get_audit_log_by_id(self, *args, **kwargs): return self.gov_repo.get_audit_log_by_id(*args, **kwargs)
    def get_reconciliation_inbox(self, *args, **kwargs): return self.gov_repo.get_reconciliation_inbox(*args, **kwargs)
    def insert_raw_events(self, *args, **kwargs): return self.gov_repo.insert_raw_events(*args, **kwargs)
    def insert_staging_items(self, *args, **kwargs): return self.gov_repo.insert_staging_items(*args, **kwargs)
    def insert_wealth_staging_items(self, *args, **kwargs): return self.gov_repo.insert_wealth_staging_items(*args, **kwargs)
    def create_import_run(self, *args, **kwargs): return self.gov_repo.create_import_run(*args, **kwargs)
    def create_import_artifact(self, *args, **kwargs): return self.gov_repo.create_import_artifact(*args, **kwargs)
    def get_import_artifact_content(self, *args, **kwargs): return self.gov_repo.get_import_artifact_content(*args, **kwargs)
    def update_import_pipeline_version(self, *args, **kwargs): return self.gov_repo.update_import_pipeline_version(*args, **kwargs)
    def get_all_event_links(self, *args, **kwargs): return self.gov_repo.get_all_event_links(*args, **kwargs)

    # Finance methods used by governance.py promotion
    def get_admin_categories(self, *args, **kwargs): return self.fin_repo.get_admin_categories(*args, **kwargs)
    def get_admin_positions(self, *args, **kwargs): return self.fin_repo.get_admin_positions(*args, **kwargs)
    def get_quarantine_transactions(self, *args, **kwargs): return self.fin_repo.get_quarantine_transactions(*args, **kwargs)
    def get_admin_dividends(self, *args, **kwargs): return self.fin_repo.get_admin_dividends(*args, **kwargs)
    def update_transaction(self, *args, **kwargs): return self.fin_repo.update_transaction(*args, **kwargs)
    def update_position(self, *args, **kwargs): return self.fin_repo.update_position(*args, **kwargs)
    def update_dividend(self, *args, **kwargs): return self.fin_repo.update_dividend(*args, **kwargs)
    def merge_categories(self, *args, **kwargs): return self.fin_repo.merge_categories(*args, **kwargs)
"""

os.makedirs('app/api/services', exist_ok=True)
with open('app/api/services/financial_service.py', 'w', encoding='utf-8') as f: f.write(fin_service)
with open('app/api/services/governance_service.py', 'w', encoding='utf-8') as f: f.write(gov_service)
with open('app/api/services/import_service.py', 'w', encoding='utf-8') as f: f.write(import_service)
