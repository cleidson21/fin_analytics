# Architecture Decision Records — Lote 10.0
**Document:** Decision Log
**Updated:** 2026-10-15

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
| ADR-011 | Wealth Intelligence Navigation Restructure | SUPERSEDED BY ADR-027 | Historical 10.0 proposal |
| ADR-012 | Google News RSS as Primary News Source | PROPOSED | 10.7 |
| ADR-013 | AI Insights Are Immutable After Storage | APPROVED | 10.9 |
| ADR-014 | accounts Table PK — Dual System Incompatibility | DOCUMENTED | 10.0-A |
| ADR-015 | Formal Deterministic Anomaly Specification | APPROVED | 10.2 |
| ADR-016 | Gemini Micro-Process Execution Strategy | APPROVED | 10.2 |
| ADR-017 | Financial Health Consolidated Account Scope | APPROVED | 10.2 |
| ADR-018 | Financial Trend, Acceptance Boundary, and Stability Readiness | APPROVED | 10.2.10-A |
| ADR-019 | Planning Input and Source Boundary | APPROVED | 10.3.0-A |
| ADR-020 | Planning Mathematical Contract | APPROVED | 10.3.0-A |
| ADR-021 | Planning Scenario Semantics and Lifecycle | APPROVED | 10.3.0-A |
| ADR-022 | Retirement/FIRE and Portfolio Intelligence Boundary | APPROVED | 10.3.0-A |
| ADR-023 | Investment Portfolio Initial Wealth Source | APPROVED | 10.3.10A |
| ADR-024 | Post-10.3 Planning UX and Simplicity Contract | APPROVED | POST-10.3-UX-A |
| ADR-025 | FIRE Deterministic Contract and Planning Composition | ACCEPTED | 10.4-B |
| ADR-026 | Wealth OS Product Realignment Gate | APPROVED | 10.R0 |
| ADR-027 | Wealth OS Product Architecture & Documentation Ownership | ACCEPTED | 10.R1 |
| ADR-028 | Smart Financial Context and Declared/Observed Income Boundary | ACCEPTED | 10.R2-A |
| ADR-029 | External Context Observation, Temporal, and Provider Boundary | ACCEPTED / LOCKED | 10.R3-B |
| ADR-030 | Hybrid AI Runtime Foundation and Assisted Local Setup | ACCEPTED | 10.R4.0 |

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

**Alembic migration `a1b2c3d4e5f6` (wealth_phase1):** Defines the canonical base `position_snapshots` schema with 11 columns and only the valid `asset_id -> assets.id` foreign key. Revision `08aabd3f3f30` later adds `current_value`, producing the 12-column schema used by the ORM and production code.

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

**Remaining risk (reconciled 2026-10-13):** The ORM and canonical Alembic chain both keep `account_id` logical-only. A later operational inspection reported a physical FK to nonexistent `accounts.id`; legacy `database/migrations/005_open_finance.sql` declares such a relationship, but the exact drift path is unproven. Conditional corrective revision `b7e2d1a4c9f3` is implemented and isolated-tested; operational deployment remains separately gated. Documented in ADR-014.

---

## ADR-010: brFinance as Isolated Adapter
**Status:** PROPOSED
**Decision:** brFinance (eudesrodrigo/brFinance) is not added as a direct application dependency. It is wrapped in an isolated `CVMAdapter` class in `backend/integrations/cvm/`. If brFinance breaks or becomes unmaintained, the adapter can be rewritten to use CVM API directly without touching other code.
**Rationale:** Community library, limited maintenance history, CVM API may be accessed directly without it.

---

## ADR-011: Wealth Intelligence Navigation Restructure
**Status:** `SUPERSEDED / HISTORICAL — ADR-027`
**Context:** Current navigation has "Metas" → /goals as a top-level sidebar item (stub only). Wealth Intelligence needs a full multi-page section.
**Decision:** Add "Wealth Intelligence" as a new top-level sidebar section with sub-tabs. The /goals stub is replaced by /wealth-intelligence/goals. The existing /goals route redirects.
**Out of scope for 10.0:** Navigation change happens in Phase 10.1.

**R1 reconciliation:** Preserve this as the original 10.0 proposal only. ADR-027
locks conceptual product areas but deliberately does not lock exact routes.
Existing URLs remain operational until R5/R6 contracts migration and deep-link
behavior.

---

