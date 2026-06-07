import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.config import DATABASE_PATH

conn = sqlite3.connect(DATABASE_PATH)
c = conn.cursor()

print(f"DATABASE PATH: {DATABASE_PATH}")

tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"Tables: {len(tables)}")

indices = c.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
print(f"Indices: {len(indices)}")

fks = c.execute("PRAGMA foreign_key_check").fetchall()
print(f"Foreign Key Violations: {len(fks)}")

expected_tables = ["transactions", "positions", "dividends", "import_runs", "import_artifacts", "users", "audit_log", "prompt_versions", "ai_runs"]
for t in expected_tables:
    try:
        count = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"Count {t}: {count}")
    except sqlite3.OperationalError:
        print(f"Count {t}: MISSING TABLE")

conn.close()
