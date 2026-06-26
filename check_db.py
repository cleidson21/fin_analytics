import sqlite3
import json

conn = sqlite3.connect('database/fin_analytics_v3.db')
cur = conn.cursor()

def get_items(item_type):
    return [row[0] for row in cur.execute(f"SELECT name FROM sqlite_master WHERE type='{item_type}'")]

output = {
    'tables': get_items('table'),
    'views': get_items('view'),
    'indices': get_items('index'),
    'triggers': get_items('trigger')
}

print(json.dumps(output, indent=2))
