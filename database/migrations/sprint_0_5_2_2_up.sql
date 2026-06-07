-- Migration: Sprint 0.5.2.2 - Wealth Staging Tables

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
