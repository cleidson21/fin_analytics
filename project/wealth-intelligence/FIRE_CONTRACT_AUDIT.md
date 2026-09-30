# STATUS: AUDIT COMPLETE — PRESERVED AS DESIGN EVIDENCE

**Contract authority:** `FIRE_CONTRACT.md` / ADR-025

**Supersession note:** The user decisions recorded in Phase 10.4-B resolved the open alternatives in this audit. The analysis below remains historical evidence and is not the implementation contract.

# Phase 10.4-A — FIRE Contract & Source-of-Truth Audit

This document is analysis before contract lock. It proposes boundaries and candidate semantics for Retirement & Financial Independence (FIRE), but it is not an approved contract, ADR, implementation plan, or authorization to start Phase 10.4-B.

## 1. Executive conclusion

The repository can support a deterministic FIRE MVP without a second projection engine. The viable architecture is a thin FIRE domain layer that constructs and explains the FIRE-specific target, progress, gap, and conditional withdrawal capacity, then delegates monthly projection, target achievement, required contribution, nominal/real handling, and source-preserving initial wealth resolution to Planning 10.3.

The strongest source-of-truth boundary is:

- current wealth: one explicit Planning source, normally the guarded `INVESTMENT_PORTFOLIO_SNAPSHOT` or a `USER_PROVIDED_SCENARIO`;
- retirement spending: explicit user assumption;
- withdrawal rate: explicit annual fraction, never a silent 4% default;
- return, inflation, contribution, horizon/date: explicit Planning assumptions;
- FIRE target and progress: deterministic derived values;
- projected date and required contribution: results from the existing Planning solvers.

The current repository does not certify net worth, retirement spending, sustainable future contribution, retirement income offsets, future dividend income, future macro rates, tax effects, longevity, or probability of success. Those concepts must not be invented or silently inferred.

## 2. Authority and evidence reviewed

### Canonical Wealth Intelligence documents read in full

- `MASTER_PLAN.md`
- `CURRENT_STATE.md`
- `IMPLEMENTATION_ROADMAP.md`
- `DECISION_LOG.md`
- `DATA_AND_SOURCE_OF_TRUTH.md`
- `PLANNING_UX_CONTRACT.md`
- `TESTING_STRATEGY.md`
- `README.md`

The optional project-root governance files named in the task were not present at the audited revision.

### Code and schema areas inspected

- Planning domain facts, assumptions, projection engine, target solver, required-contribution solver, Goal orchestration, readers, API DTOs, mappings, router, and portfolio source resolver.
- Goals enum, status, entity, ORM model, migrations, repository, DTOs, API, Planning reader, tests, and frontend representations.
- Financial Health certified query layer, deterministic services, API DTOs, routes, and tests.
- Investment portfolio snapshot model/migration, evolution endpoints, account/scope resolution, and the guarded Planning portfolio resolver.
- Dividend income-event model/migration and history, breakdown, and asset-detail read paths.
- Macro schema stub, benchmark files, MyProfit benchmark fields, and repository references.
- Profile birthdate behavior relevant to age/date semantics.

## 3. Existing domain boundaries

Planning 10.3 is the authority for monthly compounding, end-of-month contributions, target solving, minimum-cent required contribution, scenario comparison, rate conversion, nominal/real compatibility, inflation application, horizons, dates, and exact source provenance. FIRE must not copy those rules.

Goals currently define `RETIREMENT`, `FINANCIAL_INDEPENDENCE`, and `DIVIDEND_INCOME`, but generic Goal Planning deliberately returns `NOT_APPLICABLE` for those types. This is a reserved boundary for Phase 10.4, not missing authorization to reinterpret the existing Goal fields.

Financial Health exposes classified realized cashflow. It does not certify a retirement budget or sustainable future contribution. Investments expose investment wealth and historical investment facts. They do not expose net worth. Dividend data are realized historical events. Macro data are historical fields/files or an unused schema stub, not certified future assumptions.

## 4. Current FIRE-relevant data inventory

### Planning

- `InitialWealthFact` preserves source, scope, amount, as-of information, and provenance.
- One initial wealth source is selected; sources are not summed or silently substituted.
- `ForwardProjectionEngine` calculates deterministic monthly projections.
- `TargetAchievementSolver` finds the first target crossing and handles period-zero achievement.
- `RequiredContributionSolver` finds the minimum cent-level monthly contribution by delegating target tests.
- `ProjectionAssumptions` owns return basis, output mode, inflation, contribution, horizon/date, and timing validation.
- Public Planning financial values cross the API as decimal strings.

### Goals

- Exact types include `RETIREMENT`, `FINANCIAL_INDEPENDENCE`, and `DIVIDEND_INCOME`.
- Available fields include `target_amount`, `target_date`, `current_amount`, `monthly_contribution`, lifecycle `status`, `priority`, `linked_account_id`, and opaque `assumptions_json`.
- Goal CRUD currently uses float DTO/entity boundaries; the Planning Goal reader separately converts persisted numeric values directly to `Decimal`.
- There is no currency field.
- `assumptions_json` is syntax-validated opaque JSON and is not a canonical FIRE or Planning assumption store.
- Goal `progress_pct` clamps at 100%; this is a generic display behavior and should not define FIRE progress semantics.

