# STATUS: IMPLEMENTATION DECOMPOSITION LOCKED / R2-B1 READY

# AUTHORITY: ADR-028 + SMART_FINANCIAL_CONTEXT_CONTRACT.md

# Phase 10.R2-B — Smart Financial Context Implementation Decomposition

**Date:** 2026-10-03

## 1. Readiness decision

Phase 10.R2 is `CONTRACT LOCKED / IMPLEMENTATION READY`. Implementation has not
started. This plan decomposes the locked contract into independently reviewable
and testable tasks without authorizing automatic execution.

## 2. Existing conventions to reuse

- FastAPI routers are mounted under `/api/v1` in `backend/main.py`.
- Authentication uses `get_current_user`; public requests never supply
  `user_id`.
- User-owned Goals use UUID ownership and non-enumerating reads.
- Planning keeps sync certified readers separate from async authentication and
  uses exact `Decimal` DTO boundaries.
- `PlanningPortfolioSourceResolver` is the model for a guarded local
  single-tenant source.
- `HealthFinancialQuery` owns governed cashflow reads; Smart Context must not
  duplicate its aggregate SQL or calculations.
- Frontend auth/profile currently uses `AuthContext`, `/profile`, and the
  `fin_profile_extended` legacy browser record.
- Alembic is the active schema mechanism; no direct database mutation belongs
  in an implementation task.

## 3. Target dependency direction

```text
authenticated request
  -> explicit Profile or income-decision use case
  -> user-owned repositories

authenticated feature-context request
  -> SmartFinancialContextService
  -> approved readers/services
     Profile declaration reader
     recurring evidence reader + decision reader
     Health adapter
     Goal reader
     Planning portfolio resolver
  -> immutable purpose-specific DTO
```

The context service never depends on frontend state, HTTP calls, external
providers, LLMs, or financial-engine internals.

## 4. Planned persistence

One future Alembic migration creates two normalized tables:

### Declared financial context

Conceptual columns:

- `user_id` UUID primary/unique foreign key to `users.id`;
- `declared_monthly_gross_income` `NUMERIC(18,2)` nullable;
- `currency` fixed/validated `BRL` when amount exists;
- `income_period` fixed/validated `MONTHLY` when amount exists;
- `income_basis` fixed/validated `GROSS` when amount exists;
- `income_as_of_date` date nullable with amount;
- `declared_at`, `updated_at` timestamps.

No CPF, phone, birthdate, employer, occupation, regime, or employment-start
column is approved.

### Recurring-income decisions

Conceptual columns:

- server UUID decision ID;
- `user_id` UUID foreign key/index;
- opaque `source_signature` plus `signature_version`;
- internally resolved provider/account scope identifiers;
- `decision` enum/string: `CONFIRMED_AS_INCOME | REJECTED`;
- optional user-safe label, bounded and non-sensitive;
- `decided_at`, `updated_at`;
- unique `(user_id, source_signature, signature_version)`.

Raw transaction descriptions, transaction ID arrays, calculated evidence,
amounts, and counterparty PII are not persisted in this table.

## 5. Migration and rollback strategy

- Migration: required in R2-B1; none is created by planning.
- Backfill: create no declaration and no decision rows.
- Existing `users`, transactions, Goals, and portfolio tables are unchanged.
- Browser data is not imported by migration.
- Rollback removes only empty/new R2 tables when safe; production rollback
  policy must preserve user decisions once real data exists, using a forward
  disable/compatibility migration rather than destructive automatic downgrade.
- Deployment gate: schema upgrade, application compatibility, and rollback
  rehearsal must pass on a copied database before user data is accepted.

## 6. API and read-model plan

The implementation surface is limited to the endpoints locked in the contract:

- authenticated Profile context `GET` and `PATCH`;
- authenticated income-candidate list;
- explicit confirm, reject, and decision-clear actions.

Feature-specific Smart Context begins as an internal application service. Do
not publish a global context dump. A future public read must define one consumer
and one bounded response.

