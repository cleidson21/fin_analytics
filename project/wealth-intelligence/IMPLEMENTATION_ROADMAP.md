# Implementation Roadmap — Wealth OS
**Status:** `ACTIVE QUEUE — 10.R2-B6 READY / NOT STARTED`
**Date:** 2026-10-05

---

## Active queue

| Order | Phase | Outcome | Status | Hard dependency |
|---:|---|---|---|---|
| 1 | 10.R2 | Smart Financial Context: Profile persistence, declared context, observed recurring-income candidates, human decisions, feature-specific composition, provenance | `IMPLEMENTATION IN PROGRESS / B1-B5 VALIDATED / B6 READY` | R1 locked; ADR-028 and R2 contract |
| 2 | 10.R3 | External Context Layer: adapters, normalization, cache/observation, semantic class, freshness/status, macro/reference provider foundations | `NOT STARTED` | R2 taxonomy and context boundary |
| 3 | 10.R4 | AI Runtime Foundation: provider abstraction, approved read-only tools, privacy, auditability, errors/timeouts/cost telemetry, minimal surface | `NOT STARTED` | R2 + R3 context semantics and deterministic tools |
| 4 | 10.R5 | Design, navigation, and theme: semantic tokens, System/Light/Dark, shell/IA, responsive analytical and interactive patterns | `NOT STARTED` | R1 IA; R2/R3 context presentation requirements |
| 5 | 10.R6 | Experience recomposition: Wealth Home, Goals, Planning, FIRE, and appropriate Profile/Settings integration | `NOT STARTED` | R2–R5 foundations |
| 6 | 10.R7 | Fresh-context independent product, architecture, contract, privacy, UX, and regression validation | `NOT STARTED` | R1–R6 complete |
| 7 | 10.5-B | Resume Portfolio Intelligence contract lock using the realigned architecture | `PAUSED / PENDING WEALTH OS REALIGNMENT` | R7 closure; preserve 10.5-A |

R2 must not become an AI feature. R3 must not silently implement the final
Explore product. R4 is infrastructure, not the complete Copilot. R5 cannot
rewrite financial engines. R6 composes validated capabilities and may change
their interaction/presentation only within explicit contracts. R7 decides
realignment closure.

The main implementation path remains sequential. R3 provider research and R5
token/visual audits may run in parallel after their inputs are stable, but no
parallel activity changes the official dependency gates.

R2 implementation is decomposed in
`SMART_FINANCIAL_CONTEXT_IMPLEMENTATION_PLAN.md` as B1 declared-context
persistence/ownership, B2 declared Profile API, B3 recurrence evidence engine,
B4 decision state/API, B5 feature-specific composition, B6 Profile experience,
B7 consumer foundations, and B8 stabilization/independent validation. B1 through
B5 are `IMPLEMENTED / VALIDATED`; the active next task is exactly `10.R2-B6 —
PROFILE CONTEXT EXPERIENCE & BROWSER TRANSITION`. No later microprocess is
implicitly authorized.

## Closed and preserved baseline

| Phase | Status |
|---|---|
| 10.1 Goals | `IMPLEMENTED / VALIDATED` |
| 10.2 Financial Health | `IMPLEMENTED / VALIDATED` |
| 10.3 Planning | `VALIDATED / CLOSED` |
| POST-10.3 UX | `VALIDATED / CLOSED` |
| 10.4 FIRE | `VALIDATED / CLOSED` |
| 10.5-A Portfolio audit | `AUDIT COMPLETE / USER DECISIONS RESOLVED` |
| 10.R0 | `AUDIT COMPLETE` |
| 10.R1 | `ARCHITECTURE / DOCUMENTATION LOCKED` |

The former 10.6–10.12 sequence is `SUPERSEDED / HISTORICAL` as an active queue.
Its useful intentions are represented by R2–R7 or remain post-10.5 candidates;
it does not independently authorize implementation.

## Historical roadmap overview (non-authorizing)

| Phase | Name | Status | Depends On | Est. Scope |
|-------|------|--------|-----------|------------|
| 10.0 | Architecture & Product Design | **COMPLETE** | — | Documentation only |
| 10.1 | Goal Domain Foundation | IMPLEMENTED / VALIDATED | 10.0 | DB migration, Goal model enrichment, CRUD, basic UI |
| 10.2 | Financial Health Intelligence | **COMPLETED / MERGED — 10.2.10-C VALIDATED** | 10.1 | Expense analytics, savings rate, spending trends |
| 10.3 | Planning & Projection | **VALIDATED / CLOSED.** 10.3.7-A remains deferred; 10.3.8 automated validation passed with Swagger smoke deferred; 10.3.10A contract locked; 10.3.10B complete; 10.3.11–10.3.12 validated. | 10.1, 10.2 | Generic deterministic projections, target solvers, Goals integration, explicit scenarios |
| 10.4 | Retirement & Financial Independence (FIRE) | **VALIDATED / CLOSED** — A/B/C complete; D1–D5 implemented/validated; D6 validated/stabilized; D7 validated/closed | 10.3 | Deterministic real-basis FIRE semantics over reusable 10.3 engines |
| 10.R0 | Wealth OS Product Realignment Audit | **AUDIT COMPLETE** | 10.4, 10.5-A | Cross-product evidence, target IA, ownership and dependency order |
| 10.R1–R7 | Wealth OS Realignment | R1 ARCHITECTURE / DOCUMENTATION LOCKED; R2 IMPLEMENTATION IN PROGRESS, B1–B5 VALIDATED / B6 READY; R3–R7 NOT STARTED | 10.R0 | Architecture/docs, Smart Context, external context, AI runtime, design/navigation, product recomposition, independent validation |
| 10.5 | Portfolio Intelligence | **10.5-A COMPLETE; 10.5-B PAUSED / PENDING WEALTH OS REALIGNMENT** | existing Investments, 10.4, 10.R7 before resumption | Certified composition and concentration facts; exact MVP pending contract lock |
| 10.6 | Rebalancing & Watchlist | NOT_STARTED | 10.5 | Target allocation, watchlist |
| 10.7 | External Market Intelligence | NOT_STARTED | 10.5, BCB/News research | BCB, news, fundamentals |
| 10.8 | LLM Provider Foundation | NOT_STARTED | 10.7 | LLMProvider abstraction, Ollama + Gemini |
| 10.9 | Wealth AI Briefing | NOT_STARTED | 10.8, 10.4, 10.5 | Context builder, structured insights, briefing UI |
| 10.10 | Advanced Orchestration | NOT_STARTED | 10.9 — **CONDITIONAL** | Only if single-LLM approach proves insufficient |
| 10.11 | Docker & Operations | NOT_STARTED | All backend phases | Containerization, compose, ops guide |
| 10.12 | Global UX / Visual Polish | NOT_STARTED | All UI phases | Design system, typography, final visual pass |

The legacy 10.6–10.12 sequence remains historical planning input. R1 reconciled
its duplicated external-data, AI, and UX responsibilities into R2–R7; the
legacy sequence no longer authorizes implementation independently.

---

## Historical execution records (non-authorizing)

