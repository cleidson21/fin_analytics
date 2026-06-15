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

    # Phase 6 expansions
    def get_transactions(self, *args, **kwargs):
        return self.repo.get_transactions(*args, **kwargs)

    def get_transactions_summary(self, *args, **kwargs):
        return self.repo.get_transactions_summary(*args, **kwargs)

    def get_transactions_total_pages(self, *args, **kwargs):
        return self.repo.get_transactions_total_pages(*args, **kwargs)

    def update_transaction_category(self, *args, **kwargs):
        return self.repo.update_transaction_category(*args, **kwargs)

    def get_accounts_summary(self, *args, **kwargs):
        return self.repo.get_accounts_summary(*args, **kwargs)

    def get_account_catalog(self, *args, **kwargs):
        return self.repo.get_account_catalog(*args, **kwargs)

    def get_cashflow_summary(self, *args, **kwargs):
        return self.repo.get_cashflow_summary(*args, **kwargs)

    def get_expenses_by_category(self, *args, **kwargs):
        return self.repo.get_expenses_by_category(*args, **kwargs)

    def get_current_net_worth(self, *args, **kwargs):
        return self.repo.get_current_net_worth(*args, **kwargs)
"""

auth_service = """from database.financial_repository import FinancialRepository

class AuthService:
    def __init__(self):
        self.repo = FinancialRepository()

    def get_user_by_username(self, username: str):
        return self.repo.get_user_by_username(username)

    def create_user(self, username: str, email: str, password_hash: str, role: str = 'VIEWER'):
        return self.repo.create_user(username, email, password_hash, role)
"""

os.makedirs('app/api/services', exist_ok=True)
with open('app/api/services/financial_service.py', 'w', encoding='utf-8') as f:
    f.write(fin_service)
with open('app/api/services/auth_service.py', 'w', encoding='utf-8') as f:
    f.write(auth_service)
