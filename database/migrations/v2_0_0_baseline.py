import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'fin_analytics_v2.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'schema_v2.sql')

def upgrade():
    print("Running V2 Baseline Upgrade...")
    
    # In V2, we enforce PRAGMA foreign_keys = ON at connection level
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Execute the new schema definitions
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print("V2 Baseline schema created successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error executing V2 schema: {e}")
        raise
    finally:
        conn.close()

def downgrade():
    print("Running V2 Baseline Downgrade (Drop All Tables)...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF") # Turn off for dropping
    
    tables_to_drop = [
        "transactions", "positions", "dividends", "portfolio_evolution",
        "staging_imports", "staging_positions", "staging_dividends", "staging_portfolio_evolution",
        "event_links", "raw_events", "import_artifacts", "import_runs",
        "subscriptions", "goals", "categories", "users",
        "benchmarks", "ai_runs", "prompt_versions", "rules", "audit_log"
    ]
    
    try:
        for table in tables_to_drop:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
        print("V2 Baseline tables dropped successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error dropping V2 tables: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade()
