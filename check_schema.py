import sqlite3

conn = sqlite3.connect('database/fin_analytics_v3.db')
cursor = conn.cursor()

tables = ['asset_valuations', 'portfolio_snapshots', 'dividends']
for table in tables:
    print(f'--- Schema for {table} ---')
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
    result = cursor.fetchone()
    if result:
        print(result[0])
    else:
        print(f'Table {table} not found!')
    print()
