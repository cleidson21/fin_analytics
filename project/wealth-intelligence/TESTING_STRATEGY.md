# Testing Strategy — Wealth Intelligence
**Status:** ACTIVE; 10.R2 implemented, validated, independently approved, and closed;
10.R3-B contract approved/locked; R3-B.2 approved/locked/versioned; R3-C
implemented/validated/independently approved/closed; R3-D.1 contract
approved/independently verified/locked/versioned; R3-D closed/pushed; R3-E.0
contract approved/independently verified/locked/versioned/pushed; R3-E1
closed/pushed; R3-E2 closed/pushed;
R3-E3 implemented/tested/independently approved/ready for checkpoint; R3-E4 ready/not started;
10.5-B paused pending R7
**Date:** 2026-10-13

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

Validation must test repository reality, contracts, and independent oracles;
status prose is never sufficient evidence. For documentation-only locks, verify
canonical ownership, link/path validity, current-vs-future labeling, scope of
the diff, and an empty Git index. Do not run production test suites merely to
create noise when no code or contract behavior changed.

Current B7 validation proves that the typed Home, Planning, Goal, and FIRE
consumer foundations delegate once to B5 with explicit authenticated owner and
`as_of_date`, preserve immutable Smart Values, do not resolve required
assumptions, and do not alter public APIs or engines. Evidence: `31` B5+B7
focused tests, `153` B1–B7 Smart Context tests, `497` Planning regressions, `67`
FIRE regressions, `133` Goals/Health regressions, and the complete backend unit
result `835 passed, 2` unchanged historical Investments failures.

MR2 validates schema-authority and test-isolation boundaries. Seven focused
tests prove canonical sync/async URL derivation, configured-engine targeting,
fresh-process `backend.main` import with no DDL, unchanged behind-head schema,
and fail-closed refusal of the active database by pytest. Smart Context plus
MR2 passed `160`; Planning/FIRE passed `564`; Goals/Health passed `133`; complete
units passed `842` with only the same two historical Investments failures.
Copy-only testing reproduced the former drift setup without automatic table
creation and passed stamp, no-op upgrade, downgrade/re-upgrade, and Smart
Context FK checks. Independent MR2 review reported zero blocking and zero
material findings. MR3 then reconciled the active Alembic revision to
`2d6b4f8a9c1e`, verified `upgrade head` as a no-op, preserved the physical
schema and financial row counts, and returned `integrity_check = ok`. Its
post-operation isolated regression returned `19 passed`; validated pre/post
backups remain retained. B8 evidence remains `153` Smart Context, `497`
Planning, `67` FIRE, `133` Goals/Health, and `121` frontend tests, with
compatible OpenAPI and only the two unchanged historical Investments failures.

---

## 2. Test Categories

### Unit Tests (backend)
Every calculation service MUST have unit tests with known inputs/outputs.

Priority areas:
- Financial Health services: cashflow, savings rate, history, category trends,
  and anomaly rules.
- Planning engines: projection, target achievement, required contribution, Goal
  orchestration, and scenario comparison.
- FIRE summary and composition over the certified Planning solvers.
- Future Smart/External Context, Portfolio Intelligence, and AI services only
  after their phase contracts approve exact behavior.

### Integration Tests (backend)
- Database: persistence and read behavior only where an approved contract adds
  or consumes a model.
- Ownership: wrong-user, ambiguous-scope, and non-enumeration behavior according
  to the domain contract.
- Market data: yfinance mock (avoid real network calls in CI)
- Future external providers: mock HTTP/provider responses after R3 approval.
- Future LLM: mock provider/tool responses; never require paid/live AI in the
  default suite.

### Contract tests
- Exact request/response DTO parity, strict Decimal strings, enums, dates,
  nullability, provenance, and error/status semantics.
- Future AI structured-output/tool schemas only after R4 locks them; verify that
  financial numbers originate in tool results, not model arithmetic.

### Security Tests
- Ownership/isolation: every new or changed endpoint tested against its explicit
  authenticated scope, including wrong-user and ambiguity cases where relevant
- Prompt injection: test with known injection patterns in news content
- JWT: expired token, invalid token, missing token
- CORS: validate origin rejection (when production CORS configured)
- External data: malformed response handling (404, 500, timeout)

---

## 3. Historical test-structure proposal