The remainder of this file preserves completed phase contracts and former
10.6–10.12 proposals as historical evidence. Old `next` or `not started` labels
are point-in-time records and do not override the Active queue above.

### Post-10.3 Planning UX implementation

This sequence is contract-preserving refinement, not a reopening of Phase 10.3
and not the start of FIRE. ADR-024 and `PLANNING_UX_CONTRACT.md` are authoritative.

| Microtask | Scope | Status |
|---|---|---|
| UX-B1 | pt-BR exact financial input/output adapters, field errors, executable parser/formatter tests | VALIDATED |
| UX-B2 | Minimal Planning/Health page chrome, copy reduction, three intentions | VALIDATED |
| UX-B3 | Submit-time context defaults, visible nominal standard state, Advanced options | VALIDATED |
| UX-B4 | Scenario Comparison shared context with per-scenario differentiators | VALIDATED |
| UX-B5 | Answer-first result hierarchy, chart formatting, compact provenance | VALIDATED |
| UX-B5-R1 | Quiet Financial OS static visual reconciliation | VALIDATED |
| UX-B6 | Skeletons, restrained microinteractions, responsive/accessibility stabilization | VALIDATED |
| UX-B7 | Independent validation and stabilization | VALIDATED / CLOSED |

Optional portfolio preview, assumption references, and Goal-derived presets are
separate backend mini-contracts and do not block UX-B1–UX-B7.

---

## Phase Contracts

---

### PHASE 10.1 — Goal Domain Foundation

**Entry Criteria:**
- 10.0 documentation reviewed and approved
- `position_snapshots` schema conflict investigated and resolved
- `requirements.txt` updated with missing dependencies (P2 fix)

**Scope:**
- Add DB migration (018_goals_enriched.sql): current_amount, priority, monthly_contribution, linked_account_id, assumptions_json to goals table
- Add new GoalType values: WEALTH_TARGET, INVESTMENT_TARGET, DIVIDEND_INCOME, FINANCIAL_INDEPENDENCE
- Update GoalModel ORM to include new fields
- Update GoalCreateDTO, GoalResponseDTO
- Update GoalRepository: update_goal, get_goal_by_id
- Add PUT /api/v1/goals/{id} endpoint
- Add DELETE /api/v1/goals/{id} endpoint
- Replace /goals frontend stub with functional Goal cards + create/edit modal
- Add goal progress display (current_amount / target_amount)

**Out of Scope:**
- Goal projections (Phase 10.3)
- Retirement engine (Phase 10.4)
- AI integration
- Existing investments/wealth pages

**Files expected to change:**
- `database/migrations/017_goals_enriched.sql` [NEW]
- `backend/infrastructure/persistence/models/goal.py` [MODIFY]
- `backend/domain/enums/goal_type.py` [MODIFY]
- `backend/application/dtos/goal_dto.py` [MODIFY]
- `backend/infrastructure/persistence/repositories/goal_repository.py` [MODIFY]
- `backend/application/use_cases/goal/` [MODIFY + ADD]
- `backend/api/routers/goals.py` [MODIFY]
- `backend/core/container.py` [MODIFY — add new use case factories]
- `frontend/src/app/goals/page.tsx` → moved to `/wealth-intelligence/goals/page.tsx`
- New navigation item in `frontend/src/config/navigation.ts`

**Tests:**
- Unit: GoalModel fields, GoalType enum
- Unit: goal_repository CRUD
- Integration: POST, GET, PUT, DELETE /api/v1/goals
- Integration: user isolation (goal of user A not visible to user B)

**Acceptance Criteria:**
- User can create a goal with all new fields
- User can view goal list with progress displayed
- User can edit and delete goals
- User isolation enforced
- All new tests pass

---

### PHASE 10.2 — Financial Health Intelligence (Micro-Process Execution Plan)

**Entry Criteria:** 10.1 COMPLETE and validated
**Execution Strategy (ADR-016):**
- **Mode A (Sonnet):** May execute a coherent group of micro-processes sequentially if validation gates pass.
- **Mode B (Gemini):** Must execute **one micro-process at a time**. Stop, report (IMPLEMENTED, TESTS, REGRESSIONS, FILES CHANGED, LIMITATIONS, VALIDATION REQUIRED, NEXT), and await explicit user approval.
- **No Guessing Rule:** If existing data does not support a metric exactly, stop and report. DO NOT invent fields or logic.

#### Quality Gates
- **GATE A:** Repository / Architecture conformity (Source of Truth strictness).
- **GATE B:** Automated tests pass.
- **GATE C:** Regression verification (Pierre, Investments, Goals unharmed).
- **GATE D:** Manual validation (Frontend only).
- **GATE E:** Documentation / Handoff updated.

---

#### 10.2.0 — Contract and Data Audit
- **Status:** COMPLETED.
- **Objective:** Finalize the Financial Health data contract and validate provisional hypotheses. No code changes.
- **Scope:** Validate Pierre models, Governance (PENDING/CLASSIFIED/ENTRADA/SAIDA/IGNORAR), Dates, account boundaries, and query patterns.
- **Resolution status:** The operational baseline is three continuous closed months. The Spending Anomaly Engine contract is locked in ADR-015; API route naming remains reserved for 10.2.6.
- **Completed conclusions:** only `CLASSIFIED` transactions are eligible; `PENDING` and `IGNORAR` are excluded; `ENTRADA` and `SAIDA` aggregate using `abs(amount)` and `transactions.date`; scope is consolidated across all eligible accounts in the local tenant. The operational baseline is the three continuous closed months preceding the analysed month. The local SQLite architecture remains single-tenant and `transactions` has no `user_id`.

#### 10.2.1 — Financial Health Read Query Foundation
- **Status:** IMPLEMENTED / VALIDATED.
- **Objective:** Extend `GovernedFinancialQuery` (or create `HealthFinancialQuery`) to retrieve required certified data.
- **Data Dependencies:** `transactions` (`governance_status == 'CLASSIFIED'`).
- **Implementation:** Query aggregates total income/expense, historical baseline (period locked in 10.2.0), and handles `IGNORAR`/`PENDING` omissions. No persistence.
- **Automated Tests:** consolidated account scope, classified-only, ignored omissions, date boundaries.
- **Validated implementation:** `HealthFinancialQuery` provides `get_cashflow`, `get_monthly_totals`, and `get_category_expenses` using `[start_date, end_date)` boundaries. Automated tests cover classified-only, PENDING/IGNORAR exclusion, absolute values, date boundaries, category aggregation, and consolidated multi-account scope. SQL validation reproduced the September/2026 cashflow totals.

