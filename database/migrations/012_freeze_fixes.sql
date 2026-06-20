-- ==========================================================================
-- MIGRATION 012 — FREEZE FIXES
-- FinAnalytics V3 | Schema Certification
-- Applies 4 structural corrections required before architectural freeze.
--
-- Changes:
--   1. fixed_income_events   — recreate: add CORRECTION event_type + corrects_event_id
--   2. benchmark_prices      — recreate: value INTEGER → REAL (removes implicit scale ambiguity)
--   3. installments          — recreate: add CANCELLED status + cancelled_at
--   4. installment_plans     — ALTER TABLE ADD COLUMN: status + cancelled_at + renegotiated_to_plan_id
--
-- All affected tables are empty at time of application (verified: 0 rows each).
-- SQLite pattern for schema changes: CREATE new → INSERT from old → DROP old → RENAME.
-- ==========================================================================

PRAGMA foreign_keys=OFF;  -- required during table recreation to avoid FK cascade errors

-- ==========================================================================
-- FIX 1: fixed_income_events
-- Problem: no CORRECTION event_type; gross_amount CHECK(>= 0) blocks corrections.
-- Solution: add CORRECTION to event_type enum + corrects_event_id self-reference FK.
--
-- CORRECTION semantics:
--   corrects_event_id → points to the erroneous event being superseded
--   gross_amount      → the CORRECT value (not a delta)
--   Backend rule: when reading events, a CORRECTION replaces the referenced event's
--                 gross_amount with its own gross_amount for position reconstruction.
-- ==========================================================================

CREATE TABLE IF NOT EXISTS fixed_income_events_new (
    id              TEXT PRIMARY KEY,

    -- --- relationships ---
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    account_id      TEXT NOT NULL REFERENCES accounts(id),
    transaction_id  TEXT REFERENCES transactions(id),
    corrects_event_id TEXT REFERENCES fixed_income_events_new(id),  -- non-null only for CORRECTION events

    -- --- event classification ---
    event_type      TEXT NOT NULL CHECK(event_type IN (
                        'APPLICATION',          -- initial investment / aporte
                        'YIELD',                -- rendimento creditado ao saldo
                        'PARTIAL_REDEMPTION',   -- resgate parcial
                        'FULL_REDEMPTION',      -- resgate total / vencimento
                        'IRRF',                 -- imposto retido na fonte (autônomo)
                        'CORRECTION'            -- supersedes a prior erroneous event (see corrects_event_id)
                    )),

    event_date      TEXT NOT NULL,
    competence_date TEXT,

    -- --- amounts (always in centavos, always positive) ---
    -- For CORRECTION events: gross_amount = the correct value, not a delta.
    gross_amount    INTEGER NOT NULL CHECK(gross_amount >= 0),
    irrf_tax        INTEGER NOT NULL DEFAULT 0 CHECK(irrf_tax >= 0),
    net_amount      INTEGER GENERATED ALWAYS AS (gross_amount - irrf_tax) STORED,

    -- --- rate / index information (for YIELD events) ---
    rate_type       TEXT CHECK(rate_type IN ('CDI','SELIC','IPCA','PREFIXADO','IGPM', NULL)),
    rate_pct        REAL,
    period_days     INTEGER,

    -- --- instrument metadata (snapshot at event time) ---
    maturity_date   TEXT,
    institution_name TEXT,

    -- --- provenance ---
    source          TEXT NOT NULL DEFAULT 'MANUAL' CHECK(source IN (
                        'MANUAL',
                        'MYPROFIT_EVOLUCAO_CSV',
                        'BROKER_NOTE_PDF',
                        'B3_API',
                        'SYSTEM'
                    )),
    run_id          TEXT REFERENCES import_runs(id),
    notes           TEXT,

    -- --- immutability ---
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    -- NO updated_at. Append-only.
);

INSERT INTO fixed_income_events_new
SELECT
    id, asset_id, account_id, transaction_id,
    NULL,  -- corrects_event_id (new column, NULL for existing rows)
    event_type, event_date, competence_date,
    gross_amount, irrf_tax,
    rate_type, rate_pct, period_days,
    maturity_date, institution_name,
    source, run_id, notes, created_at
FROM fixed_income_events;

DROP TABLE fixed_income_events;
ALTER TABLE fixed_income_events_new RENAME TO fixed_income_events;

-- Restore indexes
CREATE INDEX IF NOT EXISTS idx_fie_asset          ON fixed_income_events(asset_id);
CREATE INDEX IF NOT EXISTS idx_fie_account         ON fixed_income_events(account_id);
CREATE INDEX IF NOT EXISTS idx_fie_event_date      ON fixed_income_events(event_date);
CREATE INDEX IF NOT EXISTS idx_fie_event_type      ON fixed_income_events(event_type);
CREATE INDEX IF NOT EXISTS idx_fie_run             ON fixed_income_events(run_id);
CREATE INDEX IF NOT EXISTS idx_fie_corrects        ON fixed_income_events(corrects_event_id)
    WHERE corrects_event_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_fie_position_rebuild
    ON fixed_income_events(asset_id, account_id, event_date);