The original 10.0 tree below is preserved as planning input only. Actual test
paths in the repository and each accepted phase contract take precedence; do
not create placeholder suites merely to match this sketch.

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
- **10.3.1 implemented coverage:** all three initial-wealth origin identities; separate Goal and portfolio facts; no aggregate output; source/scope/as-of/update provenance; missing facts; explicit portfolio account scope; two-account isolation; Goal ownership; `NULL` versus explicit zero; exact `Decimal("0.10")` regression; read-only SQL; and proof that snapshot reads do not query positions/valuations.
- **Health reuse coverage:** Planning calls `HealthFinancialQuery` and `HistoricalFinancialMetricsService`, preserves Decimal income/expense/net cashflow/realized `savings_amount`, preserves missing-month gaps, and returns an empty collection when no certified month exists.
- **10.3.1 independently validated (2026-09-16):** Planning `12 passed`; Goals regression `65 passed`; Health regression `68 passed`; general `tests/unit` baseline `130 passed, 2 failed`, limited to the same historical Investments timeline/MagicMock failures. Controlled oracles proved ownership, `NULL`/zero, exact Decimal and multi-account isolation; SQLite `mode=ro` reads matched Goal, portfolio, and closed-month Health facts; captured reader statements were only `SELECT` and sessions remained unmodified.
- **10.3.2 implemented coverage (2026-09-17):** assumptions `63 passed`, covering frozen contracts, strict Decimal/no-float inputs, contribution cent scale, finite return/inflation domains above `-1` with no positive cap, every nominal/real matrix branch, exact horizon exclusivity and bounds, target-month day equivalence, December/January resolution, strict enum inputs, and absence of projection outputs or initial wealth. Regressions: Planning Read `12 passed`, Goals `65 passed`, Health `68 passed`, and general `tests/unit` `193 passed, 2 failed`; only the identical historical Investments timeline/MagicMock failures remain.
- **10.3.2 independently validated (2026-09-17):** code audit plus an external in-memory oracle challenged strict date/money/rate/enum types, `Decimal("1.000")` scale behavior, rates through `Decimal("100")`, extended rate precision, matrix A–H, current/past target months, cross-year and leap-year resolution, and exact 1,200/1,201 boundaries. No production or test code changed. The focused and general regressions reproduced the implementation baseline exactly.
- **10.3.3 implemented coverage (2026-09-17):** projection `34 passed` using hardcoded 100-digit positive/negative/Fisher monthly-rate oracles plus an independent test-local cent recurrence. Coverage includes zero/positive/negative/extreme rates, one-time Fisher, zero nominal with positive inflation, deflation, `END_OF_MONTH`, `ROUND_HALF_EVEN` ties, cent recurrence/invariants, immutable results, all approved sources/provenance, period zero and real month ends, leap year, target-date horizon reuse, 1/12/1,200 periods, isolated Decimal context, and invalid initial wealth. Regressions: assumptions `63 passed`, Planning Read `12 passed`, Goals `65 passed`, Health `68 passed`, and general `tests/unit` `227 passed, 2 failed`; only the identical historical Investments timeline/MagicMock failures remain.
- **10.3.3-R numerical reconciliation (2026-09-17):** projection `38 passed`. Fixed 80-digit precision was replaced by a local precision budget derived from initial/contribution magnitude, annual growth-factor order, and horizon, with cent scale plus 34 guard digits. The original annual-rate `100` / 1,200-month blocker now completes with a 204-integer-digit final balance and matches an independent 500-digit Newton/cent oracle at every period, including checkpoints 1, 12, 120, 451, 452, 600, and 1,200. Added coverage also proves magnitude-sensitive precision, exact equal-return/inflation zero, determinism, cent scale, accounting invariants, and unchanged global Decimal context. Regressions: assumptions `63 passed`, Planning Read `12 passed`, Goals `65 passed`, Health `68 passed`, and general `tests/unit` `231 passed, 2 failed`; only the identical historical Investments timeline/MagicMock failures remain.
- **10.3.3-V2 independent numerical revalidation (2026-09-17):** independently derived and exercised the magnitude budget without production oracles. An 800-digit Newton/monthly recurrence matched exact money for all 1,200 blocker periods, including 439/440, plus 120-digit initial wealth, dominating contribution, combined large initial/contribution, rates 2.5/10/25/100, large Fisher and real/real cases, deflation, and negative rates near -1. Precision was monotonic across initial wealth, contribution, horizon, and growth-factor axes. Mutation-style probes proved rate precision fixed at 80 diverges at period 440 even with adaptive money, while adaptive rate with 80-digit money fails at 452. No V2 test or production change was needed. Focused and general regression counts remain `38`, `63`, `12`, `65`, `68`, and `231 passed, 2 historical failures` respectively.
- **10.3.4-A implemented coverage (2026-09-17):** target solver `32 passed`, covering strict positive finite cent-scale Decimal targets, period-zero `ALREADY_ACHIEVED`, exact/overshoot first crossings, positive and negative returns, zero-contribution growth, conservative `UNREACHABLE` proofs, growing paths beyond 1/3/1,200-month horizons, target-date period-end reuse, nominal-to-real output-basis comparison, more-than-200-digit targets, all three source identities, one engine call, immutability, determinism, and no silent coercion. Regressions: projection `38 passed`, assumptions `63 passed`, Planning Read `12 passed`, Goals `65 passed`, Health `68 passed`, and general `tests/unit` `263 passed, 2 failed`; only the identical historical Investments timeline/MagicMock failures remain.
- **10.3.4-A independently validated (2026-09-17):** external probes challenged the full target type/scale domain, including rejection of literal three-decimal `Decimal("1.000")`, engine call counts 0/1, period-zero and first-crossing consistency, exact/overshoot/positive/negative cases, all three mathematical non-achievement families, horizons 1/1,200, nominal/real output bases without target conversion, 221-digit money, all source identities/provenance, frozen results/inputs, and determinism. Source audit found no duplicated financial/calendar math, persistence, Goal/scenario, or required-contribution implementation. No production or test change was required. Focused and general counts remain `32`, `38`, `63`, `12`, `65`, `68`, and `263 passed, 2 historical failures` respectively.
- **10.3.4-B implemented coverage (2026-09-17):** required-contribution solver `40 passed`, covering `ALREADY_ACHIEVED`, `ZERO_CONTRIBUTION_REQUIRED`, strict target reuse, template-contribution independence, integer-cent binary search, explicit `C`/`C - 0.01` minimality, deterministic monotonic grids across positive/zero/negative/near-`-1` returns, `END_OF_MONTH`, `ROUND_HALF_EVEN`, target-date horizons, nominal-to-real and real-to-real output bases, all source identities, more-than-80-digit money, logarithmic oracle calls, immutability, and determinism. `IMPOSSIBLE_HORIZON` and `OUT_OF_SUPPORTED_RANGE` remain approved result identities but are not emitted for the current valid mathematical domain. Regressions: Target Solver `32 passed`, Projection `38 passed`, Assumptions `63 passed`, Planning Read `12 passed`, Goals `65 passed`, Health `68 passed`, and general `tests/unit` `303 passed, 2 failed`; only the identical historical Investments timeline/MagicMock failures remain.
- **10.3.4-B independently validated (2026-09-17):** code audit found only exact Decimal/integer-cent conversion and binary-search orchestration over the Target Solver/Forward Engine chain. Independent probes covered 90 small-domain combinations and 7,128 cent candidates, negative `ROUND_HALF_EVEN` ties, near-`-1` behavior, 3,507 pre-contribution nonnegativity cases, six cross-mode upper-bound cases, three template contributions, strict targets, all sources and output modes, 101-digit negative-rate money against a 500-digit recurrence, and logarithmic call scaling of 18/24/30. Exact oracles proved the target upper bound and `C` succeeds while `C - 0.01` fails. No production or test change was required. Focused/general counts remain Required `40`, Target `32`, Projection `38`, Assumptions `63`, Planning Read `12`, Goals `65`, Health `68`, and `303 passed, 2 historical failures` respectively.
- **10.3.5-V3 final independent validation (2026-09-19):** Validated the R2-SOL correction through separate controlled probes and the complete regression set. ACTIVE-only eligibility is a positive whitelist; non-projectable lifecycle/type paths return `NOT_APPLICABLE` before basis, provenance, or deadline validation and with zero solver calls. ACTIVE remains strict, lifecycle `ACHIEVED` remains distinct from mathematical `ALREADY_ACHIEVED`, and Goal Planning retains no financial math, IO, RequiredContribution automation, target conversion, or assumptions JSON truth-path use. Results: Goal Planning `63`; Required `40`; Target `32`; Projection `38`; Assumptions `63`; Read `12`; Goals `65`; Health `68`; general `366 passed, 2 historical Investments/MagicMock failures`. Status: `VALIDATED`; 10.3.6 is `READY / NOT STARTED`.
- **10.3.6-B mandatory comparison matrix (locked by 10.3.6-A):** Test minimum two scenarios, three archetypes and arbitrary labels, explicit non-BASE reference, duplicate/missing IDs, identical assumptions with exact zero deltas, contribution/return/inflation/explicit-initial-wealth differences, provenance preservation, equivalent and mismatched horizon representations, as-of/output-mode/timing mismatches, mixed valid return types with the same output mode, target absent/present, target amount/basis validation, both/earlier/later/same-month achievement, non-achieving reference or candidate, period-zero `ALREADY_ACHIEVED`, nested `UNREACHABLE`, large Decimal money, input-order preservation, immutability, determinism, no ranking, atomic failure, and at-most-one financial projection per scenario.
- **10.3.6-B independent validation (2026-09-19):** Separate contract/code review and controlled Decimal oracles validated explicit identity/reference behavior, atomic prevalidation, equivalent resolved horizons, output-mode compatibility, no-target and target engine reuse, period-zero temporal deltas, null temporal deltas for non-achievement, source/provenance preservation, and exact money signs. The focused scenario suite is `37 passed`; Goal Planning `63`, Required `40`, Target `32`, Projection `38`, Assumptions `63`, Read `12`, Goals `65`, and Health `68` all passed. General `tests/unit` is `403 passed, 2 failed`, limited to the unchanged Investments timeline/MagicMock sorting failures. `10.3.6 = VALIDATED`; 10.3.7 remains deferred.
- **10.3.5-R2-SOL authoritative reconciliation (2026-09-19):** Supersedes V2's ordering conclusion. The real service validated Goal-current-amount provenance and target basis/output compatibility before checking type/status applicability, so a reserved/non-ACTIVE Goal could raise instead of returning `NOT_APPLICABLE`. The correction uses an explicit `GoalStatus.ACTIVE` whitelist and determines type/status eligibility before every projection-specific input.
- **10.3.5 independently validated — V2 (2026-09-17 TSK-10.3.5-V2):** Historical validation evidence later superseded on applicability-versus-projection-input precedence by TSK-10.3.5-R2-SOL.
- Time contract: `as_of_date` is period zero; the current partial month has no projection/proration; the next complete calendar month is period one; target dates compare at `YYYY-MM` granularity; horizons accept exactly one selector and enforce 1–1,200 cycles.
- Forward projection: zero initial wealth/contribution/return, positive rates including values above 100%, every supported negative rate above -100%, invalid `<= -100%`, `END_OF_MONTH` contribution timing, cross-year/long horizons, compound monthly conversion, and exact deterministic repeatability.
- Nominal/real matrix: nominal-to-nominal without inflation, nominal-to-real with required one-time Fisher conversion, real-to-real with forbidden inflation, and validation rejection for real-to-nominal. Inflation itself must be finite and `> -1`. Goal integration must require an explicit target value basis.
- Precision: Decimal only; money inputs reject fractional cents; calculation context has at least 34 digits; equivalent monthly rates retain at least 18 decimal places; every monthly projected return uses cent-scale `ROUND_HALF_EVEN`; closing/opening recurrence reconciles exactly; JSON uses strings/null.
- Forward output: every approved period and summary field, assumption echo, provenance, scope/as-of, and conditional-result metadata; no generative narrative and no frontend financial recalculation.
- Target-date solver: `ALREADY_ACHIEVED`, `ACHIEVED`, mathematically proven `UNREACHABLE`, and `NOT_REACHED_WITHIN_HORIZON`. Exhausting 1,200 months alone must not be called unreachable.
- Required-contribution solver: approved states, the mathematically safe target-amount contribution upper bound, cent-discrete monotonic binary search through the Target Achievement Solver/Forward Projection Engine oracle chain, and the invariant that `C` succeeds while `C - 0.01` fails unless `C = 0`.
- Goal integration: nullable facts, exact eligible/ineligible Goal types, paused/cancelled behavior, the seven approved timing statuses, direct month comparison without thresholds, and user isolation.
- Scenario comparison: editable archetype labels without rates, shared comparison invariants, explicit contribution/return/inflation/initial-wealth differences, exact deltas, null months-saved/lost when either target is not reached, stable ordering, and no mutation of source facts.
- Historical facts: prove portfolio returns, CDI, IPCA, IBOV, dividends, and Health trends never become future assumptions automatically.
- Sustainable contribution capacity: TSK-10.3.7-A concluded `DEFERRED — INSUFFICIENT CONTRACT / DATA`. The audit used ADR/code inspection and the certified Planning Health adapter against the current database: 17 consecutive monthly Decimal facts, 16 closed months, 12 surpluses, 4 deficits, no session mutation. No formula, production code, or tests were created. A future proposal must first contract window, minimum history, partial/gap/deficit/anomaly handling, exact statistic, currency scope, negative/zero/null semantics, and provenance.
- **10.3.8-A locked API verification matrix:** verify `/api/v1/planning` prefix composition, bearer auth on every route, existing async auth dependency plus request-scoped synchronous `get_db` only for certified Planning reads, no manual `SessionLocal`/commit/internal HTTP, strict string-only Decimal request fields, decimal-string/null responses, ISO dates/canonical enums, exact response mapping without arithmetic, complete period/summary output, stable provenance, and deterministic repeat requests. Verify domain statuses remain `200`, malformed/domain-invalid input is `422`, wrong-owner/missing Goals are indistinguishable `404`, and unexpected arithmetic/invariant failures are `500` rather than fabricated financial results.
- **Certified-source security matrix:** prove clients cannot submit Goal/portfolio provenance as certification; `GOAL_CURRENT_AMOUNT` performs one owned `goal_id + user_id` Decimal read and rejects missing/null facts without zero fallback; Goal Planning uses the path Goal and never the legacy float DTO path; `USER_PROVIDED_SCENARIO` stays explicitly user-provided. B1 validates ADR-023's internal single-tenant/cardinality guards, successful-run ownership, as-of cutoff, and Decimal fact; B2 exposes portfolio only as a source-only selector and delegates it to B1. Test no internal HTTP, no source aggregation/fallback, no writes, no LLM, no automatic assumptions, and no Sustainable Capacity route.
- **Capability/delegation matrix:** Forward, Target, Required, Goal Planning, and Scenario Comparison endpoints must each delegate to the corresponding certified engine once per contract and map its complete result. Required Contribution preserves its assumptions-template semantics; Goal Planning preserves applicability and ownership; Scenario Comparison preserves order/reference/target pair and call-count guarantees. OpenAPI must present separate request/response schemas and exact enum values.
- **API/lifecycle:** 10.3.8-A approved transient calculation endpoints only. Full monthly timelines and summaries are returned initially; no pagination/summary flag or arbitrary scenario-count cap is approved. Atomic validation must not truncate requests. Transport body/rate/time guardrails are a later measured infrastructure concern. Persistence tests, saved-scenario CRUD, migrations, and `goals.assumptions_json` use remain prohibited until a later ownership/lifecycle/versioning/provenance/staleness contract.
- **10.3.8-B independent validation (2026-09-20):** `41 passed` confirms the endpoint-free relative Planning router and clean app/OpenAPI import, existing JWT plus synchronous-reader dependency annotations, JSON-level string-only finite non-exponent Decimal inputs, declared `Decimal("1.000")` scale preservation through domain rejection, strict dates/timestamps, canonical enums, strict horizons, safe user/Goal selectors, portfolio exclusion, forged certified-fact rejection, exact Decimal response strings, public-only provenance, local error mapping, and absence of a fake endpoint. Regressions: Goal Planning `63 passed`; Scenario Comparison `37 passed`; Goals API/domain/repository `65 passed`; Health `68 passed`; general `tests/unit` `444 passed, 2 historical Investments/MagicMock failures`.
- **10.3.8-C implementation (2026-09-21):** HTTP tests cover the three authenticated transient calculation routes with strict JSON Decimal strings: simple independent projection/target/required-contribution oracles; certified server-side Goal amount; owned/missing/wrong-owner/null Goal outcomes; target-basis incompatibility; `ALREADY_ACHIEVED`, `UNREACHABLE`, `NOT_REACHED_WITHIN_HORIZON`, solved/zero-required statuses; forged sources and portfolio rejection; arithmetic-to-generic-500 mapping; engine call counts; and exact OpenAPI route/schema scope. No endpoint recalculates domain output, writes data, persists a calculation, exposes capacity, or invokes a non-corresponding engine. Focused `18 passed`; foundation `41 passed`; Planning/Goals/Health regressions passed; general `462 passed, 2 historical Investments/MagicMock failures`.
- **10.3.8-C independent validation (2026-09-21):** `25 passed` after independent real-HTTP checks and test-only coverage additions for declared rate precision/determinism, no Forward call after failed Goal resolution, intact Required template contribution, Required basis failure before solver invocation, and JSON-number rejection in all three routes. Verified OpenAPI contains exactly the three approved POST operations; TargetValueBasis is the shared neutral enum; responses copy certified periods/summaries/results as Decimal strings; and no financial math, write, persistence, capacity, Goal Planning, or Scenario endpoint exists. Regressions: foundation `41`, Projection `38`, Target `32`, Required `40`, Goal Planning `63`, Scenario `37`, Assumptions `63`, Read Foundation `12`, Goals `65`, Health `68` passed; general `465 passed, 2 historical Investments/MagicMock failures`.
- **10.3.8-D implementation (2026-09-21):** HTTP tests cover authenticated path-Goal ownership/non-enumeration, server-only Goal fact construction, path-only Goal current amount, exact user-provided Decimal provenance, active mathematical already-achieved behavior, nonprojectable lifecycle/type applicability with zero target-solver calls, missing-basis precedence, strict ACTIVE basis mismatch, deadline-versus-horizon separation, service timing/nested-result mapping, forge-resistant request shapes, local arithmetic `500`, and exactly four approved Planning POST operations. Focused `28 passed`; foundation `41`, calculation endpoints `25`, Goal Planning `63`, Projection/Target/Required/Scenario/Assumptions/Read `222`, Goals `65`, Health `68` passed; general `497 passed, 2 historical Investments/MagicMock failures`.
- **10.3.8-D-R1-SOL authoritative reconciliation (2026-09-22):** The validation matrix now distinguishes malformed request structure from unnecessary projection-specific source consumption. ACTIVE eligible + unavailable selected Goal current amount remains `422`; `ACHIEVED`, `PAUSED`, `CANCELLED`, `RETIREMENT`, `FINANCIAL_INDEPENDENCE`, and `DIVIDEND_INCOME` with the same null source return `200 / NOT_APPLICABLE`, no initial-wealth placeholder, and zero target-solver calls. A pure service preflight is the sole eligibility authority; the router contains no status/type list. Focused Goal HTTP `37 passed`; Goal Planning `65`; foundation `41`; calculation endpoints `25`; other Planning `222`; Goals `65`; Health `68`; general `508 passed, 2 historical Investments/MagicMock failures`.
- **10.3.8-D-V2 final independent validation (2026-09-23):** Validated the reconciled boundary through real HTTP, domain, OpenAPI, source-order, and full regression probes. `preflight_applicability()` and `evaluate()` share one applicability authority across all `GoalStatus × GoalType` values; malformed Decimal remains structural `422`; non-projectable Goals stop before source resolution; ACTIVE paths resolve source then evaluate. Focused Goal HTTP `39 passed`; Goal Planning `101`; foundation `41`; calculation endpoints `25`; other Planning `222`; Goals `65`; Health `68`; general `546 passed, 2 historical Investments/MagicMock failures`.
- **10.3.8-E independent validation (2026-09-23):** Real-HTTP validation expanded Scenario Comparison coverage to prove domain prevalidation aborts before financial subengines, Goal lifecycle/type applicability does not leak into a selected Goal-current-amount source, noncontractual ranking/recommendation fields are rejected, target values remain strict Decimal strings, the mapper copies deliberately non-derivable certified deltas without recomputation, and any explicit first/middle/last scenario may be the reference without reordering. The endpoint has exactly five approved Planning operations, authenticates through the existing JWT dependency, resolves all sources atomically through the synchronous certified reader, preserves order/reference/archetype semantics, and creates no write/persistence path. Focused suite: `42 passed`; Planning domain regressions `323`; Goals `65`; Health `68`; general `585 passed, 2 historical Investments/MagicMock failures`.
- **10.3.8-F automated integration validation (2026-09-23):** A five-test cross-endpoint suite verifies the exact secure OpenAPI route inventory and unique operation IDs; `401` on every route; strict JSON-string Decimal and portfolio-source rejection across C–E; uniform non-enumerating Goal `404`; deterministic full 1,200-period projection serialization. Static inspection found no Planning API write, financial math, ranking/advice/LLM, persistence, or Sustainable Capacity path. Integration `5`; B–E API `147`; Planning domain `323`; Goals `65`; Health `68`; general `593 passed, 2 historical Investments/MagicMock failures`. Manual Swagger smoke is the remaining closure gate.
- **10.3.9 frontend foundation independent validation (2026-09-23):** The browser boundary has complete TypeScript request/response contracts and one authenticated client method per certified Planning route. Independent source/DTO inspection confirmed that financial values remain `string`, supported source enums exclude portfolio, Goal Planning preserves nullable initial wealth for `NOT_APPLICABLE`, and only Projection is user-facing with direct response rendering and loading/error/empty states. Static audit found no local financial math, numeric financial conversion, persistence, ranking, LLM, or 10.3.10 analytical UI. The existing frontend has no unit/component test runner, so no new framework was introduced: `npx.cmd tsc --noEmit`, focused ESLint, static audit, and `npm.cmd run build` passed; the production build recognizes `/wealth-intelligence/planning`. Manual UI validation remains required; Swagger Authorize manual smoke is deferred by user and is not recorded as passed.
- **10.3.9 manual closure (2026-09-24):** Nominal→Nominal, Real→Real, Nominal→Real, and unavailable Real→Nominal smoke cases passed. `10.3.9 = VALIDATED`.
- **10.3.10 analytical UI (2026-09-24):** VALIDATED. Projection, Target Achievement, Required Contribution, owned Goal Planning, and ordered Scenario Comparison use the certified client only. The lone `Number(decimalString)` conversion is isolated to Recharts rendering of certified periods. No persistence, advice, automatic portfolio wealth, Capacity, Retirement/FIRE, Portfolio Intelligence, or LLM was added. Focused TypeScript, ESLint, production build, and user manual validation passed; broader visual/UX refinements are deliberately deferred.
- **10.3.10B2 validated ADR-023 matrix:** source-only public selector, safe `422` error mapping, all-five-endpoint integration, no client amount/account/provenance, generic Projection/Target/Required delegation, Goal Planning applicability short-circuit, Scenario Comparison mixed-source atomicity, and unchanged user-provided/Goal source behavior. The as-of cutoff is passed from each request to B1 and compares `reference_month` plus snapshot-version update time, never a fabricated financial observation timestamp. API suites: `157 passed`; B1 plus Planning domain: `339 passed`; general `tests/unit`: `614 passed, 2 historical Investments/MagicMock failures`.
- **10.3.10B3 frontend integration:** the shared Planning source form and discriminated TypeScript builders expose the B2 portfolio source without a preview or Investments API read. Static review verifies source-only payload construction, per-scenario input isolation, no stale manual amount/timestamp, server-certified provenance presentation without fake daily dates or observed timestamps, no zero fallback, and no financial calculation. The project has no frontend automated runner; B3 is checked by TypeScript, focused ESLint, production build, static audits, and pending user manual smoke.
- **10.3.10B4 independent/adversarial validation (2026-09-26):** VALIDATED / COMPLETE. The audit re-proved the guarded one-user tenant invariant, semantic UUID/run provenance, zero/one/many scope handling, exact latest-eligible-as-of temporal selection, and the full Decimal path from `patrimonio` to TypeScript string. Results: B1 `16 passed`; Planning API `157 passed`; Planning domain `323 passed`; general units `614 passed, 2` unchanged historical Investments/MagicMock failures; secured five-route OpenAPI probe; TypeScript, focused ESLint, and production build passed. User-confirmed B3 manual smoke passed for all five capabilities.
- **10.3.11 integration/stabilization (2026-09-26):** `VALIDATED / STABILIZED`. Re-ran the six Planning API suites (`157 passed`) and all seven Planning-domain suites plus the ADR-023 resolver (`339 passed`), then the general baseline (`614 passed, 2` known Investments/MagicMock failures). OpenAPI retained the exact five secured POST operations and unique IDs. TypeScript, focused Planning lint, and production build passed; the route `/wealth-intelligence/planning` is present. Static review found no financial browser truth, backend float/write path, router snapshot SQL, selector forgery, persistence, advisory, Capacity, FIRE, Portfolio Intelligence, or LLM leakage.
- **10.3.12 final closure (2026-09-26):** `VALIDATED / CLOSED`. With no production change after stabilization, closure used proportional checks rather than repeating the whole suite: Planning API integration, ADR-023 resolver, and representative projection/target/required/Goal/scenario suites (`269 passed`); exact secured five-route OpenAPI; TypeScript; focused lint; production build; and final static Decimal/trust/read-only audit. The `614 passed, 2` historical Investments/MagicMock general baseline remains accepted evidence.
- **POST-10.3 UX contract (2026-09-26):** ADR-024 locks frontend-only simplification without reopening financial contracts. UX-B1 must add executable table-driven and boundary tests for exact string-only pt-BR money/rate/date adapters before migrating Planning forms. Subsequent validation must cover submit-time local-date and observation capture, nominal/real payload parity, source switching without stale fields, Goal target-basis declaration, shared comparison context materialization, explicit reference/order, primary-text no-float formatting, rendering-only chart conversion, accessibility, typecheck, focused lint, build, and manual five-capability/Health-chrome smoke.
- **POST-10.3 UX-B1 (2026-09-26):** `VALIDATED`. Node-only Vitest `3.2.4` runs the pure `planningLocale` suite: `57 passed` covering exact string-safe BRL display including values above `Number.MAX_SAFE_INTEGER`, strict pt-BR money grouping and decimal rejection, percentage-to-fraction text shifting, display rounding boundaries, civil dates/local day/reference month, and structured lexical-error copy. TypeScript, focused lint, and production build pass. No Planning component was migrated.
- **POST-10.3 UX-B2 (2026-09-26):** `VALIDATED`. The user confirmed the cleaner Planning entry, the three intentions and Objective submodes, navigation, title removal, minimal Financial Health chrome, and no lost context. Static inspection proves the five-peer Planning tab map was replaced by three keyboard-accessible intention buttons and the Objective-only secondary task switch; all five original capability components remain mounted by their mapped state.
- **POST-10.3 UX-B3 (2026-09-26):** `VALIDATED`. The user confirmed MyProfit simple/info behavior, BRL money and contribution input, human percentage input, ambiguous-money rejection, compact Advanced options, all certified nominal/real matrix cases, source switching, and Objective/Comparison consistency.
- **POST-10.3 UX-B4 implementation evidence (2026-09-26):** Four pure tests cover shared as-of/horizon/output/target expansion, scenario contribution and return differentiation, source-only MyProfit isolation beside manual and Goal selectors, per-scenario return type/inflation, request order/reference preservation, and explicit reference clearing after removal. Full Node-only Vitest is `64 passed`; TypeScript, focused lint, and production build pass. The manual review subsequently validated density, one shared context, mixed sources, explicit reference, add/remove, and unchanged comparison execution.
- **POST-10.3 UX-B4 (2026-09-27):** `VALIDATED` per the accepted UX-B5 input state.
- **POST-10.3 UX-B5/B5-R1 (2026-09-27):** `VALIDATED` after accepted user review. Result and chart components use the B1 string-safe money/rate/date/reference-month formatters for primary text; Recharts retains one isolated Decimal→`Number` adapter only for rendering. The accepted visual review covered responsive heroes, muted violet primary CTAs, emerald/amber/zinc status semantics, less nested border density, quiet provenance, neutral comparison reference, chart grid/strokes/colors, and no motion.
- **POST-10.3 UX-B6 (2026-09-27):** `VALIDATED` after the accepted user review. First-submit skeletons, recalculation, stale-result feedback, error preservation, reduced motion, charts, keyboard flow, and narrow layouts were accepted without backend, API, or financial-truth change.
- **POST-10.3 UX-B7 (2026-09-27):** `VALIDATED / CLOSED`. Independent closure repeated Vitest (`64 passed`), TypeScript, focused Planning/Health lint, production build, focused Planning backend/API/domain/resolver regression (`496 passed`), a secured five-route OpenAPI probe, and static Decimal/trust/read-only/no-ranking audits. The Recharts SSG dimension warning remains historical and non-blocking.
- **10.3.10B1 validated foundation:** `16 passed` cover one-user semantic UUID ownership, zero/one/many scopes, unknown/non-successful/incompatible/other-owned runs, malformed bucket, same-month and post-as-of behavior, future bucket rejection, latest-eligible fallback, exact Decimal, `observed_at is None`, provenance, and read-only SELECT-only execution. Planning read foundation `12` and Goal Planning `101` also pass. The `tests/unit` regression reports `609 passed, 2 historical Investments/MagicMock failures`.
- Frontend: TypeScript parity, no financial recalculation, loading/error/empty states, request-race protection, nominal/real/target-basis labels, month-level date language, and clear conditional-projection wording.
- Independent validation: compare production results with a separate Decimal oracle or independently constructed spreadsheet; production code cannot generate its own expected values.
- Regression: Goals, Financial Health, and Investments baselines remain unchanged unless a microprocess explicitly authorizes an integration modification.

