# Architecture Decision Records — Lote 10.0
**Document:** Decision Log
**Updated:** 2026-09-14

---

## Decision Index

| ADR | Title | Status | Phase |
|-----|-------|--------|-------|
| ADR-001 | Deterministic Calculations First | APPROVED | All |
| ADR-002 | Ollama Runs Natively on Host | PROPOSED → CONFIRMED | 10.8 |
| ADR-003 | Single Documentation Source | APPROVED | 10.0 |
| ADR-004 | Agent Frameworks Deferred | APPROVED | 10.10 conditional |
| ADR-005 | External Consensus is NOT Proprietary | APPROVED | 10.7 |
| ADR-006 | Market Data — No Second System | APPROVED | 10.7 |
| ADR-007 | Single LLM + Deterministic Context | PROPOSED | 10.8 |
| ADR-008 | SQLite Retained for Local Use | PROPOSED | 10.11 |
| ADR-009 | position_snapshots Conflict — Investigation Complete | RESOLVED | Lote 10.0-A |
| ADR-010 | brFinance as Isolated Adapter | PROPOSED | 10.7 |
| ADR-011 | Wealth Intelligence Navigation Restructure | PROPOSED | 10.1 |
| ADR-012 | Google News RSS as Primary News Source | PROPOSED | 10.7 |
| ADR-013 | AI Insights Are Immutable After Storage | APPROVED | 10.9 |
| ADR-014 | accounts Table PK — Dual System Incompatibility | DOCUMENTED | 10.0-A |
| ADR-015 | Formal Deterministic Anomaly Specification | APPROVED | 10.2 |
| ADR-016 | Gemini Micro-Process Execution Strategy | APPROVED | 10.2 |
| ADR-017 | Financial Health Consolidated Account Scope | APPROVED | 10.2 |
| ADR-018 | Financial Trend, Acceptance Boundary, and Stability Readiness | APPROVED | 10.2.10-A |

---

## ADR-001: Deterministic Calculations First
**Status:** APPROVED
**Context:** The LLM cannot be trusted to perform financial arithmetic reliably.
**Decision:** All financial calculations (portfolio value, goal progress, retirement projection, savings rate, attribution) are performed deterministically by backend services. The LLM receives pre-calculated data and generates natural-language interpretations only.
**Consequences:** Backend must implement full calculation layer before AI phases.

---

