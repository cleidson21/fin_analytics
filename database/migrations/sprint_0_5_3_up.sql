-- Migration: Sprint 0.5.3 - Unique Indexes for Wealth Tables
CREATE UNIQUE INDEX IF NOT EXISTS idx_positions_lookup ON positions(ticker, data_snapshot);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dividends_lookup ON dividends(ticker, data_pagamento, valor_liquido_cents);
CREATE UNIQUE INDEX IF NOT EXISTS idx_portfolio_evolution_lookup ON portfolio_evolution(reference_month);