#### 10.2.2 — Cashflow Metrics Engine
- **Status:** IMPLEMENTED / VALIDATED.
- **Objective:** Calculate deterministic Net Cashflow, Savings Amount, and Savings Rate.
- **Implementation:** `CashflowMetricsService` receives certified cashflow and monthly totals from the read layer and returns `CashflowSummaryDTO`; it does not query transactions or the database.
- **Metric Contract:** `net_cashflow = total_income - total_expense`; `savings_amount = net_cashflow`; `savings_rate = savings_amount / total_income`, or `None` when total income is zero. Monthly averages are calculated only from the supplied collection; an empty collection returns `None` averages.
- **Precision:** `HealthFinancialQuery` normalizes SQLite `SUM(ABS(amount))` aggregates to `Decimal` at the certified `NUMERIC(12,2)` transaction scale before supplying the Engine. Monetary values then remain exact `Decimal`; rates are fractional analytical `Decimal` values (for example, `0.4` = 40%) without cent quantization.
- **Trend:** The contract was absent when 10.2.2 was implemented. ADR-018 later locked deterministic month-over-month semantics, now implemented by `FinancialTrendService` in 10.2.10-B.
- **Automated Tests:** Positive, deficit, zero-income, zero-value, equal-value, single/multiple-month, empty-month collection, and Decimal precision scenarios.

#### 10.2.3 — Historical Financial Metrics
**Status:** VALIDATED.
- **Objective:** Provide a deterministic, typed series of certified monthly Financial Health metrics.
- **Implementation:** `HistoricalFinancialMetricsService` receives certified monthly totals, applies `CashflowMetricsService` to each supplied month, and returns chronological `MonthlyFinancialMetricsDTO` records. The series neither queries SQLite nor fills absent months.
- **Contract:** `reference_month` uses `YYYY-MM`; explicit zero-value months remain records; empty input returns an empty series; duplicate reference months raise `ValueError` rather than being silently aggregated. The caller remains responsible for selecting closed-month baselines and may include a current partial month when explicitly supplied.
- **Acceptance extension:** ADR-018 defines consecutive closed-month comparisons, directions, deltas, and insufficient-data behavior, implemented in 10.2.10-B. Rolling averages remain outside the locked acceptance contract.
- **Automated Tests:** chronological ordering, monthly metrics, deficit and zero-income behavior, empty history, gap preservation, explicit zero month, Decimal precision, and duplicate-month rejection.

#### 10.2.4 — Category Expense Intelligence
**Status:** VALIDATED.
- **Objective:** Provide deterministic expense-distribution metrics from certified category totals.
- **Implementation:** `CategoryExpenseIntelligenceService` receives pre-consolidated `CategoryExpenseTotalDTO` values, calculates total expense and analytical shares, and returns ranked `CategoryExpenseMetricDTO` values with a deterministic top category. It does not query SQLite or alter labels.
- **Contract:** `total_expense` is the exact sum of supplied category totals. Categories are ordered by expense descending and then lexicographically by their received label; ranks are sequential. Empty input returns total `Decimal('0.00')`, no categories, and no top category. Explicit zero categories remain records with `share_of_expenses = None`. Duplicate category input raises `ValueError`.
- **Precision and labels:** expense totals remain cent-scale `Decimal`; shares remain analytical `Decimal` without presentation rounding. Governed labels, including `Uncategorized`, are preserved exactly.
- **Acceptance extension:** ADR-018 exact-label category trends are implemented in 10.2.10-B and can later support factual budget-pressure composition. Extra concentration scores, category normalization, and aliases remain outside scope; anomaly semantics remain separately locked by ADR-015.
- **Automated Tests:** ranking, shares, total consistency, top category, unordered input, stable ties, empty input, zero total, Decimal precision, uncategorized preservation, and duplicate rejection.

#### 10.2.5 — Spending Anomaly Engine
**Status:** VALIDATED.
- **Objective:** Implement the approved deterministic anomaly contract in ADR-015. No ML/LLM.
- **Locked rules:** Require three continuous closed baseline months. A category with presence in at least two baseline months uses the arithmetic mean of certified present values (explicit zero is present) as its baseline; it is eligible for `SPIKE` only when the baseline is `>= Decimal('50.00')` and current expense is strictly greater than baseline times `Decimal('1.5')`. A category absent in all three baseline months is `NEW_EXPENSE` only when current expense is `>= Decimal('100.00')`.
- **States:** `NORMAL`, `SPIKE`, `NEW_EXPENSE`, `INSUFFICIENT_HISTORY`, `BELOW_BASELINE_FLOOR`, `NEW_EXPENSE_BELOW_THRESHOLD`, and global `INSUFFICIENT_BASELINE`. Only `SPIKE` and `NEW_EXPENSE` are anomalies.
- **Implementation:** `SpendingAnomalyService` consumes only prepared `CategoryExpenseMonthDTO` values. It has no SQLite, transaction, RAW, Pierre, persistence, API, or AI access; `SpendingAnomalySummaryDTO` exposes global status, evaluations, and only `SPIKE`/`NEW_EXPENSE` signals in `anomalies`.
- **Automated Tests:** all rule boundaries, two-of-three versus one-of-three history, explicit-zero versus absence, empty current/baseline, multiple categories, exact category matching, and Decimal precision.
- **Real-data validation:** September/2026 against June-August/2026 independently reproduced every category evaluation; `Transferências` and `Serviços` were the only `SPIKE` signals.

#### 10.2.6 — Financial Health API
**Status:** VALIDATED.
- **Objective:** Expose certified Financial Health results through authenticated FastAPI endpoints without financial calculations in the router.
- **Endpoints:** `GET /api/v1/financial-health/cashflow`, `/history`, `/categories`, and `/anomalies`, each requiring `reference_month=YYYY-MM`; there are no account filters.
- **Implementation:** The read-only router orchestrates `HealthFinancialQuery` and existing deterministic services, then serializes typed Pydantic responses. `Decimal` values are JSON strings; domain `None` values serialize as JSON `null`.
- **Automated Tests:** authentication, valid/invalid reference month, Decimal serialization, historical gaps/null rate, categories/ranking, anomaly results, and insufficient baseline.
- **Historical live reconciliation:** The authenticated API, `HealthFinancialQuery`, and independent SQLite Decimal aggregation reconciled when 10.2.6 was validated. Those September/2026 values and signals were point-in-time evidence, not fixtures. The later 10.2.10-A audit supersedes the incomplete-classification assumption: the current database has no `PENDING` transactions and its current totals must always be read live.

#### 10.2.7 — Financial Health Frontend Foundation
**Status:** VALIDATED.
- **Route and integration:** `/wealth-intelligence/health` uses the existing authenticated `fetchFromAPI` helper to load the four Financial Health API endpoints with an explicit `reference_month=YYYY-MM` selector. The configured API base already contains `/api/v1`; endpoint paths do not duplicate it.
- **Foundation states:** typed Decimal-string responses, local month selection, loading placeholders, retryable error state, empty history/categories/anomalies states, and `INSUFFICIENT_BASELINE` are implemented. The browser only formats certified values and does not calculate financial metrics, shares, ranks, or anomaly rules.
- **Intentional limitation:** the page uses simple lists and summary values only. Charts, visual comparisons, refined responsive behavior, and analytical polish remain in 10.2.8.
- **Manual Validation:** Completed with the real backend and frontend. Authentication, month selection, all four API-backed sections, consolidated values, anomaly signals, UTF-8 labels, and Wealth Intelligence navigation were confirmed in the browser.

