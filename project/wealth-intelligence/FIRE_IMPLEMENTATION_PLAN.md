# STATUS: READY FOR USER REVIEW

# AUTHORITY: ADR-025 + FIRE_CONTRACT.md

# Phase 10.4-C — FIRE Implementation Decomposition & Execution Plan

**Prepared:** 2026-09-30

**Implementation status:** NOT STARTED

This document converts the locked FIRE contract into a dependency-safe implementation sequence. It does not authorize production changes, tests, migrations, staging, commits, or push.

## 1. Readiness decision

`IMPLEMENTATION PLAN READY / AWAITING USER APPROVAL`

No substantive contradiction was found between ADR-025, `FIRE_CONTRACT.md`, and the current codebase. The implementation can remain a thin FIRE layer over the certified Planning boundary.

## 2. Locked source of truth

Authority order:

1. ADR-025 in `DECISION_LOG.md`;
2. `FIRE_CONTRACT.md`;
3. existing certified Planning domain and application behavior;
4. this implementation plan;
5. `FIRE_CONTRACT_AUDIT.md` as preserved design evidence only.

This plan does not reopen target rounding, real basis, wealth eligibility, analysis modes, persistence, or any deferred feature.

## 3. Codebase conventions found

- Planning domain objects are immutable dataclasses and string enums under `backend/domains/planning/`.
- Domain validation uses `TypeError` for wrong authority types and `ValueError` for invalid values; calculations are pure and use `Decimal` plus local contexts.
- Strict public financial inputs use `StrictDecimalString`; JSON numbers, exponent notation, non-finite values, and extra fields are rejected.
- Public source DTOs are discriminated unions keyed by `source`.
- Planning maps requests and certified results without HTTP-side financial recalculation.
- The authenticated router uses `CurrentPlanningUser` and `PlanningReadSession`; calculation collaborators are dependency-injected.
- `PlanningPortfolioSourceResolver.resolve(db, current_user_id, as_of_date)` is the only approved portfolio resolution path.
- Manual wealth is represented by `InitialWealthFact` with explicit `observed_at`, `USER_PROVIDED_SCENARIO` source/scope, and user-asserted provenance.
- Planning solvers return domain outcomes, including non-achievement, rather than converting them into HTTP errors.
- The frontend already has string-only BRL, percent, and civil-date parsing/formatting in `planningLocale.ts` and Vitest parser/builder tests.
- Planning UI has reusable state patterns for loading, preserved results, dirty results, errors, provenance, progressive disclosure, and accessible controls.
- Planning's current form builder must not be reused wholesale: it permits `GOAL_CURRENT_AMOUNT`, defaults to nominal output, and manufactures `observed_at` when empty. FIRE forbids all three behaviors.

## 4. Dependency direction

```text
POST /api/v1/fire/analysis
        |
        v
API DTO validation and FIRE mapping
        |
        v
FireAnalysisService (application orchestration)
        |-----------------------------|
        v                             v
FireSummaryCalculator          Planning application/domain
(pure FIRE mathematics)        - PlanningPortfolioSourceResolver
                               - InitialWealthFact semantics
                               - ProjectionAssumptions
                               - TargetAchievementSolver
                               - RequiredContributionSolver
```

Dependency rules:

- `backend/domains/fire/` may import Python standard-library types only.
- FIRE domain must not import FastAPI, Pydantic, SQLAlchemy, sessions, routers, current-user objects, HTTP DTOs, or database models.
- FIRE application orchestration may depend on stable Planning application/domain contracts.
- API code may depend on FIRE application/domain and Planning response mappers.
- Planning must never import FIRE.
- Frontend renders server facts; it never becomes a FIRE calculation authority.

## 5. FIRE domain responsibility

FIRE owns exactly:

- validation of eligible wealth, monthly retirement spending, and assumed withdrawal rate at the pure calculation boundary;
- exact annual required spending;
- canonical positive FIRE target with cent `ROUND_CEILING`;
- nonnegative gap;
- unclamped eight-decimal progress ratio with `ROUND_HALF_EVEN`;
- annual and monthly conditional withdrawal capacity, with monthly derived from the raw annual value;
- FIRE summary status.

FIRE domain does not own compounding, Fisher conversion, annual-to-monthly return conversion, projection periods, contribution timing, calendar horizons, target crossing, or required-contribution search.

## 6. Proposed backend file map

### New production files

| File | Responsibility |
|---|---|
| `backend/domains/fire/__init__.py` | Canonical `fire` namespace; no behavior |
| `backend/domains/fire/summary.py` | FIRE input/result dataclasses, status enum, pure calculator, precision and rounding |
| `backend/application/services/fire_analysis_service.py` | Application commands/results, one wealth resolution, summary calculation, Planning composition |
| `backend/application/services/planning_initial_wealth_fact_builder.py` | Shared manual Planning fact builder extracted from the API mapping layer |
| `backend/application/dtos/fire_dto.py` | Strict discriminated request union and exact response DTOs |
| `backend/api/fire_mapping.py` | DTO-to-command and application-result-to-response mapping; no financial math |
| `backend/api/fire_errors.py` | Local safe exception-to-HTTP translation |
| `backend/api/routers/fire.py` | One authenticated `POST /fire/analysis` route and dependency factories |

### Modified production files

| File | Minimal modification |
|---|---|
| `backend/api/planning_mapping.py` | Import/re-export the extracted manual fact builder; preserve current public imports and behavior |
| `backend/main.py` | Register the FIRE router once under `/api/v1` |

### New backend test files

| File | Responsibility |
|---|---|
| `tests/unit/test_fire_summary.py` | Pure domain vectors, validation, precision, determinism, no-float behavior |
| `tests/unit/test_fire_analysis_service.py` | Orchestration, single resolution, solver composition, provenance, basis, no persistence |
| `tests/unit/test_fire_api.py` | Authentication, strict mode DTOs, mapping, serialization, safe errors, OpenAPI route |

