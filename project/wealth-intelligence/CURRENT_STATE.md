# Current Repository State

**Status:** `VERIFIED CURRENT TRUTH`

**Updated:** 2026-10-16 — R4-C independently approved; checkpoint pending

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
| 10.R3-B.2 content fingerprint V1 amendment | `APPROVED / LOCKED / VERSIONED` |
| 10.R3-C domain/normalization/executable registry | `CLOSED / LOCKED` |
| 10.R3-D.1 registry version and UTC knowledge-time amendment | `APPROVED / LOCKED / VERSIONED` |
| 10.R3-D observation store/cache/freshness | `CLOSED / PUSHED` |
| 10.R3-E.0 historical revision windows/acquisition finalization amendment | `CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED / VERSIONED / PUSHED` |
| 10.R3-E1 store compatibility adapter | `CLOSED / PUSHED` |
| 10.R3-E2 BCB/SGS provider | `CLOSED / PUSHED` |
| 10.R3-E3 governed ingestion | `CLOSED / PUSHED` |
| 10.R3-E4 manual refresh | `IMPLEMENTED / TESTED / INDEPENDENTLY APPROVED / IMPLEMENTATION CHECKPOINT` |
| Structural FK Remediation (`position_snapshots`) | `IMPLEMENTED / FINDINGS REMEDIATED / TESTED / AWAITING INDEPENDENT DELTA REVIEW / NO DEPLOYMENT` |
| 10.R3-F.0 External Reference Context purpose contract | `CONTRACT APPROVED / DOCUMENTED` |
| 10.R3-F1 Point-in-time External Reference Read Boundary | `CLOSED / PUSHED` |
| 10.R3-G existing market boundary remediation | `SEPARATELY GATED / NOT STARTED` |
| 10.R3-H Focus expectations | `FOCUS DEFERRED / NOT IMPLEMENTED` |
| 10.R3-I independent stabilization | `INDEPENDENTLY APPROVED / DOCUMENTATION RECONCILED` |
| 10.R3 External Context | `R3-C CLOSED / R3-D.1 LOCKED / R3-D CLOSED / R3-E.0 PUSHED / R3-E1 CLOSED / R3-E2 CLOSED / R3-E3 CLOSED / R3-E4 INDEPENDENTLY APPROVED / R3-F.0 APPROVED / R3-F1 CLOSED / R3-I INDEPENDENTLY APPROVED` |
| 10.R4.0 Hybrid AI Runtime contract | `CONTRACT APPROVED / DOCUMENTATION IN PROGRESS` |
| 10.R4-A Provider-Neutral Contracts | `CLOSED / PUSHED` |
| 10.R4-B Authorization, Tools & Minimal Context | `CLOSED / PUSHED` |
| 10.R4-C Audit & Telemetry Boundary | `INDEPENDENTLY APPROVED / CHECKPOINT PENDING` |
| 10.R4-D Ollama Local Adapter | `OLLAMA NOT INSTALLED / INSTALLATION DEFERRED TO ASSISTED GATE` |
| Wealth OS Realignment | `ARCHITECTURE LOCKED / R2 CLOSED / R3-D CLOSED / R3-E3 CLOSED / R3-E4 INDEPENDENTLY APPROVED / R3-F1 CLOSED / R3-I DOCUMENTATION RECONCILED / R4-A CLOSED / R4-B CLOSED / R4-C CHECKPOINT PENDING` |

