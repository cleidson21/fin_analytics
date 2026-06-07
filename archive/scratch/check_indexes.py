import sqlite3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.config import DATABASE_PATH

conn = sqlite3.connect(DATABASE_PATH)
indexes = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()]
print('INDEXES:', indexes)
conn.close()
