-- =====================================================================================
-- FIN ANALYTICS V2 - DATABASE SCHEMA
-- =====================================================================================
-- Estrutura dividida estritamente pelos 4 Domínios (Bounded Contexts)
-- Core Finance | Wealth | Governance | AI Layer
-- =====================================================================================

-- PRAGMA foreign_keys = ON; -- Necessário habilitar no nível de conexão do Python.

-- =====================================================================================
-- 1. CORE FINANCE
-- =====================================================================================

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'VIEWER',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category_type TEXT NOT NULL, -- IN (Receita) | OUT (Despesa)
    parent_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category_id TEXT NOT NULL,
    expected_amount_cents INTEGER NOT NULL,
    billing_cycle TEXT NOT NULL DEFAULT 'MONTHLY', -- MONTHLY | YEARLY
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    category_id TEXT NOT NULL,
    limit_cents INTEGER NOT NULL,
    severity_level TEXT NOT NULL DEFAULT 'WARNING', -- GOOD | WARNING | DANGER
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

-- =====================================================================================
-- 3. GOVERNANCE (Definido aqui primeiro para permitir as FKs)
-- =====================================================================================

CREATE TABLE IF NOT EXISTS import_runs (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL DEFAULT 'PIERRE',
    file_name TEXT NOT NULL DEFAULT '',
    checksum TEXT NOT NULL DEFAULT '',
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'PENDING',
    rows_read INTEGER NOT NULL DEFAULT 0,
    rows_inserted INTEGER NOT NULL DEFAULT 0,
    rows_updated INTEGER NOT NULL DEFAULT 0,
    rows_failed INTEGER NOT NULL DEFAULT 0,
    error_log TEXT,
    preview_summary TEXT,
    created_by TEXT,
    rollback_timestamp TIMESTAMP,
    rollback_reason TEXT,
    rollback_user TEXT
);
CREATE INDEX IF NOT EXISTS idx_v2_import_runs_status ON import_runs(status);