#### 10.2.8 — Financial Health Analytical UI
**Status:** VALIDATED.
- **Objective:** Present the certified Financial Health data with useful hierarchy, visual context, and responsive analytical sections.
- **Implementation:** The route now uses reusable summary, history, category, and anomaly components. Summary cards include the API-provided recent averages; the Recharts history view uses independent monthly bars so gaps are not visually bridged and retains an exact-value table; category shares are represented as proportional ranked bars; anomaly cards expose current value, baseline reference, analytical ratio, and months used, with non-anomaly evaluations available as secondary detail.
- **States and accessibility:** Layout-shaped skeletons, retryable error messaging, empty sections, and `INSUFFICIENT_BASELINE` are retained and refined. Semantic headings, table headers/caption, form labeling, focus styles, textual legends, and non-color status labels provide basic accessible interpretation.
- **Constraint:** The frontend formats and visualizes API-certified values only. It does not recalculate financial totals, averages, shares, ranks, baselines, statuses, or thresholds; no AI/LLM was introduced.
- **Technical Validation:** Targeted ESLint and `npx tsc --noEmit` pass. The production Next.js build passes; the existing repository-wide Recharts SSR dimension warning remains non-blocking.
- **UI Polish (10.2.8-A):** The chart displays the latest six returned records while the table retains the complete returned history. Anomaly metadata reflows without overlap, long labels are protected, the Health TopNav marker follows the established color-dot pattern, and the Wealth Intelligence hub card uses a consistent icon.
- **Manual Validation:** Completed successfully for September/2026, another populated month, an empty certified month, chart/table windows, anomaly-card reflow, long labels, TopNav, hub icon, and browser console. No backend change was required.

#### 10.2.9 — Integration and Stabilization
**Status:** VALIDATED.
- **Objective:** Final code quality checks.
- **Integration audit:** Governed transactions flow through the certified query boundary, Decimal normalization, deterministic metrics/history/category/anomaly services, authenticated read-only API, typed frontend client, and analytical UI without responsibility leakage. Backend response models and frontend types match field by field.
- **Freshness:** Health endpoints query the current classified ledger on every request; the frontend uses `cache: "no-store"`. New governance classifications are reflected on the next request without snapshots, rebuild, reimport, or restart.
- **Frontend stabilization:** Rapid reference-month changes now use request sequencing so an older four-request batch cannot overwrite a newer month. History remains complete in the API/table and limited to the latest six returned records only in the chart.
- **Validation:** 47 Health tests pass. The general unit suite has 118 passes and only the two historical Investments mock/timeline failures. TypeScript, targeted Health lint, production build, authenticated real-data HTTP smoke, and OpenAPI route checks pass.
- **Known non-blockers:** ADR-014 Alembic FK mismatch, global mobile responsiveness debt, repository-wide lint debt, and the existing Recharts SSR dimension warning remain outside Financial Health stabilization.

#### 10.2.10 — Acceptance Completion and Final QA
**Status:** COMPLETED.
- **10.2.10-A — Financial Trend, Stability Readiness & Acceptance Contract Lock:** `VALIDATED`. The read-only ledger audit confirmed 1,420/1,420 transactions classified, `PENDING = 0`, and 17 continuous calendar months (`2025-05` through partial `2026-09`). ADR-018 locks global/category trend semantics, factual budget pressure, the Health/Planning boundary, and stability readiness. No code or data changed.
- **10.2.10-B — Deterministic Global & Category Trend Engine:** `VALIDATED`. Independent read-only SQLite plus Python `Decimal` reconciliation on 2026-09-15 matched all four Jul→Aug/2026 global facts and the complete 24-category union, including cross-year, insufficient-data, gap, zero, negative, invalid-input, and duplicate-input checks. `FinancialTrendService` consumes certified `MonthlyFinancialMetricsDTO` and `CategoryExpenseMonthDTO` collections without DB access. It exposes separate global/category summaries, resolves a requested current partial month to the previous closed month using an explicit caller-supplied current reference, requires the exact preceding calendar month, and returns valid empty `INSUFFICIENT_DATA` summaries rather than skipping gaps.
- **Global implementation:** income, expense, net cashflow, and savings-rate comparisons expose exact Decimal current/previous values, absolute and percentage deltas, and ADR-018 directions. Previous zero yields no percentage; an undefined savings rate yields metric-level `INSUFFICIENT_DATA` and no artificial zero.
- **Category implementation:** exact-label union with `INCREASED`, `DECREASED`, `UNCHANGED`, `NEW`, and `DISAPPEARED`; explicit zero remains presence. Target-present categories are ordered by current expense descending then label, followed by disappeared categories ordered by previous expense descending then label. This is deterministic presentation order, not a new financial ranking.
- **Validation:** 13 new tests cover the 22 required global/category/precision behaviors. The full Health suite passes (`60 passed`). Read-only production-query versus independent SQLite Decimal validation reconciled all four Jul→Aug metrics and all 24 categories in the union; Dec/2025→Jan/2026 and insufficient 2025-05 also passed. General baseline remains `118 passed, 2 failed`, exclusively the known Investments timeline mocks.
- **Stability:** `NOT IMPLEMENTED — CONTRACT PENDING`. No stability fact, variability calculation, or score was added.
- **10.2.10-C — Trend Exposure and Stability Decision:** `VALIDATED`. Authenticated `GET /api/v1/financial-health/trends?reference_month=YYYY-MM` exposes the already validated ADR-018 global and category facts using Decimal JSON strings/null. The router builds only certified history/category inputs, supplies the local current month at the API boundary, and delegates all trend arithmetic to `FinancialTrendService`. The Health UI fetches the endpoint in its existing race-protected batch. The UX polish consolidates temporal context, turns global/category trends into compact visual KPIs, and paginates the existing history array at 12 months per page with the latest records shown first. M-01 corrected the visual period direction to chronological `comparison_month → trend_target_month`. No API/UI layer recalculates financial facts.
- **Final manual QA:** completed. Functional browser validation and the independent release review found no blockers or HIGH findings; the verdict was `PASS WITH NON-BLOCKING NOTES` with LOW release risk.
- **Gate:** satisfied. Phase 10.2 is `COMPLETED` after explicit user sign-off and M-01 validation.

**Phase boundary:** Financial Health owns observed facts, realized surplus/deficit, comparisons, trends, distribution, and anomalies. Sustainable contribution capacity is deferred to Planning; investment capacity is deferred to Planning/Portfolio Intelligence; composite financial stability remains deferred until a deterministic contract is approved. These are planned boundaries, not Phase 10.2 failures. The root product specification is high-level vision, while ADR-018 is the executable trend contract.

---

### PHASE 10.3 — Planning & Projection

**Status:** `VALIDATED / CLOSED`. `10.3.0–10.3.6 = VALIDATED`; `10.3.7-A = DEFERRED — INSUFFICIENT CONTRACT / DATA`; `10.3.8-A = API CONTRACT LOCKED / PERSISTENCE DEFERRED`; `10.3.8-B–E = VALIDATED`; `10.3.8-F = AUTOMATED VALIDATION PASSED`; Swagger manual smoke is `DEFERRED BY USER`; `10.3.9–10.3.10 = VALIDATED`; `10.3.10A = CONTRACT LOCKED`; `10.3.10B1–B4 = VALIDATED`; `10.3.10B = VALIDATED / COMPLETE`; `10.3.11 = VALIDATED / STABILIZED`; `10.3.12 = VALIDATED / CLOSED`. ADR-024 governs the post-closure Planning UX refinement: `UX-B1–UX-B7 = VALIDATED`; POST-10.3 UX is `VALIDATED / CLOSED`. Planning now remains the reusable projection/solver authority under the locked Phase 10.4 FIRE contract.

