# Testing Strategy — Wealth Intelligence
**Status:** ACTIVE; Phase 10.3 contracts locked by ADRs 019–022
**Date:** 2026-09-16

---

## 1. Testing Philosophy

Every phase ends with:
1. Automated tests passing
2. Build validation (backend starts, frontend builds)
3. API validation (endpoints return correct data)
4. Manual frontend validation
5. Regression validation (existing features not broken)
6. Explicit acceptance checklist sign-off

Browser-based E2E automation is NOT the default validation strategy.

---

## 2. Test Categories

### Unit Tests (backend)
Every calculation service MUST have unit tests with known inputs/outputs.

Priority areas:
- GoalCalculationService: required_contribution, projected_completion, progress_pct
- RetirementProjectionService: compound interest, gap analysis, scenarios
- SimulationEngine: what-if calculations
- PortfolioAttributionService: contribution attribution, exposure calculations
- Financial Health services: cashflow, savings rate, historical/category trends, and anomaly detection
- RebalancingEngine: target vs current deviation, tolerance bands
- Technical indicators: RSI, SMA (verify against manual calculation)
- LLM output validator: schema validation, rejection cases
- Prompt injection sanitizer: detect and remove injection patterns

### Integration Tests (backend)
- Database: CRUD operations for every new domain model
- User isolation: access attempts across users must be rejected (HTTP 403 or 404)
- Market data: yfinance mock (avoid real network calls in CI)
- BCB data: mock HTTP response
- News: mock RSS feed parsing
- LLM: mock LLM provider response (never call real LLM in tests)
- APScheduler: test job registration (not execution)

### Contract Tests (LLM output)
- InsightResponse Pydantic schema: all required fields present
- InsightSection: is_ai_interpretation always True for AI content
- data_references: all cited fields exist in input context
- confidence: valid enum value
- No numerical claims outside expected ranges

### Security Tests
- User isolation: every endpoint tested with wrong user_id
- Prompt injection: test with known injection patterns in news content
- JWT: expired token, invalid token, missing token
- CORS: validate origin rejection (when production CORS configured)
- External data: malformed response handling (404, 500, timeout)

---

## 3. Test Structure [PROPOSED]

```
tests/
├── unit/
│   ├── calculations/
│   │   ├── test_goal_calculation.py
│   │   ├── test_retirement_projection.py
│   │   ├── test_simulation_engine.py
│   │   ├── test_portfolio_attribution.py
│   │   └── test_expense_intelligence.py
│   ├── validators/
│   │   ├── test_llm_output_validator.py
│   │   └── test_prompt_sanitizer.py
│   └── market/
│       └── test_technical_indicators.py
├── integration/
│   ├── test_goals_api.py
│   ├── test_planning_api.py
│   ├── test_portfolio_intelligence_api.py
│   ├── test_market_radar_api.py
│   ├── test_wealth_ai_api.py
│   └── test_user_isolation.py
├── security/
│   ├── test_auth.py
│   ├── test_prompt_injection.py
│   └── test_cors.py
└── fixtures/
    ├── test_portfolio.py
    ├── test_goals.py
    └── mock_providers.py
```

---

## 4. Phase-Specific Test Requirements

### Phase 10.1 — Goals
- Unit: goal progress calculation (current/target)
- Integration: POST/GET/PUT/DELETE /goals with auth
- Security: user isolation
- Manual: create goal in UI, verify display

