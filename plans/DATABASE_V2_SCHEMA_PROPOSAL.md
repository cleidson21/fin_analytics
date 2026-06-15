# DATABASE V2 SCHEMA PROPOSAL

**Fase:** DB-01 (Database V2 Foundation)

## 1. TABELAS (Ciclo de Vida)

### A. Mantidas (Base Validada)
`users`, `import_runs`, `import_artifacts`, `raw_events`, `staging_imports`, `staging_positions`, `staging_dividends`, `staging_portfolio_evolution`, `transactions`, `positions`, `dividends`, `portfolio_evolution`, `event_links`, `audit_log`.

### B. Removidas (Lixo Legado)
`etl_runs_legacy`.

### C. Consolidadas (Resolução de Conflito de IA)
As tabelas separadas do V1 (`governance_rules`, `governance_prompt_versions`, `governance_ai_runs`) serão **destruídas**.
A arquitetura V2 adotará APENAS as nomenclaturas unificadas:
* `rules` (Comporta todas as regras Regex/Semânticas manuais e governamentais).
* `prompt_versions` (Todos os templates de LLM num único ponto central).
* `ai_runs` (Log financeiro unificado do faturamento OpenAI/Gemini).

### D. Novas (O Domínio de Inteligência e Restrição)
* `categories`: `id` (PK), `name` (String), `type` (Enum: IN/OUT), `parent_id` (FK pra subcategorias).
* `subscriptions`: `id` (PK), `name`, `category_id` (FK), `expected_amount_cents`, `billing_cycle`.
* `goals`: `id` (PK), `category_id` (FK), `limit_cents`, `severity_level`.
* `benchmarks`: `id` (PK), `reference_date` (Date), `type` (Enum: CDI, IBOV, S&P500), `value_pct`.

## 2. REGRAS DE INTEGRIDADE (CONSTRAINTS)

### A. Primary Keys (PK)
Todas as tabelas novas e as de Governança utilizarão nativamente `TEXT PRIMARY KEY` contendo UUIDs (v4) na aplicação para prevenir colisões (exceção para `transactions.id_economico`).

### B. Foreign Keys & Cascata (A Raiz: import_runs)
A entidade mestre `import_runs` governa o ciclo de vida.
Toda e qualquer tabela que contenha a coluna `import_run_id` **DEVE** declarar explicitamente:
`FOREIGN KEY(import_run_id) REFERENCES import_runs(id) ON DELETE CASCADE`

As entidades a seguir herdam essa cascata:
`import_artifacts`, `raw_events`, `transactions`, `positions`, `dividends`, `portfolio_evolution` e TODAS as `staging_*`.

### C. Unique Keys e Unicidade
* `raw_events`: `UNIQUE(semantic_id)` -> Prevenção estrita contra upload duplicado do mesmo extrato.
* `portfolio_evolution`: `UNIQUE(reference_month)` -> Um mês, uma fotografia.

## 3. VALIDAÇÃO DOS CONTRATOS DOMAIN
* **Core Finance:** `transactions` agora não terá uma string solta. Terá a FK `category_id` apontando para a nova hierarquia, impedindo inserção de "Alimetacao" com erro de digitação.
* **Wealth:** `portfolio_evolution` buscará suas subtrações dinamicamente da tabela nova `benchmarks`.