R3-B now has an approved and locked contract, official five-series BCB/SGS
registry, implementation decomposition, and accepted ADR-029. R3-B.1 replaced
the unsafe assumption that SQLite
`NUMERIC(38,18)` guarantees exact persistence with canonical fixed-scale text
and explicit `Decimal` conversion; preserves `A -> B -> A` as three knowledge
events; and separates refresh age, economic freshness, and acquisition health.
Independent review reported 0 blocking, 0 material, and 0 minor findings; the
user explicitly approved all ten material decisions on 2026-10-09. Independent
delta review of R3-B.2 on 2026-10-10 returned 0 blocking, 0 material, 0 minor,
and 2 informational findings; it reproduced all three normative hashes and the
V1 binary prefix. R3-B.2 normatively closes
`content_fingerprint_v1` with a versioned eleven-field payload, registry-first
validation and normalization, deterministic JSON, a V1 domain prefix, SHA-256,
three independently verified vectors, and version-aware comparison. The
amendment preserves all ten prior decisions and is independently verified and
locked. R3-C now implements the pure immutable Python domain, the exact
five-series executable registry, strict Decimal and civil-period normalization,
economic identity, structured errors, orthogonal status enums, canonical V1
JSON, and the locked SHA-256 fingerprint boundary. It adds no migration,
provider/network path, dependency, API, frontend, database, scheduler, or
engine behavior. Independent implementation review approved R3-C with 0
blocking, 0 material, 0 minor, and 2 informational findings. It confirmed
`127` focused R3-C tests, `160` R2 regressions, `497` Planning tests, `67` FIRE
tests, all three normative SHA-256 vectors, and OpenAPI compatibility at 55
paths and 59 HTTP operations with no External Context endpoint. The two
informational findings record that direct value-object construction is not a
substitute for certified registry-validation paths in future R3-D services,
and that OpenAPI paths and operations must remain distinct counts. Complete
units still expose the two unchanged historical Investments/MagicMock timeline
failures. R3-C is closed. The user explicitly approved the R3-D.1
registry-version and UTC logical knowledge-time decisions on 2026-10-10. The
controlled amendment now defines `EXTERNAL_SERIES_REGISTRY_VERSION = 1`,
dual-structure registry-version persistence, mismatch behavior, canonical
27-character UTC text, injected per-attempt logical transaction time,
`BEGIN IMMEDIATE` ordering, and the explicit limitation that `known_from` is
not a physical commit timestamp. Gemini 3.8 Flash High independently approved
the eight-document delta (0 blocking, 0 material, 0 minor, 2 informational);
no runtime test was executed in that documentary review. R3-D.1 is `CONTRACT
APPROVED / INDEPENDENTLY VERIFIED / LOCKED / VERSIONED`. R3-D now implements
the governed registry version, canonical UTC codec, two-table observation/sync
store, explicit SQLite `BEGIN IMMEDIATE` unit of work, immutable version
history, head-only deduplication, bitemporal reads, and independent operational
state evaluation. Gemini 3.8 Flash High independently approved the
implementation with 0 blocking, 0 material, 0 minor, and 2 informational
findings; SQLAlchemy 2.0.21 and 2.0.51 both passed the approved gates. R3-D is
closed and pushed at Git baseline
`d62012413f7ec956b070c0fe21420be1f29403ff`.

