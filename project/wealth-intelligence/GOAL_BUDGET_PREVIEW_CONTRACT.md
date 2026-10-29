# Goal Budget Preview — R6.5 microcontract

**Status:** `R6.5-A CONTRACT APPROVED / R6.5-B IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED / R6.5-C IMPLEMENTED — AUTOMATED GATES PASSED — USER ACCEPTED — PUBLICATION PENDING`

**Date approved:** 2026-10-28

**Journey:** A — Goals and integrated planning.

**Authority:** explicit project-owner decisions D1–D3 in TSK-R6.5-A, recorded
under ADR-027 in `DECISION_LOG.md`. This is the phase-specific executable
contract, not a second roadmap. `IMPLEMENTATION_ROADMAP.md` owns sequencing.
The previous roadmap entry remains historical proposal evidence; this contract
supersedes its provisional field names, optional inverse-solve baseline and
unresolved decisions. No accepted ADR or existing locked contract is amended.

R6.5-A approved the contract only. R6.5-B was separately authorized and is now
`IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED`; see section 12 for
dated implementation evidence and section 13 for later publication/integration.
R6.5-C was separately authorized, implemented, automated-tested and user accepted;
publication requires separate authorization. The backend task itself did not
authorize frontend, persistence, provider calls, commits or publication.

## 1. Objective and approved decisions

Compare the effects of two user-chosen distributions of the same monthly
contribution total across the same owned Goals, under one explicit monthly
budget and one common nominal planning premise set.

- **D1 — approved:** exactly scenarios `A` and `B`, with the same owned Goals,
  reread target/current facts, explicit horizon, hypothetical rate, nominal
  basis and user budget. Only per-Goal contribution distribution varies.
  `allocated_total_A == allocated_total_B` is mandatory, with exact Decimal
  equality, not a tolerance. Identical distributions are valid. A is the fixed
  comparison reference; B is the alternative, not a recommended choice.
- **D2 — approved:** nominal return, output and target basis only. No inflation,
  real conversion or nominal/real mixing. Existing effective-annual rate,
  end-of-month contribution and certified rounding conventions remain intact.
- **D3 — approved:** an allocated total above the budget is valid. Expose the
  excess without rejecting solely for that excess, clipping contributions,
  redistributing funds or asserting affordability/sustainability.

Budget and contributions are scenario `ASSUMPTION` values explicitly supplied
by the user. The budget is not bank balance, Profile gross income, observed
Health surplus or certified sustainable contribution capacity. 10.3.7-A remains
separately deferred; no Health-derived prefill is introduced.

## 2. API boundary and reuse decision

```text
POST /api/v1/planning/goals/budget-preview
```

Authentication is mandatory, with one JSON body and no query parameters.
Reuse the Planning router, `CurrentPlanningUser`, `PlanningReadSession`, reader
dependency and local safe error translation.

The additive orchestration is necessary after inspecting existing boundaries:

- R6.4 `GoalBatchContributionPreviewService.preview` delegates to
  `RequiredContributionSolver.solve`: it replaces a candidate contribution to
  find the required amount, so it does not project the chosen allocation.
- The existing `/projection` evaluates one scenario and supplies no multi-Goal
  budget/ownership envelope. The existing `/scenarios/compare` has no budget
  accounting and one optional shared target, not a different target per Goal.
- Extending those locked request/response contracts to represent budgeted Goal
  distributions is unnecessary. Keep them unchanged; add one thin orchestration
  over the existing owned batch reader and `ScenarioComparisonEngine.compare`.
  No internal HTTP, second projection engine or parallel financial architecture.

R6.1 supplies source/ownership semantics; R6.2's null/zero and cadastral-vs-real
wealth distinction is preserved, without adding a progress calculation here;
R6.3/R6.4 supply the existing batch read boundary. R6.4's factual unavailable
codes are reusable, but its inverse solver is **not executed** in R6.5.
Required contribution is neither the chosen contribution nor a required output
of this contract. It remains available through the unchanged R6.4 capability.

