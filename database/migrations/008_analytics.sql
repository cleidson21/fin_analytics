-- ==========================================================================
-- MIGRATION 008 — ANALYTICS & SNAPSHOTS
-- FinAnalytics V3 | Context: Analytics (Materialized Performance Views)
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- ASSET POSITIONS
-- Current state of each asset holding (quantity and cost).
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS asset_positions (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id),
    account_id      TEXT NOT NULL REFERENCES accounts(id),
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    current_quantity    REAL NOT NULL DEFAULT 0,
    average_price       INTEGER NOT NULL DEFAULT 0,    -- cost basis per share (centavos)
    total_invested      INTEGER NOT NULL DEFAULT 0,    -- = current_quantity * average_price (centavos)
    dividends_12m       INTEGER DEFAULT 0,             -- 12-month trailing (centavos)
    computed_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(user_id, account_id, asset_id)
);

CREATE INDEX IF NOT EXISTS idx_asset_positions_user    ON asset_positions(user_id);
CREATE INDEX IF NOT EXISTS idx_asset_positions_asset   ON asset_positions(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_positions_account ON asset_positions(account_id);

-- --------------------------------------------------------------------------
-- ASSET VALUATIONS
-- Current market value and performance of the position (separated from cost/qty).
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS asset_valuations (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id),
    account_id      TEXT NOT NULL REFERENCES accounts(id),
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    last_price          INTEGER,                       -- centavos
    market_value        INTEGER,                       -- = current_quantity * last_price (centavos)
    unrealized_gain     INTEGER,                       -- = market_value - total_invested (centavos)
    unrealized_gain_pct REAL,                          -- = unrealized_gain / total_invested
    portfolio_weight    REAL DEFAULT 0,                -- % of total portfolio
    price_date          TEXT,                          -- date of last_price
    computed_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(user_id, account_id, asset_id)
);

CREATE INDEX IF NOT EXISTS idx_asset_valuations_user  ON asset_valuations(user_id);
CREATE INDEX IF NOT EXISTS idx_asset_valuations_asset ON asset_valuations(asset_id);

-- --------------------------------------------------------------------------
-- PORTFOLIO SNAPSHOTS
-- Daily/monthly performance snapshot.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id),
    date            TEXT NOT NULL,                  -- YYYY-MM-DD (granularity: daily)
    -- Wealth
    total_equity        INTEGER NOT NULL,           -- centavos
    cost_basis          INTEGER NOT NULL,           -- centavos
    total_deposits      INTEGER NOT NULL DEFAULT 0, -- centavos
    total_withdrawals   INTEGER NOT NULL DEFAULT 0, -- centavos
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
    dividends_month     INTEGER DEFAULT 0,          -- centavos
    dividends_year      INTEGER DEFAULT 0,          -- centavos
    dividends_total     INTEGER DEFAULT 0,          -- centavos
    -- Computed at
    computed_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_user ON portfolio_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_date ON portfolio_snapshots(date);

-- --------------------------------------------------------------------------
-- BENCHMARK SNAPSHOTS
-- Stores benchmark cumulative returns from inception date for charting.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benchmark_snapshots (
    id              TEXT PRIMARY KEY,
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
-- CASHFLOW SUMMARIES
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cashflow_summaries (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id),
    year_month      TEXT NOT NULL,                  -- 'YYYY-MM'
    total_income    INTEGER NOT NULL DEFAULT 0,     -- centavos
    total_expense   INTEGER NOT NULL DEFAULT 0,     -- centavos
    total_invested  INTEGER NOT NULL DEFAULT 0,     -- centavos
    net_cashflow    INTEGER NOT NULL DEFAULT 0,     -- centavos
    computed_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(user_id, year_month)
);