All public money is serialized as a plain Decimal string. Server-created
candidate IDs are opaque; decision endpoints recompute current evidence before
writing and return `409` if the candidate version changed.

## 7. Recurring evidence engine plan

The pure detector receives already-read, eligible observation DTOs and an
`as_of_date`. It owns:

- conservative description normalization and versioning;
- source/account/currency/direction signature construction;
- six-month evidence-window selection;
- three-distinct-month candidate threshold;
- bounded evidence summaries, including exact Decimal median and MAD;
- transfer/investment/conflict risk flags;
- insufficient-history and partial-current-month semantics.

It performs no database access, user write, AI classification, fuzzy matching,
Health aggregate, or salary labeling.

The transaction read adapter owns the active Pierre schema and applies the
governed eligibility query. Because the table lacks `user_id`, the application
resolver must enforce the single-user/current-user invariant before the adapter
may expose rows.

## 8. Context composition plan

`SmartFinancialContextService` composes named capabilities, not arbitrary keys.
Initial internal contexts are:

- Profile: declared income plus confirmed/candidate summaries;
- Home foundation: eligible wealth, Health period facts, Goal summary
  capability references; no Home DTO/UI yet;
- Planning foundation: eligible initial-wealth capability and labeled
  contribution references; no automatic assumption mutation;
- Goal foundation: owned stored Goal facts plus Health reference capability;
- FIRE foundation: eligible wealth only; spending and withdrawal rate remain
  required assumptions.

DTOs are immutable and provenance-aware. Context adapters delegate to canonical
readers; they never reproduce Goal, Health, portfolio, Planning, or FIRE math.

## 9. Frontend boundary

R2 frontend implementation is limited to:

- Profile server persistence for the approved declared income field;
- explicit display of declared versus observed context;
- candidate evidence review and confirm/reject/reverse interactions;
- source/period/provenance wording;
- explicit migration prompt for eligible legacy browser values;
- removal of misleading save-success behavior for fields that are not saved,
  within the approved Profile scope.

It must not redesign Goals, Planning, FIRE, navigation, Home, Settings, or the
theme. R5/R6 own those experiences.

## 10. Operational and privacy plan

- Use request-scoped sessions and existing auth dependencies.
- Fail closed when the single-tenant ledger invariant is not satisfied.
- Do not expose or log raw descriptions, account IDs, transaction IDs, Profile
  payloads, salary amounts, CPF, phone, birthdate, or tokens.
- Measure candidate query duration, row counts, candidate counts, decision
  result, error class, and normalizer version without sensitive values.
- Compute candidates on read initially; add no cache or scheduler.
- Bound the evidence window in SQL before materializing rows.

## 11. Validation gates common to every task

1. Repository/contract conformity and explicit scope review.
2. Focused unit/integration/API tests for the task.
3. Static financial/privacy/ownership audit.
4. Relevant Goals, Health, Planning, FIRE, and Investments regressions.
5. Documentation/current-state reconciliation.
6. No next task begins without the current task's validation gate and explicit
   authorization.

## 12. R2-B1 — Declared Context Persistence & Ownership Foundation

**Scope**

- Add the two approved tables through one reviewed Alembic migration.
- Add domain types, ORM models, repositories, and exact Decimal validation.
- Add the single-tenant transaction-scope guard as a reusable application
  boundary; do not read candidate transactions yet.
- Preserve `users` as identity only.

**Expected concepts/files**

- new R2 domain package for context enums/value objects;
- new persistence models/repositories;
- one Alembic revision;
- dependency/container wiring only where required;
- focused migration/repository/ownership tests.

**Tests**

- upgrade on representative copied schema and empty backfill;
- one declaration row per user;
- Decimal/currency/basis/as-of invariants;
- decision uniqueness and reversible updates;
- wrong-user and zero/one/many-user guards;
- no sensitive columns/raw descriptions.

**Gate**

Schema, ownership, and rollback review approved; no API/frontend behavior yet.

**Model recommendation:** GPT-5.6 Sol High because schema, privacy, ownership,
and Decimal contracts are coupled.