### Financial Health

- Source: classified transactions only, using transaction date and `[start_date, end_date)` periods.
- Facts: monthly income, expense, net cashflow, savings amount, savings rate, category expenses, historical averages, trends, and anomaly classifications.
- Money aggregates are normalized to two decimals with `ROUND_HALF_EVEN`; downstream averages/ratios remain `Decimal`.
- Facts are realized historical cashflow. Missing months are not fabricated.
- The current query layer relies on the application's single-tenant SQLite premise because transactions lack a direct user ownership key.

### Investments

- `portfolio_snapshots.patrimonio` is monthly investment portfolio wealth with `Numeric(18,2)` precision.
- The snapshot identity is `(account_id, reference_month)` and repeated imports update the same month; it is not immutable point-in-time history.
- The guarded Planning resolver selects one owned MyProfit evolution scope, the latest eligible month at or before the requested month, and validates application-user and successful-run ownership.
- Public evolution endpoints are useful UI read paths but use float conversions and do not provide the same guarded Planning source contract.

### Dividends

- `income_events` stores realized payment events with payment date, asset, quantity, per-unit amount, gross amount, optional YOC/DY, run, and source.
- History is event-level and chronological; monthly/YTD aggregation is currently delegated to the frontend.
- Breakdown is all-time by asset.
- Asset detail computes a rolling 365-day total, but there is no certified portfolio-level trailing-12-month FIRE income read model.
- Some current investment read paths accept an optional `account_id` without the guarded ownership resolution used by Planning; FIRE must not treat them as certified user-scoped inputs.

### Macro

- `macro_indicators` exists as a simple SQL schema stub with `REAL` value and no active certified reader found.
- Historical CDI/IPCA/IBOV fields exist in imported portfolio snapshots; benchmark CSV files also exist.
- No certified current/future macro assumption model was found.

## 5. Source-of-truth matrix

| Concept | Candidate source | Current table / read model | Certified? | Precision | Temporal semantics | FIRE v1? | Automatic or explicit? | Main risk | Recommendation |
|---|---|---|---|---|---|---|---|---|---|
| Current eligible wealth | Planning portfolio resolver | `portfolio_snapshots.patrimonio` through `PlanningPortfolioSourceResolver` | Yes, within documented single-user/single-scope guard | `Numeric(18,2)` → `Decimal` | Latest eligible reference month at/before `as_of_date`; mutable monthly row | Yes | Explicit source selection, server-resolved | Calling investment wealth net worth; stale/mutable month | Primary server source; name it `eligible_investment_wealth` |
| Scenario wealth | Planning request | `USER_PROVIDED_SCENARIO` | User assertion, source-preserved; not certified external fact | Decimal string | Explicit `observed_at` | Yes | Explicit | User may include ineligible/non-investable assets | Label as user-provided FIRE-eligible wealth |
| Goal current amount | Owned Goal via Planning reader | `goals.current_amount` | Certified as the user's Goal fact, not as full portfolio wealth | Numeric → `Decimal` in Planning | Goal `updated_at`; no independent valuation date | Not by default | Explicit only if later approved | Double counting or confusing earmarked amount with total eligible wealth | Exclude from base FIRE v1; decide in Goal integration contract |
| Retirement expenses | None | No canonical table/read model | No | Candidate Decimal money | Scenario assumption as of analysis | Yes | Explicit | Current expenses are not retirement expenses | Require monthly retirement spending input |
| Health expense reference | Certified Health query | classified `transactions` / monthly history | Yes as realized history only | Aggregated two-decimal `Decimal` | Closed or requested calendar months | Optional later | Opt-in prefill requiring acceptance | Silent conversion of present spending into retirement budget | Do not use automatically; add only under a separate prefill contract |
| Withdrawal rate | None | None | No; it is an assumption | Decimal annual fraction | Scenario-wide | Yes | Explicit | “Safe” or guaranteed interpretation; silent 4% | Call `assumed_annual_withdrawal_rate`; no default |
| Expected return | Planning assumption | `ProjectionAssumptions.expected_return_rate` | Certified as explicit assumption, not observed truth | Decimal annual effective rate | Projection horizon | Yes | Explicit | Historical return used as forecast | Reuse Planning field and validation |
| Inflation | Planning assumption | `ProjectionAssumptions.inflation_rate` | Certified as explicit assumption | Decimal annual effective rate | Projection horizon | When selected matrix needs it | Explicit | Historical IPCA or double conversion | Reuse Planning; never infer |
| Future contribution | Planning scenario assumption | `scenario_monthly_contribution` | Certified as explicit scenario assumption | Nonnegative cent-scale Decimal | End of each projected month | Yes for date projection | Explicit | Confusing realized savings with future sustainable capacity | Reuse Planning; no Health auto-fill |
| Desired FI date | Explicit request; possible Goal date | Planning `target_date`; `goals.target_date` | User-owned date fact | ISO date | Resolved to Planning monthly horizon | Optional | Explicit | Ambiguity between Goal deadline and FIRE analysis date | Prefer explicit `target_date`; Goal reuse requires mode contract |
| Goal facts | Planning Goal reader | `goals` | Yes as owned persisted facts | Direct Numeric → Decimal in Planning | Created/updated timestamps; target date optional | Optional integration | Server-owned after explicit Goal selection | FIRE target silently overwriting user-owned target | Keep target ownership modes distinct |
| Historical dividends | Income events | `income_events` | Historical source facts exist; FIRE-grade aggregate/ownership boundary incomplete | Gross `Numeric(18,2)`; units/rates higher scale | Payment-date events; asset detail rolling 365 days | No base MVP | Never automatic | Dividend plus total-return double count; unstable future income | Defer to separate dividend-income contract |
| External retirement income | None | None | No | Candidate Decimal money | Would need start/end dates and indexation | No base MVP | Explicit only in later contract | Invented pension/rent/income; double counting spending budget | Defer |
| Macro indicators | Snapshot fields/files/schema stub | portfolio benchmarks, CSVs, `macro_indicators` | Historical/imported context only; no certified assumption reader | Mixed Numeric/REAL/CSV | Historical periods | No automatic use | Future opt-in only | Turning CDI/SELIC/IPCA history into forecasts | Context/defer |