No migration, repository, ORM model, FIRE table, Goal change, Health change, or Planning engine change is planned.

## 7. Pure summary calculator

Proposed interface in `backend/domains/fire/summary.py`:

```python
class FireSummaryStatus(str, Enum):
    ALREADY_FINANCIALLY_INDEPENDENT = "ALREADY_FINANCIALLY_INDEPENDENT"
    BELOW_FIRE_TARGET = "BELOW_FIRE_TARGET"

@dataclass(frozen=True)
class FireSummaryInput:
    eligible_investment_wealth: Decimal
    monthly_retirement_spending: Decimal
    assumed_annual_withdrawal_rate: Decimal

@dataclass(frozen=True)
class FireSummary:
    monthly_retirement_spending: Decimal
    annual_required_spending: Decimal
    assumed_annual_withdrawal_rate: Decimal
    fire_target: Decimal
    eligible_investment_wealth: Decimal
    gap_to_fire: Decimal
    progress_ratio: Decimal
    supported_annual_withdrawal: Decimal
    supported_monthly_withdrawal: Decimal
    status: FireSummaryStatus

class FireSummaryCalculator:
    def calculate(self, input: FireSummaryInput) -> FireSummary: ...
```

Validation and precision:

- all three inputs must be finite `Decimal`; float is rejected;
- eligible wealth is nonnegative, cent-scale;
- monthly spending is positive, cent-scale;
- withdrawal rate is strictly greater than zero and less than one;
- use `localcontext()` with magnitude-derived adaptive precision, never below 34 digits, so very large values and very small positive rates can still be quantized to cents without an arbitrary FIRE cap;
- annual spending is exact multiplication by `Decimal("12")`;
- only the target uses `ROUND_CEILING` to `Decimal("0.01")`;
- ordinary money uses `ROUND_HALF_EVEN` to `Decimal("0.01")`;
- progress uses `ROUND_HALF_EVEN` to `Decimal("0.00000001")` and is not clamped.

The calculator raises `TypeError` or `ValueError`, matching Planning domain conventions. No custom HTTP-aware exception belongs in the domain.

## 8. Validation ownership

| Boundary | Owns | Does not own |
|---|---|---|
| Pydantic request DTO | exact JSON string/date/enum shapes, discriminators, required/forbidden mode fields, extra-field rejection, nominal/inflation matrix | FIRE calculations or Planning solver outcomes |
| FIRE pure domain | Decimal authority, finiteness, cent scale, positive spending, withdrawal interval, nonnegative wealth, summary invariants | HTTP status, source resolution, mode routing |
| Planning domain | return constraints, horizon/date resolution, nominal/real compatibility, projection, solver statuses | FIRE target meaning or summary status |
| Application service | one-source policy, source routing, fixed REAL basis, correct solver selected once, provenance continuity | persistence or API serialization |

Validation may be intentionally defense-in-depth, but a formula or calendar rule must have one calculation authority.

## 9. FIRE request DTO strategy

Use Pydantic discriminated unions by `analysis_type`, not one model with an optional-field soup.

Exact variants:

- `FireSummaryRequestDTO`
  - `analysis_type: Literal[SUMMARY]`
  - common fields only.
- `FireProjectedDateRequestDTO`
  - `analysis_type: Literal[PROJECTED_DATE]`
  - common fields plus required `scenario_monthly_contribution`, `expected_return_rate`, `return_type`, and `horizon_months`;
  - conditional `inflation_rate` enforced by a model validator.
- `FireRequiredContributionRequestDTO`
  - `analysis_type: Literal[REQUIRED_CONTRIBUTION]`
  - common fields plus required `expected_return_rate`, `return_type`, and `desired_fire_date`;
  - conditional `inflation_rate` enforced by a model validator.

`FireAnalysisRequestDTO` is an `Annotated[Union[...], Field(discriminator="analysis_type")]`. Every variant and nested source uses `ConfigDict(extra="forbid")`.

The common fields are exactly:

- `analysis_type`;
- `as_of_date: StrictISODate`;
- `initial_wealth: FireInitialWealthSelectorRequestDTO`;
- `monthly_retirement_spending: StrictDecimalString`;
- `assumed_annual_withdrawal_rate: StrictDecimalString`.

Reuse `StrictDecimalString`, `StrictISODate`, `StrictISODatetime`, `UserProvidedInitialWealthRequestDTO`, and `InvestmentPortfolioSnapshotInitialWealthRequestDTO` from `planning_dto.py`. Define only a FIRE union of the two allowed existing source shapes. Do not include or subclass the Goal selector.

## 10. FIRE response DTO strategy

`FireAnalysisResponseDTO` contains exactly:

- `analysis_type: FireAnalysisType`;
- `as_of_date: date`;
- `basis: Literal[OutputMode.REAL]`;
- `summary: FireSummaryResponseDTO`;
- `projection: TargetAchievementResponseDTO | None`;
- `required_contribution: RequiredContributionResponseDTO | None`;
- `assumptions: FireAssumptionsResponseDTO`;
- `provenance: FireProvenanceResponseDTO`.

`FireSummaryResponseDTO` fields are exactly:

- `monthly_retirement_spending`;
- `annual_required_spending`;
- `assumed_annual_withdrawal_rate`;
- `fire_target`;
- `eligible_investment_wealth`;
- `gap_to_fire`;
- `progress_ratio`;
- `supported_annual_withdrawal`;
- `supported_monthly_withdrawal`;
- `summary_status`.

All summary financial values and ratios are strings. No narrative or recommendation field is added.

`FireAssumptionsResponseDTO` echoes:

- common: `monthly_retirement_spending`, `assumed_annual_withdrawal_rate`;
- projection modes: `expected_return_rate`, `return_type`, and conditional `inflation_rate`;
- PROJECTED_DATE only: `scenario_monthly_contribution`, `horizon_months`;
- REQUIRED_CONTRIBUTION only: `desired_fire_date`.

Non-applicable fields are explicit `null`. Fixed server-owned facts such as `output_mode`, `rate_basis`, `contribution_timing`, and target basis are represented by top-level `basis` and the nested certified Planning result, not duplicated as user assumptions.

`FireProvenanceResponseDTO` contains one field, `initial_wealth_fact: InitialWealthFactResponseDTO`. It reuses `map_initial_wealth_fact`; it does not create a parallel provenance schema or hide the already-approved machine provenance.

## 11. Initial wealth reuse

Portfolio path:

```text
source-only DTO
  -> PortfolioInitialWealthSelection application value
  -> PlanningPortfolioSourceResolver.resolve(db, current_user_id, as_of_date)
  -> one InitialWealthFact
```

Manual path:

```text
existing UserProvidedInitialWealthRequestDTO shape
  -> UserProvidedInitialWealthSelection(amount, observed_at)
  -> shared planning_initial_wealth_fact_builder
  -> one InitialWealthFact
```

The current `build_user_initial_wealth_fact` must be extracted from `backend/api/planning_mapping.py` to the application layer so both Planning API mapping and FIRE orchestration can reuse the same semantics without an application-to-API dependency. `planning_mapping.py` should import the function at module scope so existing imports remain compatible.

The service resolves exactly once per request and reuses the same immutable `InitialWealthFact` for the FIRE summary and any Planning solver. Manual selection never calls the portfolio resolver. No fallback or source aggregation exists.

## 12. Application orchestrator

`FireAnalysisService` receives collaborators through its constructor:

- `FireSummaryCalculator`;
- `PlanningPortfolioSourceResolver`;
- `TargetAchievementSolver`;
- `RequiredContributionSolver`.

The same file contains small immutable application command/result dataclasses so the service does not depend on Pydantic or FastAPI. The API mapper converts discriminated DTOs into one of:

- `FireSummaryCommand`;
- `FireProjectedDateCommand`;
- `FireRequiredContributionCommand`.

Each command carries a typed application wealth selection, explicit FIRE assumptions, and only its mode-specific fields.

Conceptual method:

```python
def analyze(
    self,
    command: FireAnalysisCommand,
    db: Session,
    current_user_id: UUID,
) -> FireAnalysisResult: ...
```

The result carries the analysis type, date, pure summary, same initial fact, assumptions echo, and at most one certified Planning result. The service performs no commit, flush, persistence, LLM call, or financial serialization.

## 13. Data flows

### SUMMARY

```text
HTTP JSON
  -> FireSummaryRequestDTO validation
  -> API mapping to FireSummaryCommand
  -> resolve one InitialWealthFact
  -> FireSummaryCalculator.calculate(...)
  -> FireAnalysisResult with both nested solver results absent
  -> response mapping and Decimal-string serialization
```

No Planning solver or projection engine is called.

### PROJECTED_DATE

```text
HTTP JSON
  -> FireProjectedDateRequestDTO validation
  -> resolve one InitialWealthFact
  -> calculate canonical FIRE summary/target
  -> build ProjectionAssumptions(
       as_of_date=request.as_of_date,
       scenario_monthly_contribution=request.scenario_monthly_contribution,
       expected_return_rate=request.expected_return_rate,
       return_type=request.return_type,
       output_mode=OutputMode.REAL,
       inflation_rate=conditional request value,
       horizon_months=request.horizon_months,
       target_date=None,
       rate_basis=RateBasis.EFFECTIVE_ANNUAL,
       contribution_timing=ContributionTiming.END_OF_MONTH,
     )
  -> TargetAchievementSolver.solve(same_fact, assumptions, summary.fire_target)
  -> preserve TargetAchievementResult unchanged
  -> response mapping via existing Planning mapper
```

The nested result already includes the certified projection timeline when Planning produces one. There is no second projection call.

### REQUIRED_CONTRIBUTION

```text
HTTP JSON
  -> FireRequiredContributionRequestDTO validation
  -> resolve one InitialWealthFact
  -> calculate canonical FIRE summary/target
  -> build ProjectionAssumptions(
       as_of_date=request.as_of_date,
       scenario_monthly_contribution=Decimal("0.00"),
       expected_return_rate=request.expected_return_rate,
       return_type=request.return_type,
       output_mode=OutputMode.REAL,
       inflation_rate=conditional request value,
       horizon_months=None,
       target_date=request.desired_fire_date,
       rate_basis=RateBasis.EFFECTIVE_ANNUAL,
       contribution_timing=ContributionTiming.END_OF_MONTH,
     )
  -> RequiredContributionSolver.solve(same_fact, template, summary.fire_target)
  -> preserve RequiredContributionResult unchanged
  -> response mapping via existing Planning mapper
```

The internal `0.00` is a neutral solver-template requirement. It is not accepted from the user, echoed as a user assumption, or described as an actual contribution.

## 14. Planning components reused

- `InitialWealthFact`, `PlanningFactAsOf`, `PlanningFactProvenance`, sources, and scopes;
- `PlanningPortfolioSourceResolver`;
- extracted shared manual fact builder;
- `ProjectionAssumptions` and its calendar/horizon validation;
- `RateBasis.EFFECTIVE_ANNUAL`;
- `ContributionTiming.END_OF_MONTH`;
- `ReturnType.REAL` and `ReturnType.NOMINAL`;
- `OutputMode.REAL`;
- `TargetValueBasis.REAL` in response mapping and assertions;
- `TargetAchievementSolver` and its exact result/status;
- `RequiredContributionSolver` and its exact result/status;
- Planning response mappers for initial fact and both solver results;
- strict Decimal/date DTO primitives.

