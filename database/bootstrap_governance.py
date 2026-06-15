import sqlite3
from pathlib import Path
from database.config import GOVERNANCE_DB_PATH, BASE_DIR

def init_governance_db():
    schema_path = BASE_DIR / "database" / "governance_schema.sql"
    
    # We create and apply schema regardless if the file existed, because IF NOT EXISTS handles it safely.
    with sqlite3.connect(GOVERNANCE_DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as file_handle:
                conn.executescript(file_handle.read())
        conn.commit()

if __name__ == "__main__":
    init_governance_db()
