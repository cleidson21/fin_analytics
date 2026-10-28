# Goal Batch Contribution Preview — R6.4 microcontract

**Status:** `APPROVED / IMPLEMENTED / FOCUSED TESTS PASSED / CHECKPOINT PENDING`

**Date approved:** 2026-10-27

**Phase:** `TSK-R6.4 — PLANEJAMENTO CONJUNTO DE APORTES PARA METAS`

## 1. Objective and authority

The project owner expressly authorizes one authenticated, transient Planning
capability that calculates the monthly contribution required for each selected
Goal. It reuses the certified Required Contribution solver and does not create
another financial formula, engine, recommendation, ranking, persistence model,
or portfolio interpretation.

The endpoint is:

```text
POST /api/v1/planning/goals/batch-contribution-preview
```

This phase-specific contract does not alter ADR-023, ADR-024, ADR-025,
ADR-027, any `LOCKED` Planning contract, or the existing five Planning POST
responses.

## 2. Request contract

The request contains:

- `goal_ids`: an ordered collection of 1 through 20 unique UUIDs;
- `assumptions`: explicit `as_of_date`, `expected_return_rate`, `return_type`,
  `output_mode`, optional `inflation_rate`, required `horizon_months`,
  `rate_basis`, and `contribution_timing`;
- `target_value_basis`: the explicit nominal or real basis of every Goal target
  in this preview.

All rates are plain decimal strings and retain the existing Planning units:
`expected_return_rate` and optional `inflation_rate` are effective annual
fractional rates, `rate_basis` is `EFFECTIVE_ANNUAL`, and
`contribution_timing` is `END_OF_MONTH`. `horizon_months` is an explicit integer
from 1 through 1200. The request has no `target_date`, so neither a Goal date nor
the server clock can silently become the horizon. No default return is supplied.

The certified solver ignores a caller contribution while solving. R6.4
therefore does not expose `scenario_monthly_contribution`; its internal solver
template uses exact `Decimal("0.00")`, which the existing solver replaces with
each certified candidate.

The 20-Goal bound is an operational synchronous-computation limit, not a
financial rule. One Goal solve can evaluate multiple full projections of up to
1200 months; bounding the ordered batch prevents an unbounded multiplication of
that certified work without introducing pagination or partial totals.

## 3. Collection, authentication, and ownership

Authentication is mandatory. The server loads all selected Goals in one SQL
statement filtered by `authenticated_user_id` and the requested identifiers.
There is no query per Goal and no application-side filtering of a global Goal
collection.

Input order is preserved in the response. Duplicate IDs, an empty collection,
or a collection over the limit fail request validation with `422`. If any
selected identifier is missing or belongs to another user, the complete request
returns the same non-enumerating `404`; no partial result or foreign fact is
returned.

## 4. Financial sources and certified reuse

For every selected Goal:

- target is the owned cadastral `target_amount`;
- initial wealth is exclusively the owned cadastral `current_amount`, converted
  by `PlanningGoalReadQuery.current_amount_as_initial_wealth(...)` into the
  certified `GOAL_CURRENT_AMOUNT` fact;
- the calculation delegates directly to `RequiredContributionSolver.solve(...)`;
- target/output basis compatibility uses the existing Planning rule.

No Goal value is summed with another Goal. No portfolio snapshot, MyProfit,
Wealth Home, global wealth, market data, macroeconomic rate, user-provided
replacement wealth, or Goal planned contribution participates in the solve.

## 5. Result contract and unavailable data

The response contains one ordered item per selected Goal. Each item reports the
Goal ID and name, cadastral target and current amount, the explicit assumptions
and effective horizon, target basis, result availability, certified solver
status, required monthly contribution when calculable, and at most one factual
impediment code.

`AVAILABLE` means the existing solver produced a certified result. A zero
required contribution is a valid decimal string. `UNAVAILABLE` returns no
invented contribution and uses one of:

- `TARGET_MISSING`;
- `TARGET_NONPOSITIVE`;
- `CURRENT_AMOUNT_MISSING`;
- `CURRENT_AMOUNT_NEGATIVE`.

Unavailable Goal data does not invalidate results for other owned selected
Goals. This is distinct from a missing or foreign requested identifier, which
rejects the complete request with `404`.

## 6. Decimal, null, and output semantics

Financial values remain Python `Decimal` through readers, facts, assumptions,
and solvers, and serialize as plain decimal strings. The certified engines own
all compounding and `ROUND_HALF_EVEN` behavior. Source values are not rounded
again. Null remains absence, while explicit zero remains zero.

The output is a conditional preview under user-supplied assumptions. It is not
a promise, feasibility judgment, investment recommendation, priority ranking,
or realized-return calculation.

## 7. Persistence, security, and exclusions

The endpoint performs no insert, update, delete, flush, commit, Goal mutation,
scenario persistence, scheduler, cache, job, migration, schema change, AI call,
MyProfit read, portfolio read, or frontend change. Errors do not expose SQL,
authentication internals, other users' facts, or sensitive financial details.

R6.5+, R7, Portfolio Intelligence, Advisor, and deployment remain unauthorized.

## 8. Acceptance gates

Tests cover authentication; multiple owned Goals and two identities; missing
and foreign non-enumeration; invalid, duplicate, empty, and over-limit IDs;
stable request order; zero, null, negative, and invalid Goal values; positive
and zero required contribution; cent and large Decimal values; zero and invalid
rates; valid and invalid horizons; nominal/real basis validation; direct reuse
of the certified solver; one owned batch query; no writes, MyProfit, portfolio,
or parallel engine; OpenAPI; and preservation of R6.1–R6.3 plus all five prior
Planning POSTs.

## 9. Implementation evidence

R6.4 is implemented by an ordered ownership-filtered batch reader, one bounded
orchestration service over the existing `RequiredContributionSolver`, strict
request/response DTOs, and one authenticated POST. The implementation adds no
formula, engine, persistence, migration, frontend, portfolio/MyProfit read, or
Goal mutation.

Validation on 2026-10-27 passed `144` direct R6.4/domain/API/read and adjacent
Planning regression tests, then `680` tests in the broader focused Goals and
Planning selection. Existing Pydantic, `datetime.utcnow`, async-mock, and
pytest-cache warnings remain non-blocking; no new failure was observed. The
checkpoint is not staged, committed, pushed, or deployed. R6.5+ remains
unauthorized.
