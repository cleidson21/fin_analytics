# Planning Goal Context Read Model — approved microcontract

**Status:** `APPROVED / IMPLEMENTED / AUTOMATED GATES PASSED / USER MANUAL ACCEPTANCE REPORTED / COMMITTED / PUSHED`

**Phase:** `TSK-R6.1 GOALS → PLANNING / R6 GENERAL GATE SATISFIED AFTER R5 CLOSURE`

**Purpose:** define the minimum authenticated read boundary and deterministic UI
rules needed to reuse an owned Goal as the starting context for Planning.

This approved microcontract is subordinate to ADR-023, ADR-024, ADR-025,
`PLANNING_UX_CONTRACT.md`, and the existing Goals and Planning contracts. It
does not modify a locked decision. Implementation was authorized only through
the bounded ADR-027 sequencing exception and does not authorize R6.2+.

## 1. Scope and existing authority

The implemented read model reuses, without changing:

- `PlanningGoalReadQuery.get_goal(db, goal_id, current_user.id)`;
- `GoalPlanningFact`, including Decimal money and nullable stored facts;
- the existing `CurrentPlanningUser` and `PlanningReadSession` dependencies;
- the existing non-enumerating owned-Goal behavior;
- the existing Goal Planning POST and its deterministic engine/service;
- ADR-023's three mutually exclusive initial-wealth sources.

The legacy public Goals DTO remains unchanged. It uses browser numbers and is
therefore not the authority for Planning presets. `wealth-home-v2` remains an
aggregate Home contract and is not a shortcut to an individual Goal fact.

## 2. Read-only endpoint

```text
GET /api/v1/planning/goals/{goal_id}/context
```

Response DTO name: `PlanningGoalContextResponseDTO`.

Request:

- authenticated bearer session through the existing dependency;
- `goal_id` as the only path parameter, typed as UUID;
- no query parameters and no request body.

`200` response:

```json
{
  "goal_id": "00000000-0000-0000-0000-000000000000",
  "name": "Reserva de emergência",
  "goal_type": "EMERGENCY_RESERVE",
  "status": "ACTIVE",
  "target_amount": "50000.00",
  "current_amount": "12500.00",
  "planned_monthly_contribution": "750.00",
  "target_date": "2028-12-31"
}
```

Contract:

- `target_amount` is a required plain decimal string;
- `current_amount` and `planned_monthly_contribution` are plain decimal strings
  or `null`;
- `target_date` is an ISO `YYYY-MM-DD` civil date or `null`;
- `goal_type` and `status` preserve the existing internal enum values;
- `planned_monthly_contribution` maps the existing
  `GoalPlanningFact.goal_planned_monthly_contribution` field; it stores no new
  value;
- `user_id`, description, priority, linked account, assumptions JSON,
  timestamps, and progress are intentionally excluded.

No response field is calculated. Mapping copies the owned `GoalPlanningFact`
and serializes its Decimal fields through the existing Planning serializer.

## 3. Authentication, ownership, and errors

- The route must query by both `goal_id` and authenticated `current_user.id`.
- Missing and wrong-owner Goals both return the existing Planning response:
  `404 {"detail":"Goal not found."}`.
- A returned fact whose `user_id` differs from the authenticated user fails
  closed with the same non-enumerating `404`.
- Missing/invalid authentication uses the existing `401` behavior.
- A syntactically invalid UUID uses FastAPI's existing path-validation `422`.
- Unexpected read or mapping failure returns a generic Planning `500` without
  persistence detail or financial payload leakage.
- ACTIVE, PAUSED, ACHIEVED, and CANCELLED owned Goals may be read. Applicability
  remains exclusively owned by the existing Goal Planning service at POST time.
- The GET performs no commit, flush, write, engine call, source resolution, or
  simulation.

## 4. Null, zero, and source semantics

- `null` means the Goal does not contain that fact.
- A decimal string representing zero, including `"0.00"`, means an explicitly
  stored zero and must remain distinguishable from `null`.
- Goal current amount is never copied into a manual-wealth amount. When chosen,
  the request continues to send only the path-Goal
  `{ "source": "GOAL_CURRENT_AMOUNT" }` selector and the backend resolves the
  amount again at submit time.
- Goal current amount, ADR-023 investment portfolio wealth, and user-provided
  wealth remain three separate alternatives. They are never summed or used as
  silent fallbacks.
- Goal target is context for the existing Goal Planning service, not a new
  client-authored Planning target.

## 5. Deterministic preset rules

After the first successful context read for a selected Goal, while the form is
pristine:

1. select that Goal identity for the Goal Planning path;
2. display name, localized type/status, target, current amount, planned monthly
   contribution, and target date;
3. if `current_amount` is non-null, select the visible
   `GOAL_CURRENT_AMOUNT` source without copying its amount into a manual field;
4. if `current_amount` is null, do not create zero or select another financial
   source as a fallback; keep the manual amount empty and explain that Goal
   current value is unavailable;
5. if `planned_monthly_contribution` is non-null, copy its exact value through
   the existing string-safe input adapter into the editable scenario monthly
   contribution;
6. if it is null, leave the scenario contribution empty; an explicit zero is
   applied as zero;
7. mark applied fields as populated from the selected Goal;
8. leave expected return, target basis, data-base, inflation, and horizon
   untouched and explicit;
9. do not execute the Goal Planning POST.

`target_date` is displayed only. It is not converted to `horizon_months`, copied
to the simulation target date, or compared with the client clock. A future
date-to-horizon rule requires a separate approved deterministic contract.

Edits affect only the transient form. They never PATCH/PUT the Goal and never
persist a Planning scenario.

## 6. Safe Goal switching

