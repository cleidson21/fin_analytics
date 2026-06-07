CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'VIEWER',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id_economico TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    origin TEXT,
    domain TEXT,
    import_run_id TEXT,
    source_line_no INTEGER,
    data DATE NOT NULL,
    descricao_original TEXT NOT NULL,
    descricao_normalizada TEXT NOT NULL,
    valor NUMERIC NOT NULL,
    valor_cents INTEGER,
    identificador_externo TEXT,
    macro_categoria TEXT NOT NULL,
    sub_categoria TEXT NOT NULL,
    subnatureza TEXT NOT NULL DEFAULT 'INDEFINIDO',
    natureza TEXT NOT NULL,
    perfil TEXT NOT NULL,
    classificacao_fonte TEXT NOT NULL DEFAULT 'ETL',
    parcelamento TEXT,
    observacao TEXT,
    created_by TEXT,
    updated_by TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS etl_runs_legacy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    file_name TEXT NOT NULL,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rows_read INTEGER NOT NULL,
    rows_inserted INTEGER NOT NULL,
    rows_updated INTEGER NOT NULL,
    checksum TEXT
);

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
    status TEXT DEFAULT 'PENDING'
);

CREATE INDEX IF NOT EXISTS idx_import_runs_checksum ON import_runs(checksum);
CREATE INDEX IF NOT EXISTS idx_import_runs_source_type ON import_runs(source_type);
CREATE INDEX IF NOT EXISTS idx_import_runs_status ON import_runs(status);
CREATE INDEX IF NOT EXISTS idx_import_runs_started_at ON import_runs(started_at);

CREATE INDEX IF NOT EXISTS idx_import_artifacts_run ON import_artifacts(import_run_id);
CREATE INDEX IF NOT EXISTS idx_import_artifacts_type ON import_artifacts(artifact_type);

CREATE INDEX IF NOT EXISTS idx_prompt_versions_name ON prompt_versions(name);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_active ON prompt_versions(name, active);

CREATE INDEX IF NOT EXISTS idx_ai_runs_import_run ON ai_runs(import_run_id);
CREATE INDEX IF NOT EXISTS idx_ai_runs_prompt_version ON ai_runs(prompt_version_id);
CREATE INDEX IF NOT EXISTS idx_ai_runs_status ON ai_runs(status);
CREATE INDEX IF NOT EXISTS idx_ai_runs_created_at ON ai_runs(created_at);

CREATE INDEX IF NOT EXISTS idx_staging_imports_run
ON staging_imports(import_run_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_staging_imports_run_line
ON staging_imports(import_run_id, source_line_no);

CREATE INDEX IF NOT EXISTS idx_staging_imports_status
ON staging_imports(status);

CREATE INDEX IF NOT EXISTS idx_transactions_data
ON transactions(data);

CREATE INDEX IF NOT EXISTS idx_transactions_macro
ON transactions(macro_categoria);

CREATE INDEX IF NOT EXISTS idx_transactions_natureza
ON transactions(natureza);

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
    import_run_id TEXT,
    source_line_no INTEGER,
    created_by TEXT,
    updated_by TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, data_snapshot)
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
    import_run_id TEXT,
    source_line_no INTEGER,
    created_by TEXT,
    updated_by TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_positions_date
ON positions(data_snapshot);

CREATE INDEX IF NOT EXISTS idx_dividends_date
ON dividends(data_pagamento);

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
    ibov_mensal_pct DECIMAL(7, 4) DEFAULT 0,
    ibov_acumulado_pct DECIMAL(7, 4) DEFAULT 0,
    cdi_mensal_pct DECIMAL(7, 4) DEFAULT 0,
    cdi_acumulado_pct DECIMAL(7, 4) DEFAULT 0,
    ipca_mensal_pct DECIMAL(7, 4) DEFAULT 0,
    ipca_acumulado_pct DECIMAL(7, 4) DEFAULT 0,
    ifix_mensal_pct DECIMAL(7, 4) DEFAULT 0,
    ifix_acumulado_pct DECIMAL(7, 4) DEFAULT 0,
    sp500_mensal_pct DECIMAL(7, 4) DEFAULT 0,
    sp500_acumulado_pct DECIMAL(7, 4) DEFAULT 0,
    idiv_mensal_pct DECIMAL(7, 4) DEFAULT 0,
    idiv_acumulado_pct DECIMAL(7, 4) DEFAULT 0,
    import_run_id TEXT,
    source_line_no INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_positions_date
ON positions(data_snapshot);

CREATE INDEX IF NOT EXISTS idx_dividends_date
ON dividends(data_pagamento);

CREATE INDEX IF NOT EXISTS idx_portfolio_evolution_date
ON portfolio_evolution(reference_month);

CREATE INDEX IF NOT EXISTS idx_positions_run ON positions(import_run_id);
CREATE INDEX IF NOT EXISTS idx_dividends_run ON dividends(import_run_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_evo_run ON portfolio_evolution(import_run_id);

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

CREATE INDEX IF NOT EXISTS idx_staging_positions_run ON staging_positions(import_run_id);
CREATE INDEX IF NOT EXISTS idx_staging_positions_status ON staging_positions(validation_status);

CREATE INDEX IF NOT EXISTS idx_staging_dividends_run ON staging_dividends(import_run_id);
CREATE INDEX IF NOT EXISTS idx_staging_dividends_status ON staging_dividends(validation_status);

CREATE INDEX IF NOT EXISTS idx_staging_portfolio_evo_run ON staging_portfolio_evolution(import_run_id);
CREATE INDEX IF NOT EXISTS idx_staging_portfolio_evo_status ON staging_portfolio_evolution(validation_status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_positions_lookup ON positions(ticker, data_snapshot);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dividends_lookup ON dividends(ticker, data_pagamento, valor_liquido_cents);
CREATE UNIQUE INDEX IF NOT EXISTS idx_portfolio_evolution_lookup ON portfolio_evolution(reference_month);

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    field_changes TEXT,  -- JSON containing before/after state
    changed_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);