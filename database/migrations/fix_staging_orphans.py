import sqlite3

def fix_remaining():
    conn = sqlite3.connect('database/fin_analytics.db')
    tables = ['staging_positions', 'import_artifacts', 'staging_portfolio_evolution', 'staging_dividends']
    for tbl in tables:
        # Check if table exists
        exists = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl}'").fetchone()
        if not exists:
            continue
            
        sql = f"""
            UPDATE {tbl} 
            SET import_run_id = 'legacy-orphaned-imports' 
            WHERE import_run_id IS NOT NULL 
              AND import_run_id NOT IN (SELECT id FROM import_runs)
        """
        cursor = conn.execute(sql)
        print(f"Updated {cursor.rowcount} orphans in {tbl}")
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON;")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    print("Violacoes de FK apos fix:", violations)
    conn.close()

if __name__ == "__main__":
    fix_remaining()
