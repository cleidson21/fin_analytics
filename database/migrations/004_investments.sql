-- ==========================================================================
-- MIGRATION 004 — INVESTMENTS MODULE
-- FinAnalytics V3 | Context: Investments (Wealth)
-- Covers: assets, broker notes, trades, corporate actions, dividends
-- Principle: price average is COMPUTED from trades, never stored directly.
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- ASSETS
-- Master catalog of all investable instruments
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assets (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    ticker          TEXT NOT NULL UNIQUE,   -- BBAS3, MXRF11, IVV, BTC
    name            TEXT,                   -- full name: "Banco do Brasil S.A."
    asset_class     TEXT NOT NULL CHECK(asset_class IN (
                        'STOCK',        -- ações BR: BBAS3, VALE3
                        'FII',          -- fundos imobiliários: MXRF11, KNCR11
                        'BDR',          -- BDRs: IVV, AGG, VXUS, MORT
                        'ETF',          -- ETFs BR
                        'STOCK_US',     -- ações US: BABA
                        'FIXED_INCOME', -- Tesouro, RDB, CDB, LCI
                        'CRYPTO',       -- BTC, ETH
                        'OTHER'
                    )),
    sector          TEXT,                   -- Papeis, FII-Misto, Shoppings, Petróleo, etc.
    currency        TEXT NOT NULL DEFAULT 'BRL',
    yfinance_ticker TEXT,                   -- ticker as yfinance knows it (e.g. "BBAS3.SA", "^BVSP")
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_assets_ticker      ON assets(ticker);
CREATE INDEX IF NOT EXISTS idx_assets_asset_class ON assets(asset_class);

-- --------------------------------------------------------------------------
-- BROKER NOTES (Notas de Corretagem)
-- The official settlement document from B3.
-- One note can contain multiple trades.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS broker_notes (
    id                  TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    account_id          TEXT NOT NULL REFERENCES accounts(id),
    note_number         TEXT NOT NULL,          -- sequential number on document
    note_date           TEXT NOT NULL,          -- trade date (D+0), ISO 8601
    settlement_date     TEXT,                   -- D+2 settlement date
    brokerage_fee       REAL NOT NULL DEFAULT 0,    -- taxa de corretagem
    clearing_fee        REAL NOT NULL DEFAULT 0,    -- taxa de liquidação CBLC
    registration_fee    REAL NOT NULL DEFAULT 0,    -- taxa de registro
    iss_tax             REAL NOT NULL DEFAULT 0,    -- ISS sobre corretagem
    irrf_tax            REAL NOT NULL DEFAULT 0,    -- IRRF (day-trade only)
    other_fees          REAL NOT NULL DEFAULT 0,
    total_fees          REAL GENERATED ALWAYS AS (
                            brokerage_fee + clearing_fee + registration_fee + iss_tax + irrf_tax + other_fees
                        ) STORED,
    source              TEXT NOT NULL DEFAULT 'PDF' CHECK(source IN ('PDF','B3_API','MANUAL','MYPROFIT_IMPORT')),
    raw_file_path       TEXT,                   -- relative path to original PDF if parsed
    run_id              TEXT,                   -- import_runs.id
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(account_id, note_number, note_date)
);

CREATE INDEX IF NOT EXISTS idx_broker_notes_account ON broker_notes(account_id);
CREATE INDEX IF NOT EXISTS idx_broker_notes_date    ON broker_notes(note_date);

-- --------------------------------------------------------------------------
-- TRADES
-- Individual buy/sell executions within a broker note.
-- quantity uses REAL to support fractional shares (IVV=0.88, etc.)
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trades (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    broker_note_id  TEXT REFERENCES broker_notes(id) ON DELETE SET NULL,  -- NULL = manual/legacy entry
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    account_id      TEXT NOT NULL REFERENCES accounts(id),
    type            TEXT NOT NULL CHECK(type IN ('BUY','SELL')),
    trade_date      TEXT NOT NULL,              -- ISO 8601
    quantity        REAL NOT NULL CHECK(quantity > 0),
    unit_price      REAL NOT NULL CHECK(unit_price >= 0),
    gross_value     REAL GENERATED ALWAYS AS (quantity * unit_price) STORED,
    fees_allocated  REAL NOT NULL DEFAULT 0,    -- prorated share of broker_note total fees
    net_value       REAL GENERATED ALWAYS AS (
                        CASE WHEN type = 'BUY'
                             THEN (quantity * unit_price) + fees_allocated
                             ELSE (quantity * unit_price) - fees_allocated
                        END
                    ) STORED,
    source          TEXT NOT NULL DEFAULT 'BROKER_NOTE' CHECK(source IN (
                        'BROKER_NOTE','MANUAL','MYPROFIT_IMPORT','B3_API'
                    )),
    run_id          TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_trades_asset     ON trades(asset_id);
CREATE INDEX IF NOT EXISTS idx_trades_account   ON trades(account_id);
CREATE INDEX IF NOT EXISTS idx_trades_date      ON trades(trade_date);
CREATE INDEX IF NOT EXISTS idx_trades_type      ON trades(type);

-- --------------------------------------------------------------------------
-- CORPORATE ACTIONS
-- Splits, reverse splits, bonifications that adjust historical quantities/prices.
-- CRITICAL: position engine must apply these when rebuilding cost basis.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corporate_actions (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    asset_id    TEXT NOT NULL REFERENCES assets(id),
    type        TEXT NOT NULL CHECK(type IN (
                    'SPLIT',            -- desdobramento: qty * ratio, price / ratio
                    'REVERSE_SPLIT',    -- grupamento: qty / ratio, price * ratio
                    'BONUS_SHARE',      -- bonificação: receives extra shares
                    'SUBSCRIPTION',     -- subscrição: right to buy more shares
                    'SPINOFF'           -- separação de empresa
                )),
    ex_date     TEXT NOT NULL,          -- the date the event takes effect
    ratio       REAL NOT NULL,          -- 4.0 = 1 share becomes 4; 0.1 = 10 shares become 1
    description TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_corporate_actions_asset   ON corporate_actions(asset_id);
CREATE INDEX IF NOT EXISTS idx_corporate_actions_ex_date ON corporate_actions(ex_date);

-- --------------------------------------------------------------------------
-- DIVIDENDS
-- Income events: dividends, JCP, amortization, rent (FII)
-- amount = TOTAL received (quantity_held * value_per_share), net of tax
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dividends (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    asset_id        TEXT NOT NULL REFERENCES assets(id),
    account_id      TEXT NOT NULL REFERENCES accounts(id),
    type            TEXT NOT NULL CHECK(type IN (
                        'DIVIDEND',         -- dividendo isento (BR stocks, FIIs)
                        'JCP',              -- juros sobre capital próprio (15% IRRF)
                        'AMORTIZATION',     -- amortização de capital (FIIs)
                        'FII_RENT',         -- rendimento mensal de FII (isenção PF)
                        'FOREIGN_DIVIDEND'  -- dividendo de BDR/ação US
                    )),
    ex_date         TEXT NOT NULL,          -- data COM (last day to be entitled)
    payment_date    TEXT NOT NULL,          -- data do pagamento efetivo
    quantity_held   REAL NOT NULL,          -- shares held on ex_date
    value_per_share REAL NOT NULL,          -- R$ per share
    gross_amount    REAL NOT NULL,          -- = quantity_held * value_per_share
    irrf_tax        REAL NOT NULL DEFAULT 0, -- 15% on JCP
    net_amount      REAL GENERATED ALWAYS AS (gross_amount - irrf_tax) STORED,
    transaction_id  TEXT REFERENCES transactions(id), -- linked cashflow IN if credited to account
    source          TEXT NOT NULL DEFAULT 'BROKER_NOTE' CHECK(source IN (
                        'BROKER_NOTE','MYPROFIT_IMPORT','MANUAL','B3_API'
                    )),
    run_id          TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(asset_id, account_id, ex_date, type)
);

CREATE INDEX IF NOT EXISTS idx_dividends_asset        ON dividends(asset_id);
CREATE INDEX IF NOT EXISTS idx_dividends_account      ON dividends(account_id);
CREATE INDEX IF NOT EXISTS idx_dividends_payment_date ON dividends(payment_date);

-- --------------------------------------------------------------------------
-- SEED: Known assets from arquivos_base
-- --------------------------------------------------------------------------
INSERT OR IGNORE INTO assets (ticker, name, asset_class, sector, yfinance_ticker) VALUES
    -- FIIs (Papeis)
    ('MXRF11', 'Maxi Renda FII',              'FII', 'Papeis',          'MXRF11.SA'),
    ('KNCR11', 'Kinea Rendimentos Imob. FII', 'FII', 'Papeis',          'KNCR11.SA'),
    ('RZAK11', 'Riza Akin FII',               'FII', 'Papeis',          'RZAK11.SA'),
    ('RBRY11', 'RBR High Grade FII',          'FII', 'Papeis',          'RBRY11.SA'),
    ('BTHF11', 'BTG Pactual High Yield FII',  'FII', 'Fundo de Fundos', 'BTHF11.SA'),
    -- FIIs (Misto)
    ('HGRU11', 'CSHG Renda Urbana FII',       'FII', 'Misto',           'HGRU11.SA'),
    ('XPML11', 'XP Malls FII',                'FII', 'Shoppings',       'XPML11.SA'),
    ('JSRE11', 'JS Real Estate FII',          'FII', 'Misto',           'JSRE11.SA'),
    ('TRXF11', 'TRX Real Estate FII',         'FII', 'Misto',           'TRXF11.SA'),
    -- Ações BR
    ('PRIO3', 'Petro Rio S.A.',               'STOCK', 'Petróleo',      'PRIO3.SA'),
    ('VALE3', 'Vale S.A.',                    'STOCK', 'Materiais Básicos','VALE3.SA'),
    ('BBSE3', 'BB Seguridade S.A.',           'STOCK', 'Serviços Financeiros','BBSE3.SA'),
    ('BBAS3', 'Banco do Brasil S.A.',         'STOCK', 'Serviços Financeiros','BBAS3.SA'),
    ('KLBN4', 'Klabin S.A.',                  'STOCK', 'Materiais Básicos','KLBN4.SA'),
    ('TAEE11', 'Transmissora Aliança de Energia Elétrica','STOCK','Utilidade Pública','TAEE11.SA'),
    ('GGBR4', 'Gerdau S.A.',                  'STOCK', 'Materiais Básicos','GGBR4.SA'),
    -- BDRs / ETFs US
    ('IVV',   'iShares Core S&P 500 ETF',     'BDR',  'Outros',         'IVV'),
    ('AGG',   'iShares Core US Aggregate Bond','BDR', 'Outros',          'AGG'),
    ('VXUS',  'Vanguard Total International', 'BDR',  'Outros',          'VXUS'),
    ('MORT',  'VanEck Mortgage REIT Income',  'BDR',  'Outros',          'MORT'),
    ('BABA',  'Alibaba Group Holding Ltd.',   'BDR',  'Diversos',        'BABA'),
    -- Renda Fixa
    ('RDB-100-CDI', 'RDB Pós 100% CDI',       'FIXED_INCOME', 'RDB', NULL),
    ('RDB-120-CDI', 'RDB Pós 120% CDI',       'FIXED_INCOME', 'RDB', NULL),
    ('TESOURO-SELIC-2031', 'Tesouro Selic 2031','FIXED_INCOME','Tesouro Direto', NULL),
    ('TESOURO-SELIC-2029', 'Tesouro Selic 2029','FIXED_INCOME','Tesouro Direto', NULL),
    ('TESOURO-IPCA-2035',  'Tesouro IPCA+ 2035','FIXED_INCOME','Tesouro Direto', NULL),
    -- Cripto
    ('BTC',   'Bitcoin',                      'CRYPTO','Criptomoeda',    'BTC-USD');