### Phase 10.4 — Retirement & Financial Independence (FIRE)
- Unit: exact annual spending and canonical target calculation, including `ROUND_CEILING` cent boundaries.
- Unit: nonnegative gap, unclamped eight-place progress ratio, exact summary status, and withdrawal capacity derived from the unrounded annual product.
- Unit: strict Decimal/scale/rate domains and the complete required/forbidden/conditional mode matrix.
- Unit/integration: `REAL → REAL` and `NOMINAL → REAL` composition, with inflation applied exactly once by Planning.
- Integration: one authenticated transient endpoint, both allowed wealth selectors, ADR-023 unavailable/ambiguous outcomes, provenance, response nullability, and no writes.
- Delegation: canonical target equality across summary and solver calls; `TargetAchievementSolver` and `RequiredContributionSolver` remain the only projection/inverse authorities and preserve their exact statuses.
- Static boundary: no Goal source/mode, Health inference, dividends, macro forecast, external-income offset, persistence, float financial truth, scenario comparison, Portfolio Intelligence, or LLM calculation.
- Independent validation: compare FIRE-specific Decimal outputs with a separate oracle; production code and Planning solvers cannot generate their own expected values.
- **10.4-D7 independent closure (2026-10-01):** `VALIDATED / CLOSED`. Fresh-context review reconciled ADR-025 and the locked FIRE contract against the complete backend/frontend slice. FIRE backend `67 passed`; focused Planning `262 passed`; independent Decimal vectors and real-service REAL/NOMINAL composition passed; live OpenAPI exposed one secured FIRE POST plus five unchanged Planning POSTs; FIRE frontend `13 passed`, locale `57 passed`, full Vitest `77 passed`, TypeScript, focused lint, and production build passed. General backend units were `681 passed, 2 failed`, limited to the unchanged historical Investments/MagicMock sorting debt. No production/test/migration change was made during closure.

