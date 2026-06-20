-- ==========================================================================
-- MIGRATION 007 — AI & CLASSIFICATION ENGINE
-- FinAnalytics V3 | Context: AI (Classification Pipeline)
-- ==========================================================================

PRAGMA foreign_keys=ON;

-- --------------------------------------------------------------------------
-- CLASSIFICATION RULES
-- Layer 1 & 2: Deterministic rules evaluated first, ordered by priority.
-- match_type: REGEX = pattern match; EXACT = normalized string exact match
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS classification_rules (
    id              TEXT PRIMARY KEY,
    match_type      TEXT NOT NULL CHECK(match_type IN ('REGEX','EXACT','PREFIX','CONTAINS')),
    pattern         TEXT NOT NULL,              -- the regex or string to match against description
    merchant_id     TEXT REFERENCES merchants(id),
    category_id     TEXT REFERENCES categories(id),
    priority        INTEGER NOT NULL DEFAULT 100,   -- lower number = evaluated first
    is_active       INTEGER NOT NULL DEFAULT 1,
    hit_count       INTEGER NOT NULL DEFAULT 0,     -- how many times this rule fired
    source          TEXT NOT NULL DEFAULT 'MANUAL' CHECK(source IN ('MANUAL','PIERRE_IMPORT','LLM_FEEDBACK','SYSTEM')),
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_rules_priority  ON classification_rules(priority) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS idx_rules_type      ON classification_rules(match_type) WHERE is_active = 1;

-- --------------------------------------------------------------------------
-- LEARNING EXAMPLES
-- Layer 3: Vector search corpus. Embeddings stored as JSON array of floats.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS learning_examples (
    id                  TEXT PRIMARY KEY,
    original_description TEXT NOT NULL,         -- raw bank string
    normalized_input    TEXT NOT NULL,          -- cleaned version used for embedding
    merchant_id         TEXT REFERENCES merchants(id),
    category_id         TEXT REFERENCES categories(id),
    embedding           BLOB,                   -- float32 array stored as binary (numpy tobytes)
    embedding_model     TEXT DEFAULT 'all-MiniLM-L6-v2',
    source              TEXT NOT NULL DEFAULT 'USER_FEEDBACK' CHECK(source IN (
                            'USER_FEEDBACK','LLM_FEEDBACK','PIERRE_IMPORT','SYSTEM'
                        )),
    confidence          REAL DEFAULT 1.0,       -- 0..1, LLM-generated examples have lower confidence
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_learning_examples_merchant  ON learning_examples(merchant_id);
CREATE INDEX IF NOT EXISTS idx_learning_examples_category  ON learning_examples(category_id);

-- --------------------------------------------------------------------------
-- AI PROMPTS
-- Versioned prompt templates for LLM classification (Layer 4)
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_prompts (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,       -- 'classify_transaction', 'extract_merchant', etc.
    description TEXT,
    template    TEXT NOT NULL,              -- Jinja2 / f-string template
    model       TEXT NOT NULL DEFAULT 'gemini-1.5-flash',
    version     INTEGER NOT NULL DEFAULT 1,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- --------------------------------------------------------------------------
-- AI RUNS
-- Log of every LLM call made by the classification engine
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_runs (
    id              TEXT PRIMARY KEY,
    prompt_id       TEXT REFERENCES ai_prompts(id),
    input_text      TEXT NOT NULL,
    output_json     TEXT,                   -- raw JSON response from LLM
    merchant_id     TEXT REFERENCES merchants(id),     -- resolved merchant
    category_id     TEXT REFERENCES categories(id),    -- resolved category
    confidence      REAL,                   -- LLM-provided confidence 0..1
    model           TEXT,
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    cost_usd        REAL,                   -- estimated cost of this call
    latency_ms      INTEGER,
    status          TEXT NOT NULL CHECK(status IN ('SUCCESS','FAILED','FALLBACK')),
    run_id          TEXT REFERENCES import_runs(id),
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_ai_runs_date   ON ai_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_runs_status ON ai_runs(status);

-- --------------------------------------------------------------------------
-- CLASSIFICATION FEEDBACK
-- When user corrects an AI classification, the feedback is logged here.
-- This automatically generates a new learning_example (handled by app layer).
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS classification_feedback (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id),
    entity_type     TEXT NOT NULL,          -- 'transaction', 'invoice_item'
    entity_id       TEXT NOT NULL,
    original_desc   TEXT NOT NULL,
    ai_run_id       TEXT REFERENCES ai_runs(id),
    ai_merchant_id  TEXT REFERENCES merchants(id),     -- what AI guessed
    ai_category_id  TEXT REFERENCES categories(id),
    correct_merchant_id TEXT REFERENCES merchants(id), -- what user corrected to
    correct_category_id TEXT REFERENCES categories(id),
    propagate_rule  INTEGER NOT NULL DEFAULT 1,        -- 1 = create classification_rule from this
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_feedback_entity ON classification_feedback(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user   ON classification_feedback(user_id);

-- --------------------------------------------------------------------------
-- SEED: Bootstrap classification rules from Pierre data analysis
-- --------------------------------------------------------------------------
INSERT OR IGNORE INTO classification_rules (id, match_type, pattern, category_id, priority, source) VALUES
    ('rule-pix-out-001',   'REGEX',    '(?i)Transferência enviada pelo Pix',   'cat-xfer-000001', 10, 'SYSTEM'),
    ('rule-pix-in-001',    'REGEX',    '(?i)Transferência (R|r)ecebida',       'cat-xfer-000001', 10, 'SYSTEM'),
    ('rule-own-xfer-001',  'REGEX',    '(?i)Entre contas|mesma titularidade',  'cat-xfer-int-0001',5, 'SYSTEM'),
    ('rule-rdb-apply-001', 'REGEX',    '(?i)Aplicação RDB|Aplicação - Tesouro','cat-inv-000001',   5, 'SYSTEM'),
    ('rule-rdb-resgt-001', 'REGEX',    '(?i)Resgate RDB',                      'cat-invest-inc-01',5, 'SYSTEM'),
    ('rule-nuinvest-001',  'REGEX',    '(?i)Transferência de saldo NuInvest',  'cat-invest-inc-01',5, 'SYSTEM'),
    ('rule-irrf-001',      'REGEX',    '(?i)IRRF sobre resgate',               'cat-tax-000001',   5, 'SYSTEM'),
    ('rule-fatura-001',    'REGEX',    '(?i)Pagamento de fatura',              'cat-xfer-int-0001',5, 'SYSTEM'),
    ('rule-stock-buy-001', 'REGEX',    '(?i)Compra de Renda Variável',         'cat-inv-000001',   5, 'SYSTEM'),
    ('rule-energy-001',    'CONTAINS', 'NEOENERGIA',                           'cat-house-el-0001',20,'SYSTEM'),
    ('rule-energy-002',    'CONTAINS', 'COELBA',                               'cat-house-el-0001',20,'SYSTEM'),
    ('rule-telecom-001',   'REGEX',    '(?i)^Multi$',                          'cat-house-tel-001',20,'SYSTEM'),
    ('rule-spotify-001',   'CONTAINS', 'Spotify',                              'cat-svc-strea-001',20,'SYSTEM'),
    ('rule-shopee-001',    'CONTAINS', 'Shopee',                               'cat-shop-on-0001', 20,'SYSTEM'),
    ('rule-mercadol-001',  'CONTAINS', 'Mercadolivre',                         'cat-shop-on-0001', 20,'SYSTEM'),
    ('rule-gambling-001',  'REGEX',    '(?i)KAIZEN GAMING|Order O-',           'cat-gamb-000001',  15,'SYSTEM'),
    ('rule-iof-001',       'CONTAINS', 'IOF de compra',                        'cat-tax-000001',   10,'SYSTEM'),
    ('rule-natura-001',    'CONTAINS', 'NATURA',                               'cat-shop-on-0001', 20,'SYSTEM');