## 3. Request DTO and validation

Define `GoalBudgetPreviewRequestDTO` using `_PlanningRequestDTO` and the existing
`StrictDecimalString`, `StrictISODate`, UUID and `StrictInt` conventions.
Nested request DTOs are `GoalBudgetAssumptionsRequestDTO`,
`GoalBudgetAllocationRequestDTO` and `GoalBudgetScenarioRequestDTO`.
Unknown fields are forbidden at every request level.

Required top-level fields:

- `goal_ids`: ordered 1–20 unique UUIDs, retaining the R6.4 batch limit;
- `monthly_budget`: finite nonnegative cent-scale Decimal string;
- `assumptions`: the shared fields below;
- `target_value_basis`: required literal `NOMINAL`;
- `scenarios`: exactly two items, ordered `A`, then `B`.

Shared `assumptions` requires `as_of_date` (ISO civil date),
`expected_return_rate` (finite plain Decimal string, effective annual fraction
strictly greater than -1), `return_type=NOMINAL`, `output_mode=NOMINAL`,
`horizon_months` (strict integer 1–1200), `rate_basis=EFFECTIVE_ANNUAL` and
`contribution_timing=END_OF_MONTH`. All are explicit, including zero return.
There is no rate default. `inflation_rate` and `target_date` are not request
fields, even when null. Goal dates never infer the horizon.

Each scenario requires `scenario_id` (respectively `A` or `B`) and `allocations`.
Every allocation has exactly `goal_id` and `scenario_monthly_contribution`,
the latter a finite nonnegative Decimal string with at most two decimal places.
Each scenario must allocate explicitly to every selected Goal exactly once.
Reject missing, extra or duplicate allocation IDs. Allocation input order may
vary; normalize output to `goal_ids` order. No omitted allocation becomes zero.
Reject per-scenario budget, rate, horizon, source, target or premise overrides.

Use exact Decimal sums to validate equal allocated totals before database reads
or comparison execution. Equality is numeric (`"1200"` equals `"1200.00"`), not
lexical; no float, tolerance, rounding or auto-balancing. A single Goal is valid,
even though equal totals then imply the same allocation. Zero budget and zero
contributions are valid; missing/null, negative, non-finite, exponent notation,
JSON numbers and excess fractional money precision are invalid. Existing
Planning rate syntax/domain applies without a new arbitrary return ceiling.

Example with synthetic identifiers and equal allocated totals:

```json
{
  "goal_ids": [
    "00000000-0000-0000-0000-000000000001",
    "00000000-0000-0000-0000-000000000002"
  ],
  "monthly_budget": "1500.00",
  "assumptions": {
    "as_of_date": "2026-10-28",
    "expected_return_rate": "0.05",
    "return_type": "NOMINAL",
    "output_mode": "NOMINAL",
    "horizon_months": 120,
    "rate_basis": "EFFECTIVE_ANNUAL",
    "contribution_timing": "END_OF_MONTH"
  },
  "target_value_basis": "NOMINAL",
  "scenarios": [
    {
      "scenario_id": "A",
      "allocations": [
        {"goal_id": "00000000-0000-0000-0000-000000000001", "scenario_monthly_contribution": "800.00"},
        {"goal_id": "00000000-0000-0000-0000-000000000002", "scenario_monthly_contribution": "400.00"}
      ]
    },
    {
      "scenario_id": "B",
      "allocations": [
        {"goal_id": "00000000-0000-0000-0000-000000000001", "scenario_monthly_contribution": "600.00"},
        {"goal_id": "00000000-0000-0000-0000-000000000002", "scenario_monthly_contribution": "600.00"}
      ]
    }
  ]
}
```

## 4. Response DTO and provenance

`GoalBudgetPreviewResponseDTO` contains exactly:

