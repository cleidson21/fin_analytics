import sqlite3
conn = sqlite3.connect('database/fin_analytics_v3.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])
