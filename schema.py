import sqlite3
conn = sqlite3.connect('database/fin_analytics_v3.db')
print(conn.execute("SELECT sql FROM sqlite_master WHERE name='import_runs'").fetchone()[0])
print(conn.execute("SELECT sql FROM sqlite_master WHERE name='import_artifacts'").fetchone()[0])
