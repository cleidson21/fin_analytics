from database.governance_repository import GovernanceRepository

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
            summary['total_import_runs'] = cursor.execute('SELECT COUNT(*) FROM import_runs').fetchone()[0] or 0
            summary['runs_confirmed'] = cursor.execute("SELECT COUNT(*) FROM import_runs WHERE status = 'CONFIRMED'").fetchone()[0] or 0
            summary['runs_pending'] = cursor.execute("SELECT COUNT(*) FROM import_runs WHERE status IN ('PENDING', 'AWAITING_CONFIRMATION')").fetchone()[0] or 0
            summary['lines_inserted'] = cursor.execute('SELECT SUM(rows_inserted) FROM import_runs').fetchone()[0] or 0
            summary['lines_updated'] = cursor.execute('SELECT SUM(rows_updated) FROM import_runs').fetchone()[0] or 0
            summary['lines_failed'] = cursor.execute('SELECT SUM(rows_failed) FROM import_runs').fetchone()[0] or 0
            last_import = cursor.execute("SELECT MAX(finished_at) FROM import_runs WHERE status = 'CONFIRMED'").fetchone()[0]
            summary['last_import'] = str(last_import) if last_import else None
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