-- ==========================================================================
-- FIX 2: benchmark_prices — value INTEGER → REAL
-- Problem: CDI (daily rate ~0.000467) and IBOV (index ~135000) cannot share
--          an INTEGER column without an implicit, undocumented scale factor.
-- Solution: REAL (IEEE 754 double, 15-16 sig. digits) is self-documenting.
--           CDI stored as 0.000467, IBOV stored as 135248.50.
--           No scale lookup needed. accumulated_factor stays REAL (unchanged).
-- ==========================================================================

CREATE TABLE IF NOT EXISTS benchmark_prices_new (
    ticker             TEXT NOT NULL,
    date               TEXT NOT NULL,
    value              REAL NOT NULL,           -- CHANGED: INTEGER → REAL. Self-documenting.
    accumulated_factor REAL,
    source             TEXT NOT NULL DEFAULT 'BCB_SGS',
    fetched_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (ticker, date)
);

INSERT INTO benchmark_prices_new
SELECT ticker, date, CAST(value AS REAL), accumulated_factor, source, fetched_at
FROM benchmark_prices;

DROP TABLE benchmark_prices;
ALTER TABLE benchmark_prices_new RENAME TO benchmark_prices;

-- Restore indexes
CREATE INDEX IF NOT EXISTS idx_benchmark_prices_ticker ON benchmark_prices(ticker);
CREATE INDEX IF NOT EXISTS idx_benchmark_prices_date   ON benchmark_prices(date);

-- ==========================================================================
-- FIX 3: installments — add CANCELLED status + cancelled_at
-- Problem: CHECK(status IN ('PENDING','BILLED','PAID')) blocks representing
--          a cancelled installment (product return, bank dispute, renegotiation).
--          Altering CHECK constraint in SQLite requires table recreation.
-- ==========================================================================

CREATE TABLE IF NOT EXISTS installments_new (
    id                  TEXT PRIMARY KEY,
    installment_plan_id TEXT NOT NULL REFERENCES installment_plans(id) ON DELETE CASCADE,
    installment_number  INTEGER NOT NULL,
    amount              INTEGER NOT NULL,
    expected_date       TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN (
                            'PENDING',      -- not yet billed
                            'BILLED',       -- appeared on a closed invoice
                            'PAID',         -- invoice containing this installment was paid
                            'CANCELLED'     -- product returned, dispute resolved, or plan renegotiated
                        )),
    cancelled_at        TEXT,               -- ISO 8601; set when status transitions to CANCELLED
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(installment_plan_id, installment_number)
);

INSERT INTO installments_new
SELECT id, installment_plan_id, installment_number, amount, expected_date, status,
       NULL,  -- cancelled_at (new column)
       created_at
FROM installments;

DROP TABLE installments;
ALTER TABLE installments_new RENAME TO installments;

-- Restore indexes
CREATE INDEX IF NOT EXISTS idx_installments_plan   ON installments(installment_plan_id);
CREATE INDEX IF NOT EXISTS idx_installments_date   ON installments(expected_date);
CREATE INDEX IF NOT EXISTS idx_installments_status ON installments(status);

-- ==========================================================================
-- FIX 4: installment_plans — add status, cancelled_at, renegotiated_to_plan_id
-- Problem: no way to mark a plan as cancelled or renegotiated.
--          "Active plans" query would require checking all child installments.
-- Solution: ALTER TABLE ADD COLUMN (valid in SQLite for nullable/default columns).
--           No table recreation needed.
-- ==========================================================================

ALTER TABLE installment_plans ADD COLUMN
    status TEXT NOT NULL DEFAULT 'ACTIVE'
    CHECK(status IN (
        'ACTIVE',        -- plan is ongoing
        'CANCELLED',     -- all installments cancelled (product return, dispute)
        'RENEGOTIATED'   -- replaced by a new plan (debt renegotiation)
    ));

ALTER TABLE installment_plans ADD COLUMN
    cancelled_at TEXT;   -- ISO 8601; set when status = CANCELLED

ALTER TABLE installment_plans ADD COLUMN
    renegotiated_to_plan_id TEXT REFERENCES installment_plans(id);
    -- points to the new plan that replaced this one when status = RENEGOTIATED

CREATE INDEX IF NOT EXISTS idx_installment_plans_status
    ON installment_plans(status)
    WHERE status != 'ACTIVE';

-- ==========================================================================
-- Re-enable foreign key enforcement
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- ==========================================================================
-- VALIDATION CHECKPOINT
-- Run after applying this migration to confirm structural integrity:
--   PRAGMA integrity_check;        → must return 'ok'
--   PRAGMA foreign_key_check;      → must return 0 rows
-- ==========================================================================
