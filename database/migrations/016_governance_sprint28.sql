-- ==========================================================================
-- MIGRATION v2 — GOVERNANÇA FINANCEIRA MANUAL
-- Sprint 2.8 | FIN_ANALYTICS v2
-- Adiciona camada de governança à tabela transactions existente
-- e cria tabela de auditoria imutável.
-- ==========================================================================

-- Colunas de governança na tabela transactions
-- ALTER TABLE ADD COLUMN é seguro no SQLite quando o DEFAULT cobre todos os rows existentes

ALTER TABLE transactions ADD COLUMN governance_status TEXT NOT NULL DEFAULT 'PENDING';
ALTER TABLE transactions ADD COLUMN economic_classification TEXT;
ALTER TABLE transactions ADD COLUMN investment_name TEXT;
ALTER TABLE transactions ADD COLUMN notes TEXT;
ALTER TABLE transactions ADD COLUMN governed_at DATETIME;

-- Índice para queries de governança (filtro mais comum: listar pendentes)
CREATE INDEX IF NOT EXISTS idx_tx_gov_status ON transactions(governance_status);
CREATE INDEX IF NOT EXISTS idx_tx_gov_classification ON transactions(economic_classification);

-- ==========================================================================
-- TABELA IMUTÁVEL DE AUDITORIA DE GOVERNANÇA
-- INSERT-only. Nunca UPDATE ou DELETE.
-- Cada linha representa uma transição completa de estado (before → after).
-- ==========================================================================

CREATE TABLE IF NOT EXISTS governance_audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    provider        TEXT    NOT NULL,
    external_id     TEXT    NOT NULL,
    action          TEXT    NOT NULL CHECK(action IN (
                        'CREATE_CLASSIFICATION',
                        'UPDATE_CLASSIFICATION',
                        'ROLLBACK'
                    )),
    before_json     TEXT,           -- snapshot JSON do estado ANTES (governança completa)
    after_json      TEXT,           -- snapshot JSON do estado DEPOIS (governança completa)
    changed_at      DATETIME NOT NULL DEFAULT (datetime('now')),
    changed_by      TEXT,           -- reservado: futura autenticação multi-usuário
    reason          TEXT            -- motivo informado pelo usuário (opcional)
);

CREATE INDEX IF NOT EXISTS idx_gov_audit_tx   ON governance_audit_log(provider, external_id);
CREATE INDEX IF NOT EXISTS idx_gov_audit_date ON governance_audit_log(changed_at);
CREATE INDEX IF NOT EXISTS idx_gov_audit_action ON governance_audit_log(action);