### Phase 10.5 — Portfolio Intelligence
- 10.5-B remains paused until R7; 10.5-A is the preserved audit authority.
- Contract tests must first lock one governed position-valuation basis,
  completeness, temporal alignment, ownership, Decimal precision/rounding,
  provenance, and empty/partial/error semantics.
- When authorized, unit coverage may include allocation, largest position, and
  fixed top-3/top-5 concentration as deterministic facts from one complete,
  aligned valuation set.
- Performance, attribution, benchmark comparison, yield, risk, score, target
  allocation, and rebalancing tests are not approved by the MVP audit.
- Frontend validation must prove presentation-only behavior and no mixed
  fallback/browser financial authority.

### Phase 10.R2 — Smart Financial Context
- B1 persistence/ownership evidence: 23 focused tests cover migration
  upgrade/downgrade/re-upgrade, metadata parity, table/FK/check/unique/index
  constraints, exact Decimal roundtrip, null/zero/clear semantics, caller-owned
  transactions, decision update/reset, privacy-by-schema, and zero/one/many or
  wrong-user ownership. A copied real database also passed
  `f2915371d283 -> 2d6b4f8a9c1e -> f2915371d283 -> 2d6b4f8a9c1e` with empty
  backfill. Focused Planning/Goals/authentication regressions passed 30 tests.
  The complete backend unit directory returned `704 passed, 2 failed`; both
  failures are the unchanged historical Investments asset-detail/MagicMock
  timeline debt documented in `CURRENT_STATE.md`.
