# STATUS: LOCKED / APPROVED FOR IMPLEMENTATION

# AUTHORITY: ADR-025

# Phase 10.4 — FIRE MVP Contract

**Locked:** 2026-09-29

**Scope:** Retirement & Financial Independence deterministic MVP

**Implementation status:** NOT STARTED

This document is the canonical implementation contract for the Phase 10.4 FIRE MVP. It authorizes later implementation decomposition only after user review. It does not itself authorize production changes.

## 1. Purpose and definition

FIRE v1 answers deterministic questions about financial independence under explicit user assumptions. Financial independence means that one selected amount of eligible investment wealth is at least the real purchasing-power target derived from:

- explicit desired monthly retirement spending; and
- an explicit assumed annual withdrawal rate.

The result is conditional on supplied facts and assumptions. It is not a guarantee of retirement readiness, safe income, portfolio durability, lifespan coverage, or investment performance.

## 2. Architecture lock

FIRE is a thin deterministic domain and application orchestration layer.

FIRE owns only:

- retirement-spending and withdrawal-rate validation;
- FIRE target construction;
- FIRE summary facts, gap, progress, and conditional withdrawal capacity;
- mode validation;
- composition of existing Planning facts and results.

Planning 10.3 remains the sole authority for:

- initial-wealth resolution and provenance;
- monthly projection and compound-equivalent monthly rates;
- contribution recurrence and `END_OF_MONTH` timing;
- partial-current-month and calendar semantics;
- target achievement;
- required contribution;
- nominal-to-real Fisher conversion;
- projection precision and monetary recurrence;
- solver statuses and results.

A second FIRE projection, target-crossing, or required-contribution engine is prohibited.

## 3. Public capability and authentication

The MVP exposes one authenticated calculation capability:

```text
POST /api/v1/fire/analysis
```

It uses the same current-user authentication semantics as Planning. The endpoint is transient and read-only: POST represents a structured calculation request, not persistence.

The Planning portfolio resolver remains inside its existing ADR-023 guarded single-user/single-tenant contract. FIRE must not invent general multi-user account ownership.

## 4. Analysis types

The public `analysis_type` values are exactly:

- `SUMMARY`
- `PROJECTED_DATE`
- `REQUIRED_CONTRIBUTION`

Every analysis returns the FIRE summary. Exactly one mode-specific result section may additionally be populated.

There is no scenario-comparison mode, Goal mode, age mode, dividend mode, Coast FIRE mode, or portfolio-advice mode in v1.

## 5. Initial wealth contract

The request selects exactly one `initial_wealth` source. Eligible sources are limited to the existing Planning shapes below.

### 5.1 Investment portfolio source

```json
{
  "source": "INVESTMENT_PORTFOLIO_SNAPSHOT"
}
```

This selector delegates entirely to `PlanningPortfolioSourceResolver` under ADR-023. The client does not supply `account_id`, `run_id`, amount, reference month, currency, scope, or certified provenance.

The resolved amount is conceptually `eligible_investment_wealth`. It represents BRL investment portfolio wealth in the current guarded deployment. It is not net worth, consolidated personal wealth, a real-time valuation, or guaranteed withdrawable capital.

### 5.2 User-provided source

```json
{
  "source": "USER_PROVIDED_SCENARIO",
  "amount": "250000.00",
  "observed_at": "2026-09-29T10:30:00-03:00"
}
```

This reuses `UserProvidedInitialWealthRequestDTO` semantics. `amount` and `observed_at` are both explicit and required. The backend manufactures neither a timestamp nor certified provenance. The amount is a user assertion in the current single-BRL application context.

### 5.3 Prohibited wealth sources and aggregation

- `GOAL_CURRENT_AMOUNT` is not accepted by FIRE v1.
- Goal current amount and portfolio wealth are never added.
- Multiple wealth sources are never merged or used as fallbacks.
- Positions, quotes, cashflow, emergency-reserve Goals, and other assets are not added to the snapshot.
- No emergency-reserve amount is subtracted automatically.

## 6. FIRE assumptions

### 6.1 Monthly retirement spending

`monthly_retirement_spending` is the user's desired monthly spending during financial independence, expressed in the current purchasing-power basis of the real analysis.

It must be:

- a finite plain `DecimalString`;
- strictly greater than zero;
- declared with at most two decimal places.

Invalid fractional-cent input is rejected, not rounded.

```text
annual_required_spending = monthly_retirement_spending * Decimal(12)
```

The multiplication is exact. `annual_required_spending` is emitted with two decimal places.

This assumption is not inferred from current spending, Health history, budgets, cashflow, savings rate, salary, or Goals.