## 15. Real/nominal and target-basis mapping

| FIRE input | Planning mapping |
|---|---|
| REAL return | `return_type=REAL`, `output_mode=REAL`, `inflation_rate=None` |
| NOMINAL return | `return_type=NOMINAL`, `output_mode=REAL`, explicit `inflation_rate` |

Every solver call uses canonical `summary.fire_target` with `ProjectionAssumptions.output_mode=REAL`. The solver signatures do not accept a target-basis argument; API mapping therefore attaches fixed `TargetValueBasis.REAL` through the existing Planning response mapper. Tests must assert that no FIRE path constructs `OutputMode.NOMINAL` or emits `TargetValueBasis.NOMINAL`. FIRE never performs Fisher conversion.

## 16. Status mapping

FIRE summary status serializes its enum value directly:

- `ALREADY_FINANCIALLY_INDEPENDENT`;
- `BELOW_FIRE_TARGET`.

Nested Planning statuses serialize directly through existing response DTOs and mappers:

- Target: `ALREADY_ACHIEVED`, `ACHIEVED`, `UNREACHABLE`, `NOT_REACHED_WITHIN_HORIZON`;
- Required contribution: `ALREADY_ACHIEVED`, `ZERO_CONTRIBUTION_REQUIRED`, `SOLVED`, `IMPOSSIBLE_HORIZON`, `OUT_OF_SUPPORTED_RANGE`.

There is no translated FIRE synonym. `NOT_REACHED_WITHIN_HORIZON` and other valid solver outcomes remain HTTP 200 data.

## 17. Error mapping

| Error | HTTP behavior |
|---|---|
| Authentication failure | existing auth `401` behavior |
| Pydantic request/discriminator/extra-field error | FastAPI `422` |
| FIRE `TypeError`/`ValueError` invariant failure | local safe `422` |
| Portfolio unavailable or inconsistent | safe source-unavailable `422` |
| Portfolio ambiguous | safe source-ambiguous `422` |
| Planning solver domain outcome | `200`, preserved in nested result |
| `ArithmeticError` | generic FIRE calculation `500`, no internal detail |
| Unexpected exception | generic internal FIRE `500`, no trace/detail leak |

`backend/api/fire_errors.py` should mirror the locality of `planning_errors.py`; no global FastAPI handler is changed.

## 18. API integration

- Router: `APIRouter(prefix="/fire", tags=["FIRE"])`.
- Endpoint: exactly `POST /analysis` under the global `/api/v1` prefix.
- Full path: exactly `POST /api/v1/fire/analysis`.
- Authentication/session: reuse `CurrentPlanningUser` and `PlanningReadSession` without inventing new auth.
- Service dependency: one `FireAnalysisService` per request, constructed from stateless calculator/solvers and the Planning resolver.
- `backend/main.py`: one import and one `include_router` call.
- OpenAPI gate: exactly one FIRE path/operation; it is authenticated and advertises the discriminated request variants.

## 19. Backend test plan

### Domain

- exact target and CEILING target vectors;
- zero/negative spending rejected;
- zero, negative, and `>= 1` withdrawal rate rejected;
- non-Decimal and non-finite inputs rejected;
- fractional-cent money rejected;
- zero, below, equal, and above-target wealth;
- gap never negative;
- progress greater than one remains unclamped;
- raw-annual-to-monthly withdrawal rule;
- deterministic repeatability under an altered ambient Decimal context;
- domain import audit: no FastAPI, Pydantic, SQLAlchemy, DB, or Planning import.

### Application orchestration

- SUMMARY calls no solver;
- PROJECTED_DATE calls target solver exactly once;
- REQUIRED_CONTRIBUTION calls required solver exactly once;
- portfolio resolver called exactly once per portfolio request;
- same object identity for the fact used by summary input and solver;
- manual request never calls portfolio resolver;
- manual `observed_at` and provenance preserved;
- canonical CEILING target passed unchanged;
- fixed REAL output and target basis;
- REAL path has no inflation; NOMINAL path passes explicit inflation exactly once to Planning;
- required mode uses internal `0.00` template only;
- solver result/status/provenance preserved without remapping;
- no commit/flush/write invocation.

### API

- authenticated valid request for all three modes;
- unauthenticated request rejected by existing auth behavior;
- discriminator selects the correct variant;
- every missing and forbidden field in the mode matrix;
- nominal without inflation rejected;
- real with inflation rejected;
- Goal wealth selector rejected structurally;
- JSON numbers and exponent strings rejected;
- response nullability matrix;
- all financial outputs and progress are strings/null;
- safe source and internal errors;
- valid non-achievement solver statuses remain 200;
- OpenAPI contains exactly one secured FIRE operation.

## 20. Golden domain vectors

### A. Exact target

```text
monthly_retirement_spending = 5000.00
annual_required_spending = 60000.00
assumed_annual_withdrawal_rate = 0.04
raw target = 1500000
fire_target = 1500000.00
```

### B. CEILING target

```text
monthly_retirement_spending = 1000.00
annual_required_spending = 12000.00
assumed_annual_withdrawal_rate = 0.07
raw target = 171428.571428...
fire_target = 171428.58
```

The assertion must independently prove that cent `ROUND_HALF_EVEN` would not be the canonical target.

### C. Progress above 100% and zero gap

```text
eligible_investment_wealth = 1800000.00
fire_target = 1500000.00
progress_ratio = 1.20000000
gap_to_fire = 0.00
status = ALREADY_FINANCIALLY_INDEPENDENT
```

### D. Withdrawal raw-month derivation

