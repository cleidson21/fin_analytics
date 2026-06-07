import sys, sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from database.config import DATABASE_PATH as db
sql = Path("database/migrations/sprint_0_5_1_up.sql").read_text(encoding="utf-8")

conn = sqlite3.connect(db)
try:
    conn.executescript(sql)
    tables = sorted(r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
    print("Tabelas apos UP:", tables)

    cols = [r[1] for r in conn.execute("PRAGMA table_info(import_runs)").fetchall()]
    print("Colunas import_runs:", cols)

    count = conn.execute("SELECT COUNT(*) FROM import_runs").fetchone()[0]
    print(f"Registros em import_runs: {count}")

    count_art = conn.execute("SELECT COUNT(*) FROM import_artifacts").fetchone()[0]
    print(f"Registros em import_artifacts: {count_art}")

    etl_ok = conn.execute("SELECT name FROM sqlite_master WHERE name='etl_runs_legacy'").fetchone()
    print("etl_runs_legacy existe:", etl_ok is not None)

    si_cols = [r[1] for r in conn.execute("PRAGMA table_info(staging_imports)").fetchall()]
    print("Colunas staging_imports:", si_cols)

    pv_cols = [r[1] for r in conn.execute("PRAGMA table_info(prompt_versions)").fetchall()]
    print("Colunas prompt_versions:", pv_cols)

    ai_cols = [r[1] for r in conn.execute("PRAGMA table_info(ai_runs)").fetchall()]
    print("Colunas ai_runs:", ai_cols)

    conn.close()
    print("\nMigration UP aplicada com SUCESSO.")
except Exception as e:
    conn.close()
    print("ERRO:", e)
    raise
