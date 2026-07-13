-- ==========================================================================
-- MIGRATION 013 — POSITION SNAPSHOTS (Plataforma de Investimentos)
-- FinAnalytics V3 | Sprint 2 — Persistência B3 Custódia
-- ==========================================================================
--
-- Esta tabela representa o estado patrimonial estático de um ativo em uma
-- data específica. É a estrutura de persistência do PositionSnapshot gerado
-- pela Plataforma de Investimentos (Macrofase 1).
--
-- Chave de idempotência: snapshot_hash = MD5(reference_date + ticker + institution)
-- Estratégia de escrita: INSERT OR REPLACE (UPSERT por snapshot_hash UNIQUE)
-- ==========================================================================

PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS position_snapshots (
    -- Identidade
    id                  TEXT PRIMARY KEY,           -- UUID gerado pelo Repository
    snapshot_hash       TEXT NOT NULL UNIQUE,       -- MD5(ref_date + ticker + institution) — idempotência

    -- Localização temporal e patrimonial
    reference_date      TEXT NOT NULL,              -- YYYY-MM-DD (data base do snapshot)
    ticker              TEXT NOT NULL,              -- código normalizado (ex: PETR4, BRSTNC...)
    asset_type          TEXT NOT NULL CHECK(asset_type IN (
                            'STOCK', 'FII', 'ETF', 'BDR', 'FIXED_INCOME', 'TREASURY', 'CRYPTO', 'FUNDS', 'UNKNOWN'
                        )),
    institution         TEXT NOT NULL,              -- corretora/custodiante (ex: XP INVESTIMENTOS)
    source_system       TEXT NOT NULL DEFAULT 'B3_AREA_INVESTIDOR',  -- fonte dos dados

    -- Posição
    quantity            TEXT NOT NULL,              -- Decimal como TEXT para preservar precisão
    unit_price          TEXT,                       -- preço unitário (opcional)
    total_value         TEXT,                       -- valor total posição (opcional)

    -- Metadados rastreáveis
    metadata_json       TEXT NOT NULL DEFAULT '{}', -- JSON com campos originais (ISIN, CNPJ, etc.)

    -- Auditoria
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Índices de acesso frequente
CREATE INDEX IF NOT EXISTS idx_position_snapshots_ticker         ON position_snapshots(ticker);
CREATE INDEX IF NOT EXISTS idx_position_snapshots_reference_date ON position_snapshots(reference_date);
CREATE INDEX IF NOT EXISTS idx_position_snapshots_institution    ON position_snapshots(institution);
CREATE INDEX IF NOT EXISTS idx_position_snapshots_asset_type     ON position_snapshots(asset_type);
CREATE INDEX IF NOT EXISTS idx_position_snapshots_hash           ON position_snapshots(snapshot_hash);

-- Índice composto para consultas de portfólio por data
CREATE INDEX IF NOT EXISTS idx_position_snapshots_date_ticker    ON position_snapshots(reference_date, ticker);
