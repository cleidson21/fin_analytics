import os

financial_service = """from database.financial_repository import FinancialRepository

class FinancialService:
    def __init__(self):
        self.repo = FinancialRepository()

    def get_transactions(self, *args, **kwargs):
        pass # To be implemented if we refactor transactions.py completely

    def get_dashboard_metrics(self, *args, **kwargs):
        return self.repo.get_dashboard_metrics(*args, **kwargs)

    def merge_categories(self, *args, **kwargs):
        return self.repo.merge_categories(*args, **kwargs)
"""

governance_service = """from database.governance_repository import GovernanceRepository

class GovernanceService:
    def __init__(self):
        self.repo = GovernanceRepository()

    def get_active_rules(self, *args, **kwargs):
        return self.repo.get_active_rules(*args, **kwargs)

    def get_learning_metrics(self, *args, **kwargs):
        return self.repo.get_learning_metrics(*args, **kwargs)
        
    def get_all_prompts(self, *args, **kwargs):
        return self.repo.get_all_prompts(*args, **kwargs)
"""

import_service = """from database.governance_repository import GovernanceRepository
from database.financial_repository import FinancialRepository

class ImportService:
    def __init__(self):
        self.gov_repo = GovernanceRepository()
        self.fin_repo = FinancialRepository()

    def rollback_import_run(self, run_id: str):
        self.fin_repo.rollback_financial_data(run_id)
        self.gov_repo.rollback_governance_data(run_id)
"""

os.makedirs('app/api/services', exist_ok=True)
with open('app/api/services/financial_service.py', 'w', encoding='utf-8') as f:
    f.write(financial_service)
with open('app/api/services/governance_service.py', 'w', encoding='utf-8') as f:
    f.write(governance_service)
with open('app/api/services/import_service.py', 'w', encoding='utf-8') as f:
    f.write(import_service)
