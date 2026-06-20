-- ==========================================================================
-- MIGRATION 011 — AI PROMPT VERSIONING
-- FinAnalytics V3 | Context: AI (Classification Pipeline)
-- Replaces the mutable ai_prompts table with an immutable version log.
-- Ensures full traceability: every ai_run is permanently linked to the
-- exact prompt version that was active at execution time.
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- AI PROMPT VERSIONS
-- Each row is an immutable snapshot of a prompt template at a given version.
-- Rules:
--   - A new version is always a new INSERT, never an UPDATE.
--   - Only one version per prompt_name may have is_active = 1 at a time.
--     (enforced at application layer; partial index below provides a hint)
--   - Retiring a prompt = setting is_active = 0 on the previous version
--     and inserting a new row with version = old_version + 1.
--   - Rows are never deleted.
--
-- RELATIONSHIP WITH ai_prompts (migration 007):
--   ai_prompts remains in the schema for backwards compatibility and serves
--   as a named registry (name → description, current active pointer).
--   ai_prompt_versions is the immutable version store.
--   ai_runs must reference ai_prompt_versions.id going forward.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_prompt_versions (
    id              TEXT PRIMARY KEY,

    -- --- identity ---
    prompt_name     TEXT NOT NULL,  -- same name as ai_prompts.name (e.g. 'classify_transaction')
    version         INTEGER NOT NULL CHECK(version >= 1),

    -- --- content (immutable after insert) ---
    template        TEXT NOT NULL,  -- the full prompt template (Jinja2 / f-string)
    model           TEXT NOT NULL,  -- target LLM: 'gemini-1.5-flash', 'gemini-2.0-flash', etc.
    system_prompt   TEXT,           -- optional system-level instruction separate from template
    temperature     REAL DEFAULT 0.0,
    max_tokens      INTEGER,

    -- --- lifecycle ---
    is_active       INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0, 1)),
    deprecated_at   TEXT,           -- ISO 8601; set when a newer version supersedes this one
    change_summary  TEXT,           -- human-readable description of what changed vs previous version

    -- --- provenance ---
    created_by      TEXT REFERENCES users(id),  -- NULL = system/seed
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    -- NO updated_at. Rows are immutable after insert.

    UNIQUE(prompt_name, version)
);

-- --------------------------------------------------------------------------
-- INDEXES
-- --------------------------------------------------------------------------
-- Fast lookup of the active version for a given prompt name
CREATE INDEX IF NOT EXISTS idx_apv_name_active
    ON ai_prompt_versions(prompt_name, is_active);

-- Partial index: at most one active version per prompt name (advisory)
CREATE UNIQUE INDEX IF NOT EXISTS idx_apv_one_active_per_name
    ON ai_prompt_versions(prompt_name)
    WHERE is_active = 1;

-- --------------------------------------------------------------------------
-- EXTEND ai_runs: add column to link to the exact prompt version used
-- --------------------------------------------------------------------------
-- NOTE: SQLite supports ADD COLUMN on existing tables.
-- The new column is nullable to maintain compatibility with existing rows
-- that reference the old ai_prompts table via prompt_id.
-- New code must populate prompt_version_id. prompt_id is kept for legacy reads.
ALTER TABLE ai_runs ADD COLUMN prompt_version_id TEXT REFERENCES ai_prompt_versions(id);

CREATE INDEX IF NOT EXISTS idx_ai_runs_prompt_version
    ON ai_runs(prompt_version_id);

-- --------------------------------------------------------------------------
-- SEED: Bootstrap ai_prompt_versions from current ai_prompts data.
-- Creates version 1 for every existing named prompt as a placeholder,
-- so ai_runs generated going forward have a valid version to reference.
-- --------------------------------------------------------------------------
INSERT OR IGNORE INTO ai_prompt_versions (
    id, prompt_name, version, template, model, is_active, change_summary
)
SELECT
    'apv-' || lower(hex(randomblob(8))),
    name,
    1,
    template,
    model,
    1,
    'Initial version — migrated from ai_prompts on schema freeze (migration 011)'
FROM ai_prompts
WHERE is_active = 1;