### Phase 10.2 — Financial Health
- Unit: `HealthFinancialQuery` consolidates eligible `CLASSIFIED` transactions across multiple local accounts; it is not an account-isolation query.
- Unit: `CashflowMetricsService` verifies cashflow, savings equivalence, zero-income `None` rate, supplied-month averages, empty monthly collections, and Decimal precision.
- Unit: `HistoricalFinancialMetricsService` verifies chronological ordering, monthly cashflow contract reuse, explicit zero months, absent-month gap preservation, empty history, Decimal preservation, and duplicate-month rejection.
- Unit: `CategoryExpenseIntelligenceService` verifies certified category totals, exact Decimal shares, deterministic ranking/ties, top category, empty and zero-total inputs, label preservation, and duplicate-category rejection.
- Unit: savings_rate = (income - expenses) / income
- Unit: `FinancialTrendService` verifies that a current partial requested month resolves to the last closed month, a closed requested month remains the target, the comparison is the immediately preceding calendar month, cross-year continuity works, and missing/non-consecutive months return `INSUFFICIENT_DATA` without synthesis.
- Global trend unit coverage: income, expense, net cashflow, and savings-rate `INCREASED`/`DECREASED`/`UNCHANGED`; negative values; exact Decimal absolute and percentage deltas; previous zero produces `percentage_delta = None`; an undefined savings rate produces metric-level `INSUFFICIENT_DATA` rather than an artificial zero.
- Category trend unit coverage: exact-label matching, both-month directions/deltas, `NEW`, `DISAPPEARED`, explicit zero versus absence, previous-zero percentage behavior, deterministic union ordering, gaps, duplicate rejection, and Decimal preservation. Trend `NEW` remains independent of ADR-015 `NEW_EXPENSE`.
- Real-data validation: production Health query/services and an independent read-only SQLite Decimal calculation must reconcile all global metrics and the complete category union for Jul→Aug/2026, plus Dec/2025→Jan/2026 and the insufficient first-month boundary.
- Budget-pressure integration: current top category/share/rank/expense can be composed with its category trend and anomaly status without a new score or qualitative band.
- Stability remains a contract gate: no weighted/composite score may be tested or implemented until the window, statistic, minimum-history, gap, and null policies are explicitly approved.
- Unit: `SpendingAnomalyService` covers ADR-015 boundaries: normal, exactly 1.5x, greater than 1.5x, baseline exactly/below 50, two-of-three versus one-of-three history, NEW_EXPENSE at 99.99/100.00, explicit zero versus absence, multiple categories, exact category matching, empty current, insufficient global baseline, and Decimal precision.
- Integration: authenticated `/api/v1/financial-health/{cashflow,history,categories,anomalies,trends}` endpoints; invalid `reference_month` returns 422, Decimal values serialize as JSON strings, and insufficient baseline/trend comparison returns a valid domain response. Trend coverage includes partial/closed temporal resolution, `NEW`, `DISAPPEARED`, null percentage, and OpenAPI exposure.
- Frontend analytical UI: targeted ESLint, TypeScript `--noEmit`, and production build; verify the monthly chart preserves gaps, the exact-value table matches it, category rank/share presentation follows the API, anomaly facts remain backend-derived, and loading/error/empty states remain functional.
- Integration/stabilization: compare backend response models with frontend types field by field; run Health and general unit baselines, authenticated real-data HTTP smoke, OpenAPI checks, TypeScript, targeted lint, and production build. Rapid month changes must not allow an older response batch to replace the latest selection.
- Final manual QA: verify login/navigation, populated and empty reference months, rapid month switching, complete history versus the six-record chart window, category/anomaly presentation, UTF-8 labels, browser console, desktop usability, Goals smoke, and Wealth Intelligence hub links. Global mobile responsiveness debt remains non-blocking.
- Manual: verify values match known transaction history, responsive behavior, UTF-8 labels, tooltips, and browser console output.

