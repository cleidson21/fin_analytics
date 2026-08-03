import sqlite3
import json
conn = sqlite3.connect('fin_analytics_v3.db')
row = conn.execute("SELECT extra_json FROM transactions LIMIT 1;").fetchone()
if row and row[0]:
    data = json.loads(row[0])
    print("Extra keys:", data.keys())
    print("Has confidence?", 'tr_confidence' in data)
