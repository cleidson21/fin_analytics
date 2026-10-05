# Current Repository State

**Status:** `VERIFIED CURRENT TRUTH`

**Updated:** 2026-10-05 — Phase 10.R2-B4 income-decision API validation

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
| 10.R2 Smart Financial Context | `IMPLEMENTATION IN PROGRESS` |
| 10.R2-B1 persistence/ownership | `IMPLEMENTED / VALIDATED` |
| 10.R2-B2 declared Profile API | `IMPLEMENTED / VALIDATED` |
| 10.R2-B3 recurring income evidence engine | `IMPLEMENTED / VALIDATED` |
| 10.R2-B4 income decision state/API | `IMPLEMENTED / VALIDATED` |
| 10.R2-B5 feature-specific Smart Context composition | `READY / NOT STARTED` |
| Wealth OS Realignment | `ARCHITECTURE LOCKED / IMPLEMENTATION IN PROGRESS` |

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
| Smart Context B1-B4 foundation | Declared-context and recurring-decision persistence, exact Decimal constraints, fail-closed ownership, authenticated declared Profile context GET/PATCH, deterministic recurring-income evidence, and authenticated review/confirm/reject/reset decision API | migration `2d6b4f8a9c1e`, Smart Context persistence/API/evidence/decision tests |
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

`GET` and `PATCH /api/v1/profile/context` now expose the approved declared
monthly gross income for the authenticated exact-single-user owner. The API
accepts only strict Decimal strings or explicit null, returns exact strings and
minimal declared provenance, and exposes authenticated name/e-mail without an
internal user identifier. The `/profile` frontend is not connected to this API
yet. Only these extended fields persist in the browser key
`fin_profile_extended`:

- `display_name`;
- `occupation`;
- `company`;
- `tax_regime`.

Phone, birthdate, CPF, gross monthly income, and employment start appear in the
form, but the current frontend still treats gross income as transient and
removes sensitive values from old browser records. B1/B2 added no browser
upload or backfill. Goals, Health, Planning, and FIRE do not consume extended
Profile data today.

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

There is no shared Smart Context composition service yet. B1 now provides two
empty-by-migration, user-owned persistence owners:

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

Only `recurring_income_decisions` is written by B4. Transactions, governance,
Health, declared Profile context, candidate evidence, and financial engines are
unchanged. No Smart Context composition service, frontend Profile integration,
or automatic observed-income mutation exists yet.

ADR-028 and `SMART_FINANCIAL_CONTEXT_CONTRACT.md` now lock the future R2
semantics: Profile-owned declared monthly gross income; deterministic
three-distinct-months-in-six recurring candidates without an amount-similarity
score; explicit confirm/reject/reset decisions; and feature-specific context
composition. `SMART_FINANCIAL_CONTEXT_IMPLEMENTATION_PLAN.md` decomposes the
work. B1 implements persistence/ownership, B2 the declared Profile context API,
B3 deterministic recurring evidence, and B4 decision state/API. B5
feature-specific Smart Context composition is the next unstarted gate.

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