- B2 declared Profile API evidence: 32 focused tests cover real route auth,
  strict Decimal-string/date parsing, exact string serialization, empty state,
  set/update/null-clear idempotence, forged owner fields, wrong/multiple-user
  failure, purpose-limited responses, request rollback, and OpenAPI scope. B1
  remained `23 passed`; authentication/Goals/API-foundation regressions were
  `69 passed`; the complete backend unit directory returned `736 passed, 2
  failed`, limited to the same historical Investments failures.
- B3 recurring-evidence evidence: 35 focused tests cover NFKC/case-fold/space
  normalization, a fixed SHA-256 signature vector, provider/account/currency
  separation, six civil months, 3-of-6 non-consecutive coverage, partial month,
  end/start-month shifts, exact Decimal median/MAD, amount variability, stable
  ordering, structured transfer ambiguity, bounded SQL, and zero/one/many or
  wrong-user ownership. B1+B2 remained `55 passed`; focused Health/Pierre/
  transaction regressions were `101 passed`; complete units returned `771
  passed, 2 failed`, limited to the unchanged historical Investments failures.
  A read-only active-database smoke returned aggregate counts only and left the
  session with no new, dirty, or deleted objects.
- B4 income-decision API evidence: 32 focused tests cover authenticated empty
  and populated reads, privacy allowlisting, exact Decimal strings, current
  decision overlay, confirm/reject replacement and idempotence, reset,
  persisted stale decisions, signature-version isolation, forged/disappeared
  candidates, strict request fields, evidence-fingerprint `409`, fail-closed
  ownership, decision-only writes, rollback after mapping failure, and exact
  OpenAPI scope. The combined B1–B4 suite returned `122 passed`; focused
  Health/Pierre/transaction regressions returned `103 passed`; auth/Profile/
  Goals/API-foundation regressions returned `138 passed`; complete units
  returned `803 passed, 2 failed`, limited to the unchanged historical
  Investments asset-detail failures. A read-only active-database composition
  smoke returned four views with transaction/decision counts unchanged and no
  new, dirty, or deleted session objects.
- B5 feature-specific composition evidence: 20 focused tests cover the locked
  feature enum and allowlists, immutable Smart Values, exact Decimal and
  provenance, declared/confirmed/detected/rejected/stale income separation,
  no aggregation, source-specific unavailable and freshness states, explicit
  Planning/FIRE assumptions, Goal/Health references, override preservation,
  cross-feature exclusion, and fail-closed ownership. The combined B1–B5 suite
  returned `142 passed`; Goals/Health regressions returned `272 passed`;
  Planning/FIRE source and boundary regressions returned `128 passed`; complete
  units returned `824 passed, 2 failed`, limited to the unchanged historical
  Investments asset-detail failures.
- B6 Profile context experience evidence after material-findings remediation:
  `30` helper/client tests and `14` rendered Profile tests (`44 passed` focused)
  cover purpose-limited browser persistence, GET-only initial load, exact
  Decimal-string save/null-clear, candidate confirm/reject/reset, synchronous
  global candidate mutation/retry locking and release on every result, accurate
  `404`/`409` refresh feedback, empty-list message retention, distinct stale
  confirmed/rejected decisions without current money, hidden fingerprint use,
  and naïve-UTC timestamp normalization separate from civil dates. The complete
  frontend suite returned `121 passed`; TypeScript, targeted B6 lint, and the
  production build passed. Project-wide lint remains at the unchanged baseline
  of `53 errors / 46 warnings`, with none in a B6 file. Independent B6 delta
  re-review approved M1–M5 with no blocking or material findings.
