# Current Repository State

**Status:** `VERIFIED CURRENT TRUTH`

**Updated:** 2026-10-30 — legacy financial routes contained locally; ownership pending; SEC-DEP-C/JWT history below

This document describes what exists now. Future product architecture belongs to
`MASTER_PLAN.md` and `ARCHITECTURE.md`; execution order belongs to
`IMPLEMENTATION_ROADMAP.md`.

When remote `develop` confirms the isolated publication commit containing this
reconciliation, SEC-AUTH-LEGACY-ROUTES is
`PARTIALLY MITIGATED / INDEPENDENTLY REVIEWED / COMMITTED / PUSHED / OWNERSHIP PENDING`;
until then publication remains pending. The isolated line reapplies the security
commits, excludes launcher commit `b754e6e`, and leaves original local checkpoint
`8578307` intact. The histories require separate future reconciliation; local
`develop` is not thereby synchronized. The five operations remain blocked,
ownership is not certified, `INF-SEC-LEGACY-01` remains open, and no deploy or
global security approval follows. See `SECURITY_AND_GOVERNANCE.md` for details.

The following paragraph records the prior local checkpoint state:

TSK-SEC-AUTH-LEGACY-ROUTES is **PARTIALLY MITIGATED / OWNERSHIP PENDING**.
When both authorized local checkpoint commits exist, its state is
`PARTIALLY MITIGATED / INDEPENDENTLY REVIEWED / COMMITTED LOCALLY / PUBLICATION PENDING / OWNERSHIP PENDING`;
until then, the checkpoint is incomplete. At the original implementation
preflight, the changes were local and uncommitted on `develop` at
`b754e6e3665bb0a644d7c06edd1cb79473633468`.
The five actually mounted legacy operations (GET accounts, transactions,
categories, dashboard; POST pierre/import) reproduced unauthenticated and
invalid-Bearer HTTP 200 on synthetic fixtures. Both routers now reuse
`get_current_user` and deny authenticated access with 403 because their raw
ledger/import scope has no certified ownership contract. Missing/invalid/
refresh credentials return 401; inactive users retain existing 400 behavior.
No ownership or schema was invented. These capabilities are intentionally
unavailable pending an explicit scope decision; existing frontend consumers
are affected. New HTTP coverage: 54 tests; with JWT: 120 passed; expanded
56-file regression: 1339 passed, 218 warnings, zero failures/errors/skips.
OpenAPI changes only five OAuth2 security requirements; 61 paths / 65 operations
and financial schemas are preserved. The prior launcher line-ending deviation
and bytes remained intact at implementation validation. No real provider/import/
database, Engine, frontend, runtime, push or deploy change occurred in that task.
The owner reports independent approval with three informational findings:
`INF-SEC-LEGACY-01`, `INF-SEC-LEGACY-02`, and `INF-SEC-LEGACY-03`.
Ownership, review details, consumer impact, reproducible evidence and limits are owned by
`SECURITY_AND_GOVERNANCE.md`; global security is not approved and
SEC-JWT-LEGACY remains independent.

TSK-SEC-JWT-01 is `REPRODUCED / IMPLEMENTED / VALIDATED / COMMITTED / PUSHED`;
functional commit `79c7280ce6eb6a8ab362759ac4d884264b4be8ff`, documentary
commit `1684ecc57dd66ff0280a31bb6d5688645b26c503`. The pre-fix baseline accepted refresh JWTs as
access Bearers (HTTP 200) and returned 500 for malformed textual UUID subjects.
New access tokens explicitly declare their purpose; the shared HTTP boundary
rejects refresh/invalid types and malformed subjects with 401, retaining valid
legacy access sessions and the existing inactive-user policy. Focused coverage
passed 66 tests (11 warnings); expanded regressions passed 1,156 (121 warnings)
with five temporary-directory setup errors, then those five passed on isolated
retry. The checkpoint reran the same 43-file selection in one process:
`1161 passed, 121 warnings, 0 failed, 0 errors, 0 skipped`; no full-suite or
global-security approval is claimed. `SEC-JWT-LEGACY — REMOVAL PENDING` tracks
the compatibility branch without an automatic cutoff. Reproduction,
commands, limitations and legacy sunset policy are owned by
`SECURITY_AND_GOVERNANCE.md`. The Journey A publication below predates this
published security checkpoint; operational R4 remains separately gated, `LOCAL_ONLY`
remains the default and R7 is not started.