The user explicitly approved the R3-E.0 decisions on 2026-10-11 and the
Deferred Ingestion & Acquisition Finalization V1 remediation on 2026-10-12.
The documentation-only amendment now fixes the DAILY inclusive 90-day and
MONTHLY 24-civil-month revisit windows, manual bounded deep reconciliation, no
automatic first-acquisition backfill, an explicit default-compatible
`immediate`/`deferred` store adapter, read-only `get_sync_state(...)` returning
`None` for an absent row, governed `finalize_acquisition(...)`, counter/LKG
separation, and conservative requested/queried/observed coverage semantics.
It remediates `MAT-R3E0-01`, `MIN-R3E0-01`, `MIN-R3E0-02`, and
`INF-R3E0-01` at the contract level. Gemini 3.8 Flash High subsequently approved the
targeted remediation review with 0 blocking, 0 material, 0 minor, and 2
informational findings: the four findings are resolved, with `INF-R3E0-01`
governed by the contract; `INF-R3E0-02` (scalar discontinuous coverage) and
`INF-R3E0-03` (no persistent acquisition journal) remain visible V1 risks. It
implements no provider, ingestion, migration, scheduler, endpoint, deployment,
or BCB acquisition. R3-E1 now implements and tests only the store compatibility
adapter: default immediate behavior, opt-in deferred event persistence,
read-only sync-state lookup, and evidence-backed global finalization. It uses
the existing two-table R3-D schema and a documented conservative replacement
policy for newly certified continuous coverage. Gemini 3.8 Flash High approved
the independent adversarial code review with 0 blocking, 0 material, 0 minor,
and 3 informational findings: `INF-R3E1-01` scalar durable coverage,
`INF-R3E1-02` no persistent journal/distributed idempotency, and
`INF-R3E1-03` the unchanged Investments/MagicMock baseline. `INF-R3D-01` and
`INF-R3D-02` also remain preserved. R3-E1 is `CLOSED / PUSHED`. R3-E2 now
implements a persistence-free typed provider port, a fixed official BCB/SGS
HTTP client, deterministic provider-owned DAILY partitioning, sequential
bounded multichunk execution, strict response certification through R3-C, and
external-only `SUCCESS`, `EMPTY`, `PARTIAL`, and `FAILED` evidence. The five
series and their metadata remain registry-owned. No real HTTP request, SQLite
operation, scheduler, endpoint, or startup acquisition was introduced. Gemini
3.8 Flash High approved the independent adversarial R3-E2 review with 0
blocking, 0 material, 0 minor, 2 new informational findings, and 5 preserved
findings. `INF-R3E2-01` records aggregate in-memory observation accumulation;
`INF-R3E2-02` records the future-test dependence on `MockTransport` or an
equivalent injected transport. R3-E2 is `IMPLEMENTED / TESTED / INDEPENDENTLY
APPROVED / CHECKPOINT AUTHORIZED` and is closed/pushed at baseline `2ae5114`.
R3-E3 now composes that provider with the
existing R3-E1 store through an application-layer governed ingestion service.
It implements explicit ordinary and historical acquisition intents, the locked
DAILY and MONTHLY revisit windows, provider-complete-before-persistence
ordering, deferred per-observation writes, evidence-backed global
finalization, and typed separation between external provider status and the
committed global sync result. Its `34` focused tests use `httpx.MockTransport`
and disposable SQLite only. No live HTTP, active-database access, scheduler,
endpoint, frontend, migration, dependency, or financial-engine change was
introduced. Gemini 3.8 Flash High independently approved R3-E3 with 0
blocking, 0 material, 0 minor, no new informational findings, and the seven
preserved R3-D/R3-E1/R3-E2 informational findings. Its controlled checkpoint
was published as commit `686d64b49731a44a56e0d7fd8b44752ee1b663d8`; R3-E3
is `CLOSED / PUSHED`. R3-E4 now implements only the locked internal manual
trigger. It resolves a Registry V1 key, reads certified sync state through a
short-lived R3-E1 `get_sync_state(...)` boundary, evaluates the existing DAILY
six-hour or MONTHLY twenty-four-hour call-suppression policy, and delegates an
eligible request once to R3-E3. Ordinary and explicit bounded historical
intents remain distinct; no endpoint, scheduler, startup acquisition, automatic
backfill, or force bypass exists. The typed outcome keeps `NOT_ELIGIBLE`
separate from finalized `SUCCESS`, `EMPTY`, `PARTIAL`, and `FAILED`.

