# Changelog — FINANALYTICS Wealth Intelligence

---

## [TSK-10.3.0-A] — 2026-09-16 — Planning Contract Approval and ADR Lock

### Approved
- Added ADR-019 through ADR-022 for the Planning input/source boundary, the shared monthly mathematical contract, scenario semantics/lifecycle, and the combined Retirement/FIRE plus Portfolio Intelligence phase boundaries.
- Locked explicit initial-wealth origins, no-double-counting/provenance rules, the Goals Decimal read boundary, four independent contribution concepts, `END_OF_MONTH` timing, partial-month period zero, effective-annual Decimal rates with no arbitrary positive cap, compound monthly conversion, negative-return support, and the nominal/real/inflation validation matrix.
- Locked the 1–1,200-month horizon, month-level target dates, 34-digit Decimal context, monthly cent-scale `ROUND_HALF_EVEN` recurrence, forward output/equation, target-date states, and cent-discrete required-contribution solver using the Forward Projection Engine as its only production oracle.
- Locked editable `CONSERVATIVE`/`BASE`/`OPTIMISTIC` labels without rates, historical-data-not-forecast, transient-first scenarios, Goal timing/eligibility, and null months-saved/lost when temporal comparison is not applicable.

### Deferred / Boundaries
- `sustainable_monthly_contribution_capacity` remains `DEFERRED — CONTRACT NOT APPROVED` in 10.3.7; Planning MVP uses explicit `scenario_monthly_contribution`.
- Phase 10.4 is now canonically `Retirement & Financial Independence (FIRE)` and reuses 10.3 engines. Phase 10.5 remains Portfolio Intelligence. Both are boundary definitions only; neither was implemented.

### Status
- `10.3.0 = VALIDATED`.
- `10.3.1 — Planning Read Foundation = READY / NOT STARTED`.
- Documentation only. No production code, schema, migration, DTO, service, engine, endpoint, UI, database data, Retirement/FIRE, or Portfolio Intelligence implementation changed.

---

## [TSK-TRANSITION-10.2-TO-10.3] — 2026-09-16 — Post-Merge Checkpoint and Planning Decomposition

### Verified
- GitHub PR #2 merged `develop` into `main` at `b7ce8b8`; approved Goals/Health commit `2006e0f` is an ancestor of the merge.
- Local and remote `main`/`develop` were fast-forwarded to the same post-merge checkpoint without rebase, reset, or a new local merge commit.
- Phase 10.2 is `COMPLETED / MERGED`; 10.2.10-C remains `VALIDATED`.

### Planned
- Phase 10.3 is `PLANNED / NOT STARTED`, decomposed into microprocesses 10.3.0–10.3.12 in `IMPLEMENTATION_ROADMAP.md`.
- Planning remains deterministic and contract-first. It separates realized surplus, sustainable contribution capacity, and user-defined scenario contribution; keeps FIRE in 10.4 and portfolio recommendations in 10.5; and requires Decimal-safe read inputs before any engine.
- Scenario delivery is staged: transient comparisons first, persistence only after an approved lifecycle/data contract.

### Scope
- Documentation only. No Planning code, schema, migration, DTO, endpoint, frontend, calculation, or scenario engine was implemented.

---

## [PHASE-10.2-CLOSE] — 2026-09-15 — Financial Health Phase Closure

### Reviewed
- Independent release review verdict: `PASS WITH NON-BLOCKING NOTES`; no blockers, no HIGH findings, and LOW release risk.

### Fixed
- Corrected M-01 so trend periods read chronologically from `comparison_month` to `trend_target_month` (for example, `jul/26 → ago/26`) without changing backend semantics or calculations.

### Validated
- Health suite: `68 passed`. General baseline: `118 passed, 2 failed`, limited to the two historical Investments timeline/MagicMock tests. TypeScript, Health-targeted ESLint, production build, and Git whitespace validation pass.

### Status
- 10.2.10-C is `VALIDATED`; Phase 10.2 Financial Health is `COMPLETED`; Phase 10.3 Planning & Projection is `NOT STARTED / NEXT`.
- Sustainable contribution capacity, investment capacity, and composite financial stability remain formally deferred to their approved future boundaries.

---