SEC-DEP-C is `VALIDATED / CHECKPOINT PENDING`, with local uncommitted manifest
changes. The owner's runtime decision retains ordinary CPython 3.14.0 Windows
AMD64. Selected pins: FastAPI 0.139.2, Starlette 1.3.1, Pydantic 2.13.4,
settings 2.14.2, pandas 2.3.3, SQLAlchemy 2.0.44, multipart 0.0.31,
pytest 9.0.3 (separately authorized) and pytest-asyncio 1.4.0. All other direct
pins are retained. A newly created outside-repo venv installed the complete
manifest without copying main packages: 77 wheel distributions plus bootstrap
pip, `pip check` clean. Runtime/app/TestClient imports and lifespan passed.
Focused validation returned `133 passed, 26 warnings`; the exact 51-file
regression returned `1243 passed, 125 warnings` in one process. Both have
0 failed/errors/skipped. The unchanged nine Starlette tests pass, including
urlencoded rejection; four new canaries preserve pandas provider behavior and
sync/async SQLite Decimal/transaction behavior. Complete OpenAPI JSON matches
the fresh baseline (61 paths / 65 operations), not only its counts.

The main venv remains unchanged at the same 117 distribution versions; its
Starlette 1.1.0 remains vulnerable pending separately authorized rollout.
Candidate OSV queried 78 distributions: 16 alias records / 8 GHSA records across
the already-known ecdsa, python-jose and bootstrap pip findings; no matches for
the altered families. Existing applicability qualifications and A's 122-match
inventory remain preserved. SEC-DEP overall remains `PARTIALLY REMEDIATED /
LOCAL CHANGES`, not global security approval. No stage, commit, push, deploy,
financial code/schema, frontend, JWT or main-env change occurred. Details and
commands are in `SECURITY_AND_GOVERNANCE.md`.