### 6.2 Assumed annual withdrawal rate

`assumed_annual_withdrawal_rate` is an explicit annual Decimal fraction:

- finite;
- strictly greater than zero;
- strictly less than one.

Examples of representation only: `"0.04"` means 4%; `"0.035"` means 3.5%. There is no default or recommended value in the contract.

The field must never be named or described as a guaranteed or safe rate. Future user-facing language should use “taxa anual de retirada assumida” or equivalent conditional wording.

## 7. Canonical FIRE target

The canonical formula is:

```text
annual_required_spending = monthly_retirement_spending * 12
raw_fire_target = annual_required_spending / assumed_annual_withdrawal_rate
fire_target = quantize(raw_fire_target, Decimal("0.01"), ROUND_CEILING)
```

`ROUND_CEILING` is a FIRE-specific exception used only for the positive canonical target so that the target never falls below the mathematical requirement because of cent rounding.

The canonical `fire_target`, not `raw_fire_target`, is:

- displayed to the user;
- used in gap and progress calculations;
- passed as `target_amount` to Planning solvers.

Planning's general `ROUND_HALF_EVEN` money rules remain unchanged.

## 8. Real-basis lock

FIRE v1 target, summary, and output basis are always `REAL`, in purchasing power at `as_of_date`.

Planning composition always uses:

- `output_mode = REAL`;
- `target_value_basis = REAL`;
- `rate_basis = EFFECTIVE_ANNUAL`;
- `contribution_timing = END_OF_MONTH`.

These are locked operational semantics, not user-selected defaults.

FIRE v1 does not expose `NOMINAL → NOMINAL` or `REAL → NOMINAL`, and it does not construct a future nominal FIRE target.

## 9. Return and inflation matrix

`expected_return_rate` maps directly to Planning's finite effective annual Decimal fraction and must be greater than `-1`. Zero and negative rates above `-1` are valid. There is no positive cap and no default.

| `return_type` | FIRE `output_mode` | `inflation_rate` | Result |
|---|---|---|---|
| `REAL` | fixed `REAL` | Forbidden | Planning uses the supplied real return directly |
| `NOMINAL` | fixed `REAL` | Required | Planning applies Fisher conversion exactly once |

`inflation_rate`, when required, is a finite Decimal fraction greater than `-1`. It has no default and is never inferred from IPCA, an official target, macro history, or portfolio benchmarks.

Historical portfolio return, CDI, SELIC, IBOV, dividend yield, Health trends, and other observed values never become `expected_return_rate` automatically.

## 10. Contribution semantics

The public projection-mode field uses the established Planning name `scenario_monthly_contribution`.

It is an explicit future scenario assumption and inherits Planning validation: finite nonnegative Decimal money with at most two decimal places. Zero is valid.

It is not derived from Health savings, net cashflow, salary, historical investment flows, Goal contribution, or sustainable capacity.

In `REQUIRED_CONTRIBUTION`, the client must not supply this field because it is the requested output. The application constructs the Planning assumptions template with `scenario_monthly_contribution = Decimal("0.00")` solely as the neutral placeholder required by the existing solver contract. `RequiredContributionSolver` is already authoritative that the template contribution does not determine the answer. This internal value is not a user assumption and must not be presented as one.

## 11. Mode validation matrix

All common fields — `analysis_type`, `as_of_date`, `initial_wealth`, `monthly_retirement_spending`, and `assumed_annual_withdrawal_rate` — are required in every mode.

| Mode | `scenario_monthly_contribution` | `expected_return_rate` | `return_type` | `inflation_rate` | `horizon_months` | `desired_fire_date` |
|---|---|---|---|---|---|---|
| `SUMMARY` | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| `PROJECTED_DATE` | REQUIRED | REQUIRED | REQUIRED | CONDITIONAL | REQUIRED | FORBIDDEN |
| `REQUIRED_CONTRIBUTION` | FORBIDDEN | REQUIRED | REQUIRED | CONDITIONAL | FORBIDDEN | REQUIRED |

For both projection modes:

- `inflation_rate` is required when `return_type = NOMINAL`;
- `inflation_rate` is forbidden when `return_type = REAL`.

Every mode-incompatible extra field is a validation error. Fields are never silently ignored.

## 12. Time contract

`as_of_date` is an explicit ISO `YYYY-MM-DD` civil date and Planning period zero. The backend does not substitute UTC-now. A future frontend may capture the local civil date at submit under the already approved Planning UX semantics.

`as_of_date` also governs ADR-023 portfolio snapshot eligibility.