The UI tracks the applied Goal context and whether any simulation field has
been edited since it was applied.

- With no manual edit, selecting another Goal loads its context and atomically
  reapplies the rules in section 5.
- With a manual edit, selecting another Goal creates a pending selection. It
  does not change the active Goal path or any form field.
- The user must choose `Aplicar dados desta meta` to replace the active Goal and
  preset-owned fields, or cancel to retain the current Goal and edits.
- Submission is disabled while a different Goal is pending.
- No Goal switch may silently change the path Goal, current-amount source, or
  edited scenario contribution.

## 7. Frontend entry and state lifecycle

The approved deep-link shape is:

```text
/wealth-intelligence/planning?intent=objective&task=goals&goal=<UUID>
```

- `GoalCard` may expose `Simular esta meta` using only the Goal UUID in the URL.
- Planning accepts `goal` only with `intent=objective&task=goals`; otherwise it
  removes the stale parameter during route normalization.
- Planning resolves the UUID through the authenticated GET before
  applying presets. Invalid, missing, or inaccessible context produces a
  generic `Meta indisponível` state and no POST.
- The existing Goals list may continue to provide selector identity/labels,
  but its numeric money fields are not used for Planning presets.
- Context and edits remain in React memory only. Logout, `401`, or authenticated
  user-ID change clears selected/pending Goal context, presets, and transient
  results. Nothing financial is stored in the URL or `localStorage`.
- Enum values remain unchanged; explicit pt-BR presentation mappings render
  Goal type and lifecycle status.

## 8. Related presentation-only targets

These targets require no change to `wealth-home-v2` and no new engine:

- Goals: add `Simular esta meta` with the governed deep link above.
- Wealth Home: relabel the empty Planning entry as `Planejar uma meta` with
  `Abrir Planejamento`; relabel FIRE as `Simular independência` with
  `Iniciar análise`.
- Wealth Home actions only navigate. They never issue a calculation POST.
- Planning may link back to Metas and to the existing FIRE route. Routes and
  engines remain separate, and ADR-024 keeps exactly three Planning intentions.
- Existing transient-result selection and refresh clearing remain unchanged.

## 9. Focused validation

Backend:

- authenticated owned Goal returns the exact eight-field response;
- missing and wrong-owner Goals return identical `404` responses;
- Decimal strings preserve scale and never become JSON numbers;
- nullable fields remain null and explicit zero remains a decimal string;
- all lifecycle statuses are readable without duplicating applicability rules;
- invalid UUID/auth behavior follows existing dependencies;
- the request performs no write, flush, commit, engine call, or portfolio read;
- OpenAPI exposes one secured GET and leaves the five Planning POSTs unchanged.

Frontend:

- GoalCard produces the exact deep link with no financial value;
- route parsing selects Objective / Meta cadastrada and validates the Goal UUID;
- first pristine selection applies only the approved presets;
- null and zero remain distinct;
- local edits do not mutate the persisted Goal;
- edited-form Goal switching requires `Aplicar dados desta meta`;
- no calculation POST occurs on navigation, selection, context load, or preset;
- logout, `401`, and identity change clear Goal-derived transient state;
- pt-BR labels, loading, unavailable, empty, keyboard, focus, and responsive
  states are covered;
- Wealth Home action changes remain navigation-only and preserve transient
  analysis behavior.

## 10. Implemented paths

Backend:

- `backend/application/dtos/planning_dto.py`;
- `backend/api/planning_mapping.py`;
- `backend/api/routers/planning.py`;
- one focused Planning Goal-context API test file, plus existing OpenAPI
  assertions where needed.

No change is expected in `PlanningGoalReadQuery`, `GoalPlanningFact`, the Goal
ORM model, Goals public DTOs, engines, migrations, or `wealth-home-v2`.

Frontend:

- `frontend/src/lib/planning.ts`;
- Planning navigation parser/tests;
- Planning page and Goal Planning capability/pure form-state tests;
- Goal card and tests;
- Wealth Home entry-point copy/navigation and tests;
- existing pt-BR Goal enum-label mapping, extracted only if reuse requires it.

The subsequent presentation-only refinement keeps the global Wealth
Intelligence navigation as the single inter-page navigation, removes duplicate
page headings and subtitles while retaining semantic headings, presents the
three Objective tasks as a centered segmented control, and summarizes advanced
premises in compact chips. It changes none of the endpoint, preset, switching,
identity, source, Decimal, engine, persistence, or route rules above.

## 11. Approval and implementation gate

The project owner approved the endpoint path/schema, response field alias,
non-enumerating error contract, first-selection preset behavior, pending Goal
switch state, and the deliberate absence of target-date-to-horizon conversion
for TSK-R6.1 under the ADR-027 sequencing exception.

Implementation is complete with focused backend (`240 passed`), focused
frontend (`54 passed`), full frontend (`238 passed`), TypeScript, focused
ESLint, production build, and whitespace gates passing. The later minimalist
refinement passed focused frontend (`27 passed`), full frontend (`238 passed`),
TypeScript, focused ESLint, production build, and whitespace validation. The
user tested the resulting experience and reported it satisfactory for the
current scope, recorded as `R6.1 UX REFINEMENT = USER-ACCEPTED FOR CURRENT
SCOPE`. This does not assert a complete manual test matrix or independently
classify all of R6 as `VALIDATED / CLOSED`. The controlled two-commit checkpoint
was published at `1b0a1c6fa538ad69c415c29f77c8f91b68f4dd0b`. The project owner
subsequently accepted and closed the current R5 visual baseline, satisfying the
general R6 sequencing gate. No later R6 increment, engine, migration, or
persistence work is defined or authorized by this microcontract.