## 6. Fact / assumption / derived-fact classification

| Class | Items |
|---|---|
| FACT | Resolved investment portfolio wealth and provenance; owned Goal fields; classified Health history; realized dividend events; historical imported benchmarks |
| ASSUMPTION | Retirement monthly spending; assumed annual withdrawal rate; expected annual return; inflation; scenario monthly contribution; desired date/horizon; any future external-income offset |
| DERIVED FACT | Annual retirement spending; FIRE target; target gap; progress ratio; conditional supported withdrawal; projected achievement date; months to target; required contribution |

“Derived fact” means deterministic output under explicitly echoed facts and assumptions. It does not turn the assumptions into observed truth.

## 7. Planning 10.3 reuse matrix

| FIRE requirement | Existing Planning component | Reuse directly? | Wrapper needed? | New FIRE logic? | Reason |
|---|---|---:|---:|---:|---|
| Target construction | None | No | FIRE domain service | Yes | Retirement spending / withdrawal-rate semantics are FIRE-specific |
| Monthly projection | `ForwardProjectionEngine` | Yes | Orchestration only | No | Certified compounding and contribution timing already exist |
| Achievement date | `TargetAchievementSolver` | Yes | Pass FIRE target and chosen source | No | First-crossing and period-zero semantics already exist |
| Required contribution | `RequiredContributionSolver` | Yes | Pass FIRE target/date template | No | Certified minimum-cent search already exists |
| Nominal/real | `ProjectionAssumptions` and target basis validation | Yes | FIRE input guidance | No | Existing matrix prevents basis mismatch |
| Inflation | Planning Fisher conversion | Yes | None beyond orchestration | No | Must be applied exactly once |
| Initial wealth | Planning selectors/readers/resolver | Yes | FIRE eligibility policy | No new source math | Existing one-source and provenance rules must hold |
| Provenance | `InitialWealthFact` and API mappings | Yes | Add expense/target assumption provenance | Yes, only for FIRE-specific inputs | Wealth provenance already exists; expense assumptions need their own echo |
| Scenario comparison | `ScenarioComparisonEngine` | Later/direct | FIRE target supplied to comparison | No duplicate comparison engine | Useful after base analysis; not required for smallest endpoint |

## 8. New FIRE domain logic

### Must be new FIRE logic

- Validate and normalize explicit retirement spending.
- Validate the assumed annual withdrawal rate.
- Construct the FIRE target.
- Calculate gap, unbounded progress ratio, and achieved/not-achieved summary.
- Calculate conditional supported annual/monthly withdrawal.
- Preserve and echo FIRE-specific assumptions and their origin.
- Orchestrate existing Planning components without replicating their calculations.

### Must reuse Planning

- Initial wealth resolution and its one-source rule.
- Projection, compounding, monthly rate conversion, and contribution timing.
- Target achievement and projected date.
- Required contribution.
- Nominal/real matrix, inflation conversion, target-value basis, horizons, precision, and source provenance.
- Scenario comparison if introduced later.

### Defer

- Probability of success, sequence-of-returns risk, Monte Carlo, longevity, tax engine, portfolio allocation, rebalancing, asset selection, dividend sustainability, automatic income offsets, macro-derived assumptions, and persistent FIRE profiles/scenarios.

## 9. Candidate FIRE definition and formula

### Proposed base definition

