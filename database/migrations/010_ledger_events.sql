-- ==========================================================================
-- MIGRATION 010 — LEDGER EVENTS (Transaction Lifecycle)
-- FinAnalytics V3 | Context: Cashflow (Immutable Ledger Extension)
-- Provides an append-only event log for transaction state transitions.
-- The transactions table is and remains IMMUTABLE (no UPDATE, no DELETE).
-- This table extends the ledger without touching it.
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- TRANSACTION EVENTS
-- Records lifecycle events for any transaction in the ledger.
-- This is the authoritative mechanism for:
--   - Correcting category or merchant classification
--   - Linking reversals and estornos to their originals
--   - Marking transactions as ignored or reviewed
--   - Linking both sides of an internal transfer (complements transfers table)
--
-- READ SEMANTICS:
--   The effective state of a transaction is computed by replaying all events
--   in created_at order. The last event of each event_type wins.
--   For CATEGORY_CORRECTED and MERCHANT_CORRECTED, only the latest event
--   per field is the effective value. All previous events are historical record.
--
-- RELATIONSHIP WITH data_corrections (migration 006):
--   data_corrections remains active and continues to record field-level changes.
--   transaction_events is the richer, extensible mechanism for events that
--   carry structured payloads (e.g., reversal links, status transitions).
--   Both coexist. data_corrections may be deprecated in a future migration
--   if/when the backend is fully migrated to transaction_events.
--
-- IMMUTABILITY CONTRACT:
--   INSERT-ONLY. No UPDATE. No DELETE.
--   Corrections are made by inserting a new event, not overwriting the old one.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaction_events (
    id              TEXT PRIMARY KEY,

    -- --- subject ---
    transaction_id  TEXT NOT NULL REFERENCES transactions(id),

    -- --- event type ---
    event_type      TEXT NOT NULL CHECK(event_type IN (
                        'CATEGORY_CORRECTED',   -- category_id changed; see payload_json
                        'MERCHANT_CORRECTED',   -- merchant_id changed; see payload_json
                        'REVERSAL_LINKED',      -- this tx is a reversal of another; payload: {original_transaction_id}
                        'TRANSFER_LINKED',      -- this tx is one side of a transfer; payload: {transfer_id}
                        'IGNORED',              -- exclude from all cashflow reports
                        'UNIGNORED',            -- re-include (reverts a prior IGNORED event)
                        'REVIEWED'              -- user confirmed the classification is correct
                    )),

    -- --- structured payload ---
    -- JSON object containing event-specific data. Schema per event_type:
    --   CATEGORY_CORRECTED : {"old_category_id": "...", "new_category_id": "..."}
    --   MERCHANT_CORRECTED : {"old_merchant_id": "...", "new_merchant_id": "..."}
    --   REVERSAL_LINKED    : {"original_transaction_id": "...", "reversal_type": "FULL|PARTIAL", "amount": 0}
    --   TRANSFER_LINKED    : {"transfer_id": "...", "role": "OUT|IN"}
    --   IGNORED            : {"reason": "..."} (optional)
    --   UNIGNORED          : {} (no payload needed)
    --   REVIEWED           : {"confidence": 1.0} (optional)
    payload_json    TEXT,

    -- --- provenance ---
    user_id         TEXT REFERENCES users(id),      -- NULL = system-generated event
    ai_run_id       TEXT REFERENCES ai_runs(id),    -- linked AI classification run if applicable
    run_id          TEXT REFERENCES import_runs(id),-- linked import run if applicable

    -- --- immutability ---
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    -- NO updated_at. Append-only.
);

-- --------------------------------------------------------------------------
-- INDEXES
-- --------------------------------------------------------------------------
-- Primary access pattern: all events for a given transaction
CREATE INDEX IF NOT EXISTS idx_tx_events_transaction
    ON transaction_events(transaction_id, created_at);

-- Lookup by event type (e.g., find all reversals)
CREATE INDEX IF NOT EXISTS idx_tx_events_type
    ON transaction_events(event_type);

-- Lookup by user (audit: what did this user correct?)
CREATE INDEX IF NOT EXISTS idx_tx_events_user
    ON transaction_events(user_id);