CREATE TABLE IF NOT EXISTS import_artifacts (
    id TEXT PRIMARY KEY,
    import_run_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    mime_type TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS staging_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_run_id TEXT NOT NULL,
    source_line_no INTEGER,
    date TEXT,
    description TEXT,
    amount REAL,
    amount_cents INTEGER,
    account TEXT,
    category_inferred TEXT,
    status TEXT DEFAULT 'PENDING',
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS staging_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_run_id TEXT NOT NULL,
    source_line_no INTEGER,
    validation_status TEXT DEFAULT 'PENDING',
    validation_message TEXT,
    ticker TEXT,
    data_snapshot DATE,
    source TEXT,
    quantidade NUMERIC,
    preco_medio NUMERIC,
    total_investido NUMERIC,
    preco_atual NUMERIC,
    total_atual NUMERIC,
    ganho NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS staging_dividends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_run_id TEXT NOT NULL,
    source_line_no INTEGER,
    validation_status TEXT DEFAULT 'PENDING',
    validation_message TEXT,
    id_economico TEXT,
    source TEXT,
    ticker TEXT,
    tipo_evento TEXT,
    data_pagamento DATE,
    valor_liquido NUMERIC,
    valor_liquido_cents INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS staging_portfolio_evolution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_run_id TEXT NOT NULL,
    source_line_no INTEGER,
    validation_status TEXT DEFAULT 'PENDING',
    validation_message TEXT,
    reference_month DATE,
    rentabilidade_mensal_pct DECIMAL(7, 4),
    rentabilidade_acumulada_pct DECIMAL(7, 4),
    patrimonio_cents BIGINT,
    compras_cents BIGINT,
    vendas_cents BIGINT,
    op_finalizadas_cents BIGINT,
    proventos_cents BIGINT,
    ibov_mensal_pct DECIMAL(7, 4),
    ibov_acumulado_pct DECIMAL(7, 4),
    cdi_mensal_pct DECIMAL(7, 4),
    cdi_acumulado_pct DECIMAL(7, 4),
    ipca_mensal_pct DECIMAL(7, 4),
    ipca_acumulado_pct DECIMAL(7, 4),
    ifix_mensal_pct DECIMAL(7, 4),
    ifix_acumulado_pct DECIMAL(7, 4),
    sp500_mensal_pct DECIMAL(7, 4),
    sp500_acumulado_pct DECIMAL(7, 4),
    idiv_mensal_pct DECIMAL(7, 4),
    idiv_acumulado_pct DECIMAL(7, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS raw_events (
    id TEXT PRIMARY KEY,
    import_run_id TEXT NOT NULL,
    source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source_line_no INTEGER,
    raw_content TEXT,
    event_date DATE,
    reference_month DATE,
    amount_cents INTEGER,
    currency TEXT NOT NULL DEFAULT 'BRL',
    semantic_id TEXT NOT NULL UNIQUE, -- Restrição de Unicidade
    cross_fingerprint TEXT,
    external_id TEXT,
    metadata TEXT,
    pipeline_status TEXT NOT NULL DEFAULT 'RAW',
    match_status TEXT NOT NULL DEFAULT 'NEW',
    promoted_entity_id TEXT,
    promoted_table TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_links (
    id TEXT PRIMARY KEY,
    event_id_a TEXT NOT NULL,
    event_id_b TEXT NOT NULL,
    link_type TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    match_method TEXT NOT NULL DEFAULT 'EXACT',
    status TEXT NOT NULL DEFAULT 'AUTO_CONFIRMED',
    confirmed_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id_a) REFERENCES raw_events(id) ON DELETE CASCADE,
    FOREIGN KEY(event_id_b) REFERENCES raw_events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    field_changes TEXT,
    changed_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================================
-- CORE FINANCE CONTINUAÇÃO (Depende de Governance)
-- =====================================================================================

CREATE TABLE IF NOT EXISTS transactions (
    id_economico TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    origin TEXT,
    domain TEXT,
    import_run_id TEXT NOT NULL,
    source_line_no INTEGER,
    data DATE NOT NULL,
    descricao_original TEXT NOT NULL,
    descricao_normalizada TEXT NOT NULL,
    valor NUMERIC NOT NULL,
    valor_cents INTEGER,
    identificador_externo TEXT,
    category_id TEXT, -- FK NOVA
    macro_categoria TEXT, -- Legado opcional
    sub_categoria TEXT, -- Legado opcional
    subnatureza TEXT NOT NULL DEFAULT 'INDEFINIDO',
    natureza TEXT NOT NULL,
    perfil TEXT NOT NULL,
    classificacao_fonte TEXT NOT NULL DEFAULT 'ETL',
    applied_rule_id TEXT,
    parcelamento TEXT,
    observacao TEXT,
    created_by TEXT,
    updated_by TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_v2_transactions_data ON transactions(data);

-- =====================================================================================
-- 2. WEALTH
-- =====================================================================================

CREATE TABLE IF NOT EXISTS benchmarks (
    id TEXT PRIMARY KEY,
    reference_date DATE NOT NULL,
    type TEXT NOT NULL, -- CDI | IBOV | IPCA | S&P500
    value_pct DECIMAL(7, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(reference_date, type)
);

CREATE TABLE IF NOT EXISTS positions (
    ticker TEXT NOT NULL,
    data_snapshot DATE NOT NULL,
    source TEXT NOT NULL,
    quantidade NUMERIC NOT NULL,
    preco_medio NUMERIC NOT NULL,
    total_investido NUMERIC NOT NULL,
    preco_atual NUMERIC NOT NULL,
    total_atual NUMERIC NOT NULL,
    ganho NUMERIC NOT NULL,
    classe_ativo TEXT,
    observacao TEXT,
    import_run_id TEXT NOT NULL,
    source_line_no INTEGER,
    created_by TEXT,
    updated_by TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, data_snapshot),
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dividends (
    id_economico TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    ticker TEXT NOT NULL,
    tipo_evento TEXT NOT NULL,
    data_pagamento DATE NOT NULL,
    valor_liquido NUMERIC NOT NULL,
    valor_liquido_cents INTEGER,
    observacao TEXT,
    import_run_id TEXT NOT NULL,
    source_line_no INTEGER,
    created_by TEXT,
    updated_by TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS portfolio_evolution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_month DATE NOT NULL UNIQUE,
    rentabilidade_mensal_pct DECIMAL(7, 4) DEFAULT 0,
    rentabilidade_acumulada_pct DECIMAL(7, 4) DEFAULT 0,
    patrimonio_cents BIGINT NOT NULL DEFAULT 0,
    compras_cents BIGINT NOT NULL DEFAULT 0,
    vendas_cents BIGINT NOT NULL DEFAULT 0,
    op_finalizadas_cents BIGINT NOT NULL DEFAULT 0,
    proventos_cents BIGINT NOT NULL DEFAULT 0,
    import_run_id TEXT NOT NULL,
    source_line_no INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE
);

-- =====================================================================================
-- 4. AI LAYER
-- =====================================================================================

CREATE TABLE IF NOT EXISTS rules (
    id TEXT PRIMARY KEY,
    rule_type TEXT NOT NULL,
    pattern TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT,
    confidence_score REAL NOT NULL DEFAULT 1.0,
    evidence_count INTEGER NOT NULL DEFAULT 1,
    hit_count INTEGER NOT NULL DEFAULT 1,
    miss_count INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'OBSERVING',
    version INTEGER NOT NULL DEFAULT 1,
    superseded_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    status_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prompt_versions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS ai_runs (
    id TEXT PRIMARY KEY,
    import_run_id TEXT,
    prompt_version_id TEXT NOT NULL,
    model TEXT NOT NULL,
    input_text TEXT NOT NULL,
    output_json TEXT,
    confidence REAL,
    latency_ms INTEGER,
    tokens_input INTEGER,
    tokens_output INTEGER,
    estimated_cost REAL,
    status TEXT NOT NULL DEFAULT 'SUCCESS',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE SET NULL,
    FOREIGN KEY(prompt_version_id) REFERENCES prompt_versions(id) ON DELETE RESTRICT
);