Financial independence is the condition in which `eligible_investment_wealth` is at least the capital target derived from an explicit retirement-spending assumption and an explicit assumed annual withdrawal rate. This is a deterministic scenario, not a guarantee that capital will last for a particular lifespan.

Candidate base formula:

```text
annual_required_spending = monthly_retirement_spending * 12
unrounded_fire_target = annual_required_spending / assumed_annual_withdrawal_rate
```

No income offset belongs in the base formula for v1. A future offset contract would need source, gross/net meaning, start/end dates, inflation behavior, reliability, and double-counting rules.

### Advantages

- Small, explainable, deterministic, and source-preserving.
- Separates FIRE meaning from Planning projection mechanics.
- Supports current progress, projected date, and required contribution with existing engines.

### Limits

- It is not actuarial and does not model lifespan, taxes, market paths, sequence risk, fees, or portfolio composition.
- The withdrawal rate is a user assumption, not a certified safe rate.
- The target is only meaningful in the declared nominal/real basis.

## 10. Expense semantics

| Option | Assessment |
|---|---|
| `USER_PROVIDED` | Recommended for MVP. The user explicitly states desired monthly retirement spending. Clear ownership and no false inference. |
| `HEALTH_REFERENCE` | Legitimate later opt-in prefill. Must show reference months and require explicit acceptance/editing before becoming an assumption. |
| `HEALTH_AUTOMATIC` | Reject. Realized current expenses do not establish future retirement spending and may include temporary, omitted, or retirement-irrelevant items. |

Recommended public input: monthly BRL spending, two decimal places. Internal annual normalization is exact Decimal multiplication by 12. The backend should not accept monthly and annual fields simultaneously in the same mode.

## 11. Withdrawal-rate semantics

Use `assumed_annual_withdrawal_rate`: a finite Decimal annual fraction strictly greater than zero and strictly less than one. This is the broad mathematical domain, not product guidance about sensible values. The product must not label the rate “safe,” “guaranteed,” or silently default it to 4%.

If the product later offers examples or reference ranges, that requires a separate evidence and guidance decision. Such guidance must remain distinguishable from the user's selected assumption.

## 12. Current wealth and exclusions

Recommended field name: `eligible_investment_wealth`. It accurately describes `portfolio_snapshots.patrimonio` and avoids the unsupported term “net worth.”

The automatic source excludes anything not represented by the selected investment snapshot, including residence, vehicles, private business value, and other non-financial property. FIRE v1 should not synthesize or estimate those assets.

No reliable repository fact identifies an emergency-reserve portion inside the portfolio. Therefore v1 must not automatically subtract an emergency reserve or infer it from an `EMERGENCY_RESERVE` Goal. Base MVP should include the chosen snapshot as-is. A future explicit excluded-amount mode is possible but adds reconciliation and double-counting decisions and should be deferred.

## 13. Progress and withdrawal capacity

Candidate derived values:

```text
gap_to_fire = max(fire_target - eligible_investment_wealth, 0)
progress_ratio = eligible_investment_wealth / fire_target
supported_annual_withdrawal = eligible_investment_wealth * assumed_annual_withdrawal_rate
supported_monthly_withdrawal = supported_annual_withdrawal / 12
```

Do not clamp `progress_ratio`; a value above 1 is useful information. Status communicates that the target is reached. A valid base request requires positive spending and a positive withdrawal rate, so the target cannot be zero. Withdrawal capacity is conditional on the assumed rate and must not be described as guaranteed income.

## 14. Projected FIRE date and required contribution

The code supports the preferred composition:

```text
FIRE target construction
  → Planning TargetAchievementSolver
  → projected achievement date / months / status
```

For a desired FI date:

```text
FIRE target construction
  → Planning RequiredContributionSolver
  → minimum cent-level scenario contribution
```

FIRE must not implement its own compound-growth loop, target crossing, or binary search.

## 15. Nominal/real options

### Option A — real-first FIRE

Retirement spending and target are stated in today's BRL, projection output is real, and expected return is real. Inflation is not needed for the basic path. This is the clearest MVP experience and minimizes basis errors.

### Option B — explicit nominal/real matrix

Expose the existing Planning matrix: nominal→nominal, nominal→real with explicit inflation, and real→real. This is more capable but asks users to understand more assumptions.

### Option C — nominal only

Simpler in appearance but makes long-horizon retirement spending harder to interpret and can invite silent inflation errors. Not recommended.

Recommendation: lock a real-first basic path while retaining Planning's explicit matrix as an advanced mode or staged extension. User approval is required because Option B is also architecturally valid. In every option, the FIRE target basis must match Planning's target/output basis.

## 16. Return, inflation, and contribution semantics

- Expected return is an explicit effective annual Planning assumption. Historical portfolio return, CDI, SELIC, or dividend yield must never populate it automatically.
- Inflation is an explicit effective annual Planning assumption only when required by the selected nominal/real transformation. Historical IPCA must never populate it automatically.
- Monthly contribution is an explicit future scenario contribution. Historical savings, net cashflow, or Goal contribution may be shown as context later, but cannot silently become sustainable capacity.
- `END_OF_MONTH` contribution timing remains the current certified Planning contract.

