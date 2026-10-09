# Current Repository State

**Status:** `VERIFIED CURRENT TRUTH`

**Updated:** 2026-10-09 — Phase 10.R3-B contract lock and ADR-029 acceptance

This document describes what exists now. Future product architecture belongs to
`MASTER_PLAN.md` and `ARCHITECTURE.md`; execution order belongs to
`IMPLEMENTATION_ROADMAP.md`.

## Current milestone

| Phase | Current status |
|---|---|
| 10.4 FIRE | `VALIDATED / CLOSED` |
| 10.5-A Portfolio Intelligence audit | `AUDIT COMPLETE / USER DECISIONS RESOLVED` |
| 10.5-B Portfolio Intelligence contract lock | `PAUSED / PENDING WEALTH OS REALIGNMENT` |
| 10.R0 realignment audit | `AUDIT COMPLETE` |
| 10.R1 architecture/docs | `ARCHITECTURE / DOCUMENTATION LOCKED` |
| 10.R2-A Smart Financial Context contract | `CONTRACT LOCKED / IMPLEMENTATION READY` |
| 10.R2 Smart Financial Context | `IMPLEMENTED / VALIDATED / CLOSED` |
| 10.R2-B1 persistence/ownership | `IMPLEMENTED / VALIDATED` |
| 10.R2-B2 declared Profile API | `IMPLEMENTED / VALIDATED` |
| 10.R2-B3 recurring income evidence engine | `IMPLEMENTED / VALIDATED` |
| 10.R2-B4 income decision state/API | `IMPLEMENTED / VALIDATED` |
| 10.R2-B5 feature-specific Smart Context composition | `IMPLEMENTED / VALIDATED` |
| 10.R2-B6 Profile context experience/browser transition | `IMPLEMENTED / VALIDATED / INDEPENDENTLY APPROVED` |
| 10.R2-B7 consumer integration foundations | `IMPLEMENTED / VALIDATED` |
| 10.R2-B8 stabilization and independent validation | `INDEPENDENTLY APPROVED` |
| 10.R2-MR1 migration reconciliation audit | `ROOT CAUSE DIAGNOSED` |
| 10.R2-MR2 runtime bootstrap/test isolation remediation | `IMPLEMENTED / INDEPENDENTLY APPROVED` |
| 10.R2-MR3 active-database Alembic reconciliation | `COMPLETED / VALIDATED` |
| 10.R3-A External Context audit | `AUDIT COMPLETE / APPROVED` |
| 10.R3-B External Context contract/registry | `CONTRACT APPROVED / LOCKED` |
| 10.R3-B.1 contract remediation | `REMEDIATED / INDEPENDENTLY APPROVED` |
| 10.R3-C domain/normalization/executable registry | `READY / NOT STARTED` |
| 10.R3-D/E/F/I BCB-only implementation path | `PLANNED / NOT STARTED` |
| 10.R3-G existing market boundary remediation | `SEPARATELY GATED / NOT STARTED` |
| 10.R3-H Focus expectations | `FOCUS DEFERRED / NOT IMPLEMENTED` |
| 10.R3 External Context | `CONTRACT LOCKED / IMPLEMENTATION NOT STARTED` |
| Wealth OS Realignment | `ARCHITECTURE LOCKED / R2 CLOSED; R3-C READY` |

R3-B now has an approved and locked contract, official five-series BCB/SGS
registry, implementation decomposition, and accepted ADR-029. R3-B.1 replaced
the unsafe assumption that SQLite
`NUMERIC(38,18)` guarantees exact persistence with canonical fixed-scale text
and explicit `Decimal` conversion; preserves `A -> B -> A` as three knowledge
events; and separates refresh age, economic freshness, and acquisition health.
Independent review reported 0 blocking, 0 material, and 0 minor findings; the
user explicitly approved all ten material decisions on 2026-10-09. R3-C is
ready but not started. No R3 production code, migration, provider, dependency,
API, frontend, database, or engine behavior exists from this checkpoint.

## Implemented and validated capabilities

| Capability | Current reality | Primary evidence |
|---|---|---|
| Pierre / cashflow | Operational import and governed transaction flows | `backend/domains/pierre/`, dashboard and transaction routers |
| Governance | Operational classification, import, reconciliation, and audit surfaces | governance routers and frontend routes |
| Investments / Wealth | Existing operational portfolio, position, allocation, dividend, evolution, and asset-detail surfaces | `backend/api/routers/investments.py`, `frontend/src/app/wealth/` |
| Goals | Authenticated CRUD and validated objective lifecycle | Goals router/use cases/UI |
| Financial Health | Certified cashflow, history, categories, anomaly, and trend services/API/UI | Health domain, router, and UI |
| Planning | Five authenticated transient capabilities using certified Decimal engines and explicit sources | ADRs 019–024, Planning domain/API/UI |
| FIRE | One authenticated deterministic analysis capability composed over Planning | ADR-025, FIRE contract/domain/API/UI |
| Smart Context B1-B7 foundation | Declared-context and recurring-decision persistence, exact Decimal constraints, fail-closed ownership, authenticated declared Profile context GET/PATCH, deterministic recurring-income evidence, authenticated review/confirm/reject/reset decision API, internal feature-specific composition, the Profile declared/observed review experience, and typed read-only future-consumer boundaries | migration `2d6b4f8a9c1e`, Smart Context backend tests, B6 frontend tests/typecheck/build |
| Market data | yfinance adapter/service with provider-specific cache behavior | market-data protocol and yfinance integration |