## 13. R2-B2 — Declared Profile Context API

**Scope**

- Implement authenticated Profile context `GET` and `PATCH`.
- Persist only declared monthly gross income and its semantic metadata.
- Return authenticated identity fields read-only without duplicating them.
- Support explicit clear/null and non-enumerating ownership.

**Expected concepts/files**

- Profile context request/response DTOs;
- application read/update use cases;
- profile router and `backend/main.py` registration;
- API/repository tests.

**Tests**

- auth/401, current-user ownership, malformed/negative/float input rejection;
- plain Decimal string, BRL/monthly/gross invariants, ISO dates;
- nullable clear, repeated deterministic reads, no unrelated fields;
- no CPF/phone/birthdate/employer exposure.

**Gate**

OpenAPI and real-JSON contract independently verify purpose limitation.

**Model recommendation:** GPT-5.6 Sol High for backend contract implementation.

## 14. R2-B3 — Recurring Income Evidence Engine

**Scope**

- Implement the pure detector and active-ledger read adapter.
- Enforce governed eligibility, signature normalization, 3-of-6 cadence, amount
  evidence, and risk flags.
- Produce candidates only; no decision writes or frontend.

**Expected concepts/files**

- immutable observation/evidence/candidate DTOs;
- pure recurring-evidence service;
- Pierre-ledger read adapter behind the ownership guard;
- unit tests plus read-only integration tests.

**Tests**

- stable monthly credit; end/start-month shift; variable amount; missing month;
- multiple occurrences/month; two sources; refund; investment income;
- explicit same-titularity transfer; generic transfer ambiguity; one-off large
  credit; insufficient/no history; partial current month; multiple currencies;
- exact Decimal median/MAD; no numeric score; opaque signature stability;
- no raw description in DTO/log/public ID.

**Gate**

Independent vectors reproduce candidate membership and evidence from fixed
inputs; live read-only smoke reports counts only.

**Model recommendation:** GPT-5.6 Sol High for deterministic temporal and data
semantics.

## 15. R2-B4 — Income Decision State & API

**Scope**

- Compose computed candidates with durable confirm/reject decisions.
- Implement candidate list and explicit confirm/reject/clear actions.
- Recompute and validate opaque candidate identity on every write.
- Preserve Profile and transaction rows unchanged.

**Expected concepts/files**

- decision use cases and response DTOs;
- financial-context router;
- repository integration and error mapping;
- confirmation API tests.

**Tests**

- candidate is not confirmed before action;
- confirm/reject/reverse durability and idempotency;
- wrong-user/forged candidate non-enumerating `404`;
- changed evidence/version `409`;
- stale confirmed source; rejected suppression; resurfacing after reversal;
- no Profile/governance/category/Health mutation.

**Gate**

Transaction-table before/after audit proves decision-only writes.

**Model recommendation:** GPT-5.6 Sol High for trust/write-boundary work.

## 16. R2-B5 — Feature-Specific Smart Context Composition

**Scope**

- Implement the immutable Smart Value model and feature-specific application
  service.
- Add adapters to Profile declarations, confirmed income evidence, Health,
  owned Goals, and the existing portfolio resolver.
- Keep the service internal; no generic public dump.

**Expected concepts/files**

- context capability enums and immutable DTOs;
- `SmartFinancialContextService` or repository-convention equivalent;
- thin canonical-source adapters;
- composition tests.

**Tests**

- feature eligibility/no global precedence;
- provenance and unavailable reasons;
- Health services and portfolio resolver invoked rather than duplicated;
- Goal wrong-owner/non-enumeration;
- FIRE excludes spending/withdrawal defaults;
- Planning excludes return/inflation defaults;
- override result preserves offered and effective values.

**Gate**

Static audit finds no SQL outside readers, no financial formula, no provider or
LLM call, and no write path.

**Model recommendation:** GPT-5.6 Sol High for cross-domain composition.

## 17. R2-B6 — Profile Context Experience & Browser Transition

**Scope**

