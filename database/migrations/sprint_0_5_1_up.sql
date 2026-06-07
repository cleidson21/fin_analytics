-- =============================================================
-- MIGRATION: sprint_0_5_1_up.sql
-- Sprint 0.5.1 — Governança de Importação e Rastreabilidade
-- Direção: UP (aplicar)
-- Compatibilidade: SQLite >= 3.25
-- =============================================================

PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- -----------------------------------------------------------
-- 1. RENOMEAR etl_runs → etl_runs_legacy (preservar histórico)
-- -----------------------------------------------------------
ALTER TABLE etl_runs RENAME TO etl_runs_legacy;

-- -----------------------------------------------------------
-- 2. EXPANDIR import_runs (rename & recreate — SQLite não tem
--    ALTER COLUMN, então usamos a estratégia rename/copy/drop)
-- -----------------------------------------------------------
ALTER TABLE import_runs RENAME TO import_runs_old;

-- Remover índice antigo (será recriado com novo nome de coluna)
DROP INDEX IF EXISTS idx_import_runs_checksum;

CREATE TABLE import_runs (
    id          TEXT        NOT NULL PRIMARY KEY,
    source_type TEXT        NOT NULL DEFAULT 'PIERRE',   -- MYPROFIT | PIERRE | GEMINI | OPEN_FINANCE | YFINANCE | MANUAL
    file_name   TEXT        NOT NULL DEFAULT '',
    checksum    TEXT        NOT NULL DEFAULT '',          -- SHA-256 do payload original
    started_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status      TEXT        NOT NULL DEFAULT 'PENDING',  -- PENDING | PROCESSING | SUCCESS | PARTIAL | FAILED
    rows_read   INTEGER     NOT NULL DEFAULT 0,
    rows_inserted INTEGER   NOT NULL DEFAULT 0,
    rows_updated  INTEGER   NOT NULL DEFAULT 0,
    rows_failed   INTEGER   NOT NULL DEFAULT 0,
    error_log   TEXT,                                    -- JSON array de erros por linha
    created_by  TEXT
);

-- Migrar dados existentes para a nova estrutura
-- Registros antigos: source_type=PIERRE, status=SUCCESS (já foram processados)
INSERT INTO import_runs (
    id, source_type, file_name, checksum,
    started_at, finished_at,
    status, rows_read, rows_inserted, rows_updated, rows_failed
)
SELECT
    id,
    'PIERRE'                                  AS source_type,
    'importacao_legada_pierre'                AS file_name,
    COALESCE(payload_checksum, 'legacy_' || id) AS checksum,
    created_at                                AS started_at,
    created_at                                AS finished_at,
    'SUCCESS'                                 AS status,
    0, 0, 0, 0
FROM import_runs_old;

-- -----------------------------------------------------------
-- 3. CRIAR import_artifacts
-- -----------------------------------------------------------
CREATE TABLE import_artifacts (
    id              TEXT        NOT NULL PRIMARY KEY,
    import_run_id   TEXT        NOT NULL,
    artifact_type   TEXT        NOT NULL,  -- PROVENTO_CSV | EVOLUCAO_CSV | TABLE_EXPORT_CSV | PIERRE_MSG | GEMINI_JSON
    storage_path    TEXT        NOT NULL,
    sha256          TEXT        NOT NULL,
    size_bytes      INTEGER     NOT NULL DEFAULT 0,
    mime_type       TEXT,                  -- ex: text/csv, application/json
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
);

-- Migrar raw_payloads existentes como artifacts legados do tipo PIERRE_MSG
INSERT INTO import_artifacts (
    id, import_run_id, artifact_type,
    storage_path, sha256, size_bytes, mime_type, created_at
)
SELECT
    lower(hex(randomblob(16))),               -- UUID aleatório em SQLite
    id                                        AS import_run_id,
    'PIERRE_MSG'                              AS artifact_type,
    'legacy_db_payload'                       AS storage_path,
    COALESCE(payload_checksum, 'legacy_' || id) AS sha256,
    COALESCE(length(raw_payload), 0)          AS size_bytes,
    'text/plain'                              AS mime_type,
    created_at
FROM import_runs_old
WHERE raw_payload IS NOT NULL AND raw_payload != '';

-- Remover tabela antiga (dados já migrados)
DROP TABLE import_runs_old;

-- -----------------------------------------------------------
-- 4. CRIAR prompt_versions
-- -----------------------------------------------------------
CREATE TABLE prompt_versions (
    id          TEXT        NOT NULL PRIMARY KEY,
    name        TEXT        NOT NULL,
    version     INTEGER     NOT NULL,
    content     TEXT        NOT NULL,
    active      INTEGER     NOT NULL DEFAULT 0,   -- 0=false, 1=true (BOOLEAN em SQLite)
    created_at  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes       TEXT,
    UNIQUE (name, version)
);

-- -----------------------------------------------------------
-- 5. CRIAR ai_runs
-- -----------------------------------------------------------
CREATE TABLE ai_runs (
    id                  TEXT        NOT NULL PRIMARY KEY,
    import_run_id       TEXT,                              -- FK opcional
    prompt_version_id   TEXT        NOT NULL,
    model               TEXT        NOT NULL,
    input_text          TEXT        NOT NULL,
    output_json         TEXT,                              -- JSON da resposta estruturada
    confidence          REAL,                              -- 0.0–1.0
    latency_ms          INTEGER,
    tokens_input        INTEGER,
    tokens_output       INTEGER,
    estimated_cost      REAL,                              -- custo estimado em USD
    status              TEXT        NOT NULL DEFAULT 'SUCCESS',  -- SUCCESS | FAILED | LOW_CONFIDENCE
    created_at          TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (import_run_id)     REFERENCES import_runs(id) ON DELETE SET NULL,
    FOREIGN KEY (prompt_version_id) REFERENCES prompt_versions(id) ON DELETE RESTRICT
);

-- -----------------------------------------------------------
-- 6. ÍNDICES
-- -----------------------------------------------------------

-- import_runs
CREATE INDEX IF NOT EXISTS idx_import_runs_checksum    ON import_runs(checksum);
CREATE INDEX IF NOT EXISTS idx_import_runs_source_type ON import_runs(source_type);
CREATE INDEX IF NOT EXISTS idx_import_runs_status      ON import_runs(status);
CREATE INDEX IF NOT EXISTS idx_import_runs_started_at  ON import_runs(started_at);

-- import_artifacts
CREATE INDEX IF NOT EXISTS idx_import_artifacts_run    ON import_artifacts(import_run_id);
CREATE INDEX IF NOT EXISTS idx_import_artifacts_type   ON import_artifacts(artifact_type);

-- prompt_versions
CREATE INDEX IF NOT EXISTS idx_prompt_versions_name    ON prompt_versions(name);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_active  ON prompt_versions(name, active);

-- ai_runs
CREATE INDEX IF NOT EXISTS idx_ai_runs_import_run      ON ai_runs(import_run_id);
CREATE INDEX IF NOT EXISTS idx_ai_runs_prompt_version  ON ai_runs(prompt_version_id);
CREATE INDEX IF NOT EXISTS idx_ai_runs_status          ON ai_runs(status);
CREATE INDEX IF NOT EXISTS idx_ai_runs_created_at      ON ai_runs(created_at);

COMMIT;

PRAGMA foreign_keys = ON;
-- =============================================================
-- FIM DA MIGRATION UP
-- =============================================================
