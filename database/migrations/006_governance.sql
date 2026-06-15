-- ==========================================================================
-- MIGRATION 006 — GOVERNANCE
-- FinAnalytics V3 | Context: Governance & Compliance
-- Tracks every import operation and provides full audit trail.
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- IMPORT RUNS
-- One record per file import attempt.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS import_runs (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id         TEXT NOT NULL REFERENCES users(id),
    source          TEXT NOT NULL CHECK(source IN (
                        'NUBANK_CSV',
                        'NUBANK_OFX',
                        'CREDIT_CARD_CSV',
                        'BROKER_NOTE_PDF',
                        'B3_API',
                        'PIERRE_CSV',
                        'MYPROFIT_ACOES_CSV',
                        'MYPROFIT_PROVENTOS_CSV',
                        'MYPROFIT_EVOLUCAO_CSV',
                        'MARKET_DATA_YFINANCE',
                        'MARKET_DATA_BCB',
                        'MANUAL'
                    )),
    status          TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','PROCESSING','SUCCESS','PARTIAL','FAILED')),
    filename        TEXT,                   -- original filename uploaded
    file_hash       TEXT,                   -- SHA-256 of the file (prevent re-import)
    rows_parsed     INTEGER DEFAULT 0,
    rows_inserted   INTEGER DEFAULT 0,
    rows_skipped    INTEGER DEFAULT 0,
    rows_errored    INTEGER DEFAULT 0,
    error_message   TEXT,
    started_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    finished_at     TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_import_runs_file_hash ON import_runs(file_hash) WHERE file_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_import_runs_user   ON import_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_import_runs_source ON import_runs(source);
CREATE INDEX IF NOT EXISTS idx_import_runs_status ON import_runs(status);

-- --------------------------------------------------------------------------
-- IMPORT ARTIFACTS
-- Raw rows from imported files, stored for debug/re-processing.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS import_artifacts (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    run_id      TEXT NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    row_number  INTEGER NOT NULL,
    raw_data    TEXT NOT NULL,              -- JSON blob of the original row
    status      TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','INSERTED','SKIPPED','ERROR')),
    result_id   TEXT,                       -- the ID of the entity created (transaction_id, trade_id, etc.)
    error_msg   TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_import_artifacts_run ON import_artifacts(run_id);

-- --------------------------------------------------------------------------
-- AUDIT LOGS
-- Immutable trail: who changed what, when, from where.
-- INSERT-only table, never UPDATE or DELETE.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id     TEXT REFERENCES users(id),
    action      TEXT NOT NULL CHECK(action IN (
                    'CREATE','UPDATE','DELETE','IMPORT','CLASSIFY','CORRECT',
                    'TRANSFER_LINK','INVOICE_PAID','POSITION_RECOMPUTED','SNAPSHOT_CREATED'
                )),
    entity_type TEXT NOT NULL,              -- 'transaction', 'trade', 'dividend', etc.
    entity_id   TEXT NOT NULL,
    before_json TEXT,                       -- JSON snapshot of old values
    after_json  TEXT,                       -- JSON snapshot of new values
    ip_address  TEXT,
    user_agent  TEXT,
    run_id      TEXT REFERENCES import_runs(id),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user   ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_date   ON audit_logs(created_at);

-- --------------------------------------------------------------------------
-- DATA CORRECTIONS
-- When a transaction's category/merchant needs correction.
-- Instead of UPDATE, a correction event is recorded.
-- The application reads the latest correction to determine effective state.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_corrections (
    id                  TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id             TEXT NOT NULL REFERENCES users(id),
    entity_type         TEXT NOT NULL,      -- 'transaction', 'invoice_item'
    entity_id           TEXT NOT NULL,
    field_name          TEXT NOT NULL,      -- 'category_id', 'merchant_id', 'is_ignored'
    old_value           TEXT,
    new_value           TEXT,
    reason              TEXT,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_corrections_entity ON data_corrections(entity_type, entity_id);