R3-E4 has `30` focused passing tests with fake providers and disposable migrated
SQLite. Combined R3-E4/R3-E3/store/policy validation is `120 passed`; R3-E2 is
`70`, R3-C `127`, R3-D/R3-E1 `61`, bootstrap `8`, FIRE/Goals/Planning `629`,
and selected R2 Smart Context `153`. Complete units report `1165 passed, 2
failed`, limited to the unchanged Investments/MagicMock baseline. OpenAPI
remains 55 paths and 59 operations with no External Context refresh route.
Gemini 3.8 Flash High independently approved the adversarial R3-E4 review with
0 blocking, 0 material, 0 minor, 1 new informational finding, and 7 preserved
informational findings. `INF-R3E4-01` is open: the internal typed
`HISTORICAL_RECONCILIATION` intent requires future caller-boundary
authentication and specific administrative authorization if it is ever exposed;
no endpoint or RBAC mechanism is introduced by R3-E4. The preserved findings
are `INF-R3D-01/02`, `INF-R3E1-01/02/03`, and `INF-R3E2-01/02`. R3-E4 is
`IMPLEMENTED / TESTED / INDEPENDENTLY APPROVED / IMPLEMENTATION CHECKPOINT`.

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
- R4-A provider-neutral contracts, immutable registries, strict validator,
  internal proof service, and deterministic fake provider exist;
- R4-B adds an internal authenticated-scope resolver, an immutable exact
  five-tool read-only registry, a deny-by-default executor, and a minimized
  certified context builder over R2 readers;
- R4-C adds immutable versioned audit events, pseudonymous technical scope,
  allowlisted metadata construction, typed optional telemetry, replaceable sink
  ports, deterministic volatile in-memory sinks, and fail-closed audit-guarantee
  enforcement;
- no real provider adapter, router, retry executor, fallback executor, or
  durable audit/telemetry persistence;
- the three `backend/integrations/gemini/*.py` files are empty;
- AI-related database tables and environment settings are scaffolding only;
- `google-generativeai` being installed does not constitute a runtime.

Any UI copy suggesting that local Ollama or a Wealth Advisor is already active
is placeholder/future-facing copy, not implemented capability.

The R4.0 Hybrid AI Runtime contract is approved and R4-A is closed/pushed at
`bea92edb18872bd3e3603dc10ebc62bed8de8100`. R4-B is closed/pushed at
`8149e3d27a75c76ed6cc7f46fab60aabebd96396` and implements only the
internal server-scope, read-only registry/executor, and minimal R2 context
boundary. Its exact tools are
Home, Planning, Goal, FIRE context, and one owned-Goal read. Independent review
reports `84 passed` with `0 BLOCKING / 0 MATERIAL / 0 MINOR` new findings. The R2
single-tenant guard remains fail-closed and is not a universal multi-tenant
claim. No R3 External Reference consumer or Planning/FIRE engine tool is
activated. R4-C now implements the logical audit and telemetry boundary and is
`INDEPENDENTLY APPROVED / CHECKPOINT PENDING`: `21` focused tests plus `56`
direct R4-A/R4-B regressions pass (`77 passed`), with `0 BLOCKING` and `0
MATERIAL` active findings. Historical `MAT-R4C-01` is adjudicated
`INFORMATIONAL / FUTURE ACTIVATION BLOCKER`: no pre-execution guard is
integrated into R4-A/R4-B, so the emitter alone does not guarantee fail-closed
behavior before execution; a `VOLATILE` sink never substitutes for `DURABLE`.
R4-F must integrate and validate the guard before operational provider or tool
dispatch. `INF-R4C-01` remains for future HMAC-key configuration/rotation/key-ID
governance. There is still no production AI runtime. Audit persistence and
definitive retention are `NOT AUTHORIZED`; historical `ai_runs` remains
untouched. Ollama is `NOT INSTALLED`, no eligible local runtime is available,
and Gemini was `NOT CALLED`. `LOCAL_ONLY` remains the default. R4-D and later
increments are `NOT IMPLEMENTED`; benchmarking, installation, downloads,
provider SDKs, provider execution, database access, migration, endpoint,
frontend, and scheduler remain separately gated.

## External context current state