- `monthly_budget`: the explicit shared Decimal-string budget;
- `assumptions`: reuse `GoalBatchContributionAssumptionsResponseDTO` as the
  shared effective premise echo (nominal constants, explicit horizon, and
  `inflation_rate=null` because no inflation participates);
- `target_value_basis`: `NOMINAL`;
- `reference_scenario_id`: `A`;
- `scenarios`: two `GoalBudgetScenarioResponseDTO` items, ordered A/B;
- `results`: one `GoalBudgetItemResponseDTO` per Goal, in `goal_ids` order.

Each scenario summary contains `scenario_id`, `allocations` (normalized ordered
ID/contribution echoes), `allocated_total`, `unallocated_amount` and
`exceeded_amount`. Financial fields are Decimal strings, never JSON numbers.
Use the same ID/contribution shape in `GoalBudgetAllocationResponseDTO`.

Each Goal result contains `goal_id`, `name`, `target_amount`, `current_amount`,
`source_type` (literal `USER_GOVERNED_GOAL`), `goal_updated_at` (persisted ISO
timestamp or null), `initial_wealth_fact` (existing
`InitialWealthFactResponseDTO` or null), `availability`, `impediment_code` and
`comparison` (existing `ScenarioComparisonResponseDTO` or null).

Source amounts remain decimal strings or null; no reread from legacy float
Goals DTOs. `goal_updated_at` is the cadastral record update time, not a market
quote or a guarantee of reproducible historical Goal state. This endpoint reads
the current Goal record; `as_of_date` anchors the scenario, not Goal time travel.
The fact uses only `GOAL_CURRENT_AMOUNT`, `scope=GOAL` and the existing public
provenance mapper. Emit a fact for a present nonnegative current amount, even
if the target is unavailable; otherwise `initial_wealth_fact=null`.
Do not invent a timestamp. Internal table names, SQL and owner IDs stay private.

For an available Goal, `comparison` is the unchanged existing comparison DTO:
two ordered A/B entries, the same Goal fact/target and common assumptions,
per-entry contribution, complete certified projection and target result,
and engine-produced deltas. Use existing nested DTOs/mappers instead of
recalculating or flattening certified output into a second truth path.
An unavailable Goal has `comparison=null`, including no fabricated zero deltas.

## 5. Budget arithmetic and Decimal authority

For each scenario, using only the explicit monthly flows:

```text
allocated_total_A = sum(A allocations)
allocated_total_B = sum(B allocations)
require allocated_total_A == allocated_total_B
unallocated_amount = max(monthly_budget - allocated_total, 0)
exceeded_amount = max(allocated_total - monthly_budget, 0)
```

Include allocations to unavailable Goals in totals: they are still intended
spending, not missing financial facts. Since A/B have equal totals and budget,
their unallocated and exceeded amounts are necessarily equal; only per-Goal
projected effects differ. Zero budget with a positive allocated total returns
the full excess; zero totals yield the full unallocated budget. No separate
signed balance field is needed. Never sum Goal current wealth, future wealth,
growth, targets or required contributions into a consolidated patrimony total.

Use Decimal end to end. Exact budget sums/equality/subtractions must use a local
context with sufficient precision for all supplied digits and batch size, not
ambient default precision; never mutate global context or round inputs to fit.
Money accepts at most two fractional digits, as certified Planning inputs do.
Preserve fact precision and zero/absence. Reuse existing serializers and
engine-owned `ROUND_HALF_EVEN`; the mapper performs no financial arithmetic.

## 6. Certified projections and comparison metrics

For each calculable owned Goal construct two `ScenarioDefinition` values with
IDs A/B and the **same** `InitialWealthFact`, from
`PlanningGoalReadQuery.current_amount_as_initial_wealth(goal)`. Construct two
`ProjectionAssumptions` from the same common premises, differing only in
`scenario_monthly_contribution`. Invoke:

```text
ScenarioComparisonEngine.compare(
    scenarios=(A, B), reference_scenario_id="A",
    target_amount=owned_goal.target_amount,
    target_value_basis=TargetValueBasis.NOMINAL
)
```

The existing engine delegates to `TargetAchievementSolver` and
`ForwardProjectionEngine`, including full-horizon projection reuse and the
already-achieved fallback. No inverse solver, compounded-interest formula,
target-crossing search or date calculation is added to R6.5.

Comparison metrics are copied **only** from the returned certified entry:

- `projection_result.final_wealth`, `total_contributions` and
  `total_projected_growth`: that Goal's full explicit horizon, not wealth at
  first achievement;
- `final_wealth_delta`, `total_contributions_delta`,
  `total_projected_growth_delta`: B minus reference A, as already computed by
  `ScenarioComparisonEngine`; A's reference deltas remain its certified zero;
- `target_achievement_result.status`, `months_required`, `achievement_date`,
  `achievement_period` and `achieved_wealth`: `TargetAchievementSolver` outputs;
- `months_saved_or_lost`: engine-owned A months minus B months. Positive means
  B attains that same Goal sooner; it is not an overall scenario ranking.
  The existing engine returns null unless both statuses are ACHIEVED or
  ALREADY_ACHIEVED. Missing dates/months remain null, never extrapolated.

UNREACHABLE and NOT_REACHED_WITHIN_HORIZON are valid calculated solver states,
not missing-data failures: keep available projections and certified deltas,
but no invented achievement date or time difference. Results above target and
negative monetary deltas retain their meaning/sign. Never rank or recommend a
Goal/scenario, infer returns, or claim either distribution is sustainable.

## 7. Ownership, collection, availability and errors

Resolve `goal_ids + authenticated current_user.id` once through
`PlanningGoalReadQuery.get_goals_by_ids`. Ownership must be in SQL, not only in
response transformation. Verify complete requested-ID correspondence and owner
consistency before any projection. Missing or foreign IDs return the same
whole-request `404 {"detail":"One or more Goals were not found."}`, without
which-ID disclosure, partial foreign results or engine execution.
Authentication follows existing Planning 401 behavior; invalid UUIDs and
request validation failures return 422. No caller `user_id` is accepted.

For accessible Goals, retain R6.4 factual availability values/codes (reuse
`GoalBatchContributionAvailability` and `GoalBatchContributionImpediment`),
with the same precedence: target absent → TARGET_MISSING; target <= 0 →
TARGET_NONPOSITIVE; current absent → CURRENT_AMOUNT_MISSING; current < 0 →
CURRENT_AMOUNT_NEGATIVE. These yield `UNAVAILABLE`, null comparison, and no
calculation for that Goal; other owned Goals may still be available. Explicit
current zero is valid. Budget summaries remain complete even if every Goal's
projection is unavailable. The current persisted reader requires a target;
absent-target domain fixtures are defensive coverage, not permission to relax
the reader/schema. A broken reader precision/type invariant remains an error.

Lifecycle/type is reported by its existing owner and gains no new rejection
policy in this arithmetic preview. No inference that a cadastrally completed
Goal has attained its financial target. This does not change the separate
Goal Planning endpoint's eligibility rules.

422 also covers empty/over-limit collections, unequal totals, scenario/ID
coverage/order errors, negative/invalid amounts, unsupported real/inflation
fields, invalid rates/horizon, overrides and unknown fields. Unequal totals
use a generic Planning validation detail without echoing financial data. Run
this cross-field check before SQL through local Planning validation/error
translation (or an equivalent route-local safe validation response); no global
FastAPI error-handler change is required. Excess alone
is never a 422. Unexpected read/engine/mapping failures fail the whole request
through existing generic Planning error handling; do not turn exceptions into
fabricated per-Goal unavailability or expose SQL, stack traces or secrets.

## 8. Bounds, read-only operation and exclusions

