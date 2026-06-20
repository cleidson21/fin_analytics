-- ==========================================================================
-- MIGRATION 001 — CORE IDENTITY
-- FinAnalytics V3 | Context: Identity & Banking
-- CORRECTIONS: UUID generation removed (backend responsibility)
-- ==========================================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- USERS
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- --------------------------------------------------------------------------
-- INSTITUTIONS
-- Nubank (0260), Banco do Brasil (0001), B3/NuInvest, CAIXA (0104), etc.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS institutions (
    id          TEXT PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,   -- BACEN ISPB code or mnemonic (e.g. '0260', 'B3', 'NUINVEST')
    name        TEXT NOT NULL,
    short_name  TEXT,
    type        TEXT NOT NULL CHECK(type IN ('BANK','BROKER','CRYPTO_EXCHANGE','OTHER')),
    country     TEXT NOT NULL DEFAULT 'BR',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- --------------------------------------------------------------------------
-- ACCOUNTS
-- One user may have multiple accounts: checking, brokerage, credit-card holder
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accounts (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    institution_id  TEXT NOT NULL REFERENCES institutions(id),
    name            TEXT NOT NULL,
    type            TEXT NOT NULL CHECK(type IN ('CHECKING','BROKERAGE','CREDIT','SAVINGS')),
    currency        TEXT NOT NULL DEFAULT 'BRL',
    is_active       INTEGER NOT NULL DEFAULT 1,
    external_id     TEXT,               -- e.g. account number from bank
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);

-- --------------------------------------------------------------------------
-- SEED: Known institutions used in base files
-- --------------------------------------------------------------------------
INSERT OR IGNORE INTO institutions (id, code, name, short_name, type) VALUES
    ('inst-nubank-00001', '0260', 'Nu Pagamentos S.A.', 'Nubank', 'BANK'),
    ('inst-nuinvest-0001', 'NUINVEST', 'NuInvest Corretora de Valores S.A.', 'NuInvest', 'BROKER'),
    ('inst-bb-000000001', '0001', 'Banco do Brasil S.A.', 'BB', 'BANK'),
    ('inst-caixa-000104', '0104', 'Caixa Econômica Federal', 'CEF', 'BANK'),
    ('inst-bradesco-0237', '0237', 'Banco Bradesco S.A.', 'Bradesco', 'BANK'),
    ('inst-itau-000341', '0341', 'Itaú Unibanco S.A.', 'Itaú', 'BANK'),
    ('inst-b3-00000001', 'B3', 'B3 S.A. — Brasil, Bolsa, Balcão', 'B3', 'BROKER'),
    ('inst-mercado-0323', '0323', 'Mercado Pago IP Ltda.', 'MercadoPago', 'BANK');
