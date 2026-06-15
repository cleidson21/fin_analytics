-- ==========================================================================
-- MIGRATION 003 — CREDIT CARD MODULE
-- FinAnalytics V3 | Context: Credit Management
-- Rule: Invoice payment in transactions does NOT duplicate invoice_items.
--       invoice_items represent spending under accrual basis.
--       The cash-basis impact happens only when invoice is paid (transaction).
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- CREDIT CARDS
-- Linked to a CREDIT type account
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS credit_cards (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    account_id      TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,          -- "Nubank Gold", "Nubank Ultravioleta"
    last_four       TEXT,                   -- last 4 digits
    closing_day     INTEGER NOT NULL,       -- day of month the bill closes
    due_day         INTEGER NOT NULL,       -- day of month the bill is due
    credit_limit    REAL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_credit_cards_account ON credit_cards(account_id);

-- --------------------------------------------------------------------------
-- INVOICES (Faturas)
-- One per billing cycle per credit card
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    credit_card_id  TEXT NOT NULL REFERENCES credit_cards(id),
    closing_date    TEXT NOT NULL,          -- ISO 8601 date
    due_date        TEXT NOT NULL,          -- payment due date
    total_amount    REAL NOT NULL DEFAULT 0,
    paid_amount     REAL NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN','CLOSED','PAID','PARTIAL')),
    payment_transaction_id TEXT REFERENCES transactions(id),  -- the OUT transaction that paid this
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(credit_card_id, closing_date)
);

CREATE INDEX IF NOT EXISTS idx_invoices_card   ON invoices(credit_card_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);

-- --------------------------------------------------------------------------
-- INSTALLMENT PLANS
-- One plan per purchase: "Petlove 2x R$218,32" creates 1 plan + 2 installments
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS installment_plans (
    id                  TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    credit_card_id      TEXT NOT NULL REFERENCES credit_cards(id),
    merchant_id         TEXT REFERENCES merchants(id),
    category_id         TEXT REFERENCES categories(id),
    description         TEXT NOT NULL,          -- raw original description
    purchase_date       TEXT NOT NULL,          -- when the purchase happened
    total_amount        REAL NOT NULL,          -- total across all installments
    total_installments  INTEGER NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_installment_plans_card ON installment_plans(credit_card_id);

-- --------------------------------------------------------------------------
-- INSTALLMENTS
-- Each individual monthly installment within a plan
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS installments (
    id                  TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    installment_plan_id TEXT NOT NULL REFERENCES installment_plans(id) ON DELETE CASCADE,
    installment_number  INTEGER NOT NULL,       -- 1, 2, 3 ... total_installments
    amount              REAL NOT NULL,
    expected_date       TEXT NOT NULL,          -- YYYY-MM-DD when it will appear on invoice
    status              TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','BILLED','PAID')),
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    UNIQUE(installment_plan_id, installment_number)
);

CREATE INDEX IF NOT EXISTS idx_installments_plan   ON installments(installment_plan_id);
CREATE INDEX IF NOT EXISTS idx_installments_date   ON installments(expected_date);

-- --------------------------------------------------------------------------
-- INVOICE ITEMS
-- Individual line items within a billed invoice
-- Optionally linked to an installment (if part of an installment plan)
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoice_items (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    invoice_id      TEXT NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    installment_id  TEXT REFERENCES installments(id),   -- NULL if not an installment purchase
    merchant_id     TEXT REFERENCES merchants(id),
    category_id     TEXT REFERENCES categories(id),
    description     TEXT NOT NULL,
    amount          REAL NOT NULL,
    date            TEXT NOT NULL,                      -- the transaction date on the card
    run_id          TEXT,                               -- import_runs.id
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice     ON invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_items_installment ON invoice_items(installment_id);
CREATE INDEX IF NOT EXISTS idx_invoice_items_merchant    ON invoice_items(merchant_id);