Reuse the existing 20-Goal bound and 1–1200 month horizon. Exactly two scenarios
bound the work to one comparison invocation per available Goal, at most 40
scenario evaluations; existing solvers may internally invoke projections.
There is one Goal SQL read, no N+1 and no extra per-Goal HTTP call. The existing
full-period response is bounded by this collection/horizon, not silently
truncated or paginated. No monetary aggregate is presented as portfolio wealth.

No INSERT/UPDATE/DELETE, flush/commit, Goal mutation, simulation persistence,
schema/migration, cache, scheduler, job, automatic allocation, optimization,
investment operation, tax/fee model, Health capacity engine, FIRE linkage,
MyProfit/portfolio/Wealth Home read, market rate, AI/provider call, frontend or
new dependency. No changes to R6.1–R6.4, the original five Planning POSTs,
certified Engines, public legacy Goals DTOs, ADRs or locked contracts.

## 9. R6.5-B — single executable backend task

**State at implementation completion (historical; current state in section 13):**
`IMPLEMENTED / FOCUSED TESTS PASSED / CHECKPOINT PENDING`.
Contract readiness was not permission to implement during R6.5-A. The separately
authorized R6.5-B task follows the unchanged scope below: implement only
the endpoint/DTO/orchestration and tests below, stopping after documentation of
the actual results. No R6.5-C, new contract decision, commit or push is implied.

Modify only the necessary existing implementation files:

- `backend/application/dtos/planning_dto.py`: strict request/response DTOs and
  structural/coverage/nominal validation; reuse existing primitives/nested DTOs;
- `backend/api/planning_mapping.py`: pure assumptions builder and response
  mapping through existing comparison/fact serializers; no arithmetic in mapper;
- `backend/api/routers/planning.py`: one authenticated POST and service
  dependency, pre-read equal-total validation, one existing batch read,
  complete-ID/owner guard, safe errors.

Create only the necessary pure orchestration and focused tests:

- `backend/domains/planning/goal_budget.py`: immutable request/result values,
  exact local-Decimal budget accounting and `GoalBudgetPreviewService` over an
  injected existing `ScenarioComparisonEngine`; no SQL or new financial engine;
- `tests/unit/test_goal_budget.py`: budget/selection/availability/orchestration
  tests with independent Decimal expected values and comparison parity;
- `tests/unit/test_planning_goal_budget_api.py`: real JSON/API/ownership/read-only
  and OpenAPI tests using the existing isolated test infrastructure.

The reader `backend/domains/planning/readers.py` already provides the exact
batch/fact methods and should remain unchanged. Reuse without modifying
`scenario_comparison.py`, `target_solver.py`, `projection.py` and
`goal_batch_contribution.py`. If this requires an Engine/locked-contract change,
stop rather than patching around a contract incompatibility.

Existing route/OpenAPI allowlist candidates, verified in the current repository:

- `tests/unit/test_planning_api_calculation_endpoints.py`;
- `tests/unit/test_planning_api_foundation.py`;
- `tests/unit/test_planning_api_integration.py`;
- `tests/unit/test_planning_api_goal_endpoint.py`;
- `tests/unit/test_planning_api_scenario_comparison.py`;
- `tests/unit/test_planning_goal_context_api.py`;
- `tests/unit/test_planning_goal_progress_api.py`;
- `tests/unit/test_planning_goal_overview_api.py`;
- `tests/unit/test_planning_goal_batch_contribution_api.py`;
- `tests/unit/test_profile_context_api.py`.

Update these only where their actual allowlists require the new POST; never
weaken assertions or alter unrelated fixtures. Reader/Engine regressions run
without changing their production owners. Update this contract's implementation
evidence and the existing state/roadmap/changelog only after real execution.

## 10. Required tests and acceptance