## [10.2.10-C-UX2] — 2026-09-15 — Financial Health Visual Identity

### Improved
- Added an exact-label deterministic Health category accent resolver backed by a controlled ten-color muted palette. Category dots/bars and category-trend card accents now retain the same identity independently of rank, month, value, or trend state.
- Added restrained metric identity to income, expense, net-cashflow, and savings-rate KPI cards. Historical rows now use subtle zebra striping and metric-consistent text accents, with sign-sensitive net-cashflow and savings-rate values.
- Strengthened category-trend numeric hierarchy: current values remain primary, while absolute and relative deltas use mathematical increase/decrease/neutral presentation colors independently from category and status accents.

### Validated
- TypeScript, targeted Health ESLint, and the Next.js production build pass. Backend, financial contracts, pagination, trend ordering, and anomaly semantics remain unchanged.

### Status
- 10.2.10-C remains `IMPLEMENTED / READY FOR FINAL VISUAL VALIDATION`. Phase 10.2 remains open.

---

## [10.2.10-C-UX] — 2026-09-15 — Financial Health Visual Information Design Polish

### Improved
- Consolidated requested/comparison months into one compact temporal context and replaced repeated card sentences with visual trend badges, signed deltas, and presentation-only semantic color.
- Added client-side history pagination at 12 chronological rows per page, opening on the latest records and resetting when the selected reference month changes; the chart remains limited to the latest six returned records.
- Redesigned category trends into compact, responsive cards with status badges, clearer numeric hierarchy, six-item initial disclosure, and full ordered detail on demand. Removed implementation-language microcopy from the user interface.

### Validated
- TypeScript, targeted Health ESLint, and the Next.js production build pass. Backend, API contracts, financial calculations, and stability scope were untouched.

### Status
- 10.2.10-C is `IMPLEMENTED / READY FOR FINAL VISUAL VALIDATION`. Phase 10.2 remains open.

---

## [10.2.10-C] — 2026-09-15 — Trend API/UI Exposure

### Added
- Authenticated `GET /api/v1/financial-health/trends?reference_month=YYYY-MM` with shared reference-month validation, an explicit API-boundary current-month resolver, certified Health history/category orchestration, and ADR-018 DTO-to-HTTP serialization.
- Typed Health frontend trend contract and a fifth request inside the existing race-protected batch. Summary cards label the closed comparison period and present savings-rate absolute change in percentage points; an expandable secondary panel presents the complete certified category order without mixing it with partial requested-month category values.
- Eight API tests covering auth, partial/closed month resolution, JSON Decimal strings/null, `NEW`, `DISAPPEARED`, null percentage, insufficient data, invalid input, and OpenAPI presence.

### Validated
- Authenticated real-ledger API response for Sep/2026 returned `2026-08` versus `2026-07`, all four validated global facts, and the complete 24-item category union.
- Health suite: `68 passed`; TypeScript, targeted Health lint, and production build pass. General unit baseline remains `118 passed, 2 failed`, exclusively the known Investments MagicMock/timeline failures.

### Status
- 10.2.10-C is `IMPLEMENTED / READY FOR USER VALIDATION`. Stability remains `NOT IMPLEMENTED — CONTRACT PENDING`; Phase 10.2 remains open.

---

## [10.2.10-B-V] — 2026-09-15 — Independent Trend Engine Validation

### Validated
- ADR-018 compliance and engine purity: `FinancialTrendService` consumes only certified DTO facts, retains `Decimal`, and has no database, transaction, RAW, Pierre, Investments, anomaly, narrative, API, or UI dependency.
- A separate read-only SQLite plus Python `Decimal` oracle reconciled all four Jul→Aug/2026 global facts and all 24 categories in the exact-label union. Cross-year Dec/2025→Jan/2026, partial-month resolution, insufficient first month, gap, negative, zero, unchanged, undefined-rate, invalid-input, and duplicate-input behavior also passed.
- Health suite: `60 passed`. General unit baseline: `118 passed, 2 failed`; both failures remain the documented Investments MagicMock/timeline failures and no new regression occurred.

### Status
- 10.2.10-B is `VALIDATED`; 10.2.10-C is `NOT STARTED / NEXT`. API/UI trend exposure remains unimplemented and stability remains `NOT IMPLEMENTED — CONTRACT PENDING`. Phase 10.2 remains open.