```text
eligible_investment_wealth = 120.61
assumed_annual_withdrawal_rate = 0.10
raw supported annual = 12.061
supported_annual_withdrawal = 12.06
raw supported monthly = 12.061 / 12 = 1.0050833...
supported_monthly_withdrawal = 1.01
```

The rejected implementation path would divide rounded annual `12.06 / 12 = 1.005` and produce `1.00` under `ROUND_HALF_EVEN`. This vector detects that error.

### E. Exact already-achieved boundary

```text
eligible_investment_wealth = 1500000.00
fire_target = 1500000.00
gap_to_fire = 0.00
progress_ratio = 1.00000000
status = ALREADY_FINANCIALLY_INDEPENDENT
```

Projected-date and required-contribution integration tests use invariants, not a second hand-built solver oracle: identical fact, assumptions, and target must produce exactly the same result as the injected Planning solver.

## 21. Planning regression plan

Run focused Planning regressions at D2, D3, and D6 as appropriate:

- `tests/unit/test_planning_assumptions.py`;
- `tests/unit/test_planning_projection_engine.py`;
- `tests/unit/test_planning_target_solver.py`;
- `tests/unit/test_planning_required_contribution_solver.py`;
- `tests/unit/test_planning_portfolio_source_resolver.py`;
- `tests/unit/test_planning_api_foundation.py`;
- `tests/unit/test_planning_api_calculation_endpoints.py`;
- `tests/unit/test_planning_api_portfolio_source.py`.

Do not run the full repository suite after every microtask. D6 owns the consolidated focused regression run. Historical Investments/MagicMock failures remain unrelated if reproduced unchanged.

## 22. Portfolio and manual source integration cases

Portfolio boundary cases:

- eligible latest snapshot;
- no snapshot;
- future-only snapshot;
- ambiguous scope/cardinality;
- source-only request, with no client amount/account/run/reference-month fields;
- same resolved fact object used by summary and solver.

Manual boundary cases:

- valid cent-scale Decimal amount;
- explicit `observed_at` required and preserved;
- user-provided source/scope/provenance preserved;
- portfolio resolver invocation count is zero.

These tests cover FIRE integration only; they do not duplicate every ADR-023 resolver test.

## 23. Read-only and static audits

Implementation gates include static searches proving:

- no `Session.commit()`, `flush()`, `INSERT`, `UPDATE`, or `DELETE` in FIRE code;
- no ORM model or migration for FIRE;
- no FastAPI/SQLAlchemy/Pydantic import under `backend/domains/fire/`;
- no Planning import from FIRE-facing changes;
- no second compound loop, Fisher formula, crossing loop, or binary search in FIRE;
- no float/`float()` authority in backend FIRE;
- no frontend `parseFloat`, `toFixed`, local target/progress/withdrawal/crossing calculation;
- no `localStorage`, cookie, or persistence of FIRE assumptions.

## 24. Frontend reuse audit

Reuse directly:

- `planningLocale.ts` string-only money, percent, date, and display functions;
- `DecimalString`, ISO date types, InitialWealthFact, and nested Planning result types where structurally identical;
- `CapabilityPanel`, `CapabilityError`, `CapabilityEmpty`, and `CapabilityResultState` state patterns;
- visual conventions for progressive advanced disclosure, source explanation, focus rings, live regions, loading skeletons, dirty-result preservation, and provenance display.

Do not reuse directly:

- `PlanningInputs`, because it includes Goal source, output-basis selection, nominal defaults, contribution/horizon fields in every mode, and optional manufactured manual observation time;
- `planningForm.toInitialWealthSelector`, because FIRE requires explicit manual `observed_at`;
- Planning capability components, because their request shapes and user questions differ;
- Planning result components if they force Planning-specific hierarchy or wording.

This avoids a broad shared-component refactor. Small FIRE-specific presentation duplication is preferred over destabilizing the validated Planning UI.

## 25. Proposed frontend file map

### New files

| File | Responsibility |
|---|---|
| `frontend/src/lib/fire.ts` | exact request/response types and authenticated API client |
| `frontend/src/app/wealth-intelligence/fire/page.tsx` | route, mode state, submit lifecycle, dirty-result preservation |
| `frontend/src/app/wealth-intelligence/fire/components/fireForm.ts` | FIRE form state, strict request builders, mode-specific validation |
| `frontend/src/app/wealth-intelligence/fire/components/fireForm.test.ts` | Vitest request-builder and pt-BR parsing contract tests |
| `frontend/src/app/wealth-intelligence/fire/components/FireInputs.tsx` | accessible basic fields and progressive mode disclosure |
| `frontend/src/app/wealth-intelligence/fire/components/FireResults.tsx` | summary, mode-specific result, assumptions, provenance |

### Modified files

| File | Minimal modification |
|---|---|
| `frontend/src/config/navigation.ts` | add `Independência Financeira` at `/wealth-intelligence/fire` |
| `frontend/src/components/layout/TopNav.tsx` | add the route accent only |
| `frontend/src/app/wealth-intelligence/page.tsx` | add one active FIRE entry card/link without redesigning the hub |

No new state library, test framework, chart library, or global component abstraction is planned.

## 26. Frontend basic and mode-specific flow

Basic flow, always visible:

1. wealth source;
2. monthly retirement spending;
3. assumed annual withdrawal rate;
4. analysis question.

Human labels:

- `Resumo`;
- `Quando atinjo?`;
- `Quanto preciso aportar?`.

SUMMARY asks for no return, contribution, inflation, horizon, or desired date.

PROJECTED_DATE additionally shows:

- scenario monthly contribution;
- expected real annual return;
- horizon in months.

Its advanced disclosure allows nominal return only when explicit inflation is also entered. Output remains real and is not selectable.

REQUIRED_CONTRIBUTION additionally shows:

- expected real annual return;
- desired FIRE date.

Its advanced disclosure has the same nominal-plus-inflation option. Contribution and horizon do not appear as inputs.

No rate has a default. Manual wealth requires both amount and observation date/time. The portfolio option explains that it is eligible investment wealth, not total net worth.

## 27. FIRE result contract and wording

Primary result:

- `Meta estimada sob suas premissas` — FIRE target.

Secondary facts:

- eligible investment wealth;
- progress;
- nonnegative gap;
- conditional monthly withdrawal capacity;
- annual spending and annual conditional withdrawal capacity as supporting detail.

Mode result:

- projected achievement date/status for PROJECTED_DATE;
- required monthly contribution/status for REQUIRED_CONTRIBUTION.

Also show the exact assumptions and wealth provenance returned by the server. Use `reference_month` for portfolio facts and explicit `observed_at` for manual facts; do not invent a daily portfolio valuation date.

Prohibited wording includes “você pode se aposentar”, “renda garantida”, and “taxa segura”. Preferred wording includes “meta estimada sob suas premissas”, “patrimônio elegível”, “capacidade mensal sob a taxa informada”, and “data projetada”.

## 28. Chart decision

The initial FIRE UI should omit a chart.

The real `TargetAchievementResult` does expose a complete certified `projection_result` for projected paths except period-zero achievement, so no second calculation would be required. However, a chart is not necessary to answer the MVP questions, and the existing chart is coupled to the Planning route. Omitting it avoids either cross-feature imports or a transversal extraction during the first FIRE implementation.

The API must still preserve the nested certified projection. A later presentation-only task may extract/reuse the chart with `Number(decimalString)` isolated to the Recharts adapter and no frontend financial calculation.

## 29. Frontend test and accessibility plan

Vitest covers:

- three exact request builders;
- absent incompatible fields, not `undefined` placeholders serialized by accident;
- pt-BR money and human-percent conversion through existing locale primitives;
- real return without inflation;
- nominal return requiring inflation;
- explicit manual `observed_at`;
- source-only portfolio selector;
- local civil `as_of_date` capture;
- desired-date and horizon mapping;
- no Goal source.

Technical validation uses focused Vitest, `tsc --noEmit`, focused ESLint, and production build. No Jest, RTL, Playwright, Cypress, or browser E2E is added. Observable UI behavior is covered by a prepared manual smoke in D6/D7.

Accessibility requirements:

- one visible or screen-reader page heading;
- labeled fieldsets for source and question;
- `aria-pressed` or native radio semantics for question selection;
- `aria-expanded`/`aria-controls` for advanced disclosure;
- field errors connected with `aria-describedby`;
- error region with `role="alert"`;
- loading/result updates through `role="status"` or `aria-live`;
- keyboard-visible focus;
- disabled submit behavior while loading;
- motion-reduced skeleton/transitions;
- result status not communicated by color alone.

## 30. Financial safety plan

- API and frontend financial contracts remain `DecimalString`.
- Backend performs every authoritative FIRE and Planning calculation with `Decimal`.
- Frontend never uses `Number`, `parseFloat`, or `toFixed` for target, gap, progress, withdrawal, date crossing, or contribution truth.
- Formatting uses string-only `planningLocale` helpers.
- No local target, progress, gap, withdrawal, Fisher, projection, or crossing formula exists.
- Server response is the only result authority.
- No default return, inflation, withdrawal rate, or contribution is introduced.

## 31. Persistence, migrations, security, performance, observability

### Persistence

`NONE`. No DB tables, scenario records, Goal writes, `localStorage` truth, cookies, or saved assumptions. React form state for the current page session is presentation state only.

### Migrations

`NONE`. Any discovered migration need is a contract conflict and must stop implementation for reconciliation.

### Security

- existing authenticated current-user dependency;
- read-only session use;
- no client-selected account ID;
- no arbitrary data-source/table selector;
- ADR-023 guarded portfolio ownership remains unchanged;
- no LLM or prompt path;
- safe error details with no stack/internal leakage.

### Performance

- summary is O(1);
- projected date inherits Planning O(horizon), maximum 1,200 months;
- required contribution inherits existing Planning binary search;
- one wealth resolution per request;
- no extra projection for charts, nested simulations, Monte Carlo, background task, or scheduler.

### Observability

Reuse normal API logging/error behavior if already present. Do not introduce FIRE-specific telemetry or analytics infrastructure.

## 32. Deferred register

- Health prefill;
- Goal linkage or synchronization;
- dividend independence or dividend sustainability;
- external retirement income;
- taxes and fees;
- emergency-reserve exclusion;
- target age or birthdate;
- Coast, Lean, Fat, and Barista FIRE;
- Monte Carlo, sequence risk, longevity, and probability;
- scenario comparison;
- persistence and saved profiles;
- macro-derived guidance or defaults;
- portfolio recommendations, allocation, rebalance, or trades;
- Copilot/LLM explanation.

## 33. Implementation task D1 — FIRE Domain Core

**Purpose:** implement only the pure FIRE summary mathematics and invariants.

**Files created:**

- `backend/domains/fire/__init__.py`;
- `backend/domains/fire/summary.py`;
- `tests/unit/test_fire_summary.py`.

**Files modified:** none outside the new FIRE namespace/tests.

**Dependencies:** ADR-025, `FIRE_CONTRACT.md`; no Planning runtime dependency.

**Contract rules implemented:** summary inputs/results/status, target CEILING, ordinary HALF_EVEN money, eight-decimal unclamped progress, raw-month withdrawal derivation, Decimal/local precision.

**Tests:** all domain cases and golden vectors A–E.

**Static audits:** no FastAPI, Pydantic, SQLAlchemy, DB, Planning, float, projection, Fisher, or solver code.

