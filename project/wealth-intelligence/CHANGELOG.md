# Changelog — FINANALYTICS Wealth Intelligence

## [TSK-R6.1] — 2026-10-26 — Goals → Planning Context and Presets

- Added authenticated `GET /api/v1/planning/goals/{goal_id}/context` over the
  existing owned Goal reader. The eight-field response preserves Decimal money
  as strings, distinguishes null from explicit zero, returns non-enumerating
  `404` for missing/wrong-owner Goals, and performs no write, Engine, portfolio,
  MyProfit, simulation, or Goal mutation.
- Added `Simular esta meta` with a UUID-only deep link. Planning validates the
  route, loads the authenticated context, displays localized Goal facts, applies
  only current-amount origin and monthly-contribution presets, and never derives
  horizon or return assumptions.
- Preserved local edits during Goal switching through explicit `Aplicar dados
  desta meta` or `Cancelar` actions, blocks ambiguous submission, ignores stale
  asynchronous responses, and clears Goal-derived state across authentication
  failure, logout, token, or identity changes.
- Kept the global Wealth Intelligence navigation as the single inter-page
  journey and added navigation-only Wealth Home empty actions while preserving
  the in-memory `TransientAnalysisContext` and explicit `Mostrar na Visão Geral`
  flow.
- Applied the accepted minimalist refinement: removed repeated page titles,
  subtitles, and local journey navigation; centered the segmented Objective
  selector; compacted advanced-premise summaries into chips; and retained
  semantic headings, keyboard behavior, responsiveness, and the required
  nominal/real identification.
- Validation before the refinement: focused backend Planning/Goals `240
  passed`, including `13 passed` for the new GET; focused frontend `54 passed`;
  full Vitest `238 passed`; TypeScript, focused ESLint, Next.js production
  build, and `git diff --check` passed. After the refinement: focused frontend
  `27 passed`; full Vitest `238 passed`; TypeScript, focused ESLint, production
  build, and `git diff --check` passed. Historical deprecation warnings and the
  existing Recharts SSR size warning remain unchanged.
- The user subsequently tested the experience and reported it satisfactory for
  the current scope. This is recorded as `R6.1 UX REFINEMENT = USER-ACCEPTED
  FOR CURRENT SCOPE`; it does not claim every viewport, browser, calculation,
  or manual accessibility scenario and does not approve R5 visually.
- Status: R6.1 is `IMPLEMENTED / AUTOMATED GATES PASSED / USER MANUAL
  ACCEPTANCE REPORTED / CHECKPOINT PENDING`. R5 visual acceptance remains
  `PENDING`; the general R6 gate remains blocked and R6.2+ remains unauthorized.
  No staging, commit, or push was performed.

## [TSK-R5-R6-GOVERNANCE-AMENDMENT] — 2026-10-25 — R5 → R6.1 Sequencing Reconciliation

- Recorded the project owner's explicit, bounded amendment to ADR-027's
  sequencing rule. R5 visual acceptance remains `PENDING`; R5 is not closed.
- Confirmed the published R5 technical checkpoint as `COMMITTED / PUSHED` at
  `1fae590fb316b4f9d9584aad23cdde4fe8f3af9b`.
- Preserved the general R6 gate as `BLOCKED PENDING R5 VISUAL ACCEPTANCE` while
  authorizing only R6.1 Goals → Planning as `EXPLICITLY AUTHORIZED / NOT
  IMPLEMENTED`, bounded by the approved
  `PLANNING_GOAL_CONTEXT_READ_MODEL_PROPOSAL.md` microcontract.
- Kept R6.2+, R7, Advisor, and Portfolio Intelligence unauthorized. No later
  increment inherits the R6.1 exception, and any R5 regression remains subject
  to the existing gate and remediation requirements.
- Changed documentation governance only. No endpoint, DTO, mapper, test,
  Goals/Planning behavior, navigation, preset, product code, migration,
  dependency, database, staging, commit, or push action was introduced. The
  microcontract file and ADR-023/024/025 authorities remain unchanged.

## [PHASE-10.R5-IMPLEMENTATION] — 2026-10-24 — Design, Navigation, and Theme

- Recorded the user's explicit approval and implementation start for the
  bounded frontend-only R5 contract. R6, R7, Portfolio Intelligence 10.5-B,
  operational AI/provider work, migrations, deployment, commit, and push remain
  unauthorized.
- Validated R5-0 without recreating the existing routes: `/wealth-intelligence`
  and its Goals, Health, Planning, and FIRE children preserve direct access,
  active navigation, month-aware links, query state, and the tested legacy
  `/goals` redirect.
- Implemented R5-1 System/Light/Dark selection with hydration-safe bootstrap,
  operating-system preference tracking, and appearance-only `fin_theme`
  persistence. Added semantic surface, text, border, status, financial, chart,
  focus, and interaction tokens and migrated the bounded Wealth Intelligence
  shell and shared primitives without persisting financial state.
- Implemented R5-2's ADR-024 hierarchy: `Simular`, `Objetivo`, and `Comparar`
  are the three top-level intentions; `Quando alcanço?`, `Quanto aportar?`, and
  `Meta cadastrada` are nested Objective tasks. All five existing deterministic
  services, conditional forms, results, charts, deep links, and the transient
  “Mostrar na Visão Geral” flow are preserved without automatic calculation.
- Implemented R5-3 stabilization for semantic living states, responsive
  controls, global reduced motion and focus, theme-aware chart axes/series, and
  accessible Goals dialogs with labels, initial/contained/restored focus,
  Escape handling, and mutation-safe dismissal.
- Validation: frontend Vitest `218 passed`; focused backend Wealth
  Home/Goals/Planning/FIRE contracts `219 passed`; TypeScript and focused ESLint
  passed; the 38-route Next.js production build passed; `git diff --check`
  remains the final repository integrity gate. The legacy
  `/wealth/asset/[ticker]` Recharts SSR size warning remains visible and is not
  attributed to an R5 route.
- R5 is `IMPLEMENTED / AUTOMATED GATES PASSED / USER VISUAL ACCEPTANCE
  PENDING`. R6 remains `NOT STARTED`.

## [R4-C-CHECKPOINT-RECONCILIATION] — 2026-10-24

- Verified that `HEAD` and the local `origin/develop` tracking ref both resolve
  to the published R4-C checkpoint
  `14cb65db1cddd5466523eefdca54c78affb3eca7`.
- Reran the exact R4-C plus direct R4-A/R4-B regression selection: `77 passed`.
  R4-C is `CLOSED / PUSHED`; no runtime correction was required.
- Preserved `MAT-R4C-01` as an `INFORMATIONAL / FUTURE ACTIVATION BLOCKER` for
  R4-F pre-execution durable audit and preserved `INF-R4C-01` for future HMAC
  key configuration, rotation, and key-ID governance.
- Added the non-normative checkpoint decision and executable R5 proposal in
  `audits/R4_C_CHECKPOINT_AND_R5_PREPARATION_2026-10-24.md`. R5 remains
  `NOT STARTED` pending explicit authorization.

## [UNRELEASED-W2-W4.2-LOCAL] — 2026-10-24 — Wealth Intelligence Product Increments

- Reconciled the current local W2–W4.2 implementation: authenticated
  `wealth-home-v2`, monthly Health and ADR-023 investment wealth, current owned
  Goals, nested navigation with month propagation, five deterministic Planning
  flows, three explicit FIRE modes, and one navigation-scoped in-memory selected
  result. This is worktree evidence, not a canonical R5/R6/R7 phase closure.
- Corrected Goal progress localization to pt-BR, made Health trend deltas
  directionally factual rather than qualitatively red/green, and updated the
  Wealth Home loading state to cover all governed sources.
- Added the non-normative traceability audit
  `audits/W2_W4_2_RECONCILIATION_2026-10-24.md` and reconciled README, Current
  State, and Roadmap tracking text without changing ADRs or locked contracts.
- Validation: `828` governed backend tests passed; the broader Investments
  selection preserved the two documented MagicMock/timeline failures; frontend
  Vitest passed `206` tests in 24 files; TypeScript, focused ESLint, and the
  38-route Next.js production build passed. The existing Recharts SSR size
  warning remains.
- No financial Engine, migration, Portfolio Intelligence, Advisor integration,
  LLM execution, benchmark, download, deployment, commit, or push occurred.

## [PHASE-10.R4-C] — 2026-10-16 — Audit & Telemetry Boundary

- Added immutable, typed, versioned minimized audit events and typed optional
  telemetry metrics over the existing R4-A/R4-B contracts. Technical user scope
  is HMAC-pseudonymized; prompts, responses, raw financial context, transaction
  descriptions, tool arguments, credentials, headers, and provider messages
  have no event field.
- Added separate replaceable audit/telemetry ports and deterministic volatile
  in-memory sinks. Required audit fails closed on sink failure or insufficient
  guarantee; remote and tool-enabled execution requires durability, so the
  in-memory sink is not accepted as persistent evidence. Optional telemetry
  failure remains explicit and non-critical.
- Focused R4-C validation: `21 passed`; direct R4-A/R4-B regressions: `56
  passed`; combined: `77 passed`. No global suite was run.
- R4-B is `CLOSED / PUSHED` at checkpoint
  `8149e3d27a75c76ed6cc7f46fab60aabebd96396`. R4-C is `INDEPENDENTLY APPROVED
  / CHECKPOINT PENDING` in this time-of-implementation record; the later
  checkpoint reconciliation verifies it `CLOSED / PUSHED` at
  `14cb65db1cddd5466523eefdca54c78affb3eca7`.
- Independent review approved R4-C with `77 passed`, `0 BLOCKING`, and `0
  MATERIAL` active findings. Historical `MAT-R4C-01` is retained and adjudicated
  `INFORMATIONAL / FUTURE ACTIVATION BLOCKER`: a future R4-F orchestration must
  integrate and validate a pre-execution audit guard before operational provider
  or tool dispatch; `VOLATILE` does not substitute for `DURABLE`. `INF-R4C-01`
  remains for future HMAC key configuration/rotation/key-ID governance. The
  current reconciled status is `CLOSED / PUSHED`.
- Audit persistence and definitive retention are `NOT AUTHORIZED`; historical
  `ai_runs` was not reused or modified. Ollama is `NOT INSTALLED`, Gemini was
  `NOT CALLED`, and R4-D and later increments are `NOT IMPLEMENTED`. No database
  access, migration, HTTP call, provider SDK, endpoint, frontend, scheduler,
  commit, or push occurred.

## [PHASE-10.R4-B] — 2026-10-16 — Authorization, Read-Only Tools & Minimal Context

- Added a trusted server-side scope resolver over the existing authenticated
  user DTO and a deny-by-default executor that enforces scope, purpose,
  privacy, exact arguments, request/per-tool call budgets, deadline, local
  timeout, ownership, and safe typed failures.
- Added an immutable exact registry for `read_home_context`,
  `read_planning_context`, `read_goal_context`, `read_fire_context`, and
  `read_owned_goal`. The first four reuse R2 `SmartContextConsumerFoundation`;
  the fifth reuses and revalidates the existing owned Goal reader.
- Added a minimized context builder preserving Decimal strings, zero, source,
  owner/scope, time, freshness, explicit absence, evidence, provenance, and
  completeness while marking retrieved text as untrusted data and omitting
  Goal ownership/account identifiers.
- Focused R4-B validation: `24 passed`; directly related R4-A/R2/Planning
  regressions: `60 passed`; combined: `84 passed`. No global suite was run.
- Independent review approved R4-B with `84 passed`, five read-only tools, and
  `0 BLOCKING / 0 MATERIAL / 0 MINOR` new findings. It is `CLOSED / PUSHED` at
  `8149e3d27a75c76ed6cc7f46fab60aabebd96396`. R3 External Reference,
  provider adapters/calls, Engines, writes, persistence, migrations, endpoints,
  frontend, and scheduler remain absent or deferred; the later checkpoint
  changed Git state only.

## [PHASE-10.R4-A] — 2026-10-15 — Provider-Neutral Contracts

- Added an asynchronous SDK-free `AIProvider` port, immutable request/response,
  provider/model capability and evidence contracts, exact registries with no
  default model, safe typed errors, and strict local output/source validation.
- Added an internal non-routing application service that enforces exact
  provider/model registration, lifecycle, capabilities, privacy, consent,
  execution mode, and deadline before invoking the caller-supplied adapter.
- Added a deterministic no-I/O fake provider for valid output, invalid schema,
  timeout, unavailability, rate limit, cancellation, discovery, health, usage,
  Decimal cost, and resource-closure verification.
- Focused R4-A validation: `32 passed`. Minimal R2 Smart Context and R3 External
  Reference regressions: `39 passed`. No global suite was run.
- R4-A was independently approved and published at
  `bea92edb18872bd3e3603dc10ebc62bed8de8100`; it is `CLOSED / PUSHED`.
  Ollama is not installed, Gemini was not called, and benchmarking was not
  executed.
- No provider SDK installation/import, API-key read/test, network call,
  operational database access, migration, persistence, endpoint, frontend,
  scheduler, commit, or push occurred.

## [PHASE-10.R4.0] — 2026-10-15 — Hybrid AI Runtime Contract Formalization

- Formalized the user-approved D1-D12 provider-neutral runtime contract and its
  four mandatory refinements in the canonical AI architecture and ADR-030.
- Preserved `LOCAL_ONLY` as the default, explicit unavailability without a
  local model, opt-in `HYBRID`, and the separation between Gemini adapter
  integration and authorization to transmit real financial data.
- Planned R4-A through R4-H without authorizing implementation. R4-A remains
  `NOT IMPLEMENTED / NEXT GATE CANDIDATE`; every later increment is separately
  gated.
- Recorded that Ollama is not installed and defined the assisted R4-D.0-D.3
  hardware, installation, model setup, offline, performance, and adapter
  validation checklist. No installation or model download occurred.
- Kept benchmark quality and availability separate, with no model or time-window
  choice before evidence and no execution, provider call, quota, or cost
  authorization.
- Defined the minimized telemetry contract before persistence. Reuse of
  `ai_runs`, retention, schema, database, and migration remain separate gates.
- Documentation only: no code, dependency, API-key test, Gemini call,
  operational database access, endpoint, frontend, scheduler, commit, or push.

## [PHASE-10.R3-I] — 2026-10-15 — Independent Stabilization Documentation Reconciliation

- Recorded R3-F1 independent approval with 0 blocking, 0 material, and 0 minor
  findings and its published checkpoint
  `30c4df058fd80923c37243252f4ee8fc6fa76dce`; current status is `CLOSED /
  PUSHED`.
- Recorded R3-I fresh-context stabilization evidence: `234` transversal tests
  passed, no new code finding, and eight historical informational findings
  preserved.
- R3-I is `INDEPENDENTLY APPROVED / DOCUMENTATION RECONCILED`; it is
  not declared closed or pushed before this documentation is checkpointed.
- This reconciliation changes documentation only. It does not alter locked
  contracts, code, tests, migrations, providers, refresh behavior, runtime
  consumers, R3-G/R3-H activation, or introduce an R3-F2.

## [PHASE-10.R3-F1] — 2026-10-15 — Point-in-time External Reference Read Boundary

- Added the exact three-value `ExternalReferencePurpose` enum and immutable
  purpose-to-Registry-key allowlist approved in R3-F.0.
- Added immutable request/result envelopes and the internal read-only
  `ExternalReferenceContextService`, delegating bitemporal selection and current
  sync-state reads to the certified R3-D/E Store boundary.
- Preserved exact Decimal, canonical text, the selected event and economic
  period, knowledge sequence, and complete available provenance; missing data
  remains explicit and cross-purpose access fails with `PURPOSE_NOT_ALLOWED`
  before Store access.
- Kept deterministic `reference_replay` separate from the non-historical
  `operational_state_snapshot`; no `state_observed_at` is invented. Registry
  mismatch preserves eligible LKG and forces freshness/acquisition health to
  `UNKNOWN`.
- Reused certified state evaluation. `CURRENT` requires complete positive
  coverage plus selected-head evidence; without it freshness is `UNKNOWN`, and
  no new `STALE` rule is invented.
- Validation: `28 passed` focused and `100 passed` for R3-F1 plus minimal
  Registry/Store regressions. At this implementation checkpoint, status was
  `IMPLEMENTED / TESTED / AWAITING INDEPENDENT REVIEW`; no runtime consumer,
  write, provider call, refresh,
  endpoint, frontend, migration, engine, operational database access, commit,
  or push was introduced or executed.

## [PHASE-10.R3-F.0] — 2026-10-14 — Purpose Contract Formalization

- Formalized the user-approved D1-D6 contract for the future internal
  `ExternalReferenceContextService`: a closed three-purpose enum and immutable
  purpose-to-series allowlist for the future Market context composer only.
- Approved point-in-time selection with explicit economic-date and UTC
  knowledge-time cuts, deterministic `knowledge_sequence` replay, exact
  Decimal, full provenance, typed `PURPOSE_NOT_ALLOWED`, and explicit absence.
- Separated deterministic bitemporal `reference_replay` from the current,
  non-historical `operational_state_snapshot`; mutable sync state cannot claim
  historical health, coverage, or freshness.
- Required certified conservative freshness policy (`UNKNOWN` without enough
  evidence) and preservation of the eligible observation's original economic
  period across weekends, holidays, and months without publication.
- Recorded R3-F.0 as `CONTRACT APPROVED / DOCUMENTED` and R3-F1 as
  `NOT IMPLEMENTED`. Registry V1, locked contracts, R3-E4's checkpoint,
  financial engines, and the canonical wealth source remain unchanged.

## [MICROPHASE-FK-REMEDIATION] — 2026-10-13 — Structural Foreign Key Remediation for Position Snapshots

- Implemented a conditional remediation for the SQLite `foreign key mismatch`
  on `position_snapshots` confirmed by the backend traceback. The user later
  confirmed that MyProfit import resumed after a targeted operational hotfix
  removed only the invalid physical FK.
- Created canonical Alembic migration `b7e2d1a4c9f3` (successor of `4f9c2d7e1a6b`)
  using `op.batch_alter_table(..., copy_from=corrected_table, recreate="always")`
  to drop the invalid physical constraint `fk_position_snapshots_account_id` referencing
  non-existent `accounts(id)`. The repair is a no-op on the canonical schema and
  fails closed on unknown columns, foreign keys, inbound foreign keys,
  semantically divergent indexes, triggers, or views. It preserves
  the valid foreign key to `assets(id)`, unique constraint
  `uq_position_snapshot_account_asset_date`, all 4 secondary indexes, and exact
  Decimal precisions.
- Corrected historical provenance: canonical Alembic revision `a1b2c3d4e5f6`
  never declared the invalid account FK; legacy SQL
  `database/migrations/005_open_finance.sql` did, but the exact drift path remains
  unproven.
- Added 12 regression test functions in
  `tests/unit/test_position_snapshots_fk_remediation.py`, expanding to 22 pytest
  cases using isolated disposable SQLite databases. Verified pre-remediation error reproduction,
  100% preservation of 223 synthetic snapshots via SHA256 digest, exact PRAGMA
  structural checks, valid asset FK enforcement, logical `account_id` semantics,
  canonical-schema no-op, fail-closed unknown-shape/orphan handling, explicitly
  blocked downgrade, inbound-FK rejection, semantic index rejection, and
  `ConfirmMyProfitAtivosSyncUseCase` with 30 synthetic assets under
  verified active `foreign_keys=ON`. This is a use-case test, not an HTTP test.