Unit cases: under/exact/over budget, zero budget/allocations, cent/large values,
equal totals with different lexical scale, unequal totals, default-context
precision stress, identical A/B, one and 20 Goals, stable order and no duplicate
IDs. Cover all factual unavailable codes, lifecycle/type independence,
target already attained, zero/negative-but-valid/positive hypothetical return,
positive/zero contribution, horizon boundaries, target unreachability and
nonattainment. Keep null dates/deltas distinct from certified zero results.

HTTP/integration cases: authenticated two-identity isolation; identical foreign
and missing 404 with no comparison; malformed UUID, missing/extra/duplicate
allocation, invalid scenario count/order, unequal totals, strict Decimal JSON
strings, absent/null/negative money, forbidden inflation/real/overrides,
invalid rate and horizon 422; no query per Goal, no write/flush/commit,
no MyProfit/portfolio/Health/provider read. Capture one SQL batch read and spy
on exact same-Goal A/B engine inputs; prove the inverse solver is never called.

Comparison parity: compare full nested results and all exposed deltas to direct
existing `ScenarioComparisonEngine` results, plus independent known-output
zero-rate cases. Verify full-horizon outputs when the target is attained early
or already attained, B-minus-A sign, nullable months-saved, identical-scenario
zeroes and per-Goal (never cross-Goal) targets. No duplicated projection math.

OpenAPI must add exactly this authenticated POST while preserving all three
R6.1–R6.3 GETs, R6.4 POST and five original Planning POSTs. Run focused new
domain/API tests from repository root with `python -m pytest`, then relevant
Goals/Planning regressions per `TESTING_STRATEGY.md`, using disposable fixtures
and mocked external boundaries; no active database, internet, LLM or frontend
tests. Record actual commands/counts/warnings, never inherited pass claims.

Acceptance: equal-total A/B distributions yield exact budget summaries and
owned certified per-Goal results, even when over budget; insufficient facts
stay explicitly unavailable; no financial write or source/contract regression.
R6.5-B is implemented/tested only after those gates pass. R6.5-C later validates
the complete minimal user journey under a separate task; no UI acceptance is
claimed here.

## 11. Dependencies, AI continuity and current evidence

R5 CLOSED, general R6 gate SATISFIED and published R6.1–R6.4 are existing inputs,
not reopened approvals. This contract creates no new dependency on Health,
portfolio attribution or AI. After R6.5-B and authorized R6.5-C, retain the
roadmap's explicit R4 safety/audit, synthetic pilot, Ollama/Qwen, Gemini and
comparative test milestones. `LOCAL_ONLY` stays default. Operational protected
execution requires its actual audit/consent gates; no real financial data may
be sent remotely by this task. R7/10.5-B gates and later-increment permissions
remain unchanged.

**Evidence for R6.5-A:** documentary/code-boundary inspection only. No R6.5
endpoint, DTO, service or test has been implemented or executed. No additional
material business decision or higher-contract incompatibility was identified
for the bounded contract above. Backend implementation awaits its explicit task.

## 12. R6.5-B implementation evidence — 2026-10-29

**State:** `IMPLEMENTED / FOCUSED TESTS PASSED / CHECKPOINT PENDING`.
R6.5-A remains `CONTRACT APPROVED`; R6.5-C remains `PLANNED / NOT STARTED`;
R4 AI remains separately gated. D1–D3 and the normative boundaries above are unchanged.

Preflight matched `develop`, HEAD
`40a23566b3b068e26cb8bd3ae94bc7ed060ec4b0`, an empty index, exactly the ten
expected modified tracked documents and this untracked contract. The prior
documentary work was retained; no unexpected code change was present.

Implemented the strict request/response DTOs, pure builder/serializers, one
authenticated Planning POST and injected `GoalBudgetPreviewService` in the
six implementation/test paths specified in section 9. Existing allowlists
changed only by the new exact POST (nine existing test files; the R6.4 API test
needed no allowlist edit). No Engine, reader, legacy Goal DTO, locked contract,
dependency, migration, frontend or historical laboratory changed.