### Phase 10.3 — Planning & Projection
- Contract/read boundary: all three initial-wealth origins, single-origin enforcement, no double counting, source/scope/as-of/update provenance, missing/stale facts, account scope, Goal ownership, and exact Decimal normalization from persisted `Numeric` sources. Prove that Planning bypasses the current Goal float path and never labels MyProfit investment wealth as net worth.
- Time contract: `as_of_date` is period zero; the current partial month has no projection/proration; the next complete calendar month is period one; target dates compare at `YYYY-MM` granularity; horizons accept exactly one selector and enforce 1–1,200 cycles.
- Forward projection: zero initial wealth/contribution/return, positive rates including values above 100%, every supported negative rate above -100%, invalid `<= -100%`, `END_OF_MONTH` contribution timing, cross-year/long horizons, compound monthly conversion, and exact deterministic repeatability.
- Nominal/real matrix: nominal-to-nominal without inflation, nominal-to-real with required one-time Fisher conversion, real-to-real with forbidden inflation, and validation rejection for real-to-nominal. Inflation itself must be finite and `> -1`. Goal integration must require an explicit target value basis.
- Precision: Decimal only; money inputs reject fractional cents; calculation context has at least 34 digits; equivalent monthly rates retain at least 18 decimal places; every monthly projected return uses cent-scale `ROUND_HALF_EVEN`; closing/opening recurrence reconciles exactly; JSON uses strings/null.
- Forward output: every approved period and summary field, assumption echo, provenance, scope/as-of, and conditional-result metadata; no generative narrative and no frontend financial recalculation.
- Target-date solver: `ALREADY_ACHIEVED`, `ACHIEVED`, mathematically proven `UNREACHABLE`, and `NOT_REACHED_WITHIN_HORIZON`. Exhausting 1,200 months alone must not be called unreachable.
- Required-contribution solver: approved states, dynamic upper-bound expansion, cent-discrete monotonic binary search using the Forward Projection Engine as oracle, and the invariant that `C` succeeds while `C - 0.01` fails unless `C = 0`.
- Goal integration: nullable facts, exact eligible/ineligible Goal types, paused/cancelled behavior, the seven approved timing statuses, direct month comparison without thresholds, and user isolation.
- Scenario comparison: editable archetype labels without rates, shared comparison invariants, explicit contribution/return/inflation/initial-wealth differences, exact deltas, null months-saved/lost when either target is not reached, stable ordering, and no mutation of source facts.
- Historical facts: prove portfolio returns, CDI, IPCA, IBOV, dividends, and Health trends never become future assumptions automatically.
- Sustainable contribution capacity: `DEFERRED — CONTRACT NOT APPROVED`; no formula or implementation test until the 10.3.7 contract is separately approved.
- API/lifecycle: authentication, validation boundaries, provenance/as-of, Decimal strings/null, and transient-only scenarios. Persistence tests are prohibited until a later lifecycle/versioning/ownership contract.
- Frontend: TypeScript parity, no financial recalculation, loading/error/empty states, request-race protection, nominal/real/target-basis labels, month-level date language, and clear conditional-projection wording.
- Independent validation: compare production results with a separate Decimal oracle or independently constructed spreadsheet; production code cannot generate its own expected values.
- Regression: Goals, Financial Health, and Investments baselines remain unchanged unless a microprocess explicitly authorizes an integration modification.

### Phase 10.4 — Retirement & Financial Independence (FIRE)
- Unit: FI target = annual_expenses / withdrawal_rate
- Unit: compound growth with monthly contributions
- Unit: gap analysis = FI_target - current_wealth
- Unit: sensitivity: return ±1%, contribution ±10%
- Manual: validate against known retirement calculators

### Phase 10.5 — Portfolio Intelligence
- Unit: portfolio attribution = price_return + dividend_return + contribution_return
- Unit: sector exposure = sector_value / total_portfolio
- Unit: concentration score
- Integration: attribution API with test portfolio
- Manual: verify attribution sums to total portfolio return

### Phase 10.7 — External Data
- Unit: news sanitizer removes injection patterns
- Unit: BCB data parsing
- Integration: BCB mock HTTP
- Integration: news RSS mock
- Security: prompt injection test cases (10+ known patterns)
- Manual: verify external data labels/timestamps appear in UI

### Phase 10.8 — LLM Provider
- Unit: OllamaProvider.complete (mock HTTP)
- Unit: GeminiProvider.complete (mock)
- Unit: InsightResponse schema validation (valid + invalid cases)
- Unit: fallback chain (primary fails → fallback triggered)
- Contract: structured output always conforms to schema
- Security: injection in context → sanitized before LLM
- Manual: run real briefing generation, verify content quality

### Phase 10.9 — AI Briefing
- Unit: WealthContextBuilder produces valid context
- Unit: BriefingService generates valid InsightResponse
- Integration: briefing endpoint with mocked LLM
- Integration: APScheduler job registration
- Manual: full briefing generation, verify AI labels present
- Manual: verify historical briefings list

---

## 5. Manual Validation Checklist Template (per phase)

```
Phase: [X.Y]
Date: [YYYY-MM-DD]

[ ] Backend starts without errors
[ ] Frontend builds without errors (npm run build)
[ ] All new automated tests pass
[ ] Existing tests still pass (regression)
[ ] API endpoints return correct data (checked via browser/curl)
[ ] Frontend displays data correctly
[ ] Loading states visible during data fetch
[ ] Error states graceful (no blank screens)
[ ] Empty states show actionable message
[ ] User isolation verified (cannot see other user's data)
[ ] Mobile layout acceptable (basic check)
[ ] No console errors in browser
[ ] [Phase-specific items]

Sign-off: [ ] APPROVED to close phase
```