- Earlier review findings were remediated: the `aiosqlite` listener no longer incorrectly
  filters out the adapted DBAPI connection; the deployment plan now acknowledges
  SQLite non-transactional DDL; incident evidence is no longer overstated; and
  migration provenance is accurately bounded. Final continuity review then
  identified missing inbound-FK detection and name-only secondary-index checks;
  both are now implemented with pre-DDL adversarial coverage.
- Fresh targeted validation: new adversarial selection `12 passed`; remediation
  `22 passed`; remediation plus pertinent External Context migration `27 passed`.
  Historical complete units remain `1175 passed, 2 failed`; they were not rerun.
- A disposable empty-database probe exposed pre-existing Alembic bootstrap debt:
  the two historical roots both create `categories`, so `upgrade head` from empty
  fails before this revision. This remediation does not claim or alter that
  repository-wide bootstrap path.
- This reconciliation did not access or modify the operational database. The
  separately applied operational hotfix was user-validated, while operational
  Alembic remains at `2d6b4f8a9c1e`; repository deployment remains blocked
  pending independent delta review and intermediate revision alignment.

## [PHASE-10.R3-E4] — 2026-10-13 — Governed Manual Refresh

- Added an explicit internal-only `ManualExternalRefreshService`; no API route,
  CLI, screen, scheduler, startup hook, deployment, or automatic acquisition
  was introduced. The locked R3-E4 surface remains an application service.
- Added immutable manual request, eligibility, and result types. Requests accept
  only a Registry V1 key, acquisition/correlation identity, and the existing
  R3-E3 ordinary-refresh or explicit bounded historical-reconciliation intent;
  arbitrary SGS IDs, URLs, provider settings, table names, ingestion modes, and
  unrestricted force flags remain impossible.
- Added a pure UTC eligibility decision over registry definition plus certified
  sync state. DAILY uses the existing six-hour call-suppression policy and
  MONTHLY uses twenty-four hours. Missing state permits only the ordinary or
  explicitly bounded request already represented by R3-E3; it creates no row
  and authorizes no full-history fallback.
- Eligibility reuses persisted `next_refresh_eligible_at`. `SUCCESS` and `EMPTY`
  obey their finalized cooldown; `PARTIAL` and `FAILED` preserve the prior
  successful boundary and may retry immediately only when the certified state
  has no retry boundary. Clock regression, registry-version mismatch, and sync
  identity mismatch fail closed without provider or store mutation.
- The sync-state reader is a short-lived read-only boundary over R3-E1
  `get_sync_state(...)` and releases its read transaction before provider I/O.
  Eligible requests delegate once to R3-E3, which remains the sole owner of
  provider acquisition, deferred persistence, finalization, coverage, LKG, and
  counters. Manual results preserve `SUCCESS`, `EMPTY`, `PARTIAL`, and `FAILED`;
  cooldown denial is the separate `NOT_ELIGIBLE` outcome.
- Added `30` focused R3-E4 tests using fake providers and disposable migrated
  SQLite only. They cover all five series, exact 6h/24h boundaries, UTC and
  clock regression, absent/mismatched state, failure retry semantics, request
  validation, all four finalized results, no-write cooldown, correlation,
  provider/finalization errors, single finalization, safe telemetry, sequential
  calls, and concurrent calls.
- Current validation: R3-E4 `30 passed`; combined R3-E4/R3-E3/store/policy `120
  passed`; R3-E2 `70 passed`; R3-C `127 passed`; R3-D/R3-E1 `61 passed`;
  bootstrap `8 passed`; FIRE/Goals/Planning `629 passed`; R2 Smart Context `153
  passed`; complete units `1165 passed, 2 failed`. The two failures are the
  unchanged Investments/MagicMock timeline baseline. Runtime versions were
  Python 3.14.0, SQLite 3.50.4, and SQLAlchemy 2.0.51.
- Concurrent eligible triggers may still duplicate external calls because V1
  has no persistent acquisition journal or distributed single-flight. R3-E1
  serialization/finalization preserved one correct sync state in the exercised
  race; no exactly-once claim is made. This remains the inherited
  `INF-R3E1-02` limitation, not a new closed finding.
- Gemini 3.8 Flash High independently approved the adversarial R3-E4 review:
  0 blocking, 0 material, 0 minor, 1 new informational finding, and 7 preserved
  informational findings. `INF-R3E4-01` is open: if a future authenticated
  caller exposes the existing typed `HISTORICAL_RECONCILIATION` intent, it must
  enforce specific administrative authorization, validate intent and interval,
  deny anonymous access, and not provide an uncontracted cooldown bypass. This
  phase remains internal-only and adds no endpoint or RBAC mechanism. The seven
  preserved findings are `INF-R3D-01/02`, `INF-R3E1-01/02/03`, and
  `INF-R3E2-01/02`.
- OpenAPI remains 55 paths and 59 operations with no External Context refresh
  route. No live BCB request, active-database access, migration, dependency,
  frontend, financial-engine, locked-contract, R3-E1, R3-E2, or R3-E3 change
  was made. R3-E4 is `IMPLEMENTED / TESTED / INDEPENDENTLY APPROVED /
  IMPLEMENTATION CHECKPOINT`.

## [PHASE-10.R3-E3] — 2026-10-13 — Governed Ingestion & Sync State Integration

- Added an internal application-layer governed-ingestion service that composes
  the closed/pushed R3-E2 provider port with the closed/pushed R3-E1 store
  service. The request requires an explicit acquisition identity,
  registry-owned series key, and ordinary-refresh or bounded
  historical-reconciliation intent.
- Implemented the locked ordinary revision windows: DAILY uses the inclusive
  interval `max(registry floor, D - 89 days)..D`; MONTHLY uses the inclusive 24
  civil-month interval from the first day 23 months before `D` through `D`.
- Enforced provider-complete-before-persistence ordering. Certified successful
  observations are written only through R3-E1 deferred ingestion; empty,
  failed, incomplete, and persistence-failed chunks become typed acquisition
  evidence; one final R3-E1 call derives and commits the global sync outcome.
- Kept external provider status separate from the committed global store
  result. The service preserves R3-C registry validation, exact Decimal values,
  fingerprint identity, UTC evidence, immutable history, event counters, LKG,
  and R3-E1's conservative coverage policy.
- Added `34` focused tests using only `httpx.MockTransport` and disposable
  migrated SQLite. Regressions pass for R3-C `127`, R3-D/R3-E1 `61`, R3-E2
  `70`, bootstrap `8`, FIRE/Goals/Planning `629`, and the selected current R2
  Smart Context suite `153`. Complete units report `1135 passed, 2 failed`,
  limited to the unchanged Investments/MagicMock baseline; the R3-E3 plus
  R3-D/R3-E1 selection also reports `95 passed` on SQLAlchemy 2.0.21.
- Gemini 3.8 Flash High independently approved the adversarial R3-E3 review:
  0 blocking, 0 material, 0 minor, 0 new informational findings, and 7
  preserved informational findings (`INF-R3D-01/02`, `INF-R3E1-01/02/03`, and
  `INF-R3E2-01/02`). It reproduced the listed gates on Python 3.14.0, SQLite
  3.50.4, and SQLAlchemy 2.0.51; the isolated SQLAlchemy 2.0.21 `95 passed`
  result remains implementation evidence, not an independent-review claim.
- No live BCB request, active-database access, migration, dependency, scheduler,
  startup acquisition, endpoint, frontend, financial-engine, locked-contract,
  R3-E1, or R3-E2 change was made. The controlled checkpoint was published as
  `686d64b49731a44a56e0d7fd8b44752ee1b663d8`; R3-E3 is `CLOSED / PUSHED`, and
  R3-E4 is `AUTHORIZED / NOT IMPLEMENTED`.

## [PHASE-10.R3-E2] — 2026-10-12 — Contract-Aligned BCB/SGS Provider Foundation

- Added a typed, persistence-free external-observation provider port with
  immutable interval, per-chunk, aggregate-result, status, and safe-error
  types. Provider `PARTIAL` remains external acquisition evidence and cannot
  assert persisted sync success.
- Added a fixed official BCB/SGS `httpx` client that executes one request per
  call, derives the five allowed SGS IDs and metadata from Registry V1, keeps
  TLS enabled and redirects disabled, and applies explicit timeout, retry,
  `Retry-After`, elapsed-budget, response-byte, and record limits.
- Added deterministic provider-owned DAILY partitioning using inclusive civil
  intervals of at most ten years, with conservative 29-February handling,
  exact gap-free/non-overlapping coverage, and no redundant boundary calls.
  MONTHLY SGS 433 remains one explicitly bounded request and normalizes each
  returned economic month to its first and last civil day.
- Added the BCB/SGS adapter for sequential bounded multichunk execution, strict
  JSON/schema/date/textual-Decimal validation, atomic chunk rejection,
  deterministic ordering, identical-duplicate collapse, conflicting-duplicate
  rejection, and canonical R3-C normalization with per-response UTC
  `retrieved_at`.
- Added `70` focused mocked-transport tests. Current regressions are R3-C `127
  passed`, R3-D/R3-E1 `61 passed`, bootstrap `8 passed`, and complete units
  `1101 passed, 2 failed`; the two failures are the unchanged
  Investments/MagicMock timeline baseline.
- No live HTTP, SQLite persistence, active-database access, migration,
  scheduler, startup acquisition, endpoint, frontend, dependency, locked
  contract, R3-E1 store, Pierre, or financial-engine change was made.
- Gemini 3.8 Flash High independently approved the adversarial R3-E2 review:
  0 blocking, 0 material, 0 minor, 2 new informational findings, and 5
  preserved findings. `INF-R3E2-01` is aggregate in-memory observation
  accumulation; `INF-R3E2-02` is future-test dependence on `MockTransport` or
  equivalent injection. `INF-R3D-01`, `INF-R3D-02`, and `INF-R3E1-01` through
  `INF-R3E1-03` remain unresolved.
- R3-E2 is `IMPLEMENTED / TESTED / INDEPENDENTLY APPROVED / CHECKPOINT
  AUTHORIZED`. R3-E3 governed ingestion and R3-E4 manual refresh remain `NOT
  STARTED`.

## [PHASE-10.R3-E1] — 2026-10-12 — Store Compatibility Adapter

- Extended the existing `ExternalObservationStoreService` with a typed
  default-compatible `immediate` mode and an opt-in `deferred` mode. Immediate
  ingestion preserves the complete R3-D success, refresh, coverage, event,
  fingerprint, registry-version, and UTC behavior.
- Deferred ingestion reuses the certified R3-C/R3-D event transaction and may
  update immutable history, supersession, sequence, LKG, and existing event
  counters without publishing global success, advancing successful refresh,
  clearing partial state, or expanding coverage from economic extrema.
- Added a strictly read-only `get_sync_state(...)` and typed
  `finalize_acquisition(...)` evidence/result DTOs. Finalization validates an
  exact ordered gap-free chunk partition, derives rather than trusts the global
  result, rejects stale/conflicting conclusions, leaves event counters and LKG
  unchanged, and publishes `SUCCESS`, `EMPTY`, `PARTIAL`, or `FAILED` under
  `BEGIN IMMEDIATE`.
- Adopted the R3-E.0-permitted conservative scalar-coverage policy: a complete
  `SUCCESS`/`EMPTY` replaces the two coverage fields with the newly certified
  continuous requested interval; it is never unioned with legacy or
  disconnected evidence. `PARTIAL`/`FAILED` preserve prior coverage without
  expansion, and valid empty chunks create no economic observation or zero.
- Added regression and integration coverage for legacy immediate calls,
  deferred transition/retransmission/A→B→A behavior, crash-before-finalization,
  counters, LKG, sequence, fingerprint, registry mismatch, read-only lookup,
  all four outcomes, invalid/gapped evidence, stale and repeated finalization,
  rollback, and independent SQLite writers.
- Validation on disposable SQLite only: R3-D/R3-E1 `61 passed`; R3-C `127
  passed`; bootstrap `8 passed`; SQLAlchemy 2.0.21 combined R3-C/R3-D/R3-E1
  `188 passed`; R2/bootstrap `161 passed`; Planning `503 passed`; FIRE `71
  passed`; complete units `1031 passed, 2 failed`, limited to the unchanged
  Investments/MagicMock timeline failures.
- Gemini 3.8 Flash High independently reproduced the approved evidence and
  approved the adversarial code review with 0 blocking, 0 material, 0 minor,
  and 3 informational findings: `INF-R3E1-01` scalar durable coverage,
  `INF-R3E1-02` no persistent journal/distributed idempotency, and
  `INF-R3E1-03` the unchanged Investments/MagicMock baseline. `INF-R3D-01` and
  `INF-R3D-02` remain preserved, not resolved.
- No provider, HTTP/BCB request, scheduler, migration, dependency, public API,
  frontend, financial engine, or active-database access was added. The user
  authorized the controlled Git checkpoint. R3-E1 is `IMPLEMENTED / VALIDATED /
  INDEPENDENTLY APPROVED / CHECKPOINT AUTHORIZED`; R3-E2 is `READY / NOT
  STARTED`; R3-E3 and R3-E4 remain `NOT STARTED`.

## [PHASE-10.R3-E.0] — 2026-10-11/12 — Historical Revision Windows & Deferred Ingestion Finalization V1

- Recorded the user's explicit approval of the R3-E.0 material decisions as a
  controlled documentation-only amendment to accepted/locked ADR-029.
- Locked the ordinary DAILY inclusive revisit window to 90 civil days using
  explicit stable `D`, bounded by the registry normalized floor, including the
  unchanged SGS 1 floor `1994-07-01`.
- Locked the ordinary MONTHLY inclusive revisit window to the current civil
  month of `D` plus the 23 preceding civil months, using calendar-month
  subtraction and the normalized floor. Missing, weekend, holiday, current-
  month, or unpublished periods receive no manufactured observation.
- Kept revision windows separate from 6h/24h call suppression and from
  consumer `as_of` economic/knowledge cuts. Revisions outside the windows are
  not presumed discovered.
- Contracted explicit bounded manual deep reconciliation only: registry series,
  start/end dates, reconciliation intent, governed chunks, R3-C certification,
  and R3-D persistence. No startup backfill, scheduler, silent whole-history
  fallback, public endpoint, screen, or reconciliation run is authorized.
- Defined first acquisition conservatively: an ordinary first request may use
  its moving window; missing history never authorizes automatic full backfill,
  and first-request success never proves complete historical coverage.
- Approved only the future minimal same-service R3-D responsibilities
  `get_sync_state(...)` and `finalize_acquisition(...)`, following existing
  backend types with no parallel store, third table, or migration.
- Distinguished requested interval, fully received and validated queried
  chunks, and observed economic periods. Current `coverage_start`/
  `coverage_end` cannot bridge a failed chunk or claim an observation for every
  intermediate date.
- Defined EMPTY, PARTIAL, FAILED, and interrupted-before-finalization behavior;
  preserved valid committed observations, prior certified coverage, and LKG;
  prohibited false continuous coverage, `AVAILABLE`, `CURRENT`, zero, and
  global `SUCCESS` before finalization.
- Preserved atomicity per R3-D transaction without promising global atomicity
  across chunks. If the approved minimal extension cannot keep intermediate
  chunk success conservative after a crash, implementation must stop for a
  material contract decision before adding another mechanism.
- Preserved the five-series registry, Registry Contract Version V1,
  `EXTERNAL_SERIES_REGISTRY_VERSION = 1`, Content Fingerprint V1, UTC V1,
  immutable history, `A -> B -> A`, financial-authority boundaries, and both
  R3-D informational findings.
- Gemini 3.8 Flash High approved the targeted remediation review with 0
  blocking, 0 material, 0 minor, and 2 informational findings. It resolved
  `MAT-R3E0-01`, `MIN-R3E0-01`, `MIN-R3E0-02`, and `INF-R3E0-01`; the latter
  remains governed by the conservative-coverage contract. `INF-R3E0-02`
  (scalar discontinuous coverage) and `INF-R3E0-03` (no persistent acquisition
  journal) remain explicit V1 risks. `INF-R3D-01` and `INF-R3D-02` remain
  preserved R3-D findings.
- Preserved conventional `ingest()` as default `immediate` behavior and
  authorized an explicit typed `deferred` mode that commits certified events,
  LKG, and existing event counters without publishing global success, moving
  successful refresh eligibility, clearing partial state, or expanding
  coverage from observation extrema.
- Made `finalize_acquisition(...)` the exclusive global-result publisher for
  `SUCCESS`, `EMPTY`, `PARTIAL`, and `FAILED`; it consumes typed chunk proof,
  preserves already-counted event counters, rejects stale/regressive outcomes,
  and inserts no observations.
- Made `get_sync_state(registry_key)` strictly read-only, with `None` for no
  persisted row and no call to sync-state initialization.
- Locked conservative durable coverage: only a complete, gap-free, globally
  finalized interval may be promoted; PARTIAL/FAILED never enlarge it;
  disconnected chunks are never unioned; valid empty chunks prove queried
  continuity without creating an economic observation; legacy extrema-based
  coverage is not retroactively reinterpreted.
- Recorded crash/retry limits: committed chunk events, counters, and LKG
  survive a pre-finalization crash with no new global success or coverage;
  finalization retries are counter-idempotent; V1 has no durable attempt
  journal, `STARTED` state, persistent idempotency key, or exactly-once claim.
- Updated the R3-E plan into Store Compatibility Adapter, BCB Provider,
  Governed Ingestion, and Manual Refresh, plus 32 future remediation tests with
  mocked HTTP and disposable SQLite. Timeout, exact retries/backoff, response
  caps, call rate, workers, and automatic execution remain undecided.
- Status at the R3-E.0 checkpoint: R3-C `CLOSED / LOCKED`; R3-D.1
  `APPROVED / LOCKED / VERSIONED`; R3-D `CLOSED / PUSHED`; R3-E.0
  `CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED / VERSIONED / PUSHED`;
  R3-E `READY / NOT STARTED`;
  R3-F `PLANNED / NOT STARTED`.
- Next gate: controlled Git checkpoint, then separately authorized R3-E implementation.
- Documentation only. No Python, executable test, migration, dependency,
  active-database access, HTTP/BCB call, provider, scheduler, public API,
  frontend, engine, Pierre, staging, commit, or push action was performed.

## [PHASE-10.R3-D] — 2026-10-10 — Governed Observation Store Implementation

- Implemented executable Registry Version V1 and a strict 27-character UTC
  persistence codec without changing the five-series registry or Content
  Fingerprint V1.
- Added the two approved Alembic-owned structures only:
  `external_observation_versions` and `external_series_sync_state`, with exact
  Decimal/UTC text, identity/sequence constraints, self/sync FKs, head/as-of
  indexes, and defensive append-only update/delete triggers. Revision
  `4f9c2d7e1a6b` descends from `2d6b4f8a9c1e` and passed disposable
  upgrade/downgrade/re-upgrade validation.
