-- =============================================================
-- MIGRATION: sprint_0_5_1_down.sql
-- Sprint 0.5.1 — Governança de Importação e Rastreabilidade
-- Direção: DOWN (reverter)
-- =============================================================

PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- -----------------------------------------------------------
-- 1. Remover tabelas novas
-- -----------------------------------------------------------
DROP TABLE IF EXISTS ai_runs;
DROP TABLE IF EXISTS import_artifacts;
DROP TABLE IF EXISTS prompt_versions;

-- -----------------------------------------------------------
-- 2. Recriar import_runs no formato original
-- -----------------------------------------------------------
DROP INDEX IF EXISTS idx_import_runs_checksum;
DROP INDEX IF EXISTS idx_import_runs_source_type;
DROP INDEX IF EXISTS idx_import_runs_status;
DROP INDEX IF EXISTS idx_import_runs_started_at;

CREATE TABLE import_runs_restore (
    id               TEXT PRIMARY KEY,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_payload      TEXT NULL,
    payload_checksum TEXT
);

-- Restaurar IDs que existiam antes (raw_payload não pode ser recuperado — perdido)
INSERT INTO import_runs_restore (id, created_at, raw_payload, payload_checksum)
SELECT
    id,
    started_at AS created_at,
    NULL       AS raw_payload,
    checksum   AS payload_checksum
FROM import_runs;

DROP TABLE import_runs;
ALTER TABLE import_runs_restore RENAME TO import_runs;

-- Recriar índice original
CREATE INDEX IF NOT EXISTS idx_import_runs_checksum
ON import_runs(payload_checksum);

-- -----------------------------------------------------------
-- 3. Restaurar etl_runs a partir de etl_runs_legacy
-- -----------------------------------------------------------
ALTER TABLE etl_runs_legacy RENAME TO etl_runs;

COMMIT;

PRAGMA foreign_keys = ON;
-- =============================================================
-- FIM DA MIGRATION DOWN
-- AVISO: raw_payload NÃO é recuperável após o DOWN — faça backup antes.
-- =============================================================
