import sqlite3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.config import DATABASE_PATH

conn = sqlite3.connect(DATABASE_PATH)
indexes = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name IN ('idx_positions_lookup', 'idx_dividends_lookup', 'idx_transactions_macro')").fetchall()
for n, s in indexes: print(f'{n}: {s}')
conn.close()
