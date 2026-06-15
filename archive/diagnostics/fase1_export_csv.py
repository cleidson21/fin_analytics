"""
FASE 1 - Exportacao Total dos Dados para CSV
Cria /exports/rebuild/ e exporta todas as tabelas com hash e manifest.
"""
import sqlite3
import csv
import hashlib
import json
import os
import sys
from datetime import datetime

# Fix stdout encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = os.path.join("database", "fin_analytics.db")
EXPORT_DIR = os.path.join("exports", "rebuild")
os.makedirs(EXPORT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

TABLES_TO_EXPORT = [
    # Financeiro core
    "transactions",
    "positions",
    "dividends",
    "portfolio_evolution",
    "import_runs",
    "import_artifacts",
    # Staging
    "staging_imports",
    "staging_positions",
    "staging_dividends",
    "staging_portfolio_evolution",
    # ETL v2
    "raw_events",
    "event_links",
    "reconciliation_hints",
    # Governança
    "rules",
    "audit_log",
    "prompt_versions",
    "ai_runs",
    # Auth + Cache
    "users",
    "market_cache",
    "etl_runs_legacy",
]

manifest = {
    "generated_at": datetime.now().isoformat(),
    "database": DB_PATH,
    "export_dir": EXPORT_DIR,
    "tables": []
}

for tname in TABLES_TO_EXPORT:
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM [{tname}]")
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description] if cursor.description else []

        csv_path = os.path.join(EXPORT_DIR, f"{tname}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            for row in rows:
                writer.writerow(list(row))

        # Hash SHA-256
        sha256 = hashlib.sha256()
        with open(csv_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        file_hash = sha256.hexdigest()
        file_size = os.path.getsize(csv_path)

        entry = {
            "table": tname,
            "rows": len(rows),
            "columns": cols,
            "file": f"{tname}.csv",
            "sha256": file_hash,
            "size_bytes": file_size,
            "status": "OK"
        }
        manifest["tables"].append(entry)
        print(f"[OK] {tname}: {len(rows)} rows -> {tname}.csv (sha256: {file_hash[:16]}...)")

    except Exception as e:
        entry = {
            "table": tname,
            "rows": 0,
            "columns": [],
            "file": f"{tname}.csv",
            "sha256": None,
            "size_bytes": 0,
            "status": f"ERROR: {e}"
        }
        manifest["tables"].append(entry)
        print(f"[ERROR] {tname}: {str(e).encode('ascii', errors='replace').decode()}")

conn.close()

manifest_path = os.path.join(EXPORT_DIR, "export_manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"\n[DONE] Manifest salvo em: {manifest_path}")
print(f"Total tables: {len(manifest['tables'])}")
print(f"Total rows: {sum(t['rows'] for t in manifest['tables'])}")
