
    def get_import_run(self, run_id: str) -> Dict[str, Any]:
        query = text("SELECT id, user_id, source, status, filename, file_hash, rows_parsed, rows_inserted, rows_skipped, rows_errored, error_message, started_at, finished_at FROM import_runs WHERE id = :id")
        row = self.session.execute(query, {"id": run_id}).mappings().first()
        return dict(row) if row else None

    def get_staging_items(self, run_id: str) -> List[Dict[str, Any]]:
        query = text("SELECT row_number, raw_data, status, error_msg FROM import_artifacts WHERE run_id = :id ORDER BY row_number LIMIT 200")
        rows = self.session.execute(query, {"id": run_id}).mappings().all()
        return [dict(r) for r in rows]

    def rollback_import(self, run_id: str):
        self.session.execute(text("DELETE FROM dividends WHERE run_id = :id"), {"id": run_id})
        self.session.execute(text("DELETE FROM transactions WHERE run_id = :id"), {"id": run_id})
        self.session.execute(text("DELETE FROM position_snapshots WHERE run_id = :id"), {"id": run_id})
        self.session.execute(text("DELETE FROM portfolio_snapshots WHERE run_id = :id"), {"id": run_id})
        self.session.execute(text("UPDATE import_runs SET status = 'FAILED', error_message = 'Rolled back by user' WHERE id = :id"), {"id": run_id})
        self.session.commit()
