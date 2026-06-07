-- Migration UP: Sprint 0.5.1.1 (Governança Wealth e Rollback)

-- 1. Adição de colunas na tabela positions
ALTER TABLE positions ADD COLUMN import_run_id TEXT;
ALTER TABLE positions ADD COLUMN source_line_no INTEGER;

-- 2. Adição de colunas na tabela dividends
ALTER TABLE dividends ADD COLUMN import_run_id TEXT;
ALTER TABLE dividends ADD COLUMN source_line_no INTEGER;

-- 3. Adição de colunas na tabela portfolio_evolution
ALTER TABLE portfolio_evolution ADD COLUMN import_run_id TEXT;
ALTER TABLE portfolio_evolution ADD COLUMN source_line_no INTEGER;

-- 4. Criação de índices para facilitar o Rollback e as Consultas
CREATE INDEX IF NOT EXISTS idx_positions_run ON positions(import_run_id);
CREATE INDEX IF NOT EXISTS idx_dividends_run ON dividends(import_run_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_evo_run ON portfolio_evolution(import_run_id);