**Entry Criteria:** 10.1 and 10.2 are complete, validated, merged, and available as certified inputs. Satisfied by PR #2 merge commit `b7ce8b8`.

**Responsibility:** Planning combines certified current facts, user-governed Goals, and explicit user assumptions to produce generic deterministic forward projections, future wealth, target dates, required contributions, scenario comparisons, inflation-aware nominal/real results, Goal timing facts, and other conditional Planning results. Projections are conditional outputs, never guaranteed returns.

**Out of Scope:** FIRE/retirement-specific target wealth, withdrawal rates, retirement income sustainability, asset selection, portfolio rebalancing, trades, market forecasts, recommendation engines, and LLM calculation. Phase 10.4 owns FIRE/retirement semantics; Phase 10.5 owns portfolio intelligence. A future LLM may explain certified Planning results but never calculate them.

#### Verified Reuse Baseline

| Existing Component | Reuse in Planning | Read-only? | Notes |
|---|---|---:|---|
| Goals model/repository/API | Target amount/date, current amount, planned contribution, type, status, priority | Yes | Persisted `Numeric` values are currently converted to `float` by Goal entity/repository/DTOs. Planning must establish a Decimal-safe boundary and must not execute opaque `assumptions_json` without a new contract. |
| `HealthFinancialQuery` | Certified classified monthly income/expense facts | Yes | Reuse through an application/read boundary, not router SQL duplication. |
| `HistoricalFinancialMetricsService` | Realized net cashflow and savings facts over supplied months | Yes | Historical realized surplus is context; it is not sustainable contribution capacity. |
| `FinancialTrendService` | Closed-month factual direction/context | Yes | Useful as context only; trends are not return or contribution forecasts. |
| Health categories/anomalies | Optional factual spending context | Yes | Not a default projection input and never a source of automatic advice. |
| `PortfolioSnapshotModel` | Candidate current investment wealth and monthly investment history | Yes | `patrimonio` is MyProfit investment-portfolio wealth, not proven consolidated net worth. Current Investments endpoints return dynamic dictionaries and convert values to `float`; Planning needs a typed Decimal read boundary if this source is approved. |
| `PositionSnapshotModel` + asset valuations | Reconciliation or scoped investment facts | Yes | Do not sum positions inside Planning when an approved portfolio total exists. Current value freshness and account scope must be contracted. |
| `IncomeEventModel` | Historical dividend context | Yes | Not guaranteed future income. Future-dated rows require explicit semantics before use. |
| Portfolio snapshot benchmarks | Historical CDI/IPCA/IBOV context | Yes | Historical external facts must not become future return/inflation assumptions automatically. |
| `MarketDataService` / yfinance | Current external quote context | Yes | External and cached; not a projection-rate authority. |
| Existing Goals/Health/Investments APIs | Contract reference for frontend integration | Yes | Backend Planning orchestration must reuse repositories/services, not call its own HTTP endpoints. |

#### Planning Data Lineage

```text
Certified investment wealth + certified Health facts + user-governed Goals
                              + explicit user assumptions
                                      ↓
                         Planning input/read boundary
                   (source, as-of date, scope, Decimal)
                                      ↓
                    Deterministic Planning engines
                                      ↓
                 Typed Planning results and provenance
                                      ↓
                           Authenticated API
                                      ↓
                         Read-only frontend UI
                                      ↓
                 Future LLM interpretation only
```

#### Locked Contract Summary

ADRs 019–023 are the detailed source of truth. The approved implementation constraints are:

1. **Typed inputs:** initial wealth declares exactly one origin (`GOAL_CURRENT_AMOUNT`, `INVESTMENT_PORTFOLIO_SNAPSHOT`, or `USER_PROVIDED_SCENARIO`) with scope/as-of/provenance; sources are never summed automatically. MyProfit `patrimonio` is investment wealth, not consolidated net worth.
2. **Decimal boundary:** 10.3.1 must bypass the existing Goal float path through read-only Decimal adapters. No projection math belongs in 10.3.1.
3. **Monthly math:** period zero is `as_of_date`; the next complete calendar month is period one; contributions use `END_OF_MONTH` timing.
4. **Rates:** explicit finite effective annual Decimal rates accept every value `> -1`, with no arbitrary positive cap. Monthly conversion is compound-equivalent, never annual/12.
5. **Nominal/real:** the approved matrix applies inflation exactly once when converting nominal return to real output. `REAL` return to `NOMINAL` output is unsupported initially. Goal integration must declare `target_value_basis`.
6. **Horizon and precision:** exactly one horizon selector; 1–1,200 full months; month-level target dates; 34-digit context; monthly rate with at least 18 decimal places; cent-scale `ROUND_HALF_EVEN` monetary recurrence.
7. **Solvers:** both reuse the Forward Projection Engine. Required contribution uses monotonic cent-based binary search and returns the smallest satisfying cent value.
8. **Scenarios:** archetypes are editable labels without hardcoded rates; historical data is never an automatic forecast; scenarios are transient first.
9. **Boundaries:** sustainable contribution capacity remains deferred in 10.3.7; Retirement/FIRE is Phase 10.4; Portfolio Intelligence is Phase 10.5.

#### Microprocess Roadmap