`PROJECTED_DATE.horizon_months` is an integer from 1 through 1,200 complete Planning months. It has no default.

`REQUIRED_CONTRIBUTION.desired_fire_date` is an ISO `YYYY-MM-DD` civil date mapped to Planning `ProjectionAssumptions.target_date`. Planning resolves it at calendar-month granularity and enforces one through 1,200 projected months. It is not an exact-day achievement promise.

FIRE v1 does not accept age or depend on birthdate.

## 13. Summary calculations

All summary calculations use a local Decimal context precision of at least 34 digits and no float conversion.

### 13.1 Gap

```text
gap_to_fire = max(fire_target - eligible_investment_wealth, Decimal("0.00"))
```

Both operands are cent-scale canonical money, so the result remains two-decimal money. A negative gap is never returned.

### 13.2 Progress

```text
raw_progress_ratio = eligible_investment_wealth / fire_target
progress_ratio = quantize(raw_progress_ratio, Decimal("0.00000001"), ROUND_HALF_EVEN)
```

Progress is not clamped. A value greater than one is valid and preserves overachievement.

### 13.3 Conditional withdrawal capacity

```text
raw_supported_annual_withdrawal =
    eligible_investment_wealth * assumed_annual_withdrawal_rate

supported_annual_withdrawal =
    quantize(raw_supported_annual_withdrawal, Decimal("0.01"), ROUND_HALF_EVEN)

raw_supported_monthly_withdrawal =
    raw_supported_annual_withdrawal / Decimal(12)

supported_monthly_withdrawal =
    quantize(raw_supported_monthly_withdrawal, Decimal("0.01"), ROUND_HALF_EVEN)
```

The monthly value is derived from the unrounded annual value, not the rounded annual output. These outputs are conditional capacities under the supplied rate, not guaranteed income, dividend income, or safe income.

### 13.4 Summary status

The FIRE-specific summary status enum contains exactly:

- `ALREADY_FINANCIALLY_INDEPENDENT` when `eligible_investment_wealth >= fire_target`;
- `BELOW_FIRE_TARGET` otherwise.

There are no `NEAR_FIRE`, `ON_TRACK`, `AT_RISK`, score, or subjective intermediate states.

## 14. Projection composition

`PROJECTED_DATE` builds one valid `ProjectionAssumptions` instance with:

- request `as_of_date`;
- request `scenario_monthly_contribution`;
- request `expected_return_rate`;
- request `return_type`;
- fixed `output_mode = REAL`;
- conditional request `inflation_rate`;
- request `horizon_months`;
- `target_date = None`;
- fixed `EFFECTIVE_ANNUAL` and `END_OF_MONTH`.

The orchestrator calls `TargetAchievementSolver` with the resolved initial wealth fact, those assumptions, and the canonical FIRE target. The solver's real statuses remain authoritative:

- `ALREADY_ACHIEVED`
- `ACHIEVED`
- `UNREACHABLE`
- `NOT_REACHED_WITHIN_HORIZON`

FIRE does not reinterpret or duplicate them. Partial-current-month behavior, monthly conversion, contribution timing, projection periods, and achievement date come entirely from Planning.

## 15. Required-contribution composition

`REQUIRED_CONTRIBUTION` builds one Planning assumptions template with:

- request `as_of_date`;
- internal neutral `scenario_monthly_contribution = 0.00`;
- request `expected_return_rate`;
- request `return_type`;
- fixed `output_mode = REAL`;
- conditional request `inflation_rate`;
- `horizon_months = None`;
- request `desired_fire_date` mapped to `target_date`;
- fixed `EFFECTIVE_ANNUAL` and `END_OF_MONTH`.

The orchestrator calls `RequiredContributionSolver` with the resolved initial wealth fact, the template, and the canonical FIRE target. Its real statuses remain authoritative:

- `ALREADY_ACHIEVED`
- `ZERO_CONTRIBUTION_REQUIRED`
- `SOLVED`
- `IMPOSSIBLE_HORIZON`
- `OUT_OF_SUPPORTED_RANGE`

The solver's cents-exact binary search and minimum-satisfying-cent semantics remain Planning authority.

## 16. Conceptual request contract

The locked public request shape is conceptually:

```json
{
  "analysis_type": "SUMMARY | PROJECTED_DATE | REQUIRED_CONTRIBUTION",
  "as_of_date": "YYYY-MM-DD",
  "initial_wealth": {
    "source": "INVESTMENT_PORTFOLIO_SNAPSHOT | USER_PROVIDED_SCENARIO"
  },
  "monthly_retirement_spending": "DecimalString",
  "assumed_annual_withdrawal_rate": "DecimalString",
  "scenario_monthly_contribution": "DecimalString | absent",
  "expected_return_rate": "DecimalString | absent",
  "return_type": "REAL | NOMINAL | absent",
  "inflation_rate": "DecimalString | absent",
  "horizon_months": "integer | absent",
  "desired_fire_date": "YYYY-MM-DD | absent"
}
```