The existing Investments product surfaces are real, but their mixed valuation,
performance-like, score, and browser-calculation paths are not certified
Portfolio Intelligence authority. Phase 10.5-A remains the governing audit for
that distinction.

## Present UI and navigation

The current top-level product is still organized around Controle Financeiro,
Investimentos, Wealth Intelligence, Governança, and Configurações. The Wealth
Intelligence hub links separately to Goals, Health, Planning, and FIRE and is a
module directory rather than a context-rich Home.

R1 locks a target information architecture but changes no route. Existing deep
links remain operational until R5/R6 explicitly implement migration.

## Profile

`GET` and `PATCH /api/v1/profile/context` expose the approved declared monthly
gross income for the authenticated exact-single-user owner. The `/profile`
experience now reads, explicitly saves, and explicitly clears that fact using
exact Decimal strings and displays its declared/monthly/gross/BRL provenance.
The same page separately presents bounded recurring-income evidence and the
authenticated confirm/reject/reset actions without treating detection or a
confirmed recurring source as salary. Only these presentation/professional
fields persist in the browser key
`fin_profile_extended`:

- `display_name`;
- `occupation`;
- `company`;
- `tax_regime`.

No persisted legacy declared-income value exists in that browser record, so B6
does not invent a migration prompt or issue an automatic upload. Initial load
performs GET requests only. Old unapproved fields are removed from the local
record while the four approved local-only fields remain local; no local object
is sent through the declared-context API. Goals, Health, Planning, and FIRE do
not consume these local Profile fields today.

After the first independent review, B6 now also prevents overlapping candidate
mutations and candidate retries, preserves confirmed-versus-rejected decision
meaning when evidence is stale, keeps action feedback visible after an empty
canonical refresh, reports refresh failure without false success, and treats
offset-less repository timestamps as UTC without changing civil-date handling.
Rendered Profile tests cover these behaviors. The independent delta re-review
approved M1–M5 with no blocking or material findings.

## Settings

`/settings` is the existing canonical configuration surface. Security,
Notifications, Appearance, and Data/System sections exist, but current behavior
is limited:

- password change is a client-only success simulation;
- 2FA, notifications, weekly reports, anomaly alerts, theme, and locale are
  marked `Em breve` or remain component-local;
- export/clear operate only on the browser profile record;
- there is no settings backend, provider configuration workflow, or secret
  storage UI.

## AI current state

There is **no production AI runtime**.

- no Advisor service;
- no Insights generator/runtime;
- no Copilot;
- no OpenAI client/runtime;
- no Ollama integration/runtime;
- no AI scheduler;
- no provider abstraction or tool registry;
- the three `backend/integrations/gemini/*.py` files are empty;
- AI-related database tables and environment settings are scaffolding only;
- `google-generativeai` being installed does not constitute a runtime.

Any UI copy suggesting that local Ollama or a Wealth Advisor is already active
is placeholder/future-facing copy, not implemented capability.

## External context current state

| Source | Current state | Boundary |
|---|---|---|
| Pierre Finance | Active import/API | Governed after ingestion under existing rules |
| MyProfit CSV | Active import for positions, portfolio history, and income events | Provider facts with grain/provenance limitations |
| yfinance | Active quote/history/fundamental adapter with memory cache | Provider-specific reference; not a shared external-context layer |
| BCB/SGS | Research/proposal only | No active normalized adapter or read model |
| News | Absent | No provider, provenance, or relevance contract |

There is no normalized External Context Layer today.

## Theme and design current state

Light and dark semantic CSS variables exist, but the root layout and AppShell
apply dark-specific classes and at least 71 TSX files still contain dark-only
utility patterns. Settings does not persist a theme. System/Light/Dark is a
future R5 target, not current behavior.

## Smart Context current state

The internal `SmartFinancialContextService` now composes purpose-limited context
for `PROFILE`, `HOME`, `PLANNING`, `GOAL`, and `FIRE`. It resolves the
authenticated exact-single-user guard before reading approved sources, applies
an explicit allowlist per feature, and returns immutable provenance-aware Smart
Values. It has no public route, write path, internal HTTP, provider/AI call, or
financial formula. B1 provides two empty-by-migration, user-owned persistence
owners:

- `user_declared_financial_context`, with nullable positive cent-scale
  `NUMERIC(18,2)` declared monthly gross income and explicit BRL/monthly/gross
  semantics;
- `recurring_income_decisions`, with versioned opaque signature identity and
  only `CONFIRMED_AS_INCOME` or `REJECTED` persisted decisions.