| ID | Name | Objective | Depends On | Produces Code? |
|---|---|---|---|---:|
| 10.3.0 | Planning Contract & Data Audit | **VALIDATED.** Domain/data audit completed and contracts locked by ADRs 019–022. No engine. | 10.1, 10.2 | No |
| 10.3.1 | Planning Read Foundation | **VALIDATED.** Immutable typed facts; Decimal-safe owned Goal reads; explicit-account latest portfolio snapshot reads; certified Health query/service reuse; typed source/scope/as-of/provenance; no automatic source selection or aggregation. No projection math. | 10.3.0 | Yes |
| 10.3.2 | Projection Assumptions Boundary | **VALIDATED.** Immutable typed assumptions enforce Decimal-only contribution/rates, the nominal/real matrix, explicit constants, and one calendar-month horizon source. Independent validation confirmed strict boundaries without rate conversion, Fisher calculation, or projection math. | 10.3.0, 10.3.1 | Yes |
| 10.3.3 | Deterministic Forward Projection Engine | **VALIDATED.** Pure immutable Decimal engine with magnitude-derived adaptive local precision, effective annual → monthly equivalent conversion, one-time Fisher when applicable, `END_OF_MONTH` contributions, cent-scale monthly `ROUND_HALF_EVEN`, month-end timeline, provenance, and exact cumulative totals. Independent V2 revalidation matched an 800-digit oracle across extreme and cross-mode cases and proved both sides of the former precision bug are regression-protected. No solver or Goal coupling. | 10.3.2 | Yes |
| 10.3.4 | Target & Required Contribution Solvers | **VALIDATED.** `10.3.4-A = VALIDATED`: strict target input, period-zero semantics, first crossing, conservative `UNREACHABLE`, output-basis neutrality, provenance, immutability, and Decimal magnitude. `10.3.4-B = VALIDATED`: independent cent-grid and 500-digit oracles proved template-contribution independence, monotonicity including negative `ROUND_HALF_EVEN` ties and near-`-1`, the constructive target upper bound, logarithmic integer-cent search, and exact `C`/`C - 0.01` minimality without sustainability semantics. | 10.3.3 | Yes |
| 10.3.5 | Goal Planning Integration | **VALIDATED** (TSK-10.3.5-V3). Final independent validation confirmed ACTIVE-only positive eligibility, applicability before target basis/output, Goal-current-amount provenance, and deadline validation, zero solver calls for non-projectable Goals, strict ACTIVE validation, and separation between lifecycle `ACHIEVED` and mathematical `ALREADY_ACHIEVED`. 63 tests. | 10.3.1, 10.3.3, 10.3.4 | Yes |
| 10.3.6-A | Scenario Comparison Contract & Architecture Lock | **CONTRACT LOCKED.** Explicit unique scenario/reference IDs; BASE is not automatic reference; minimum two ordered scenarios; shared as-of/resolved horizon/output mode/timing; optional shared target; certified engine reuse; exact delta/month semantics; atomic prevalidation; transient, non-advisory output. | 10.3.3, 10.3.4, 10.3.5 | No |
| 10.3.6-B | Scenario Comparison Engine Implementation | **VALIDATED.** Independent contract/code/oracle validation confirmed immutable pure-domain comparison over `ForwardProjectionEngine` and `TargetAchievementSolver`, explicit references, atomic comparability validation, optional shared target, exact Decimal deltas, certified-result preservation, and no second financial math, persistence, Goal auto-integration, Required Contribution automation, ranking, or advice. Focused suite: `37 passed`; all Planning/Goals/Health regressions passed; general unit: `403 passed, 2 historical Investments/MagicMock failures`. | 10.3.6-A | Yes |
| 10.3.7-A | Sustainable Contribution Capacity Contract Decision | **DEFERRED — INSUFFICIENT CONTRACT / DATA.** Certified Health provides realized history, not recurring forward affordability. No approved window, minimum history, partial-month, deficit, anomaly/outlier, statistic, negative-result, currency, or missing/zero policy supports the word `sustainable`. No formula or implementation was created. | 10.3.0, validated Health facts | No; implementation remains gated |
| 10.3.8-A | Planning API & Scenario Persistence Contract Audit | **API CONTRACT LOCKED / PERSISTENCE DEFERRED — TRANSIENT API FIRST.** Five authenticated capability endpoints are locked under `/api/v1/planning`; request facts cannot impersonate certified sources; Goal ownership is enforced server-side; portfolio API sourcing is deferred because snapshot accounts lack user ownership; JSON money/rates are strings; persistence lacks lifecycle/versioning/provenance/staleness contracts. | 10.3.3–10.3.6; 10.3.7-A decision | No |
| 10.3.8-B | Planning API Foundation | **VALIDATED.** Independent review confirmed the empty registered `/planning` router, existing-JWT and synchronous-reader dependency annotations, real-JSON strict Decimal strings, secure selectors, pure builders/mappers, local error translation, and OpenAPI/startup safety. No financial endpoint, engine call, persistence, or portfolio source was added. | 10.3.8-A | Yes |
| 10.3.8-C | Generic Planning Calculation Endpoints | **VALIDATED.** Independent HTTP validation confirmed exactly three authenticated transient routes, strict Decimal-string request/response fidelity, server-owned Goal-current-amount resolution and 404 non-enumeration, exact engine delegation, domain-status preservation, local errors, OpenAPI scope, and no financial recomputation, write, persistence, or out-of-scope endpoint. Focused suite: `25 passed`; general unit: `465 passed, 2 historical Investments/MagicMock failures`. | 10.3.8-B | Yes |
| 10.3.8-D | Goal Planning Endpoint | **VALIDATED.** Final independent validation proved the pure preflight and evaluate path share one lifecycle/type authority across all real status/type pairs. Non-projectable Goals do not consume selected Goal current amount; ACTIVE eligible Goals still return `422` when that fact is required and absent. No dummy wealth, DB access in domain, or router eligibility duplication. Focused suite: `39 passed`; Goal Planning domain: `101`; general unit: `546 passed, 2 historical Investments/MagicMock failures`. | 10.3.8-B, 10.3.8-C | Yes |
| 10.3.8-E | Scenario Comparison Endpoint | **VALIDATED.** Independent HTTP/domain/OpenAPI validation confirmed explicit scenario/reference IDs, input-order preservation, metadata-only archetypes, server-owned Goal resolution, atomic source failure, resolved-horizon equivalence, ReturnType variation, target-pair strictness, one Comparison engine call, certified delta mapping, and no ranking/recommendation/persistence/portfolio source. Focused HTTP suite: `42 passed`; Planning domain regressions: `323 passed`; Goals `65`; Health `68`; general `585 passed, 2 historical Investments/MagicMock failures`. | 10.3.8-B, 10.3.8-C | Yes |
| 10.3.8-F | API Integration & Independent Validation | **AUTOMATED VALIDATION PASSED.** Cross-endpoint validation confirms exact authenticated OpenAPI route set, strict Decimal/source consistency, Goal ownership, read-only dependency boundaries, D/E regressions, deterministic 1,200-month serialization, and no persistence/advice/math duplication. Swagger Authorize manual smoke is deferred by user. | 10.3.8-C–10.3.8-E | Validation/fixes only |
| 10.3.9 | Planning Frontend Foundation | **VALIDATED.** Manual smoke passed for Nominal→Nominal, Real→Real, Nominal→Real, and unavailable Real→Nominal. | 10.3.8 | Yes |
| 10.3.10 | Planning Analytical UI | **VALIDATED.** Five certified capabilities share string-only assumptions/source inputs; certified results and chart-only period visualizations are displayed without browser financial calculation or persistence. Technical and manual validation passed; broader visual/UX refinements were deferred by the user. | 10.3.9 | Yes |
| 10.3.10A | Investment Portfolio Source Contract & Ownership Audit | **CONTRACT LOCKED.** ADR-023 formalizes guarded single-tenant ownership, one canonical MyProfit scope, source-only request shape, no-look-ahead as-of selection, Decimal/BRL/provenance boundaries, all-five-endpoint coverage, and no migration for this constrained mode. | 10.3.10 | No |
| 10.3.10B1 | Investment Portfolio Source Resolver & Reader Foundation | **VALIDATED.** Internal read-only ADR-023 resolver validates the exact one-user tenant invariant, semantic UUID ownership, complete MyProfit scope/run provenance, deterministic zero/one/many outcomes, strict `YYYY-MM` buckets, and latest-eligible-as-of Decimal fact construction without a fabricated `observed_at`. No public selector, router, frontend, engine, migration, or persistence was added. | 10.3.10A | Yes |
| 10.3.10B2 | Planning API Portfolio Source Integration | **VALIDATED.** The strict source-only public selector is wired through Projection, Target Achievement, Required Contribution, Goal Planning after domain preflight, and Scenario Comparison before its atomic engine call. B1 remains the only portfolio resolver; source errors are safe `422`; no frontend, migration, schema, engine, or write path was added. | 10.3.10B1 | Yes |
| 10.3.10B3 | Planning Frontend Portfolio Source Integration | **VALIDATED.** The shared Planning UI sends source-only portfolio requests and renders certified amount/month/provenance without preview, account selection, client-certified facts, or UI financial math. User smoke passed for all five capabilities. | 10.3.10B2 | Yes |
| 10.3.10B4 | Planning Portfolio Source Independent Validation | **VALIDATED.** Adversarial end-to-end validation confirmed ownership, temporal, Decimal, trust, read-only, API, frontend, and documentation gates. Macro `10.3.10B = VALIDATED / COMPLETE`. | 10.3.10B3 | No |
| 10.3.11 | Integration & Stabilization | **VALIDATED / STABILIZED.** Five APIs/capabilities, all approved sources, Decimal, provenance, auth, source switching, status/error/loading states, static boundaries, and regressions reconciled without a new Planning contract or production fix. | 10.3.5–10.3.10B | Yes, fixes only |
| 10.3.12 | Manual Validation & Phase Closure | **VALIDATED / CLOSED.** Consolidated accepted manual evidence with proportional final backend/frontend/OpenAPI/static checks; no production fix, feature, or contract change required. Do not start 10.4 automatically. | 10.3.11 | Documentation/validation only |