The discriminated `initial_wealth` object uses one of the exact shapes in section 5. `extra = forbid` semantics are required at the request and source-variant boundaries.

## 17. Conceptual response contract

The locked response structure is:

```json
{
  "analysis_type": "SUMMARY",
  "as_of_date": "YYYY-MM-DD",
  "basis": "REAL",
  "summary": {
    "monthly_retirement_spending": "10000.00",
    "annual_required_spending": "120000.00",
    "assumed_annual_withdrawal_rate": "0.035",
    "fire_target": "3428571.43",
    "eligible_investment_wealth": "250000.00",
    "gap_to_fire": "3178571.43",
    "progress_ratio": "0.07291667",
    "supported_annual_withdrawal": "8750.00",
    "supported_monthly_withdrawal": "729.17",
    "summary_status": "BELOW_FIRE_TARGET"
  },
  "projection": null,
  "required_contribution": null,
  "assumptions": {
    "return_type": null,
    "expected_return_rate": null,
    "inflation_rate": null,
    "scenario_monthly_contribution": null,
    "horizon_months": null,
    "desired_fire_date": null
  },
  "provenance": {
    "initial_wealth_fact": {}
  }
}
```

The numbers above illustrate representation only and are not defaults or guidance.

Financial values and ratios serialize as exact decimal strings. The nested `projection` must preserve the existing Target Achievement result semantics and complete certified projection. The nested `required_contribution` must preserve the existing Required Contribution result semantics. API DTO names may reuse existing Planning response DTOs or exact structural equivalents; mappings may not recalculate or rename statuses.

## 18. Response nullability

| Mode | `projection` | `required_contribution` |
|---|---|---|
| `SUMMARY` | `null` | `null` |
| `PROJECTED_DATE` | populated | `null` |
| `REQUIRED_CONTRIBUTION` | `null` | populated |

The non-applicable section is always explicitly `null`, never an empty object or partial result.

## 19. Provenance

The response preserves:

- selected wealth source;
- resolved `InitialWealthFact` source, scope, amount, and as-of data;
- analysis `as_of_date`;
- portfolio `reference_month` and approved Planning provenance when applicable;
- explicit user-provided `observed_at` when applicable;
- all FIRE and mode-specific assumptions actually used.

Portfolio `observed_at` remains null. `updated_at` retains its technical snapshot-version/import meaning and is never presented as a daily valuation time. `account_id` and `run_id` may remain in the approved machine provenance inherited from Planning but are not primary user-facing semantics.

No daily observation date is invented for a monthly snapshot.

## 20. Precision contract

- All financial calculations use `Decimal`; float is prohibited as financial authority.
- FIRE local calculation context precision is at least 34 digits.
- Public financial values use finite plain decimal strings; JSON numbers are rejected.
- Money inputs have at most two declared decimal places and are never silently rounded.
- Money outputs have exactly two decimal places.
- Rates are Decimal fractions.
- Canonical FIRE target uses `ROUND_CEILING` to `0.01`.
- Ordinary derived money uses `ROUND_HALF_EVEN` to `0.01`.
- Progress uses `ROUND_HALF_EVEN` to eight decimal places.
- Planning engine precision, adaptive context, monthly rate precision, and cent recurrence remain unchanged.

## 21. Error categories

The implementation must distinguish:

1. request validation — malformed Decimal/date/enums, missing required fields, or forbidden extra fields;
2. source unavailable — explicitly selected portfolio fact cannot be resolved;
3. source ambiguous — ADR-023 portfolio cardinality/ownership ambiguity;
4. unsupported mode or basis — invalid analysis type or nominal/real combination;
5. Planning solver domain outcome — valid `200` result status, not an error;
6. internal failure — invariant/arithmetic/unclassified server failure without leaked trace.

Authentication retains existing `401` semantics. Validation and unavailable/ambiguous selected source follow the existing safe Planning boundary, normally `422`. Legitimate Planning non-achievement and required-contribution statuses remain successful response data.

## 22. Edge-case locks