**Success gate:** focused domain tests pass; calculator is deterministic under changed ambient Decimal context; D1 scope contains no non-domain behavior.

**Explicit non-goals:** source resolution, Planning composition, DTOs, endpoint, frontend, persistence.

**Recommended model:** Terra High.

**Fresh context:** YES.

## 34. Implementation task D2 — FIRE Application Orchestration

**Purpose:** compose one resolved wealth fact, the D1 summary, and the existing Planning solvers.

**Files created:**

- `backend/application/services/fire_analysis_service.py`;
- `backend/application/services/planning_initial_wealth_fact_builder.py`;
- `tests/unit/test_fire_analysis_service.py`.

**Files modified:**

- `backend/api/planning_mapping.py` only to reuse/re-export the extracted manual fact builder.

**Dependencies:** D1; existing resolver, facts, assumptions, target solver, required solver.

**Contract rules implemented:** one resolution, two allowed sources, explicit manual observation, three mode branches, fixed REAL output/basis, Planning-owned Fisher/calendar/solvers, canonical target reuse, neutral required template, provenance continuity.

**Tests:** orchestration matrix, mock resolver/solvers, object identity, no double resolution, result equality with injected solvers, no write calls, relevant Planning regressions.

**Static audits:** no FastAPI/Pydantic dependency in service; no financial serialization; no projection/search math; no commits/writes.

**Success gate:** orchestration tests prove one fact and one solver maximum, target CEILING passed unchanged, REAL basis, preserved provenance/status, and no persistence.

**Explicit non-goals:** HTTP DTO, router, OpenAPI, frontend.

**Recommended model:** Terra High.

**Fresh context:** YES.

## 35. Implementation task D3 — FIRE API

**Purpose:** expose the locked authenticated transient API without moving calculations into HTTP code.

**Files created:**

- `backend/application/dtos/fire_dto.py`;
- `backend/api/fire_mapping.py`;
- `backend/api/fire_errors.py`;
- `backend/api/routers/fire.py`;
- `tests/unit/test_fire_api.py`.

**Files modified:**

- `backend/main.py`.

**Dependencies:** D1–D2.

**Contract rules implemented:** discriminated modes, strict Decimal/date/source shapes, one endpoint, auth, nullability, Decimal-string response, safe errors, existing Planning response semantics.

**Tests:** complete mode matrix, auth, errors, serialization, source rejection, OpenAPI, direct mapping with no recalculation.

**Static audits:** exactly one FIRE route; no optional soup; no Goal selector; no financial math in router/mapping; no global handler change.

**Success gate:** OpenAPI contains exactly authenticated `POST /api/v1/fire/analysis`; all three modes validate; incompatible fields are rejected structurally; D1–D3 and focused Planning API tests pass.

**Explicit non-goals:** frontend, persistence, chart, new auth, Planning refactor.

**Recommended model:** Terra High.

**Fresh context:** YES.

## 36. Implementation task D4 — FIRE Frontend Foundation

**Purpose:** add the route, client, strict form builders, basic/mode inputs, and entry points without result redesign.

**Files created:**

- `frontend/src/lib/fire.ts`;
- `frontend/src/app/wealth-intelligence/fire/page.tsx`;
- `frontend/src/app/wealth-intelligence/fire/components/fireForm.ts`;
- `frontend/src/app/wealth-intelligence/fire/components/fireForm.test.ts`;
- `frontend/src/app/wealth-intelligence/fire/components/FireInputs.tsx`.

**Files modified:**

- `frontend/src/config/navigation.ts`;
- `frontend/src/components/layout/TopNav.tsx`;
- `frontend/src/app/wealth-intelligence/page.tsx`.

**Dependencies:** D3 validated API/OpenAPI.

**Contract rules implemented:** pt-BR parsing, two-source selector, explicit manual timestamp, no defaults, human question labels, progressive mode fields, REAL-first path, nominal+inflation advanced path, exact request builders.

**Tests:** focused Vitest request-builder matrix and existing `planningLocale` regressions.

**Static audits:** no Goal source, no output-basis choice, no local financial calculation, no persistence, no enum labels shown to users.

**Success gate:** forms generate the exact three API variants; source/mode disclosure is accessible; typecheck, focused lint, and focused tests pass.

**Explicit non-goals:** final results hierarchy, chart, saved assumptions, broad Planning component extraction.

**Recommended model:** Terra High.

**Fresh context:** YES.

## 37. Implementation task D5 — FIRE Results & UX

**Purpose:** render the direct FIRE answer, mode result, assumptions, provenance, and complete interaction states.

**Files created:**

- `frontend/src/app/wealth-intelligence/fire/components/FireResults.tsx`.

**Files modified:**

- `frontend/src/app/wealth-intelligence/fire/page.tsx`;
- FIRE-specific files from D4 only when needed.

**Dependencies:** D4.

**Contract rules implemented:** target-first hierarchy, eligible wealth/progress/gap/conditional withdrawal, nested Planning result, provenance, safe conditional wording, loading/error/dirty/empty behavior, accessibility.

**Tests:** builder/client tests plus typecheck/lint/build; manual observable state matrix prepared. No new UI test framework.

**Static audits:** no guarantee/safe-rate wording, no browser math, no fabricated portfolio date, no chart recomputation.

**Success gate:** all result and state requirements are observable; BRL/rate/date formatting is string-safe; provenance and nested statuses remain intact.

**Explicit non-goals:** chart in initial MVP, recommendations, scenario comparison, UI redesign outside FIRE.

**Recommended model:** Terra High.

**Fresh context:** YES.

## 38. Implementation task D6 — Integration & Stabilization

**Purpose:** validate the complete backend/frontend slice and repair only in-contract regressions.

**Files created:** none expected.

