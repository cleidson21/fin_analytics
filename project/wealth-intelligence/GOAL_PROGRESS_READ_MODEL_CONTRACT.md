# Goal Progress Read Model — R6.2 microcontract

**Status:** `APPROVED / IMPLEMENTED / FOCUSED TESTS PASSED / CHECKPOINT PENDING`

**Date approved:** 2026-10-27

**Phase:** `TSK-R6.2 — GOAL PROGRESS READ MODEL`

## 1. Authority and scope

The project owner explicitly authorizes one authenticated, read-only Planning
endpoint that reports the nominal cadastral progress of an owned Goal. This
microcontract is phase-specific truth under the accepted ADR hierarchy. It does
not alter ADR-023, ADR-024, ADR-025, ADR-027, `PLANNING_UX_CONTRACT.md`, or any
certified Planning/FIRE engine contract.

The endpoint is:

```text
GET /api/v1/planning/goals/{goal_id}/progress
```

It has one UUID path parameter, no query parameters, no request body, and no
writes or side effects.

## 2. Source and ownership

The sole source is the existing `PlanningGoalReadQuery.get_goal(...)` result,
resolved by `goal_id + authenticated user_id`. The read fact is
`GoalPlanningFact`; no parallel Goal reader is permitted.

Missing Goals and Goals owned by another user both return the same `404`.
Invalid UUIDs retain FastAPI `422`; authentication and session behavior reuse
the existing Planning dependencies. Unexpected failures return a generic `500`
without SQL, authentication detail, or financial values.

The endpoint must not read Wealth Home, MyProfit, portfolio snapshots, market
quotes, macroeconomic context, dividends, or AI output. `current_amount` is the
manual cadastral Goal fact and is not automatically synchronized investment
wealth.

## 3. Response contract

```json
{
  "goal_id": "00000000-0000-0000-0000-000000000000",
  "name": "Reserva de emergência",
  "target_amount": "50000.00",
  "current_amount": "18500.00",
  "gap_amount": "31500.00",
  "completion_percent": "37.00"
}
```

Money and percentage values are plain decimal strings or `null`. Explicit zero
remains a decimal string and is never converted to absence. No float or JSON
number crosses the response boundary.

## 4. Deterministic calculation

All arithmetic uses finite Python `Decimal` values inside a local precision
context and never mutates the process-global Decimal context.

```text
gap_amount = target_amount - current_amount
completion_percent = (current_amount / target_amount) * 100
```

- `gap_amount` is signed and unquantized beyond the exact subtraction of the
  stored Decimal facts. It may be positive, zero, or negative.
- `completion_percent` is available only when `target_amount > 0` and
  `current_amount` is present.
- The percentage is quantized to `0.01` with explicit `ROUND_HALF_EVEN`, the
  established backend financial rounding mode.
- Percentage values above `100.00` are preserved.
- A missing required operand makes the corresponding derived value `null`.
- A missing, zero, or negative target makes `completion_percent` `null`.

The current governed reader requires a non-null persisted target, but the pure
calculation retains explicit absent-target behavior for defensive contract
coverage. It invents no replacement value.

## 5. Legacy compatibility

The public Goals DTO and `Goal.progress_pct()` remain unchanged. That legacy
path uses float and caps progress at 100%, so it is not equivalent to R6.2 and
must not be reused by this endpoint. R6.2 introduces no change to legacy Goals
responses and no change to the five certified Planning POST operations.

## 6. Architecture and exclusions

Implementation is limited to:

- one immutable pure Decimal calculation/result;
- one Planning response DTO and mapper;
- one authenticated router GET;
- focused calculation, HTTP, ownership, OpenAPI, and regression tests.

No migration, table, scheduler, background job, persistence, frontend, engine
change, FIRE change, portfolio integration, projection, expected return,
inflation, target-date inference, LLM, R6.3+, R7, or Portfolio Intelligence is
authorized.

## 7. Acceptance gates

Tests must cover partial, exact, above-target, zero, null, non-positive target,
cent values, large Decimal magnitude, non-integer percentage, lifecycle status
independence, authentication, ownership/non-enumeration, invalid UUID, generic
failure, no writes, no engine/portfolio access, OpenAPI, and preservation of
the existing Planning routes.

## 8. Implementation evidence

R6.2 is implemented by the pure `goal_progress` calculation, one Planning DTO
and mapper, and the authenticated router GET over the existing
`PlanningGoalReadQuery`. The implementation changes no legacy Goals DTO, Goal
entity method, Planning POST, engine, persistence, schema, or frontend.

Validation on 2026-10-27:

- direct R6.2 calculation/API plus context/foundation regressions: `90 passed`;
- complete focused Goals and Planning unit selection: `611 passed`;
- OpenAPI exposes the two approved Planning GETs and preserves all five POSTs;
- warnings are unchanged legacy Pydantic, `datetime.utcnow`, async-mock, and
  Windows pytest-cache diagnostics; no new failure was observed.

The checkpoint is not staged, committed, pushed, or deployed. R6.3+ remains
unauthorized.