- Added caller-transactional Core repositories and an application-owned unit of
  work that emits real `BEGIN IMMEDIATE` before head reads, captures one
  injected logical time after reservation, commits event plus sync state
  atomically, retries only bounded busy failures, and treats ambiguous commit
  outcomes conservatively without blind replay.
- Implemented certified R3-C revalidation before writes and after reads,
  fingerprint comparison, head-only retransmission deduplication, immutable
  A→B→A history, per-identity knowledge sequence, supersession, explicit
  two-cut as-of reads, no-look-ahead, and the approved logical retroactivity
  window between `known_from` and physical commit.
- Implemented safe sync-state initialization, last-known-good preservation,
  empty/partial/failed attempt state, independent availability/economic
  freshness/acquisition health, conservative registry mismatch, and 6h/24h
  operational refresh evaluation without provider, scheduler, or endpoint.
- Focused R3-C/R3-D/bootstrap validation: `180 passed`. R2/bootstrap:
  `161 passed` (the prior 160 plus the new runtime FK check); Planning:
  `497 passed`; FIRE: `67 passed`; complete units: `1015 passed, 2 failed`,
  limited to the two unchanged Investments/MagicMock timeline failures.
  Backend import/OpenAPI remains 55 paths, 59 operations, and zero External
  Context endpoints; import created no database file.
- All SQLite migrations/tests used disposable databases under `C:\tmp`; the
  active `database/fin_analytics.db` was neither opened nor migrated. No HTTP
  provider, BCB call, scheduler, frontend, financial engine, portfolio source,
  public API, dependency, commit, or push was added.
- Gemini 3.8 Flash High independently approved R3-D: 0 blocking, 0 material,
  0 minor, and 2 informational findings. SQLAlchemy 2.0.21 independently
  reproduced R3-D `45 passed` and R3-C `127 passed`; SQLAlchemy 2.0.51
  reproduced R3-D `45 passed`, R3-C `127 passed`, and bootstrap `8 passed`.
  R3-D is `IMPLEMENTED / VALIDATED / INDEPENDENTLY APPROVED / CHECKPOINT
  AUTHORIZED`; R3-E is `READY / NOT STARTED`.
- `INF-R3D-01`: SQLite foreign keys are enabled globally for sync and async
  connections and work in validated environments, but deployment remains
  separately gated by legacy referential-integrity assessment, backup/rollback,
  startup validation, and explicit authorization. The active database was not
  inspected or migrated.
- `INF-R3D-02`: the declared Pydantic pins are incompatible in a clean install,
  and `pytest-asyncio` is required by existing tests but not declared. This
  remains a separate `DEPENDENCY REPRODUCIBILITY & PACKAGING REMEDIATION` task;
  requirements and installed project dependencies were not changed.

## [PHASE-10.R3-D.1] — 2026-10-10 — Final Registry Version & UTC Knowledge-Time Checkpoint

- Recorded the user's explicit approval of the two material R3-D preflight
  decisions without reopening the ten original ADR-029 decisions. ADR-029
  remains `ACCEPTED / LOCKED`; R3-B.2 and Content Fingerprint V1 remain intact.
- Defined normative `EXTERNAL_SERIES_REGISTRY_VERSION = 1`, strict positive
  integer/no-bool rules, immutable V1 evolution policy, and independence from
  fingerprint, Alembic, application, and deployment versions.
- Required future `registry_contract_version INTEGER NOT NULL` persistence in
  observation versions and sync state, immutable historical event versions,
  certified-acquisition/reconciliation-only sync updates, explicit mismatch
  `UNKNOWN` states, last-known-good preservation, and registry-version-aware
  cache identity.
- Confirmed that registry version is outside the eleven-field fingerprint
  payload, prefix, canonical JSON, SHA-256 input/digest, and economic identity;
  head-only deduplication and `A -> B -> A` are unchanged.
- Defined canonical persisted UTC text as exactly
  `YYYY-MM-DDTHH:MM:SS.ffffffZ` in 27 ASCII characters, plus a strict future
  Python/SQLite codec with byte-identical validation and typed integrity
  failure. Economic civil dates remain separate.
- Defined `retrieved_at` as R3-E acquisition provenance and
  `ingested_at = known_from = transaction_time_utc` as the single injected
  logical time captured per R3-D transaction attempt after the SQLite write
  reservation. Clock regressions fail without clamping or silent repair.
- Locked the future order around `BEGIN IMMEDIATE`, head read, one clock
  capture, deduplication/sequence, atomic event plus sync update, and one commit;
  repositories neither own the clock nor commit. Retry rereads the head and
  receives a new explicit timestamp.
- Explicitly documented SQLite's limitation: `known_from` is governed logical
  knowledge time, not physical commit completion or first visibility. Replay
  can be logically retrospective inside the transaction window; no physical
  microsecond-perfect claim is made.
- Added future R3-D normative tests for registry version, mismatch, UTC codec,
  bitemporal cuts, per-identity sequence, rollback, concurrency, two-connection
  `BEGIN IMMEDIATE`, logical retroactivity, and compatibility with declared
  `SQLAlchemy==2.0.21` plus locally observed `2.0.51`.
- Recorded `PHASE 10.R3-D.1 — INDEPENDENT CONTRACT DELTA REVIEW APPROVED`:
  Gemini 3.8 Flash High audited eight documentation files and the reviewed
  657-insertion/48-removal delta, reporting 0 blocking, 0 material, 0 minor,
  and 2 informational findings. Registry V1, UTC Persistence V1, the physical
  commit limitation, ADR-029, R3-B.2, Content Fingerprint V1, and the five SGS
  series were preserved. No runtime test was run by the documentary review.
- Carried the two informational implementation obligations forward: prove actual
  `BEGIN IMMEDIATE` before head read with independent SQLite connections and no
  sequence race; initialize sync state with the registry version without
  fabricating successful-acquisition evidence.
- Updated the R3-D/E/F responsibility split and current roadmap state. R3-D.1
  is `CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED / VERSIONED`; R3-D is
  `READY / NOT STARTED` and still needs its own authorized implementation task.
- Documentation only: no Python, executable test, migration, table, database,
  dependency, provider, API, frontend, scheduler, or engine behavior changed.

## [PHASE-10.R3-C] — 2026-10-10 — Domain, normalization, and executable registry

- Added the pure immutable `backend.domains.external_context` domain with typed
  observation/content/provenance/economic-identity models, independent
  availability/freshness/acquisition-health enums, and structured domain
  errors. No clock value is generated implicitly.
- Added the immutable executable allowlist for exactly SGS 432, 11, 12, 433,
  and reference-only SGS 1, preserving official concept, provider identity,
  frequency, unit, scope, currency, precision, historical bounds, eligibility,
  source URL, attribution, and license metadata. SGS 1 enforces the
  `1994-07-01` normalized floor and is not renamed PTAX.
- Added strict ASCII lexical Decimal parsing directly to `Decimal`, fixed-scale
  canonical text without rounding, trailing-zero fill, negative-zero
  normalization, global representation limits, registry-scale enforcement,
  and context-independent digit preservation.
- Added deterministic daily/monthly civil-period validation, including leap
  years, month ends, inverted/incompatible periods, official coverage limits,
  and the SGS 1 real-era floor.
- Implemented the locked Content Fingerprint V1 boundary: exact eleven-field
  payload, registry validation before hashing, compact sorted UTF-8 JSON,
  53-byte NUL-terminated domain prefix, SHA-256, lowercase output, and separate
  version `1`. All three normative hashes reproduce exactly.
- Added `127` focused R3-C tests covering registry, immutability, Decimal,
  periods, identity, provenance, prefix/JSON/hash vectors, complementary cases,
  strict rejection including Python booleans as integers, and `A -> B -> A`.
  Implementation validation recorded `159` R2/bootstrap regressions; independent
  review confirmed `160` R2 regressions, Planning `497`, and FIRE `67`.
  Complete units report `969 passed, 2 failed`, limited to the unchanged
  historical Investments/MagicMock timeline failures.
- Backend import and OpenAPI smoke passed against an explicit disposable
  database URL without creating a database: 55 paths, five unchanged Planning
  paths, one unchanged FIRE path, and no External Context public path.
- Independent implementation review with Gemini 3.8 Flash High returned 0
  blocking, 0 material, 0 minor, and 2 informational findings; it distinguished
  55 OpenAPI paths from 59 HTTP operations and approved all three normative
  SHA-256 vectors.
- `INF-01` requires future R3-D repositories/services to use certified
  registry-validation paths rather than treating directly constructed value
  objects as automatically registry-valid. `INF-02` preserves the separate
  OpenAPI path and operation counts. Neither finding changes R3-C code.
- Added no database access, migration, provider/network call, dependency,
  scheduler, API, frontend, engine, Investments, or locked-contract change.
  `R3-C = IMPLEMENTED / VALIDATED / INDEPENDENTLY APPROVED / CLOSED`; R3-D is
  `READY / NOT STARTED`.

## [PHASE-10.R3-B.2] — 2026-10-10 — Content Fingerprint V1 contract amendment lock

- Recorded the user's explicit approval of the controlled ADR-029 amendment
  without reopening the ten previously accepted R3-B decisions. ADR-029 remains
  `ACCEPTED / LOCKED`.
- Fixed `content_fingerprint_version = 1`, the closed eleven-field payload,
  registry-first validation and normalization, deterministic compact sorted-key
  UTF-8 JSON, the NUL-terminated V1 domain prefix, SHA-256, lowercase output,
  and version/fingerprint pair comparison.
- Added the three complete normative Selic, negative-IPCA, and USD vectors and
  independently reproduced all three expected hashes. Separated coherent valid
  complementary vectors from structured registry/domain rejection cases.
- Independent delta review approved the amendment with 0 blocking, 0 material,
  0 minor, and 2 informational findings; it confirmed the V1 binary prefix,
  eleven-field payload, ADR-029 preservation, financial-authority boundaries,
  and absence of code-file changes.
- Preserved content versus event identity, head-only consecutive
  deduplication, `A -> B -> A`, and the absence of a global fingerprint unique
  constraint. R3-C owns calculation/tests; R3-D retains persistence,
  concurrency, knowledge time, predecessor, and replay.
- Added no code, test implementation, migration, database mutation, dependency,
  provider, API, frontend, engine, or registry change. R3-B.2 is
  `APPROVED / INDEPENDENTLY VERIFIED / LOCKED`; R3-C is
  `READY / NOT STARTED`.

## [PHASE-10.R3-B-LOCK] — 2026-10-09 — External Context contract lock

- Recorded explicit user approval of all ten R3-B material decisions after the
  independent R3-B.1 review returned 0 blocking, 0 material, and 0 minor
  findings. Promoted ADR-029, the External Context contract, official series
  registry, and implementation plan to `ACCEPTED/APPROVED / LOCKED`.
- Locked the five-series BCB-only MVP, Focus deferral, two-structure bitemporal
  store, canonical SQLite decimal text, `A -> B -> A` event history, orthogonal
  availability/freshness/acquisition states, 6h/24h refresh policy, and
  R3-C/D/E/F/I execution path. R3-G remains separately gated and R3-H remains
  deferred/not implemented.
- Added R3-D future test gates for ingestion concurrency, atomic sequence
  allocation, simultaneous deduplication/conflict handling, rollback, replay,
  and exact TEXT-to-Decimal persistence. No runtime behavior was implemented.
- Preserved the user-updated root `ESPECIFICACAO_PRODUTO_METAS.md` as aligned
  personal product vision, subordinate to canonical plans, contracts, and ADRs.
- R3-C is `READY / NOT STARTED`. No code, migration, database, dependency,
  provider, frontend, API, engine, R4, R5, R6, or Portfolio change was made.

---

## [PHASE-10.R3-B.1] — 2026-10-09 — External Context contract remediation (pre-lock record)

- Replaced the draft `NUMERIC(38,18)` SQLite exactness assumption with a
  proposed canonical fixed-scale `TEXT` representation, registry-owned scales,
  explicit Python `Decimal` conversion, no rounding, and an explicit ban on
  SQL lexical ordering/casts/arithmetic as numeric authority.
- Separated economic identity, content identity, and committed knowledge-event
  identity. The revised model preserves `A -> B -> A` as three events while
  deduplicating only consecutive identical retransmissions.
- Separated operational refresh age, economic freshness, acquisition health,
  and availability. Provider failure no longer forces an eligible
  last-known-good observation to `STALE`; insufficient evidence remains
  `UNKNOWN` with a structured cause.
- Clarified that R3-C/D/E/F/I form the proposed BCB-only closure path, R3-G
  requires separate legacy-impact approval and is mandatory only before
  yfinance admission, and R3-H remains deferred and not implemented.
- Added no code, migration, database mutation, dependency, provider, API,
  frontend, engine, or runtime behavior. At this pre-lock checkpoint R3-B and
  proposed ADR-029 remained unlocked; the lock entry above supersedes that
  then-current status.

---

## [PHASE-10.R3-B] — 2026-10-08 — External Context contract and series registry draft (historical)

- Added a documentation-only External Context contract, five-series official
  BCB/SGS registry, and implementation plan with immutable Decimal observations,
  economic/knowledge time, revision history, availability/freshness, governed
  cache, typed provider failures, and purpose-limited reference context.
- Proposed ADR-029 without accepting it. Material choices—including the SGS
  MVP, Focus deferral, persistent bitemporal store, `NUMERIC(38,18)`, refresh
  policies, and revised microphase order—remained pending explicit approval.
  The `NUMERIC(38,18)` proposal is superseded by the R3-B.1 remediation above.
- Revalidated SGS 432, 11, 12, 433, and 1 against official metadata. Corrected
  the proposed daily CDI identity to SGS 12; historical SGS 4389 guidance is not
  used as an alias. SGS 1 remains reference-only and is not labeled PTAX or used
  for portfolio valuation.
- Added no code, migration, database mutation, dependency, provider, API,
  frontend, engine, AI, R4, or R6 behavior. `10.R3-B = CONTRACT DRAFT COMPLETE /
  READY FOR APPROVAL` was the historical status; the lock entry above
  supersedes it. R3 implementation remains not started.

---

## [PHASE-10.R2-CLOSURE] — 2026-10-08 — Smart Financial Context closure

- Closed B1–B7 after B8 independent validation and MR2 independent approval;
  no blocking or material findings remain in the R2 foundation.
- Recorded MR1 diagnosis and MR2 removal of runtime schema bootstrap: Alembic
  is the schema authority, configured database URLs are authoritative, and
  pytest refuses the active database while using isolated storage.
- Recorded MR3 operational reconciliation of the already-equivalent active
  Smart Context schema to revision `2d6b4f8a9c1e`. `upgrade head` was a no-op,
  SQLite integrity remained `ok`, and schema plus financial data were
  preserved with validated pre/post backups.
- Final focused database-bootstrap, migration, and B7 regression returned
  `19 passed`. B8 evidence remains `153` Smart Context, `497` Planning, `67`
  FIRE, `133` Goals/Health, and `121` frontend tests; MR2 complete units remain
  `842 passed, 2` unchanged historical Investments failures.
- `10.R2 = IMPLEMENTED / VALIDATED / CLOSED`; `10.R3 = READY / NOT STARTED`.
  R6 retains product recomposition and smart-prefill ownership.

---

## [PHASE-10.R2-MR2] — 2026-10-07 — Runtime schema-authority remediation

- Removed application-import `create_all`; runtime and startup are now DDL-inert
  and Alembic remains the explicit schema authority.
- Derived synchronous and asynchronous SQLite engines from the canonical
  configured `DATABASE_URL`; Alembic reuses the same typed normalization.
- Added repository-wide pytest database isolation, fail-closed active-database
  refusal, and fresh-process import/configuration regression coverage. Removed
  the remaining metadata creation from the account seed utility.
- Validated copy-only old-defect reproduction, stamp/no-op upgrade, migration
  round-trip, and Smart Context FK integrity. The active DB remained byte-for-
  byte unchanged at revision `f2915371d283` with zero Smart Context rows.
- `10.R2-MR2 = IMPLEMENTED / VALIDATED`; R2 remains open until a separate,
  explicitly authorized active-database Alembic reconciliation is executed.

---

## [PHASE-10.R2-B7] — 2026-10-06 — Consumer integration foundations

- Added a typed, read-only internal foundation for future Home, Planning, Goal,
  and FIRE consumers. Each method fixes its B5 feature and delegates exactly
  once with the authenticated owner and explicit `as_of_date`.
- Preserved B5 Smart Values without flattening provenance or converting
  references into effective engine inputs. Planning contribution/return/
  inflation and FIRE spending/withdrawal/return/inflation/contribution remain
  explicit `ASSUMPTION_REQUIRED` outcomes.
- Added no SQL, source-domain reader, internal HTTP, write path, migration,
  frontend, financial formula, public route, AI, external provider, or R6 smart
  prefill. Relevant OpenAPI operations are byte-identical before and after B7.
- Validated `31` B5+B7 focused tests, `153` B1–B7 Smart Context tests, `497`
  Planning regressions, `67` FIRE regressions, `133` Goals/Health regressions,
  and complete units at `835 passed, 2` unchanged historical Investments
  failures.
- `10.R2-B1–B7 = IMPLEMENTED / VALIDATED`; `10.R2-B6 = INDEPENDENTLY
  APPROVED`; `10.R2-B8 — Stabilization & Independent Validation = READY / NOT
  STARTED`. No staging, commit, push, or B8 work was performed.

---

## [PHASE-10.R2-B6] — 2026-10-06 — Profile context experience and browser transition

- Connected the existing `/profile` experience to authenticated declared
  context GET/PATCH and recurring-income list/confirm/reject/reset APIs without
  adding a route, backend behavior, schema, or migration.
- Separated declared monthly gross income from observed recurring evidence,
  preserved exact Decimal strings, exposed bounded provenance and evidence,
  and added explicit save, clear, confirm, reject, reset, stale, ambiguity,
  unavailable, and evidence-change states.
- Confirmed that `fin_profile_extended` has no persisted declared-income field
  eligible for transition. Initial load is GET-only, sends no browser object,
  and preserves only the existing four local presentation/professional fields.
- Remediated all five material findings from the first independent review:
  serialized candidate mutations/retries, distinct stale confirmed/rejected
  presentation, persistent and truthful action feedback, naïve-UTC timestamp
  normalization, and rendered Profile behavior coverage. Added only the minimal
  compatible test dependencies `@testing-library/react@16.3.3` and
  `jsdom@30.1.2`.
- Validated `44` focused B6 tests (`30` helper/client plus `14` rendered page),
  `121` complete frontend tests, TypeScript, targeted lint, and the production
  build. Global lint remains at the unchanged `53 errors / 46 warnings`, with
  no finding in a B6 file.
- Independent delta re-review approved the M1–M5 remediation with `0` blocking
  and `0` material findings; each material finding is closed.
- `10.R2-B1–B6 = IMPLEMENTED / VALIDATED`; `10.R2-B6 = INDEPENDENTLY APPROVED`;
  `10.R2-B7 — CONSUMER INTEGRATION FOUNDATIONS = READY / NOT STARTED`. No
  commit or push was created before this checkpoint.

---