---

## [10.2.10-B] — 2026-09-14 — Deterministic Global and Category Trend Engine

### Added
- `FinancialTrendService` with typed global/category summaries, metric and direction enums, exact Decimal deltas, explicit current-month resolution, strict consecutive-month lookup, and non-exceptional `INSUFFICIENT_DATA` results.
- Exact-label category union with deterministic target-first ordering, `NEW`/`DISAPPEARED` presence semantics, and explicit-zero preservation. ADR-015 anomaly types and thresholds remain independent and unchanged.
- `test_financial_trend_service.py` with 13 tests covering the 22 required temporal, global, category, and precision behaviors.

### Validated
- Full Health suite: `60 passed`. General unit baseline: `118 passed, 2 failed`, with only the two known Investments MagicMock/timeline failures.
- Read-only production-query versus independent SQLite Decimal validation passed for all four Jul→Aug global metrics, all 24 categories in the union, Dec/2025→Jan/2026 continuity, missing 2025-04, and Decimal types.

### Status
- 10.2.10-B is `IMPLEMENTED / READY FOR VALIDATION`. API/UI exposure is not implemented. Stability remains `NOT IMPLEMENTED — CONTRACT PENDING`.

---

## [10.2.10-A] — 2026-09-14 — Financial Trend and Stability Readiness Contract Lock

### Audited
- A read-only audit of `database/fin_analytics.db` found 1,420 transactions: 1,420 `CLASSIFIED`, 0 `PENDING`, 341 `ENTRADA`, 898 `SAIDA`, and 181 `IGNORAR`.
- The current governed ledger covers 17 consecutive calendar months from `2025-05` through partial `2026-09`, including 16 continuous closed months through `2026-08`. Earlier reports based on partial governance remain historical evidence and are not current baselines.

### Approved
- ADR-018 locks consecutive closed-month global trends for income, expense, net cashflow, and savings rate; exact-label category trends; factual budget-pressure composition; and Decimal/absence semantics.
- `savings_amount` remains realized surplus/deficit. Sustainable contribution capacity is deferred to Planning, and investment capacity to Planning/Portfolio Intelligence.
- The ledger is ready for a simple deterministic stability-facts contract, but no formula, weighting, or composite score is approved. The executable stability contract remains a gate for 10.2.10-C.

### Status
- 10.2.10-A is `VALIDATED`; 10.2.10-B Deterministic Global & Category Trend Engine is `NOT STARTED / NEXT`. Phase 10.2 and final QA remain open.
- Documentation only; backend, frontend, tests, schema, migrations, and database data were not changed.

---

## [10.2.10-PREP] — 2026-09-14 — Final Manual Validation / Visual QA Preparation

### Closed
- 10.2.9 integration and stabilization is `VALIDATED`: backend and frontend contracts, Decimal handling, data freshness, navigation, race-condition protection, automated suites, build, HTTP smoke, and OpenAPI checks passed without a Financial Health blocker.

### Prepared
- 10.2.10 is `IN PROGRESS / READY FOR USER FINAL QA`. The final manual checklist covers navigation, populated and empty months, rapid month switching, analytical sections, UTF-8, console behavior, desktop usability, Goals smoke, and the Wealth Intelligence hub.
- Phase 10.2 remains open until explicit user sign-off. No feature, financial rule, backend contract, schema, or database data changed during this preparation.

### Accepted Non-Blocking Debt
- Global mobile responsiveness, repository-wide lint debt, the Recharts SSR dimension warning, the ADR-014 Alembic FK mismatch, and the two historical Investments test failures remain unchanged.

---

## [10.2.9] — 2026-09-14 — Financial Health Integration and Stabilization

### Stabilized
- Audited the complete governed-data-to-UI chain and confirmed backend response models match frontend TypeScript contracts, Decimal strings remain presentation-only in the browser, navigation/auth are shared, and live Health requests bypass frontend caching.
- Added request sequencing to the Financial Health page so rapid month changes cannot let an obsolete four-endpoint response batch overwrite the latest selection. Removed the now-unused Health panel description path created during the UI phase.