**Files modified:** only evidence-backed fixes inside D1–D5 scope.

**Dependencies:** D1–D5 complete.

**Contract rules validated:** all ADR-025 rules, exact endpoint, Planning reuse, no persistence, no frontend truth, navigation/route integrity.

**Tests:** all FIRE backend tests; selected Planning regression list; focused frontend Vitest; `tsc --noEmit`; focused ESLint; production build; OpenAPI audit; static write/math/secret audit.

**Static audits:** import direction, route count, no migration/model/write, no float truth, no duplicate projection/solver, no localStorage, no deferred-feature leakage.

**Success gate:** automated checks pass or only explicitly unchanged historical Investments debt remains; manual UI smoke script/evidence checklist is ready.

**Explicit non-goals:** independent phase closure, new feature expansion, broad repository cleanup.

**Recommended model:** Terra High.

**Fresh context:** YES.

## 39. Implementation task D7 — Independent Validation & Closure

**Purpose:** independently validate the implemented slice against ADR-025 and close or block Phase 10.4.

**Files created:** validation report only if the established documentation pattern requires one.

**Files modified:** canonical status documents only after evidence supports closure.

**Dependencies:** D6 green and manual UI evidence available.

**Contract rules validated:** complete source-of-truth, numerical golden vectors, composition, API, UI, provenance, read-only, security, deferred boundaries.

**Tests:** fresh-context adversarial review, proportional reruns, independent Decimal oracle for FIRE-specific summary only, manual UI validation, final diff/status audit.

**Static audits:** production code cannot be its own oracle; no scope expansion during validation.

**Success gate:** exactly `PHASE 10.4 VALIDATED / CLOSED` or `BLOCKED — RECONCILIATION REQUIRED`.

**Explicit non-goals:** implementing fixes that change the locked contract; starting Phase 10.5 or Copilot.

**Recommended model:** Sol High.

**Fresh context:** YES.

## 40. Dependency graph and execution gates

```text
D1 FIRE Domain Core
  |
  v
D2 Application Orchestration
  |
  v
D3 API
  |
  v
D4 Frontend Foundation
  |
  v
D5 Results & UX
  |
  v
D6 Integration & Stabilization
  |
  v
D7 Independent Validation & Closure
```

Hard gates:

- D2 cannot start until D1 pure tests pass.
- D3 cannot start until one-resolution/solver-reuse/provenance tests pass.
- Frontend cannot start until D3 API and OpenAPI are validated.
- D5 cannot start until D4 request builders and disclosure pass.
- D6 requires D1–D5 complete.
- D7 performs no feature expansion.

Seven tasks are retained because each boundary has a distinct review oracle: pure FIRE math, application composition, HTTP contract, form/request foundation, result UX, integration, and independent closure. Fusing them would weaken gates; splitting further would create unnecessary microtasks.

## 41. Estimated change surface

Expected implementation surface before closure documentation:

- backend: 8 new production files, 2 minimally modified production files;
- backend tests: 3 new focused files;
- frontend: 6 new files, 3 minimally modified integration files;
- migrations/models/repositories: 0;
- existing Planning engine/solver files: 0;
- existing Health/Goals/Investments production files: 0.

The shared manual fact-builder extraction is the only planned change to an existing Planning path. It must be behavior-preserving and regression-tested.

## 42. Principal risks and mitigations

| Risk | Mitigation/gate |
|---|---|
| Optional-field soup accepts incompatible modes | top-level discriminated union plus extra-forbid variants |
| Manual wealth timestamp is silently manufactured | FIRE builder requires explicit `observed_at`; do not reuse Planning form builder wholesale |
| Goal source leaks into FIRE | FIRE-specific union contains only two existing source DTOs; structural API/frontend tests |
| Portfolio resolved twice | service resolves before branching and tests exact call count/object identity |
| Target rounds down | golden CEILING vector and exact target assertion at solver boundary |
| Monthly withdrawal derives from rounded annual | detecting golden vector D |
| FIRE duplicates Planning math | import/static audit and injected solver equality tests |
| Nominal/real conversion occurs twice | FIRE constructs Planning assumptions only; no Fisher code; matrix tests |
| Solver outcome becomes HTTP error | API tests preserve valid status as 200 |
| API leaks float | strict Decimal-string DTOs and JSON type assertions |
| Frontend becomes financial authority | static ban plus string-only formatting/builders |
| Result language implies guarantee | copy audit and manual UX gate |
| Broad Planning UI refactor causes regressions | reuse primitives/patterns, not entire Planning components |
| FIRE route crowds navigation | one concise `Independência Financeira` entry; manual responsive check |
| Persistence sneaks in as convenience | no model/migration/repository/localStorage; static write audit |

## 43. Blockers

`NONE`

The existing code supports the locked contract. The minor builder extraction is an implementation detail, not a contract reconciliation.

## 44. Explicit out of scope

No implementation task may add Health inference, Goal linkage, dividends, external income, reserve adjustment, taxes, longevity, Monte Carlo, FIRE variants, scenario comparison, persistence, portfolio advice, macro defaults, telemetry infrastructure, LLM behavior, or a second Planning engine/solver.

## 45. First authorized implementation task after approval

`PHASE 10.4-D1 — FIRE DOMAIN CORE`

Do not start D1 until the user explicitly approves implementation.

## 46. Current stop state

- Phase 10.4-A: `AUDIT COMPLETE`.
- Phase 10.4-B: `CONTRACT LOCKED`.
- Phase 10.4-C: `IMPLEMENTATION PLAN READY / AWAITING USER APPROVAL`.
- FIRE implementation: `NOT STARTED`.
- Commit: `NOT CREATED`.
- Push: `NOT EXECUTED`.

`WAITING FOR USER APPROVAL BEFORE FIRE IMPLEMENTATION`