#### 10.3.10B Locked Implementation Order

A. **Schema/migration:** no migration in the ADR-023 single-tenant mode; verify the locked invariant at runtime rather than introducing a partial ownership schema.
B. **Reader/resolver:** add an ownership-aware application resolver plus an as-of-aware, read-only Decimal portfolio reader.
C. **Domain/API selector:** expose only the portfolio source discriminant; reuse the existing source, scope, fact, and public provenance contracts.
D. **Endpoint integration:** wire the selector into Projection, Target Achievement, Required Contribution, Goal Planning after applicability preflight, and atomically into Scenario Comparison.
E. **Tests:** execute the ADR-023 ownership, cardinality, temporal, Decimal, provenance, endpoint, atomicity, and existing-source regression matrix.
F. **Frontend source selector:** add the explicit portfolio option to existing Planning contracts and controls without accepting or calculating an amount in the browser.
G. **Focused UI integration:** display only the returned certified amount and provenance dates; do not add a preview endpoint or broader UX redesign.
H. **Independent validation:** adversarially validate the complete boundary before advancing to 10.3.11.

#### Acceptance Question Ownership

| User Question | Owner | Required Engine | Microtask |
|---|---|---|---|
| Quanto terei em 5, 10 e 20 anos? | Planning | Forward projection | 10.3.3 |
| Quando atinjo R$ 1 milhão? | Planning | Target-date solver | 10.3.4 |
| Quanto preciso investir por mês para atingir minha meta? | Planning | Required-contribution solver | 10.3.4 generic capability; explicit invocation only, not a 10.3.5 timing side effect |
| Se aumentar meu aporte em R$ 500, o que muda? | Planning | Scenario comparison | 10.3.6 |
| Minha meta está no caminho certo? | Planning + Goals | Goal integration over projection/solver facts | 10.3.5 |
| Quanto posso aportar de forma sustentável? | Planning, contract-gated | Sustainable capacity engine only if approved | 10.3.7 |
| Quanto preciso para viver de renda? | Phase 10.4 FIRE | FIRE target/withdrawal-income contract | 10.4, not 10.3 |

#### Test Strategy Gate

- Known-output unit tests for zero contribution/return, positive return, supported negative return, zero initial wealth, target already achieved, impossible/invalid targets, cross-year and long horizons.
- Exact Decimal, rate-conversion, timing, quantization, solver-tolerance, deterministic-repeatability, scenario-equality, and scenario-delta tests.
- Missing/stale source facts, account scope, provenance, Goal eligibility/integration, auth/user isolation, JSON string/null serialization, and transient/persisted scenario lifecycle tests as applicable.
- Independent spreadsheet or separate Decimal oracle validation for projection and inverse-solver cases; the production engine cannot be its own oracle.
- Frontend contract/type/build/lint validation plus proof that the browser does not recalculate projections.

**Execution Gate:** Phase 10.3 is `VALIDATED / CLOSED`. 10.3.7-A remains `DEFERRED — INSUFFICIENT CONTRACT / DATA`; `10.3.8-F = AUTOMATED VALIDATION PASSED` and Swagger Authorize manual smoke remains `DEFERRED BY USER`; `10.3.10A = CONTRACT LOCKED`; macro `10.3.10B = VALIDATED / COMPLETE`; `10.3.11 = VALIDATED / STABILIZED`; `10.3.12 = VALIDATED / CLOSED`. Persistence remains prohibited until a separate owner/lifecycle/versioning/provenance/staleness contract is approved. ADR-024 governs the separate UX-B1–UX-B7 implementation sequence.

---

### PHASE 10.4 — Retirement & Financial Independence (FIRE)

**Entry Criteria:** 10.3 COMPLETE

**Status:** `VALIDATED / CLOSED`

| Microtask | Scope | Status |
|---|---|---|
| 10.4-A | FIRE contract and source-of-truth audit | AUDIT COMPLETE |
| 10.4-B | FIRE contract lock and ADR-025 | CONTRACT LOCKED |
| 10.4-C | Implementation decomposition | IMPLEMENTATION PLAN COMPLETE |
| 10.4-D1 | FIRE Domain Core | IMPLEMENTED / VALIDATED — pure Decimal summary core; 27 focused tests passed |
| 10.4-D2 | FIRE Application Orchestration | IMPLEMENTED / VALIDATED — one wealth resolution, canonical target handoff, REAL Planning composition, provenance continuity |
| 10.4-D3 | FIRE API | IMPLEMENTED / VALIDATED — authenticated discriminated endpoint, strict Decimal strings, safe mapping/OpenAPI |
| 10.4-D4 | FIRE Frontend Foundation | IMPLEMENTED / VALIDATED — typed client, strict builders, pt-BR form inputs, mode disclosure, minimal entry points |
| 10.4-D5 | FIRE Results & UX | IMPLEMENTED / VALIDATED — target-first presentation, provenance, living result states, accessibility, and string-safe rendering |
| 10.4-D6 | Integration & Stabilization | VALIDATED / STABILIZED — consolidated backend/frontend, OpenAPI, authority, read-only, and regression evidence |
| 10.4-D7 | Independent Validation & Closure | VALIDATED / CLOSED — fresh-context contract, implementation, oracle, regression, OpenAPI, frontend, and boundary review passed |

**Authority:** ADR-025 and `FIRE_CONTRACT.md`.