At SEC-DEP-B's historical checkpoint the state was `BLOCKED / REQUIRES DECISION`.
Both proposed framework combinations
resolve their framework-only subsets, but full clean Python 3.14 installations
fail building the unchanged pandas 2.1.1 pin (no matching wheel; Meson cannot
find Visual Studio's vswhere.exe). The unchanged SQLAlchemy 2.0.21 pin also
fails a standalone import under Python 3.14. No framework/Pydantic/scientific
pin was promoted into requirements.txt; the prior multipart 0.0.31 edit and
multipart test remain byte-identical to SEC-DEP-A's preflight snapshot.
The new nine-case Starlette regression reproduces two failures on main 1.1.0
and passes all nine on a fresh framework-only 1.3.1 probe. This is component
evidence, not application/OpenAPI/51-file validation. Those gates were not run
because the clean full-manifest gate failed. The main venv remains unchanged;
the dependency/runtime decision matrix is in `SECURITY_AND_GOVERNANCE.md`.

At SEC-DEP-A's historical checkpoint, SEC-DEP was `PARTIALLY REMEDIATED /
LOCAL UNCOMMITTED CHANGE`: only the declared
multipart pin changes from vulnerable `0.0.6` to `0.0.31`, the lowest version
outside all nine current maintainer/GHSA advisory ranges. The main virtualenv
already contains `0.0.32` and remains unchanged. A disposable Python 3.14 clone
preserved all 117 installed distribution versions except multipart, and passed
`pip check`, 80 focused tests (12 warnings), and 1,243 selected regressions in
51 files (122 warnings; 0 failures/errors/skips), including the prior 43-file
JWT selection and Health. OpenAPI is identical: 61 paths / 65 operations.
This validates the installed-stack replica, not a clean requirements install:
the declared Pydantic/settings pins remain unsatisfiable. A bounded probe also
confirmed Starlette 1.1.0 ignores urlencoded field/part limits. Neither that
framework finding nor the other OSV version matches is remediated here.
Evidence, sources, distribution-only inventory, applicability and next approval
boundary are owned by `SECURITY_AND_GOVERNANCE.md`; SEC-DEP is not closed.

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
| 10.R4-C Audit & Telemetry Boundary | `CLOSED / PUSHED` |
| 10.R4-D Ollama Local Adapter | `R4-D.2 USER-OBSERVED VALIDATION RECORDED / TECHNICAL CANDIDATE ONLY` |
| 10.R5 technical implementation/checkpoint | `IMPLEMENTED / AUTOMATED GATES PASSED / COMMITTED / PUSHED` |
| 10.R5 visual acceptance / closure | `USER VISUAL ACCEPTANCE APPROVED FOR CURRENT BASELINE / CLOSED` |
| 10.R6 general gate | `SATISFIED / READY FOR EXPLICITLY CONTRACTED INCREMENTS` |
| 10.R6.1 Goals → Planning | `IMPLEMENTED / AUTOMATED GATES PASSED / USER MANUAL ACCEPTANCE REPORTED / COMMITTED / PUSHED` |
| 10.R6.2 Goal Progress | `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED` |
| 10.R6.3 Goal Monitoring Overview | `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED` |
| 10.R6.4 Goal Batch Contribution Preview | `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED` |
| 10.R6.5-A budget contract | `CONTRACT APPROVED` |
| 10.R6.5-B budget backend | `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED` |
| 10.R6.5-C product integration | `IMPLEMENTED / AUTOMATED GATES PASSED / USER ACCEPTED / COMMITTED / PUSHED` |
| Later R6 increments | `NOT AUTHORIZED` |
| Wealth OS Realignment | R2 and R5 closed; R3 foundation independently approved; R4-A/B/C closed, operational R4 gated; R6.1–R6.5-B published; R6.5-A approved; C user accepted/committed/pushed; Journey A functionally accepted/published; R7 not started |

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
| Wealth Intelligence W2–W4.2 / R5 checkpoint | Authenticated Wealth Home v2 composition for monthly Health, current Goals, and governed monthly investment wealth; month-aware navigation; five Planning flows; three FIRE modes; one in-memory selected result | `GET /api/v1/wealth-home`, Wealth Intelligence frontend/tests, reconciliation audit, checkpoint `1fae590fb316b4f9d9584aad23cdde4fe8f3af9b` |
| Smart Context B1-B7 foundation | Declared-context and recurring-decision persistence, exact Decimal constraints, fail-closed ownership, authenticated declared Profile context GET/PATCH, deterministic recurring-income evidence, authenticated review/confirm/reject/reset decision API, internal feature-specific composition, the Profile declared/observed review experience, and typed read-only future-consumer boundaries | migration `2d6b4f8a9c1e`, Smart Context backend tests, B6 frontend tests/typecheck/build |
| Market data | yfinance adapter/service with provider-specific cache behavior | market-data protocol and yfinance integration |

The existing Investments product surfaces are real, but their mixed valuation,
performance-like, score, and browser-calculation paths are not certified
Portfolio Intelligence authority. Phase 10.5-A remains the governing audit for
that distinction.

## Present UI and navigation

The current top-level product is organized around Controle Financeiro,
Investimentos, Inteligência Patrimonial, Governança, and Configurações. In the
current worktree, `/wealth-intelligence` is a composed Home rather than a module
directory. It presents independently governed monthly Health, current Goals,
and ADR-023 investment-wealth facts; keeps demonstration content explicit;
links to the canonical nested Goals, Health, Planning, and FIRE routes; and can
show one user-selected Planning/FIRE response in navigation-scoped memory only.
The selected result is not persisted and disappears on refresh, logout, token
change, or identity change.

The user explicitly authorized the bounded R5 contract on 2026-10-24. The
existing W2–W4.2 implementation is reused as its product baseline. R5 automated
acceptance gates passed, and its technical checkpoint is committed and pushed
at `1fae590fb316b4f9d9584aad23cdde4fe8f3af9b`. On 2026-10-27 the project owner
expressly accepted the current visual baseline and deferred additional UI/UX
improvements to backlog. That acceptance does not claim that every browser,
viewport, state combination, or manual accessibility scenario was individually
tested. R5 is closed and the general R6 sequencing gate is satisfied. The
project owner had expressly amended the sequencing rule on 2026-10-25 only for
R6.1 Goals → Planning; that exception remains preserved historically. R6.1 now
implements the approved authenticated Goal-context read model, deep link,
presets, safe Goal switching, navigation, and tests. Its minimalist refinement
removes duplicate page chrome and local journey navigation, keeps the global
navigation authoritative, and preserves accessible semantic headings, the
segmented Objective selector, and compact nominal/real option summaries. The
automated gates pass, and the user reported the tested experience satisfactory
for the current scope. Its two-commit checkpoint is published at
`1b0a1c6fa538ad69c415c29f77c8f91b68f4dd0b`. This report does not assert every
viewport, browser, calculation, or manual accessibility scenario and does not
independently classify all of R6 as closed. R6.2 was subsequently defined and
explicitly authorized as a bounded Goal Progress read model. It exposes
authenticated cadastral progress from `target_amount` and `current_amount`
through the existing owned Planning Goal reader, with signed Decimal gap and an
uncapped two-decimal completion percentage. It performs no writes, projection,
engine execution, portfolio/MyProfit read, or automatic investment-to-Goal
linkage. Focused validation passed and its checkpoint is published at
`7828f64a2d8d0a25605bcb2c459775e176f99292`. R6.3 provides the explicitly
authorized authenticated Goal Monitoring overview over the owned batch reader
and is published at `1f743b297449d17064d68376891edab88432e1d2`. R6.4 now
provides an authenticated, transient preview of the required monthly
contribution for each explicitly selected owned Goal. It performs one batch
read, uses only each Goal's cadastral target/current amount, and delegates every
calculable item to the certified Required Contribution solver. Missing or
invalid facts remain unavailable rather than becoming invented zeroes. Focused
validation passed. R6.4's functional commit is
`7827f8a3820b23dbe42ab93040cccf1161af192d` and its documentary commit is
`40a23566b3b068e26cb8bd3ae94bc7ed060ec4b0`. Publication was confirmed in the
preceding controlled push; this documentary task verified local HEAD and the
local `origin/develop` reference at that SHA without a new remote query.
R6.2–R6.4 remain backend capabilities, not an implemented multi-Goal UI.
R6.5-A now records the owner's D1–D3 approval in
`GOAL_BUDGET_PREVIEW_CONTRACT.md`: exactly A/B with equal allocated totals,
common nominal premises and permitted explicit excess. The contract defines
the additive authenticated budget preview and direct reuse of the certified
scenario comparator per owned Goal, not an inverse required-contribution solve.
R6.5-B is `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED` under the
explicit TSK-R6.5-B authorization. `POST /api/v1/planning/goals/budget-preview`
performs one owned batch read, exact local-Decimal budget accounting, and one
certified `ScenarioComparisonEngine.compare` call per available Goal. A/B have
equal allocated totals and common nominal premises; excess is permitted and
shown. Missing facts preserve null comparisons. No inverse solve, write,
external/AI call, Engine change or simulation persistence is introduced.
Final validation on 2026-10-29: new domain/API suites `192 passed, 3 warnings`;
Planning/Goals/FIRE/Profile regression selection `946 passed, 113 warnings`,
including those 192 tests. Warnings originate in existing Pierre/Goals code.
Commands and scope are recorded in the microcontract implementation evidence.
R6.5-B's functional commit is `754a9dedf3fe57590c0af3f524573a14b6dfe961`;
the documentary commit is `b59e2af63fbc6a093bafa4a50a375571a1877ab6`.
The preceding controlled push confirmed the latter as the real remote
`develop` SHA with `git ls-remote`; this frontend task did not repeat that push.
Earlier checkpoint-pending/uncommitted statements in dated phase evidence
describe the pre-publication state and do not override this current record.

R6.5-C now integrates `Objetivo → Meta cadastrada → Distribuir orçamento` in
the existing Planning route, without a fourth intention or additional tab bar.
Users explicitly select 1–20 owned Goals, enter a monthly budget, horizon,
hypothetical annual return and independent A/B allocations, then request the
comparison. Existing lexical pt-BR adapters retain financial strings; the
backend alone validates equal totals, accounts for budget/excess and calculates
projections/deltas. Selection uses only Goal identity/name/status; legacy
numeric Goal amounts are not Planning facts or automatic presets.

Responsive cards show returned budget summaries and A/B results per Goal,
including unavailable projections, target states, signed certified deltas and
source/update context. Inputs/results remain memory-only. Edits, Goal refresh,
401, logout, identity/token changes and unmount invalidate old requests/results.
The shared cancellable HTTP path rejects obsolete responses before an old 401
can clear a replacement session. A missing/foreign Goal requires explicit list
refresh; missing selections are never silently removed from the simulation.

R6.5-C automated validation on 2026-10-29: focused form/component/client/page
tests `69 passed`; complete frontend Vitest `292 passed` in 34 files;
TypeScript `--noEmit`, affected-file ESLint and Next.js build passed (38 routes).
The existing Recharts prerender width/height warning remains. Two synthetic
JSON fixtures were generated through the existing certified backend services;
no backend suite, active database, provider or LLM was executed for this task.
On 2026-10-29 the responsible owner formally accepted R6.5-C and Journey A's
functional scope. **USER-REPORTED MANUAL PASS — NOT DIRECTLY OBSERVED BY AGENT.**
The owner reported C1 (1,200 allocated, 300 available), C2 (300 excess, no
redistribution), C3 (unequal totals rejected and prior result invalidated), and
C4 (explicit zero budget and contributions accepted). Reported checks also
covered per-Goal results against the API, navigation/deep links, responsive
layouts, Light/Dark/System, keyboard and safe session cases including delayed
401. No screenshots are claimed. This acceptance covers Goal selection, context,
progress, individual and joint planning, required contributions, monthly budget,
A/B comparisons and certified results. R6.5-C is now `USER ACCEPTED / COMMITTED /
PUSHED` at `0ac08c11ba4a05342641c0c9365977c9d2c727e6` (functional parent
`342c83ced47419269d4ae850345e5cd5a368a4c7`); at this task's preflight local
`develop` and the existing `origin/develop` ref matched that checkpoint. Publication is confirmed by the
owner's current task; no network refresh was performed. Journey A is
`FUNCTIONALLY ACCEPTED / PUBLISHED`. Publication does not imply deployment,
operational AI, Health-derived assumptions, automatic Goal wealth linkage,
Portfolio Intelligence or R7 closure.
No Health-derived future capacity or automatic Goal–FIRE/portfolio link exists.

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

**Evidence reconciliation (2026-10-28):** the historical local laboratory is
present under ignored `experiments/llm-benchmarks/` and the four historical
`benchmark/finanalytics_benchmark*` directories (not a blanket benchmark ignore).
Its `reports/consolidated.md` records synthetic local experiments, not official
R4-G completion. Qwen 3.5 4B remains the initial evaluation baseline, not a
production selection. The later lab records Ollama 0.40.6; the 0.40.5 setup
record below remains dated evidence, not today's environment inventory.
`stage_q1_hr_corrected_consolidation_v2.md` preserves 20 completed assisted
human reviews without converting textual quality into objective correctness.
`stage_q1_thinking_t0_final.md` records 5/8 calls and an interrupted,
methodologically failed battery, with no T1 eligibility. No experiment was
rerun and no installed-model/service state was probed in this task.

For local AI: `LAB TESTED` with limitations; operational `RUNTIME IMPLEMENTED`,
end-to-end `SECURITY GATES PASSED`, `APPROVED FOR REAL DATA`, and
`PRODUCT INTEGRATED` are not established. For Gemini: no equivalent online
fixture evidence was found in the inspected lab reports; adapter and product
integration are absent, and real-data approval is absent. R4-A/B/C tests prove
their internal boundaries only. The governed comparison plan lives in
`AI_AND_LLM.md`; its order and gates live in `IMPLEMENTATION_ROADMAP.md`.

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
activated. R4-C implements the logical audit and telemetry boundary and is
`CLOSED / PUSHED` at checkpoint
`14cb65db1cddd5466523eefdca54c78affb3eca7`: `21` focused tests plus `56`
direct R4-A/R4-B regressions pass (`77 passed`), with `0 BLOCKING` and `0
MATERIAL` active findings. Historical `MAT-R4C-01` is adjudicated
`INFORMATIONAL / FUTURE ACTIVATION BLOCKER`: no pre-execution guard is
integrated into R4-A/R4-B, so the emitter alone does not guarantee fail-closed
behavior before execution; a `VOLATILE` sink never substitutes for `DURABLE`.
R4-F must integrate and validate the guard before operational provider or tool
dispatch. `INF-R4C-01` remains for future HMAC-key configuration/rotation/key-ID
governance. There is still no production AI runtime. Audit persistence and
definitive retention are `NOT AUTHORIZED`; historical `ai_runs` remains
untouched. Ollama `0.40.5` is installed through the exact user-scoped WinGet
package. User-observed evidence records user-scoped `LOCAL_ONLY` operation,
Qwen 3.5 4B `Q4_K_M` with Ollama model ID `d8b0f5e9760c`, context `4096`, and
concurrency `1`. No provider is activated in FinAnalytics. Gemini was `NOT
CALLED`; operational provider integration, formal benchmarking, provider SDKs,
database access, migration, endpoint, frontend, scheduler, and subsequent R4
work remain separately gated.

The user-approved R4-D evaluation order is Qwen 3.5 4B `Q4_K_M` first and Qwen
3.5 9B `Q4_K_M` second. PrismML Bonsai 8B GGUF `Q1_0` is a third,
experimental candidate and does not alter that priority. It is based on
Qwen3-8B, not Qwen 3.5, and published as approximately 8.19B parameters, a
1.16 GB GGUF file, and Apache 2.0. Compatibility with Ollama `0.40.5` and total
VRAM are `NOT VERIFIED`; a compatible llama.cpp may be required under a
separate gate. Published unfavorable comparative tool-calling evidence must be
retested locally. These are candidates only: no winner exists without
equivalent, entirely offline synthetic-financial-task evidence for Portuguese,
financial interpretation, structured JSON, Decimal/provenance preservation,
tool selection, abstention, grounding/hallucination, quality, latency, tokens/s,
context use, RAM, VRAM, and GPU/CPU layer placement. The host has 32 GB across
four declared DDR4-2400 8 GB modules in a declared quad-channel configuration;
the resulting theoretical 76.8 GB/s ceiling remains subject to verification.
Ollama is the initial runtime and direct llama.cpp remains a future comparison.

The user-observed R4-D.2 validation ran Qwen 3.5 4B on the RTX 5060 through
CUDA with `33/33` layers on GPU. With thinking off, synthetic tests completed,
JSON was syntactically valid, warmed generation was approximately `80-84
tokens/s`, and tested warmed responses took approximately `3.5-4.9 seconds`.
Source fidelity still requires stricter testing: this is a technical candidate,
not a production-certified model. With thinking on, JSON plus `1800` tokens
produced no final answer, and no JSON plus `3000` tokens produced a partial final
answer; both ended with `done_reason=length`, at generation near `81 tokens/s`.
That mode is `NOT APPROVED IN TESTED CONFIGURATION`; no automatic budget
increase or universal model-defect conclusion follows. Initial loads showed
intermittent GPU-discovery timeouts before successful initialization. Empty or
partial answers, sources, grounding, and financial conclusions require strict
future validation. No operational integration is authorized, and R4-F remains
blocked on its pre-execution guard and `DURABLE` audit requirement.

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

The live shell now supports System, Light, and Dark through semantic surface,
text, border, status, financial, chart, focus, spacing, and interaction tokens.
Only the `fin_theme` appearance preference is persisted; financial data,
scenarios, and transient Planning/FIRE results remain outside browser storage.
The inline bootstrap and provider keep first paint and hydration aligned with
the stored or operating-system preference. Wealth Intelligence shared cards,
tables, charts, inputs, dialogs, loading/error/empty states, and the Goals CRUD
surface consume the semantic theme boundary. Reduced-motion and visible-focus
rules are global. The Planning route now exposes ADR-024's three top-level
intentions with the three Objective tasks nested under `Objetivo`, while all
five deterministic capabilities and their endpoints remain unchanged.

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
- Repository-wide mobile and lint debt outside the bounded R5 surfaces remains.
  The production build also preserves a Recharts SSR dimension warning from
  the legacy `/wealth/asset/[ticker]` route; the R5 Health chart declares
  minimum and initial dimensions.
- The public Goals API still represents money and progress with `float`; the
  Decimal-safe Planning reader deliberately bypasses that legacy path.
- R5 is user-accepted and closed for the current visual baseline. Automated
  component, accessibility, type, lint, build, route, and backend contract gates
  passed; the project-owner acceptance does not claim an exhaustive browser,
  viewport, state, or manual-accessibility matrix. Further UI/UX work is backlog.
- The general R6 sequencing gate is satisfied. R6.1 Goals → Planning is
  `IMPLEMENTED / AUTOMATED GATES PASSED / USER MANUAL ACCEPTANCE REPORTED /
  COMMITTED / PUSHED`. R6.2 Goal Progress is `IMPLEMENTED / FOCUSED TESTS
  PASSED / COMMITTED / PUSHED`. R6.3 Goal Monitoring Overview is `IMPLEMENTED /
  FOCUSED TESTS PASSED / COMMITTED / PUSHED`. R6.4 Goal Batch Contribution
  Preview is `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED`.
  R6.5-A's contract is approved; R6.5-B is committed/pushed; R6.5-C is user accepted/committed/pushed, and Journey A is functionally accepted/published;
  R7, Advisor, Portfolio Intelligence, and later increments remain gated.
- `PLANNING_GOAL_CONTEXT_READ_MODEL_PROPOSAL.md` records the approved R6.1
  contract and implementation evidence and is included in the published
  checkpoint. The new GET is authenticated, owned, Decimal-safe,
  and read-only; the legacy Goals DTO, Planning POST contracts, engines,
  persistence, and locked ADRs are unchanged.
- `GOAL_PROGRESS_READ_MODEL_CONTRACT.md` governs R6.2. The read model uses only
  owned cadastral Goal amounts, preserves signed gap, null versus explicit zero,
  and completion above 100%, and does not claim automatic portfolio progress.
- `GOAL_MONITORING_OVERVIEW_READ_MODEL_CONTRACT.md` governs R6.3. Its
  authenticated batch read reuses R6.2 per Goal, classifies mutually exclusive
  progress states, exposes factual data flags, and summarizes counts only. It
  performs no monetary aggregation, MyProfit/portfolio read, engine call, write,
  migration, or frontend change.
- `GOAL_BATCH_CONTRIBUTION_PREVIEW_CONTRACT.md` governs R6.4. Its bounded,
  ordered request loads selected Goals once under ownership, uses only
  `GOAL_CURRENT_AMOUNT`, and delegates each calculable item to the certified
  Required Contribution solver. It does not infer a horizon from Goal dates,
  aggregate Goal wealth, persist a simulation, or read MyProfit/portfolio data.
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
  performance engine, rebalancing engine, watchlist, news integration,
  Docker deployment, or operational AI runtime. BCB/SGS provider and internal
  reference foundations do exist; a Market product consumer is not activated.

Historical phase-by-phase execution evidence remains in `CHANGELOG.md`,
`TESTING_STRATEGY.md`, accepted ADRs, and locked contracts. It is intentionally
not duplicated in this current-state summary.
