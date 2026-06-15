from database.financial_repository import FinancialRepository
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