## [PHASE-10.R2-B5] — 2026-10-05 — Feature-specific Smart Context composition

- Added an internal authenticated `SmartFinancialContextService` with immutable
  Smart Values and explicit allowlists for Profile, Home, Planning, Goal, and
  FIRE. Unknown/free-form features fail instead of receiving generic context.
- Added thin read adapters over declared Profile context, B3/B4 recurring
  evidence/decisions, certified Health monthly facts, the Decimal-safe owned
  Goal reader, and the ADR-023 portfolio resolver. The composer contains no SQL,
  financial formula, internal HTTP, write, provider, or AI path.
- Preserved declared versus observed versus derived meaning, current versus
  stale evidence, source-specific periods/freshness, explicit unavailable
  reasons, exact Decimal values, multiple recurring sources without aggregation,
  and offered/effective override metadata without persistence.
- Planning and FIRE receive only eligible investment wealth and explicit
  assumption-required states. Health realized savings remains a labeled
  historical reference, not contribution capacity; current expenses do not
  become retirement spending.
- Validated `20` focused B5 tests, `142` combined B1–B5 tests, `272`
  Goals/Health regressions, `128` Planning/FIRE regressions, and complete units
  at `824 passed, 2` unchanged historical Investments failures. OpenAPI is
  unchanged and contains no generic Smart Context route.
- `10.R2-B1/B2/B3/B4/B5 = IMPLEMENTED / VALIDATED`; `10.R2-B6 — PROFILE
  CONTEXT EXPERIENCE & BROWSER TRANSITION = READY / NOT STARTED`. No frontend,
  migration, public API, financial-engine change, commit, or push was added.

---

## [PHASE-10.R2-B4] — 2026-10-05 — Income decision state and authenticated API

- Added the four contract-locked authenticated income-candidate routes for
  deterministic review and explicit confirm/reject/reset actions.
- Composed B3 current evidence with B1 durable decisions without persisting
  candidates. Exact-version overlay, visible stale decisions, reversible state
  replacement, and deterministic current-first ordering are enforced.
- Added strict fingerprint-only decision requests. Every confirm/reject
  recomputes the current server-owned candidate; changed evidence returns `409`
  and forged, absent, or disappeared candidates return a non-enumerating `404`.
- Public responses use exact Decimal strings and omit raw descriptions,
  transaction identifiers, account scope, source signatures, internal user
  identity, and unapproved labels. Only `recurring_income_decisions` may change;
  Profile, transactions, governance, Health, financial engines, and frontend
  remain untouched.
- Validated `32` focused B4 tests, `122` combined B1–B4 tests, `103`
  Health/Pierre/transaction regressions, `138` auth/Profile/Goals/API-foundation
  regressions, and complete units at `803 passed, 2` unchanged historical
  Investments failures. A read-only active-database smoke left transaction and
  decision counts unchanged with no pending ORM mutations.
- `10.R2-B1/B2/B3/B4 = IMPLEMENTED / VALIDATED`; `10.R2-B5 — FEATURE-SPECIFIC
  SMART CONTEXT COMPOSITION = READY / NOT STARTED`. No B5 composition,
  frontend, migration, AI, external provider, commit, or push was added.

---

## [PHASE-10.R2-B3] — 2026-10-05 — Deterministic recurring-income evidence engine

- Added a bounded read-only adapter over eligible governed
  `CLASSIFIED`/`ENTRADA`/`CREDIT` ledger rows after the exact-single-user guard.
- Added version-1 NFKC/case-fold/whitespace normalization, an explicit canonical
  SHA-256 signature payload, opaque candidate identity, six-calendar-month
  selection, and the three-distinct-month recurrence gate.
- Added exact Decimal latest/min/max/median/MAD evidence, monthly occurrence
  counts, partial-current-month semantics, deterministic ordering, structured
  same-titularity/investment exclusions, and transfer-ambiguity flags.
- Validated `35` focused B3 tests, the unchanged `55` B1+B2 tests, `101`
  Health/Pierre/transaction regressions, a read-only aggregate live smoke, and
  complete units at `771 passed, 2` unchanged historical Investments failures.
- `10.R2-B1/B2/B3 = IMPLEMENTED / VALIDATED`; `10.R2-B4 — INCOME DECISION STATE
  & API = READY / NOT STARTED`. No decision write/API, candidate persistence,
  frontend, migration, AI, external provider, commit, or push was added.

---

## [PHASE-10.R2-B2] — 2026-10-05 — Authenticated declared Profile context API

- Added authenticated `GET` and `PATCH /api/v1/profile/context` for only the
  approved declared monthly gross income and authenticated read-only name/email.
- Reused the B1 exact-single-user guard and declared-context repository; requests
  accept only positive cent-scale Decimal strings or explicit null and expose no
  public owner/account selector.
- Added purpose-limited declared provenance, safe ownership/error translation,
  and a request dependency that owns commit/rollback while B1 repositories
  remain commit-free.
- Validated `32` focused B2 tests, the unchanged `23` B1 tests, `69` relevant
  auth/Goals/API-foundation regressions, OpenAPI route preservation, and the
  complete unit result `736 passed, 2` unchanged historical Investments
  failures.
- `10.R2-B1/B2 = IMPLEMENTED / VALIDATED`; `10.R2-B3 — RECURRING INCOME
  EVIDENCE ENGINE = READY / NOT STARTED`. No detector, recurring-decision API,
  frontend, migration, external provider, AI, commit, or push was added.

---

## [PHASE-10.R2-B1] — 2026-10-05 — Declared context persistence and ownership foundation

- Added one Alembic revision with only `user_declared_financial_context` and
  `recurring_income_decisions`; no candidate/evidence table and no backfill.
- Added exact Decimal/BRL/monthly/gross declaration invariants, versioned
  confirm/reject decision identity, reversible repository operations, and
  caller-controlled transaction semantics.
- Added a reusable fail-closed exact-single-user ownership guard without
  coupling Smart Context to Planning's portfolio resolver.
- Validated 23 focused B1 tests, 30 relevant ownership/Planning/Goals/auth
  regressions, a single Alembic head, and upgrade/downgrade/re-upgrade against a
  disposable copy of the real database. The complete backend unit directory
  returned `704 passed, 2 failed`, with only the two unchanged historical
  Investments/MagicMock failures.
- `10.R2 = IMPLEMENTATION IN PROGRESS`; `10.R2-B1 = IMPLEMENTED / VALIDATED`;
  `10.R2-B2 = READY / NOT STARTED`. No API, frontend, detector, AI, external
  provider, financial engine, commit, or push change was made.

---

## [PHASE-10.R2-A] — 2026-10-03 — Smart Financial Context contract lock

- Audited the real Profile/browser boundary, active transaction model and
  endpoints, read-only SQLite evidence, and Health/Goals/Planning/FIRE source
  authorities before defining R2 behavior.
- Locked ADR-028 and `SMART_FINANCIAL_CONTEXT_CONTRACT.md`: minimal declared
  monthly gross income; deterministic three-distinct-months-in-six recurring
  candidates; no amount confidence gate; explicit human decisions; strict
  provenance, ownership, privacy, and feature-specific composition.
- Added `SMART_FINANCIAL_CONTEXT_IMPLEMENTATION_PLAN.md` with B1–B8 gates.
  `10.R2-A = CONTRACT LOCKED / IMPLEMENTATION READY`; `10.R2-B1 = READY / NOT
  STARTED`. Documentation only; no code, test, migration, staging, commit, or
  push action.

---

## [PHASE-10.R1] — 2026-10-02 — Wealth OS architecture and documentation lock

- Locked FINANALYTICS as a personal Wealth OS and adopted the incremental
  composition-refactor strategy while preserving Goals, Financial Health,
  Planning, FIRE, and the 10.5-A decisions.
- Consolidated product vision, current state, active queue, architecture, data
  semantics, frontend/UX, AI, security, product references, agent guidance, and
  document precedence into their existing canonical owners.
- Locked the target product areas; Profile and Settings reuse; seven-class Smart
  Context taxonomy; smart-value/provenance rules; External Context pipeline;
  AI tool/privacy/secret boundary; System/Light/Dark target; and the R2–R7 then
  10.5-B dependency order in ADR-027.
- Marked the root product specification and final-product narrative as preserved
  historical inputs rather than active authorities. R0 and 10.5-A remain
  evidence, not duplicated architecture owners.
- Reconciled current AI reality: no Advisor, Insights, Copilot, OpenAI, Ollama,
  working Gemini, scheduler, tool registry, or provider abstraction exists.
- `10.R1 = ARCHITECTURE / DOCUMENTATION LOCKED`; `10.R2 = READY / NOT STARTED`;
  `10.5-B = PAUSED / PENDING WEALTH OS REALIGNMENT`. Documentation/agent files
  only; no backend, frontend, test, migration, dependency, staging, commit, or
  push action.

---

## [PHASE-10.R0] — 2026-10-02 — Wealth OS product realignment audit

- Audited current product architecture, navigation, Goals/Planning/FIRE overlap, Profile, Settings, recurring-income feasibility, external data, AI, theme, privacy, product references, documentation ownership, target information architecture, and dependency order without changing production code.
- Added the root operational `AGENTS.md`, one canonical realignment audit, and one product-reference catalog; recorded the high-level realignment gate in ADR-026 and updated status owners minimally.
- `10.R0 = AUDIT COMPLETE`; `10.R1 = READY / NOT STARTED`; `10.5-A` remains complete with decisions preserved; `10.5-B = PAUSED / PENDING WEALTH OS REALIGNMENT`. No code, test, migration, package, staging, commit, or push was created.

---

## [PHASE-10.4-D7] — 2026-10-01 — FIRE independent validation and closure

- Independently reconciled ADR-025 and `FIRE_CONTRACT.md` against the complete FIRE domain, orchestration, API, frontend, source/provenance, read-only, and deferred-feature boundaries. The implementation remains a thin deterministic REAL-basis layer over Planning with one selected wealth fact and no persistence.
- Repeated FIRE backend (`67 passed`), focused Planning (`262 passed`), FIRE frontend (`13 passed`), locale (`57 passed`), full Vitest (`77 passed`), TypeScript, focused lint, production build, live secured OpenAPI, independent Decimal golden vectors, and real-service REAL/NOMINAL composition. General backend units reproduced only the two unchanged historical Investments/MagicMock failures (`681 passed, 2 failed`).
- `10.4-A = AUDIT COMPLETE`; `10.4-B = CONTRACT LOCKED`; `10.4-C = IMPLEMENTATION PLAN COMPLETE`; `10.4-D1–D5 = IMPLEMENTED / VALIDATED`; `10.4-D6 = VALIDATED / STABILIZED`; `10.4-D7 = VALIDATED / CLOSED`; Phase 10.4 FIRE is `VALIDATED / CLOSED`. Phase 10.5 Portfolio Intelligence is `READY / NOT STARTED`. No code, test, migration, commit, or push was created during closure.

---

## [POST-10.3-UX-B7] — 2026-09-27 — Independent validation and UX closure

- Independently reconciled ADR-024, real Planning UX implementation, source boundaries, accessibility/living states, and documentation. The user-approved UX-B6 manual review is recorded as `VALIDATED`.
- Repeated frontend Vitest (`64 passed`), TypeScript, focused Planning/Health lint, production build, focused Planning API/domain/resolver regression (`496 passed`), and a secured five-route Planning OpenAPI probe. The only textual financial conversion to `Number` remains the isolated Recharts rendering adapter.
- `UX-B1–UX-B7 = VALIDATED`; `POST-10.3 UX = VALIDATED / CLOSED`. No backend/API/engine/financial-contract/persistence/FIRE/Portfolio Intelligence/Copilot change, commit, or push was made. Historical Swagger manual auth, Investments timeline tests, ADR-014, and Recharts SSG warning remain explicit debt.

---

## [POST-10.3-UX-B6] — 2026-09-27 — Living states and responsive polish

- Added CSS-only first-submit skeletons, accessible loading announcements, preserved prior results during recalculation, and explicit stale-premise feedback across all five Planning capabilities. No API call occurs outside explicit submit.
- Result surfaces now transition as a unit with reduced-motion support; no financial counter, optimistic value, live indicator, backend/API change, or new dependency was added.

---

## [POST-10.3-UX-B5-R1] — 2026-09-27 — Quiet Financial OS visual polish

- Reconciled the accepted Planning result surfaces toward a quieter output-first hierarchy: responsive tabular hero values, restrained two-pixel semantic accent edges, editorial secondary metrics, calmer form surfaces, and a deliberate CTA-to-result/chart rhythm.
- Unified primary Planning calculation actions under violet. Success, attention/target, comparison, and neutral reference states remain semantic within results; late Goal projection is amber rather than pink/rose.
- Refined Recharts grid, analytical line palette and stroke hierarchy, compact provenance details, and neutral comparison-reference treatment. No motion, live/freshness affordance, recommendation, backend/API/financial behavior, or additional Decimal conversion was added. `UX-B5 = FUNCTIONALLY ACCEPTED`; `UX-B5-R1 = IMPLEMENTED / READY FOR MANUAL VISUAL REVIEW`; `UX-B6 = READY / NOT STARTED`.

---

## [POST-10.3-UX-B5] — 2026-09-27 — Results, Charts, Visual Hierarchy & Provenance

- Reworked all Planning response surfaces into answer-first result heroes with pt-BR string-safe BRL, annual/monthly rate, civil-date, and reference-month formatting. Supporting metrics are visually secondary; no response contract, financial calculation, or source semantics changed.
- Compressed source provenance into accessible details chips, preserving MyProfit monthly buckets and imported-version terminology while omitting technical account/run IDs and never fabricating portfolio observation dates. Comparison cards now present neutral named scenarios and the explicit reference without ranking.
- Improved Recharts axis, tooltip, legend, line hierarchy, spacing, and certified target reference lines. The sole Decimal→`Number` conversion remains isolated in the chart-rendering adapter. Vitest `64`, TypeScript, focused lint, and production build passed. `UX-B4 = VALIDATED`; `UX-B5 = IMPLEMENTED / READY FOR MANUAL UI REVIEW`; `UX-B6 = READY / NOT STARTED`.

---

## [POST-10.3-UX-B4] — 2026-09-26 — Scenario Comparison Shared Context

- Replaced repeated scenario context with one shared date-base, horizon, output mode, fixed operational disclosure, and optional target pair. The pure builder expands that context into the unchanged ordered comparison request; source, contribution, return, return type, inflation, label, archetype, and manual provenance remain scenario-specific.
- Reference is now explicitly selected and clears when its scenario is removed. Scenario cards show user-facing fallback names rather than internal IDs, preserve mixed source semantics, and remain responsive without a parallel API or calculation path.
- Added four pure shared-context tests; the Node-only Vitest suite is `64 passed`. TypeScript, focused Planning lint, and production build passed. `UX-B3 = VALIDATED` from accepted manual review; `UX-B4 = IMPLEMENTED / READY FOR MANUAL UI REVIEW`; `UX-B5 = READY / NOT STARTED`. No backend, API, engine, persistence, result/chart redesign, skeleton, motion, commit, or push was added.

---

## [POST-10.3-UX-B3] — 2026-09-26 — Smart Defaults & Advanced Options

- Added submit-time local civil data-base context, submit-time manual-source observation, explicit Advanced overrides, and a visible Nominal→Nominal standard state. The backend still receives the complete certified contract; no financial assumption, API contract, or backend behavior changed.
- Migrated user-entered Planning money, contribution, targets, return, and conditional inflation through the UX-B1 exact pt-BR parsers. Lexical errors remain beside the field and prevent the request without clearing form state. MyProfit now has an accessible compact information disclosure rather than permanent technical copy.
- Added three pure request-builder tests; the Node-only Vitest suite is now `60 passed`. TypeScript, focused Planning lint, and production build passed. `UX-B2 = VALIDATED` from the accepted manual review; `UX-B3 = IMPLEMENTED / READY FOR MANUAL UI REVIEW`; `UX-B4 = READY / NOT STARTED`. No backend, engine, persistence, result/chart redesign, shared comparison context, commit, or push was added.

---

## [POST-10.3-UX-B2] — 2026-09-26 — Page Chrome, Copy & Three Intentions

- Replaced the five peer Planning tabs with the compact `Simular`, `Objetivo`, and `Comparar` entry control. `Objetivo` reveals the secondary tasks `Quando alcanço?`, `Quanto aportar?`, and `Meta existente`; all map to the unchanged capability components and API contracts.
- Removed redundant visible Planning and Financial Health eyebrows/titles, preserving semantic `sr-only` H1 headings. Removed repeated capability headers and implementation-detail copy without changing forms, results structure, charts, financial display/input, or request payloads.
- TypeScript, B1 Vitest (`57 passed`), focused Planning/Health lint, and production build passed. `UX-B2 = IMPLEMENTED / READY FOR MANUAL UI REVIEW`; `UX-B3 = READY / NOT STARTED`; Phase 10.3 remains `VALIDATED / CLOSED` and 10.4 remains `READY / NOT STARTED`.

---

## [POST-10.3-UX-B1] — 2026-09-26 — pt-BR Financial Input/Output Primitives

- Added isolated, string-safe `planningLocale` primitives for BRL money, human percentage/fraction conversion, civil dates, monthly reference buckets, and structured lexical error codes/copy. Financial text never converts through JavaScript `Number` or float formatting.
- Added Node-only Vitest `3.2.4` as a dev dependency and `57` focused table/boundary tests, including values beyond `Number.MAX_SAFE_INTEGER`, strict pt-BR grouping, no silent rounding, percentage unit semantics, display rounding, and local civil dates.
- TypeScript, focused lint, and production build pass. No Planning form, capability, backend, engine, or financial request path changed. `UX-B1 = VALIDATED`; `UX-B2 = READY / NOT STARTED`; Phase 10.3 remains `VALIDATED / CLOSED` and 10.4 remains `READY / NOT STARTED`.

---

## [POST-10.3-UX-A] — 2026-09-26 — Planning UX & Simplicity Contract

- Locked ADR-024 and `PLANNING_UX_CONTRACT.md` without production changes. The official direction is `Quiet Financial OS`, with minimal Wealth Intelligence page chrome, three Planning intentions (`Simular`, `Objetivo`, `Comparar`), progressive disclosure, and answer-first result hierarchy.
- Defined exact string-safe pt-BR money, percentage, and date input/display; submit-time temporal context defaults; explicit source semantics; Goal target-basis handling; shared Scenario Comparison context; compact provenance; Recharts presentation boundaries; restrained motion; and the Tailwind/Radix/shadcn-compatible/Recharts stack policy.
- Classified frontend-now, small-backend-contract, future-phase, and rejected items. Portfolio preview, assumption references, and Goal-derived presets remain separate optional contracts; FIRE, Portfolio Intelligence, Copilot, persistence, automatic assumptions, ranking, and browser-side MyProfit lookup were not started. Phase 10.3 remains `VALIDATED / CLOSED`; 10.4 remains `READY / NOT STARTED`.

---

## [TSK-10.3.12] — 2026-09-26 — Planning Final Validation & Closure