### Validated
- 47 Health tests passed. The general unit suite retained exactly the two historical Investments MagicMock/timeline failures (`118 passed, 2 failed`). TypeScript, targeted Health lint, production build, real-data HTTP smoke, application startup through TestClient, and all four OpenAPI routes passed.
- September/2026 current-ledger smoke returned six historical records, 11 categories, and the certified `SPIKE` signals `Transferências` and `Serviços`; financial amounts remain live and are not hardcoded.

### Technical Debt
- Global mobile responsiveness, repository-wide lint debt, the Recharts SSR dimension warning, the ADR-014 Alembic FK mismatch, and the two historical Investments test failures remain non-blocking and unchanged.

### Next
- 10.2.9 is `VALIDATED`; 10.2.10 is `IN PROGRESS / READY FOR USER FINAL QA`.

---

## [10.2.8] — 2026-09-14 — Financial Health Analytical UI

### Added
- Responsive analytical summary cards with API-provided recent averages, a Recharts monthly cashflow view plus exact-value table, proportional category ranking, and explainable anomaly cards with secondary non-anomaly states.
- Layout-specific skeletons and refined error, empty-data, and insufficient-baseline presentation with basic semantic and keyboard accessibility.

### Validated
- Targeted ESLint, TypeScript typecheck, and the production Next.js build pass. Financial values and classifications remain API-derived; the client performs presentation formatting only.

### UI Polish and Manual Validation
- 10.2.8-A limited the chart to the latest six returned records while retaining the full history table, corrected anomaly-card and long-label reflow, restored the Health TopNav color marker, and aligned the Wealth Intelligence hub card icon. No backend contract changed.
- Manual browser validation passed for populated and empty months, history windows, anomaly cards, labels, navigation, and console behavior. 10.2.8 is `VALIDATED`; integration/stabilization 10.2.9 remains NOT STARTED / NEXT.

---

## [10.2.7] — 2026-09-14 — Financial Health Frontend Foundation

### Validated
- Manual browser validation with the real backend and frontend confirmed authentication, reference-month selection, cashflow, history, category ranking, anomaly signals, UTF-8 labels, consolidated scope, and Wealth Intelligence navigation.

---

## [10.2.6] — 2026-09-13 — Financial Health API

### Added
- Authenticated read-only endpoints under `/api/v1/financial-health`: `cashflow`, `history`, `categories`, and `anomalies`, all requiring `reference_month=YYYY-MM` and deliberately exposing no account filter.
- Typed response schemas that preserve domain `Decimal` values as JSON strings and domain `None` as JSON `null`.

### Validated
- HTTP tests cover authentication, query validation, cashflow, chronological history/gaps, categories, anomalies, insufficient baseline, and Decimal serialization.
- Manual authenticated validation confirmed all four endpoints, 401 without credentials, and 422 for an invalid `reference_month`.
- Live reconciliation confirmed that the API, `HealthFinancialQuery`, and independent SQLite Decimal aggregation agree against the current ledger. September/2026 values may legitimately change as transactions are classified; no financial values are hardcoded. UTF-8 JSON labels and the historical response schema were also verified.

### Deferred / Out of Scope
- Frontend, persistence, alerts, new calculations, and account-level filters remain out of scope.

---

## [10.2.5] — 2026-09-12 — Spending Anomaly Engine

### Added
- `SpendingAnomalyService` plus typed month input, evaluation, summary, category-state, and global-status contracts, all operating only on certified pre-consolidated category data.
- Deterministic ADR-015 handling for continuous three-month baseline availability, exact category matching, two-of-three historical presence, present-value arithmetic means, inclusive R$50 baseline floor, strict 1.5x SPIKE threshold, and inclusive R$100 NEW_EXPENSE threshold.

### Validated
- Unit coverage for all approved boundaries, explicit-zero semantics, missing/non-continuous baseline, Decimal preservation, and anomaly collection filtering.
- Independent read-only September/2026 comparison against June-August/2026 category aggregates. `Transferências` and `Serviços` were the only `SPIKE` signals; no `NEW_EXPENSE` was produced.
- Independent validation closed 10.2.5 as `VALIDATED`; the Health suite passed 39 tests and the unit suite retained only the two historical Investments mock/timeline failures.