## 17. Goal integration and target ownership

The cleanest initial ownership model is two explicit modes:

1. `CALCULATED_FIRE_TARGET`: FIRE derives the target from spending and withdrawal rate. It does not overwrite `goal.target_amount`.
2. `MANUAL_WEALTH_TARGET`: an existing Goal or explicit target can use Planning, but must not be presented as a FIRE target derived from withdrawal semantics.

Recommended FIRE Goal integration:

- `RETIREMENT` and `FINANCIAL_INDEPENDENCE` may link to a FIRE analysis after a contract is approved.
- `target_date` can represent the desired FI date when the user explicitly chooses the Goal-linked mode.
- `monthly_contribution` may be an explicit prefill, but must be confirmed as a scenario assumption.
- `current_amount` should not be the default FIRE wealth. It may be earmarked or manually maintained and can double count the investment portfolio.
- A calculated FIRE target must not silently replace the user-owned `target_amount`; synchronization requires an explicit command and persistence decision.
- `assumptions_json` must not become a FIRE contract store by convenience.

## 18. Date versus age

No server-owned birthdate source exists. The profile page has a birthdate field only in ephemeral component state; sensitive fields are deliberately excluded from local persistence. Therefore FIRE v1 should use `target_date`, not target age. Age may be a presentation-only value derived from a user-provided birthdate in a future privacy-aware contract.

## 19. Retirement income offsets

Base MVP should exclude offsets. The repository cannot certify future INSS/pension, rent, business income, or other retirement income. A later explicit user-provided offset is possible only with amount, gross/net basis, recurrence, start/end dates, indexation, and provenance. Dividend income from the same projected portfolio is not an independent offset under a total-return projection.

## 20. Dividends and “living from dividends”

Realized dividend history exists, but a future sustainable dividend-income contract does not. “How much capital do I need to live from dividends?” is not automatically equivalent to withdrawal-rate FIRE. It needs a separate model covering eligible assets, yield definition, sustainability, tax, reinvestment, variability, and whether price appreciation is included.

Recommendation: make dividend-income independence a later specialized contract, coordinated with Phase 10.5 Portfolio Intelligence because it depends on portfolio composition and sustainable income analysis. It may be surfaced under the broader 10.4 product area later, but it must not enter the base FIRE calculation.

## 21. Double-counting risks

| Risk | Failure mode | Required guard |
|---|---|---|
| Dividends + total return | Projected total return already includes distributions economically, then dividend income is added again | Base FIRE excludes derived dividends; any future income model must declare price-return versus total-return basis |
| Emergency reserve + portfolio | A Goal balance is added to a snapshot that already contains the same assets | One initial wealth source only; no source summation; no automatic reserve adjustment |
| Goal current amount + portfolio | Earmarked Goal amount may be a subset or duplicate of portfolio wealth | Never add them; require one explicit source |
| External income + expense budget | User may already have entered spending net of pension/rent and then subtract the income again | Future contract must declare gross expense and offsets separately, with an explicit no-double-count acknowledgement |
| Inflation twice | Expenses/target are inflation-adjusted and Planning also converts nominal to real | Target basis must equal Planning output basis; one conversion authority only |
| Nominal/real conversion twice | FIRE pre-converts return, then Planning applies Fisher conversion | FIRE passes declared rates/basis; Planning remains sole rate conversion authority |

This table is a contract gate, not optional documentation.

## 22. Taxes, longevity, probability, and FIRE flavors

- Taxes: current data do not support withdrawal-tax modeling. Treat spending as the amount the portfolio scenario is intended to support; whether that is gross or net must be made explicit in UI language. Defer a tax engine.
- Longevity: withdrawal-rate FIRE is not a life-expectancy or survival model. Do not request death age or claim lifetime sufficiency.
- Monte Carlo: defer probability of success and sequence-of-returns risk. The initial contract remains deterministic.
- Lean/Fat/Barista FIRE: defer. Today these would mostly be labels over uncontracted spending or income-offset semantics.
- Coast FIRE: conceptually valid and reusable through Planning with zero future contribution, but it needs its own target/basis questions. Make it a later 10.4 subphase, not the MVP.

## 23. Macro data

CDI, SELIC, and IPCA cannot become future FIRE assumptions automatically. Current repository evidence is historical imported context, files, or an unintegrated schema stub. A future reference selector could let the user opt in to a sourced value, but it must disclose observation period, provenance, and that selection converts the reference into a user-approved scenario assumption.

## 24. Precision and rounding candidates

