-- ==========================================================================
-- MIGRATION 005 — OPEN FINANCE & POSITION SNAPSHOTS
-- FinAnalytics V3 | Context: Investments (Wealth)
-- ==========================================================================

PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

-- --------------------------------------------------------------------------
-- 1. CREATE POSITION SNAPSHOTS TABLE
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS position_snapshots (
    id              TEXT PRIMARY KEY,  -- Idempotency hash
    account_id      TEXT NOT NULL REFERENCES accounts(id),
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    reference_date  TEXT NOT NULL,
    quantity        REAL NOT NULL,
    unit_price      INTEGER,           -- centavos
    total_value     INTEGER,           -- centavos
    source_system   TEXT NOT NULL,
    metadata        TEXT,              -- JSON string
    run_id          TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(account_id, asset_id, reference_date)
);

CREATE INDEX IF NOT EXISTS idx_position_snapshots_account ON position_snapshots(account_id);
CREATE INDEX IF NOT EXISTS idx_position_snapshots_asset   ON position_snapshots(asset_id);
CREATE INDEX IF NOT EXISTS idx_position_snapshots_date    ON position_snapshots(reference_date);


-- --------------------------------------------------------------------------
-- 2. ALTER BROKER_NOTES (Add OPEN_FINANCE to source)
-- --------------------------------------------------------------------------
CREATE TABLE new_broker_notes (
    id                  TEXT PRIMARY KEY,
    account_id          TEXT NOT NULL REFERENCES accounts(id),
    note_number         TEXT NOT NULL,          
    note_date           TEXT NOT NULL,          
    settlement_date     TEXT,                   
    brokerage_fee       INTEGER NOT NULL DEFAULT 0,    
    clearing_fee        INTEGER NOT NULL DEFAULT 0,    
    registration_fee    INTEGER NOT NULL DEFAULT 0,    
    iss_tax             INTEGER NOT NULL DEFAULT 0,    
    irrf_tax            INTEGER NOT NULL DEFAULT 0,    
    other_fees          INTEGER NOT NULL DEFAULT 0,    
    total_fees          INTEGER GENERATED ALWAYS AS (
                            brokerage_fee + clearing_fee + registration_fee + iss_tax + irrf_tax + other_fees
                        ) STORED,
    source              TEXT NOT NULL DEFAULT 'PDF' CHECK(source IN ('PDF','B3_API','MANUAL','MYPROFIT_IMPORT','OPEN_FINANCE')),
    raw_file_path       TEXT,                   
    run_id              TEXT,                   
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(account_id, note_number, note_date)
);

INSERT INTO new_broker_notes (
    id, account_id, note_number, note_date, settlement_date,
    brokerage_fee, clearing_fee, registration_fee, iss_tax, irrf_tax, other_fees,
    source, raw_file_path, run_id, created_at
)
SELECT 
    id, account_id, note_number, note_date, settlement_date,
    brokerage_fee, clearing_fee, registration_fee, iss_tax, irrf_tax, other_fees,
    source, raw_file_path, run_id, created_at
FROM broker_notes;

DROP TABLE broker_notes;
ALTER TABLE new_broker_notes RENAME TO broker_notes;

CREATE INDEX idx_broker_notes_account ON broker_notes(account_id);
CREATE INDEX idx_broker_notes_date    ON broker_notes(note_date);


-- --------------------------------------------------------------------------
-- 3. ALTER TRADES (Add OPEN_FINANCE to source)
-- --------------------------------------------------------------------------
CREATE TABLE new_trades (
    id              TEXT PRIMARY KEY,
    broker_note_id  TEXT REFERENCES broker_notes(id) ON DELETE SET NULL,
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    account_id      TEXT NOT NULL REFERENCES accounts(id),
    type            TEXT NOT NULL CHECK(type IN ('BUY','SELL')),
    trade_date      TEXT NOT NULL,              
    quantity        REAL NOT NULL CHECK(quantity > 0),
    unit_price      INTEGER NOT NULL CHECK(unit_price >= 0),  
    gross_value     INTEGER GENERATED ALWAYS AS (CAST(quantity * unit_price AS INTEGER)) STORED,
    fees_allocated  INTEGER NOT NULL DEFAULT 0,    
    net_value       INTEGER GENERATED ALWAYS AS (
                        CASE WHEN type = 'BUY'
                             THEN CAST(quantity * unit_price AS INTEGER) + fees_allocated
                             ELSE CAST(quantity * unit_price AS INTEGER) - fees_allocated
                        END
                    ) STORED,
    source          TEXT NOT NULL DEFAULT 'BROKER_NOTE' CHECK(source IN (
                        'BROKER_NOTE','MANUAL','MYPROFIT_IMPORT','B3_API','OPEN_FINANCE'
                    )),
    run_id          TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

INSERT INTO new_trades (
    id, broker_note_id, asset_id, account_id, type, trade_date,
    quantity, unit_price, fees_allocated, source, run_id, created_at
)
SELECT 
    id, broker_note_id, asset_id, account_id, type, trade_date,
    quantity, unit_price, fees_allocated, source, run_id, created_at
FROM trades;

DROP TABLE trades;
ALTER TABLE new_trades RENAME TO trades;

CREATE INDEX idx_trades_asset     ON trades(asset_id);
CREATE INDEX idx_trades_account   ON trades(account_id);
CREATE INDEX idx_trades_date      ON trades(trade_date);
CREATE INDEX idx_trades_type      ON trades(type);


-- --------------------------------------------------------------------------
-- 4. ALTER DIVIDENDS (Add OPEN_FINANCE to source)
-- --------------------------------------------------------------------------
CREATE TABLE new_dividends (
    id              TEXT PRIMARY KEY,
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    account_id      TEXT NOT NULL REFERENCES accounts(id),
    type            TEXT NOT NULL CHECK(type IN (
                        'DIVIDEND',         
                        'JCP',              
                        'AMORTIZATION',     
                        'FII_RENT',         
                        'FOREIGN_DIVIDEND'  
                    )),
    currency        TEXT NOT NULL DEFAULT 'BRL',
    ex_date         TEXT NOT NULL,          
    payment_date    TEXT NOT NULL,          
    quantity_held   REAL NOT NULL,          
    value_per_share INTEGER NOT NULL,       
    gross_amount    INTEGER NOT NULL,       
    irrf_tax        INTEGER NOT NULL DEFAULT 0, 
    net_amount      INTEGER GENERATED ALWAYS AS (gross_amount - irrf_tax) STORED,
    transaction_id  TEXT REFERENCES transactions(id), 
    source          TEXT NOT NULL DEFAULT 'BROKER_NOTE' CHECK(source IN (
                        'BROKER_NOTE','MYPROFIT_IMPORT','MANUAL','B3_API','OPEN_FINANCE'
                    )),
    run_id          TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(asset_id, account_id, ex_date, type)
);

INSERT INTO new_dividends (
    id, asset_id, account_id, type, currency, ex_date, payment_date,
    quantity_held, value_per_share, gross_amount, irrf_tax,
    transaction_id, source, run_id, created_at
)
SELECT 
    id, asset_id, account_id, type, currency, ex_date, payment_date,
    quantity_held, value_per_share, gross_amount, irrf_tax,
    transaction_id, source, run_id, created_at
FROM dividends;

DROP TABLE dividends;
ALTER TABLE new_dividends RENAME TO dividends;

CREATE INDEX idx_dividends_asset        ON dividends(asset_id);
CREATE INDEX idx_dividends_account      ON dividends(account_id);
CREATE INDEX idx_dividends_payment_date ON dividends(payment_date);

COMMIT;
PRAGMA foreign_keys=ON;
