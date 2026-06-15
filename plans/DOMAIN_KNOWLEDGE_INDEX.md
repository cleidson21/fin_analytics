# DOMAIN KNOWLEDGE INDEX

**Objetivo:** Consolidar e catalogar o conhecimento fragmentado entre todos os relatórios gerados desde o início do projeto V2 (Sprint DB-01 até GATE-01).

---

## 1. Documentos Fundacionais e Arquitetura

### `SYSTEM_REBUILD_PACKAGE.md`
* **Origem:** Planejamento Inicial V2
* **Assuntos:** Visão sistêmica, dívida técnica do V1, separação em Bounded Contexts.
* **Regras Descobertas:** Proibição de acoplamento direto entre módulos; API deve ser burra; Lógica puramente em Services.
* **Pendências Abertas:** (Resolvido nas fases subsequentes).

### `V2_ARCHITECTURE_MASTER_PLAN.md` e `ROADMAP.md`
* **Origem:** Planejamento V2 Master
* **Assuntos:** Divisão em Core Finance, Wealth, Governance, AI Layer. Estratégia de "Destroy & Rebuild" (DB -> BE -> API).

### `V2_GOVERNANCE_AND_BOOTSTRAP.md`
* **Origem:** Planejamento de Governança V2
* **Assuntos:** Ciclo de vida da importação (Raw -> Staging -> Ledger), Fuzzy Matching (±3 dias), Tolerância de Centavos.
* **Regras Descobertas:** Regra rigorosa de aprovação (Approval Flow); Reconciliação não pode sobrescrever manual.

---

## 2. Camada de Persistência (Database V2)

### `DATABASE_V2_GAP_REPORT.md`, `DATABASE_V2_SCHEMA_PROPOSAL.md`, `DATABASE_V2_MIGRATION_PLAN.md`, `DATABASE_V2_MIGRATION_ROADMAP.md`, `DATABASE_V2_EXECUTION_REPORT.md`
* **Origem:** Sprint DB-01
* **Assuntos:** Auditoria do schema V1, identificação de tabelas legadas (`analises`, `relatorios`), criação do `schema_v2.sql`.
* **Regras Descobertas:** PKs puras; FKs restritas com ON DELETE CASCADE na importação (limpeza em cascata); valores monetários em `Integer` (`_cents`) além dos numéricos flutuantes.
* **Entidades Descobertas:** `transactions` como Ledger imutável; `import_runs`, `staging_*` tables; `portfolio_evolution` e `benchmarks`.

---

## 3. Camada de Backend & Domínio (Sprints BE-01 e BE-02)

### `BACKEND_V2_BASELINE.md`, `BACKEND_V2_DOMAIN_MAP.md`, `BACKEND_V2_FOUNDATION_REPORT.md`
* **Origem:** Sprint BE-01 (Foundation)
* **Assuntos:** Modelos SQLAlchemy mapeados do banco V2, DTOs Pydantic (baselines), Repositories vazios implementando Generic T.

### `BE02_SERVICE_INVENTORY.md`
* **Origem:** Sprint BE-02 (Discovery)
* **Assuntos:** Mapeamento 1-para-1 dos serviços V1 que precisam ser transcritos para V2.

### `BE02A_EXECUTION_REPORT.md` (Core Finance)
* **Origem:** Sprint BE-02A
* **Assuntos:** Pacing, Cashflow, Metas Mensais.
* **Cálculos Descobertos:** Ritmo de Gastos = Gasto Atual / Gasto Previsto no período. Balance = Receitas - Despesas.
* **Entidades:** `Transaction`, `Category`, `Goal`.

### `BE02B_EXECUTION_REPORT.md` (Wealth)
* **Origem:** Sprint BE-02B
* **Assuntos:** Posições, Yield on Cost (YOC), Rentabilidade Alpha (vs CDI/IBOV), Allocation.
* **Cálculos Descobertos:** YOC = Dividendos / Total Investido; Rentabilidade = (Preço Atual - Preço Médio) / Preço Médio.

### `BE02C_EXECUTION_REPORT.md` (Governance)
* **Origem:** Sprint BE-02C
* **Assuntos:** Lifecycle de `import_runs`, `Staging` tables e Reconciliação.
* **Regras Descobertas:** Exclusão em cascata automatizada (ON DELETE CASCADE) se o `import_run_id` falhar ou expirar; Reconciliação busca valores exatos em até ±3 dias de janela.

### `BE02D_EXECUTION_REPORT.md` (AI Layer)
* **Origem:** Sprint BE-02D
* **Assuntos:** Fallback Pipeline, Rule Engine (Regex), Few-Shot Learning.
* **Regras Descobertas:** Fluxo de prioridade: RECONCILIATION -> RULES (Regex) -> AI (Mock/LLM) -> FALLBACK. Regras têm prioridade resolvida via `confidence_score`.

---

## 4. Auditorias e Segurança

### `V2_ARCHITECTURE_AUDIT_REPORT.md`
* **Origem:** GATE-01
* **Assuntos:** Avaliação final dos artefatos construídos.
* **Regras Descobertas:** Repositories estão órfãos dos Services (que abrem queries diretas no ORM); DTOs não são retornados (Services retornam dict/ORM).
* **Pendências Abertas:** O sistema precisa passar por forte refatoração (`BE-02.5` ou em conjunto na API) para conectar de fato os Services aos Repositories.
