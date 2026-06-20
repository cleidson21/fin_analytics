-- ==========================================================================
-- MIGRATION 002 — CASHFLOW LEDGER
-- FinAnalytics V3 | Context: Cashflow (Immutable Ledger)
-- CORRECTIONS:
--   - UUID generation removed (backend responsibility)
--   - transactions.amount: REAL → INTEGER (centavos)
--   - transfers.fee_amount: REAL → INTEGER (centavos)
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- CATEGORIES
-- Hierarchical tree: parent_id = NULL means top-level
-- type: EXPENSE | INCOME | TRANSFER | INVESTMENT | IGNORE
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id          TEXT PRIMARY KEY,
    parent_id   TEXT REFERENCES categories(id),
    name        TEXT NOT NULL,
    slug        TEXT NOT NULL UNIQUE,   -- machine-readable key e.g. 'food.delivery'
    type        TEXT NOT NULL CHECK(type IN ('EXPENSE','INCOME','TRANSFER','INVESTMENT','IGNORE')),
    icon        TEXT,                   -- emoji or icon name for UI
    color       TEXT,                   -- hex color for charts
    is_system   INTEGER NOT NULL DEFAULT 0,  -- 1 = cannot be deleted by user
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_slug   ON categories(slug);

-- --------------------------------------------------------------------------
-- MERCHANTS
-- Normalized counterparties: shops, services, people (PIX recipients)
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS merchants (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,          -- cleaned display name: "Shopee"
    normalized_name TEXT NOT NULL UNIQUE,   -- lowercase, no spaces: "shopee"
    category_id     TEXT REFERENCES categories(id),  -- default category for this merchant
    cnpj            TEXT,                   -- for business recipients
    is_person       INTEGER NOT NULL DEFAULT 0,  -- 1 = physical person (PIX CPF)
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_merchants_normalized ON merchants(normalized_name);

-- --------------------------------------------------------------------------
-- TRANSACTIONS
-- THE IMMUTABLE LEDGER. Never UPDATE, never DELETE.
-- id = idempotent fingerprint from bank (UUID from Nubank, or SHA-256 hash)
-- amount: stored in centavos (INTEGER). R$ 150,23 → 15023
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id                   TEXT PRIMARY KEY,     -- bank-provided UUID or SHA-256 fingerprint
    account_id           TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    merchant_id          TEXT REFERENCES merchants(id),
    category_id          TEXT REFERENCES categories(id),
    date                 TEXT NOT NULL,         -- ISO 8601: YYYY-MM-DD
    amount               INTEGER NOT NULL,      -- in centavos. Always positive. Sign from 'type'.
    type                 TEXT NOT NULL CHECK(type IN ('IN','OUT')),
    original_description TEXT NOT NULL,         -- raw bank string, never modified
    normalized_desc      TEXT,                  -- cleaned description after processing
    source               TEXT NOT NULL CHECK(source IN (
                             'NUBANK_CSV','NUBANK_OFX','PIERRE_CSV',
                             'MANUAL','SYSTEM','BROKER_NOTE','CREDIT_CARD_CSV'
                         )),
    is_transfer          INTEGER NOT NULL DEFAULT 0,  -- part of an internal transfer?
    is_investment        INTEGER NOT NULL DEFAULT 0,  -- investment movement?
    is_ignored           INTEGER NOT NULL DEFAULT 0,  -- excluded from cash reports
    needs_review         INTEGER NOT NULL DEFAULT 0,  -- flagged for user review
    run_id               TEXT,    -- import_runs.id that created this record
    created_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    -- NO updated_at: immutable. Create correction events instead.
);

CREATE INDEX IF NOT EXISTS idx_transactions_account  ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date     ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant ON transactions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_run      ON transactions(run_id);

