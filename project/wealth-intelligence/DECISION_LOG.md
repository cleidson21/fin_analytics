# Architecture Decision Records — Lote 10.0
**Document:** Decision Log
**Updated:** 2026-09-29

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
| ADR-019 | Planning Input and Source Boundary | APPROVED | 10.3.0-A |
| ADR-020 | Planning Mathematical Contract | APPROVED | 10.3.0-A |
| ADR-021 | Planning Scenario Semantics and Lifecycle | APPROVED | 10.3.0-A |
| ADR-022 | Retirement/FIRE and Portfolio Intelligence Boundary | APPROVED | 10.3.0-A |
| ADR-023 | Investment Portfolio Initial Wealth Source | APPROVED | 10.3.10A |
| ADR-024 | Post-10.3 Planning UX and Simplicity Contract | APPROVED | POST-10.3-UX-A |
| ADR-025 | FIRE Deterministic Contract and Planning Composition | ACCEPTED | 10.4-B |

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
