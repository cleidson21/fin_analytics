import sqlite3
conn = sqlite3.connect('database/fin_analytics.db')
for row in conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='accounts';"):
    print(row[0])