- Contract-test declared versus observed context, feature-specific source
  choice, strict Decimal strings, provenance, freshness, confirmation, reset,
  and override semantics against `SMART_FINANCIAL_CONTEXT_CONTRACT.md`.
- Test declared monthly gross income validation, nullable/delete behavior,
  timestamps, purpose limitation, ownership, persistence, and no automatic
  mutation from transactions.
- Test the versioned exact signature, six-month window, three-distinct-month
  threshold, same-month duplicates, partial current month, Unicode/whitespace
  normalization, no fuzzy/digit stripping, and deterministic ordering.
- Test exclusions for non-classified, outgoing, ignored, same-titularity, and
  investment evidence; absence of an amount-similarity gate or confidence
  score; bounded evidence; stale confirmed sources; reject/reset lifecycle; and
  signature-version reconciliation behavior.
- Integration coverage must authenticate every endpoint and prove the
  exact-single-user/current-user guard, ambiguity failure, non-enumeration,
  minimum exposure, and no Profile/transaction/Health/Goal/Planning/FIRE writes.
- Composition tests must prove feature allowlists and reuse certified Health,
  Goal, Planning/ADR-023, and FIRE boundaries without duplicating their math or
  source resolvers.

### Phase 10.R3 — External Context
- **R3-C implementation evidence (2026-10-10):** `127` focused pure-domain
  tests pass across the exact five-series immutable registry, strict lexical
  Decimal normalization and bounds, daily/monthly civil periods, economic
  identity, provenance, independent status enums, the three normative V1 hash
  vectors, complementary equivalence/difference cases, exact prefix/JSON/null,
  structured rejection, and `A -> B -> A`. R2/bootstrap regressions pass `159`,
  Planning `497`, and FIRE `67`. Complete units report `969 passed, 2 failed`;
  both failures are the unchanged Investments asset-detail MagicMock/string
  timeline sorting baseline. Backend import/OpenAPI smoke passed with 55 paths,
  five unchanged Planning paths, one unchanged FIRE path, zero External Context
  paths, and no disposable database file created. Static scans found no network,
  SQL/ORM, migration, application bootstrap, clock, yfinance, router, or engine
  dependency in the R3-C package.
- **R3-C independent implementation review (2026-10-10):** Gemini 3.8 Flash
  High returned 0 blocking, 0 material, 0 minor, and 2 informational findings.
  It confirmed `127` R3-C tests, `160` R2 regressions, `497` Planning tests,
  `67` FIRE tests, the three normative SHA-256 vectors, and OpenAPI compatibility
  at 55 paths and 59 HTTP operations without an External Context endpoint.
  `INF-01` records that direct construction of value objects does not replace
  the certified registry-validation functions; R3-D repositories and services
  must accept observations only through certified validation paths. `INF-02`
  records the distinct OpenAPI path and operation counts. Neither finding
  changes R3-C implementation or reopens ADR-029/fingerprint V1.
- R3-C owns registry, immutable domain types, strict Decimal parsing, exact
  units/frequencies, daily/monthly reference periods, provenance requirements,
  observation/expectation separation, fixed-scale canonicalization without
  rounding, over-scale rejection, and explicit separation of source unit,
  provider precision, normalization scale, and internal precision.
- R3-C also owns `content_fingerprint_v1`: a typed closed eleven-field payload,
  registry validation before hashing, canonical Decimal and civil-period
  normalization, deterministic sorted compact UTF-8 JSON, the exact
  NUL-terminated V1 domain prefix, SHA-256, version `1`, and lowercase
  `sha256:<64 hex>` output. The three complete Selic, negative-IPCA, and USD
  vectors in `EXTERNAL_CONTEXT_CONTRACT.md` are normative and must execute
  through production code rather than reproducing the implementation in the
  test oracle.
- Complementary valid tests cover dictionary-construction-order independence,
  `10.5`/`10.50` equivalence, negative-zero normalization, different valid
  value and period, and another series with coherent registry metadata. Every
  valid case states its complete payload or an unambiguous delta. Tests also
  prove that `retrieved_at` and all other excluded operational/provenance fields
  cannot enter the closed hash payload.
- Structured rejection tests cover incompatible unit, semantic class,
  currency, and scale; unknown series; missing or extra keys; float values;
  booleans masquerading as integers; and other registry-invalid payloads.
  Rejected input has no expected valid domain fingerprint. Tests independently
  assert prefix bytes, no BOM/newline/salt, stable key order, exact null, and no
  Decimal-to-float conversion.
- R3-D owns migration/metadata parity and exact canonical-`TEXT` roundtrip
  through the real SQLite/SQLAlchemy path after close/reopen. Test small
  percentages, approved lexical extremes, storage class, no float, and the
  prohibition on SQL lexical ordering/ranges/casts/arithmetic as numeric
  authority. It also owns economic/content/knowledge-event identity,
  `A -> B -> A`, consecutive retransmission deduplication, immutable history,
  concurrent ingestion atomicity, simultaneous deduplication/conflict handling,
  sequence allocation, deterministic tie-breaking, rollback cleanliness,
  exact `consumer_as_of` replay, late ingestion/no look-ahead, absent
  `published_at`, sync state, negative cache, separate refresh/economic
  freshness/acquisition health, partial/unavailable reasons, and
  last-known-good without failure-forced staleness.
- R3-D persists `content_fingerprint_version` separately from
  `content_fingerprint`, compares their pair only against the current head of
  the same economic identity, has no global fingerprint uniqueness, and proves
  consecutive deduplication plus `A -> B -> A` replay. Future versions cannot
  be deduplicated across V1 without an approved transition policy.

- **R3-D final independent implementation review (2026-10-10):** Gemini 3.8
  Flash High approved R3-D with 0 blocking, 0 material, 0 minor, and 2
  informational findings. SQLAlchemy 2.0.21 independently reproduced `45`
  R3-D and `127` R3-C tests; SQLAlchemy 2.0.51 reproduced `45` R3-D, `127`
  R3-C, and `8` bootstrap tests. The `180` focused R3-C/R3-D/bootstrap tests
  pass on SQLAlchemy 2.0.51. They cover Registry
  Version V1, UTC codec extremes and rejection, the two-table migration,
  metadata/schema/constraint/index/FK parity, append-only triggers, exact
  Decimal/UTC `TEXT`, close/reopen, certified read/write revalidation,
  fingerprint mismatch before transaction, real `BEGIN IMMEDIATE`, two
  independent writers, busy retry, rollback, ambiguous commit, atomic
  event/sync state, A→A, A→B→A, per-identity sequence, supersession, two-cut
  as-of/no-look-ahead, the logical commit window, LKG, safe initialization,
  empty/partial/failed attempts, mismatch, and independent availability,
  freshness, health, and refresh policy. R2/bootstrap is `161 passed`, Planning
  `497`, FIRE `67`, and complete units `1015 passed, 2 failed`; the failures are
  the unchanged Investments/MagicMock timeline baseline. Import/OpenAPI remains
  55 paths, 59 operations, and zero External Context paths, and creates no DB.
  Every migration/integration/concurrency test used disposable SQLite storage
  under `C:\tmp`; the active DB was not opened. R3-D is
  `IMPLEMENTED / VALIDATED / INDEPENDENTLY APPROVED / CHECKPOINT AUTHORIZED`.
  `INF-R3D-01`: the global SQLite foreign-key listener is verified in tested
  environments but deployment remains separately gated by legacy referential
  integrity, backup/rollback, startup, and explicit deployment authorization.
  `INF-R3D-02`: clean installation cannot resolve the declared Pydantic pins
  (`pydantic==2.4.2` with `pydantic-settings==2.14.2`), and `pytest-asyncio`
  is required by tests but undeclared; this is a separate Dependency
  Reproducibility & Packaging Remediation task, not an R3-D code change.

#### R3-D.1 normative test gates

The following are future R3-D executable requirements. This documentary
amendment creates no test code.

`PHASE 10.R3-D.1 — INDEPENDENT CONTRACT DELTA REVIEW APPROVED`: Gemini 3.8
Flash High reviewed eight documentation files (657 insertions/48 removals) and
reported 0 blocking, 0 material, 0 minor, and 2 informational findings. This
was a documentary review, not runtime-test execution.

**Registry version V1:**

- assert `EXTERNAL_SERIES_REGISTRY_VERSION == 1`, positive strict-integer type,
  Python-bool rejection, and no implicit V2 behavior;