| Condition | Locked behavior |
|---|---|
| Spending `<= 0` | Validation error |
| Spending with more than two decimals | Validation error; no rounding |
| Withdrawal rate `<= 0` or `>= 1` | Validation error |
| Wealth `0.00` | Valid when accepted by selected Planning source |
| Wealth `>= fire_target` | FIRE summary `ALREADY_FINANCIALLY_INDEPENDENT`; Planning decides its own nested status |
| Scenario contribution `0.00` | Valid in `PROJECTED_DATE` |
| Expected return `0` | Valid |
| Expected return `>-1` and negative | Valid |
| Missing/future-only portfolio snapshot | Existing ADR-023 source failure semantics |
| Missing required mode field | Validation error |
| Forbidden field for mode | Validation error |
| Nominal return without inflation | Validation error |
| Real return with inflation | Validation error |
| Very large target | No arbitrary FIRE cap; reuse Planning supported-range behavior |

## 23. Double-counting and inference gates

- Never add historical or projected dividends on top of a total-return Planning projection.
- Never combine Goal current amount with portfolio snapshot wealth.
- Never add or subtract an emergency reserve silently.
- Never inflate the real spending/target path and also apply nominal-to-real conversion to that target.
- Fisher conversion occurs exactly once and only inside Planning.
- No retirement-income offset exists in the MVP.
- No Health, macro, portfolio-history, or Goal value becomes a future assumption automatically.

## 24. Persistence and Goal boundary

FIRE v1 is standalone and transient:

- no `goal_id` request field;
- no Goal read/write or implicit synchronization;
- no `fire_profile` or `fire_scenario` storage;
- no migration;
- no `assumptions_json` use;
- no canonical `localStorage` persistence.

RETIREMENT and FINANCIAL_INDEPENDENCE Goals remain reserved for a later explicit integration contract.

## 25. Health, dividends, external income, and macro boundary

- Health supplies no automatic spending, savings, contribution, or prefill in the MVP.
- Dividend history, TTM, yield, and forecasts do not participate.
- INSS, pension, rent, business income, and all other income offsets are excluded.
- CDI, SELIC, IPCA, IBOV, macro tables/files, and historical portfolio returns do not provide future assumptions.

Future references or offsets require new source, temporal, precision, opt-in, and double-counting contracts.

## 26. Deferred models

The MVP excludes:

- tax and gross-up modeling;
- longevity, death age, survival curves, and actuarial guarantees;
- Monte Carlo, sequence-of-returns simulation, and probability of success;
- Lean, Fat, Barista, and Coast FIRE;
- dividend-income independence;
- sustainable contribution capacity;
- emergency-reserve exclusions;
- Goal integration and persistence;
- scenario comparison;
- target age and birthdate;
- Portfolio Intelligence, asset allocation, rebalancing, asset selection, and advice;
- LLM calculation or assumption selection.

## 27. Conceptual frontend contract

No UI is implemented by this lock. A future Quiet Financial OS flow should:

1. ask for source, monthly retirement spending, and assumed annual withdrawal rate;
2. let the user choose Summary, “When?”, or “How much monthly contribution?”;
3. reveal only the chosen mode's additional fields;
4. ask for explicit expected annual real return in the basic projection flow;
5. offer nominal return only as an advanced path that requires explicit inflation;
6. show target, assumptions, basis, source, date, and provenance without guarantee language.

The UI must not prepopulate withdrawal rate, return, inflation, contribution, horizon, or desired date. It contains no Health prefill in the initial contract.

## 28. Wording boundary

Approved concepts include:

- target under supplied assumptions;
- assumed annual withdrawal rate;
- conditional withdrawal capacity;
- projected date under supplied assumptions;
- eligible investment wealth.

Prohibited claims include:

- guaranteed or safe income;
- guaranteed retirement;
- “you can retire” as an authoritative conclusion;
- probability of success;
- net worth when the source is investment portfolio wealth.

## 29. Required future validation categories

Implementation must later cover, at minimum:

- target formula and `ROUND_CEILING` boundaries;
- exact annualization, gap, progress, and raw-annual monthly withdrawal behavior;
- Decimal-only and scale validation;
- all mode required/forbidden/conditional combinations;
- real and nominal-to-real Planning composition;
- canonical target equality between summary and solvers;
- exact existing Planning statuses and one solver delegation;
- both wealth sources, provenance, authentication, and ADR-023 failures;
- transient/no-write behavior;
- double-counting and forbidden-source static gates;
- response nullability and Decimal-string serialization;
- independent Decimal oracle validation.

## 30. Implementation gate

Phase 10.4-B is contract lock only. Production implementation, tests, endpoint registration, UI, migrations, and persistence remain `NOT STARTED`.

The next allowed step after user review is Phase 10.4-C implementation decomposition. That step must split implementation around this contract without reopening locked FIRE meaning or duplicating Planning.