- Closed Phase 10.3 as a deterministic, transient Planning capability: forward projection, Target Achievement, Required Contribution, Goal Planning, Scenario Comparison, authenticated API, analytical frontend, and the certified MyProfit investment-portfolio wealth source.
- Closure checks: `269 passed` across API integration, portfolio resolver, and representative Planning domain suites; five secured OpenAPI operations; TypeScript, focused lint, and production build passed. The general baseline remains `614 passed, 2` known historical Investments/MagicMock failures.
- Preserved boundaries: no persistence, Sustainable Capacity, FIRE, Portfolio Intelligence, LLM, net-worth aggregation, realtime portfolio claim, multi-user portfolio ownership, or complete historical snapshot reconstruction. Swagger manual auth remains deferred by user. `10.3 = VALIDATED / CLOSED`; `10.4 = READY / NOT STARTED`; post-closure Planning UX refinement review awaits user feedback.

---

## [TSK-10.3.11] — 2026-09-26 — Planning Integration & Stabilization

- Reconciled all five Planning capabilities and authenticated APIs against ADRs 019–023, including source-specific selector boundaries, nominal/real behavior, period-zero/timing/horizon semantics, Goal applicability-first, explicit ordered scenarios, certified deltas, and ADR-023 portfolio temporality/provenance.
- No production defect or feature change was needed. Planning API suites: `157 passed`; Planning domain/resolver suites: `339 passed`; full unit baseline: `614 passed, 2` unchanged historical Investments/MagicMock timeline failures. TypeScript, focused Planning ESLint, and production build passed; `/wealth-intelligence/planning` remains present.
- `10.3.11 = VALIDATED / STABILIZED`; `10.3.12 = READY / NOT STARTED`. Swagger Authorize manual smoke, ADR-014, Investments timeline tests, Recharts SSR warning, absent frontend test runner, and broad UX refinements remain deferred/accepted debt. No commit or push was created.

---

## [TSK-10.3.10B4] — 2026-09-26 — Independent / Adversarial Portfolio Source Validation

- Validated `INVESTMENT_PORTFOLIO_SNAPSHOT` end-to-end: guarded single-user/single-tenant ownership, semantic UUID and import-run provenance, zero/one/many scope handling, Decimal preservation, strict source-only API selection, and frontend source-state isolation.
- Reconfirmed `LATEST ELIGIBLE AS OF`: the greatest eligible monthly `reference_month` is selected only when its technical snapshot-version update time is not after the requested as-of date. `observed_at` remains null; the UI presents only `MM/YYYY` and an import/update timestamp, never a fabricated daily observation.
- B1 resolver: `16 passed`; Planning API: `157 passed`; Planning domain: `323 passed`; full units: `614 passed, 2` unchanged historical Investments/MagicMock timeline failures. OpenAPI has exactly five secured Planning POST routes; TypeScript, focused ESLint, and production build pass. User confirmed B3 manual smoke for Projection, Target, Required, Goal, and Scenario Comparison.
- `10.3.10B1` through `10.3.10B4 = VALIDATED`; `10.3.10B = VALIDATED / COMPLETE`; `10.3.11 = READY / NOT STARTED`. Limitations remain: investment portfolio wealth, not net worth; BRL-only; monthly reference bucket; no complete historical time travel, preview endpoint, or multi-user account ownership model. No production code, schema, migration, engine, frontend dependency, commit, or push was added during validation.

---

## [TSK-10.3.10B3] — 2026-09-25 — Planning Frontend Portfolio Source Integration

- Added the strict `INVESTMENT_PORTFOLIO_SNAPSHOT` selector to the existing shared Planning form and request unions for Projection, Target Achievement, Required Contribution, Goal Planning, and Scenario Comparison. The browser sends only the discriminant; no manual amount/timestamp state, account, run, temporal data, or provenance can enter the portfolio selector.
- The UI now labels the source as MyProfit investment-portfolio wealth, hides manual wealth inputs, has no preview or Investments lookup, and renders only certified source facts. Monthly `reference_month` is displayed as `MM/YYYY`; technical `updated_at` is not called a financial observation; null `observed_at` is omitted.
- TypeScript and focused ESLint pass. `10.3.10B3 = IMPLEMENTED / READY FOR MANUAL VALIDATION`; `10.3.10B4 = READY / NOT STARTED`; `10.3.10B = IN PROGRESS`. No backend, migration, engine, persistence, dependency, commit, or push was added.

---

## [TSK-10.3.10B2] — 2026-09-25 — Planning API Portfolio Source Integration

- Added the strict source-only `INVESTMENT_PORTFOLIO_SNAPSHOT` selector to the authenticated Planning boundary and routed it exclusively to the validated ADR-023 resolver with `current_user.id` and the request `as_of_date`.
- Integrated Projection, Target Achievement, Required Contribution, Goal Planning after applicability preflight, and atomic Scenario Comparison source resolution. Resolver failures now produce a safe `422`; `reference_month` and technical provenance `updated_at` are preserved while `observed_at` remains null.
- Added `8` dedicated B2 HTTP tests. Planning API suites: `157 passed`; B1 plus Planning domain: `339 passed`; general units: `614 passed, 2 historical Investments/MagicMock failures`. No frontend, migration, schema, engine, write path, preview endpoint, commit, or push was added. `10.3.10B2 = VALIDATED`; `10.3.10B3 = READY / NOT STARTED`; `10.3.10B = IN PROGRESS`.

---

## [TSK-10.3.10B1] — 2026-09-25 — Investment Portfolio Source Resolver & Reader Foundation

- Added the internal ADR-023 resolver and Decimal-safe portfolio fact construction. It verifies the one-user tenant guard, semantic UUID ownership, complete scope/run provenance, zero/one/many cardinality, strict monthly bucket validity, latest-eligible-as-of selection, and `observed_at = null` for this source.
- No router, public DTO selector, OpenAPI, frontend, Planning engine, migration, schema, write path, aggregation, or automatic source exposure was added.
- Focused resolver tests: `16 passed`; Planning read foundation: `12 passed`; Goal Planning: `101 passed`; general units: `609 passed, 2 historical Investments/MagicMock failures`. `10.3.10B1 = VALIDATED`; `10.3.10B2 = READY / NOT STARTED`; `10.3.10B = IN PROGRESS`.

---

## [TSK-10.3.10A-R1] — 2026-09-25 — MyProfit Snapshot Temporal Semantics Lock

- Confirmed from the real MyProfit Evolução CSV and parser that `Data` contains only `Mmm-YYYY`; `reference_month` is a monthly evolution bucket, not an invariant month-end timestamp. A live `2026-09` row persisted before September month-end proves that the current bucket may be month-to-date.
- Confirmed that `portfolio_snapshots.updated_at` is assigned by the confirmation UPSERT and means snapshot-version update/import time, not financial observation time. ADR-023 no longer aliases it to `PlanningFactAsOf.observed_at`.
- Retained `LATEST ELIGIBLE AS OF` as look-ahead safe: the greatest period not after the as-of month is eligible only when its current persisted version was updated no later than `as_of_date`. Same-month data can be eligible; a later import cannot be used for an earlier as-of.
- Locked `HISTORICAL AS-OF UNSUPPORTED WITH CURRENT DATA MODEL` as a reproducible time-travel guarantee because UPSERT retains neither previous versions nor a source observation timestamp. No production code, schema, or database data changed.

---

## [TSK-10.3.10A] — 2026-09-24 — Investment Portfolio Source Contract & Ownership Audit

### Contract

- Added ADR-023. The authenticated selector will contain only `INVESTMENT_PORTFOLIO_SNAPSHOT`; the server must enforce a formal one-user/one-MyProfit-scope tenant invariant and successful import-run ownership. Zero or multiple scopes are `422`; the client never supplies account, amount, or certified provenance.
- Locked `LATEST ELIGIBLE AS OF`: select the greatest portfolio reference month not after the scenario month only when the current persisted row version was updated no later than `as_of_date`. TSK-10.3.10A-R1 later clarified that this is technical persistence/import time rather than a financial observation timestamp. Future data and later UPSERT versions cannot leak into historical requests; no arbitrary staleness threshold was added.
- Locked `portfolio_snapshots.patrimonio` as Decimal investment-portfolio wealth in the current BRL application context, never net worth or a positions aggregation. All five Planning capabilities may use the source; Goal applicability remains first and comparison resolution remains atomic.

### Evidence and status

- Read-only live audit: 1 user, 7 Pierre/Core accounts, no MyProfit row in `accounts`, 1 logical MyProfit scope, and 49 unique monthly snapshots from `2022-09` through `2026-09`, all currently tied to a successful `MYPROFIT_EVOLUCAO` run for the sole user. ADR-014 does not govern `portfolio_snapshots` and is non-blocking.
- `NO MIGRATION REQUIRED` for this constrained single-tenant implementation; future multi-user or multi-portfolio support requires a separate explicit investment-account ownership model. No production code or database row changed.
- `10.3.10 = VALIDATED`; `10.3.10A = CONTRACT LOCKED / READY FOR 10.3.10B`; `10.3.10B = READY / NOT STARTED`; `10.3.11–10.3.12 = NOT STARTED`. Planning visual/UX refinements remain deliberately deferred by the user. Swagger Authorize manual smoke remains `DEFERRED BY USER`.

---

## [TSK-10.3.9] — 2026-09-23 — Planning Frontend Foundation

### Added

- Canonical `/wealth-intelligence/planning` entry, Wealth Intelligence navigation, and a functional hub card.
- Strict TypeScript contracts plus authenticated API client functions for all five transient Planning routes. Financial values are preserved as strings; only approved user-provided and Goal-current-amount selectors are represented.
- Projection-only vertical slice with explicit inputs, loading, error, empty, and direct certified-result states. No browser calculation, chart, persistence, recommendation, capacity, Retirement/FIRE, Portfolio Intelligence, or LLM capability was added.

### Verified

- `npx.cmd tsc --noEmit`, focused ESLint, static search for financial conversions/math, and `npm.cmd run build` passed. The production build includes `/wealth-intelligence/planning`; the pre-existing Recharts SSR size warning remains unrelated.

### Status

- Independent validation passed: `10.3.9 = TECHNICALLY VALIDATED / MANUAL UI SMOKE PENDING`; `10.3.10 = READY / NOT STARTED`.
- `10.3.8-F` automated validation remains complete. Swagger Authorize manual smoke is `DEFERRED BY USER`, not passed.

---

## [TSK-10.3.8-F] — 2026-09-23 — Planning API Integration & Stabilization

### Status

`AUTOMATED VALIDATION PASSED / READY FOR MANUAL SMOKE`

### Verification

- Added only `tests/unit/test_planning_api_integration.py`: five cross-endpoint checks for exact secured route/OpenAPI inventory, common Decimal and blocked-portfolio request behavior, uniform non-enumerating Goal ownership, and deterministic 1,200-month serialization.
- Integration `5 passed`; B–E API `147 passed`; Planning domain `323 passed`; Goals `65 passed`; Health `68 passed`; general unit `593 passed, 2 historical Investments/MagicMock failures`.
- No production fix. `10.3.8` macro closure remains pending the user Swagger smoke; persistence remains `DEFERRED — TRANSIENT API FIRST`.

## [TSK-10.3.8-E-V] — 2026-09-23 — Independent Scenario Comparison Endpoint Validation

### Status

`VALIDATED`

### Verification

- Independently validated the authenticated ordered endpoint through HTTP, domain, mapper, OpenAPI, ownership, and regression probes. Added test-only checks for atomic prevalidation before financial subengines, no Goal Planning applicability leakage, strict target Decimal input, rejected ranking/recommendation fields, and direct certified-delta mapping.
- Focused suite: `42 passed`; Planning domain regressions `323 passed`; Goals `65 passed`; Health `68 passed`; general unit `585 passed, 2 historical Investments/MagicMock failures`.
- `10.3.8-E = VALIDATED`; `10.3.8-F = READY / NOT STARTED`; scenario persistence remains `DEFERRED — TRANSIENT API FIRST`.

## [TSK-10.3.8-E] — 2026-09-23 — Scenario Comparison Endpoint

### Status

`IMPLEMENTED / READY FOR VALIDATION`

### Added

- Added authenticated transient `POST /api/v1/planning/scenarios/compare` with strict ordered DTOs, explicit reference, optional shared target/basis, metadata-only archetypes, source-preserving response DTOs, and full certified nested projection/target results.
- The boundary resolves every approved Goal source server-side before one `ScenarioComparisonEngine` call; clients cannot forge a certified fact and portfolio source remains structurally unavailable.
- The API only maps engine-owned Decimal deltas and temporal semantics. It neither sorts/ranks/recommends nor recomputes financial values, invokes other Planning services, writes state, or persists scenarios.

### Verification

- Focused Scenario Comparison HTTP suite: `21 passed`; focused foundation/calculation/Goal/Scenario/Goal Planning regression: `428 passed`.
- `10.3.8-E = IMPLEMENTED / READY FOR VALIDATION`; `10.3.8-F = READY / NOT STARTED`; persistence remains `DEFERRED — TRANSIENT API FIRST`.

## [TSK-10.3.8-D-R1-SOL] — 2026-09-22 — Goal Source / Applicability Reconciliation

### Status

`RECONCILED / READY FOR FINAL REVALIDATION`

### Reconciled

- Locked the authoritative result: a structurally valid non-projectable Goal does not consume an unavailable projection-specific `GOAL_CURRENT_AMOUNT` and returns `200 / NOT_APPLICABLE`; an ACTIVE eligible Goal still returns `422` when that selected fact is required and absent.
- Added a pure `GoalPlanningService` applicability preflight used by the HTTP orchestration before source resolution. The service remains the single type/status authority; the router has no duplicated eligibility list, and the domain has no database knowledge.
- No dummy wealth, fallback source, Goal mutation, financial-engine change, persistence, or 10.3.8-E implementation was introduced.

### Verification

- Goal endpoint `37 passed`; Goal Planning `65`; foundation `41`; calculation endpoints `25`; other Planning `222`; Goals `65`; Health `68`. General unit: `508 passed, 2 historical Investments/MagicMock failures`.
- `10.3.8-D = RECONCILED / READY FOR FINAL REVALIDATION`; `10.3.8-E = NOT STARTED`.

## [TSK-10.3.8-D-V2] - 2026-09-23 - Final Owned Goal Planning API Validation

### Status

`VALIDATED`

### Validation

- Confirmed one internal lifecycle/type applicability authority shared by `preflight_applicability()` and `evaluate()` across all real Goal status/type pairs.
- Confirmed HTTP call order: applicable Goals resolve the selected source only after preflight; non-projectable Goals stop after preflight even when current amount is available.
- Added validation-only matrix and malformed-user-source coverage. No production code was changed during V2.

### Verification

- Goal endpoint `39 passed`; Goal Planning `101`; foundation `41`; calculation endpoints `25`; other Planning `222`; Goals `65`; Health `68`. General unit: `546 passed, 2 historical Investments/MagicMock failures`.
- `10.3.8-D = VALIDATED`; `10.3.8-E = READY / NOT STARTED`.

## [TSK-10.3.8-D] — 2026-09-21 — Owned Goal Planning Endpoint

### Status

`IMPLEMENTED / READY FOR VALIDATION`

### Added

- Authenticated transient `POST /api/v1/planning/goals/{goal_id}/projection`, with owned server-side Goal/Decimal read, a path-specific Goal-current-amount selector, and a separate Goal Planning response mapper/DTO.
- One `GoalPlanningService` delegation per executable request. The HTTP boundary does not duplicate eligibility, target crossing, timing, monetary math, or Goal state changes.
- Strict Goal-field forgery rejection; exact Decimal-string response mapping for the Goal fact, assumptions, initial fact, and nested target result.

### Verification

- Focused endpoint suite: `28 passed`; foundation `41`, calculation endpoints `25`, Goal Planning `63`, other Planning `222`, Goals `65`, Health `68` passed. General unit: `497 passed, 2 historical Investments/MagicMock failures`.
- `10.3.8-E = READY / NOT STARTED`; Scenario Persistence remains `DEFERRED — TRANSIENT API FIRST`.

## [TSK-10.3.8-C] — 2026-09-21 — Planning Calculation Endpoints

### Status
`IMPLEMENTED / READY FOR VALIDATION`

### Implementation
- Added authenticated transient `POST /api/v1/planning/projection`, `/target-achievement`, and `/required-contribution` with boundary DTOs that preserve Decimal-string request and response truth, certified projection timelines/summaries, solver statuses, nested results, and public provenance.
- `USER_PROVIDED_SCENARIO` remains caller-provided only. `GOAL_CURRENT_AMOUNT` is resolved only through `PlanningGoalReadQuery(goal_id, current_user.id)` and the Decimal-safe reader; missing and wrong-owner Goals share `404`, unavailable selected amount is `422`, and portfolio source remains structurally unsupported.
- Each route delegates exactly once to its corresponding certified engine. Target value basis must match output mode without conversion. Valid domain outcomes, including non-achievement states, return `200`; local validation maps to `422`, unexpected arithmetic to generic `500`. No write, persistence, financial recalculation, Goal Planning endpoint, Scenario endpoint, Sustainable Capacity, commit, or push was added.

### Verification
- Independent validation: `25 passed` after adding validation-only HTTP coverage for declared precision/determinism, no engine call after failed Goal resolution, intact Required template contribution, Required basis mismatch, and string-only numbers across every endpoint. Foundation `41`, Projection `38`, Target `32`, Required `40`, Goal Planning `63`, Scenario `37`, Assumptions `63`, Read Foundation `12`, Goals `65`, Health `68` passed. General unit: `465 passed, 2 historical Investments/MagicMock failures`.
- `10.3.8-C = VALIDATED`; `10.3.8-D = READY / NOT STARTED`; Scenario Persistence remains `DEFERRED — TRANSIENT API FIRST`.

## [TSK-10.3.8-A] — 2026-09-20 — Planning API & Scenario Persistence Contract Audit

### Status
`API CONTRACT LOCKED / PERSISTENCE DEFERRED — TRANSIENT API FIRST`

### Contract
- Locked five separate authenticated transient POST capabilities under `/api/v1/planning`: Forward Projection, Target Achievement, Required Contribution, owned Goal Planning, and Scenario Comparison. DTOs must use strict decimal strings, canonical ISO dates/enums, stable domain-to-API mapping, complete period/summary results, and no recalculation or automatic assumptions.
- Locked a discriminated initial-wealth selector. User-provided amounts remain explicitly user-provided; Goal current amount is loaded server-side through `goal_id + current_user.id` and the Decimal-safe Planning reader; clients cannot manufacture certified provenance. Portfolio snapshot sourcing is not exposed because its MyProfit account scope has no authenticated-user ownership relation.
- Locked existing bearer/JWT reuse, wrong-owner Goal `404` non-enumeration, `422` for request/domain validation, successful payloads for legitimate solver/planning statuses, and `500` for unexpected arithmetic/invariant failures.
- Full certified monthly timelines and summaries are returned in the initial contract. No arbitrary scenario-count cap, pagination, or summary-only flag was added; transport resource controls remain a later measured infrastructure concern and must never truncate financial requests.