- API boundary: finite plain decimal strings, matching Planning.
- Money inputs: two decimal places; no float authority.
- Rates and ratios: `Decimal`; preserve sufficient internal precision and serialize as strings.
- Monthly-to-annual spending: exact multiplication by `Decimal(12)`.
- FIRE target division: calculate at an adaptive/sufficient Decimal precision; final monetary target requires a user-approved rounding rule.
- General money outputs and withdrawal capacity: two decimals with `ROUND_HALF_EVEN`, consistent with Planning.
- Progress ratio: do not quantize as money; preserve Decimal result and let presentation format it.

Two legitimate target-rounding choices remain. `ROUND_HALF_EVEN` maximizes consistency with Planning money. `ROUND_CEILING` produces the minimum whole cent that is not below the mathematical requirement. Recommendation: use `ROUND_CEILING` only for the final positive FIRE target and retain `ROUND_HALF_EVEN` for all ordinary money outputs. This exception must be explicitly locked before implementation.

## 25. Temporal semantics and provenance

- Analysis `as_of_date` is the Planning period-zero anchor.
- Portfolio wealth keeps its actual `reference_month`, run/source, and created/updated provenance. The system must not invent `observed_at`.
- Explicit spending and withdrawal-rate assumptions are effective for the submitted scenario as of the analysis; their source is `USER_PROVIDED`.
- If Health prefill is added later, its reference months must remain visible and distinct from the portfolio reference month.
- Different source dates may be allowed with preserved provenance and a stale/misaligned-source warning; they must never be presented as one common observation instant.
- Projection begins at `as_of_date`, not at the snapshot's month, while the response must expose the difference.

## 26. Candidate status model

Avoid cloning Planning statuses. A composed response can contain:

- FIRE summary status: `ALREADY_FINANCIALLY_INDEPENDENT` or `BELOW_FIRE_TARGET`.
- Nested Planning target status: existing `ALREADY_ACHIEVED`, `ACHIEVED`, `UNREACHABLE`, or `NOT_REACHED_WITHIN_HORIZON`.
- Desired-date assessment, if Goal-style timing is approved: reuse existing semantic outcomes `PROJECTED_EARLY`, `PROJECTED_ON_TIME`, `PROJECTED_LATE`, and `NOT_REACHED_WITHIN_HORIZON` through an orchestration mapping rather than a second solver.
- Request-level missing facts should be validation errors, not fabricated `INSUFFICIENT_DATA`, unless a later read-oriented endpoint needs a partial-result status.

## 27. Edge-case matrix

| Edge case | Candidate behavior |
|---|---|
| Withdrawal rate = 0 | Reject; division undefined |
| Negative withdrawal rate | Reject |
| Withdrawal rate >= 1 | Reject under proposed product domain |
| Expenses = 0 | Reject for base FIRE analysis; no meaningful positive FIRE target |
| Negative expenses | Reject |
| Wealth = 0 | Valid; progress 0 and full gap |
| Wealth > target | Valid; unbounded ratio > 1 and achieved status |
| Target = 0 | Cannot arise from valid base inputs; reject manual FIRE target if zero |
| Contribution = 0 | Valid Planning scenario |
| Negative expected return | Valid only within existing Planning constraint `> -1` and declared basis |
| Zero expected return | Valid |
| Very high target | Use Decimal; Planning horizon/status governs reachability; no float overflow |
| Target already reached | FIRE achieved; Planning period-zero `ALREADY_ACHIEVED` |
| No portfolio snapshot | Source-resolution error; user may explicitly choose a user-provided scenario |
| Future-only snapshot | Not eligible for the selected `as_of_date`; source-resolution error |
| Missing expenses | Validation error |
| Missing desired date | Base target/progress can still work; required-contribution-to-date analysis unavailable |
| Real/nominal mismatch | Reject through existing Planning target-basis checks |

## 28. Architecture options

### Option A — thin FIRE orchestration layer

Components: a small deterministic FIRE target/progress service, a FIRE application orchestrator, existing Planning source resolution and solvers, and FIRE-specific DTO composition.

Benefits: no duplicated projection math, strong provenance, small testing surface, consistent precision/status behavior, and low contract drift. FIRE remains responsible only for FIRE meaning.

### Option B — independent FIRE engine with projection math

Components: new target logic plus separate compounding, target-date, required-contribution, rate, and rounding implementations.

Costs: duplicated certified logic, divergent edge cases and statuses, larger tests, inconsistent nominal/real behavior, and future maintenance risk. There is no repository evidence that justifies this duplication.

### Recommendation

Choose Option A. A thin FIRE target service is new domain logic; everything that evolves wealth over time remains Planning.

## 29. Candidate API shape — not approved

One composed endpoint is sufficient for an MVP:

```text
POST /api/v1/fire/analysis
```

Candidate request:

```json
{
  "initial_wealth": {
    "source": "INVESTMENT_PORTFOLIO_SNAPSHOT"
  },
  "as_of_date": "YYYY-MM-DD",
  "monthly_retirement_spending": "10000.00",
  "assumed_annual_withdrawal_rate": "0.035",
  "projection_assumptions": {
    "scenario_monthly_contribution": "2000.00",
    "expected_return_rate": "0.05",
    "return_type": "REAL",
    "output_mode": "REAL",
    "inflation_rate": null,
    "horizon_months": 600,
    "target_date": null,
    "rate_basis": "EFFECTIVE_ANNUAL",
    "contribution_timing": "END_OF_MONTH"
  },
  "desired_fire_date": null
}
```

