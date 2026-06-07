import sys, shutil, sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from database.config import DATABASE_PATH as db
bak = Path("fin_analytics.db.bak_sprint_0_5_1")

if not db.exists():
    print("ERRO: banco nao encontrado")
    exit(1)

shutil.copy2(db, bak)
print(f"Backup criado: {bak}  ({bak.stat().st_size} bytes)")

conn = sqlite3.connect(db)
tables = sorted(r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
print("Tabelas atuais:", tables)
conn.close()