### Persistence Decision
- Scenario storage remains deferred. Owner-scoped lifecycle, identity/naming, update/versioning, frozen-versus-live provenance, refresh/staleness, timestamps/expiration, deletion, Goal relationship, and schema/migration semantics are not approved. `goals.assumptions_json` remains prohibited as canonical storage.
- No router, DTO, service, migration, table, frontend, production test, commit, or push was created. `10.3.8-B — Planning API Foundation` is `READY / NOT STARTED`.

## [TSK-10.3.8-B] — 2026-09-20 — Planning API Foundation

### Status
`VALIDATED`

### Foundation
- Added the registered but endpoint-free `/api/v1/planning` router; shared existing-JWT and synchronous Planning-read dependency annotations; strict decimal-string/date/timestamp request primitives; safe supported source selectors; pure Planning builders/mappers; public provenance responses; and local Planning error translation.
- Decimal input rejects JSON numbers, floats, booleans, non-finite values, scientific notation, and whitespace. It retains declared exponent through the domain boundary; `"1.000"` remains `Decimal("1.000")` until the domain rejects cent-scale violations. Responses emit Decimal strings without rounding or float conversion.
- No financial engine, calculation endpoint, Goal lookup, database read/write, portfolio source, persistence, migration, frontend, Sustainable Capacity, commit, or push was added.

### Verification
- Independent validation added real-JSON Decimal/source-selector coverage. Foundation `41 passed`; Goal Planning `63 passed`; Scenario Comparison `37 passed`; Goals API/domain/repository `65 passed`; Health `68 passed`; general `444 passed, 2 historical Investments/MagicMock failures`.
- `10.3.8-C = READY / NOT STARTED`; Scenario Persistence remains `DEFERRED — TRANSIENT API FIRST`.

---

## [TSK-10.3.7-A] — 2026-09-19 — Sustainable Contribution Capacity Contract Decision

### Status
`DEFERRED — INSUFFICIENT CONTRACT / DATA`

### Decision
- Audited ADRs 019–022, certified Health/Planning boundaries, canonical documentation, and the current database through read-only certified facts. Health exposes realized monthly income, expense, net cashflow/`savings_amount`, savings rate, dates/gaps, categories, anomalies, and trends; it does not establish recurring future affordability.
- Current evidence is 17 consecutive monthly facts from `2025-05` through partial `2026-09`, including 16 closed months with 12 surpluses and 4 deficits. No approved contract selects a lookback, minimum history, partial-month, deficit, anomaly/outlier, statistic, negative-result, currency, or zero/null policy. Future obligations, required cash buffers, income continuity, and external commitments are not certified inputs.
- No formula, production code, test, API, frontend, migration, persistence, commit, or push was created. Realized, planned, scenario, and required contributions remain distinct and are never mapped automatically to sustainable capacity.
- The deferral does not block already certified Planning capabilities. `10.3.8 — Planning API & Scenario Persistence Contract Audit` is `READY / NOT STARTED`; transient API exposure may be contracted independently, while persistence remains separately unapproved.

---

## [TSK-10.3.6-B-V] — 2026-09-19 — Independent Scenario Comparison Validation

### Status
`VALIDATED`

### Validation
- Independently audited the locked ADR-021 contract, comparison implementation, certified engine reuse, and an external Decimal oracle. Verified explicit non-BASE reference behavior, atomic prevalidation before engine calls, exact candidate-minus-reference deltas, period-zero/null temporal semantics, source/provenance preservation, and absence of duplicate financial math, persistence, ranking, recommendation, Goal auto-integration, or Required Contribution automation.
- Added only a validation regression proving frozen `ScenarioDefinition` and preservation of the caller-owned scenario list. No production code changed during validation.
- Results: Scenario Comparison `37 passed`; Goal Planning `63`; Required `40`; Target `32`; Projection `38`; Assumptions `63`; Read `12`; Goals `65`; Health `68`; general `tests/unit` `403 passed, 2 historical Investments/MagicMock failures`.
- `10.3.6-A = CONTRACT LOCKED`; `10.3.6-B = VALIDATED`; `10.3.6` macro = `VALIDATED`; `10.3.7 = DEFERRED — CONTRACT NOT APPROVED`.

---

## [TSK-10.3.6-B] — 2026-09-19 — Scenario Comparison Engine Implementation

### Status
`IMPLEMENTED / READY FOR VALIDATION`

### Implementation
- Added a pure immutable Scenario Comparison engine over the certified `ForwardProjectionEngine` and `TargetAchievementSolver`, with no duplicate financial recurrence, rate conversion, Fisher calculation, rounding, or target crossing logic.
- Added ordered explicit scenarios, unique IDs, explicit reference selection, atomic comparison prevalidation, optional shared target/basis handling, source-preserving nested results, exact Decimal candidate-minus-reference deltas, and certified period-zero/null temporal behavior.
- Extracted `TargetValueBasis` mechanically into a neutral Planning module while preserving `goal_planning.TargetValueBasis` public identity.
- Added contract-focused comparison tests. No API, frontend, persistence, database, migration, Required Contribution automation, sustainable-capacity implementation, commit, or push was created.
- `10.3.6-A = CONTRACT LOCKED`; `10.3.6-B = IMPLEMENTED / READY FOR VALIDATION`; `10.3.6` macro = `IMPLEMENTED / READY FOR VALIDATION`; `10.3.7 = DEFERRED — CONTRACT NOT APPROVED`.

---

## [TSK-10.3.6-A] — 2026-09-19 — Scenario Comparison Contract & Architecture Lock

### Status
`CONTRACT LOCKED / READY FOR IMPLEMENTATION`

### Contract Locked
- ADR-021 now defines ordered immutable scenarios with unique opaque string IDs, optional non-authoritative labels/archetypes, and an explicit reference ID; `BASE` is never an automatic reference.
- Comparison requires at least two scenarios and shared as-of date, resolved monthly horizon, output mode, and contribution timing. Return type and explicit initial wealth may differ while complete provenance is preserved.
- Target comparison is optional. Without target, one Forward Projection runs per scenario. With one shared target amount/basis, Target Achievement is authoritative and its projection is reused; period-zero `ALREADY_ACHIEVED` receives one forward projection only for the horizon summary.
- Money deltas are candidate minus reference. Months saved/lost are reference months minus candidate months; period zero participates, while any non-achieving side makes the temporal delta null.
- Results preserve input order and complete certified nested outputs. Prevalidation and failure are atomic; no ranking, recommendation, causal attribution, persistence, Goal auto-integration, Required Contribution automation, sustainable-capacity inference, market forecast, or 10.4/10.5 implementation is allowed.
- `10.3.6-A = CONTRACT LOCKED`; `10.3.6-B = READY / NOT STARTED`; `10.3.7 = DEFERRED — CONTRACT NOT APPROVED`. No production code, tests, API, frontend, schema, migration, commit, or push was created.

---

## [TSK-10.3.5-V3] — 2026-09-19 — Final Independent Goal Planning Validation

### Status
`VALIDATED`

### Final Evidence
- Final independent controlled probes and the complete regressions confirmed the R2-SOL applicability-first correction.
- `GoalStatus.ACTIVE` is the sole projectable lifecycle status. Non-active Goals and reserved Goal types return `NOT_APPLICABLE` before target basis/output, Goal-current-amount provenance, and deadline validation, with zero solver calls.
- ACTIVE Goals retain strict target-basis and cross-goal-provenance validation. Persisted lifecycle `ACHIEVED` remains separate from mathematical `ALREADY_ACHIEVED`.
- Goal Planning `63 passed`; Required `40`; Target `32`; Projection `38`; Assumptions `63`; Read `12`; Goals `65`; Health `68`; general `366 passed, 2 historical Investments/MagicMock failures`.
- No production code was changed during V3. No database, migration, API, frontend, commit, or push was performed.
- `10.3.5 = VALIDATED`; `10.3.6 = READY / NOT STARTED`.

---

## [TSK-10.3.5-R2-SOL] — 2026-09-19 — Authoritative Goal Planning Contract Reconciliation

### Status
`RECONCILED / READY FOR FINAL REVALIDATION`

### Reconciliation
- Re-audited ADRs 019–022, the real Goal enums/entity/update semantics, Planning code, tests, canonical documentation, and Git baseline without relying on prior validation reports.
- Confirmed the projection-specific validation ordering defect: `GoalPlanningService` previously validated Goal-current-amount provenance and target basis/output compatibility before determining whether the Goal was eligible for forward Planning.
- Corrected the smallest affected boundary: a positive `GoalStatus.ACTIVE` whitelist and type/status applicability now precede projection-specific validation. `ACHIEVED`, `PAUSED`, `CANCELLED`, and reserved Goal types return `NOT_APPLICABLE` without solver calls, basis/output validation, or Goal-current-amount provenance consumption.
- Active eligible Goals still reject basis/output mismatches and cross-Goal `GOAL_CURRENT_AMOUNT` provenance. Mathematical `ALREADY_ACHIEVED` remains exclusive to an ACTIVE Goal evaluated by `TargetAchievementSolver`.
- ADR-020 gained only the ordering clarification. No financial engine, Goals-domain, API, frontend, schema, migration, database, or persistence behavior changed.

### Verification
- Goal Planning: `63 collected`, `63 passed`; Required `40`; Target `32`; Projection `38`; Assumptions `63`; Read Foundation `12`; Goals `65`; Health `68`.
- General unit suite: `366 passed, 2 failed`; the two known historical Investments timeline tests still fail only on `MagicMock` versus `str` sorting.
- `10.3.6 = NOT STARTED`; no commit or push.

---

## [TSK-10.3.5-V2] — 2026-09-17 — Independent Goal Status Revalidation

### Status
`VALIDATED`

### Verification Performed (independent, no trust in 10.3.5-R report)
- **GoalStatus real enum:** Exactly 4 members: `ACTIVE`, `ACHIEVED`, `PAUSED`, `CANCELLED`. No hidden or extra members.
- **ACTIVE-only contract:** `_NON_PROJECTABLE_STATUSES = {ACHIEVED, PAUSED, CANCELLED}` correctly enforces ACTIVE as the sole projectable lifecycle status in the current domain.
- **ACHIEVED coverage confirmed:** `NOT_APPLICABLE` for initial below/equal/above target, missing basis, missing deadline, and `current_amount=None`. Solver calls = 0 in all cases.
- **ALREADY_ACHIEVED separation confirmed:** `GoalStatus.ACHIEVED` (lifecycle) and `GoalPlanningStatus.ALREADY_ACHIEVED` (mathematical) are distinct. ACTIVE + initial ≥ target → ALREADY_ACHIEVED (1 solver call). ACHIEVED never produces ALREADY_ACHIEVED (0 calls, mutation guard).
- **Code audit:** `goal_planning.py` contains zero financial math, zero IO, zero RequiredContributionSolver reference. No `ln`, `exp`, `Fisher`, `quantize`, `ROUND_HALF_EVEN`, `date.today`, `utcnow`, `Session`, or solver arithmetic.
- **Goals domain:** Untouched (`git diff HEAD -- backend/domain/enums/goal_status.py backend/domain/entities/ ...` returned empty).
- **ADR-020 clarification (DECISION_LOG.md line 321):** Confirmed. Records: ACTIVE-only eligibility, ACHIEVED = NOT_APPLICABLE, persisted ACHIEVED ≠ mathematical ALREADY_ACHIEVED, no reconciliation engine in 10.3.
- **Ordering:** `_require_matching_target_basis` fires before NOT_APPLICABLE gate (basis mismatch is a validation error regardless of type/status — confirmed by `test_explicit_basis_mismatch_is_invalid_even_for_non_projectable_goal`).
- **Cross-goal provenance:** Confirmed unchanged for ACTIVE Goals.
- **Contribution, deadline/horizon, nested UNREACHABLE, immutability, determinism:** All preserved.

### Test Counts (real, independently verified)
- Goal Planning collected: **54** | Executed: **54 passed**
- Required Solver: **40 passed** | Target Solver: **32 passed**
- Projection: **38 passed** | Assumptions: **63 passed** | Read: **12 passed**
- Goals: **65 passed** | Health (explicit): **68 passed** (`pytest backend/tests/domains/health`)
- General `tests/unit`: **357 passed, 2 failed** (historical Investments/MagicMock only — unchanged)

### Test Count Discrepancy (§41 mandatory audit)
- The 10.3.5-R report contained inconsistent text: stated "−1 removed + 9 added / net +8" but also "+6 net". The real result: 54 tests collected. The 10.3.5-R implementation removed 1 test and added 8 new tests (7 ACHIEVED contract + 1 separation proof §31). Net = +7 tests above the original 47-test baseline → 54. The discrepancy in the report's arithmetic was in the narrative text only; the test code and execution result are correct and consistent.

### Production Changes During V2
`NONE`

---

## [TSK-10.3.5-R] — 2026-09-17 — Goal Status Contract Reconciliation

### Context
Independent validation of 10.3.5 returned `BLOCKED — GOAL STATUS CONTRACT GAP`. The validation confirmed that `GoalStatus.ACHIEVED` is a persisted/manual lifecycle fact that does not prove `current_amount >= target_amount`, yet the prior implementation treated it as projectable (alongside `ACTIVE`). No approved contract existed for this behavior.

### Human Contract Decision
- `GoalStatus.ACTIVE` is the **only** lifecycle status eligible for forward Planning 10.3.
- `GoalStatus.ACHIEVED` → `GoalPlanningStatus.NOT_APPLICABLE`. `TargetAchievementSolver` is not called. No re-projection. No automatic conversion to `ALREADY_ACHIEVED`.
- `GoalStatus.PAUSED` → `NOT_APPLICABLE` (unchanged).
- `GoalStatus.CANCELLED` → `NOT_APPLICABLE` (unchanged).
- `GoalPlanningStatus.ALREADY_ACHIEVED` remains valid but is **strictly mathematical**: it may only arise from `TargetAchievementSolver` for a `ACTIVE` Goal when initial wealth ≥ target. It is not equivalent to and must not be inferred from `GoalStatus.ACHIEVED`.
- No reconciliation engine, status-mismatch detection, or automatic lifecycle correction is implemented.

### Changed
- `goal_planning.py`: Added `GoalStatus.ACHIEVED` to `_NON_PROJECTABLE_STATUSES`. Added module-level comment documenting the ACTIVE-only forward planning contract and the lifecycle/mathematical distinction.

### Tests Added / Updated
- Removed `test_active_and_persisted_achieved_statuses_use_mathematical_target_state` (encoded the contract gap).
- Added ACHIEVED coverage (6 mandatory + 1 mutation guard): `test_achieved_goal_with_initial_below_target_is_not_applicable`, `test_achieved_goal_with_initial_equal_target_is_not_applicable`, `test_achieved_goal_with_initial_above_target_is_not_applicable`, `test_achieved_goal_with_missing_basis_is_not_applicable_not_insufficient`, `test_achieved_goal_with_missing_deadline_is_not_applicable`, `test_achieved_goal_with_current_amount_none_is_not_applicable`, `test_achieved_status_never_produces_already_achieved`.
- Added separation proof: `test_active_goal_with_initial_at_target_produces_mathematical_already_achieved` (ACTIVE + initial ≥ target → mathematical ALREADY_ACHIEVED via solver, 1 solver call).

### ADR Change
- ADR-020 in `DECISION_LOG.md` updated with a "Goal status eligibility — TSK-10.3.5-R clarification (2026-09-17)" note recording the human contract decision.

### Validation
- Goal Planning: `54 passed` (was 48; +6 ACHIEVED contract tests, +1 separation proof, −1 removed gap test = net +6).
- Required/Target Solvers: `72 passed`. Projection/Assumptions: `101 passed`. Planning Read: `12 passed`. Goals: `65 passed`.
- General: `357 passed, 2 failed`; failures are the unchanged historical Investments MagicMock cases only. No new regression.
- `10.3.5 = RECONCILED / READY FOR REVALIDATION`. `10.3.6 = NOT STARTED`. No database, migration, Goal domain, API, frontend, or financial math was changed.
- ADR-020 updated. No new ADR created. No commit or push performed.

---

## [TSK-10.3.5] — 2026-09-17 — Goal Planning Integration

### Added
- Added immutable `TargetValueBasis`, `GoalPlanningStatus`, and `GoalPlanningResult` contracts plus a pure `GoalPlanningService` over the already validated Target Achievement Solver.
- Added explicit Goal/source/basis validation, cross-Goal current-amount provenance protection, approved Goal type/status eligibility, month-level early/on-time/late classification, and preservation of the complete nested solver result.
- Added 48 focused tests proving basis behavior, no target conversion, no automatic wealth selection/aggregation, no planned-to-scenario contribution copy, Goal deadline/horizon independence, all source identities, large Decimal values, immutability, determinism, and solver call counts.

### Validation
- Focused/regression results: Goal Planning `48 passed`; Required/Target Solvers `72 passed`; Projection/Assumptions `101 passed`; Planning Read `12 passed`; Goals `65 passed`; Health `68 passed`.
- General unit result: `351 passed, 2 failed`; failures are the unchanged historical Investments asset-detail timeline/MagicMock cases.
- `10.3.5 = IMPLEMENTED / READY FOR VALIDATION`; `10.3.6 = NOT STARTED`. No Required Contribution automation, scenario comparison, sustainable capacity, database, migration, API, frontend, Retirement/FIRE, or Portfolio Intelligence implementation was added.
- ADR-019 through ADR-022 remain unchanged. No commit or push was performed.

---

## [TSK-10.3.4-B-V] — 2026-09-17 — Independent Required Contribution Solver Validation

### Validated
- Independently audited the solver chain and confirmed that Required Contribution performs only exact Decimal/integer-cent conversion and binary-search orchestration over `TargetAchievementSolver` and `ForwardProjectionEngine`; no financial recurrence, target-basis conversion, Goal integration, scenario comparison, or sustainability semantics were introduced.
- Proved monotonicity independently for positive, zero, and negative monthly rates. Negative-rate validation covered adjacent-cent `ROUND_HALF_EVEN` ties, near-`-1` behavior, 90 small-domain combinations with 7,128 candidates, and exact agreement between brute-force first-success cents and production results.
- Proved `target_amount` is a constructive first-period upper bound because cent-scale pre-contribution wealth remains nonnegative for every monthly rate above `-1`; exercised 3,507 local cases and six source/mode/magnitude cases.
- Confirmed strict targets, three template contributions, exact `C`/`C - 0.01`, target-date and monthly horizons, nominal/real modes, all source identities, 101-digit negative-rate money against a 500-digit oracle, immutable provenance, determinism, and logarithmic target-solver call growth of 18/24/30.

### Validation
- No production or test change was required. Required Solver `40 passed`; Target Solver `32 passed`; Projection `38 passed`; Assumptions `63 passed`; Planning Read `12 passed`; Goals `65 passed`; Health `68 passed`.
- General unit result remains `303 passed, 2 failed`; both failures are the unchanged historical Investments timeline/MagicMock cases.
- `10.3.4-A = VALIDATED`; `10.3.4-B = VALIDATED`; macro `10.3.4 = VALIDATED`; `10.3.5 = READY / NOT STARTED`.
- ADR-019 through ADR-022 remain unchanged. No commit or push was performed.

---

## [TSK-10.3.4-B] — 2026-09-17 — Required Contribution Solver

