-- Migration DOWN: Sprint 0.5.1.1 (Rollback da Governança Wealth)
-- Como o SQLite mais antigo ou padrão Python nem sempre suporta ALTER TABLE DROP COLUMN, 
-- utilizaremos a abordagem Rename-Recreate-Insert-Drop para maior segurança em qualquer ambiente.

PRAGMA foreign_keys=off;
BEGIN TRANSACTION;

-- ==========================================
-- Revertendo positions
-- ==========================================
ALTER TABLE positions RENAME TO _positions_old;

CREATE TABLE positions (
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

INSERT INTO positions (
    ticker, data_snapshot, source, quantidade, preco_medio, total_investido,
    preco_atual, total_atual, ganho, criado_em, atualizado_em
)
SELECT 
    ticker, data_snapshot, source, quantidade, preco_medio, total_investido,
    preco_atual, total_atual, ganho, criado_em, atualizado_em
FROM _positions_old;

DROP TABLE _positions_old;

CREATE INDEX idx_positions_date ON positions(data_snapshot);


-- ==========================================
-- Revertendo dividends
-- ==========================================
ALTER TABLE dividends RENAME TO _dividends_old;

CREATE TABLE dividends (
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

INSERT INTO dividends (
    id_economico, source, ticker, tipo_evento, data_pagamento, 
    valor_liquido, valor_liquido_cents, criado_em, atualizado_em
)
SELECT 
    id_economico, source, ticker, tipo_evento, data_pagamento, 
    valor_liquido, valor_liquido_cents, criado_em, atualizado_em
FROM _dividends_old;

DROP TABLE _dividends_old;

CREATE INDEX idx_dividends_date ON dividends(data_pagamento);


-- ==========================================
-- Revertendo portfolio_evolution
-- ==========================================
ALTER TABLE portfolio_evolution RENAME TO _portfolio_evolution_old;

CREATE TABLE portfolio_evolution (
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO portfolio_evolution (
    id, reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,
    patrimonio_cents, compras_cents, vendas_cents, op_finalizadas_cents, proventos_cents,
    ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,
    ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,
    sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct, created_at
)
SELECT 
    id, reference_month, rentabilidade_mensal_pct, rentabilidade_acumulada_pct,
    patrimonio_cents, compras_cents, vendas_cents, op_finalizadas_cents, proventos_cents,
    ibov_mensal_pct, ibov_acumulado_pct, cdi_mensal_pct, cdi_acumulado_pct,
    ipca_mensal_pct, ipca_acumulado_pct, ifix_mensal_pct, ifix_acumulado_pct,
    sp500_mensal_pct, sp500_acumulado_pct, idiv_mensal_pct, idiv_acumulado_pct, created_at
FROM _portfolio_evolution_old;

DROP TABLE _portfolio_evolution_old;

CREATE INDEX idx_portfolio_evolution_date ON portfolio_evolution(reference_month);

COMMIT;
PRAGMA foreign_keys=on;
