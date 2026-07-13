-- ==========================================================================
-- MIGRATION 014 — IMPORT LOGS (GATE 10.2)
-- FinAnalytics V3 | Context: Governance & Compliance
-- Transforms every import attempt into a permanent and auditable event.
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- IMPORT LOGS
-- One record per file import attempt, ensuring nothing is lost.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS import_logs (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL REFERENCES users(id),
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    filename            TEXT NOT NULL,
    file_type           TEXT NOT NULL,
    file_size           INTEGER NOT NULL,
    checksum            TEXT NOT NULL,
    parser              TEXT NOT NULL,
    rows_read           INTEGER DEFAULT 0,
    rows_imported       INTEGER DEFAULT 0,
    rows_duplicated     INTEGER DEFAULT 0,
    rows_failed         INTEGER DEFAULT 0,
    processing_time_ms  INTEGER DEFAULT 0,
    status              TEXT NOT NULL CHECK(status IN ('SUCCESS', 'FAILED', 'PARTIAL')),
    error_message       TEXT,
    metadata_json       TEXT
);

CREATE INDEX IF NOT EXISTS idx_import_logs_created_at ON import_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_import_logs_status     ON import_logs(status);
CREATE INDEX IF NOT EXISTS idx_import_logs_checksum   ON import_logs(checksum);
