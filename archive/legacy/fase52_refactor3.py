import sqlite3

def append_to_gov():
    code = """
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
"""
    with open('database/governance_repository.py', 'a', encoding='utf-8') as f:
        f.write(code)

    with open('app/api/routes/governance.py', 'r', encoding='utf-8') as f:
        gov_py = f.read()

    target_241 = '''        with gov_repo._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            artifact = conn.execute("SELECT raw_content FROM import_artifacts WHERE import_run_id = ?", (run_id,)).fetchone()
            if not artifact:
                raise HTTPException(status_code=404, detail="Artifact não encontrado")
            raw_content = artifact['raw_content']'''
    replacement_241 = '''        raw_content = gov_repo.get_import_artifact_content(run_id)
        if not raw_content:
            raise HTTPException(status_code=404, detail="Artifact não encontrado")'''
    gov_py = gov_py.replace(target_241, replacement_241)

    target_522 = '''        with gov_repo._get_connection() as conn:
            conn.execute("UPDATE import_runs SET pipeline_version = 'etl_v2' WHERE id = ?", (run_id,))
            conn.commit()'''
    replacement_522 = '''        gov_repo.update_import_pipeline_version(run_id, 'etl_v2')'''
    gov_py = gov_py.replace(target_522, replacement_522)

    target_541 = '''        with gov_repo._get_connection() as conn:
            existing_links_rows = conn.execute("SELECT event_id_a, event_id_b FROM event_links").fetchall()
            existing_links = set([(r[0], r[1]) for r in existing_links_rows])'''
    replacement_541 = '''        existing_links_rows = gov_repo.get_all_event_links()
        existing_links = set(existing_links_rows)'''
    gov_py = gov_py.replace(target_541, replacement_541)

    with open('app/api/routes/governance.py', 'w', encoding='utf-8') as f:
        f.write(gov_py)

append_to_gov()
