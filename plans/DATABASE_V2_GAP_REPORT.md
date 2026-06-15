# DATABASE V2 GAP REPORT

**Fase:** DB-01 — AUDITORIA

Este documento analisa a discrepância (Gap) entre o estado atual dos schemas SQL congelados (V1) e o estado desejado da Arquitetura V2.

---

## 1. TABELAS EXISTENTES (V1)
Atualmente o banco de dados está fragmentado entre `schema.sql` e `governance_schema.sql`, gerando colisão de responsabilidades.
* **Core/Wealth:** `users`, `transactions`, `positions`, `dividends`, `portfolio_evolution`.
* **Governança/ETL:** `import_runs`, `import_artifacts`, `raw_events`, `staging_imports`, `staging_positions`, `staging_dividends`, `staging_portfolio_evolution`, `event_links`, `audit_log`.
* **Inteligência (Duplicada):** `rules`, `prompt_versions`, `ai_runs` (no schema principal) vs `governance_rules`, `governance_prompt_versions`, `governance_ai_runs`, `governance_reconciliation`, `governance_feedback`, `governance_embeddings` (no schema de governança).
* **Lixo Legado:** `etl_runs_legacy`.

## 2. ANÁLISE DE GAP (O que falta para a V2)
A Fase 10.3 (Domain Architecture) exigiu novos subdomínios autônomos que atualmente são apenas *Strings* ou cálculos em memória no backend.

* **Falta (Core Finance):** Entidades próprias para `categories`, `subscriptions` (assinaturas) e `goals` (metas). Na V1, a categoria é só uma string solta na transação.
* **Falta (Wealth):** Entidade própria para `benchmarks`. Na V1, o IBOV/CDI são apenas colunas flutuantes dentro de `portfolio_evolution`.

## 3. DESTINO DAS TABELAS (Ciclo de Vida V2)

### A. Tabelas Mantidas (Com ajustes de Foreign Key)
* `users`
* `import_runs` e `import_artifacts`
* `raw_events` e `event_links`
* `staging_imports`, `staging_positions`, `staging_dividends`, `staging_portfolio_evolution`
* `transactions`
* `positions` e `dividends`
* `portfolio_evolution`
* `audit_log`

### B. Tabelas Removidas (Expurgos)
* `etl_runs_legacy` (código morto).
* `governance_rules`, `governance_prompt_versions`, `governance_ai_runs`, `governance_reconciliation`, `governance_audit_log` (Duplicação esquizofrênica do schema de governança que conflita com o schema central).

### C. Tabelas Recriadas / Novas (V2 Models)
* `categories` (Nova entidade relacional de hierarquia).
* `subscriptions` (Nova entidade gerenciadora de despesas contínuas).
* `goals` (Nova entidade de teto de gastos orçamentários).
* `benchmarks` (Nova entidade centralizando índices de mercado).
* `rules`, `prompt_versions`, `ai_runs` (Consolidação única e definitiva da inteligência).

## 4. DEPENDÊNCIAS, FOREIGN KEYS E ÍNDICES (Regras V2)
* **A Regra de Ouro (ON DELETE CASCADE):** Todas as entidades mutáveis originadas de extratos (`transactions`, `positions`, `dividends`, `staging_*`, `raw_events`) precisam ter o FK `import_run_id` apontando para `import_runs(id) ON DELETE CASCADE`.
* **Unicidade Estrita:** `raw_events` precisará do constraint `UNIQUE(semantic_id)` para barrar inserção dupla via script. `portfolio_evolution` precisa manter `UNIQUE(reference_month)`.

## 5. RISCOS LEVANTADOS
1. **Risco de Integridade na Migração de Categorias:** Se transformarmos `macro_categoria` e `sub_categoria` (que hoje são TEXT) em Foreign Keys para a nova tabela `categories`, precisaremos de um script de migração DML pesado (Data Manipulation Language) para inferir as strings antigas para os novos UUIDs da tabela relacional.
2. **Risco de Duplicação de Regras:** A fusão de `rules` e `governance_rules` num único motor de classificação pode gerar chaves conflitantes no motor de inteligência.