### Deferred / Out of Scope
- API, persistence, alerts, severity, trends, forecasts, category normalization, and AI remain out of scope.

---

## [10.2.5-PRE] — 2026-09-12 — Anomaly Contract Lock

### Governance
- Closed 10.2.4 as VALIDATED after independent real-data validation of September/2026 category totals, ranking, shares, Decimal precision, zero/empty behavior, duplicate rejection, and label preservation.
- ADR-015 is APPROVED. It locks the three-month continuous closed baseline, category presence semantics, two-of-three history rule, mean reference over present certified values, inclusive R$50 baseline floor, strict 1.5x SPIKE operator, and inclusive R$100 NEW_EXPENSE threshold.
- At this preparatory point, 10.2.5 remained NOT STARTED / NEXT and no anomaly implementation had been added.

---

## [10.2.4] — 2026-09-12 — Category Expense Intelligence

### Added
- `CategoryExpenseIntelligenceService` plus typed certified input, ranked category metric, and summary DTOs.
- Deterministic total, analytical share, sequential ranking, lexicographic tie-break, and top-category behavior without label normalization.

### Contract
- Empty input returns total `Decimal('0.00')`, no categories, and no top category; explicit zero categories remain ranked records with `None` shares.
- Duplicate category input fails fast with `ValueError`; concentration measures, historical comparisons, normalization, and anomalies remain deferred.

### Validated
- Read-only September/2026 validation found 10 certified expense categories totaling `4486.90`; independent SQL Decimal aggregation reproduced the category totals, ranking, shares, and top category.

---

## [10.2.3] — 2026-09-12 — Historical Financial Metrics

### Added
- `HistoricalFinancialMetricsService`, `MonthlyCashflowPeriodDTO`, and `MonthlyFinancialMetricsDTO` for a deterministic chronological series built from certified monthly totals.
- Coverage for ordering, monthly cashflow reuse, deficits, zero income, explicit zero months, empty history, gaps, Decimal preservation, and duplicate-month rejection.

### Contract
- The service does not query the database and never synthesizes absent months; `2025-06` to `2026-06` remains a gap in real data.
- Duplicate `reference_month` input fails fast with `ValueError`; monthly totals must already be consolidated by `HealthFinancialQuery`.
- At that implementation point, month-over-month comparisons, rolling averages, trends, and insufficient-data classification were deferred because their formal contracts were absent. ADR-018 later superseded that contract gap for deterministic month-over-month trends; rolling averages remain outside the locked scope.

### Validated
- Read-only database validation produced six real months in chronological order: `2025-05`, `2025-06`, `2026-06`, `2026-07`, `2026-08`, and `2026-09`.
- Independent validation also confirmed chronological ordering, gap preservation, absent-versus-zero behavior, duplicate rejection, Decimal precision, mathematical invariants, and regression baseline.

---

## [10.2.2-A] — 2026-09-12 — Financial Decimal Precision Correction

### Fixed
- SQLite returns `SUM(ABS(transactions.amount))` as a binary `float` despite the persisted `NUMERIC(12,2)` amount scale. `HealthFinancialQuery` now normalizes all monetary aggregates (`get_cashflow`, `get_monthly_totals`, and `get_category_expenses`) once at the read boundary to cent-scale `Decimal` values.
- Added regression coverage for the SQLite `0.10 + 0.20` aggregate artifact, including exact `Decimal` type assertions for cashflow, monthly, and category outputs.

### Validated
- Independent read-only real-data validation reproduces the certified September/2026 totals and June-August/2026 baseline exactly in `Decimal`; the corrected baseline averages are income `10775.61`, expense `6285.22`, and net cashflow `4490.39`.
- Savings rate remains an unrounded analytical fraction; no presentation rounding was added.

---

## [10.2.2] — 2026-09-12 — Cashflow Metrics Engine

### Added
- `CashflowMetricsService` and typed `CashflowSummaryDTO` / `MonthlyCashflowDTO` for deterministic certified cashflow metrics.
- Decimal-based total, net cashflow, savings, savings-rate, and supplied-month average calculations.
- Unit coverage for positive, deficit, zero-income, zero-value, equal-value, single/multiple-month, empty-month collection, and Decimal precision cases.