## ADR-002: Ollama Runs Natively on Host
**Status:** PROPOSED (audit confirmed this is correct)
**Context:** Docker GPU passthrough on Windows requires WSL2 + NVIDIA Container Toolkit. This adds setup complexity and fragility.
**Decision:** Ollama installs natively on Windows. Dockerized backend connects to Ollama via `http://host.docker.internal:11434`. Models persist in `%USERPROFILE%\.ollama\models\`.
**Alternatives considered:** Option B (Docker GPU container) — deferred as future option if host-native proves inconvenient.
**Consequences:** User must install Ollama separately from `docker compose up`. Docker compose handles backend + frontend only.

---

## ADR-003: Single Documentation Source
**Status:** APPROVED
**Decision:** `project/wealth-intelligence/` is the sole architectural source of truth. No documentation in README files, Notion, or other locations that may diverge.

---

## ADR-004: Agent Frameworks Deferred
**Status:** APPROVED
**Decision:** No LangGraph, CrewAI, AutoGen, or similar frameworks until a demonstrated quality gap proves they are necessary. Start with Option D (single LLM + deterministic context). Revisit in Phase 10.10 only if needed.
**Rationale:** RTX 5060 8GB cannot run multiple models simultaneously. Sequential agents have unacceptable latency. Custom orchestration is simpler to debug and maintain.

---

## ADR-005: External Consensus Is Not Proprietary
**Status:** APPROVED
**Decision:** Analyst consensus data, where available, is displayed as external opinion clearly labeled with source and date. Never presented as application recommendation. Never fabricated.

---

## ADR-006: Market Data — No Second yfinance System
**Status:** APPROVED
**Decision:** Future market data needs (BCB, news, fundamentals) extend the existing `MarketDataProvider` protocol or add new dedicated adapters. The existing `YFinanceProvider` + `MarketDataService` singleton is NOT replaced or duplicated.
**Consequences:** BCBAdapter, NewsAdapter, and brFinanceAdapter are new independent classes, not forks of YFinanceProvider.

---

## ADR-007: Single LLM + Deterministic Context (Hybrid Option D)
**Status:** PROPOSED
**Context:** Options A-D were evaluated. Option D (hybrid deterministic services + single LLM call for natural language) provides the best balance of quality, latency, token cost, and hardware feasibility on RTX 5060 8GB.
**Decision:** WealthContextBuilder aggregates all pre-calculated data. One LLM call generates the structured InsightResponse. No sequential or parallel agent swarms at this stage.
**Revisit condition:** If Phase 10.9 briefing quality is demonstrably insufficient for all briefing types, start Phase 10.10 to evaluate sequential specialization.

---

## ADR-008: SQLite Retained for Local Use
**Status:** PROPOSED
**Decision:** SQLite with WAL mode is retained for the personal-use local deployment scenario. A PostgreSQL upgrade path is documented but not implemented.
**Revisit condition:** If multi-worker backend deployment or concurrent write volume justifies PostgreSQL.

---

## ADR-009: position_snapshots Schema Conflict — RESOLVED
**Status:** RESOLVED (Lote 10.0-A — 2026-09-09)
**Investigation findings (verified against live DB):**

**Migration 013 (SQL script):** Defines `position_snapshots` with `snapshot_hash` UNIQUE — designed for B3 Área do Investidor import (never used).

**Alembic migration `a1b2c3d4e5f6` (wealth_phase1):** Defines the CORRECT `position_snapshots` with schema: id + account_id + asset_id + reference_date + quantity + avg_price + source_type + run_id + is_manual + current_value. This is what the ORM and all production code use.

**Live DB inspection (2026-09-09):**
- Real table schema: id, account_id, asset_id, reference_date, quantity, avg_price, source_type, run_id, is_manual, created_at, updated_at, current_value
- `snapshot_hash` column: **DOES NOT EXIST in the live DB**
- UNIQUE constraint: `uq_position_snapshot_account_asset_date` (account_id, asset_id, reference_date) — matches ORM
- 53 rows, all source_type = MYPROFIT_ATIVOS
- `alembic_version` = `183e77495632` (head) — Alembic controls this table

**Resolution:** The "conflict" was apparent, not real. Migration 013 uses `CREATE TABLE IF NOT EXISTS`. By the time it could run, the Alembic migration had already created the table with the correct schema. The 013 SQL was silently skipped by SQLite's IF NOT EXISTS guard. `_schema_migrations` table does not exist in the live DB, confirming `create_db.py` was never applied to this database — the DB was bootstrapped entirely via Alembic.

**Actions taken:**
1. `database/create_db.py`: Migration 013 commented out with explanatory note (NOT removed — preserved for historical record)
2. `database/migrations/013_position_snapshots.sql`: NOT modified (historical record)
3. `requirements.txt`: Updated with missing dependencies
4. `DECISION_LOG.md`: Updated to RESOLVED
5. `CURRENT_STATE.md`: Updated to reflect verified state

**BLOCKER is cleared. No schema change required. Ready for Lote 10.1.**

**Remaining risk:** `alembic check` raises `NoReferencedColumnError` for FK `accounts.id` because the Pierre `accounts` table uses composite PK (provider, external_id), not a column named `id`. The FK in `PositionSnapshotModel` is already declared as logical-only (see comment in the model: "validated programmatically; no FK constraint"). The FK declared in the Alembic migration DDL is the issue — but this is a pre-existing condition that did NOT prevent the system from running. Documented in ADR-014.

---

## ADR-010: brFinance as Isolated Adapter
**Status:** PROPOSED
**Decision:** brFinance (eudesrodrigo/brFinance) is not added as a direct application dependency. It is wrapped in an isolated `CVMAdapter` class in `backend/integrations/cvm/`. If brFinance breaks or becomes unmaintained, the adapter can be rewritten to use CVM API directly without touching other code.
**Rationale:** Community library, limited maintenance history, CVM API may be accessed directly without it.

---

## ADR-011: Wealth Intelligence Navigation Restructure
**Status:** PROPOSED
**Context:** Current navigation has "Metas" → /goals as a top-level sidebar item (stub only). Wealth Intelligence needs a full multi-page section.
**Decision:** Add "Wealth Intelligence" as a new top-level sidebar section with sub-tabs. The /goals stub is replaced by /wealth-intelligence/goals. The existing /goals route redirects.
**Out of scope for 10.0:** Navigation change happens in Phase 10.1.

---

## ADR-012: Google News RSS as Primary News Source
**Status:** PROPOSED
**Decision:** Google News RSS (https://news.google.com/rss/search?q=...) is the primary news retrieval mechanism. Free, no API key, validated by b3analysis project. If Google removes RSS access, fallback to alternative RSS news sources.
**Constraints:** News content is sanitized before LLM exposure. Source URL always preserved and displayed.

---

## ADR-014: accounts Table PK — Dual System Incompatibility
**Status:** DOCUMENTED — no change required for Lote 10.1
**Discovered:** Lote 10.0-A (2026-09-09)
**Context:** The Pierre `accounts` table uses a composite PK `(provider, external_id)` — there is no `id` column. The `PositionSnapshotModel` ORM declares `account_id` as a FK to `accounts.id`, but with an explicit comment: "validated programmatically; no FK constraint due to dual-schema accounts table in live DB — logical reference only." The Alembic migration `a1b2c3d4e5f6` also declares this FK in DDL (`fk_position_snapshots_account_id`), but SQLite does not enforce FK constraints by default. The `alembic check` command fails with `NoReferencedColumnError` because it tries to resolve this FK during autogenerate comparison.

**Why this exists:** position_snapshots.account_id stores a string identifier (e.g., `'Myprofit'`) that is NOT an actual FK to the Pierre accounts table. It is a logical grouping identifier for investment data imported from MyProfit, which is a separate system from Pierre Finance.

**Impact:** No runtime impact. `alembic check` fails, but `alembic upgrade head` and `alembic current` work correctly. The application starts and all Investments endpoints function correctly.

**Decision:** No change in Lote 10.0-A. This is a pre-existing architectural constraint from the dual-system design. The correct long-term resolution (Lote 10.1 or later) is to either: (a) create a separate `investment_accounts` table not linked to Pierre `accounts`, or (b) formalize the MyProfit account identifier in the data model. Documented for awareness.

**Gate impact:** Does NOT block Lote 10.1. No migration needed.

---

## ADR-013: AI Insights Are Immutable After Storage
**Status:** APPROVED
**Decision:** Once an InsightResponse is stored in the `ai_insights` table, it is never modified. If the AI would generate a different insight (e.g., after new data), a NEW insight row is created. Old insights are marked as superseded. Immutable history enables full auditability.
**Rationale:** Consistent with the existing ai_prompt_versions immutability pattern.

---

## ADR-015: Formal Deterministic Anomaly Specification
**Status:** APPROVED
**Date locked:** 2026-09-12
**Context:** Financial Health needs deterministic, reconstructible spending signals; machine learning, arbitrary multipliers, and implicit treatment of absent categories are prohibited.

**Decision:**
- **Global baseline:** exactly the three immediately preceding continuous closed months; the target month never participates. A missing required closed month yields `INSUFFICIENT_BASELINE`, no anomalies, and no synthetic or extrapolated data.
- **Presence:** a category is present only with a certified record. Absence is not zero. An explicit `Decimal('0.00')` is present and participates in history counting and arithmetic.
- **SPIKE eligibility:** a current category needs presence in at least 2 of 3 baseline months. Its `baseline_reference` is the arithmetic mean of certified values from its present months only. It must be `>= Decimal('50.00')`.
- **SPIKE:** emit only when `current_expense > baseline_reference * Decimal('1.5')`. The operator is strict `>`; exactly 1.5x is `NORMAL`. A category with 1 of 3 historical months is `INSUFFICIENT_HISTORY`; otherwise-eligible baseline below 50 is `BELOW_BASELINE_FLOOR`.
- **NEW_EXPENSE:** a current category absent in all three baseline months emits `NEW_EXPENSE` when `current_expense >= Decimal('100.00')`. Below that boundary its state is `NEW_EXPENSE_BELOW_THRESHOLD`. The operator is `>=`; an explicit historical zero means present, not new.
- **States:** `NORMAL`, `SPIKE`, `NEW_EXPENSE`, `INSUFFICIENT_HISTORY`, `BELOW_BASELINE_FLOOR`, `NEW_EXPENSE_BELOW_THRESHOLD`, and global `INSUFFICIENT_BASELINE`. Only `SPIKE` and `NEW_EXPENSE` are anomalies.
- **Precision and identity:** money, thresholds, and multiplier are `Decimal`; ratio is analytical `Decimal` only when the baseline reference is positive. Categories match by exact certified string, with no normalization, aliases, or fuzzy matching.
- **Explainability:** each future evaluation exposes deterministic inputs, history, baseline, ratio, and applicable thresholds. Severity, trend anomalies, fraud detection, and AI narrative are not part of this ADR.

**Consequences:** The implementation may produce only `SPIKE` and `NEW_EXPENSE` signals. Historical categories absent from the target month do not produce a signal. No R$50 minimum absolute delta exists; R$50 is solely the inclusive baseline-reference floor.

---

## ADR-016: Gemini Micro-Process Execution Strategy
**Status:** APPROVED
**Context:** Lote 10.2 is complex. Autonomous agents (Gemini) can silently accumulate technical debt or invent architecture if left unchecked.
**Decision:**
- **Mode A (Sonnet/High-Context):** May execute coherent groups of micro-processes sequentially, respecting explicit validation gates.
- **Mode B (Gemini):** Must execute one micro-process at a time. Must STOP and wait for explicit user approval before moving to the next.
- **No Guessing Rule:** If the repository does not clearly support a metric, stop and report. DO NOT invent fields, proxy models, or business logic.
- **No Refactoring Rule:** Do not opportunistically refactor unrelated architecture.
**Consequences:** Ensures the project prioritizes correctness, deterministic calculations, and auditability over implementation speed.

---

## ADR-017: Financial Health Consolidated Account Scope
**Status:** APPROVED
**Date:** 2026-09-12
**Decision:** Financial Health represents the consolidated financial health of the local tenant. All eligible governed transactions from every account and provider in the local SQLite database participate in its calculations.

**Rationale:** The current application is local and single-tenant; legacy `transactions` has no `user_id`; multiple accounts belong to the same local financial context; and Financial Health is intended to reflect that consolidated situation. Per-account isolation is not a requirement of this phase.

**Consequences:** `HealthFinancialQuery` does not receive account filters. No schema change, `user_id`, multi-tenancy, or Pierre alteration is introduced. Any multi-user or multi-tenant scope requires its own future architectural evolution.

---

## ADR-018: Financial Trend, Acceptance Boundary, and Stability Readiness
**Status:** APPROVED
**Date locked:** 2026-09-14
**Context:** The Phase 10.2 acceptance specification requires deterministic expense, savings-rate, realized-surplus, and category evolution. A read-only audit of the current governed ledger found 1,420 transactions, all `CLASSIFIED`, with `PENDING = 0`, and 17 consecutive calendar months from `2025-05` through the current partial month `2026-09`. The previous incomplete-classification limitation is therefore superseded for the current database.

**Global trend decision:**
- Formal trends compare two consecutive closed calendar months. No missing month is synthesized and no gap is skipped.
- `requested_reference_month` preserves the caller's month. If it is the current partial calendar month, `trend_target_month` is the immediately preceding closed month; otherwise a closed requested month is the trend target. `comparison_month` is the closed calendar month immediately before the target.
- If either required month or metric value is unavailable, the corresponding result is `INSUFFICIENT_DATA`; deltas are `None`. In particular, an undefined `savings_rate` caused by zero income is not replaced with zero.
- Metrics are `total_income`, `total_expense`, `net_cashflow`, and `savings_rate`. `savings_amount` remains an alias of realized net cashflow, not contribution or investment capacity.
- For each metric, `absolute_delta = current_value - previous_value`. When `previous_value != 0`, `percentage_delta = absolute_delta / abs(previous_value)`; otherwise `percentage_delta = None`.
- Directions are exactly `INCREASED`, `DECREASED`, `UNCHANGED`, and `INSUFFICIENT_DATA`, based on exact value comparison without thresholds. For savings rate, a numerically higher rate is `INCREASED`; this is a fact, not a quality judgment.
- Monetary values and ratios remain `Decimal`. No trend value is rounded prematurely.

**Category trend decision:**
- Category trends use the same two consecutive closed months and exact certified-string matching. ADR-015 anomaly evaluation remains independent.
- The output covers the union of categories present in either month. A certified record with `Decimal('0.00')` is presence; no record is absence.
- Present in both months: `INCREASED`, `DECREASED`, or `UNCHANGED`, with current, previous, absolute delta, and percentage delta. When previous expense is zero, percentage delta is `None`.
- Present only in the target month: `NEW`. Present only in the comparison month: `DISAPPEARED`. An invalid month comparison yields `INSUFFICIENT_DATA`.
- Trend `NEW` is not anomaly `NEW_EXPENSE`; no anomaly threshold or inference is reused.

**Budget-pressure decision:** No pressure score or qualitative band is introduced. The factual answer is composed from the current top category, share, rank, expense, category trend, and anomaly status. Rank 1/top share may be described only as the category with the greatest current budget weight.

**Health and Planning boundary:** Financial Health owns observed facts, historical comparisons, trends, anomalies, distribution, and realized surplus/deficit. Sustainable contribution capacity is deferred to Planning. Investment capacity is deferred to Planning and Portfolio Intelligence. `savings_amount` may be an input to those future domains but is not their answer.

**Stability readiness:** The current 16-month continuous closed history is sufficient to design and validate simple deterministic stability facts within Phase 10.2. No composite score, weighting, or stability formula is approved by this ADR. Candidate facts such as positive-cashflow-month ratio and separate income, expense, savings-rate, or surplus variability require a subsequent explicit contract for window, statistic, minimum history, gaps, and null handling before implementation.

**Acceptance mapping:** “Am I spending more?” is answered by the closed-month expense trend. “Is my savings rate improving?” is answered by its numerical direction. “Which category is pressuring my budget?” is answered factually by top share/rank plus category trend and anomaly context. “Is my contribution capacity increasing?” remains a Planning question; Health answers only whether realized surplus/deficit increased.

**Product vision and AI boundary:** Root `ESPECIFICACAO_PRODUTO_METAS.md` is high-level product vision used to preserve acceptance goals and expose roadmap gaps; the executable micro-phase contracts remain in `project/wealth-intelligence/`. Deterministic backend services calculate directions, deltas, trends, and any future approved stability facts. A future LLM may explain those certified facts but must not recalculate them.

**Consequences:** 10.2.10-B may implement only the global and category trend contracts above. Stability implementation remains gated by a separate explicit contract decision in 10.2.10-C. Certified trend facts are reusable by Planning and Goals context, the deterministic Dashboard, and future LLM/Copilot explanations without transferring calculation authority. Phase 10.2 and its final QA remain open.
