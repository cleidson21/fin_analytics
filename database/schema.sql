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
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS etl_runs (
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_payload TEXT NULL,
    payload_checksum TEXT
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

CREATE INDEX IF NOT EXISTS idx_import_runs_checksum
ON import_runs(payload_checksum);

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
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_positions_date
ON positions(data_snapshot);

CREATE INDEX IF NOT EXISTS idx_dividends_date
ON dividends(data_pagamento);
