-- ==========================================================================
-- MIGRATION 009 — FIXED INCOME EVENTS
-- FinAnalytics V3 | Context: Investments (Wealth)
-- Provides full event representation for FIXED_INCOME assets.
-- Assets of class FIXED_INCOME exist in the catalog (migration 004) but had
-- no event table to reconstruct position or yield history.
-- This table is APPEND-ONLY. No UPDATE, no DELETE.
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- FIXED INCOME EVENTS
-- Represents the full lifecycle of a fixed-income instrument:
--   APPLICATION       → initial deposit / purchase
--   YIELD             → interest credited (rendimento creditado)
--   PARTIAL_REDEMPTION→ partial withdrawal before maturity
--   FULL_REDEMPTION   → full withdrawal / maturity settlement
--   IRRF              → tax withheld at source (autonomous event, e.g. come-cotas)
--
-- Position reconstruction algorithm:
--   current_balance = SUM(gross_amount) FILTER (event_type IN ('APPLICATION','YIELD','PARTIAL_REDEMPTION','FULL_REDEMPTION'))
--   net_balance     = SUM(net_amount)   same filter
--   Note: APPLICATION is positive; PARTIAL_REDEMPTION and FULL_REDEMPTION
--         are stored as POSITIVE values representing the amount withdrawn.
--         The backend is responsible for applying the correct sign when summing.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fixed_income_events (
    id              TEXT PRIMARY KEY,

    -- --- relationships ---
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    account_id      TEXT NOT NULL REFERENCES accounts(id),
    transaction_id  TEXT REFERENCES transactions(id),  -- linked cashflow movement if applicable

    -- --- event classification ---
    event_type      TEXT NOT NULL CHECK(event_type IN (
                        'APPLICATION',          -- initial investment / aporte
                        'YIELD',                -- rendimento creditado ao saldo
                        'PARTIAL_REDEMPTION',   -- resgate parcial
                        'FULL_REDEMPTION',      -- resgate total / vencimento
                        'IRRF'                  -- imposto retido na fonte (autônomo)
                    )),

    event_date      TEXT NOT NULL,              -- ISO 8601 YYYY-MM-DD (data do evento)
    competence_date TEXT,                       -- competence date if different from event_date

    -- --- amounts (always in centavos, always positive) ---
    gross_amount    INTEGER NOT NULL CHECK(gross_amount >= 0),
    irrf_tax        INTEGER NOT NULL DEFAULT 0 CHECK(irrf_tax >= 0),
    net_amount      INTEGER GENERATED ALWAYS AS (gross_amount - irrf_tax) STORED,

    -- --- rate / index information (for YIELD events) ---
    rate_type       TEXT CHECK(rate_type IN ('CDI','SELIC','IPCA','PREFIXADO','IGPM', NULL)),
    rate_pct        REAL,   -- percentage over index: 120.0 = 120% CDI; or fixed rate: 12.5 = 12.5% a.a.
    period_days     INTEGER,-- number of days this yield covers

    -- --- instrument metadata (snapshot at event time) ---
    maturity_date   TEXT,   -- vencimento do título (may differ per event if re-applied)
    institution_name TEXT,  -- name of the issuing institution (CDB do Banco X)

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

-- --------------------------------------------------------------------------
-- INDEXES
-- --------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fie_asset        ON fixed_income_events(asset_id);
CREATE INDEX IF NOT EXISTS idx_fie_account       ON fixed_income_events(account_id);
CREATE INDEX IF NOT EXISTS idx_fie_event_date    ON fixed_income_events(event_date);
CREATE INDEX IF NOT EXISTS idx_fie_event_type    ON fixed_income_events(event_type);
CREATE INDEX IF NOT EXISTS idx_fie_run           ON fixed_income_events(run_id);

-- Composite index for position reconstruction queries:
-- SELECT * FROM fixed_income_events WHERE asset_id = ? AND account_id = ? ORDER BY event_date
CREATE INDEX IF NOT EXISTS idx_fie_position_rebuild
    ON fixed_income_events(asset_id, account_id, event_date);
