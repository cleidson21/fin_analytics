# Implementation Roadmap — Wealth Intelligence
**Status:** ACTIVE (Phase 10.2 completed; Phase 10.3 next)
**Date:** 2026-09-15

---

## Roadmap Overview

| Phase | Name | Status | Depends On | Est. Scope |
|-------|------|--------|-----------|------------|
| 10.0 | Architecture & Product Design | **COMPLETE** | — | Documentation only |
| 10.1 | Goal Domain Foundation | IMPLEMENTED / VALIDATED | 10.0 | DB migration, Goal model enrichment, CRUD, basic UI |
| 10.2 | Financial Health Intelligence | **COMPLETED — 10.2.10-C VALIDATED** | 10.1 | Expense analytics, savings rate, spending trends |
| 10.3 | Planning & Projection Engine | **NOT STARTED / NEXT** | 10.1, 10.2 | Goal calculations, projections, scenarios |
| 10.4 | Retirement / Financial Independence | NOT_STARTED | 10.3 | Retirement engine, FI projection, sensitivity |
| 10.5 | Portfolio Intelligence & Simulation | NOT_STARTED | existing Investments, 10.3 | Attribution, simulations |
| 10.6 | Rebalancing & Watchlist | NOT_STARTED | 10.5 | Target allocation, watchlist |
| 10.7 | External Market Intelligence | NOT_STARTED | 10.5, BCB/News research | BCB, news, fundamentals |
| 10.8 | LLM Provider Foundation | NOT_STARTED | 10.7 | LLMProvider abstraction, Ollama + Gemini |
| 10.9 | Wealth AI Briefing | NOT_STARTED | 10.8, 10.4, 10.5 | Context builder, structured insights, briefing UI |
| 10.10 | Advanced Orchestration | NOT_STARTED | 10.9 — **CONDITIONAL** | Only if single-LLM approach proves insufficient |
| 10.11 | Docker & Operations | NOT_STARTED | All backend phases | Containerization, compose, ops guide |
| 10.12 | Global UX / Visual Polish | NOT_STARTED | All UI phases | Design system, typography, final visual pass |

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

### PHASE 10.3 — Planning & Projection Engine

**Entry Criteria:** 10.1 and 10.2 COMPLETE

**Scope:**
- GoalCalculationService: compute required_monthly_contribution, projected_completion_date, progress_pct, scenarios (conservative/baseline/optimistic)
- RetirementProjectionService (foundation): compound interest engine, gap analysis (full UI in 10.4)
- SimulationEngine: what-if scenarios for goals
- Endpoints: /api/v1/goals/{id}/projection, /api/v1/goals/{id}/scenarios
- Frontend: Goal projection charts, scenario comparison

**Tests:** Unit tests for every calculation with known inputs/outputs, edge cases (negative progress, 0 contribution, overshot goals)

---

### PHASE 10.4 — Retirement / Financial Independence

**Entry Criteria:** 10.3 COMPLETE

**Scope:**
- Full Retirement/FI page: inputs panel, scenario chart, gap analysis, sensitivity table
- RetirementProjectionService: full implementation (inflation, withdrawal rate, passive income)
- UserRetirementProfile model/endpoint for saving assumptions
- Simulation scenarios: conservative/baseline/optimistic

**Tests:** Unit tests for projection engine (compare against Excel formula manually), sensitivity calculation tests

---

### PHASE 10.5 — Portfolio Intelligence & Simulation

**Entry Criteria:** 10.3 COMPLETE, existing Investments stable

**Scope:**
- Portfolio attribution service (contributions + price changes + dividends + FX)
- Winners/losers analysis
- Sector/class/geographic exposure
- Concentration risk indicator
- SimulationEngine extended for portfolio scenarios
- Frontend: Portfolio Intelligence page, Simulations page
- NOTE: Do NOT modify existing /wealth pages

**Tests:** Attribution calculation unit tests, integration tests against test portfolio data

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