Values above illustrate shape only; they are not defaults or guidance.

Candidate response groups:

- `as_of_date` and source provenance;
- echoed FIRE assumptions;
- `annual_retirement_spending`, `fire_target`, `eligible_investment_wealth`, `gap_to_fire`, `progress_ratio`;
- `supported_annual_withdrawal` and `supported_monthly_withdrawal`;
- FIRE summary status;
- nested existing Planning target-achievement result;
- optional required-contribution result when a desired date is requested;
- explicit basis and warnings.

Specialized endpoints could be added later, but splitting target, progress, date, and contribution now would repeat source resolution and invite inconsistent assumptions.

## 30. Persistence options

| Option | Assessment |
|---|---|
| Transient calculations | Recommended MVP; matches Planning 10.3 and avoids premature schema ownership |
| Reuse Goal persistence | Possible only after target-ownership and synchronization decisions; do not store derived FIRE target silently |
| New FIRE profile/config | Not justified for MVP; introduces lifecycle, versioning, and stale-assumption concerns |
| Persist assumptions later | Valid future capability after scenario persistence is contracted across Planning/FIRE |

## 31. Frontend implications without UI design

### Basic inputs

- Wealth source selection.
- Monthly retirement spending.
- Assumed annual withdrawal rate.
- Scenario monthly contribution.
- Expected annual return.
- Horizon or desired FI date.

### Advanced assumptions

- Nominal/real mode and explicit inflation when applicable.
- User-provided wealth and observation time.
- Scenario comparison.
- Future opt-in Health reference, only after a separate contract.

### Server-owned facts

- Resolved portfolio wealth and provenance.
- Owned Goal facts when explicitly linked.
- Planning-derived projection, achievement, and required-contribution outputs.

Progressive disclosure should make a real-first basic path concise, while advanced users can access the full Planning basis matrix. The frontend presents facts and assumptions; it does not calculate authoritative financial results.

## 32. Minimum user flow candidate

1. Select portfolio snapshot or user-provided eligible wealth.
2. Enter desired monthly retirement spending.
3. Enter the assumed annual withdrawal rate.
4. Enter contribution and expected return for projection.
5. Choose horizon or desired FI date.
6. Review source dates, assumptions, target, progress, and Planning results.

## 33. Questions FIRE v1 should answer

- How much investment wealth would this spending and withdrawal-rate scenario require?
- What percentage of that target does the selected eligible investment wealth represent?
- What is the remaining gap?
- What monthly/annual withdrawal would current eligible wealth conditionally support at the assumed rate?
- When does the existing Planning model project the target will be reached?
- What monthly scenario contribution would Planning require to reach it by a chosen date?

## 34. Questions outside the MVP

- Which asset or portfolio should the user buy?
- What is the ideal FIRE allocation or rebalance?
- Which dividends are safe or sustainable?
- What withdrawal rate is guaranteed?
- What is the probability that money lasts 40 years?
- What tax strategy or pension benefit should be assumed?
- What is the user's certified net worth?

## 35. Phase boundaries

Phase 10.5 remains responsible for Portfolio Intelligence. FIRE may consume a certified investment-wealth fact but cannot recommend allocation, concentration changes, rebalancing, assets, or trades.

Future Copilot may explain deterministic FIRE results and disclosed assumptions. It cannot calculate authoritative targets, choose rates, change assumptions, persist decisions, or manufacture financial truth.

## 36. Recommended to lock

1. Thin FIRE domain/orchestration layer; no duplicate projection engine.
2. Planning remains sole authority for projection, target achievement, required contribution, nominal/real conversion, inflation, contribution timing, and scenario comparison.
3. Automatic wealth is investment wealth, never labeled net worth.
4. Exactly one explicit wealth source per analysis; never sum Goal and portfolio sources.
5. Explicit monthly retirement spending as the MVP expense assumption.
6. Explicit annual withdrawal-rate fraction with no default and no “guaranteed safe” wording.
7. Deterministic target, progress, gap, and conditional withdrawal-capacity outputs.
8. No automatic Health expense/contribution assumptions.
9. No dividend income added to a total-return projection.
10. No automatic macro-derived return or inflation.
11. Transient calculations first.
12. Decimal-string API boundary and preserved provenance.
13. Target date rather than target age in v1.
14. No taxes, longevity, Monte Carlo, portfolio recommendations, or LLM calculations in the base contract.

## 37. User decision required

### Decision 1 — nominal/real product surface

- Question: Should the MVP expose only a real-first basic FIRE path or the complete Planning nominal/real matrix immediately?
- Option A: Real-first basic path, advanced matrix later.
- Option B: Full explicit Planning matrix from the first FIRE endpoint/UI.
- Recommendation: Option A, while keeping the backend composition compatible with Option B.
- Reason: retirement spending is naturally understood in today's BRL and the simpler path reduces basis errors without changing Planning authority.