- Connect `/profile` to the declared Profile API.
- Separate declared information from observed financial context.
- Add candidate evidence review and confirm/reject/reverse UI.
- Implement explicit opt-in migration of the one approved legacy income value
  only if present in old browser state; never upload other fields.
- Clarify which legacy fields are display-only/deferred/not stored.

**Expected concepts/files**

- Profile page and focused client/types/hooks;
- reusable smart-value/provenance primitives only if needed here;
- frontend tests using the existing runner and contract-safe formatters.

**Tests**

- no automatic upload; reviewed save action; server-confirmed success only;
- declared versus observed wording; candidate evidence and states;
- exact string-safe money; accessible controls; narrow layout;
- legacy key cleanup only after successful save;
- no sensitive value in localStorage, URL, console, or error output.

**Gate**

Manual privacy/UX smoke plus Vitest, TypeScript, focused lint, and build.

**Model recommendation:** Sonnet 4.6 for frontend implementation, followed by
GPT-5.6 Sol High contract review.

## 18. R2-B7 — Consumer Integration Foundations

**Scope**

- Prove internal context DTOs can serve future Home/Planning/Goal/FIRE
  consumers without changing current engines or pages.
- Add only adapters/tests needed for R6 readiness.
- Do not enable smart prefill in Goals, Planning, or FIRE UI.

**Expected concepts/files**

- focused application adapters and contract tests;
- no required frontend consumer changes.

**Tests**

- Planning initial-wealth capability delegates to the current resolver;
- Goal facts retain owned Decimal readers;
- Health realized savings is never labeled capacity;
- FIRE spending/withdrawal remain absent/assumption-required;
- Home foundation omits unsupported net worth/capacity/performance.

**Gate**

Existing five Planning endpoints and FIRE endpoint remain byte-contract
compatible; no new consumer behavior is claimed.

**Model recommendation:** GPT-5.6 Sol High.

## 19. R2-B8 — Stabilization & Independent Validation

**Scope**

- Fresh-context review of architecture, schema, ownership, privacy, API,
  frontend, and canonical documentation.
- Run focused and proportional regression suites.
- Reconcile actual current state and close R2 only if evidence supports it.

**Tests and audits**

- complete R2 suites, OpenAPI, database migration rehearsal, read/write audit;
- Goals, Health, Planning, FIRE, and relevant Investments regressions;
- frontend Vitest, TypeScript, focused lint, production build;
- no secrets/local paths/sensitive logs; no R3/R4/R5/R6 scope leakage;
- known historical failures classified separately.

**Gate**

Independent report must establish `IMPLEMENTED / VALIDATED` before R3 becomes
eligible. Status documents cannot close R2 on their own.

**Model recommendation:** GPT-5.6 Sol High; independent product/UX critique may
use Opus 4.6 in a separate review context if explicitly authorized.

## 20. Dependency order

```text
R2-B1 persistence/ownership
  -> R2-B2 declared Profile API
  -> R2-B3 recurring evidence
  -> R2-B4 confirmation state/API
  -> R2-B5 context composition
  -> R2-B6 Profile experience
  -> R2-B7 consumer foundations
  -> R2-B8 independent validation
```

B2 and pure B3 test design may be prepared in parallel after B1 contracts are
stable, but the authorized implementation queue remains one validated task at a
time.

## 21. Explicitly deferred

- per-user Pierre account/transaction ownership migration beyond the guarded
  local single-tenant bridge;
- fuzzy/AI salary classification;
- sustainable contribution capacity;
- automatic FIRE spending/withdrawal defaults;
- Planning return/inflation defaults;
- external macro/market/news providers;
- AI runtime/tool registry;
- Settings controls without real configuration;
- Home/Goals/Planning/FIRE redesign;
- theme/navigation work;
- Portfolio Intelligence.

## 22. First authorized implementation task after approval

`PHASE 10.R2-B1 — DECLARED CONTEXT PERSISTENCE & OWNERSHIP FOUNDATION`

It may start only through a new explicit implementation task. This planning
session stops with documentation and an empty Git index.