The B1 repositories and B2 Profile API are scoped by a reusable fail-closed guard that requires
the authenticated user to equal the exact single application user. They leave
transaction commit/rollback to the caller. Candidate evidence, raw transaction
descriptions, amounts, and account numbers are not stored.

B3 now reads only bounded eligible `CLASSIFIED`/`ENTRADA`/`CREDIT` rows after
the B1 ownership guard and computes versioned candidates on read. Description
normalization is limited to NFKC, case-folding, trim, and whitespace collapse;
candidate evidence requires three distinct calendar months in the six-month
window and uses exact Decimal median/MAD without amount-similarity or confidence
scores. Explicit same-titularity and investment evidence is ineligible; generic
structured transfer categories remain eligible with an ambiguity flag.

Candidates remain computed on read and are never persisted or copied into
Profile. B4 now exposes authenticated review plus explicit confirm/reject/reset
actions. Every confirm/reject recomputes the current candidate and validates an
opaque evidence fingerprint; changed evidence returns `409`. Durable decisions
overlay only the exact signature version, while incompatible or disappeared
evidence is reported as `STALE` without changing the stored decision. The API
returns exact Decimal strings and bounded evidence without raw descriptions,
transaction IDs, account scope, signatures, or internal user identity.

Only `recurring_income_decisions` is written by B4. B5 is read-only and delegates
to Profile, B3/B4 recurring evidence, certified Health facts, the Decimal-safe
owned Goal reader, and `PlanningPortfolioSourceResolver`. Planning and FIRE
receive certified investment wealth plus explicit assumption-required states;
income, savings, expenses, returns, inflation, contribution, retirement
spending, and withdrawal rate are not silently substituted. Transactions,
governance, Health, declared Profile context, candidate evidence, and financial
engines are unchanged. B6 adds only the Profile presentation and explicit
human actions over the existing B2/B4 APIs; it does not automatically mutate
declared or observed income, and it adds no generic Smart Context route.
B7 adds typed, read-only internal boundaries for future Home, Planning, Goal,
and FIRE consumers. Each boundary delegates once to B5 with an explicit feature,
authenticated owner, and `as_of_date`; it does not query source domains, create
effective engine inputs, resolve assumptions, change public APIs, or implement
R6 smart-prefill behavior.

MR1 diagnosed the migration drift: runtime `create_all` had created the physical
Smart Context tables without advancing Alembic bookkeeping. MR2 removes that
recurring cause: application import/startup is DDL-inert, both database engines
honor the canonical configured URL, Alembic is the schema authority, and pytest
defaults to a disposable database while refusing the active SQLite file. MR2
was independently approved with no blocking or material findings. MR3 then
reconciled the already-equivalent active schema to revision `2d6b4f8a9c1e` by
bookkeeping stamp and verified `upgrade head` as a no-op. The schema and
financial data were preserved, SQLite integrity remained `ok`, and pre/post
backups were retained.

ADR-028 and `SMART_FINANCIAL_CONTEXT_CONTRACT.md` now lock the future R2
semantics: Profile-owned declared monthly gross income; deterministic
three-distinct-months-in-six recurring candidates without an amount-similarity
score; explicit confirm/reject/reset decisions; and feature-specific context
composition. `SMART_FINANCIAL_CONTEXT_IMPLEMENTATION_PLAN.md` decomposes the
work. B1 implements persistence/ownership, B2 the declared Profile context API,
B3 deterministic recurring evidence, B4 decision state/API, B5 internal
feature-specific composition, and B6 the Profile context experience with a
safe no-upload browser transition. B6 is independently approved; B7 implements
and validates the consumer-integration foundations; B8 independently approved
the complete R2 foundation. R2 is closed. External Context is
`10.R3-B = CONTRACT APPROVED / LOCKED`, with implementation beginning only when
the separately scoped `10.R3-C = READY / NOT STARTED` task is authorized;
product recomposition and smart-prefill behavior remain reserved for R6.

## Portfolio Intelligence state

10.5-A established:

- guarded monthly `portfolio_snapshots.patrimonio` is aggregate investment
  wealth, not net worth or live position valuation;
- MyProfit `total_atual` is the selected future position-valuation direction;
- aggregate wealth and position-valued totals remain distinct until reconciled;
- performance and benchmark presentation are outside the MVP;
- monthly snapshots support wealth evolution, not performance.

No Portfolio Intelligence service, endpoint, engine, or page has been created.
10.5-B remains paused until R7 closes the realignment.

## Known debt and limitations

- JWT access token and user JSON persist in `localStorage`.
- CORS remains broad for local development.
- ADR-014 records the historical `accounts` primary-key/model mismatch.
- Two Investments asset-detail unit tests have historical MagicMock/timeline
  sorting failures.
- Repository-wide mobile, lint, and Recharts SSR warning debt remains.
- There is no certified sustainable contribution-capacity engine, portfolio
  performance engine, rebalancing engine, watchlist, BCB/news integration,
  Docker deployment, or AI runtime.

Historical phase-by-phase execution evidence remains in `CHANGELOG.md`,
`TESTING_STRATEGY.md`, accepted ADRs, and locked contracts. It is intentionally
not duplicated in this current-state summary.
