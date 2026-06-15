import sqlite3
import os

def audit_db(db_path):
    if not os.path.exists(db_path):
        print(f"Skipping {db_path}, not found.")
        return
    print(f'Auditing {db_path}')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for t in tables:
        tname = t[0]
        try:
            count = cursor.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
            if count == 0:
                print(f'  [EMPTY TABLE] {tname}')
        except:
            pass
    views = cursor.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall()
    for v in views:
        print(f'  [VIEW] {v[0]}')

audit_db('database/fin_analytics.db')
audit_db('database/governance.db')