- persist `registry_contract_version INTEGER NOT NULL` in both observation
  versions and sync state, with backend-owned assignment and immutable event
  history;
- prove first sync-state initialization sets
  `registry_contract_version = EXTERNAL_SERIES_REGISTRY_VERSION` but preserves
  an absence-consistent never-acquired state, without fabricated success,
  attempt, valid observation, coverage, healthy, or current evidence;
- preserve historical events, fingerprints, fingerprint versions,
  last-known-good, economic identity, sequence, logical time, and supersession
  across version mismatch;
- prove Content Fingerprint V1 and its eleven-field payload are independent of
  registry version;
- prove `REGISTRY_VERSION_MISMATCH` yields `UNKNOWN` acquisition health and
  economic freshness while availability remains independent, with no forced
  `STALE`, `UNAVAILABLE`, zero, refresh, deletion, or synthetic event;
- prove a post-reconciliation identical retransmission may update bounded sync
  telemetry without creating an event, and that no future-version support is
  inferred.

**UTC codec V1:**

- exact `YYYY-MM-DDTHH:MM:SS.ffffffZ`, 27 ASCII characters, fixed zero padding,
  six microsecond digits, literal `Z`, byte-identical roundtrip, real SQLite
  `TEXT`, close/reopen, and valid lexicographic/chronological ordering;
- cover extreme and invalid civil dates, exact microseconds, aware UTC output,
  and rejection of naive datetimes, non-zero offsets, strings at the governed
  Python write boundary, missing microseconds, variable offsets, non-canonical
  text, and incompatible types;
- verify invalid stored text fails with a typed integrity error and is never
  silently normalized or repaired.

**Logical knowledge time and transactionality:**

- use an injected clock and capture `transaction_time_utc` exactly once per
  attempt after SQLite write reservation; assign
  `ingested_at = known_from = transaction_time_utc`;
- enforce transaction time not earlier than `retrieved_at` or the current
  head's `known_from`, including equal-microsecond sequence tie-breaking and
  typed failure without clamping;
- prove per-identity sequence starts at 1, advances only on committed content
  transitions, is not consumed by rollback or retransmission, is not global,
  and produces sequences 1/2/3 for `A -> B -> A`;
- cover commit, rollback, lock timeout, bounded retry with a new timestamp and
  head reread, and exact as-of behavior before, at, and after each logical cut;
- use two independent connections to prove `BEGIN IMMEDIATE` is the first
  relevant transaction operation, event/sync-state atomicity, uncommitted
  invisibility, and serialized conflicting writers;
- capture actual SQLite SQL/transaction evidence rather than assuming
  `Session.begin()` emits `BEGIN IMMEDIATE`, and prove no concurrent
  `knowledge_sequence` allocation race;
- include an adversarial case where a retrospective cut between logical
  `known_from` and physical commit can select the event after commit. The test
  must document the logical retroactivity window and must not claim a physical
  commit or first-visibility timestamp;
- run on a disposable database only, never the active SQLite file.

**SQLAlchemy compatibility:**

- use only APIs available in the declared `SQLAlchemy==2.0.21` and prove the
  actual SQL/transaction boundary there;
- also verify the locally observed `2.0.51` behavior;
- do not change, install, upgrade, or downgrade dependencies without a separate
  authorization.

#### R3-E.0 normative future test gates

This documentation-only amendment creates no executable test. Future R3-E
automated tests use mocked HTTP responses and disposable SQLite only; they do
not contact BCB and never open the active database.

The targeted independent remediation review was approved by Gemini 3.8 Flash
High with 0 blocking, 0 material, 0 minor, and 2 informational findings.
`MAT-R3E0-01`, `MIN-R3E0-01`, `MIN-R3E0-02`, and `INF-R3E0-01` are resolved;
the remaining V1 risks are `INF-R3E0-02` (scalar discontinuous coverage) and
`INF-R3E0-03` (no persistent acquisition journal). This approval does not run
or replace the future normative test matrix below.

**Ordinary windows and reconciliation:**

- DAILY is inclusive for exactly `D - 89 days` through explicit stable `D`,
  truncated only by the series normalized floor;
- MONTHLY begins on the first civil day of the month 23 calendar months before
  `D`, includes the current month, and ends on explicit `D`;
- cover civil month and year transitions, including 29 February and leap-year
  boundaries, without replacing calendar-month arithmetic with fixed days;
- preserve the exact `1994-07-01` normalized floor for SGS 1 and each other
  series' registry floor;
- prove no request ends after its explicit cut, creates weekend/holiday rows,
  invents a missing monthly observation, or accumulates/annualizes a monthly
  rate;
- prove revisions outside ordinary windows are not presumed discovered;
- require registry key, inclusive start/end, and explicit historical-
  reconciliation intent for bounded manual deep reconciliation;
- prove no automatic whole-history fallback, startup backfill, scheduler,
  public endpoint, or first-acquisition full backfill.

**Deferred ingestion, coverage, and finalization remediation matrix:**

1. Calling `ingest()` without a mode preserves the complete R3-D immediate
   behavior and result contract.
2. Deferred ingestion never records global `SUCCESS`.
3. Deferred ingestion never advances successful refresh eligibility.
4. Deferred ingestion never expands `coverage_start`/`coverage_end`.
5. Deferred ingestion preserves the certified event, fingerprint, sequence,
   and supersession semantics.
6. `observations_received`, `accepted_transitions`, and
   `consecutive_retransmissions` change only under their existing event
   semantics.
7. LKG changes atomically with the valid committed event.
8. `finalize_acquisition(...)` covers global `SUCCESS` only with complete chunk
   proof and committed finalization.
9. It covers whole-operation `EMPTY` without an observation or numeric zero.
10. It covers `PARTIAL` while preserving committed events, prior success, and
    LKG.
11. It covers `FAILED` while preserving history, prior success, and LKG.
12. Finalization never increments or recalculates event counters.
13. `get_sync_state(...)` returns `None` for a missing row.
14. The read-only query emits no `INSERT`, including no call to `initialize()`.
15. Chunk A committed followed by a process crash records no global success,
    coverage expansion, or successful refresh advancement.
16. Chunk A success, chunk B failure, and chunk C success yields global
    `PARTIAL` and reports B.
17. Disconnected completed chunks never become a fictitious continuous range.
18. With no prior durable coverage, `PARTIAL` keeps both coverage fields null.
19. A fully received, validated empty chunk participates in successfully
    queried continuity but creates no economic observation.
20. Legacy R3-D coverage is not reclassified as proved queried continuity
    without additional evidence.
21. Retrying the same finalization is counter-idempotent and rejects stale or
    temporally regressive overwrites.
22. Reprocessing preserves content idempotence and `A -> A`, `A -> B`, and
    `A -> B -> A` history without false transitions.
23. Independent writers retain serialized, deterministic state transitions.
24. `BEGIN IMMEDIATE` remains the first relevant writer operation.
25. Any failure inside one owned transaction rolls back all its event/sync
    mutations, without claiming global rollback across prior chunks.
26. The store adapter and ingestion path run with declared
    `SQLAlchemy==2.0.21`.
27. The same gates run with observed SQLAlchemy `2.0.51`.
28. All 45 existing R3-D tests pass without regression.
29. All 127 existing R3-C tests pass without regression.
30. Metadata/migration inspection proves no new migration or third table.
31. A path guard proves the active financial database remains unopened and
    unmodified.
32. Static and behavioral checks prove no Planning, FIRE, Goals, Health,
    Portfolio, or other financial authority changes.

The scenario matrix also proves complete chunk validation before first
persistence, safe ambiguous-commit handling without blind retry, explicit
separation of successfully queried and observed economic coverage, preserved
Registry Version V1, Content Fingerprint V1, UTC V1, and no claim of a durable
`STARTED` state or cross-process exactly-once execution.

If the existing R3-D service, its two tables, and the approved
`get_sync_state(...)`/`finalize_acquisition(...)` responsibilities cannot pass
the interrupted-acquisition and no-false-global-success gates, implementation
stops for a material contract decision before an alternative mechanism is
introduced.

#### R3-E1 executable validation record

R3-E1 implements only the approved store compatibility boundary. Its tests use
disposable SQLite and no HTTP: default immediate compatibility; opt-in deferred
transition, retransmission, and `A -> B -> A`; event counters, LKG, sequence,
fingerprint, registry mismatch, and crash-before-finalization; read-only
present/absent sync-state lookup; evidence-derived `SUCCESS`, `EMPTY`,
`PARTIAL`, and `FAILED`; empty and failed middle chunks; null/prior/disconnected
coverage; inconsistent or gapped evidence; stale/repeated finalization;
rollback; and independent SQLite writers.

