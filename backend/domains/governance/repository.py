from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any

class ImportRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_import_runs(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        query = text("""
            SELECT 
                id, 
                source as source_type, 
                filename as file_name, 
                started_at, 
                status, 
                rows_parsed as rows_read, 
                rows_inserted, 
                rows_errored as rows_failed
            FROM import_runs 
            ORDER BY started_at DESC 
            LIMIT :limit OFFSET :offset
        """)
        rows = self.session.execute(query, {"limit": limit, "offset": offset}).mappings().all()
        return [dict(r) for r in rows]

    def count_import_runs(self) -> int:
        return self.session.execute(text("SELECT COUNT(*) FROM import_runs")).scalar() or 0

    def get_import_run(self, run_id: str) -> Dict[str, Any]:
        query = text("SELECT id, user_id, source, status, filename, file_hash, rows_parsed, rows_inserted, rows_skipped, rows_errored, error_message, started_at, finished_at FROM import_runs WHERE id = :id")
        row = self.session.execute(query, {"id": run_id}).mappings().first()
        return dict(row) if row else None

    def get_staging_items(self, run_id: str) -> List[Dict[str, Any]]:
        query = text("SELECT row_number, raw_data, status, error_msg FROM import_artifacts WHERE run_id = :id ORDER BY row_number LIMIT 200")
        rows = self.session.execute(query, {"id": run_id}).mappings().all()
        return [dict(r) for r in rows]

    def rollback_import(self, run_id: str):
        self.session.execute(text("DELETE FROM import_artifacts WHERE run_id = :id"), {"id": run_id})
        self.session.execute(text("DELETE FROM dividends WHERE run_id = :id"), {"id": run_id})
        self.session.execute(text("DELETE FROM transactions WHERE run_id = :id"), {"id": run_id})
        self.session.execute(text("DELETE FROM position_snapshots WHERE run_id = :id"), {"id": run_id})
        self.session.execute(text("DELETE FROM portfolio_snapshots WHERE run_id = :id"), {"id": run_id})
        self.session.execute(text("UPDATE import_runs SET status = 'ROLLED_BACK', error_message = 'Rolled back by user' WHERE id = :id"), {"id": run_id})
        self.session.commit()

class DashboardRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_import_metrics(self) -> Dict[str, Any]:
        metrics = self.session.execute(text("""
            SELECT 
                COUNT(*) as total_runs,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as confirmed_runs,
                SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending_runs,
                SUM(rows_inserted) as lines_inserted,
                0 as lines_updated,
                SUM(rows_errored) as lines_failed,
                MAX(started_at) as last_import
            FROM import_runs
        """)).mappings().first()
        
        return dict(metrics) if metrics else {
            "total_runs": 0, "confirmed_runs": 0, "pending_runs": 0,
            "lines_inserted": 0, "lines_updated": 0, "lines_failed": 0, "last_import": None
        }
