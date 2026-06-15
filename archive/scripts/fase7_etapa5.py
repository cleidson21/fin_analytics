import sqlite3

conn = sqlite3.connect('database/fin_analytics.db')

integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
print(f'integrity_check: {integrity}')

fks = conn.execute('PRAGMA foreign_key_check').fetchall()
print(f'foreign_key_check: {fks}')

tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f'tabelas_restantes: {[t[0] for t in tables]}')

views = conn.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall()
print(f'views_restantes: {[v[0] for v in views]}')
