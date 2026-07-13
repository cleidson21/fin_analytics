import sqlite3
import os
import sys

def test_migration():
    db_path = "test_migration.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    
    # Run migrations 001 to 004 to simulate existing DB
    # We will just run 004 as it has what we need for this test, but 004 depends on accounts/assets.
    # So let's create a minimal schema for accounts and transactions
    
    conn.executescript("""
        CREATE TABLE accounts (id TEXT PRIMARY KEY, name TEXT);
        CREATE TABLE transactions (id TEXT PRIMARY KEY);
    """)
    
    with open("database/migrations/004_investments.sql", "r", encoding="utf-8") as f:
        m4 = f.read()
    conn.executescript(m4)
    
    # Insert some data to ensure preservation
    conn.execute("INSERT INTO accounts (id, name) VALUES ('acc1', 'Nubank')")
    # Asset is seeded in 004
    conn.execute("INSERT INTO broker_notes (id, account_id, note_number, note_date) VALUES ('n1', 'acc1', '123', '2024-01-01')")
    
    conn.execute("INSERT INTO trades (id, asset_id, account_id, type, trade_date, quantity, unit_price, source) VALUES ('t1', 'asset-001', 'acc1', 'BUY', '2024-01-01', 10, 1000, 'B3_API')")
    
    conn.commit()
    
    # Now run 005
    with open("database/migrations/005_open_finance.sql", "r", encoding="utf-8") as f:
        m5 = f.read()
        
    try:
        conn.executescript(m5)
    except Exception as e:
        print("Error running 005:", str(e))
        sys.exit(1)
        
    # Verify data preservation
    t = conn.execute("SELECT id, source FROM trades").fetchone()
    if not t or t[0] != 't1' or t[1] != 'B3_API':
        print("Data preservation failed for trades!")
        sys.exit(1)
        
    # Verify new constraint works
    try:
        conn.execute("INSERT INTO trades (id, asset_id, account_id, type, trade_date, quantity, unit_price, source) VALUES ('t2', 'asset-001', 'acc1', 'BUY', '2024-01-02', 10, 1000, 'OPEN_FINANCE')")
        conn.commit()
    except Exception as e:
        print("Constraint OPEN_FINANCE failed:", str(e))
        sys.exit(1)
        
    # Verify invalid source still fails
    try:
        conn.execute("INSERT INTO trades (id, asset_id, account_id, type, trade_date, quantity, unit_price, source) VALUES ('t3', 'asset-001', 'acc1', 'BUY', '2024-01-02', 10, 1000, 'INVALID')")
        print("Invalid constraint DID NOT fail! Danger!")
        sys.exit(1)
    except sqlite3.IntegrityError:
        pass # Expected
        
    # Verify position_snapshots
    try:
        conn.execute("INSERT INTO position_snapshots (id, account_id, asset_id, reference_date, quantity, source_system) VALUES ('snap1', 'acc1', 'asset-001', '2024-01-01', 100, 'OPEN_FINANCE')")
        conn.commit()
    except Exception as e:
        print("Error inserting into position_snapshots:", str(e))
        sys.exit(1)
        
    print("ALL TESTS PASSED!")
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    test_migration()
