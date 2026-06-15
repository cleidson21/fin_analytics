-- ==========================================================================
-- MIGRATION 008 — ANALYTICS & SNAPSHOTS
-- FinAnalytics V3 | Context: Analytics (Materialized Performance Views)
-- All computed nightly by cron job. Never recomputed on frontend request.
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- ASSET POSITIONS
-- Current state of each asset holding (recomputed after every trade).
-- This is a COMPUTED view materialized for performance.
-- Source of truth: trades + corporate_actions → this table is derived.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS asset_positions (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id         TEXT NOT NULL REFERENCES users(id),
    account_id      TEXT NOT NULL REFERENCES accounts(id),
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    -- Computed from trades
    current_quantity    REAL NOT NULL DEFAULT 0,
    average_price       REAL NOT NULL DEFAULT 0,    -- cost basis per share (includes fees)
    total_invested      REAL NOT NULL DEFAULT 0,    -- = current_quantity * average_price
    -- Computed from market data (updated nightly)
    last_price          REAL,
    current_value       REAL,                       -- = current_quantity * last_price
    unrealized_gain     REAL,                       -- = current_value - total_invested
    unrealized_gain_pct REAL,                       -- = unrealized_gain / total_invested
    -- Dividend metrics (12-month trailing)
    dividends_12m       REAL DEFAULT 0,
    dy_current          REAL DEFAULT 0,             -- = dividends_12m / current_value
    yoc                 REAL DEFAULT 0,             -- = dividends_12m / total_invested
    -- Allocation
    portfolio_weight    REAL DEFAULT 0,             -- % of total portfolio
    -- Timestamps
    computed_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    price_date          TEXT,                       -- date of last_price
    UNIQUE(user_id, account_id, asset_id)
);

CREATE INDEX IF NOT EXISTS idx_asset_positions_user    ON asset_positions(user_id);
CREATE INDEX IF NOT EXISTS idx_asset_positions_asset   ON asset_positions(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_positions_account ON asset_positions(account_id);

-- --------------------------------------------------------------------------
-- PORTFOLIO SNAPSHOTS
-- Daily/monthly performance snapshot. Enables historical charts.
-- TWR is computed as unit-of-account (quota value starting at 1.00).
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id         TEXT NOT NULL REFERENCES users(id),
    date            TEXT NOT NULL,                  -- YYYY-MM-DD (granularity: daily)
    -- Wealth
    total_equity        REAL NOT NULL,              -- total market value of portfolio
    cost_basis          REAL NOT NULL,              -- total invested
    total_deposits      REAL NOT NULL DEFAULT 0,    -- cumulative deposits to date
    total_withdrawals   REAL NOT NULL DEFAULT 0,    -- cumulative withdrawals to date
    -- Performance (TWR)
    quota_value         REAL NOT NULL DEFAULT 1.0,  -- the "fund share" value
    daily_twr           REAL DEFAULT 0,             -- daily TWR
    monthly_twr         REAL DEFAULT 0,
    cumulative_twr      REAL DEFAULT 0,             -- total return since inception
    -- Performance (MWR / XIRR)
    mwr                 REAL,                       -- money-weighted return (IRR)
    -- Risk metrics (rolling 252 trading days)
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    beta_ibov           REAL,
    alpha_ibov          REAL,
    max_drawdown        REAL,                       -- max peak-to-trough loss
    volatility_annual   REAL,                       -- annualized standard deviation
    -- Benchmark comparison
    ibov_cumulative     REAL,                       -- IBOV cumulative return same period
    cdi_cumulative      REAL,                       -- CDI cumulative return same period
    ifix_cumulative     REAL,
    spx_cumulative      REAL,
    -- Dividends
    dividends_month     REAL DEFAULT 0,
    dividends_year      REAL DEFAULT 0,
    dividends_total     REAL DEFAULT 0,
    -- Computed at
    computed_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_user ON portfolio_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_date ON portfolio_snapshots(date);

-- --------------------------------------------------------------------------
-- BENCHMARK SNAPSHOTS
-- Stores benchmark cumulative returns from inception date for charting.
-- Computed from benchmark_prices during nightly cron.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benchmark_snapshots (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id         TEXT NOT NULL REFERENCES users(id),     -- anchor to user's inception date
    ticker          TEXT NOT NULL,                          -- 'CDI','IBOV','IFIX','SPX'
    date            TEXT NOT NULL,
    daily_return    REAL NOT NULL DEFAULT 0,
    cumulative_return REAL NOT NULL DEFAULT 0,              -- from user's inception date
    computed_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(user_id, ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_benchmark_snapshots_user   ON benchmark_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_snapshots_ticker ON benchmark_snapshots(ticker);
CREATE INDEX IF NOT EXISTS idx_benchmark_snapshots_date   ON benchmark_snapshots(date);

-- --------------------------------------------------------------------------
-- CASHFLOW SUMMARIES (Monthly aggregation for budget analysis)
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cashflow_summaries (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id         TEXT NOT NULL REFERENCES users(id),
    year_month      TEXT NOT NULL,                  -- 'YYYY-MM'
    total_income    REAL NOT NULL DEFAULT 0,
    total_expense   REAL NOT NULL DEFAULT 0,
    total_invested  REAL NOT NULL DEFAULT 0,
    net_cashflow    REAL NOT NULL DEFAULT 0,        -- income - expense
    computed_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(user_id, year_month)
);