-- --------------------------------------------------------------------------
-- TRANSFERS
-- Links two transactions (OUT from account A, IN to account B)
-- fee_amount: in centavos
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transfers (
    id                  TEXT PRIMARY KEY,
    out_transaction_id  TEXT NOT NULL UNIQUE REFERENCES transactions(id),
    in_transaction_id   TEXT NOT NULL UNIQUE REFERENCES transactions(id),
    fee_amount          INTEGER NOT NULL DEFAULT 0,  -- in centavos
    notes               TEXT,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- --------------------------------------------------------------------------
-- SEED: System categories (cannot be deleted)
-- --------------------------------------------------------------------------
INSERT OR IGNORE INTO categories (id, name, slug, type, icon, is_system) VALUES
    -- TOP LEVEL EXPENSE
    ('cat-food-000001',   'Alimentacao',        'food',               'EXPENSE', 'fork_knife',     1),
    ('cat-trans-000001',  'Transporte',         'transport',          'EXPENSE', 'car',            1),
    ('cat-house-000001',  'Moradia',            'housing',            'EXPENSE', 'house',          1),
    ('cat-health-000001', 'Saude',              'health',             'EXPENSE', 'hospital',       1),
    ('cat-edu-000001',    'Educacao',           'education',          'EXPENSE', 'books',          1),
    ('cat-entert-000001', 'Entretenimento',     'entertainment',      'EXPENSE', 'ticket',         1),
    ('cat-shop-000001',   'Compras',            'shopping',           'EXPENSE', 'bag',            1),
    ('cat-svc-000001',    'Servicos',           'services',           'EXPENSE', 'box',            1),
    ('cat-gamb-000001',   'Apostas',            'gambling',           'EXPENSE', 'dice',           1),
    ('cat-tax-000001',    'Impostos e Taxas',   'taxes',              'EXPENSE', 'clipboard',      1),
    -- TOP LEVEL INCOME
    ('cat-salary-000001', 'Salario',            'salary',             'INCOME',  'briefcase',      1),
    ('cat-invest-inc-01', 'Renda de Investimentos', 'investment_income','INCOME', 'money_bag',     1),
    ('cat-refund-000001', 'Estornos e Reembolsos', 'refunds',         'INCOME',  'arrow_left',     1),
    -- TRANSFER & SPECIAL
    ('cat-xfer-000001',   'Transferencias',     'transfers',          'TRANSFER','arrows',         1),
    ('cat-inv-000001',    'Investimentos',      'investments',        'INVESTMENT','chart_up',     1),
    ('cat-ignore-000001', 'Ignorar',            'ignore',             'IGNORE',  'ban',            1),
    -- SUB-CATEGORIES
    ('cat-food-del-0001', 'Delivery',           'food.delivery',      'EXPENSE', 'scooter',        1),
    ('cat-food-sup-0001', 'Supermercado',       'food.supermarket',   'EXPENSE', 'cart',           1),
    ('cat-food-rest-001', 'Restaurante',        'food.restaurant',    'EXPENSE', 'utensils',       1),
    ('cat-house-el-0001', 'Eletricidade',       'housing.electricity','EXPENSE', 'lightning',      1),
    ('cat-house-tel-001', 'Telecomunicacao',    'housing.telecom',    'EXPENSE', 'antenna',        1),
    ('cat-shop-on-0001',  'Compras Online',     'shopping.online',    'EXPENSE', 'laptop',         1),
    ('cat-svc-strea-001', 'Streaming',          'services.streaming', 'EXPENSE', 'play',           1),
    ('cat-xfer-int-0001', 'Entre Contas Proprias','transfers.internal','TRANSFER','refresh',       1);

-- Update parent_id for sub-categories
UPDATE categories SET parent_id = 'cat-food-000001'  WHERE slug IN ('food.delivery','food.supermarket','food.restaurant');
UPDATE categories SET parent_id = 'cat-house-000001' WHERE slug IN ('housing.electricity','housing.telecom');
UPDATE categories SET parent_id = 'cat-shop-000001'  WHERE slug = 'shopping.online';
UPDATE categories SET parent_id = 'cat-svc-000001'   WHERE slug = 'services.streaming';
UPDATE categories SET parent_id = 'cat-xfer-000001'  WHERE slug = 'transfers.internal';
