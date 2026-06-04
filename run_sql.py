import sqlite3
conn = sqlite3.connect('fin_analytics.db')
cur = conn.cursor()
cur.execute("SELECT strftime('%Y-%m', data), COUNT(*) FROM transactions GROUP BY 1 ORDER BY 1 DESC;")
print('\n'.join(str(row) for row in cur.fetchall()))