### Added
- Added immutable `RequiredContributionStatus`/`RequiredContributionResult` contracts and a pure `RequiredContributionSolver` that treats the supplied assumptions as a template and delegates every candidate to `TargetAchievementSolver`.
- Added integer-cent monotonic binary search with zero-contribution short-circuiting, a mathematically safe `target_amount` upper bound, and explicit final verification that `C` succeeds while `C - 0.01` fails.
- Added 40 focused tests covering status semantics, strict Decimal targets, positive/negative/near-`-1` returns, `END_OF_MONTH`, `ROUND_HALF_EVEN`, nominal/real modes, target-date horizons, source/provenance independence, large magnitudes, monotonicity, logarithmic call count, immutability, and determinism.

### Validation
- Focused/regression results: Required Contribution `40 passed`; Target Solver `32 passed`; Projection `38 passed`; Assumptions `63 passed`; Planning Read `12 passed`; Goals `65 passed`; Health `68 passed`.
- General unit result: `303 passed, 2 failed`; failures are the unchanged historical Investments asset-detail timeline/MagicMock cases.
- `10.3.4-A = VALIDATED`; `10.3.4-B = IMPLEMENTED / READY FOR VALIDATION`; macro 10.3.4 remains incomplete pending independent validation; `10.3.5 = NOT STARTED`.
- No database, migration, API, frontend, Goal integration, scenario comparison, Retirement/FIRE, or Portfolio Intelligence behavior was added. ADR-019 through ADR-022 remain unchanged.

---

## [TSK-10.3.4-A-V] — 2026-09-17 — Independent Target Achievement Solver Validation

### Validated
- Independently audited the four approved statuses, strict positive finite cent-scale Decimal target boundary, period-zero representation, exact first crossing, engine call counts, conservative impossibility proofs, horizon-exhaustion distinction, output-basis neutrality, and complete result consistency.
- External probes covered literal scale behavior through rejected `Decimal("1.000")`, nominal/nominal, nominal/real and real/real targets without conversion, horizons 1 and 1,200, 221-digit money, all initial-wealth origins, provenance, immutable inputs/results, and deterministic repetitions. Source inspection found no duplicated financial or calendar mathematics.
- Existing tests kill the critical `>`/last-crossing/overbroad-unreachable/wrong-date/repeated-engine-call mutations, so no validation test or production change was required.
- Target Solver `32 passed`; Projection `38 passed`; Assumptions `63 passed`; Planning Read `12 passed`; Goals `65 passed`; Health `68 passed`; general unit `263 passed, 2 failed`, limited to the unchanged historical Investments timeline/MagicMock failures.

### Status
- `10.3.4-A = VALIDATED`.
- `10.3.4-B = READY / NOT STARTED`; 10.3.4 remains incomplete and 10.3.5 was not promoted.
- ADR-019 through ADR-022 remain unchanged.

---

## [TSK-10.3.4-A] — 2026-09-17 — Target Achievement Solver

### Implemented
- Added a pure immutable Decimal `TargetAchievementSolver` that validates a positive finite cent-scale target, returns period-zero `ALREADY_ACHIEVED` without projecting, and otherwise scans exactly one complete validated `ForwardProjectionEngine` result for the first `ending_wealth >= target_amount` crossing.
- Added the four approved mathematical statuses, complete fact/assumption/projection audit references, projection-owned achievement dates, and conservative `UNREACHABLE` proofs limited to zero-contribution paths that cannot grow. Targets are compared in the projection output basis without nominal/real conversion.
- Added 32 focused tests for exact and overshoot crossings, positive/negative/real modes, unreachable versus horizon exhaustion, target-date reuse, source independence, determinism, immutability, strict Decimal validation, one engine call, and more-than-200-digit money.

### Validation
- Projection `38 passed`; assumptions `63 passed`; Planning Read `12 passed`; Goals `65 passed`; Health `68 passed`; general unit `263 passed, 2 failed`, limited to the unchanged historical Investments timeline/MagicMock failures.

### Status
- `10.3.4-A = IMPLEMENTED / READY FOR VALIDATION`.
- `10.3.4-B = NOT STARTED`; no required-contribution search, Goal integration, scenario comparison, database, API, frontend, Retirement/FIRE, or Portfolio Intelligence behavior was added.

---

## [TSK-10.3.3-V2] — 2026-09-17 — Independent Numerical Revalidation

### Validated
- Independently revalidated the adaptive precision derivation, monotonicity, cent-level rate accuracy, local Decimal exponent context, deterministic recurrence, and accounting/summary invariants without changing production or tests.
- Matched an independent 800-digit Newton/cent oracle across every blocker period, including 439/440, and across large initial wealth, dominating contribution, combined magnitude, rates 2.5/10/25/100, Fisher, real/real, zero-real, deflation, and negative/near-`-1` cases.
- Mutation-style probes proved that an 80-digit rate still diverges at period 440 even when money arithmetic is adaptive, while adaptive rate with 80-digit money still fails at period 452. The permanent extreme regression therefore protects both halves of the former defect.
- Projection `38 passed`; assumptions `63 passed`; Planning Read `12 passed`; Goals `65 passed`; Health `68 passed`; general unit `231 passed, 2 failed`, limited to the unchanged historical Investments timeline/MagicMock failures.

### Status
- `10.3.3 = VALIDATED`.
- `10.3.4 = READY / NOT STARTED`.
- ADR-020 remains unchanged; no production/test code, solver, Goal integration, scenario, API, frontend, database, Retirement/FIRE, or Portfolio Intelligence behavior changed.

---

## [TSK-10.3.3-R] — 2026-09-17 — Forward Projection Numerical Precision Reconciliation

### Reconciled
- Reproduced the valid annual-rate `100` / 1,200-month failure at period 452 and confirmed cent drift already began at period 440 under the fixed 80-digit context.
- Replaced fixed calculation precision as a ceiling with a deterministic local budget derived from initial wealth, contribution, annual growth-factor magnitude, and horizon. The engine retains an 80-digit floor, cent scale, 34 guard digits, `ROUND_HALF_EVEN`, and the stdlib Decimal native exponent range.
- Added a 500-digit independent Newton/cent oracle for the original blocker. All 1,200 monetary periods now match exactly; the final balance has 204 integer digits and the scenario completes without exception in approximately 0.02 seconds on the validation environment.
- Projection tests now report `38 passed`; assumptions `63 passed`, Planning Read `12 passed`, Goals `65 passed`, and Health `68 passed`. General unit regression reports `231 passed, 2 failed`, limited to the unchanged historical Investments timeline/MagicMock failures.

### Status
- `10.3.3 = RECONCILED / READY FOR REVALIDATION`.
- `10.3.4 = NOT STARTED`; no solver, Goal integration, scenario, API, frontend, persistence, Retirement/FIRE, or Portfolio Intelligence implementation was added.
- ADR-020 remains unchanged.

---

## [TSK-10.3.3] — 2026-09-17 — Forward Projection Engine

### Implemented
- Added a pure immutable Forward Projection Engine over one explicit `InitialWealthFact` and validated `ProjectionAssumptions`, with no database, reader, HTTP, API, or wall-clock dependency.
- Added isolated 80-digit Decimal rate mathematics: direct nominal/real modes, one-time Fisher conversion, and compound-equivalent monthly conversion through stdlib Decimal `ln`/`exp`; zero annual rate remains exactly zero.
- Added `END_OF_MONTH` monthly recurrence, cent-scale `ROUND_HALF_EVEN` projected returns, real calendar month ends, immutable period tuples/results, preserved source/provenance, and exact cumulative contribution/growth invariants.
- Added 34 projection tests with hardcoded 100-digit rate constants and a test-local independent recurrence. The general unit suite reports `227 passed, 2 failed`, limited to the unchanged historical Investments timeline/MagicMock failures.

### Status
- `10.3.3 = IMPLEMENTED / READY FOR VALIDATION`.
- No target/contribution solver, Goal integration, scenario comparison/persistence, database, migration, API, frontend, Retirement/FIRE, or Portfolio Intelligence implementation was added.

---

## [TSK-10.3.2-V] — 2026-09-17 — Independent Projection Assumptions Validation

### Validated
- Independently reconciled ADRs 019–022 against the assumptions, facts/readers, exports, and both Planning test suites.
- Challenged strict types, Decimal scale/precision and domains, matrix A–H, immutable/fixed contract identities, horizon XOR, month-level calendar behavior, leap year, and exact 1,200/1,201 limits without modifying production or test code.
- Repeated assumptions (`63 passed`), Planning Read (`12 passed`), Goals (`65 passed`), Health (`68 passed`), and general unit regression (`193 passed, 2 failed`). The two failures remain the identical historical Investments timeline/MagicMock baseline.

### Status
- `10.3.2 = VALIDATED`.
- `10.3.3 = READY / NOT STARTED`.
- No database, migration, API, frontend, rate conversion, Fisher calculation, projection engine, solver, scenario, Retirement/FIRE, or Portfolio Intelligence implementation changed.

---

## [TSK-10.3.2] — 2026-09-17 — Projection Assumptions Contract

### Implemented
- Added immutable typed Planning assumptions with explicit `EFFECTIVE_ANNUAL`, nominal/real, and `END_OF_MONTH` identities.
- Enforced strict Decimal inputs, non-negative cent-scale scenario contribution, finite return/inflation rates greater than `-1` without arbitrary positive caps, and the approved nominal/real inflation matrix.
- Enforced one explicit 1–1,200-month horizon source and centralized deterministic `YYYY-MM` target-date resolution, including partial-month and cross-year behavior.
- Added 63 assumptions tests; Planning Read, Goals, and Health regressions pass. The general unit suite reports `193 passed, 2 failed`, limited to the unchanged historical Investments timeline/MagicMock failures.

### Status
- `10.3.2 = IMPLEMENTED / READY FOR VALIDATION`.
- No rate conversion, Fisher calculation, projection engine, solver, scenario comparison/persistence, database, API, frontend, Retirement/FIRE, or Portfolio Intelligence implementation was added.

---

## [TSK-10.3.1-V] — 2026-09-16 — Independent Planning Read Foundation Validation

### Validated
- Independently reconciled ADR-019 against immutable Planning facts, Goal/portfolio readers, certified Health reuse, SQLAlchemy models, controlled fixtures, and the live SQLite database opened in read-only mode.
- Confirmed Decimal end-to-end, Goal ownership, `NULL` versus zero, explicit and isolated portfolio account scope, composite snapshot identity, typed provenance, gap preservation, no staleness invention, no automatic source resolution, no double counting, and read-only session state.
- Repeated Planning (`12 passed`), Goals (`65 passed`), Health (`68 passed`), and general unit regression (`130 passed, 2 failed`). The two failures remain the identical historical Investments timeline/MagicMock baseline.

### Status
- `10.3.1 = VALIDATED`.
- `10.3.2 = READY / NOT STARTED`.
- Validation changed documentation only; no production/test code, migration, API, frontend, projection mathematics, scenario implementation, Retirement/FIRE, or Portfolio Intelligence behavior changed.

---

## [TSK-10.3.1] — 2026-09-16 — Planning Read Foundation

### Implemented
- Added immutable Planning facts for the three approved initial-wealth origin identities, typed scope/as-of/provenance, and Decimal-safe Goal facts.
- Added an owned Goal reader that filters by `goal_id + user_id`, bypasses the legacy float entity/DTO path, preserves `NULL` versus explicit zero, and never executes `assumptions_json`.
- Added an explicit-account portfolio reader that selects the latest canonical `reference_month` for only that account, preserves MyProfit source/run/update provenance, labels the scope as investment portfolio, and never sums positions or valuations.
- Added a thin Health adapter over `HealthFinancialQuery` and `HistoricalFinancialMetricsService`, preserving realized savings semantics and historical gaps.

### Validated Locally
- Planning: `12 passed`; Goals: `65 passed`; Health: `68 passed`.
- General unit baseline: `130 passed, 2 failed`; both failures are the unchanged Investments asset-detail timeline/MagicMock baseline.
- Read-only live checks returned Goal `113000.00`, MyProfit portfolio `112888.91` at `2026-09`, and August 2026 Health metrics identical to the certified Health layer. All captured statements were `SELECT`; Goal and portfolio remained separate origins with no automatic sum.

### Status
- `10.3.1 = IMPLEMENTED / READY FOR VALIDATION`.
- No projection/rate/inflation/solver/scenario engine, API, frontend, migration, scenario persistence, Retirement/FIRE, or Portfolio Intelligence implementation was added.

---

## [TSK-10.3.0-A] — 2026-09-16 — Planning Contract Approval and ADR Lock

### Approved
- Added ADR-019 through ADR-022 for the Planning input/source boundary, the shared monthly mathematical contract, scenario semantics/lifecycle, and the combined Retirement/FIRE plus Portfolio Intelligence phase boundaries.
- Locked explicit initial-wealth origins, no-double-counting/provenance rules, the Goals Decimal read boundary, four independent contribution concepts, `END_OF_MONTH` timing, partial-month period zero, effective-annual Decimal rates with no arbitrary positive cap, compound monthly conversion, negative-return support, and the nominal/real/inflation validation matrix.
- Locked the 1–1,200-month horizon, month-level target dates, 34-digit Decimal context, monthly cent-scale `ROUND_HALF_EVEN` recurrence, forward output/equation, target-date states, and cent-discrete required-contribution solver using the Forward Projection Engine as its only production oracle.
- Locked editable `CONSERVATIVE`/`BASE`/`OPTIMISTIC` labels without rates, historical-data-not-forecast, transient-first scenarios, Goal timing/eligibility, and null months-saved/lost when temporal comparison is not applicable.

### Deferred / Boundaries
- `sustainable_monthly_contribution_capacity` remains `DEFERRED — CONTRACT NOT APPROVED` in 10.3.7; Planning MVP uses explicit `scenario_monthly_contribution`.
- Phase 10.4 is now canonically `Retirement & Financial Independence (FIRE)` and reuses 10.3 engines. Phase 10.5 remains Portfolio Intelligence. Both are boundary definitions only; neither was implemented.

### Status
- `10.3.0 = VALIDATED`.
- `10.3.1 — Planning Read Foundation = READY / NOT STARTED`.
- Documentation only. No production code, schema, migration, DTO, service, engine, endpoint, UI, database data, Retirement/FIRE, or Portfolio Intelligence implementation changed.

---

## [TSK-TRANSITION-10.2-TO-10.3] — 2026-09-16 — Post-Merge Checkpoint and Planning Decomposition

### Verified
- GitHub PR #2 merged `develop` into `main` at `b7ce8b8`; approved Goals/Health commit `2006e0f` is an ancestor of the merge.
- Local and remote `main`/`develop` were fast-forwarded to the same post-merge checkpoint without rebase, reset, or a new local merge commit.
- Phase 10.2 is `COMPLETED / MERGED`; 10.2.10-C remains `VALIDATED`.

### Planned
- Phase 10.3 is `PLANNED / NOT STARTED`, decomposed into microprocesses 10.3.0–10.3.12 in `IMPLEMENTATION_ROADMAP.md`.
- Planning remains deterministic and contract-first. It separates realized surplus, sustainable contribution capacity, and user-defined scenario contribution; keeps FIRE in 10.4 and portfolio recommendations in 10.5; and requires Decimal-safe read inputs before any engine.
- Scenario delivery is staged: transient comparisons first, persistence only after an approved lifecycle/data contract.

### Scope
- Documentation only. No Planning code, schema, migration, DTO, endpoint, frontend, calculation, or scenario engine was implemented.

---

## [PHASE-10.2-CLOSE] — 2026-09-15 — Financial Health Phase Closure

### Reviewed
- Independent release review verdict: `PASS WITH NON-BLOCKING NOTES`; no blockers, no HIGH findings, and LOW release risk.

### Fixed
- Corrected M-01 so trend periods read chronologically from `comparison_month` to `trend_target_month` (for example, `jul/26 → ago/26`) without changing backend semantics or calculations.

### Validated
- Health suite: `68 passed`. General baseline: `118 passed, 2 failed`, limited to the two historical Investments timeline/MagicMock tests. TypeScript, Health-targeted ESLint, production build, and Git whitespace validation pass.

### Status
- 10.2.10-C is `VALIDATED`; Phase 10.2 Financial Health is `COMPLETED`; Phase 10.3 Planning & Projection is `NOT STARTED / NEXT`.
- Sustainable contribution capacity, investment capacity, and composite financial stability remain formally deferred to their approved future boundaries.

---

## [10.2.10-C-UX2] — 2026-09-15 — Financial Health Visual Identity

### Improved
- Added an exact-label deterministic Health category accent resolver backed by a controlled ten-color muted palette. Category dots/bars and category-trend card accents now retain the same identity independently of rank, month, value, or trend state.
- Added restrained metric identity to income, expense, net-cashflow, and savings-rate KPI cards. Historical rows now use subtle zebra striping and metric-consistent text accents, with sign-sensitive net-cashflow and savings-rate values.
- Strengthened category-trend numeric hierarchy: current values remain primary, while absolute and relative deltas use mathematical increase/decrease/neutral presentation colors independently from category and status accents.

### Validated
- TypeScript, targeted Health ESLint, and the Next.js production build pass. Backend, financial contracts, pagination, trend ordering, and anomaly semantics remain unchanged.

### Status
- 10.2.10-C remains `IMPLEMENTED / READY FOR FINAL VISUAL VALIDATION`. Phase 10.2 remains open.

---

## [10.2.10-C-UX] — 2026-09-15 — Financial Health Visual Information Design Polish

### Improved
- Consolidated requested/comparison months into one compact temporal context and replaced repeated card sentences with visual trend badges, signed deltas, and presentation-only semantic color.
- Added client-side history pagination at 12 chronological rows per page, opening on the latest records and resetting when the selected reference month changes; the chart remains limited to the latest six returned records.
- Redesigned category trends into compact, responsive cards with status badges, clearer numeric hierarchy, six-item initial disclosure, and full ordered detail on demand. Removed implementation-language microcopy from the user interface.

### Validated
- TypeScript, targeted Health ESLint, and the Next.js production build pass. Backend, API contracts, financial calculations, and stability scope were untouched.

### Status
- 10.2.10-C is `IMPLEMENTED / READY FOR FINAL VISUAL VALIDATION`. Phase 10.2 remains open.

---

## [10.2.10-C] — 2026-09-15 — Trend API/UI Exposure

### Added
- Authenticated `GET /api/v1/financial-health/trends?reference_month=YYYY-MM` with shared reference-month validation, an explicit API-boundary current-month resolver, certified Health history/category orchestration, and ADR-018 DTO-to-HTTP serialization.
- Typed Health frontend trend contract and a fifth request inside the existing race-protected batch. Summary cards label the closed comparison period and present savings-rate absolute change in percentage points; an expandable secondary panel presents the complete certified category order without mixing it with partial requested-month category values.
- Eight API tests covering auth, partial/closed month resolution, JSON Decimal strings/null, `NEW`, `DISAPPEARED`, null percentage, insufficient data, invalid input, and OpenAPI presence.

### Validated
- Authenticated real-ledger API response for Sep/2026 returned `2026-08` versus `2026-07`, all four validated global facts, and the complete 24-item category union.
- Health suite: `68 passed`; TypeScript, targeted Health lint, and production build pass. General unit baseline remains `118 passed, 2 failed`, exclusively the known Investments MagicMock/timeline failures.