The request validates ordered A/B coverage and equal allocated totals before
SQL. Budget sums/subtractions use locally sized Decimal precision, including
large magnitudes/carry and cent differences hidden by ambient precision.
One ownership-filtered SQL batch read resolves all Goals; complete ID/owner
correspondence is checked before engine execution. Each available Goal uses
one certified comparison over the same cadastral fact/target and common nominal
premises. Existing nested serializers copy projections, statuses and deltas.
Unavailable comparisons stay null; their intended allocations remain in totals.
Excess is permitted, explicit, and never labeled sustainable or recommended.
Unexpected reader/type/engine/mapper errors return generic internal errors.

Final executed commands, from the repository root using the existing venv:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_goal_budget.py tests/unit/test_planning_goal_budget_api.py -q -p no:cacheprovider --basetemp=.pytest_tmp/r65-focused-final
$focused = @(Get-ChildItem tests/unit/test_planning*.py, tests/unit/test_goal*.py, tests/unit/test_profile_context_api.py, tests/unit/test_fire*.py | Select-Object -ExpandProperty FullName)
& .\.venv\Scripts\python.exe -m pytest @focused -q -p no:cacheprovider --basetemp=.pytest_tmp/r65-regression-final
```

- New domain/API suites: **192 passed, 3 warnings**, 5.48 seconds.
- Relevant Planning/Goals/FIRE/Profile selection: **946 passed, 113 warnings**,
  13.44 seconds, including those 192 tests; these counts are not additive.
- Warnings are in existing Pierre Pydantic configuration, Goals UTC timestamp
  calls and asynchronous repository mocks. Initial test-authoring failures were
  corrected before these final runs; an existing pytest cache warning was
  avoided with `-p no:cacheprovider`, without altering cache files.
- Real isolated SQLite capture proves one SELECT with ownership and ID filters,
  no per-Goal query and no write/flush/commit or Goal mutation. Dynamic guards
  forbid inverse solver, portfolio/MyProfit source and Health reads; the new
  path has no AI/provider integration. Fixtures require no internet/active DB.
- OpenAPI preserves R6.1–R6.4 and the five original POSTs, adding precisely the
  new authenticated budget POST. Full nested parity and independent zero-rate
  oracles cover certified outputs/deltas and early/already-attained targets.

No staging, commit, push, deploy or R6.5-C work was performed. Backend checkpoint
and subsequent UI integration remain separate tasks; no UI acceptance is claimed.

Final Git gates: branch/HEAD unchanged, index empty, 22 modified tracked paths
(the ten prior documents, three implementation files and nine exact allowlists)
plus four untracked paths (this contract and the three new code/test files).
`git diff --check`, explicit whitespace/single-EOF checks for all 26 paths and
`git diff --no-index --check` for all four untracked files passed. No protected
Engine/reader, locked contract, migration, frontend or historical lab changed.

## 13. Publication and frontend status — 2026-10-29

R6.5-B was subsequently committed and pushed as functional
`754a9dedf3fe57590c0af3f524573a14b6dfe961` followed by documentary
`b59e2af63fbc6a093bafa4a50a375571a1877ab6`; the controlled push confirmed the
latter as the real remote `develop` SHA. Section 12 retains the implementation
task's pre-checkpoint facts rather than rewriting its chronology.

R6.5-C now consumes this exact API under the separately authorized frontend
task. Its effective state is `IMPLEMENTED / AUTOMATED GATES PASSED / USER
ACCEPTED / PUBLICATION PENDING`; Journey A is functionally accepted. Current
implementation/tests/manual acceptance evidence is owned by
`CURRENT_STATE.md`; the single queue and the unchanged separately gated R4
safety/audit/local/online sequence remain in `IMPLEMENTATION_ROADMAP.md`.
D1–D3, financial input/output semantics, Engine boundaries and errors in
sections 1–8 are unchanged. No later phase is authorized by this status record.