## ADR-012: Google News RSS as Primary News Source
**Status:** PROPOSED
**Decision:** Google News RSS (https://news.google.com/rss/search?q=...) is the primary news retrieval mechanism. Free, no API key, validated by b3analysis project. If Google removes RSS access, fallback to alternative RSS news sources.
**Constraints:** News content is sanitized before LLM exposure. Source URL always preserved and displayed.

---

## ADR-014: accounts Table PK — Dual System Incompatibility
**Status:** DOCUMENTED / CORRECTIVE REVISION IMPLEMENTED / DEPLOYMENT BLOCKED
**Discovered:** Lote 10.0-A (2026-09-09)
**Context:** The Pierre `accounts` table uses a composite PK `(provider, external_id)` — there is no `id` column. `PositionSnapshotModel.account_id` is a mandatory indexed string with no physical `ForeignKey`; it is a logical reference. Canonical Alembic migration `a1b2c3d4e5f6` likewise declares only the valid `asset_id -> assets.id` FK. A reported operational schema nevertheless contained `account_id -> accounts.id`; legacy SQL `database/migrations/005_open_finance.sql` declares that relationship, but its exact introduction into the reported database has not been established.

**Why this exists:** position_snapshots.account_id stores a string identifier (e.g., `'Myprofit'`) that is NOT an actual FK to the Pierre accounts table. It is a logical grouping identifier for investment data imported from MyProfit, which is a separate system from Pierre Finance.

**Impact:** On a database carrying that physical drift, enabling `PRAGMA foreign_keys=ON` makes snapshot inserts deterministically fail with SQLite `foreign key mismatch`. This mechanism was reproduced in isolated SQLite and is compatible with the observed MyProfit HTTP 500, but it is not proven as that incident's root cause because the original backend traceback is unavailable.

**Decision:** Preserve `account_id` as the current logical reference. Corrective revision `b7e2d1a4c9f3` conditionally removes the invalid physical FK only when the exact supported drift is present, performs no table rewrite on canonical schemas, fails closed on unknown physical shapes, and blocks unsafe downgrade. A future model redesign may still introduce a dedicated investment-account identity, but it is outside this remediation.

**Gate impact:** Repository implementation is available, but operational deployment is blocked pending independent review, verified backup/restore, actual revision/schema inspection, intermediate-migration review, maintenance window, and explicit authorization.

**Operational follow-up (2026-10-14):** A targeted SQLite hotfix removed only the invalid physical account FK; the user confirmed restored MyProfit import. The operational Alembic revision remains `2d6b4f8a9c1e`. Repository revision `b7e2d1a4c9f3` now additionally rejects inbound FKs and semantically divergent secondary indexes before batch DDL, with disposable adversarial coverage. This follow-up does not alter the ADR decision, authorize deployment, or change the R3-E4 `IMPLEMENTATION CHECKPOINT`; R3-F remains `NOT STARTED`.

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

---

## ADR-019: Planning Input and Source Boundary
**Status:** APPROVED
**Date locked:** 2026-09-16
**Context:** Phase 10.3 needs an explicit, Decimal-safe boundary between certified current facts, user-governed Goals, and scenario assumptions. The 10.3.0 audit found no universal certified value that can safely be called global `initial_wealth`. It also found material double-counting risk between manual Goal progress and MyProfit investment wealth, and confirmed that the existing Goals application/entity path converts persisted SQL `Numeric` money to `float`.

**Initial-wealth decision:** Planning has no implicit global `initial_wealth`. Every input declares exactly one conceptual origin:
- `GOAL_CURRENT_AMOUNT` — the user-governed, nullable amount recorded for one Goal;
- `INVESTMENT_PORTFOLIO_SNAPSHOT` — the selected MyProfit investment-portfolio snapshot;
- `USER_PROVIDED_SCENARIO` — an explicit scenario assumption, not a certified observed fact.

These origins are alternatives for one calculation. They are never added, merged, or substituted automatically. A user may explicitly select or copy a value, but that action creates an auditable input choice rather than an inferred equivalence.

**Investment-wealth decision:** `portfolio_snapshots.patrimonio` represents investment wealth within the currently governed MyProfit scope. It is not proven consolidated net worth and must not be labeled `net worth`. It does not prove coverage of real estate, liabilities, non-imported accounts, or every external financial asset. `PositionSnapshotModel` and asset-level valuations may reconcile scoped facts but must not be summed inside Planning when the approved portfolio total is used.

**Goal precision decision:** Goals persists monetary fields as SQL `Numeric`, but the current Goal entity, repository, DTO, progress calculation, and HTTP response path introduce `float`. Planning must not consume that path as mathematical truth. Phase 10.3.1 must introduce a read-only Decimal boundary/adapter for approved Goal facts without changing Goal ownership or treating opaque `assumptions_json` as an executable contract.

**Provenance decision:** Every Planning input/result boundary retains the selected origin, scope/account where applicable, reference or as-of date, source/update timestamp when available, and Decimal value. Missing ownership, freshness, scope, or required facts must remain explicit; no silent fallback is permitted.

**Consequences:** Phase 10.3.1 may add only the typed read adapters/DTOs needed to expose approved Goal, Health, and investment-wealth facts. It must not create projection mathematics, duplicate existing read engines, call internal HTTP APIs, synthesize consolidated net worth, or modify Goals/Investments semantics without separate scope.

---

## ADR-020: Planning Mathematical Contract
**Status:** APPROVED
**Date locked:** 2026-09-16
**Context:** Forward projections and inverse solvers must share one deterministic, auditable monthly model. The contract must support explicit nominal and real scenarios, negative returns above -100%, exact cent behavior, and reuse by Retirement/FIRE without turning historical data into forecasts.

**Time and contribution decision:** The engine operates monthly. `as_of_date` is period zero. A partial current month receives no projected return, projected contribution, or daily proration; the first cycle is the next complete calendar month. Contributions use `END_OF_MONTH` timing, so the contribution for period `t` earns no return in that same period. `scenario_monthly_contribution` must be a non-negative cent-scale Decimal; zero is valid and negative contributions are invalid. Withdrawals require a future separate contract.

**Rate decision:** `rate_basis = EFFECTIVE_ANNUAL`. The UI may accept a human percentage, while the backend/API contract uses a Decimal fraction such as `"0.085"`. Any finite Decimal `annual_rate > -1` is mathematically valid: zero, supported negative rates, and positive rates above 100% are allowed. `NaN`, infinity, and rates `<= -1` are invalid. The core has no arbitrary positive upper cap; future UX may warn about extreme assumptions without changing them.

The equivalent monthly rate is:

```text
monthly_rate = (1 + annual_rate)^(1/12) - 1
```

Simple division by 12 and all float arithmetic are prohibited.

**Nominal/real and inflation decision:** `return_type` and `output_mode` are explicit `NOMINAL` or `REAL` values. Inflation is an explicit finite effective annual Decimal with `inflation_rate > -1`; it is never inferred from IPCA, MyProfit, CDI, IBOV, portfolio history, dividend history, or Health trends.

| Return Type | Output Mode | Inflation | Approved Behavior |
|---|---|---|---|
| `NOMINAL` | `NOMINAL` | Does not participate | Nominal return, constant nominal monthly contribution, nominal outputs |
| `NOMINAL` | `REAL` | Required | Apply Fisher exactly once, then run directly in real money of `as_of_date`; contribution is constant in real terms |
| `REAL` | `REAL` | Forbidden | Use the supplied real return directly; contribution is constant in real terms |
| `REAL` | `NOMINAL` | Not supported initially | Validation error; never reinflate silently |

For nominal return to real output:

```text
real_annual_rate = (1 + nominal_annual_rate) / (1 + inflation_rate) - 1
```

Any inconsistent combination is a validation error. Goals does not currently define whether `target_amount` is future nominal money or current purchasing power; Goal Planning requests must therefore declare `target_value_basis = NOMINAL | REAL` (or an exactly equivalent approved name) without changing the Goals schema in this contract-lock task.

**Horizon decision:** A projection supplies exactly one of `horizon_months` or `target_date`. The supported horizon is 1 through 1,200 complete monthly cycles. The 1,200-month maximum is a series-size and computational guardrail, not a market forecast. Dates compare at `YYYY-MM` granularity: every day in the same month is the same target month, and future UI language must say “até mês/ano,” not promise an exact day.

**Precision decision:** Monetary inputs are Decimal with at most two decimal places; fractional-cent inputs are validation errors. Rates are Decimal. The calculation context has at least 34 digits, and the equivalent monthly rate retains at least 18 decimal places. Monthly projected monetary return is quantized to `Decimal("0.01")` with `ROUND_HALF_EVEN`; the cent-scale ending wealth becomes the next period's opening wealth. Financial API values serialize as strings and null remains JSON `null`. The frontend formats but never recalculates projection truth.

**Forward equation and output:** With `q` as the approved monetary quantization:

```text
projected_return[t] = q(opening_wealth[t] * monthly_rate)
ending_wealth[t] = opening_wealth[t] + projected_return[t] + contribution[t]
opening_wealth[t+1] = ending_wealth[t]
```

Each period exposes `period`, `period_end`, `opening_wealth`, `contribution`, `projected_return`, `ending_wealth`, `cumulative_contributions`, and `cumulative_projected_growth`. The summary exposes initial/final wealth, total contributions, total projected growth, assumptions, provenance, `as_of`, scope, and conditional-result disclaimer metadata. No generative narrative belongs to the engine result.

**Target-date solver:** It reuses the Forward Projection Engine month by month and returns `ALREADY_ACHIEVED`, `ACHIEVED`, `UNREACHABLE`, or `NOT_REACHED_WITHIN_HORIZON`. `UNREACHABLE` is used only when impossibility is mathematically demonstrated; exhausting 1,200 months alone produces `NOT_REACHED_WITHIN_HORIZON`. Missing facts produce orchestration-layer `INSUFFICIENT_DATA`; invalid mathematical inputs are validation errors.

**Required-contribution solver:** It returns `ALREADY_ACHIEVED`, `ZERO_CONTRIBUTION_REQUIRED`, `SOLVED`, `IMPOSSIBLE_HORIZON`, or `OUT_OF_SUPPORTED_RANGE`. It performs monotonic binary search over integer cents and uses the same Forward Projection Engine as its oracle. The result is the smallest cent-scale `C` such that ending wealth reaches the target: `C` succeeds and `C - 0.01` fails unless `C = 0`. The upper bound may expand dynamically; any technical bound must be documented as computational protection, never as a financially reasonable maximum.

**Goal timing and eligibility:** Approved Planning statuses are `PROJECTED_EARLY`, `PROJECTED_ON_TIME`, `PROJECTED_LATE`, `ALREADY_ACHIEVED`, `NOT_REACHED_WITHIN_HORIZON`, `INSUFFICIENT_DATA`, and `NOT_APPLICABLE`. They compare achievement month directly with Goal target month and use no percentage threshold. Initially eligible amount-based types are `EMERGENCY_RESERVE`, `TRAVEL`, `PURCHASE`, `CUSTOM`, `WEALTH_TARGET`, and `INVESTMENT_TARGET`. `RETIREMENT` and `FINANCIAL_INDEPENDENCE` belong to Phase 10.4; `DIVIDEND_INCOME` requires a specific income/yield contract. `PAUSED` and `CANCELLED` goals are not projected automatically.

**Goal status eligibility — TSK-10.3.5-R clarification (2026-09-17):** `GoalStatus.ACTIVE` is the **only** lifecycle status eligible for forward Planning 10.3. `GoalStatus.ACHIEVED` is a persisted/manual lifecycle fact in the Goals domain that does **not** prove `current_amount >= target_amount` and must produce `GoalPlanningStatus.NOT_APPLICABLE` without calling `TargetAchievementSolver`. `GoalStatus.PAUSED` and `GoalStatus.CANCELLED` remain `NOT_APPLICABLE`. `GoalPlanningStatus.ALREADY_ACHIEVED` is a strictly mathematical result produced by `TargetAchievementSolver` only when an `ACTIVE` Goal's selected `InitialWealthFact` amount is already at or above target. `GoalStatus.ACHIEVED` (lifecycle) and `GoalPlanningStatus.ALREADY_ACHIEVED` (mathematical) are **not equivalent** and must never be synchronized automatically. Eligibility is determined before consuming or validating projection-specific inputs, including target basis/output compatibility, selected Goal-current-amount provenance, and Goal deadline; a non-projectable Goal returns `NOT_APPLICABLE` without solver execution. No reconciliation engine, status-mismatch detection, or automatic correction of lifecycle vs monetary facts is performed in Phase 10.3.


**Consequences:** All future projection, solver, Goal integration, API, UI, and Retirement/FIRE reuse must conform to this single mathematical contract. An independent Decimal oracle or spreadsheet must validate implementations; production code cannot be its own oracle.

---

## ADR-021: Planning Scenario Semantics and Lifecycle
**Status:** APPROVED
**Date locked:** 2026-09-16
**Context:** Planning must distinguish observed surplus, stored intent, explicit simulation inputs, and any future derived capacity. Scenario comparison must remain deterministic, non-advisory, and isolated from real financial state.

**Contribution semantics:** The following concepts are independent:
- `realized_savings_amount` — Health's realized surplus or deficit;
- `goal_planned_monthly_contribution` — the user's stored Goal plan;
- `scenario_monthly_contribution` — the explicit non-negative input for one Planning scenario;
- `sustainable_monthly_contribution_capacity` — a future derived capacity with no approved formula.

No value becomes another automatically. In particular, `savings_amount` is not sustainable capacity, and a Goal contribution is not the scenario contribution unless the user explicitly selects or copies it.

**Archetype decision:** `CONSERVATIVE`, `BASE`, and `OPTIMISTIC` are scenario identities/slots only. They contain no hardcoded rates. The user supplies all assumptions. The core does not require `optimistic > base > conservative`; a future UI may warn about unusual ordering but must not change values.

**Comparison decision:** Comparable scenarios share `as_of_date`, horizon, target, output mode, `END_OF_MONTH` timing, and currency semantics. They may explicitly vary contribution, return, coherent inflation assumptions, and initial wealth when that difference is declared. Outputs include final-wealth delta, achievement month/date, months saved/lost, contribution delta, projected-growth delta, and assumptions. If either scenario does not reach the target, months saved/lost is `null` and the result states that temporal comparison is not applicable.

**Executable Scenario Comparison contract — TSK-10.3.6-A (2026-09-19):** A comparison contains an ordered collection of at least two immutable scenarios. Each scenario has a required, non-empty opaque string `scenario_id` that is unique within the comparison, optional free label, optional `CONSERVATIVE | BASE | OPTIMISTIC` archetype metadata, one explicit `InitialWealthFact`, and one explicit `ProjectionAssumptions`. Labels and archetypes are not identities, need not be unique, provide no rates or other assumptions, impose no economic ordering, and never select the reference. Identical assumptions are valid when IDs are distinct. There is no core maximum scenario count without demonstrated resource need.

The comparison requires an explicit `reference_scenario_id` that matches exactly one scenario. `BASE` has no automatic reference, authority, recommendation, or ranking meaning. Results preserve input scenario order; they are never reordered by wealth, achievement, contribution, return, label, or archetype.

All scenarios must have the same `ProjectionAssumptions.as_of_date`, the same `resolved_horizon_months`, the same `output_mode`, and the same `contribution_timing`. `horizon_months` and `target_date` are equivalent representations when they resolve from the shared `as_of_date` to the same number of monthly periods; differing resolved horizons are invalid and are never truncated, extended, or filled. `return_type` may differ when each assumptions object is valid and all outputs have the same mode, including comparison of nominal-to-real and real-to-real assumptions. Initial wealth amount/source/provenance may differ because every scenario declares its complete `InitialWealthFact`; results must preserve those facts and make no automatic causal attribution. Planning currently has no currency field, so comparison is limited to the same application-currency boundary; multi-currency comparison is unsupported until an explicit currency contract exists.

Target comparison is optional. Without a target, each scenario executes `ForwardProjectionEngine` once and exposes only forward-result and monetary comparison facts; achievement fields and months saved/lost are `null`/not applicable. With a target, one shared comparison-level target contains a positive finite cent-scale Decimal `target_amount` and explicit `TargetValueBasis`; scenario-specific targets are prohibited. The target basis must match the shared projection output mode, without inference or conversion. `TargetAchievementSolver` is called once per scenario and is the sole achievement authority. Its nested `projection_result` is reused for final wealth, contributions, and growth. For `ALREADY_ACHIEVED`, whose certified solver result intentionally has no projection, `ForwardProjectionEngine` runs once to produce the horizon summary; this still performs at most one financial projection for that scenario.

Money deltas use exact cent-scale Decimal `scenario value - reference value`. The reference scenario's final-wealth, total-contribution, and projected-growth deltas are `Decimal("0.00")`. `months_saved_or_lost = reference months_required - scenario months_required`: positive means the scenario achieves earlier, negative later, and zero in the same period. `ALREADY_ACHIEVED` participates as period/month zero. If either the reference or compared scenario has `UNREACHABLE` or `NOT_REACHED_WITHIN_HORIZON`, months saved/lost is `null`; a non-achieving reference therefore also has `null` for its own temporal delta. Achievement comparison uses certified monthly periods, never day differences.

The immutable result preserves the explicit reference ID, optional shared target metadata, shared comparison semantics, and an input-ordered tuple of entries. Each entry preserves scenario identity/metadata, original fact and assumptions, the complete certified `ForwardProjectionResult`, optional complete `TargetAchievementResult`, monetary summaries/deltas, achievement facts when applicable, and months saved/lost when defined. No winner, best/optimal scenario, score, ranking, rate delta, recommendation, or causal attribution is produced.

All structural and comparability rules are prevalidated for every scenario before any engine call. Any invalid scenario or engine failure aborts the whole comparison; partial results are prohibited. Execution is deterministic, stateless, transient, and conceptually `O(number_of_scenarios × resolved_horizon_months)` with at most one financial projection per scenario and no pairwise reprojection. It uses no database, scenario persistence, Goal auto-integration, Required Contribution automation, sustainable-capacity formula, historical-data forecast, or LLM calculation.

**No-forecast decision:** Portfolio historical return, CDI, IPCA, IBOV, dividend history, and Health trends may be future context only. None may become a future return, inflation, income, or contribution assumption automatically.

**Lifecycle decision:** Initial projections and comparisons are `TRANSIENT FIRST` and do not persist. Saved scenarios require a later explicit ownership, lifecycle, versioning, expiration, and provenance contract after engines and API are validated. `goals.assumptions_json` is not canonical scenario persistence.

**Sustainable-capacity contract decision — TSK-10.3.7-A (2026-09-19):** `sustainable_monthly_contribution_capacity` remains `DEFERRED — INSUFFICIENT CONTRACT / DATA`. The certified Health boundary supplies realized monthly income, expense, net cashflow/`savings_amount`, savings rate, month identity, gaps, category totals, anomaly metadata, and closed-month trends. It does not certify forward obligations, debt schedules, annual/seasonal expenses, future taxes, minimum cash or emergency-reserve policy, dependents, income continuity, salary changes, planned acquisitions, commitments outside the imported ledger, or personal risk tolerance. Raw installment metadata is not a certified future-obligation schedule. The Health aggregate also has no approved multi-currency normalization contract for this purpose.

The current read-only audit observed 17 monthly facts from `2025-05` through partial `2026-09`, including 16 continuous closed months with 12 realized surpluses and 4 realized deficits. This is useful historical evidence but does not establish a contractual lookback or minimum-history threshold. No approved rule selects all history or an arbitrary 3/6/12-month window; includes or excludes partial months; handles negative months; excludes anomaly/outlier observations; selects mean, median, percentile, minimum, or haircut; or decides whether a negative estimate remains negative or is clamped to zero. `0.00` must remain distinct from unavailable/insufficient evidence, but no result/status contract is approved while the method itself is undefined.

The word `sustainable` would imply recurring forward affordability that the certified inputs cannot establish. No realized, planned, scenario, or required contribution may be mapped automatically to this future concept. Any renewed proposal must define a historically descriptive or forward-looking meaning, complete input and currency scope, window, minimum history, partial-month/gap/deficit/anomaly handling, exact statistic, negative/zero/null semantics, and auditable provenance before implementation. It must remain informational and non-advisory, deterministic, Health-certified-only, and never replace `scenario_monthly_contribution`, `goal_planned_monthly_contribution`, or a Required Contribution result.

This deferral does not block 10.3.8. The Planning API contract audit may proceed over already certified engines using explicit scenario contributions and transient requests. Scenario persistence remains separately gated by the ownership/lifecycle/versioning contract already required above; it is not approved by this decision.

**Planning API contract decision — TSK-10.3.8-A (2026-09-20):** Planning is exposed as five authenticated, transient calculation capabilities under the existing global `/api/v1` prefix and a Planning router prefix `/planning`: `POST /projection`, `POST /target-achievement`, `POST /required-contribution`, `POST /goals/{goal_id}/projection`, and `POST /scenarios/compare`. Separate endpoints are required because their inputs, result statuses, ownership rules, and OpenAPI schemas differ; no generic operation discriminator is approved. POST expresses a complex deterministic calculation request and does not imply persistence. Sustainable Contribution Capacity has no endpoint.

Every endpoint reuses the existing bearer/JWT `get_current_user` dependency and does not create a second authentication mechanism. Authentication retains its existing `AsyncSession` dependency; certified Planning readers retain their validated synchronous `Session` contract and receive a request-scoped read session from `get_db` only when the selected source/Goal endpoint needs one. Routers must not instantiate `SessionLocal` manually, commit read requests, refactor the certified readers into HTTP calls, or share a session across incompatible sync/async boundaries. Goal lookup uses `PlanningGoalReadQuery.get_goal(goal_id, current_user.id)`, not the legacy float Goal entity/DTO path or internal HTTP. A missing Goal and a Goal owned by another user both return the existing non-enumerating `404` behavior. The Goal Planning endpoint builds `GoalPlanningFact` server-side and accepts only an explicit initial-wealth selector plus assumptions and target basis; it never accepts a caller-authored Goal fact.

The public initial-wealth request is a discriminated selector, not a serialized `InitialWealthFact`. `USER_PROVIDED_SCENARIO` accepts an explicit Decimal-string amount and explicit ISO-8601 provenance timestamp and is always labeled user-provided. `GOAL_CURRENT_AMOUNT` accepts only a Goal identifier for generic calculations, or uses the path Goal for Goal Planning; the server performs the owned Decimal read and constructs source, scope, as-of, and provenance. The caller cannot supply a Goal amount or certified provenance. `INVESTMENT_PORTFOLIO_SNAPSHOT` is not exposed by the authenticated API now: the current snapshot `account_id` is an external MyProfit scope with no certified relation to the authenticated user. The domain/read capability remains valid, but API use is deferred until an explicit authorized account boundary exists. Local/single-user deployment is not authorization and does not relax this rule.

Requests use strict JSON decimal strings for every monetary value and rate; JSON numbers, floats, booleans, and silent numeric coercion are not accepted in the Planning truth path. Money responses and money deltas are decimal strings, rates are exact decimal strings, missing values are JSON `null`, dates are ISO `YYYY-MM-DD`, provenance timestamps are ISO-8601 date-times without inventing a timezone, and enums use their existing canonical values. Projection assumptions remain explicit: as-of date, contribution, return, return/output modes, inflation when required, exactly one horizon selector, `EFFECTIVE_ANNUAL`, and `END_OF_MONTH`. The API never supplies return, inflation, contribution, horizon, target basis, initial-wealth origin, or comparison reference on the caller's behalf.

The Forward Projection request carries one supported initial-wealth selector and one complete assumptions object. Target Achievement and Required Contribution additionally carry one positive cent-scale target and explicit `TargetValueBasis` matching the assumptions output mode; the API performs no target conversion. The required-contribution assumptions field is a template exactly as defined by the domain, and its supplied scenario contribution is not treated as the required answer. Goal Planning uses the owned Goal target/deadline/type/status and preserves the domain's `NOT_APPLICABLE`, `INSUFFICIENT_DATA`, mathematical achievement, and monthly timing statuses. Scenario Comparison mirrors the validated contract: at least two ordered scenario definitions, explicit unique IDs, explicit reference ID, explicit initial-wealth selector and assumptions per scenario, optional label/archetype, and an optional shared target/basis pair. `BASE` is never an implicit reference, and the API does not rank or recommend.

API response DTOs are stable boundary models mapped from domain results; internal dataclasses are not returned directly. Mapping copies certified facts, assumptions, statuses, provenance, periods, summaries, and nested solver/comparison results without recalculating, re-rounding, searching crossings, or flattening away source identity. The initial contract returns both summary and the complete monthly period tuple (up to the approved 1,200 months), including the complete certified projection nested in solver/comparison results when present. No pagination or `include_periods` variant is approved in the initial contract. Server-certified provenance exposes source, scope, temporal anchor, source type, relevant Goal/account/reference/run identity, and source timestamps when present; internal table names are not public API fields.

FastAPI/Pydantic structural errors and domain input `TypeError`/`ValueError` map to `422`; an explicitly selected certified fact that is absent, such as a null Goal current amount, also maps to `422` rather than fabricating zero **when an applicable calculation requires that fact**. For the owned Goal Planning capability, `GoalPlanningService` determines lifecycle/type applicability before the API consumes projection-specific source values: a structurally valid non-projectable request returns `200 / NOT_APPLICABLE` without resolving an unavailable selected Goal current amount, while an ACTIVE eligible Goal with that required fact unavailable returns `422`. Malformed request representation remains `422` before domain execution. Authentication failures retain `401`; missing/wrong-owner Goals retain `404`; legitimate domain outcomes such as `NOT_APPLICABLE`, `INSUFFICIENT_DATA`, `UNREACHABLE`, `NOT_REACHED_WITHIN_HORIZON`, and Required Contribution result statuses are successful `200` payloads. Unexpected `ArithmeticError`, impossible engine invariants, and unclassified failures are `500` and must not be converted into financial results. The existing FastAPI `detail` response convention remains the error envelope; implementation must not expose internal exception traces.

The transient API is deterministic relative to its complete request and the server-certified facts read for that request. No calculation endpoint writes database state, calls an LLM, reads historical market values into assumptions, or invokes Sustainable Contribution Capacity. The application currently has no approved Planning-specific scenario-count cap, pagination rule, body-size rule, or rate limiter. The domain's no-arbitrary-maximum decision remains intact: requests are validated atomically and never truncated. Transport-level body/rate/time protection may be added later as infrastructure policy after measurement, without changing financial semantics.

**Scenario persistence decision — TSK-10.3.8-A (2026-09-20):** `PERSISTENCE DEFERRED — TRANSIENT API FIRST`. No concrete MVP need overrides ADR-021's transient-first rule, and the required storage contract is incomplete: owner and access semantics beyond authentication; saved-scenario identity/name uniqueness; draft/active/archive/delete lifecycle; mutable update versus immutable revision history; source snapshot versus live-reference provenance; refresh/staleness behavior after Goal/portfolio/as-of changes; timestamps and expiration; duplication; Goal relation; deletion policy; and migration/schema shape are not approved. `goals.assumptions_json` remains prohibited as canonical scenario storage. Calculation and any future save action must remain separate endpoints. No scenario table, migration, repository, CRUD route, or persistence test is authorized by this decision.

**10.3.8 execution split:** `10.3.8-A` locks this contract. `10.3.8-B` adds the authenticated Planning router, strict Decimal-string DTO primitives, source-selector boundary, response mappers, dependency wiring, and error mapping. `10.3.8-C` adds Forward Projection, Target Achievement, and Required Contribution endpoints. `10.3.8-D` adds the owned Goal Planning endpoint. `10.3.8-E` adds Scenario Comparison. `10.3.8-F` performs independent API integration/OpenAPI/security-boundary validation and stabilization. Persistence is not an implementation subphase until a separate contract is approved.

**Planning API foundation implementation — TSK-10.3.8-B (2026-09-20):** The app now includes the intentionally endpoint-free relative `/planning` router under `/api/v1`; empty-router registration is not a healthcheck or public financial capability. Shared annotations retain existing JWT authentication and give future certified readers the synchronous request-scoped `get_db` session without changing readers, auth, or global error behavior. API DTO primitives accept only finite, plain JSON decimal strings and preserve their declared Decimal exponent until the domain validates it. Date-only inputs are strict ISO dates; user-provided provenance is an explicit ISO date-time without clock/timezone invention. The only public initial-wealth selectors are user-provided amount/timestamp and Goal ID; portfolio snapshots and caller-authored certified facts are structurally excluded. Pure mappers expose approved source/as-of/provenance without `source_table`; local translation maps validation to `422` and arithmetic/invariant failures to generic `500`. No engine, reader, database operation, endpoint, persistence, migration, or capacity logic was called or created.

**Planning API foundation independent validation — TSK-10.3.8-B-V (2026-09-20):** VALIDATED. Independent JSON parsing, source-forgery, declared-scale, mapper serialization, startup/OpenAPI, dependency-boundary, and regression checks passed. The foundation remains endpoint-free; no financial engine, persistence, capacity capability, or global API behavior was added.

**Planning calculation endpoints implementation — TSK-10.3.8-C (2026-09-21):** `POST /api/v1/planning/projection`, `/target-achievement`, and `/required-contribution` now authenticate through the existing dependency, construct only user-provided facts locally, and resolve selected Goal current amount through the owned synchronous Decimal reader. Missing and wrong-owner Goals return the same `404`; a null selected Goal amount is `422`; portfolio input remains structurally absent. Each route delegates once to exactly its certified engine and maps complete certified results, including Decimal-string timelines, nested projection status, and solver statuses; compatible target-basis is checked at the boundary without conversion. Legitimate non-achievement solver outcomes remain `200`; validation is local `422` and unexpected arithmetic maps to generic `500`. There is no recalculation, write, persistence, Goal Planning or Scenario endpoint, capacity feature, or financial-domain change. `10.3.8-C = IMPLEMENTED / READY FOR VALIDATION`; `10.3.8-D = READY / NOT STARTED`.

**Planning calculation endpoints independent validation — TSK-10.3.8-C-V (2026-09-21):** VALIDATED. An independent HTTP/OpenAPI/code audit confirmed all three and only three approved authenticated routes; strict decimal-string requests and exact declared response precision; server-owned Goal resolution with 404 non-enumeration and null-fact `422`; canonical `TargetValueBasis` with no conversion; one certified engine delegation per successful route; valid domain-status `200`; local validation/arithmetic errors; controlled provenance; sync reader versus async authentication boundary; no float, second financial math, write, persistence, Sustainable Capacity, Goal Planning, or Scenario comparison operation. Test-only coverage additions passed. `10.3.8-D = READY / NOT STARTED`.

**Owned Goal Planning endpoint implementation — TSK-10.3.8-D (2026-09-21):** `POST /api/v1/planning/goals/{goal_id}/projection` is implemented and awaits independent validation. The authenticated route obtains its Goal only through owned `PlanningGoalReadQuery` read semantics, builds the complete `GoalPlanningFact` server-side, accepts no client Goal lifecycle/type/amount/deadline/provenance fields, and delegates exactly once to `GoalPlanningService`. It deliberately does not duplicate eligibility; the service preserves ACTIVE-only applicability, lifecycle `ACHIEVED` distinct from mathematical `ALREADY_ACHIEVED`, reserved/non-active `NOT_APPLICABLE`, optional target-basis `INSUFFICIENT_DATA`, strict ACTIVE basis validation, timing, and nested target semantics. The path-specific `GOAL_CURRENT_AMOUNT` selector cannot name another Goal; user-provided wealth remains user-provided. All output Decimals are strings. Read-only requests perform no Goal mutation, persistence, Required Contribution automation, Scenario Comparison, capacity calculation, or financial math. `10.3.8-D = IMPLEMENTED / READY FOR VALIDATION`; `10.3.8-E = READY / NOT STARTED`.

**Owned Goal source/applicability reconciliation — TSK-10.3.8-D-R1-SOL (2026-09-22):** The apparent conflict between ADR-020 applicability-first behavior and the 10.3.8-A unavailable-certified-fact rule is resolved by classifying Goal current amount resolution as projection-specific semantic consumption, not request structure. `GoalPlanningService` now exposes the same pure lifecycle/type applicability decision before source resolution; the router consults it without importing or reproducing Goal status/type rules. Non-projectable Goals return `200 / NOT_APPLICABLE` even when their selected Goal current amount is null, with no dummy fact and no target-solver call. ACTIVE eligible Goals still require the selected fact and return `422` when it is unavailable. Structural JSON/DTO errors remain `422` before service execution. The domain stays IO-free, and `10.3.8-D = RECONCILED / READY FOR FINAL REVALIDATION`; `10.3.8-E = NOT STARTED`.

**Owned Goal Planning endpoint final independent validation — TSK-10.3.8-D-V2 (2026-09-23):** VALIDATED. Independent HTTP/domain inspection confirmed `preflight_applicability()` and `evaluate()` share one lifecycle/type authority: all real `GoalStatus × GoalType` combinations are covered, with no duplicate router eligibility rule. The preflight is pure and does not resolve wealth, validate basis for applicable Goals, call a solver, calculate timing, or access IO. HTTP probes prove `lookup → preflight → source resolution → evaluate` for ACTIVE Goals and stop after preflight for non-projectable Goals, including available and unavailable Goal current amount. Decimal structural failures remain `422`; all valid non-projectable outcomes are `200 / NOT_APPLICABLE`; applicable missing source remains `422`. No financial engine, persistence, Goal write, or Scenario endpoint changed. `10.3.8-D = VALIDATED`; `10.3.8-E = READY / NOT STARTED`.

**Scenario Comparison endpoint implementation — TSK-10.3.8-E (2026-09-23):** `POST /api/v1/planning/scenarios/compare` is implemented and awaits independent validation. Its request contains an ordered tuple of explicit scenario IDs, per-scenario approved wealth selector and assumptions, optional label/archetype metadata, explicit reference ID, and an optional shared target/basis pair. The authenticated boundary resolves every selected Goal current amount by `goal_id + current_user.id` through the certified synchronous reader before exactly one `ScenarioComparisonEngine.compare()` call; a missing/wrong-owner Goal is the existing non-enumerating `404`, and a selected null Goal amount is `422`. No Goal lifecycle/applicability behavior is applied because a comparison source is always necessary to execute that explicit scenario. The mapper copies the engine's complete ordered nested results, Decimal values, candidate-minus-reference money deltas, and reference-minus-candidate temporal deltas without sorting, calculating, ranking, persistence, or recommendation. `INVESTMENT_PORTFOLIO_SNAPSHOT` remains structurally unavailable; no Goal Planning, Required Contribution, Health/Sustainable Capacity, database write, or second financial math is introduced. `10.3.8-E = IMPLEMENTED / READY FOR VALIDATION`; `10.3.8-F = READY / NOT STARTED`.

**Scenario Comparison endpoint independent validation — TSK-10.3.8-E-V (2026-09-23):** VALIDATED. Independent HTTP/domain/OpenAPI validation confirmed explicit ID/reference semantics, input-order preservation, metadata-only archetypes, strict Decimal strings, server-resolved owned Goal current amounts, atomic source resolution, no Goal Planning applicability leakage, resolved-horizon equivalence, permitted ReturnType variation, shared target/basis strictness, and exactly one `ScenarioComparisonEngine.compare()` call. Added test-only probes prove domain prevalidation reaches no financial subengine, any first/middle/last input scenario can be the reference without reordering, and the mapper copies certified money/temporal deltas without recalculation. No ranking/recommendation, persistence, database write, Goal mutation, portfolio source, Goal Planning, Required Contribution, Sustainable Capacity, or second financial math exists. Focused HTTP suite: `42 passed`; Planning domain regressions `323`; Goals `65`; Health `68`; general `585 passed, 2 historical Investments/MagicMock failures`. `10.3.8-E = VALIDATED`; `10.3.8-F = READY / NOT STARTED`.

**Planning API integration and stabilization — TSK-10.3.8-F (2026-09-23):** AUTOMATED VALIDATION PASSED / READY FOR MANUAL SMOKE. Cross-endpoint inspection and real HTTP tests confirm exactly five secured Planning POST operations under `/api/v1/planning`, unique operation IDs, the existing async-auth plus synchronous certified-reader split, uniform strict Decimal request rejection, portfolio source rejection, non-enumerating Goal ownership, deterministic 1,200-month serialization, and no write/persistence/ranking/advice/LLM or duplicated API math. No production fix was required. Integration `5`; B–E API `147`; Planning domain `323`; Goals `65`; Health `68`; general `593 passed, 2 historical Investments/MagicMock failures`. Macro `10.3.8` remains unvalidated pending user Swagger smoke; `10.3.7` and persistence remain deferred.

**Consequences:** Scenarios never modify Goals, Health, portfolio snapshots, or other real financial data. Scenario output is factual conditional comparison, not a recommendation.

---

## ADR-022: Retirement/FIRE and Portfolio Intelligence Boundary
**Status:** APPROVED
**Date locked:** 2026-09-16
**Context:** Product vision includes generic Planning, retirement, financial independence, and portfolio intelligence. Their responsibilities must be separated without duplicating the deterministic engines.

**Phase decision:** Phase 10.4 is named `Retirement & Financial Independence (FIRE)` and is one combined phase. It will reuse Phase 10.3 Forward Projection, target-date solver, required-contribution solver, scenario comparison, inflation, contribution, wealth, and horizon contracts.

**Modes:** Retirement mode asks, “With a target age, what will my financial situation be?” FIRE mode asks, “When do my wealth/income facts satisfy the approved independence contract?” Phase 10.4 will add age, desired retirement age, desired income, FIRE target wealth, potential/passive income, withdrawal/sustainable-income assumptions, FI progress, and estimated FI age/date.

**Portfolio boundary:** Phase 10.5 remains `Portfolio Intelligence` and owns allocation, concentration, diversification, rebalance analysis, portfolio quality, and asset-level intelligence. Planning does not select investments, recommend assets, rebalance portfolios, or infer expected returns from portfolio composition/history.

**Consequences:** ADR-022 establishes boundaries only. TSK-10.3.0-A implements no Retirement, FIRE, or Portfolio Intelligence schema, service, endpoint, or UI. Phase 10.4 cannot begin until Phase 10.3 is complete and explicitly closed.

---

## ADR-023: Investment Portfolio Initial Wealth Source
**Status:** APPROVED
**Date locked:** 2026-09-24
**Temporal semantics refined:** 2026-09-25 (TSK-10.3.10A-R1)

**Context:** ADR-019 approved `INVESTMENT_PORTFOLIO_SNAPSHOT` as one explicit alternative initial-wealth origin, while TSK-10.3.8-A correctly withheld it from the authenticated API because `portfolio_snapshots.account_id` had no approved relation to `current_user`. The live model confirms that this identifier is a user-entered MyProfit portfolio scope, not a key in the Pierre/Core `accounts` table. The latter has composite key `(provider, external_id)`, contains no MyProfit row in the current database, and does not own portfolio snapshots. `portfolio_snapshots.run_id` does resolve to `sync_logs.user_id`, but that is provenance of the latest UPSERT, not an immutable account-ownership relation.

The read-only 10.3.10A audit observed one active application user, seven Pierre/Core account rows, one MyProfit portfolio scope (`Myprofit`), and 49 unique monthly portfolio snapshots from `2022-09` through `2026-09`. Every current portfolio row has `source_type = MYPROFIT_EVOLUCAO`, a non-null run that resolves to a successful import by the single application user, and no duplicate `(account_id, reference_month)`. These facts justify a guarded single-tenant contract; they do not justify general multi-user account ownership.

**Ownership decision:** 10.3.10B may expose this source only under an explicit single-user/single-tenant invariant. The server authenticates normally, verifies that the database contains exactly one application user and that this identity equals `current_user.id`, compares UUID identity semantically rather than relying on hyphenated storage text, and derives the set of MyProfit portfolio scopes from certified `MYPROFIT_EVOLUCAO` snapshots whose non-null `run_id` resolves to a successful sync owned by that user. The complete scope must be internally consistent: null/unmatched runs or another owner make the source unavailable. Zero eligible scopes produces `422`; exactly one becomes the canonical scope; more than one produces `422` as ambiguous. The resolver must never select the first row. Before any multi-user deployment or multiple MyProfit portfolios are supported, an explicit user-to-investment-account model and a new account-selection contract are required.

**Selector and trust decision:** The public selector is exactly `{ "source": "INVESTMENT_PORTFOLIO_SNAPSHOT" }` for generic, Goal Planning, and comparison requests. The caller supplies no account identifier, amount, currency, snapshot date, run identifier, scope, or certified provenance. The backend resolves and re-reads the canonical scope for each request. Existing `USER_PROVIDED_SCENARIO` and `GOAL_CURRENT_AMOUNT` semantics do not change, and Planning still consumes exactly one selected source without aggregation or fallback.

**Snapshot decision:** The authoritative value is only `portfolio_snapshots.patrimonio`; Planning does not sum positions, current quotes, cash, Goals, or other sources. The MyProfit source field is only `Data = Mmm-YYYY`; the parser converts it to `reference_month = YYYY-MM` and receives no source day or financial-observation timestamp. A live `2026-09` row was first persisted on 2026-09-05 and updated again on 2026-09-24, before September month-end. Therefore `reference_month` is a monthly evolution period/bucket: closed periods may contain their final monthly value, while the current period may be month-to-date. It is not universally a month-end-position timestamp.

For `ProjectionAssumptions.as_of_date`, the resolver selects the greatest `reference_month` in the canonical scope such that (a) the reference month is not after the as-of calendar month and (b) the current persisted version has non-null `updated_at` whose calendar date is not after `as_of_date`. `source_type` must be `MYPROFIT_EVOLUCAO`, and the selected row's run must satisfy the ownership rule above. This remains `LATEST ELIGIBLE AS OF`: the same-month row is eligible once its current version has been persisted, because it is not contractually a future month-end value; a row imported after the requested as-of remains ineligible. The predicate is conservative and safe against look-ahead, but it does not create an exact daily valuation.

`portfolio_snapshots.updated_at` is assigned by the confirmation use case with `datetime.utcnow()` in every INSERT/UPSERT. It means **snapshot-version-updated-at** (technical persistence/import time), not source financial observation time. 10.3.10B must not map it to `PlanningFactAsOf.observed_at`; the portfolio fact's financial as-of carries `reference_month`, while public provenance retains the existing `updated_at` field documented with this technical meaning. Provenance also carries source/scope, the opaque portfolio scope, `MYPROFIT_EVOLUCAO`, run identity, and approved source/persistence timestamps. Internal table names, SQL, ORM state, and secrets remain excluded. The composite primary key `(account_id, reference_month)` makes same-month duplicates impossible, so no secondary tie-break is invented. If that invariant changes or corruption produces duplicates, implementation must stop for reconciliation rather than choose arbitrarily.

**Temporal limitation:** `HISTORICAL AS-OF UNSUPPORTED WITH CURRENT DATA MODEL` as a reproducible time-travel guarantee. The mutable UPSERT table does not retain prior versions or a source financial-observation timestamp. Current/future scenarios are supported from the latest eligible current row version; a historical request can succeed only when that same currently persisted version was already persisted no later than `as_of_date`. A later UPSERT cannot reconstruct or prove the prior version and must make that row unavailable for the earlier as-of. If all available snapshots are future by reference month or snapshot-version update time, the selected fact is unavailable and the API returns `422`. No 30/60/90-day staleness threshold is approved; reference month and version-update time remain visible in provenance.

**Value, currency, and coverage decision:** `patrimonio` is `Numeric(18, 2)` and must cross the Planning read boundary as `Decimal`, never through existing float-valued Investments HTTP responses. It means **investment portfolio wealth, not net worth**. The current source is limited to the application's single BRL currency context: no FX conversion, mixed-currency aggregation, or currency inference is performed. The current asset catalog is BRL-only, and the MyProfit evolution import is the governed BRL portfolio-total source; if that deployment assumption changes, this source must be disabled pending a currency-aware contract. The aggregate's asset-class coverage is provider-defined and not derivable from `portfolio_snapshots`; the UI/API must not claim that it covers cash, liabilities, real estate, every foreign holding, or all personal wealth.

**Endpoint and orchestration decision:** Projection, Target Achievement, Required Contribution, Goal Planning, and Scenario Comparison may all accept this selector. Generic calculations resolve the fact before their certified engine call. Goal Planning preserves ADR-020 applicability precedence: a non-projectable Goal returns `NOT_APPLICABLE` without consuming the portfolio source, while an applicable Goal resolves it or returns `422`. Scenario Comparison resolves every scenario source atomically before the one comparison-engine call; each scenario uses its own `as_of_date`, and no partial comparison is returned. Reusing an identical resolved fact within one request is an optional application optimization only and may not change provenance or semantics.

**Architecture and migration decision:** `NO MIGRATION REQUIRED` for the locked single-tenant integration. 10.3.10B1 added an ownership-aware, read-only application resolver and as-of-aware Decimal portfolio fact construction; pure Planning engines remain database-free. B2 alone may add the public API selector and endpoint wiring. Existing source/scope enums and public provenance fields already represent the fact. API and frontend selector unions gain the portfolio discriminant only in their approved later microprocesses, while engine mathematics and the two existing source contracts remain unchanged. A future multi-user or multi-portfolio design requires a separate migration/ADR for an explicit investment-account entity and owner relation; ADR-014 is not repaired here.

**TSK-10.3.10B2 implementation record (2026-09-25):** VALIDATED. The source-only public discriminant is available to all five authenticated Planning endpoints. The API forwards only request `as_of_date`, sync Planning session, and authenticated user identity to the B1 resolver; it does not select an account, query snapshots/runs, manufacture provenance, or accept a certified amount. Goal Planning still preflights before source resolution, and Scenario Comparison resolves all facts before its one engine invocation. Public provenance keeps `reference_month` and existing technical `updated_at`; `PlanningFactAsOf.observed_at` remains null. No frontend, migration, schema, engine, persistence, or write path was added.

**Frontend decision:** The UI may offer “Carteira de investimentos MyProfit” as an explicit source and may display the server-certified amount and dates returned by the calculation. No current authenticated preview contract exists, so 10.3.10B must not read Investments endpoints, calculate a total, or send a certified amount from the browser. A pre-calculation preview is optional future work requiring its own ownership-aware read endpoint. Broader Planning visual/UX refinements remain deliberately deferred for later user review after functional consolidation.

**TSK-10.3.10B3 implementation record (2026-09-25):** The Planning frontend now offers “Carteira de investimentos MyProfit” through the existing shared source form and all five certified Planning capabilities. The discriminated request builder emits exactly `{ "source": "INVESTMENT_PORTFOLIO_SNAPSHOT" }`, so prior user-provided amount and timestamp state cannot contaminate a portfolio request. The UI performs no preview, Investments lookup, account selection, certified amount/provenance submission, portfolio aggregation, or financial calculation. Returned certified facts identify the portfolio source, render `reference_month` only as `MM/YYYY`, present `updated_at` only as technical import/update time, and omit null `observed_at`. Availability failures remain safe UI errors with no zero or manual-source fallback. `10.3.10B3 = IMPLEMENTED / READY FOR MANUAL VALIDATION`; `10.3.10B4 = READY / NOT STARTED`.

**TSK-10.3.10B4 independent/adversarial validation (2026-09-25):** `VALIDATED — 10.3.10B COMPLETE`. Independent code, contract, OpenAPI, static, and executable-test review confirmed semantic UUID ownership, the exact one-user tenant guard, zero/one/many scope behavior, complete run provenance validation, isolation from Core accounts, Numeric→Decimal→JSON string→TypeScript string fidelity, same-month eligibility, post-as-of/future-bucket rejection, prior-month fallback, null portfolio `observed_at`, and monthly-only `reference_month`. All five secured POSTs expose the source-only selector; client forgery is structurally forbidden; Goal applicability-first, comparison atomicity/order/reference, and frontend source isolation remain intact. B1 `16`, Planning API `157`, and Planning domain `323` tests passed; general units were `614 passed, 2 historical Investments/MagicMock failures`; TypeScript, focused ESLint, and production build passed. The user separately confirmed all five B3 capability smokes and visual provenance checks. No production, engine, migration, schema, dependency, persistence, commit, or push change occurred during validation. `10.3.10B1–B4 = VALIDATED`; macro `10.3.10B = VALIDATED / COMPLETE`; `10.3.11 = READY / NOT STARTED`.

**TSK-10.3.11 Planning integration & stabilization (2026-09-26):** `VALIDATED / STABILIZED — READY FOR 10.3.12`. Consolidated review retained exactly five authenticated Planning POST capabilities and the certified source matrix: generic endpoints and Scenario Comparison accept user-provided, Goal-current, and portfolio selectors; the Goal-path endpoint accepts user-provided, path-Goal-current, and portfolio selectors. ADR-019 one-source semantics, ADR-020 nominal/real/timing/period-zero/horizon semantics, ADR-021 scenario ordering/reference/delta semantics, ADR-022 boundaries, and ADR-023 portfolio semantics remained intact. Planning API `157 passed`; domain plus resolver `339 passed`; general units `614 passed, 2` unchanged historical Investments/MagicMock failures; TypeScript, focused Planning lint, and production build passed. No Planning production defect, feature, migration, persistence, or broad UI redesign was required. Swagger OAuth smoke, ADR-014, the two Investments tests, Recharts SSR warning, missing frontend runner, and broader UX refinement remain accepted debt. `10.3.12 = READY / NOT STARTED`.

**TSK-10.3.12 Planning final validation & closure (2026-09-26):** `PHASE 10.3 CLOSED / VALIDATED`. Closure consolidated the previously accepted 10.3.9, 10.3.10, and 10.3.10B3 manual evidence with final proportional checks: `269 passed` across API integration, ADR-023 resolver, and representative projection/target/required/Goal/scenario domain suites; the real OpenAPI still exposes exactly five secured Planning POST operations with unique IDs and portfolio selector; TypeScript, focused Planning lint, and production build passed. No production change occurred since stabilization and no defect, contract gap, or scope leakage was found. The general baseline remains `614 passed, 2` known historical Investments/MagicMock failures. Phase boundaries remain explicit: sustainable capacity deferred, transient/no persistence, portfolio wealth not net worth/realtime/full historical time travel, no multi-user ownership model, no FIRE, Portfolio Intelligence, or LLM. `10.3.12 = VALIDATED / CLOSED`; `10.4 = READY / NOT STARTED`; `POST-10.3 PLANNING UX REFINEMENT REVIEW = PENDING USER FEEDBACK`.

---

## ADR-024: Post-10.3 Planning UX and Simplicity Contract
**Status:** APPROVED

**Date locked:** 2026-09-26

**Authoritative specification:** `PLANNING_UX_CONTRACT.md`

**Context:** Phase 10.3 is financially correct and closed, but the validated interface exposes five technical capabilities, repeated assumptions, implementation-detail copy, raw decimal strings, and manual temporal fields. Current screenshots confirm duplicated page chrome, low answer hierarchy, unreadable money/rate precision, and full assumptions repeated per comparison scenario.

**Decision:** Adopt the `Quiet Financial OS` direction and expose three user intentions — `Simular`, `Objetivo`, and `Comparar` — while preserving the five certified endpoints. Planning and Financial Health remove redundant visible eyebrow/title/architecture copy but retain semantic `sr-only` page headings. Common Planning entry becomes source, contribution, expected annual percentage, and horizon; today and manual observation time are captured at submit unless explicitly overridden. Nominal/nominal is the visible standard interpretation, not a hidden numeric assumption. Exact pt-BR money/rate/date input and display use string-safe lexical adapters; financial card/text truth never crosses binary float. Comparison moves required-equal values into shared context while preserving per-scenario source, contribution, return type/rate, conditional inflation, metadata, explicit reference, and user order.

**Result and interaction decision:** Results lead with the answer, not certification language. Provenance remains available in compressed chips/details. Recharts continues to consume only certified period data through the existing rendering-only numeric boundary; certified target lines and achievement markers are permitted without local crossing logic. Skeletons and 150–250 ms CSS transitions are approved; numeric counters and an initial Motion dependency are not. Tailwind, the small existing UI primitive layer, Radix/shadcn-compatible components, and Recharts remain the stack.

**Future boundary:** Certified portfolio preview, assumption-reference facts, and Goal-derived presets each require a separate small backend contract. Historical portfolio performance requires a cashflow-aware certified engine/read model. FIRE, Portfolio Intelligence, Copilot scenario drafting, Goal proposals, and Planning persistence remain future phases/contracts. Direct browser MyProfit/Investments preview, automatic financial assumptions, ranking/advice, direct BCB assumption fetches, and `localStorage` scenario persistence are rejected.

**Consequences:** Implementation is split into UX-B1 through UX-B7 as defined in `PLANNING_UX_CONTRACT.md`. No production code, financial engine, API, schema, persistence, or 10.4 work is authorized by this ADR alone. Phase 10.3 remains `VALIDATED / CLOSED`; 10.4 remains `READY / NOT STARTED`.

---

## ADR-025: FIRE Deterministic Contract and Planning Composition

**Status:** ACCEPTED

**Date locked:** 2026-09-29

**Authoritative specification:** `FIRE_CONTRACT.md`

**Context:** Phase 10.3 is validated and closed with certified deterministic projection, target-achievement, required-contribution, nominal/real, precision, provenance, and initial-wealth capabilities. Phase 10.4 must define financial independence without duplicating those engines or promoting historical Health, investment, dividend, or macro data into future assumptions.

**Architecture decision:** FIRE is a thin deterministic domain and orchestration layer. It owns explicit retirement-spending and withdrawal-rate validation, FIRE target construction, summary status, gap, unbounded progress, and conditional withdrawal capacity. Planning remains the sole authority for initial-wealth resolution, projection, compound growth, contribution timing, nominal-to-real Fisher conversion, target achievement, required contribution, and their statuses. A second FIRE projection or solver engine is prohibited.

**Target decision:** `monthly_retirement_spending` is an explicit positive cent-scale Decimal assumption in current purchasing power. `assumed_annual_withdrawal_rate` is an explicit annual Decimal fraction strictly between zero and one, with no default and no “safe” or guaranteed meaning. The real target is calculated as:

```text
annual_required_spending = monthly_retirement_spending * 12
raw_fire_target = annual_required_spending / assumed_annual_withdrawal_rate
fire_target = raw_fire_target quantized to 0.01 with ROUND_CEILING
```

`ROUND_CEILING` is limited to the positive canonical FIRE target. That same canonical target is displayed and passed to Planning. Ordinary FIRE money uses `ROUND_HALF_EVEN`; progress is an unclamped Decimal ratio quantized to eight decimal places with `ROUND_HALF_EVEN`.

**Real-basis decision:** FIRE v1 target and output are always `REAL`. A supplied real effective annual return composes as `REAL → REAL` without inflation. A supplied nominal effective annual return composes as `NOMINAL → REAL` and requires explicit inflation; Planning applies Fisher exactly once. `NOMINAL → NOMINAL` and `REAL → NOMINAL` are not FIRE v1 modes. Return and inflation are never inferred and accept the existing Planning finite Decimal domain greater than `-1`.

**Wealth decision:** Each analysis accepts exactly one of `INVESTMENT_PORTFOLIO_SNAPSHOT` or `USER_PROVIDED_SCENARIO`. Portfolio input is the source-only Planning selector and delegates exclusively to the ADR-023 resolver. Manual input reuses its explicit Planning amount and `observed_at` shape. `GOAL_CURRENT_AMOUNT` is excluded. The resolved concept is `eligible_investment_wealth`, not net worth; sources are never summed or used as fallbacks, and no emergency reserve is automatically added or subtracted.

**API and mode decision:** The MVP has one authenticated transient endpoint, `POST /api/v1/fire/analysis`, and exactly three explicit analysis types: `SUMMARY`, `PROJECTED_DATE`, and `REQUIRED_CONTRIBUTION`. Every mode returns summary facts. `PROJECTED_DATE` requires explicit scenario contribution, return type/rate, conditional inflation, and a 1–1,200 month horizon, then delegates to `TargetAchievementSolver`. `REQUIRED_CONTRIBUTION` requires return type/rate, conditional inflation, and `desired_fire_date`, then delegates to `RequiredContributionSolver`; client contribution and horizon are forbidden. Mode-incompatible fields are rejected, not ignored. Planning solver statuses are preserved rather than renamed as FIRE statuses.

**Summary decision:** FIRE summary contains spending, annualized spending, assumed rate, canonical target, eligible wealth, nonnegative gap, unclamped progress, conditional annual/monthly withdrawal capacity, as-of date, and wealth provenance. Summary status is exactly `ALREADY_FINANCIALLY_INDEPENDENT` or `BELOW_FIRE_TARGET`. Supported monthly withdrawal is derived from the unrounded annual product divided by 12, then rounded to cents with `ROUND_HALF_EVEN`.

**Source and inference decision:** Health supplies no automatic expense, savings, contribution, or prefill in the MVP. Dividend history/yield is excluded to prevent total-return plus dividend double counting. External income offsets, taxes, macro-derived assumptions, Goal integration/writes, persistence, age/birthdate, emergency-reserve exclusions, FIRE variants, Monte Carlo, longevity, probability of success, and Portfolio Intelligence are deferred. The endpoint is deterministic, read-only, Decimal-first, and non-advisory.

**Consequences:** Phase 10.4-B is `CONTRACT LOCKED / READY FOR USER REVIEW`; implementation remains not started. Phase 10.4-C may decompose implementation only after approval and must conform to `FIRE_CONTRACT.md`. No endpoint, engine, migration, frontend, test, persistence, or production source is created by this ADR lock.

---

## ADR-026: Wealth OS Product Realignment Gate

**Status:** APPROVED

**Date:** 2026-10-02

**Decision:** Insert the 10.R0–10.R7 Wealth OS product realignment sequence before
continuing Phase 10.5-B. Preserve Goals, Financial Health, Planning, FIRE, and
the completed 10.5-A decisions; do not treat the gate as cancellation or
authorization to rewrite validated engines.

**Authority boundary:** `WEALTH_OS_REALIGNMENT_AUDIT.md` records R0 findings and
recommendations. Future Smart Context, external-provider, AI-tool, navigation,
theme, and product-recomposition contracts remain unapproved until their
explicit phases. `10.5-B = PAUSED / PENDING WEALTH OS REALIGNMENT`.

---

## ADR-027: Wealth OS Product Architecture & Documentation Ownership

**Status:** ACCEPTED

**Date locked:** 2026-10-02

**Context:** R0 found validated deterministic capabilities but fragmented
product composition, repeated form entry, overlapping vision/status/roadmap
documents, provider-specific external context, placeholder Profile/Settings
behavior, and no production AI runtime. The product needed one target
architecture and one owner per documentation concern before implementation
could continue.

**Product decision:** FINANALYTICS is a personal Wealth OS connecting financial
reality, Goals, Planning, portfolio, income, monitoring, external context,
tools, and AI interpretation. The conceptual product areas are Home, Plan,
Portfolio, Explore, Income, Monitor, Market, Copilot, Tools, Profile, Settings,
and Data & Governance. Exact routes remain unlocked. Existing routes continue
until a later migration contract.

**Composition decision:** Adopt an incremental composition refactor. Goals owns
objective lifecycle, Planning remains the deterministic engine/tool, FIRE
remains a specialized Planning consumer, and future Portfolio Intelligence owns
certified portfolio analysis. Goals 10.1, Health 10.2, Planning 10.3, FIRE 10.4,
and the 10.5-A decisions remain valid. No rewrite-first strategy is approved.

**Profile and Settings decision:** Reuse the existing Profile as the canonical
Declared User Context surface and the existing Settings as the canonical
configuration surface. Observed transactions do not become Profile data, and
provider credentials do not become browser preferences. No Profile V2,
Settings V2, standalone Preferences, or standalone AI Settings surface is
approved.

**Context decision:** Lock the conceptual classes `DECLARED`, `OBSERVED`,
`DERIVED`, `EXTERNAL_OBSERVATION`, `EXTERNAL_EXPECTATION`, `ASSUMPTION`, and
`USER_OVERRIDE`. There is no universal precedence. Each feature selects the
semantically correct class. Known eligible values should prefill or be offered
with visible source, meaning, scope, time/freshness, and explicit override
semantics. Empty forms are a fallback. Declared and observed income never
overwrite one another; recurring-income direction is deterministic candidates
plus human confirmation.

**External-context decision:** External providers flow through adapter,
normalization/semantic classification, cache or governed observation,
freshness/status, and reference context before feature/tool consumption.
External observations and expectations remain distinct and never silently
replace internal certified facts.

**AI decision:** A future provider-aware runtime may support OpenAI, Gemini, and
Ollama without a parity promise or hard-coded provider dependency. AI consumes
approved tools and minimum-necessary context; it does not calculate financial
truth, query arbitrary tables, write records autonomously, or receive secrets.
Credentials remain server-side. Investment recommendations require a separate
future contract.

**Design decision:** The target is System/Light/Dark through incremental
semantic-token migration. Quiet Financial OS principles continue with
search-first discovery where appropriate, smart prefill, contextual actions,
inline scenarios, side-by-side comparison, progressive disclosure,
accessibility, controlled density, visible provenance, and visible freshness.
R1 changes no routes, components, or theme behavior.

**Documentation decision:** One concern has one canonical owner. Accepted ADRs
and locked contracts prevail in their scope; then the concern owner;
`CURRENT_STATE.md`; `MASTER_PLAN.md`; `IMPLEMENTATION_ROADMAP.md`; audit/research
evidence; historical/superseded material. `ARCHITECTURE.md` owns cross-cutting
architecture and product IA. `DATA_AND_SOURCE_OF_TRUTH.md` owns data semantics.
`UI_UX_PLAN.md` owns frontend/UX principles. `AI_AND_LLM.md` owns AI direction
and runtime truth. `PRODUCT_REFERENCES.md` owns external product inspiration.
Root `AGENTS.md` operationalizes this order, while nested agent files add only
scope-specific rules.

**Roadmap decision:** The official path is R2 Smart Financial Context, R3
External Context, R4 AI Runtime Foundation, R5 Design/Navigation/Theme, R6
experience recomposition, R7 independent validation, then 10.5-B resume. R3
provider research and R5 token audits may overlap after inputs stabilize, but
the deterministic main queue remains sequential.

**Portfolio gate:** 10.5-A remains authoritative. 10.5-B remains
`PAUSED / PENDING WEALTH OS REALIGNMENT` and resumes only after R7 closure unless
an explicit later decision changes the gate.

**ADR packaging:** This single consolidated ADR is sufficient under the current
repository convention. Separate ADRs for each product-area bullet would
duplicate canonical owners and are not required.

---

## ADR-028: Smart Financial Context and Declared/Observed Income Boundary

**Status:** ACCEPTED

**Date locked:** 2026-10-03

**Authoritative specification:** `SMART_FINANCIAL_CONTEXT_CONTRACT.md`

**Context:** R1 established the seven Smart Context classes and assigned
Profile as the Declared User Context surface, but it did not define persistence,
recurrence evidence, human decisions, ownership, API semantics, or composition.
The current Profile has no backend model and keeps only four non-sensitive
extended fields in browser storage; gross income is transient. The governed
ledger has enough incoming history for deterministic recurrence evidence but no
transaction-level user ownership and substantial transfer ambiguity. Health,
Goals, Planning, and FIRE already own certified domain semantics that R2 must
reuse rather than recalculate.

**Declared-context decision:** R2 persists only nullable
`declared_monthly_gross_income`, a positive cent-scale BRL Decimal with explicit
`GROSS` and `MONTHLY` meaning, source, declaration/as-of time, and update time.
It is Profile-owned, editable, and never inferred or overwritten from the
ledger. CPF, phone, birthdate, employment start, and authoritative employer,
occupation, or tax-regime data are not added. Existing authenticated identity
remains in `users`; decorative display name does not become a second identity
authority.

**Observed-candidate decision:** A recurring-income candidate is computed from
eligible governed `CLASSIFIED` incoming transaction evidence with exact
`CREDIT` transaction type and valid
provider/account/description/currency/date/amount.
The versioned signature is provider, account scope, currency, normalized exact
description, and direction. Normalization is limited to Unicode NFKC,
case-folding, trim, and whitespace collapse; fuzzy matching and digit stripping
are prohibited. A candidate requires evidence in at least three distinct
calendar months inside the six most recent calendar months. Multiple events in
one month count once and months need not be consecutive. The current partial
month may contribute but must be identified.

**Evidence and decision semantics:** Amount similarity is not an eligibility
gate and there is no authoritative numeric confidence score. The response may
show occurrence/month counts, first/latest dates, typical median amount,
minimum, maximum, median absolute deviation, freshness, and deterministic risk
flags. Candidate state is `DETECTED_CANDIDATE`, `CONFIRMED_AS_INCOME`, or
`REJECTED`; `STALE` is freshness, not a fourth classification. Confirm, reject,
and reset are explicit authenticated user actions. A decision never edits the
transactions, Profile, or Health aggregates, and confirmed sources are not
silently aggregated into a single income amount.

**Persistence and ownership decision:** Candidate evidence is computed on
read. R2 may add one user-owned declared-context record and one user-owned,
signature-versioned recurring-income decision record. Because current ledger
rows have no `user_id`, access must fail closed unless the authenticated user
matches the exact-single-user local invariant; a general multi-user ownership
migration requires a separate contract. APIs expose opaque candidate IDs and
minimum necessary evidence.

**Composition decision:** Smart Context is an internal feature-specific service,
not a global context dump, arbitrary query layer, financial engine, or AI
memory. Each consumer receives an explicit allowlist of typed values with
source, meaning, scope, time/freshness, and override semantics. Health retains
aggregate observed cashflow authority. Goals retains objective lifecycle.
Planning retains ADR-023 source resolution and all projection mathematics. FIRE
retains explicit spending, withdrawal, return, inflation, contribution, and
date assumptions; R2 does not silently prefill them. R3 external context, R4
AI, R5 design/navigation, R6 recomposition, and 10.5-B remain out of scope.

**API and precision decision:** The approved conceptual surface is authenticated
Profile context GET/PATCH, income-candidate GET, and candidate confirm/reject/
decision-delete actions. There is no generic context endpoint. Financial values
remain Decimal in authority and serialize as strings; dates are ISO values;
floats are not accepted as financial truth.

**Implementation decision:** `SMART_FINANCIAL_CONTEXT_IMPLEMENTATION_PLAN.md`
decomposes R2 into B1 persistence/ownership, B2 Profile context API, B3
recurrence evidence, B4 decisions/API, B5 feature-specific composition, B6
Profile experience, B7 consumer foundations, and B8 stabilization/independent
validation. The next authorized implementation gate is B1 only. This ADR and
its contract create no production code, schema, endpoint, UI, or test behavior.

---

## ADR-029: External Context Observation, Temporal, and Provider Boundary

**Status:** ACCEPTED / LOCKED

**Date proposed:** 2026-10-08

**Remediated:** 2026-10-09

**Date accepted:** 2026-10-09

**Approval:** Explicit user approval — “Sim, aprovo. Vamos prosseguir.”

**Independent review:** APPROVED; 0 BLOCKING, 0 MATERIAL, 0 MINOR.

**Authoritative contract:** `EXTERNAL_CONTEXT_CONTRACT.md`

**Locked series catalog:** `EXTERNAL_SERIES_REGISTRY.md`

**Context:** R3-A found an existing yfinance market-data boundary but no
normalized official macro provider, durable observation store, bitemporal
knowledge model, or purpose-limited external reference service. R2 already
reserves `EXTERNAL_OBSERVATION` and `EXTERNAL_EXPECTATION`, while ADR-006,
ADR-023, and ADR-028 prohibit a second market-data system, replacement of
aggregate portfolio authority, or silent context defaults.

**Decision:** R3 uses an allowlisted provider/series registry and a
provider-neutral immutable observation model with exact Decimal values,
economic reference periods, local knowledge time, provenance, availability,
and freshness. Provider adapters normalize into that model; consumers use an
internal purpose-limited reference service and never call providers directly.

**Persistence decision:** Store immutable observation versions and
separate operational series sync state in new Alembic-owned SQLite structures.
The store preserves revisions, deduplication, late-ingestion knowledge time,
historical `as_of`, and last-known-good. It does not store user financial data,
raw provider payloads, credentials, or values in `REAL`/float columns.

The locked SQLite value representation is canonical fixed-scale `TEXT`, with
the scale owned by the series registry and explicit conversion to and from
Python `Decimal`. SQLite `NUMERIC` affinity and SQLAlchemy `Numeric` do not, by
themselves, prove an exact fixed-precision roundtrip through the real SQLite
driver. SQL lexical ordering is not numeric ordering, so database-side value
ordering, ranges, casts, aggregates, and arithmetic are prohibited in this
contract. Stored value, provider unit, provider precision, normalization scale,
and internal Decimal precision remain separate concepts.

**Revision decision:** Economic identity, semantic content identity,
and local knowledge-event identity are distinct. A consecutive identical
retransmission creates no new event; a content transition does. `A -> B -> A`
therefore produces three immutable knowledge events even though the first and
third share a content fingerprint. Historical resolution selects the latest
committed event eligible at explicit `consumer_as_of`.

**Status decision:** Operational refresh age, economic freshness, and
acquisition health are evaluated independently. A failed refresh does not make
an otherwise valid last-known-good economically `STALE`; insufficient evidence
is `UNKNOWN`, with a structured acquisition-failure reason. Six-hour daily and
twenty-four-hour monthly intervals are locked call-suppression policies,
not publication calendars or proof of economic recency.

**MVP decision:** Start with the five documented BCB/SGS observation
series 432, 11, 12, 433, and 1. SGS 1 is reference-only, uses the locked
real-era ingestion floor, and cannot value a portfolio. Focus remains
contract-ready but implementation-deferred and, when activated, remains
`EXTERNAL_EXPECTATION` rather than observation.

**Authority decision:** External references never become effective Planning,
FIRE, Goals, Health, Portfolio, or Smart Context inputs automatically. ADR-023
and ADR-028 remain unchanged. Product integration and smart prefill stay in R6.

**Existing market-data decision:** ADR-006 remains controlling. R3 may later
remediate the current yfinance boundary only through a focused, independently
reviewed task. The hard-coded FX fallback `5.0` is priority debt but this ADR
does not authorize changing it.

**Accepted material decisions:**

1. Lock the five-series BCB/SGS registry: 432, 11, 12, 433, and reference-only
   SGS 1, with its 1994-07-01 MVP floor and no PTAX/valuation authority.
2. Keep Focus `CONTRACT_READY / IMPLEMENTATION_DEFERRED / NOT IMPLEMENTED` and
   semantically `EXTERNAL_EXPECTATION`.
3. Use the conceptual `external_observation_versions` and
   `external_series_sync_state` bitemporal persistence structures; R3-D owns
   their migration.
4. Use Python `Decimal` plus canonical fixed-scale SQLite `TEXT`, registry
   scales, preserved provider lexical text, no silent rounding/float, and no
   uncertified SQL numeric authority.
5. Separate economic identity, content identity, and knowledge-event identity;
   preserve `A -> B -> A` while deduplicating consecutive `A -> A`.
6. Keep availability, economic freshness, and acquisition health orthogonal;
   network failure does not automatically mean economic `STALE`.
7. Use six-hour daily and twenty-four-hour monthly refresh intervals only as
   call-suppression policy.
8. Execute the BCB-only implementation in order R3-C, R3-D, R3-E, R3-F, R3-I.
9. Keep R3-G separately gated and required only before yfinance admission;
   keep R3-H deferred and never report it as implemented.
10. Accept ADR-029 as the canonical architectural authority for these choices.

### ADR-029 — Amendment R3-B.2: Content Fingerprint V1

**ADR status:** `ACCEPTED / LOCKED` (unchanged)

**Amendment status:** `APPROVED / INDEPENDENTLY VERIFIED / LOCKED`

**Date approved:** 2026-10-09

**Approval:** Explicit user approval in the controlled R3-B.2 amendment task.

**Independent delta review:** APPROVED on 2026-10-10; 0 BLOCKING, 0 MATERIAL,
0 MINOR, and 2 INFORMATIONAL. It reproduced the three normative hashes,
validated the V1 binary prefix and eleven-field payload, confirmed ADR-029 and
financial-authority boundaries, and found no code-file change.

**Problem:** At the start of R3-C, the locked contract's content-identity rule
was found to be architecturally sound but incomplete as an executable formula:
it did not close the version, exact payload, canonical serialization, domain
prefix, output representation, or normative test vectors.

**Limited amendment decision:** Keep all ten accepted R3-B decisions unchanged
and normatively define `content_fingerprint_version = 1` in
`EXTERNAL_CONTEXT_CONTRACT.md`. V1 hashes exactly eleven registry-validated and
normalized semantic fields using deterministic compact, sorted-key UTF-8 JSON,
the version-specific NUL-terminated domain prefix, and SHA-256. Version and
fingerprint are compared as a pair. Invalid inputs are rejected before hashing
and do not acquire a valid domain fingerprint.

**Revision protection:** Content identity remains separate from economic and
knowledge-event identity. `A -> B -> A` still creates three knowledge events;
the first and third may share the V1 fingerprint. Deduplication is only against
the current head of the same economic identity, and no global unique
fingerprint constraint is authorized.

**Consequences:** R3-C owns the typed V1 payload, executable registry
validation, Decimal/civil-period normalization, canonical serialization,
prefix, SHA-256 calculation, version, three normative vectors, complementary
valid cases, and structured invalid-input tests. R3-D continues to own separate
version/fingerprint persistence, head deduplication, concurrency, knowledge
sequence, `known_from`, predecessor linkage, and historical replay. No
production code, schema, provider, database, API, frontend, or engine behavior
is created by this amendment.

**Gate:** R3-B is `CONTRACT APPROVED / LOCKED / VERSIONED`. R3-B.2 is
`APPROVED / INDEPENDENTLY VERIFIED / LOCKED`; R3-C is `READY / NOT STARTED`
and still requires its own implementation task.

**Consequences and exclusions:** R3-C is `READY / NOT STARTED`; R3-D/E/F/I are
planned and not started. This acceptance and its amendment create no code, schema, provider,
dependency, public API, frontend, scheduler, or engine change. ADR-006,
ADR-023, ADR-027, and ADR-028 remain unchanged. External references cannot
replace `portfolio_snapshots.patrimonio`, user assumptions, Goal state, Health
facts, Planning/FIRE inputs, or R2 feature allowlists. R3-G and R3-H require
their explicit future gates.

### ADR-029 — Amendment R3-D.1: Registry Version & UTC Knowledge-Time V1

**ADR status:** `ACCEPTED / LOCKED` (unchanged)

**Amendment status:** `CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED / VERSIONED`

**Date approved:** 2026-10-10

**Approval:** The user explicitly approved all material D-1 and D-2 decisions
in the controlled R3-D.1 task.

**Independent review:** `PHASE 10.R3-D.1 — INDEPENDENT CONTRACT DELTA REVIEW
APPROVED`. Gemini 3.8 Flash High reviewed eight documentation files and the
657-insertion/48-removal delta: 0 blocking, 0 material, 0 minor, and 2
informational findings. It confirmed Registry Version V1, UTC Persistence V1,
the documented physical-commit limitation, preservation of ADR-029/R3-B.2/
Content Fingerprint V1, and all five SGS series. No runtime test was executed
by this documentary review.

**Origin and gaps:** The R3-D preflight found two material contract gaps before
persistence implementation could begin: the registry had no explicit normative
version/evolution contract, and the UTC/knowledge-time wording did not close
the canonical SQLite representation, assignment order, clock coherence, or the
distinction between logical knowledge time and physical commit completion.

**D-1 — Registry version decision:** The normative registry version is the
positive strict integer `EXTERNAL_SERIES_REGISTRY_VERSION = 1`; Python `bool`
is rejected and V1 is immutable after publication. It versions the catalog and
its governed rules independently of the fingerprint version, Alembic revision,
application version, and deployment. An approved normative change increments
it when series membership, provider/identifier, economic concept, semantic
class, frequency, unit, currency, scope, precision/scale, normalized historical
limit, provenance, eligibility, permitted use, registry-owned operational
policy, or accepted validation behavior changes. Spelling, formatting,
non-normative comments, behavior-preserving refactors, tests, equivalent
optimization, Alembic/application changes, and an isolated fingerprint-formula
change do not increment it.

R3-D will persist `registry_contract_version INTEGER NOT NULL` in both
`external_observation_versions` and `external_series_sync_state`, with strict
positive-integer validation and server ownership. An event keeps the version
under which it was validated and accepted. Sync state keeps the version under
which its operational evidence was produced or explicitly reconciled; startup
alone cannot rewrite it. Certified acquisition under the current version or a
future governed deterministic reconciliation is required to update it.

Registry version is excluded from the eleven-field Content Fingerprint V1
payload, prefix, JSON bytes, SHA-256 input, digest, and locked economic
identity. Head-only deduplication, identical retransmission behavior, and
`A -> B -> A` remain unchanged. Append-only events, original fingerprints and
versions, registry version, economic identity, `knowledge_sequence`,
`known_from`, and supersession are preserved. Registry V2 requires a separate
contract for V1 definition retention, reconstruction, read compatibility,
typed rejection, reconciliation, and eligibility/semantic tests.

A sync-state version mismatch yields `acquisition_health = UNKNOWN`,
`economic_freshness = UNKNOWN`, and
`reason_code = REGISTRY_VERSION_MISMATCH` until certified acquisition or
governed reconciliation. Mismatch alone does not delete observations or
last-known-good, change fingerprints/history, create an event or zero, imply
`STALE`/`UNAVAILABLE`, trigger refresh, or collapse independent availability.
Series removal or eligibility change uses its specific policy while preserving
history. Registry-dependent cache identities include provider, registry key,
interval, request semantics, and the server-resolved registry version; the
observation store never becomes a disposable cache.

**D-2 — UTC and logical knowledge-time decision:** Every persisted R3-D UTC
timestamp uses SQLite `TEXT` in exact 27-character ASCII form
`YYYY-MM-DDTHH:MM:SS.ffffffZ`, with fixed separators, zero padding, six
microsecond digits, and literal `Z`. Variable offsets, local representation,
Unix timestamp authority, floats, omitted precision, and silent rounding are
forbidden. Economic dates remain ISO civil dates.

The governed codec accepts only UTC-aware zero-offset Python `datetime`
objects, writes canonical text, and on read validates shape, real calendar
values, microseconds, UTC, and a byte-identical reserialization before
returning `timezone.utc`. Naive/non-zero-offset datetimes, unvalidated strings,
incompatible types, and non-canonical persisted data fail with typed errors;
`DateTime(timezone=True)` is not sufficient proof on SQLite. Lexicographic
ordering is chronological only for codec-certified timestamps and never grants
SQL numeric authority over financial text.

`retrieved_at` is assigned by the R3-E adapter after complete provider-response
receipt and remains acquisition provenance. R3-D's application service, after
obtaining the SQLite write reservation, captures one injected
`transaction_time_utc` per attempt as late as practical and assigns
`ingested_at = known_from = transaction_time_utc`. The equal value represents
two concepts: logical governed ingestion and logical replay eligibility. It is
not backdated to economic time, derived from publication time, generated by a
hidden default, or claimed to equal physical commit or first visibility.

The normative order is certified R3-C validation, Content Fingerprint V1,
write unit of work, `BEGIN IMMEDIATE`, current-head read, one time capture,
clock validation, deduplication or per-identity sequence allocation, optional
event insert, sync-state update, and one commit. Repositories neither create
clock values nor commit. Coherence requires transaction time not earlier than
`retrieved_at` or the current head's `known_from`; failure is typed and never
clamped or silently repaired. Equal timestamps use `knowledge_sequence`. Retry
rereads the head and obtains a new explicit timestamp.

SQLite atomicity and isolation do not provide an application-visible physical
commit instant that can be stored atomically inside the event before commit.
An event assigned `known_from` before commit is invisible until commit, yet a
later retrospective logical cut between those instants can select it. V1
therefore guarantees logical knowledge-time replay, not exact physical
commit-time reconstruction or zero physical retroactivity inside the
transaction window. It does not promise first visibility equal to
`known_from`, global causal order, absolute host-clock accuracy, or physically
perfect microsecond replay.

R3-D must use `BEGIN IMMEDIATE` before head read, one transactional unit of
work, commit-free repositories, atomic event/sync-state updates, bounded
timeout/retry, and head reread after retry. `knowledge_sequence` begins at 1
per economic identity, increments only for a committed transition, does not
advance for retransmission or rollback, and is not global. Bitemporal reads
retain both explicit cuts and order eligible versions by
`known_from DESC, knowledge_sequence DESC` within the identity.

**Compatibility gate:** The declared authority remains
`SQLAlchemy==2.0.21`; the preflight observed local `2.0.51`. R3-D must use APIs
present in 2.0.21, prove actual `BEGIN IMMEDIATE` behavior with independent
connections, and verify both compatible environments without silently changing
the dependency pin.

**Informational implementation findings:** `INF-R3D1-01` requires R3-D tests
on disposable SQLite to prove physical `BEGIN IMMEDIATE` before head read with
two independent connections, writer serialization, atomicity, rollback,
bounded retry, and no `knowledge_sequence` race; `Session.begin()` is not
equivalent proof. `INF-R3D1-02` requires first sync-state initialization to
set `registry_contract_version = EXTERNAL_SERIES_REGISTRY_VERSION` without
implying acquisition success or fabricating last-success, last-attempt,
last-valid-observation, coverage, healthy, or current evidence.

**Preservation and impact:** Content Fingerprint V1, its eleven fields, binary
prefix, normative vectors, identity, and R3-B.2 amendment remain unchanged.
All ten original ADR-029 decisions remain accepted. Financial authority is not
transferred. R3-D gains the future executable constant, dual persistence,
codec, logical-time, serialized unit-of-work, mismatch, replay, concurrency,
and normative-test responsibilities; R3-E owns `retrieved_at`; R3-F consumes
logical `known_from` and exposes conservative mismatch state.

**Gate and exclusions:** This amendment adds documentation only. It creates no
code, executable test, migration, table, database access, dependency change,
provider, API, frontend, scheduler, or engine behavior. The independent
contract-delta review passed; R3-D is `READY / NOT STARTED` and still requires
its separately authorized implementation task.

### ADR-029 — Amendment R3-E.0: Historical Revision Windows & Acquisition Finalization V1

**ADR status:** `ACCEPTED / LOCKED` (unchanged)

**Amendment status:** `CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED / CHECKPOINT AUTHORIZED`

**Date approved:** 2026-10-11

**Approval:** The user explicitly approved all R3-E.0 material decisions in
the controlled documentation-only amendment task and explicitly approved the
minimal Deferred Ingestion & Acquisition Finalization V1 compatibility
adaptation on 2026-10-12.

**Targeted independent remediation review:** Gemini 3.8 Flash High approved
the remediated amendment with 0 blocking, 0 material, 0 minor, and 2
informational findings. `MAT-R3E0-01`, `MIN-R3E0-01`, `MIN-R3E0-02`, and
`INF-R3E0-01` are resolved; `INF-R3E0-01` remains a governed limitation.
`INF-R3E0-02` (scalar representation of discontinuous coverage) and
`INF-R3E0-03` (absence of a persistent acquisition journal) remain explicit
V1 risks. `INF-R3D-01` and `INF-R3D-02` remain preserved R3-D findings.

**Problem:** The R3-E preflight left two material boundaries open: how ordinary
acquisition revisits recent economic periods to discover provider revisions,
and how a multi-request or multichunk acquisition is finalized without turning
requested dates, successful outer chunks, or observed endpoints into false
continuous coverage or global success.

**Decision:**

1. Every eligible ordinary DAILY update uses one explicit stable civil date
   `D` and the inclusive 90-day window
   `max(registry_normalized_floor, D - 89 days)` through `D`. SGS 1 retains its
   `1994-07-01` floor. Missing weekends/holidays create no observations, and
   revisions outside the window are not presumed discovered.
2. Every eligible ordinary MONTHLY update uses the civil month of `D` and the
   23 preceding civil months: the maximum of the normalized floor and the first
   day of the month 23 calendar months before `D`, through explicit `D`.
   Calendar-month subtraction is mandatory; missing or not-yet-published months
   create no value, accumulation, or annualization.
3. The two revisit windows are independent from the existing 6h/24h operational
   refresh policy and from both economic and knowledge cuts in consumer `as_of`.
4. Historical deep reconciliation is manual, explicit, bounded by registry
   series plus start/end dates, chunked under BCB limits, R3-C-certified, and
   R3-D-persisted. It never runs at startup, from a scheduler, as a silent
   whole-history fallback, or as financial authority.
5. A never-acquired series may begin with the ordinary window. Missing history
   does not authorize automatic full backfill, and first-request success does
   not prove complete historical coverage.
6. R3-E may make the minimal controlled extension of the existing R3-D
   application service, without schema change, for responsibilities named
   `get_sync_state(...)` and `finalize_acquisition(...)`. Exact signatures
   follow existing backend types; no parallel store or interface is authorized.
7. Requested interval, proven queried interval, and observed economic coverage
   are separate. A valid empty response can prove a chunk was queried while
   producing no economic observation.
8. Current `coverage_start`/`coverage_end` cannot encode discontinuous evidence.
   They must not bridge a failed chunk or be reinterpreted as proof of an
   observation on every intermediate date. Prior certified coverage and LKG
   survive later failure without a fabricated extension.
9. Every chunk is fully validated before first persistence. Valid committed
   chunks survive other chunk failures, but the final operation is `PARTIAL`,
   continuity is not invented, and failure is neither zero nor economic
   unavailability.
10. R3-D atomicity remains per owned persistence transaction. No global
    all-chunk atomicity is promised. Ambiguous commits are not blindly retried.
11. A crash after some event commits but before finalization preserves those
    events without proving global acquisition success. No chunk success may be
    exposed as global `SUCCESS` before effective finalization.
12. If the existing service plus the approved minimal extension cannot
    guarantee conservative interim state with the current two tables, R3-E
    implementation stops for a material decision before adding any alternative
    method, interface, table, or schema mechanism.
13. No migration, scheduler, public endpoint, screen, deployment, active-DB
    access, or automatic execution is authorized. Timeout, exact retries,
    backoff, payload/row caps, call rate, worker count, and automatic policy
    remain undecided implementation values.

**Remediation addendum — Deferred Ingestion & Acquisition Finalization V1:**
The independent review identified `MAT-R3E0-01`, `MIN-R3E0-01`,
`MIN-R3E0-02`, and `INF-R3E0-01`. This addendum remediates only the still-
unversioned R3-E.0 amendment; it does not retroactively modify original
ADR-029, R3-B.2, R3-D.1, or the closed R3-D immediate contract.

14. The existing `ingest()` behavior remains the default `immediate` mode and
    keeps all 45 R3-D tests and legacy semantics. An explicit opt-in `deferred`
    mode is authorized only for governed R3-E acquisitions or future callers
    that deliberately adopt it.
15. Deferred ingestion still recertifies R3-C content, validates Registry
    Contract Version V1, recalculates Content Fingerprint V1, and performs the
    existing `BEGIN IMMEDIATE` event transaction. It may atomically update LKG
    and the existing observation/transition/retransmission counters, but it
    does not publish global `SUCCESS`, advance `last_success_at` or successful
    refresh eligibility, clear partial state, or expand coverage from observed
    extrema.
16. `finalize_acquisition(...)` is the exclusive publisher of global
    `SUCCESS`, `EMPTY`, `PARTIAL`, or `FAILED`. It receives typed evidence for
    requested/completed/uncompleted chunks and proved queried coverage, rejects
    unsupported or temporally stale success, preserves event counters without
    adding them again, and never inserts observations or edits historical
    knowledge time.
17. `get_sync_state(registry_key)` is strictly read-only and returns `None`
    when no row exists. It performs no HTTP, refresh, migration, initialization,
    `INSERT`, `UPDATE`, or artificial acquisition evidence.
18. Durable coverage is promoted only by a globally complete, gap-free,
    fully received and validated operation, including valid empty chunks. A
    `PARTIAL` or `FAILED` operation never enlarges it; without prior coverage
    the fields remain `None`. Disconnected intervals are never joined by
    extrema or selected arbitrarily.
19. Existing R3-D coverage may reflect economic observation extrema and is not
    retroactively treated as proof of complete queried continuity. No backfill,
    event deletion, third table, or automatic correction is authorized.
20. A crash after deferred event commits but before finalization preserves the
    events, counters, and LKG while recording no new global success, coverage,
    or successful refresh advancement. Without a persisted acquisition journal,
    V1 does not reconstruct in-flight attempts or claim cross-process exactly-
    once behavior.
21. Repeated finalization is counter-idempotent. Reprocessing preserves
    `A -> A`, `A -> B`, and `A -> B -> A` semantics; no persistent idempotency
    key, durable `STARTED` state, migration, or scheduler is introduced.

**Registry and history preservation:** These orchestration decisions do not
change the five-series catalog, identifiers, metadata, units, scales,
frequencies, permitted use, normalized floors, Registry Contract Version V1,
or Content Fingerprint V1. `EXTERNAL_SERIES_REGISTRY_VERSION` remains `1`.
Immutable history, original fingerprints, UTC V1, head-only retransmission
deduplication, `A -> B -> A`, last-known-good, and financial-authority
boundaries remain unchanged.

**Gate and exclusions:** The amendment is documentation only. R3-C is `CLOSED
/ LOCKED`; R3-D.1 is `APPROVED / LOCKED / VERSIONED`; R3-D is `CLOSED /
PUSHED`; R3-E.0 is `CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED /
CHECKPOINT AUTHORIZED`; R3-E is `READY / NOT STARTED`; and R3-F is `PLANNED /
NOT STARTED`. R3-E implementation remains separately gated. ADR-029 remains
`ACCEPTED / LOCKED` throughout.

### ADR-029 — Addendum R3-F.0: Purpose-Limited Point-in-Time Reference Context

**Status:** `APPROVED / DOCUMENTED`

**Date:** 2026-10-14

**Approval:** The user explicitly approved D1-D6 and the three refinements
below. This addendum constrains the future R3-F1 read boundary; it does not
modify the locked External Context contract, Registry V1, or prior ADR-029
decisions, and it activates no runtime consumer.

1. **D1 — closed purpose enum.** R3-F1 may expose only
   `MARKET_INTEREST_RATE_REFERENCE`, `MARKET_INFLATION_REFERENCE`, and
   `MARKET_FX_REFERENCE`.
2. **D2 — immutable allowlist.** Interest-rate reference is restricted to
   `BCB_SGS_SELIC_TARGET`, `BCB_SGS_SELIC_EFFECTIVE`, and `BCB_SGS_CDI`;
   inflation reference to `BCB_SGS_IPCA_MONTHLY`; and FX reference to
   `BCB_SGS_USD_SELL`. Only the future internal Market context composer is an
   approved consumer at this stage. Access outside the purpose/consumer/series
   matrix returns typed `PURPOSE_NOT_ALLOWED`.
3. **D3 — Registry V1 preservation.** The matrix is an additional service
   restriction. It changes no `SeriesUse`, unit, definition, eligibility,
   identifier, fingerprint, or locked Registry version.
4. **D4 — point lookup only.** Every request provides explicit
   `consumer_as_of_date` and UTC `consumer_as_of_timestamp`. R3-F1 does not
   authorize `history_window`; any unapproved history request is rejected and
   never silently ignored.
5. **D5 — replay/status separation.** `reference_replay` contains the value,
   original economic period, selected knowledge event, and provenance chosen
   deterministically by the two cuts. `operational_state_snapshot` is current
   operational state observed at read time and does not represent the past.
   Mutable sync state does not reconstruct historical health, coverage, or
   freshness. `state_observed_at` is populated only from reliable temporal
   evidence; otherwise its absence is explicit.
6. **D6 — conservative state policy.** Certified service policy alone derives
   `economic_freshness`: `CURRENT` requires sufficient positive evidence,
   `STALE` requires a previously approved objective criterion, and missing
   evidence yields `UNKNOWN`. HTTP success alone is insufficient. Missing data
   returns `reference=None`, a reason code, and appropriate availability;
   Decimal zero is valid data. Registry mismatch preserves eligible LKG and
   does not automatically mean `STALE` or `UNAVAILABLE`.

**Temporal invariants:** Deterministic selection requires
`reference_period_end <= consumer_as_of_date` and
`known_from <= consumer_as_of_timestamp`, with explicit UTC and no implicit
clock. `knowledge_sequence` remains the tie-breaker, including `A -> B -> A`.

**Approved refinements:** `reference_replay` is explicitly separate from the
non-historical `operational_state_snapshot`; economic freshness is derived only
from certified conservative policy and otherwise is `UNKNOWN`; and the last
eligible observation retains its original economic period. A Friday FX quote
does not become a Sunday quote, and the last published IPCA observation does
not become the current month. No interpolation, economic carry-forward,
annualization, projection, conversion, or automatic assumption is authorized.

**Next gate:** `R3-F1 — Point-in-time External Reference Read Boundary` is
`NOT IMPLEMENTED`. Its bounded scope is a read-only service over certified
Registry/Store boundaries, immutable request/result, closed purpose matrix,
explicit two-cut selection, Decimal, provenance, explicit absence, orthogonal
statuses, replay/current-state separation, and focused tests. Direct consumer
SQL/provider access, writes, refresh, scheduler, endpoint, frontend, migration,
financial-engine calculation, and canonical wealth-source changes remain
prohibited. R3-E4's published implementation checkpoint remains preserved.

**Historical R3-F1 implementation record (2026-10-15):** At its implementation
checkpoint, the approved point-in-time read boundary was `IMPLEMENTED / TESTED
/ AWAITING INDEPENDENT REVIEW`. The additive
implementation consists of the closed immutable purpose matrix, immutable
request/result and replay/operational envelopes, and the internal read-only
`ExternalReferenceContextService`. It delegates selection to the existing
`get_latest_series_as_of(...)` Store boundary and current operational evidence
to `get_sync_state(...)`; it adds no repository, persistence, provider call,
write, refresh, endpoint, frontend, migration, engine calculation, or runtime
consumer. The implementation reuses the certified R3-D state evaluator and
introduces no `STALE` criterion: complete positive coverage plus selected-head
evidence may establish `CURRENT`; otherwise freshness remains `UNKNOWN`.
Focused evidence was `28 passed`; the combined R3-F1 plus Registry/Store gate
was `100 passed`. At that point this record did not close R3-F1 or alter
ADR-029's locked history.

**R3-F1 approval and closure record (2026-10-15):** Independent review
completed with 0 blocking, 0 material, and 0 minor findings. The implementation
checkpoint is published at `30c4df058fd80923c37243252f4ee8fc6fa76dce`, and
R3-F1 is now `CLOSED / PUSHED`. This current status does not rewrite the
chronology above, amend ADR-029, activate a runtime consumer, or authorize
history windows or a new R3-F2.

**R3-I independent stabilization record (2026-10-15):** The fresh-context
transversal audit passed `234` tests, reported 0 blocking, 0 material, and 0
minor findings, required no code change, and preserved eight historical
informational findings. R3-I is `INDEPENDENTLY APPROVED / DOCUMENTATION
RECONCILED`, not `CLOSED / PUSHED`. R3-G remains separately gated and
R3-H remains deferred.

---

## ADR-030: Hybrid AI Runtime Foundation and Assisted Local Setup

**Status:** `ACCEPTED — R4.0 CONTRACT APPROVED / DOCUMENTATION IN PROGRESS`

**Date:** 2026-10-15

**Context:** There is no production AI runtime, functional Advisor, provider
abstraction, or tool registry. Historical Gemini files, SDK dependencies,
tables, settings, and UI text are scaffolding rather than capability. Ollama is
not installed. R4 needs one provider-neutral runtime that consumes deterministic
Engines and governed R2/R3 context without duplicating financial authority or
silently sending financial data to a remote provider.

**Decision:** The user approved D1-D12 of the R4.0 Hybrid AI Runtime proposal:

1. Local Llama candidates are admitted only after a read-only hardware gate and
   are pinned by exact digest; no candidate is the definitive model now.
2. Hardware and environment inspection is mandatory before installation or
   model download.
3. Real financial data is ineligible for free Gemini. Future remote processing
   requires a verified paid project, explicit opt-in, data minimization, and a
   compatible provider policy.
4. Gemini uses one adapter based on the then-current official `google-genai`
   SDK; historical scaffolding is reconciled rather than duplicated.
5. One retry controller owns application and SDK attempts. The initial
   configurable baseline is no more than three total attempts inside one
   deadline and token/cost budget.
6. `LOCAL_ONLY` is default; `HYBRID` is opt-in; fallback and offline-to-cloud
   promotion are never silent.
7. Circuit-breaker parameters begin as experimental values and require
   evidence-based calibration.
8. Benchmarking follows a reproducible protocol but no run, download, provider
   call, schedule, quota use, or expense is authorized.
9. Telemetry uses a minimized envelope. Persistence, `ai_runs` reuse, schema,
   retention, and migration require a separate gate.
10. Initial personalization is limited to authorized preferences and retrieval
    of certified information. There is no silent memory, training, or weight
    update.
11. R4 supplies one infrastructure and reconciles historical scaffolding; it
    does not presume or create a parallel Advisor.
12. The first increment is exercised through an internal application service
    and mocks, without endpoint, frontend, or scheduler.

**Mandatory refinements:** Adapter integration authorization is distinct from
authorization to send real financial data. `LOCAL_ONLY` remains binding when no
local model exists and then returns typed unavailability. Benchmark quality and
availability are separate dimensions and cannot elect a model or time window
before measurements. The telemetry contract precedes persistence and real
execution; no database or migration is implied.

**Runtime boundary:** AI interprets or orchestrates approved capabilities. It
does not calculate wealth, returns, dividends, or other Engine-owned truth;
query arbitrary SQL; execute financial operations; or write records. Tools are
authenticated, server-side, user-scoped, typed, call-bounded, audited, and
read-only. Minimum certified context, provenance, prompt-injection isolation,
structured-output validation, server-side secrets, and explicit errors are
mandatory. ADR-023 and locked R2/R3 contracts remain authoritative.

**Provider and routing boundary:** The provider/model registries record exact
capabilities, health, revision/digest, limits, and measured evidence. The router
applies privacy, consent, task capability, token, cost, and availability gates
before comparing quality, latency, and cost evidence. `LOCAL_ONLY`,
`REMOTE_ONLY`, and opt-in `HYBRID` are explicit modes. Gemini-to-Ollama fallback
is allowed only when authorized and contract-compatible; offline/local policy
can never fall through to cloud. No suitable provider produces a typed error or
explicit degraded result.

**Ollama assisted plan:** R4-D.0 is a read-only OS/CPU/RAM/GPU/VRAM/driver/disk
preflight with no installation. R4-D.1 is separately authorized guided
installation from current official instructions, including service, PATH,
version, loopback, exposure, and cloud-disabled verification. R4-D.2 separately
authorizes a hardware-supported model download, digest/license/quantization
validation, structured JSON, and offline inference. R4-D.3 measures cold/warm
start, latency, tokens/s, resources, effective context, controlled concurrency,
and local-adapter behavior. Exact commands, expected evidence, side effects,
and success/stop criteria are presented to the user at each gate. D.0-D.3 are
an internal R4-D checklist unless a later roadmap decision promotes them.

**Telemetry and benchmark boundary:** The logical audit envelope includes
request ID, opaque user scope, provider/model/version or digest, routing and
tool decisions, latency, tokens, cost when known, retries, error, fallback,
outcome, UTC time, and certified-source references. It excludes raw prompts,
full financial context, personal data, credentials, and API keys. The separate
benchmark uses identical synthetic/verifiable tasks, exact configurations,
alternated order, and distributed `America/Bahia` windows; it reports quality
and availability separately, including success, `429`/`503`, latency, tokens,
cost, factual/financial quality, source adherence, invalid output, fallback,
local resources, throughput, and sample confidence where applicable.

**Increment and authorization consequence:** R4-A Provider-Neutral Contracts,
R4-B Authorization/Tools/Minimal Context, R4-C Audit/Telemetry, R4-D Ollama,
R4-E Gemini, R4-F Hybrid Router, R4-G Benchmark Harness, and R4-H
Personalization/Memory are `PLANNED`, not authorized implementations. R4-A is
the first candidate and remains `NOT IMPLEMENTED`. Proposed model choices,
retention periods, budgets, and recovery thresholds are not approved
operational configuration.

**Preservation and exclusions:** ADR-030 does not rewrite ADR-002, ADR-007,
ADR-023, ADR-027, ADR-028, ADR-029, or any locked R2/R3 contract. R3-I remains
`INDEPENDENTLY APPROVED / DOCUMENTATION RECONCILED`. This formalization changes
documentation only and authorizes no code, dependency, installation, model
download, API-key test, Gemini call, benchmark, database access, migration,
endpoint, frontend, scheduler, commit, or push.