### Status
- 10.2.10-C is `IMPLEMENTED / READY FOR USER VALIDATION`. Stability remains `NOT IMPLEMENTED — CONTRACT PENDING`; Phase 10.2 remains open.

---

## [10.2.10-B-V] — 2026-09-15 — Independent Trend Engine Validation

### Validated
- ADR-018 compliance and engine purity: `FinancialTrendService` consumes only certified DTO facts, retains `Decimal`, and has no database, transaction, RAW, Pierre, Investments, anomaly, narrative, API, or UI dependency.
- A separate read-only SQLite plus Python `Decimal` oracle reconciled all four Jul→Aug/2026 global facts and all 24 categories in the exact-label union. Cross-year Dec/2025→Jan/2026, partial-month resolution, insufficient first month, gap, negative, zero, unchanged, undefined-rate, invalid-input, and duplicate-input behavior also passed.
- Health suite: `60 passed`. General unit baseline: `118 passed, 2 failed`; both failures remain the documented Investments MagicMock/timeline failures and no new regression occurred.

### Status
- 10.2.10-B is `VALIDATED`; 10.2.10-C is `NOT STARTED / NEXT`. API/UI trend exposure remains unimplemented and stability remains `NOT IMPLEMENTED — CONTRACT PENDING`. Phase 10.2 remains open.

---

## [10.2.10-B] — 2026-09-14 — Deterministic Global and Category Trend Engine

### Added
- `FinancialTrendService` with typed global/category summaries, metric and direction enums, exact Decimal deltas, explicit current-month resolution, strict consecutive-month lookup, and non-exceptional `INSUFFICIENT_DATA` results.
- Exact-label category union with deterministic target-first ordering, `NEW`/`DISAPPEARED` presence semantics, and explicit-zero preservation. ADR-015 anomaly types and thresholds remain independent and unchanged.
- `test_financial_trend_service.py` with 13 tests covering the 22 required temporal, global, category, and precision behaviors.

### Validated
- Full Health suite: `60 passed`. General unit baseline: `118 passed, 2 failed`, with only the two known Investments MagicMock/timeline failures.
- Read-only production-query versus independent SQLite Decimal validation passed for all four Jul→Aug global metrics, all 24 categories in the union, Dec/2025→Jan/2026 continuity, missing 2025-04, and Decimal types.

### Status
- 10.2.10-B is `IMPLEMENTED / READY FOR VALIDATION`. API/UI exposure is not implemented. Stability remains `NOT IMPLEMENTED — CONTRACT PENDING`.

---

## [10.2.10-A] — 2026-09-14 — Financial Trend and Stability Readiness Contract Lock

### Audited
- A read-only audit of `database/fin_analytics.db` found 1,420 transactions: 1,420 `CLASSIFIED`, 0 `PENDING`, 341 `ENTRADA`, 898 `SAIDA`, and 181 `IGNORAR`.
- The current governed ledger covers 17 consecutive calendar months from `2025-05` through partial `2026-09`, including 16 continuous closed months through `2026-08`. Earlier reports based on partial governance remain historical evidence and are not current baselines.

### Approved
- ADR-018 locks consecutive closed-month global trends for income, expense, net cashflow, and savings rate; exact-label category trends; factual budget-pressure composition; and Decimal/absence semantics.
- `savings_amount` remains realized surplus/deficit. Sustainable contribution capacity is deferred to Planning, and investment capacity to Planning/Portfolio Intelligence.
- The ledger is ready for a simple deterministic stability-facts contract, but no formula, weighting, or composite score is approved. The executable stability contract remains a gate for 10.2.10-C.

### Status
- 10.2.10-A is `VALIDATED`; 10.2.10-B Deterministic Global & Category Trend Engine is `NOT STARTED / NEXT`. Phase 10.2 and final QA remain open.
- Documentation only; backend, frontend, tests, schema, migrations, and database data were not changed.

---

## [10.2.10-PREP] — 2026-09-14 — Final Manual Validation / Visual QA Preparation

### Closed
- 10.2.9 integration and stabilization is `VALIDATED`: backend and frontend contracts, Decimal handling, data freshness, navigation, race-condition protection, automated suites, build, HTTP smoke, and OpenAPI checks passed without a Financial Health blocker.

### Prepared
- 10.2.10 is `IN PROGRESS / READY FOR USER FINAL QA`. The final manual checklist covers navigation, populated and empty months, rapid month switching, analytical sections, UTF-8, console behavior, desktop usability, Goals smoke, and the Wealth Intelligence hub.
- Phase 10.2 remains open until explicit user sign-off. No feature, financial rule, backend contract, schema, or database data changed during this preparation.

### Accepted Non-Blocking Debt
- Global mobile responsiveness, repository-wide lint debt, the Recharts SSR dimension warning, the ADR-014 Alembic FK mismatch, and the two historical Investments test failures remain unchanged.

---

## [10.2.9] — 2026-09-14 — Financial Health Integration and Stabilization

### Stabilized
- Audited the complete governed-data-to-UI chain and confirmed backend response models match frontend TypeScript contracts, Decimal strings remain presentation-only in the browser, navigation/auth are shared, and live Health requests bypass frontend caching.
- Added request sequencing to the Financial Health page so rapid month changes cannot let an obsolete four-endpoint response batch overwrite the latest selection. Removed the now-unused Health panel description path created during the UI phase.

### Validated
- 47 Health tests passed. The general unit suite retained exactly the two historical Investments MagicMock/timeline failures (`118 passed, 2 failed`). TypeScript, targeted Health lint, production build, real-data HTTP smoke, application startup through TestClient, and all four OpenAPI routes passed.
- September/2026 current-ledger smoke returned six historical records, 11 categories, and the certified `SPIKE` signals `Transferências` and `Serviços`; financial amounts remain live and are not hardcoded.

### Technical Debt
- Global mobile responsiveness, repository-wide lint debt, the Recharts SSR dimension warning, the ADR-014 Alembic FK mismatch, and the two historical Investments test failures remain non-blocking and unchanged.

### Next
- 10.2.9 is `VALIDATED`; 10.2.10 is `IN PROGRESS / READY FOR USER FINAL QA`.

---

## [10.2.8] — 2026-09-14 — Financial Health Analytical UI

### Added
- Responsive analytical summary cards with API-provided recent averages, a Recharts monthly cashflow view plus exact-value table, proportional category ranking, and explainable anomaly cards with secondary non-anomaly states.
- Layout-specific skeletons and refined error, empty-data, and insufficient-baseline presentation with basic semantic and keyboard accessibility.

### Validated
- Targeted ESLint, TypeScript typecheck, and the production Next.js build pass. Financial values and classifications remain API-derived; the client performs presentation formatting only.

### UI Polish and Manual Validation
- 10.2.8-A limited the chart to the latest six returned records while retaining the full history table, corrected anomaly-card and long-label reflow, restored the Health TopNav color marker, and aligned the Wealth Intelligence hub card icon. No backend contract changed.
- Manual browser validation passed for populated and empty months, history windows, anomaly cards, labels, navigation, and console behavior. 10.2.8 is `VALIDATED`; integration/stabilization 10.2.9 remains NOT STARTED / NEXT.

---

## [10.2.7] — 2026-09-14 — Financial Health Frontend Foundation

### Validated
- Manual browser validation with the real backend and frontend confirmed authentication, reference-month selection, cashflow, history, category ranking, anomaly signals, UTF-8 labels, consolidated scope, and Wealth Intelligence navigation.

---

## [10.2.6] — 2026-09-13 — Financial Health API

### Added
- Authenticated read-only endpoints under `/api/v1/financial-health`: `cashflow`, `history`, `categories`, and `anomalies`, all requiring `reference_month=YYYY-MM` and deliberately exposing no account filter.
- Typed response schemas that preserve domain `Decimal` values as JSON strings and domain `None` as JSON `null`.

### Validated
- HTTP tests cover authentication, query validation, cashflow, chronological history/gaps, categories, anomalies, insufficient baseline, and Decimal serialization.
- Manual authenticated validation confirmed all four endpoints, 401 without credentials, and 422 for an invalid `reference_month`.
- Live reconciliation confirmed that the API, `HealthFinancialQuery`, and independent SQLite Decimal aggregation agree against the current ledger. September/2026 values may legitimately change as transactions are classified; no financial values are hardcoded. UTF-8 JSON labels and the historical response schema were also verified.

### Deferred / Out of Scope
- Frontend, persistence, alerts, new calculations, and account-level filters remain out of scope.

---

## [10.2.5] — 2026-09-12 — Spending Anomaly Engine

### Added
- `SpendingAnomalyService` plus typed month input, evaluation, summary, category-state, and global-status contracts, all operating only on certified pre-consolidated category data.
- Deterministic ADR-015 handling for continuous three-month baseline availability, exact category matching, two-of-three historical presence, present-value arithmetic means, inclusive R$50 baseline floor, strict 1.5x SPIKE threshold, and inclusive R$100 NEW_EXPENSE threshold.

### Validated
- Unit coverage for all approved boundaries, explicit-zero semantics, missing/non-continuous baseline, Decimal preservation, and anomaly collection filtering.
- Independent read-only September/2026 comparison against June-August/2026 category aggregates. `Transferências` and `Serviços` were the only `SPIKE` signals; no `NEW_EXPENSE` was produced.
- Independent validation closed 10.2.5 as `VALIDATED`; the Health suite passed 39 tests and the unit suite retained only the two historical Investments mock/timeline failures.

### Deferred / Out of Scope
- API, persistence, alerts, severity, trends, forecasts, category normalization, and AI remain out of scope.

---

## [10.2.5-PRE] — 2026-09-12 — Anomaly Contract Lock

### Governance
- Closed 10.2.4 as VALIDATED after independent real-data validation of September/2026 category totals, ranking, shares, Decimal precision, zero/empty behavior, duplicate rejection, and label preservation.
- ADR-015 is APPROVED. It locks the three-month continuous closed baseline, category presence semantics, two-of-three history rule, mean reference over present certified values, inclusive R$50 baseline floor, strict 1.5x SPIKE operator, and inclusive R$100 NEW_EXPENSE threshold.
- At this preparatory point, 10.2.5 remained NOT STARTED / NEXT and no anomaly implementation had been added.

---

## [10.2.4] — 2026-09-12 — Category Expense Intelligence

### Added
- `CategoryExpenseIntelligenceService` plus typed certified input, ranked category metric, and summary DTOs.
- Deterministic total, analytical share, sequential ranking, lexicographic tie-break, and top-category behavior without label normalization.

### Contract
- Empty input returns total `Decimal('0.00')`, no categories, and no top category; explicit zero categories remain ranked records with `None` shares.
- Duplicate category input fails fast with `ValueError`; concentration measures, historical comparisons, normalization, and anomalies remain deferred.

### Validated
- Read-only September/2026 validation found 10 certified expense categories totaling `4486.90`; independent SQL Decimal aggregation reproduced the category totals, ranking, shares, and top category.

---

## [10.2.3] — 2026-09-12 — Historical Financial Metrics

### Added
- `HistoricalFinancialMetricsService`, `MonthlyCashflowPeriodDTO`, and `MonthlyFinancialMetricsDTO` for a deterministic chronological series built from certified monthly totals.
- Coverage for ordering, monthly cashflow reuse, deficits, zero income, explicit zero months, empty history, gaps, Decimal preservation, and duplicate-month rejection.

### Contract
- The service does not query the database and never synthesizes absent months; `2025-06` to `2026-06` remains a gap in real data.
- Duplicate `reference_month` input fails fast with `ValueError`; monthly totals must already be consolidated by `HealthFinancialQuery`.
- At that implementation point, month-over-month comparisons, rolling averages, trends, and insufficient-data classification were deferred because their formal contracts were absent. ADR-018 later superseded that contract gap for deterministic month-over-month trends; rolling averages remain outside the locked scope.

### Validated
- Read-only database validation produced six real months in chronological order: `2025-05`, `2025-06`, `2026-06`, `2026-07`, `2026-08`, and `2026-09`.
- Independent validation also confirmed chronological ordering, gap preservation, absent-versus-zero behavior, duplicate rejection, Decimal precision, mathematical invariants, and regression baseline.

---

## [10.2.2-A] — 2026-09-12 — Financial Decimal Precision Correction

### Fixed
- SQLite returns `SUM(ABS(transactions.amount))` as a binary `float` despite the persisted `NUMERIC(12,2)` amount scale. `HealthFinancialQuery` now normalizes all monetary aggregates (`get_cashflow`, `get_monthly_totals`, and `get_category_expenses`) once at the read boundary to cent-scale `Decimal` values.
- Added regression coverage for the SQLite `0.10 + 0.20` aggregate artifact, including exact `Decimal` type assertions for cashflow, monthly, and category outputs.

### Validated
- Independent read-only real-data validation reproduces the certified September/2026 totals and June-August/2026 baseline exactly in `Decimal`; the corrected baseline averages are income `10775.61`, expense `6285.22`, and net cashflow `4490.39`.
- Savings rate remains an unrounded analytical fraction; no presentation rounding was added.

---

## [10.2.2] — 2026-09-12 — Cashflow Metrics Engine

### Added
- `CashflowMetricsService` and typed `CashflowSummaryDTO` / `MonthlyCashflowDTO` for deterministic certified cashflow metrics.
- Decimal-based total, net cashflow, savings, savings-rate, and supplied-month average calculations.
- Unit coverage for positive, deficit, zero-income, zero-value, equal-value, single/multiple-month, empty-month collection, and Decimal precision cases.

### Contract
- `savings_amount = net_cashflow`.
- `savings_rate = None` when income is zero.
- At that implementation point, expense trend was deferred because no formal trend contract existed. ADR-018 later superseded this limitation.
- 10.2.3 remains NOT STARTED / NEXT.

---

## [10.2.1-A] — 2026-09-12 — Financial Health Contract & Documentation Stabilization

### Validated
- Financial Health uses consolidated account scope for the local single-tenant database.
- Operational baseline: three continuous closed months before the analysed month; for September/2026, June through August.
- September/2026 SQL validation: income 2203.90, expenses 4486.90, and 10 `CLASSIFIED` `SAIDA` categories.
- `HealthFinancialQuery` read foundation and its multi-account consolidation test.

### Status Alignment
- Phase 10.1 Goals: IMPLEMENTED / VALIDATED.
- Phase 10.2.0: COMPLETED.
- Phase 10.2.1: IMPLEMENTED / VALIDATED.
- Phase 10.2.2: NOT STARTED / NEXT.

### Scope Protection
- No production Financial Health logic, schema, migrations, API, frontend, Goals, Investments, Pierre, or database data changed.
- Worktree remains intentionally uncommitted pending human validation.

---

## [10.0.0] — 2026-09-08 — Architecture & Product Design

### Added — Documentation (project/wealth-intelligence/)
- `README.md` — project overview, stack, getting started, phase index
- `MASTER_PLAN.md` — vision, phase roadmap, pre-work blockers, decision index
- `CURRENT_STATE.md` — verified reality of repository (post full audit)
- `ARCHITECTURE.md` — current + target architecture, 8-layer data pipeline model
- `AI_AND_LLM.md` — LLM provider design, Ollama evaluation, prompt safety, multi-agent analysis
- `DATA_AND_SOURCE_OF_TRUTH.md` — source of truth matrix, data authority rules
- `DECISION_LOG.md` — 13 Architecture Decision Records (ADRs 001-013)
- `IMPLEMENTATION_ROADMAP.md` — phase contracts (10.1–10.12), scope, tests, acceptance criteria
- `UI_UX_PLAN.md` — 11-page module designs, navigation architecture, design system
- `SECURITY_AND_GOVERNANCE.md` — prompt injection defense, financial data security, AI governance
- `INFRASTRUCTURE.md` — Docker strategy, Ollama native host rationale, deployment options
- `TESTING_STRATEGY.md` — test categories, structure, per-phase requirements, validation checklist
- `CHANGELOG.md` — this file
- `audits/REPOSITORY_AUDIT.md` — full verified backend, DB, frontend, AI infrastructure audit
- `audits/EXTERNAL_DATA_ECOSYSTEM.md` — external data source research and decisions
- `audits/ENV_VARIABLE_INVENTORY.md` — current + proposed env variable inventory
- `audits/DEPENDENCY_ROADMAP.md` — dependency installation plan per phase
- `audits/FINAL_PRODUCT_DEFINITION.md` — product vision and user experience narrative

### Discovered — Critical Issues
- **BLOCKER:** Dual `position_snapshots` schema (migration 013 vs ORM PositionSnapshotModel) must be resolved before Phase 10.1
- **P2:** `requirements.txt` is incomplete (missing pydantic-settings, aiosqlite, python-jose, passlib)
- **P2:** `GEMINI_API_KEY` integration files are empty (0 bytes) — database scaffold only

### Verified — Repository Baseline
- 9 active FastAPI routers (investments, dashboard, Pierre, governance, goals, auth, accounts, transactions, governance API)
- 17 database migrations applied to SQLite WAL database
- YFinanceProvider fully implemented with MarketDataProvider Protocol abstraction
- Pierre Finance + MyProfit CSV import pipelines fully operational
- Next.js frontend with complete /wealth module (5 sub-pages)
- Goals domain: basic CRUD only, missing critical fields for Wealth Intelligence
- AI infrastructure: database schema only, all integration files empty

### No Code Changed
This phase is documentation-only. No backend, frontend, or database changes were made.

---

## [3.1.0-investments] — Previous Baseline

Prior version. Stable investments module. Pierre Finance + MyProfit integration operational. Goals stub introduced. AI prompt versioning DB scaffold added.
## [TSK-10.3.9-R1] — 2026-09-23 — Planning Nominal/Real Form Reconciliation

- Inflation is visible and sent only for `NOMINAL → REAL`; hidden combinations clear stale input and send `inflation_rate: null`.
- `REAL → NOMINAL` is unavailable. No rate conversion or other financial calculation was added.
- Automatic portfolio wealth remains deferred pending an authenticated ownership/source contract. Swagger Authorize manual smoke remains `DEFERRED BY USER`.
- `10.3.9 = RECONCILED / READY FOR FINAL MANUAL UI SMOKE`; `10.3.10 = READY / NOT STARTED`.
## [TSK-10.3.10] — 2026-09-24 — Planning Analytical UI

- Closed 10.3.9 as `VALIDATED`: manual Nominal→Nominal, Real→Real, Nominal→Real, and unavailable Real→Nominal smoke cases passed.
- Added analytical UI capabilities for Projection, Target Achievement, Required Contribution, owned Goal Planning, and ordered Scenario Comparison through the certified Planning client.
- Added certified period charts and scenario chart rendering. The only Decimal-to-number conversion is isolated in the Recharts adapter and is presentation-only.
- No backend change, persistence, automatic portfolio wealth, Sustainable Capacity, Retirement/FIRE, Portfolio Intelligence, ranking, recommendation, or LLM was added.
- `10.3.10 = IMPLEMENTED / READY FOR MANUAL VALIDATION`; `10.3.11 = READY / NOT STARTED`. Swagger Authorize manual smoke remains `DEFERRED BY USER`.