**Locked MVP boundary:** FIRE is a thin deterministic orchestration layer over Planning. It constructs a real FIRE target from explicit monthly retirement spending and an explicit assumed annual withdrawal rate, reports summary progress and conditional withdrawal capacity, and delegates projected date and required contribution to the existing Planning solvers. It accepts exactly one of the certified portfolio selector or a user-provided Planning wealth scenario. Investment wealth is not net worth.

The one future authenticated endpoint has three contracted modes: `SUMMARY`, `PROJECTED_DATE`, and `REQUIRED_CONTRIBUTION`. Output is real; return input may be real, or nominal with explicit inflation and one Planning-owned Fisher conversion. Health inference, dividends, external income, Goal linkage, persistence, taxes, longevity, Monte Carlo, FIRE variants, scenario comparison, and portfolio advice are outside the MVP.

`FIRE_IMPLEMENTATION_PLAN.md` remains the decomposition authority for D1–D7. `10.4-D1` through `10.4-D5` are implemented and validated; D6 is validated/stabilized; D7 independently validated and closed the phase without reopening locked semantics. Phase 10.5-A subsequently completed its audit; 10.5-B is paused by the Wealth OS realignment gate.

---

### PHASE 10.5 — Portfolio Intelligence

**Entry Criteria:** 10.4 COMPLETE, existing Investments stable

**Status:** `10.5-A AUDIT COMPLETE / USER DECISIONS RESOLVED; 10.5-B PAUSED / PENDING WEALTH OS REALIGNMENT`

| Microtask | Scope | Status |
|---|---|---|
| 10.5-A | Portfolio Intelligence contract and source-of-truth audit | AUDIT COMPLETE / USER DECISIONS RESOLVED |
| 10.5-B | Portfolio Intelligence contract lock | PAUSED / PENDING WEALTH OS REALIGNMENT |

**Approved boundary only (ADR-022):** Future allocation, concentration, diversification, attribution, rebalance analysis, portfolio quality, and asset-level intelligence. Planning does not select assets, recommend investments, or infer future returns from portfolio composition/history.

The 10.5-A evidence is preserved in `PORTFOLIO_INTELLIGENCE_CONTRACT_AUDIT.md`. It found a certified aggregate monthly investment-wealth fact, but no currently reconciled position-valuation authority and no locally certified portfolio-performance engine. No Portfolio Intelligence implementation is authorized before 10.5-B locks the source, temporal, precision, ownership, and MVP metric contracts. Existing `/wealth` remains unchanged by 10.5-A.

**Tests:** To be locked in 10.5-B; no attribution or performance test contract is accepted by 10.5-A.

---

### PHASE 10.6 — Rebalancing & Watchlist

**Entry Criteria:** 10.5 COMPLETE

**Scope:**
- TargetAllocation model (user defines % per asset class)
- Rebalancing engine (deviation calculation)
- Rebalancing UI (target editor + deviation table)
- Watchlist model + CRUD endpoints
- Watchlist frontend page
- Basic threshold alerts (not push notifications — display in UI only)

---

### PHASE 10.7 — External Market Intelligence

**Entry Criteria:** 10.5 COMPLETE, bcb and news research validated

**Scope:**
- BCBAdapter: CDI, SELIC, IPCA from BCB/SGS API
- NewsService: Google News RSS retrieval + sanitization
- brFinance adapter (isolated): CVM fundamentals for BR stocks
- Technical indicators service: RSI, SMA, EMA from yfinance history
- Market Radar frontend page
- News & Events frontend page
- All external data labeled with timestamps and source

**Dependency additions:** python-bcb, feedparser (or requests+lxml), pandas-ta
**Tests:** BCB integration tests (mock HTTP), news sanitization tests (injection patterns)

---

### PHASE 10.8 — LLM Provider Foundation

**Entry Criteria:** 10.7 COMPLETE, Ollama installed on host

**Scope:**
- LLMProvider Protocol + OllamaProvider + GeminiProvider + OpenAIProvider
- LLMProviderFactory (reads AI_PROVIDER env var)
- Structured output with Pydantic schema enforcement
- InsightResponse model + validation pipeline
- Prompt injection sanitization utility
- ai_insights DB table (new migration)
- Fallback chain: Ollama → Gemini (if local unavailable)
- Observability: ai_runs integration with new provider

**Environment variables added (to .env.example):**
- AI_PROVIDER, AI_MODEL, AI_OLLAMA_BASE_URL, AI_TEMPERATURE, AI_MAX_TOKENS, AI_TIMEOUT_SECONDS, AI_FALLBACK_PROVIDER

**Tests:** Unit tests for each provider (mocked HTTP), structured output validation tests, prompt injection tests

---

### PHASE 10.9 — Wealth AI Briefing

**Entry Criteria:** 10.8 COMPLETE, 10.4 COMPLETE, 10.5 COMPLETE

**Scope:**
- WealthContextBuilder: aggregates portfolio, cashflow, goals, market, news into structured context
- BriefingService: DAILY, WEEKLY, PORTFOLIO, GOAL, EXPENSE insight generation
- APScheduler jobs: daily briefing at 7AM (configurable)
- Wealth AI frontend page: briefing display, historical list, data freshness indicators
- All AI content labeled with violet accent + generated_at timestamp

**Tests:** Context builder unit tests, briefing validation tests (schema), scheduling tests, prompt injection defense tests

---

### PHASE 10.10 — Advanced Orchestration [CONDITIONAL]

**Entry Criteria:** 10.9 COMPLETE + demonstrated quality gap
**Status:** Only start this phase if single-LLM briefings are demonstrably insufficient.

If started:
- Evaluate sequential agent approach for specific insight types
- Document quality delta vs single LLM
- No external agent framework (custom orchestration only)

---

### PHASE 10.11 — Docker & Operations

**Entry Criteria:** All backend phases stable

**Scope:**
- Dockerfile for backend
- Dockerfile for frontend (Next.js production build)
- docker-compose.yml (backend + frontend + optional services)
- Environment variable documentation
- Startup guide for `docker compose up`
- CORS configuration for production
- Ollama native setup guide

---

### PHASE 10.12 — Global UX / Visual Polish

**Entry Criteria:** All functional phases complete

**Scope:**
- Google Fonts integration (Inter or Plus Jakarta Sans)
- Expanded color system
- Typography scale standardization
- Consistent card hierarchy
- Animation/transition review
- Mobile responsiveness audit
- Accessibility audit (aria labels, keyboard navigation)
- Visual consistency pass across all pages (existing + new)

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| position_snapshots schema conflict | HIGH | HIGH | Must verify and fix BEFORE 10.1 migration |
| Ollama model doesn't fit in 8GB VRAM | MEDIUM | MEDIUM | Test before committing, use quantized models |
| yfinance rate limiting at scale | MEDIUM | LOW | Persistent cache in future |
| brFinance maintenance/reliability | MEDIUM | LOW | Wrap in adapter, fallback to yfinance.info |
| BCB API changes | LOW | MEDIUM | Version API calls, document series IDs |
| Google News RSS access removed | MEDIUM | LOW | Have alternate news source |
| requirements.txt incomplete | HIGH | MEDIUM | Fix immediately (P2) |
| GoalModel missing fields | HIGH | HIGH | Phase 10.1 migration |
