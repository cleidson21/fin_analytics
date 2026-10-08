"""
FinAnalytics — Database Bootstrap
=====================================
Legacy-only bootstrap for the historical Pierre/Core SQL migrations 001-012.
It is not the current application-schema bootstrap, is never called by runtime
startup, and must not create Alembic-managed tables. Current schema evolution
is an explicit ``alembic upgrade head`` operation.

Migration history:
    001 — Core Identity (users, institutions, accounts)
    002 — Cashflow Ledger (transactions, transfers, categories, merchants)
    003 — Credit Card (invoices, installment_plans, installments, invoice_items)
    004 — Investments (assets, trades, broker_notes, corporate_actions, dividends)
    005 — Market Data (asset_prices, benchmark_prices, benchmarks)
    006 — Governance (import_runs, import_artifacts, audit_logs, data_corrections)
    007 — AI Classification (classification_rules, learning_examples, ai_prompts, ai_runs, classification_feedback)
    008 — Analytics (asset_positions, asset_valuations, portfolio_snapshots, benchmark_snapshots, cashflow_summaries)
    --- FREEZE PREPARATION ---
    009 — Fixed Income Events (fixed_income_events)
    010 — Ledger Events (transaction_events)
    011 — AI Prompt Versioning (ai_prompt_versions + ALTER ai_runs)
    012 — Freeze Fixes (fixed_income_events CORRECTION, benchmark_prices REAL, installments CANCELLED, installment_plans status)

Legacy usage:
    python database/create_db.py [--db-path PATH]

Default DB path: database/fin_analytics.db
"""

import sqlite3
import os
import sys
import argparse
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
DEFAULT_DB_PATH = Path(__file__).parent / "fin_analytics.db"

MIGRATION_ORDER = [
    # --- Core domain ---
    "001_core_identity.sql",
    "002_cashflow_ledger.sql",
    "003_credit_card.sql",
    "004_investments.sql",
    "005_market_data.sql",
    "006_governance.sql",
    "007_ai_classification.sql",
    "008_analytics.sql",
    # --- Freeze preparation (schema certification) ---
    "009_fixed_income_events.sql",
    "010_ledger_events.sql",
    "011_ai_prompt_versioning.sql",
    "012_freeze_fixes.sql",
    # --- Plataforma de Investimentos (Sprint 2) ---
    # NOTA (Lote 10.0-A): 013_position_snapshots.sql define um schema com snapshot_hash
    # (B3 Área do Investidor) que foi SUPERSEDIDO pelo Alembic (wealth_phase1 / a1b2c3d4e5f6)
    # antes de ser executado em produção.
    # O banco atual usa o schema Alembic: id + account_id + asset_id + reference_date (MYPROFIT_ATIVOS).
    # O CREATE TABLE IF NOT EXISTS da 013 não causou dano porque a tabela já existia.
    # Em ambientes fresh (novo DB), o create_db.py NÃO deve ser usado para tabelas de Investments.
    # O Alembic (alembic upgrade head) é o único sistema de migration autorizado para Investments.
    # Este arquivo (create_db.py) só é relevante para as migrations 001–012 (domínio Pierre/Core).
    # "013_position_snapshots.sql",  # SUPERSEDIDO — não executar em novos ambientes

]


def run_migrations(db_path: str) -> None:
    print(f"[DB] Connecting to: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    # Migrations tracking table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _schema_migrations (
            filename    TEXT PRIMARY KEY,
            applied_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
    """)
    conn.commit()

    applied = {row[0] for row in conn.execute("SELECT filename FROM _schema_migrations")}

    for filename in MIGRATION_ORDER:
        if filename in applied:
            print(f"  [SKIP] {filename} — already applied")
            continue

        migration_path = MIGRATIONS_DIR / filename
        if not migration_path.exists():
            print(f"  [ERROR] Migration file not found: {migration_path}", file=sys.stderr)
            sys.exit(1)

        print(f"  [RUN]  {filename}")
        sql = migration_path.read_text(encoding="utf-8")

        try:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO _schema_migrations (filename) VALUES (?)", (filename,)
            )
            conn.commit()
            print(f"  [OK]   {filename}")
        except sqlite3.Error as e:
            conn.rollback()
            print(f"  [FAIL] {filename}: {e}", file=sys.stderr)
            sys.exit(1)

    conn.close()
    print(f"\n[DB] All migrations applied. Database ready at: {db_path}")


def verify_schema(db_path: str) -> None:
    """Print table list and row counts for quick sanity check."""
    conn = sqlite3.connect(db_path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_schema%' ORDER BY name"
    ).fetchall()

    print(f"\n[VERIFY] Tables in {db_path}:")
    for (name,) in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"  {name:<35} {count:>6} rows")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinAnalytics — Database Bootstrap")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Path to SQLite database file")
    parser.add_argument("--verify", action="store_true", help="Show table counts after migration")
    args = parser.parse_args()

    run_migrations(args.db_path)

    if args.verify:
        verify_schema(args.db_path)