Current evidence is R3-D/R3-E1 `61 passed`, R3-C `127 passed`, bootstrap `8
passed`, and combined R3-C/R3-D/R3-E1 `188 passed` under the retained isolated
SQLAlchemy 2.0.21 environment. Main SQLAlchemy 2.0.51 also passed the focused
suites. Direct regressions are R2/bootstrap `161 passed`, Planning `503
passed`, FIRE `71 passed`, and complete units `1031 passed, 2 failed`; the two
failures are the unchanged Investments/MagicMock timeline baseline. All
persistence fixtures refuse the active financial database.

Gemini 3.8 Flash High independently reproduced the R3-E1 evidence above on
SQLAlchemy 2.0.51 and the isolated 2.0.21 environment, approving the
adversarial code review with 0 blocking, 0 material, 0 minor, and 3
informational findings. `INF-R3E1-01` retains the scalar durable-coverage
limitation; `INF-R3E1-02` retains the absence of a persistent acquisition
journal and distributed idempotency; `INF-R3E1-03` retains the two historical
Investments/MagicMock failures. `INF-R3D-01` and `INF-R3D-02` remain preserved.
The user authorized and published the R3-E1 Git checkpoint; R3-E1 is `CLOSED /
PUSHED`.

#### R3-E2 executable validation record

R3-E2 tests the provider boundary without live HTTP or SQLite. The `70` focused
tests cover the five registry-owned SGS endpoints, exact safe query parameters,
redirect and permanent/transient HTTP behavior, bounded retries and
`Retry-After`, timeouts, streaming/body/record caps, strict content type and
payload certification, deterministic inclusive civil-date partitioning beyond
ten years, leap-day boundaries, MONTHLY normalization, duplicate handling,
per-response UTC `retrieved_at`, all aggregate outcomes, adversarial
`SUCCESS + FAILED + SUCCESS`, retry recovery, and explicit incomplete chunks
for count or elapsed-budget exhaustion. Static isolation checks reject store,
SQLAlchemy, scheduler, endpoint, and finalization dependencies.

Current R3-E2 evidence is provider `70 passed`, R3-C `127 passed`, R3-D/R3-E1
`61 passed`, and bootstrap `8 passed`. The complete unit suite is `1101 passed,
2 failed`; both failures are the unchanged Investments/MagicMock timeline
baseline. All provider HTTP was simulated with `httpx.MockTransport`; no live
BCB request or active-database access occurred. Gemini 3.8 Flash High
independently reproduced provider `70 passed`, R3-C `127 passed`, R3-D/R3-E1
`61 passed`, bootstrap `8 passed`, FIRE/Goals/Planning `629 passed`, Smart
Financial Context R2 `121 passed`, and complete units `1101 passed, 2 failed`.
The two failures remain the named Investments/MagicMock baseline. The review
returned 0 blocking, 0 material, 0 minor, 2 new informational findings, and 5
preserved findings: `INF-R3E2-01` aggregate in-memory accumulation and
`INF-R3E2-02` future-test dependence on `MockTransport` or equivalent
injection; `INF-R3D-01`, `INF-R3D-02`, and `INF-R3E1-01` through
`INF-R3E1-03` remain unresolved. R3-E2 is `IMPLEMENTED / TESTED /
INDEPENDENTLY APPROVED / CHECKPOINT AUTHORIZED` and is now closed/pushed. R3-E3
is `IMPLEMENTED / TESTED / INDEPENDENTLY APPROVED / READY FOR CHECKPOINT`;
R3-E4 is `READY / NOT STARTED`.

#### R3-E3 executable validation record

R3-E3 tests the internal governed-ingestion composition without a public
trigger, live HTTP, or active-database access. The `34` focused tests cover all
five registry keys through `httpx.MockTransport`, explicit ordinary and bounded
historical intents, exact DAILY 90-day and MONTHLY 24-civil-month revisit
windows and floors, provider-complete-before-persistence ordering, deferred-only
store calls, empty evidence, all four derived global outcomes, discontinuous
success/failure/success plans, first/mid-observation persistence failure,
simulated interruption between chunks, prior-coverage preservation, A→A and
A→B→A history, stale and failed finalization, and independent-reader visibility
only after the finalization commit. Corrupt provider evidence is rejected before
store mutation.

Current evidence is R3-E3 `34 passed`, R3-C `127 passed`, R3-D/R3-E1 `61
passed`, R3-E2 `70 passed`, bootstrap `8 passed`, FIRE/Goals/Planning `629
passed`, and the selected current R2 Smart Context suite `153 passed`. Complete
units report `1135 passed, 2 failed`; both failures are the unchanged
Investments/MagicMock timeline baseline. The combined R3-E3 plus R3-D/R3-E1
selection reports `95 passed` on the retained SQLAlchemy 2.0.21 environment.
All persistence tests used disposable migrated SQLite databases; no live BCB
request or active financial database access occurred. Gemini 3.8 Flash High
independently approved R3-E3 with 0 blocking, 0 material, 0 minor, 0 new
informational findings, and the 7 preserved R3-D/R3-E1/R3-E2 findings. The
review reproduced the listed gates on Python 3.14.0, SQLite 3.50.4, and
SQLAlchemy 2.0.51. The isolated SQLAlchemy 2.0.21 `95 passed` result remains
implementation evidence; it was not attributed to the independent review.

- R3-E owns mocked BCB/SGS transport: allowlisted series, inclusive date bounds,
  daily ten-year partitioning, monthly normalization, response limits,
  malformed payloads, unit conflicts, timeout/DNS/429/4xx/5xx, bounded retry,
  partial chunks, SSRF prevention, privacy, and safe logging.
- R3-F owns explicit purpose and `as_of`, historical replay, provenance/status
  preservation, cross-purpose isolation, no hidden defaults, no SQL in the
  composer, no internal HTTP, no financial writes, and OpenAPI/engine
  compatibility.
- R3-G, only if separately activated, owns focused existing-yfinance
  regression, Decimal/provenance/error remediation, removal of invented FX
  fallback only after impact approval, and ADR-023 protection. R3-H owns Focus
  expectation tests only if separately activated and is otherwise deferred,
  not implemented. R3-I independently repeats contract/code, migration, provider,
  security, authority, no-float, no-default, and regression gates.
- Automated suites use deterministic fixtures and mocks; internet availability
  is never a pass condition.

### Phase 10.R4 — AI Runtime Foundation
- Test provider abstraction without financial-domain coupling, approved tool
  authorization, minimum context, secret absence, structured output, audit,
  timeout/error/cost telemetry, injection boundaries, and read-only behavior.
- Real provider calls are not the default automated-test strategy.

### Phase 10.R5 — Design / Navigation / Theme
- Validate System/Light/Dark, persistence/system preference, semantic tokens,
  contrast, charts, reduced motion, keyboard/focus, responsive layouts, living
  states, deep links, and absence of financial-contract changes.

### Phase 10.R6 — Experience Recomposition
- Regress Goals, Health, Planning, and FIRE independently; verify smart values,
  provenance, source switching, contextual actions, and no duplicated engines.

### Phase 10.R7 — Independent Validation
- Use a fresh context to challenge architecture, documentation precedence,
  context semantics, external-data authority, AI/privacy/secrets, design/theme,
  navigation, recomposed journeys, and regressions before closing realignment.

### Historical 10.7 test input — superseded by 10.R3
- Unit: news sanitizer removes injection patterns
- Unit: BCB data parsing
- Integration: BCB mock HTTP
- Integration: news RSS mock
- Security: prompt injection test cases (10+ known patterns)
- Manual: verify external data labels/timestamps appear in UI

### Historical 10.8 test input — superseded by 10.R4
- Unit: OllamaProvider.complete (mock HTTP)
- Unit: GeminiProvider.complete (mock)
- Unit: InsightResponse schema validation (valid + invalid cases)
- Unit: fallback chain (primary fails → fallback triggered)
- Contract: structured output always conforms to schema
- Security: injection in context → sanitized before LLM
- Manual: run real briefing generation, verify content quality

### Historical 10.9 test input — superseded by 10.R4 / 10.R6
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
