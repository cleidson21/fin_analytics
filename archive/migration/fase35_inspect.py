import sqlite3

conn = sqlite3.connect('database/fin_analytics.db')
tables = ['transactions', 'positions', 'dividends', 'portfolio_evolution']
for tbl in tables:
    row = conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{tbl}'").fetchone()
    if row:
        print(f'=== TABLE {tbl} ===')
        print(row[0])
    
    indexes = conn.execute(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{tbl}' AND sql IS NOT NULL").fetchall()
    print(f'=== INDEXES {tbl} ===')
    for idx in indexes:
        print(idx[0])

print('=== VIEW ===')
vw = conn.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name='vw_rules_training_dataset'").fetchone()
if vw: print(vw[0])
