# Goal Monitoring Overview Read Model — R6.3 microcontract

**Status:** `APPROVED / IMPLEMENTED / FOCUSED TESTS PASSED / CHECKPOINT PENDING`

**Date approved:** 2026-10-27

**Phase:** `TSK-R6.3 — CONSOLIDATED GOAL MONITORING READ MODEL`

## 1. Authority and objective

The project owner expressly authorizes one authenticated, read-only Planning
endpoint that consolidates the cadastral context from R6.1 and the certified
individual progress calculation from R6.2 for every Goal owned by the current
user. This microcontract is phase-specific truth under the accepted ADR and
`LOCKED` contract hierarchy.

The endpoint is:

```text
GET /api/v1/planning/goals/overview
```

It has no path parameter, query parameter, request body, write, or side effect.
It does not modify the responses of the R6.1 context endpoint or the R6.2
individual progress endpoint.

## 2. Authentication, ownership, and source of truth

Authentication is mandatory. The collection is loaded by the existing
`PlanningGoalReadQuery.list_goals(db, authenticated_user_id)` boundary, whose
database query filters ownership before facts are returned. The result uses
`GoalPlanningFact`; legacy float-based Goal DTOs are not a financial source.

The endpoint never performs a global Goal read followed by application-only
ownership filtering. A user with no Goals receives an empty collection and a
zeroed summary. Unexpected failures return a generic response without SQL,
authentication details, or financial values.

The read model does not query MyProfit, portfolio snapshots, market data,
macroeconomic context, dividends, or AI output. Goal `current_amount` remains a
manual cadastral fact and is not represented as automatically synchronized
investment wealth.

## 3. Collection semantics and performance

`summary` and `goals` refer to the same complete universe of owned Goals. This
endpoint is intentionally unpaginated: no existing governed Goal limit applies,
and a partial page must not be presented as a global total.

The reader performs one SQL statement for the collection, with no SQL query per
Goal. It provides deterministic ordering by priority ascending with nulls last,
then creation time descending, then Goal identifier ascending. The
transformation preserves that order and rejects duplicate identifiers rather
than silently emitting the same Goal twice.

## 4. Response contract

The response contains a count-only summary and one item per owned Goal:

```json
{
  "summary": {
    "total_goals": 1,
    "not_started": 0,
    "in_progress": 1,
    "achieved": 0,
    "exceeded": 0,
    "negative_current": 0,
    "unavailable": 0
  },
  "goals": [
    {
      "goal_id": "00000000-0000-0000-0000-000000000001",
      "name": "Reserva de emergência",
      "goal_type": "EMERGENCY_RESERVE",
      "status": "ACTIVE",
      "target_amount": "50000.00",
      "current_amount": "35000.00",
      "planned_monthly_contribution": "750.00",
      "target_date": "2028-12-31",
      "gap_amount": "15000.00",
      "completion_percent": "70.00",
      "progress_state": "IN_PROGRESS",
      "data_flags": []
    }
  ]
}
```

Financial values and the derived percentage are decimal strings or `null`.
Explicit zero remains a decimal string and is never converted to absence.

## 5. Certified progress reuse

Every item calls the existing R6.2 `calculate_goal_progress(...)` function.
That function remains the sole implementation for signed `gap_amount`, uncapped
`completion_percent`, `ROUND_HALF_EVEN`, unavailable operands, and percentage
values above 100%. R6.3 must not implement an equivalent formula independently,
use `Goal.progress_pct()`, or mutate the process-global Decimal context.

## 6. Progress-state classification

Each Goal belongs to exactly one category, evaluated in this order:

1. `UNAVAILABLE`: target is absent or nonpositive, or current amount is absent.
2. `NEGATIVE_CURRENT`: target is positive and current amount is negative.
3. `NOT_STARTED`: target is positive and current amount is exactly zero.
4. `IN_PROGRESS`: current amount is positive and below the positive target.
5. `ACHIEVED`: current amount equals the positive target.
6. `EXCEEDED`: current amount is above the positive target.

The derived category is independent of the cadastral Goal lifecycle status.
The seven summary fields are nonnegative integer counts, and the six category
counts always sum to `total_goals`.

## 7. Factual data flags

Flags report only the following observed conditions, in deterministic field
order:

- `TARGET_MISSING`;
- `TARGET_NONPOSITIVE`;
- `CURRENT_MISSING`;
- `CURRENT_NEGATIVE`;
- `MONTHLY_CONTRIBUTION_MISSING`;
- `MONTHLY_CONTRIBUTION_ZERO`.

Zero contribution is a fact, not an error or recommendation. No severity,
notification, persisted alert, target-date delay, probability, or financial
advice is inferred.

## 8. Decimal precision and absence semantics

Persisted financial facts remain Python `Decimal` through the governed reader
and domain transformation. Serialization uses the existing plain-decimal string
boundary. The model preserves `null` versus explicit zero and does not round
source facts unnecessarily.

## 9. No monetary consolidation

The summary contains counts only. It does not sum target amounts, current
amounts, contributions, investment wealth, or any other monetary fact. It does
not calculate a portfolio-wide completion percentage or imply that values
assigned to multiple Goals are disjoint. Any such aggregation requires a
separate authorized contract.

## 10. Architecture and exclusions

Implementation is limited to the existing batch Goal read, one immutable domain
transformation, response DTOs and mapper, one authenticated router GET, focused
tests, and minimum canonical documentation. It creates no table, migration,
cache, scheduler, job, persistence, notification, frontend, engine, FIRE change,
legacy Goal API change, Portfolio Intelligence integration, Advisor capability,
R6.4+, or deploy operation.

## 11. Tests and acceptance gates

Tests must cover empty, single, and multiple owned collections; two identities;
all progress states and flags; null and explicit zero; nonpositive target;
negative current; achieved and exceeded values; Decimal precision; exact R6.2
reuse; lifecycle-status independence; stable order; duplicate rejection; one
collection query without writes; no MyProfit, portfolio, or engine access;
generic failures; authentication; OpenAPI; static-route resolution; and
preservation of the R6.1, R6.2, and five Planning POST routes.

R6.3 is implemented only when the code matches this contract and the relevant
focused backend gates pass. Commit, push, publication, frontend consumption,
and R6.4+ remain separately gated.

## 12. Implementation evidence

R6.3 is implemented by one immutable domain transformation, response DTOs and
mapper, and the authenticated static Planning route over the existing
`PlanningGoalReadQuery.list_goals(...)` batch boundary. The transformation
calls the certified R6.2 calculation once per emitted Goal, preserves reader
order, rejects duplicate identifiers, and produces only count aggregates.

Validation on 2026-10-27:

- direct R6.3 domain/API plus reader and R6.1/R6.2 regressions: `68 passed`;
- complete focused Goals and Planning unit selection: `634 passed`;
- OpenAPI exposes the three approved Planning GETs and preserves all five POSTs;
- existing Pydantic, `datetime.utcnow`, and async-mock warnings remain
  non-blocking; no new failure was observed.

The checkpoint is not staged, committed, pushed, or deployed. Frontend
consumption and R6.4+ remain unauthorized.