| Source | Current state | Boundary |
|---|---|---|
| Pierre Finance | Active import/API | Governed after ingestion under existing rules |
| MyProfit CSV | Active import for positions, portfolio history, and income events | Provider facts with grain/provenance limitations |
| yfinance | Active quote/history/fundamental adapter with memory cache | Provider-specific reference; not a shared external-context layer |
| BCB/SGS | R3-C domain/registry and R3-D persistence closed; R3-E1 through R3-E3 closed/pushed; R3-E4 internal manual refresh independently approved with fake providers and disposable SQLite | No live BCB acquisition, public API, scheduler, automatic refresh, deployment, or consumer read model |
| News | Absent | No provider, provenance, or relevance contract |

The R3-C foundation and R3-D persistence implementation now exist. R3-D adds
the executable registry-version constant, canonical UTC codec, Alembic revision
`4f9c2d7e1a6b`, the two approved tables, caller-session repositories, explicit
writer serialization, immutable event history, sync state, as-of reads, and
state evaluators. No provider, scheduler, endpoint, or consumer context was
added. Gemini 3.8 Flash High independently approved R3-D with 0 blocking, 0
material, 0 minor, and 2 informational findings. SQLAlchemy 2.0.21 and 2.0.51
both passed the R3-D/R3-C gates; every migration and persistence test used a
disposable SQLite database and the active database was untouched. R3-E1 is
closed and pushed. R3-E2 adds only the external provider foundation: one
bounded request per client call, deterministic multichunk planning in the
adapter, strict JSON/date/Decimal validation, R3-C normalization, and typed
per-chunk and aggregate evidence without persistence claims. Its `70` focused
tests used only `httpx.MockTransport`; R3-C `127`, R3-D/R3-E1 `61`, and
bootstrap `8` regressions pass. Gemini 3.8
Flash High approved the independent R3-E2 review with 0 blocking, 0 material,
0 minor, 2 new informational findings, and 5 preserved findings. R3-E2 is at
closed and pushed baseline. R3-E3 adds the internal application
orchestrator without a public trigger: all provider work completes before any
SQLite write; successful observations use R3-E1 deferred ingestion; empty,
failed, and incomplete chunks become typed finalization evidence; and the
service returns only after R3-E1 commits the derived global result. R3-E3
focused tests report `34 passed`; current complete units report `1135 passed, 2
failed`, limited to the unchanged Investments/MagicMock baseline. The same
R3-E3 plus R3-D/R3-E1 selection reports `95 passed` on SQLAlchemy 2.0.21.
The independent review reproduced the R3-E3 `34`, R3-E2 `70`, R3-C `127`,
R3-D/R3-E1 `61`, combined `95`, bootstrap `8`, FIRE/Goals/Planning `629`, R2
`153`, and complete-unit `1135 passed, 2 failed` evidence on Python 3.14.0,
SQLite 3.50.4, and SQLAlchemy 2.0.51. R3-E3 is closed and pushed at
`686d64b49731a44a56e0d7fd8b44752ee1b663d8`. R3-E4 adds the internal explicit
trigger and is implemented/tested and independently approved. Concurrent
eligible triggers may duplicate external calls because V1 has no persistent
attempt journal or distributed single-flight; store serialization preserves
history and operational state, and no exactly-once guarantee is claimed. No
live BCB observation has been acquired.

R3-F.0 is `CONTRACT APPROVED / DOCUMENTED`. Its closed purpose enum contains
only `MARKET_INTEREST_RATE_REFERENCE`, `MARKET_INFLATION_REFERENCE`, and
`MARKET_FX_REFERENCE`. The additional immutable service allowlist maps them,
respectively, to the three SELIC/CDI series, IPCA monthly, and USD sell from
Registry V1, for the future internal Market context composer only; no runtime
consumer is active. R3-F1 is `CLOSED / PUSHED` at checkpoint
`30c4df058fd80923c37243252f4ee8fc6fa76dce`; its independent audit reported
0 blocking, 0 material, and 0 minor findings.