### Contract
- `savings_amount = net_cashflow`.
- `savings_rate = None` when income is zero.
- At that implementation point, expense trend was deferred because no formal trend contract existed. ADR-018 later superseded this limitation.
- 10.2.3 remains NOT STARTED / NEXT.

---

## [10.2.1-A] — 2026-09-12 — Financial Health Contract & Documentation Stabilization

### Validated
- Financial Health uses consolidated account scope for the local single-tenant database.
- Operational baseline: three continuous closed months before the analysed month; for September/2026, June through August.
- September/2026 SQL validation: income 2203.90, expenses 4486.90, and 10 `CLASSIFIED` `SAIDA` categories.
- `HealthFinancialQuery` read foundation and its multi-account consolidation test.

### Status Alignment
- Phase 10.1 Goals: IMPLEMENTED / VALIDATED.
- Phase 10.2.0: COMPLETED.
- Phase 10.2.1: IMPLEMENTED / VALIDATED.
- Phase 10.2.2: NOT STARTED / NEXT.

### Scope Protection
- No production Financial Health logic, schema, migrations, API, frontend, Goals, Investments, Pierre, or database data changed.
- Worktree remains intentionally uncommitted pending human validation.

---

## [10.0.0] — 2026-09-08 — Architecture & Product Design

### Added — Documentation (project/wealth-intelligence/)
- `README.md` — project overview, stack, getting started, phase index
- `MASTER_PLAN.md` — vision, phase roadmap, pre-work blockers, decision index
- `CURRENT_STATE.md` — verified reality of repository (post full audit)
- `ARCHITECTURE.md` — current + target architecture, 8-layer data pipeline model
- `AI_AND_LLM.md` — LLM provider design, Ollama evaluation, prompt safety, multi-agent analysis
- `DATA_AND_SOURCE_OF_TRUTH.md` — source of truth matrix, data authority rules
- `DECISION_LOG.md` — 13 Architecture Decision Records (ADRs 001-013)
- `IMPLEMENTATION_ROADMAP.md` — phase contracts (10.1–10.12), scope, tests, acceptance criteria
- `UI_UX_PLAN.md` — 11-page module designs, navigation architecture, design system
- `SECURITY_AND_GOVERNANCE.md` — prompt injection defense, financial data security, AI governance
- `INFRASTRUCTURE.md` — Docker strategy, Ollama native host rationale, deployment options
- `TESTING_STRATEGY.md` — test categories, structure, per-phase requirements, validation checklist
- `CHANGELOG.md` — this file
- `audits/REPOSITORY_AUDIT.md` — full verified backend, DB, frontend, AI infrastructure audit
- `audits/EXTERNAL_DATA_ECOSYSTEM.md` — external data source research and decisions
- `audits/ENV_VARIABLE_INVENTORY.md` — current + proposed env variable inventory
- `audits/DEPENDENCY_ROADMAP.md` — dependency installation plan per phase
- `audits/FINAL_PRODUCT_DEFINITION.md` — product vision and user experience narrative

### Discovered — Critical Issues
- **BLOCKER:** Dual `position_snapshots` schema (migration 013 vs ORM PositionSnapshotModel) must be resolved before Phase 10.1
- **P2:** `requirements.txt` is incomplete (missing pydantic-settings, aiosqlite, python-jose, passlib)
- **P2:** `GEMINI_API_KEY` integration files are empty (0 bytes) — database scaffold only

### Verified — Repository Baseline
- 9 active FastAPI routers (investments, dashboard, Pierre, governance, goals, auth, accounts, transactions, governance API)
- 17 database migrations applied to SQLite WAL database
- YFinanceProvider fully implemented with MarketDataProvider Protocol abstraction
- Pierre Finance + MyProfit CSV import pipelines fully operational
- Next.js frontend with complete /wealth module (5 sub-pages)
- Goals domain: basic CRUD only, missing critical fields for Wealth Intelligence
- AI infrastructure: database schema only, all integration files empty

### No Code Changed
This phase is documentation-only. No backend, frontend, or database changes were made.

---

## [3.1.0-investments] — Previous Baseline

Prior version. Stable investments module. Pierre Finance + MyProfit integration operational. Goals stub introduced. AI prompt versioning DB scaffold added.
