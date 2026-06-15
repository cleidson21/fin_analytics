-- FASE 3: GOVERNANCE DB SCHEMA

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

CREATE INDEX IF NOT EXISTS idx_gov_import_runs_status ON import_runs(status);
CREATE INDEX IF NOT EXISTS idx_gov_import_runs_started_at ON import_runs(started_at);

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

CREATE INDEX IF NOT EXISTS idx_gov_import_artifacts_run ON import_artifacts(import_run_id);

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

CREATE INDEX IF NOT EXISTS idx_gov_staging_imports_run ON staging_imports(import_run_id);
CREATE INDEX IF NOT EXISTS idx_gov_staging_imports_status ON staging_imports(status);

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

CREATE INDEX IF NOT EXISTS idx_gov_staging_positions_run ON staging_positions(import_run_id);
CREATE INDEX IF NOT EXISTS idx_gov_staging_positions_status ON staging_positions(validation_status);

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

CREATE INDEX IF NOT EXISTS idx_gov_staging_dividends_run ON staging_dividends(import_run_id);
CREATE INDEX IF NOT EXISTS idx_gov_staging_dividends_status ON staging_dividends(validation_status);

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

CREATE INDEX IF NOT EXISTS idx_gov_staging_portfolio_evo_run ON staging_portfolio_evolution(import_run_id);
CREATE INDEX IF NOT EXISTS idx_gov_staging_portfolio_evo_status ON staging_portfolio_evolution(validation_status);

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
    semantic_id TEXT NOT NULL,
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

CREATE INDEX IF NOT EXISTS idx_gov_raw_events_run ON raw_events(import_run_id);
CREATE INDEX IF NOT EXISTS idx_gov_raw_events_date ON raw_events(event_date);
CREATE INDEX IF NOT EXISTS idx_gov_raw_events_status ON raw_events(pipeline_status);

CREATE TABLE IF NOT EXISTS governance_rules (
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

CREATE INDEX IF NOT EXISTS idx_gov_rules_status ON governance_rules(status);
CREATE INDEX IF NOT EXISTS idx_gov_rules_active ON governance_rules(active);

CREATE TABLE IF NOT EXISTS governance_rule_versions (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    previous_pattern TEXT,
    previous_action TEXT,
    changed_by TEXT,
    reason_for_change TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(rule_id) REFERENCES governance_rules(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gov_rule_versions_rule ON governance_rule_versions(rule_id);

CREATE TABLE IF NOT EXISTS governance_audit_log (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    field_changes TEXT,
    changed_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gov_audit_log_entity ON governance_audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_gov_audit_log_action ON governance_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_gov_audit_log_created_at ON governance_audit_log(created_at);

CREATE TABLE IF NOT EXISTS governance_prompt_versions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS governance_ai_runs (
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
    FOREIGN KEY(prompt_version_id) REFERENCES governance_prompt_versions(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_gov_ai_runs_run ON governance_ai_runs(import_run_id);
CREATE INDEX IF NOT EXISTS idx_gov_ai_runs_status ON governance_ai_runs(status);

CREATE TABLE IF NOT EXISTS governance_reconciliation (
    id TEXT PRIMARY KEY,
    event_id_a TEXT NOT NULL,
    event_id_b TEXT NOT NULL,
    link_type TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    match_method TEXT NOT NULL DEFAULT 'EXACT',
    status TEXT NOT NULL DEFAULT 'PENDING',
    confirmed_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id_a) REFERENCES raw_events(id) ON DELETE CASCADE,
    FOREIGN KEY(event_id_b) REFERENCES raw_events(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gov_reconciliation_status ON governance_reconciliation(status);

CREATE TABLE IF NOT EXISTS governance_feedback (
    id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    original_category TEXT,
    suggested_category TEXT,
    user_correction TEXT,
    was_ai_generated INTEGER DEFAULT 0,
    incorporated_into_rule INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gov_feedback_transaction ON governance_feedback(transaction_id);

CREATE TABLE IF NOT EXISTS governance_training_dataset (
    id_economico TEXT PRIMARY KEY,
    data DATE,
    descricao_original TEXT,
    valor_cents INTEGER,
    macro_categoria TEXT,
    applied_rule_id TEXT,
    reason TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gov_training_rule ON governance_training_dataset(applied_rule_id);

CREATE TABLE IF NOT EXISTS governance_embeddings (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    vector_data BLOB,
    model_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gov_embeddings_entity ON governance_embeddings(entity_type, entity_id);
