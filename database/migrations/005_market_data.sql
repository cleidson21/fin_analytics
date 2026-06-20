-- ==========================================================================
-- MIGRATION 005 — MARKET DATA
-- FinAnalytics V3 | Context: Market Data (External, Read-Only)
-- Populated nightly by yfinance + BCB SGS API cron job.
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- ASSET PRICES
-- Daily close prices for all tracked assets (from yfinance)
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS asset_prices (
    asset_id             TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    date                 TEXT NOT NULL,              -- YYYY-MM-DD
    open_price           INTEGER,                    -- centavos
    high_price           INTEGER,                    -- centavos
    low_price            INTEGER,                    -- centavos
    close_price          INTEGER NOT NULL,           -- centavos
    adjusted_close_price INTEGER,                    -- centavos (Correction 3)
    volume               REAL,
    currency             TEXT NOT NULL DEFAULT 'BRL',
    source               TEXT NOT NULL DEFAULT 'YFINANCE',
    fetched_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (asset_id, date)
);

CREATE INDEX IF NOT EXISTS idx_asset_prices_date ON asset_prices(date);

-- --------------------------------------------------------------------------
-- BENCHMARK PRICES
-- Index values: IBOV, CDI (daily rate), IPCA, IFIX, S&P500
-- CDI and IPCA: value = daily rate in decimal (e.g. 0.1027%) - stored as INTEGER multiplied by 10^x? 
-- Wait, the prompt asked to store value as INTEGER for benchmark_prices.value. 
-- Since it's a rate, we store it multiplied by an appropriate factor if needed, or if it's points, just points * 100.
-- The backend will handle conversion.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benchmark_prices (
    ticker             TEXT NOT NULL,              -- 'CDI','IPCA','IBOV','IFIX','SPX','IDIV'
    date               TEXT NOT NULL,              -- YYYY-MM-DD
    value              INTEGER NOT NULL,           -- value representation in backend format
    accumulated_factor REAL,                       -- Correction 5
    source             TEXT NOT NULL DEFAULT 'BCB_SGS',   -- BCB_SGS | YFINANCE | MANUAL
    fetched_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_benchmark_prices_ticker ON benchmark_prices(ticker);
CREATE INDEX IF NOT EXISTS idx_benchmark_prices_date   ON benchmark_prices(date);

-- --------------------------------------------------------------------------
-- BENCHMARK METADATA
-- Registry of known benchmarks and how to fetch them
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benchmarks (
    ticker          TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    source          TEXT NOT NULL CHECK(source IN ('BCB_SGS','YFINANCE','MANUAL')),
    source_code     TEXT,    -- BCB SGS series code (e.g. 12 = CDI, 433 = IPCA)
    yfinance_ticker TEXT,    -- e.g. '^BVSP' for IBOV
    value_type      TEXT NOT NULL CHECK(value_type IN ('RATE','INDEX_POINT','CUMULATIVE')),
    currency        TEXT NOT NULL DEFAULT 'BRL',
    is_active       INTEGER NOT NULL DEFAULT 1
);

INSERT OR IGNORE INTO benchmarks (ticker, name, source, source_code, value_type) VALUES
    ('CDI',  'Taxa CDI',                          'BCB_SGS', '12',   'RATE'),
    ('IPCA', 'IPCA Mensal',                       'BCB_SGS', '433',  'RATE'),
    ('SELIC','Taxa Selic',                        'BCB_SGS', '11',   'RATE'),
    ('IBOV', 'IBOVESPA',                          'YFINANCE', NULL,   'INDEX_POINT'),
    ('IFIX', 'Índice de Fundos Imobiliários',     'YFINANCE', NULL,   'INDEX_POINT'),
    ('SPX',  'S&P 500',                           'YFINANCE', NULL,   'INDEX_POINT'),
    ('IDIV', 'Índice Dividendos BOVESPA',         'YFINANCE', NULL,   'INDEX_POINT');

UPDATE benchmarks SET yfinance_ticker = '^BVSP'  WHERE ticker = 'IBOV';
UPDATE benchmarks SET yfinance_ticker = '^IFIX'  WHERE ticker = 'IFIX';
UPDATE benchmarks SET yfinance_ticker = '^GSPC'  WHERE ticker = 'SPX';
UPDATE benchmarks SET yfinance_ticker = '^IDIV'  WHERE ticker = 'IDIV';
