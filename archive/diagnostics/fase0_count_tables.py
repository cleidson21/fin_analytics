import sqlite3
import os

db_path = os.path.join("database", "fin_analytics.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for t in tables:
    tname = t[0]
    try:
        count = cursor.execute(f"SELECT COUNT(*) FROM [{tname}]").fetchone()[0]
        print(f"{tname}: {count} rows")
    except Exception as e:
        print(f"{tname}: ERROR - {e}")

conn.close()