### Decision 2 — final FIRE-target cent rounding

- Question: How should the positive quotient `annual_spending / withdrawal_rate` become a two-decimal monetary target?
- Option A: `ROUND_CEILING` to the minimum cent not below the mathematical requirement.
- Option B: `ROUND_HALF_EVEN` for complete consistency with ordinary Planning money.
- Recommendation: Option A for the target only; retain `ROUND_HALF_EVEN` elsewhere.
- Reason: a minimum required target should not round below sufficiency, but this is a deliberate exception to the prevailing money rule.

### Decision 3 — Goal linkage in the MVP

- Question: Should the first FIRE contract accept an optional `RETIREMENT`/`FINANCIAL_INDEPENDENCE` Goal, or remain standalone and transient?
- Option A: Standalone transient analysis first; Goal link in a following subphase.
- Option B: Optional owned Goal link from the first endpoint, with explicit date/contribution prefills and no silent writes.
- Recommendation: Option A.
- Reason: the base math needs no persistence, while Goal target ownership and synchronization require a distinct write contract.

### Decision 4 — Health expense reference

- Question: Should the first UI offer certified historical Health expenses as an opt-in prefill?
- Option A: Explicit spending only in MVP.
- Option B: Offer a provenance-rich historical reference that the user must accept/edit.
- Recommendation: Option A for the initial contract, Option B as an immediately following enhancement.
- Reason: Health is certified as history, but reference-window selection and mismatched source dates add contract surface.

### Decision 5 — emergency-reserve treatment

- Question: Should v1 use selected investment wealth as-is or accept a user-provided excluded amount?
- Option A: Use the selected wealth fact as-is and disclose its scope.
- Option B: Accept an explicit nonnegative excluded amount with separate provenance.
- Recommendation: Option A.
- Reason: no certified reserve-identification fact exists, and an exclusion field can create reconciliation ambiguity.

## 38. Deferred decisions and capabilities

- External retirement-income offsets and their time/indexation model.
- Dividend-income independence and sustainability.
- Health-based spending and contribution prefills.
- Goal write/synchronization behavior and persistent FIRE configurations.
- Target age and birthdate persistence/privacy contract.
- Emergency-reserve exclusions.
- Coast FIRE and other FIRE variants.
- Tax, fee, longevity, Monte Carlo, and sequence-risk models.
- Macro reference selectors and evidence-backed product guidance.
- Portfolio Intelligence, asset selection, allocation, and rebalancing.

## 39. Risks and source-of-truth gaps

### Principal risks

- Users may interpret a deterministic withdrawal-rate scenario as a guarantee.
- Mutable monthly portfolio snapshots can change after an earlier analysis.
- Current investment endpoints do not all enforce the guarded ownership path used by Planning.
- Existing Goals expose float DTO/entity boundaries, so FIRE must use Decimal-safe readers or new strict boundaries.
- Long horizons amplify basis and rounding misunderstandings.
- Mixing source dates without clear provenance can imply false contemporaneity.

### Source-of-truth gaps

- No certified net-worth model.
- No retirement-spending fact.
- No sustainable-contribution-capacity fact.
- No future retirement-income source.
- No certified future dividend-income model.
- No active certified macro assumption reader.
- No server-owned birthdate.
- No tax, longevity, or probability model.
- No unambiguous mapping from Goal balances to portfolio assets.

None of these gaps blocks the recommended minimal transient contract because its missing values are explicit assumptions or deferred features. They do block broader claims.

## 40. Proposed FIRE MVP contract summary — candidate only

A transient authenticated analysis accepts one explicit Planning wealth selector, an `as_of_date`, positive monthly retirement spending, a positive annual withdrawal-rate fraction below one, and the explicit Planning assumptions required for projection. A thin FIRE service derives annual spending, a two-decimal FIRE target under the approved rounding rule, gap, unbounded progress ratio, achieved summary, and conditional withdrawal capacity. The application layer passes the same resolved wealth fact and FIRE target to Planning's existing target-achievement solver and, when a desired date is supplied, its required-contribution solver. The response serializes all financial values as strings, echoes all assumptions, preserves wealth and temporal provenance, states value basis, and never labels the result guaranteed, safe, net worth, or future income truth.

This candidate remains subject to the five user decisions above. No production implementation is authorized by this document.

## 41. Audit disposition

- Phase 10.3 Planning: `VALIDATED / CLOSED`.
- Post-10.3 Planning UX: `VALIDATED / CLOSED`.
- Phase 10.4: `CONTRACT AUDIT — AWAITING USER REVIEW`.
- Production files changed: none.
- Test files changed: none.
- Migrations: none.
- Endpoints: none.
- Frontend: none.
- Next step: user review before Phase 10.4-B FIRE contract lock.