The approved R3-F1 boundary is a read-only point lookup with explicit economic
date and UTC knowledge-time cuts. It separates deterministic bitemporal
`reference_replay` from current `operational_state_snapshot`, which makes no
historical-state claim. Economic freshness is policy-derived and conservative:
insufficient evidence is `UNKNOWN`. The selected observation retains its
original economic period across weekends, holidays, or unpublished months.
No history window, interpolation, carry-forward, implicit financial default,
write, endpoint, frontend, scheduler, migration, engine calculation, or change
to the canonical wealth source is implemented or authorized. The implementation
adds only a closed immutable purpose matrix, immutable request/result envelopes,
and a read-only service that delegates to `get_latest_series_as_of(...)` and
`get_sync_state(...)`. It preserves the certified event unchanged, reports
explicit absence, keeps operational state separate with no invented
`state_observed_at`, and derives `CURRENT` only from complete positive coverage
and selected-head evidence; otherwise freshness is `UNKNOWN`. R3-F1 focused
tests report `28 passed`, and its combined Registry/Store regression gate
reports `100 passed`.

R3-I Independent Stabilization is `INDEPENDENTLY APPROVED / DOCUMENTATION
RECONCILED`. Its fresh-context transversal audit passed `234` tests,
found no new code finding, and preserved eight historical informational
findings. R3-G remains separately gated, R3-H remains deferred, and no R3-F2
exists in the current roadmap.

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
`10.R3-B = CONTRACT APPROVED / LOCKED`; R3-B.2 is approved, locked, and
versioned. R3-C is
`IMPLEMENTED / VALIDATED / INDEPENDENTLY APPROVED / CLOSED`; R3-D.1 is
`APPROVED / LOCKED / VERSIONED`; R3-D is `CLOSED / PUSHED`; R3-E.0 is
`CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED / VERSIONED / PUSHED`;
R3-E1 is `CLOSED / PUSHED`; R3-E2 is `CLOSED / PUSHED`; R3-E3 is `CLOSED /
PUSHED`; R3-E4 is `IMPLEMENTED / TESTED / INDEPENDENTLY APPROVED / IMPLEMENTATION CHECKPOINT`.
Product
recomposition and smart-prefill behavior remain reserved for R6.

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
- `INF-R3D-01`: global SQLite foreign-key enablement passed tested
  environments. A conditional structural remediation for a reported invalid
  `position_snapshots.account_id -> accounts.id` physical constraint was
  implemented in migration `b7e2d1a4c9f3`. Its preflight now rejects inbound
  FKs and semantically divergent secondary indexes before batch DDL. Targeted
  evidence is `22 passed` for remediation and `27 passed` with pertinent
  External Context migration coverage. Historical complete units remain `1175
  passed, 2 failed` and were not rerun in this targeted task.
  Canonical Alembic history never declared that FK; the exact origin of the
  reported physical drift remains unproven. The backend traceback confirmed the
  invalid FK failure, and the user confirmed MyProfit import after the separate
  operational hotfix.
  Operational Alembic remains at `2d6b4f8a9c1e`; this reconciliation did not
  access or modify the operational database.
  Active-database deployment remains blocked pending legacy referential-integrity
  assessment, backup/rollback, intermediate migration alignment, and explicit authorization.
- Fresh `alembic upgrade head` from an empty disposable database remains blocked
  by pre-existing dual-root bootstrap debt: both historical roots attempt to
  create `categories`. The FK remediation neither reaches nor changes that path.
- `INF-R3D-02`: declared Pydantic pins are not clean-install reproducible and
  existing tests require undeclared `pytest-asyncio`; dependency remediation
  remains a separate unauthorized task.
- There is no certified sustainable contribution-capacity engine, portfolio
  performance engine, rebalancing engine, watchlist, BCB/news integration,
  Docker deployment, or AI runtime.

Historical phase-by-phase execution evidence remains in `CHANGELOG.md`,
`TESTING_STRATEGY.md`, accepted ADRs, and locked contracts. It is intentionally
not duplicated in this current-state summary.
