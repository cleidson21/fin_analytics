# Current Repository State
**Updated:** 2026-09-30 (Phase 10.4 implementation decomposition complete; implementation not started)

This document reflects the VERIFIED reality of the repository as of the baseline audit.

---

## Module Status Matrix

| Module | Actual State | Verified In | Planned Next Step |
|--------|-------------|------------|-------------------|
| **Pierre / Cashflow** | STABLE | `domains/pierre/`, routers, migrations 001-003, 005b | DO NOT MODIFY |
| **Investments / Wealth** | STABLE | `backend/api/routers/investments.py`, `frontend/src/app/wealth/` | DO NOT MODIFY |
| **Market Data (yfinance)** | COMPLETE | `backend/integrations/yfinance/yfinance_provider.py` | Reuse existing |
| **Governance** | STABLE | `domains/pierre/governance_router.py`, migrations 006, 016 | DO NOT MODIFY |
| **AI Classification DB** | SCHEMA ONLY | Migrations 007, 011 | Activate in Phase 10.8 |
| **Gemini Integration** | EMPTY (0 bytes) | `integrations/gemini/` (3 files, all 0 bytes) | Implement in 10.8 |
| **Goals Backend** | IMPLEMENTED / VALIDATED | `api/routers/goals.py`, `use_cases/goal/`, `persistence/models/goal.py` | Complete |
| **Goals Frontend** | IMPLEMENTED / VALIDATED | `frontend/src/app/goals/`, `/wealth-intelligence` hub | Complete |
| **Financial Health** | **PHASE 10.2 COMPLETED / MERGED; 10.2.10-C VALIDATED** | `backend/domains/health/repository.py`, `domains/health/service.py`, `api/routers/financial_health.py`, `frontend/src/app/wealth-intelligence/health/` | Complete |
| **Planning & Projection** | **VALIDATED / CLOSED.** 10.3.7-A remains deferred; 10.3.8 automated validation passed with Swagger smoke deferred; 10.3.10A contract locked; 10.3.10B complete; 10.3.11–10.3.12 validated. Post-10.3 UX is `VALIDATED / CLOSED`; UX-B1–UX-B7 are validated. | ADRs 019–024; `backend/domains/planning/`; `frontend/src/lib/planning.ts`; `frontend/src/lib/planningLocale.ts`; `PLANNING_UX_CONTRACT.md` | Remains the reusable authority for FIRE projection/solvers |
| **Retirement & Financial Independence (FIRE)** | **IMPLEMENTATION PLAN READY / IMPLEMENTATION NOT STARTED** | ADR-022, ADR-025, `FIRE_CONTRACT.md`; 10.4-A audit complete; 10.4-B contract locked; `FIRE_IMPLEMENTATION_PLAN.md` | User review before 10.4-D1 FIRE Domain Core |
| **Portfolio Intelligence** | NOT STARTED — BOUNDARY ONLY | ADR-022 | Phase 10.5 |
| **Rebalancing** | NOT STARTED | — | Phase 10.6 |
| **Watchlist** | NOT STARTED | — | Phase 10.6 |
| **BCB / Macro Data** | NOT STARTED | — | Phase 10.7 |
| **News Integration** | NOT STARTED | — | Phase 10.7 |
| **LLM Provider** | NOT STARTED | — | Phase 10.8 |
| **Ollama** | NOT INSTALLED | — | Phase 10.8 |
| **AI Briefings / Insights** | NOT STARTED | — | Phase 10.9 |
| **Agent Orchestration** | NOT STARTED | — | Phase 10.10 (conditional) |
| **Docker** | NOT STARTED | — | Phase 10.11 |
| **Visual Polish** | NOT STARTED | — | Phase 10.12 |

---

## Database State

- Runtime database `database/fin_analytics.db` is operational and at the current Alembic head.
- All core tables exist and are operational
- **Financial Health ledger audit (read-only, refreshed 2026-09-19):** 1,431 transactions; all 1,431 `CLASSIFIED`; 0 `PENDING`; 343 `ENTRADA`; 905 `SAIDA`; 183 `IGNORAR`. The certified monthly boundary exposes 17 consecutive months from `2025-05` through partial `2026-09`, including 16 continuous closed months through `2026-08`; those closed months contain 12 realized surpluses and 4 realized deficits. Currency metadata contains 1,428 BRL and 3 USD rows (the USD rows are classified `SAIDA`), while Health has no approved currency-conversion contract for sustainable capacity.
- **RESOLVED (Lote 10.0-A):** The `position_snapshots` schema conflict was investigated and resolved:
  - The live DB uses the CORRECT Alembic schema: `id`, `account_id`, `asset_id`, `reference_date`, `quantity`, `avg_price`, `source_type`, `run_id`, `is_manual`, `current_value`
  - `snapshot_hash` column does NOT exist in the live DB — migration 013 was never applied (DB was bootstrapped via Alembic)
  - 53 rows, all `source_type = MYPROFIT_ATIVOS`
  - `alembic_version` = `f2915371d283` (head) — Alembic is in sync
  - Migration 013 (`snapshot_hash` schema) commented out in `create_db.py` with explanatory note
- **KNOWN (ADR-014):** `alembic check` fails due to FK `accounts.id` not existing (Pierre accounts uses composite PK). Pre-existing condition, no runtime impact.
- **10.3.10A read-only audit:** 1 application user; 7 Pierre/Core account rows and no MyProfit account row; 1 logical MyProfit portfolio scope; 49 unique monthly snapshots from `2022-09` through `2026-09`; all current rows have `MYPROFIT_EVOLUCAO` provenance tied to a successful import by the sole user. This supports ADR-023's guarded single-tenant resolver, not a general account-ownership relation.

---

## Backend Facts

- FastAPI 0.103.2 with 10 registered routers
- SQLAlchemy 2.0.21 async ORM
- yfinance 0.2.31 with in-memory TTL cache
- google-generativeai 0.8.6 installed but not called
- **FIXED (Lote 10.0-A):** `requirements.txt` updated with verified missing dependencies:
  - `pydantic-settings==2.14.2` (used in `backend/core/config.py`)
  - `aiosqlite==0.22.1` (used in `backend/database/engine.py`)
  - `python-jose[cryptography]==3.5.0` (used in `backend/infrastructure/security/jwt_service.py`)
  - `httpx==0.28.1` (used in `backend/infrastructure/http/pierre_client.py`)
  - `alembic==1.18.5` (used for migrations)
  - **NOTE:** `passlib` was NOT added — no import found in codebase (audited and confirmed)

---

## Frontend Facts

- Next.js 16.2.6 App Router
- React 19.2.4
- TailwindCSS 4
- Recharts 3.8.1
- TanStack Query 5.101
- Zustand 5.0.14
- Active wealth pages: /wealth, /wealth/patrimonio, /wealth/allocation, /wealth/dividends, /wealth/evolution, /wealth/asset, /wealth/performance, /wealth/positions
- Active Wealth Intelligence pages: /wealth-intelligence, /wealth-intelligence/health, /goals

---

## Known Technical Debt

- **HISTORICAL:** Two Investments asset-detail unit tests fail because their incomplete `MagicMock` session supplies a mock date that is sorted together with timeline strings. This is outside Financial Health and remains unchanged.
- **HISTORICAL:** `alembic check` still raises the ADR-014 `NoReferencedColumnError` for logical FK `position_snapshots.account_id -> accounts.id`; the legacy Pierre `accounts` table has a composite key and no `id` column.
- **GLOBAL / NON-BLOCKING:** Mobile responsiveness remains incomplete across multiple legacy FinAnalytics areas. It requires a transversal UX/polish phase and is not a Financial Health blocker.
- **GLOBAL / NON-BLOCKING:** Repository-wide frontend lint debt and the existing Recharts SSR dimension warning remain outside this microprocess. Health-targeted lint and the production build pass.
- **INFRASTRUCTURE / ACCEPTED:** CORS wildcard, JWT storage in `localStorage`, category-trend N+1 queries, and global `console.error` behavior remain tracked backlog; none blocks Phase 10.2.
- **UX / ACCEPTED:** Minor pagination polish remains backlog alongside the global mobile-responsiveness and Recharts SSR items.

---

## What the System Does NOT Do (verified)

- No real-time market data streaming (15-min cache only)
- No retirement projection calculations
- No Planning-derived sustainable contribution-capacity calculation; TSK-10.3.7-A concluded `DEFERRED — INSUFFICIENT CONTRACT / DATA`.
- No investment-capacity calculation; deferred to Planning / Portfolio Intelligence.
- No composite financial-stability metric or score; deferred until a deterministic contract is approved.
- No AI insight generation (empty files)
- No LLM integration of any kind
- No external news integration
- No BCB macro data
- No rebalancing engine
- No watchlist
- No Docker containerization
- No production deployment configuration

---

## Post-Merge Checkpoint

- GitHub PR #2 (`develop` → `main`) merged the approved Goals 10.1 and Financial Health 10.2 work.
- `main`, `develop`, `origin/main`, and `origin/develop` were synchronized at merge commit `b7ce8b8` on 2026-09-16.
- Phase 10.3 has validated read-only facts, assumptions, Forward Projection, both solvers, Goal Planning, and Scenario Comparison. The transient Planning API exposes the three generic calculation endpoints, owned Goal Planning, and Scenario Comparison; there is still no UI, schema migration, scenario persistence, or sustainable-capacity implementation.
- TSK-10.3.0 and its approval lock are validated. ADRs 019–022 approve the Planning input/source, mathematical, scenario/lifecycle, and Retirement/FIRE/Portfolio boundaries.
- `10.3.1 — Planning Read Foundation` is `VALIDATED`: Goal facts bypass the legacy float path with `goal_id + user_id` ownership; portfolio wealth requires an explicit snapshot `account_id`; Health reuses `HealthFinancialQuery` and `HistoricalFinancialMetricsService`; origins remain independent with typed provenance and no automatic sum.
- Real read-only validation on 2026-09-16 observed Goal current amount `113000.00` and MyProfit portfolio wealth `112888.91` as separate `Decimal` facts, plus an exact match between the Planning Health adapter and certified August 2026 Health metrics. Every captured database statement was `SELECT`; no session state was mutated.
- Independent validation repeated the 10.3.1 code audit, controlled `NULL`/zero and two-account oracles, SQLite `mode=ro` reconciliation, Planning/Goals/Health suites, and the general unit baseline.
- `10.3.2 — Projection Assumptions Boundary` is `VALIDATED`: independent probes confirmed strict types, Decimal domains and precision, the complete nominal/real matrix, fixed `END_OF_MONTH` timing, horizon XOR, leap-year/cross-year calendar resolution, and exact 1,200/1,201 boundaries. The boundary itself remains validation-only and now feeds the separate 10.3.3 engine.
- `10.3.3 — Forward Projection Engine` is `VALIDATED`: V2 independent revalidation proved magnitude-derived precision monotonicity, exact cent equality against an 800-digit Newton oracle across the original 1,200-month blocker and large initial/contribution/Fisher/real/negative cases, plus separate protection of the rate-precision and money-quantization sides of the former bug. No Goal/scenario orchestration was added.
- `10.3.4-A — Target Achievement Solver` is `VALIDATED`: independent probes confirmed positive finite cent-scale Decimal targets, period-zero `ALREADY_ACHIEVED`, exact first crossing, engine call counts 0/1, only zero-contribution non-growth proofs for `UNREACHABLE`, correct horizon exhaustion, nominal/real output-basis neutrality, 221-digit money, source/provenance preservation, immutability, and determinism. No validation test or production change was required.
- `10.3.4-B — Required Contribution Solver` is `VALIDATED`: independent code audit and external Decimal oracles proved strict target reuse, template-contribution independence, negative-rate and `ROUND_HALF_EVEN` monotonicity, target-as-upper-bound safety, exact integer-cent binary-search invariants, logarithmic scaling, and `C`/`C - 0.01` minimality. The validation covered 90 small-domain combinations, 7,128 cent candidates, all supported output modes/sources, and a 101-digit negative-rate case using a 500-digit recurrence. No production/test change was required. Macro `10.3.4 = VALIDATED`; `10.3.5 = READY / NOT STARTED`.
- `10.3.5 — Goal Planning Integration` is `VALIDATED` (TSK-10.3.5-V3, 2026-09-19): final independent validation confirmed the R2-SOL correction. Positive `GoalStatus.ACTIVE` eligibility precedes all projection-specific validation; `ACHIEVED`, `PAUSED`, `CANCELLED`, and reserved types return `NOT_APPLICABLE` with zero solver calls, while ACTIVE paths remain strict for target basis and Goal-current-amount provenance. Lifecycle `ACHIEVED` remains distinct from mathematical `ALREADY_ACHIEVED`. Controlled independent probes and `63` Goal Planning tests passed; Required `40`; Target `32`; Projection `38`; Assumptions `63`; Read `12`; Goals `65`; Health `68`; general `366 passed, 2 historical Investments/MagicMock failures`.
- `10.3.6-A — Scenario Comparison Contract & Architecture Lock` remains `CONTRACT LOCKED` (2026-09-19). `10.3.6-B — Scenario Comparison Engine` is `VALIDATED` after independent contract/code/oracle validation: the pure immutable engine preserves explicit source/provenance and order; performs atomic comparability prevalidation; reuses certified Forward/Target engines; returns exact Decimal deltas and period-zero/null temporal semantics; and contains no persistence, ranking, recommendation, Goal auto-integration, Required Contribution invocation, or second financial math. The focused suite is `37 passed`; all Planning regressions, Goals `65`, and Health `68` passed; general unit is `403 passed, 2 historical Investments/MagicMock failures`. The macro `10.3.6` is `VALIDATED`; `10.3.7 = DEFERRED — CONTRACT NOT APPROVED`.
- `10.3.7-A — Sustainable Contribution Capacity Contract Decision` is `DEFERRED — INSUFFICIENT CONTRACT / DATA`: Health certifies realized historical cashflow, not recurring future affordability. Missing future-obligation and cash-buffer facts plus unapproved lookback, minimum-history, partial-month, deficit, anomaly/outlier, statistic, negative-result, currency, and zero/null rules make `sustainable` indefensible today. No formula, implementation, API, migration, or UI was created. This optional deferral did not block the completed 10.3.8-A contract audit and remains outside the approved API surface.
- `10.3.8-A — Planning API & Scenario Persistence Contract Audit` is `API CONTRACT LOCKED / PERSISTENCE DEFERRED`: five explicit authenticated transient POST capabilities are contracted under `/api/v1/planning`; strict Decimal strings, stable response DTO mapping, Goal-owned certified facts, caller-provided facts that cannot impersonate certified sources, and deterministic/no-write delegation are required. `INVESTMENT_PORTFOLIO_SNAPSHOT` is not exposed because its external account scope has no authenticated-user ownership relation. Scenario storage remains deferred for missing lifecycle, versioning, frozen-vs-live provenance, staleness, expiration, Goal relationship, and migration semantics.
- `10.3.8-B — Planning API Foundation` is `VALIDATED`: strict public Decimal-string/date/datetime primitives, supported initial-wealth selectors, pure builders, Decimal/provenance mappers, sync-reader/auth dependency annotations, and local Planning error translation remain the shared API boundary. Independent validation exercised actual JSON parsing, strict source rejection, OpenAPI/startup, and global-error isolation. Focused coverage: `41 passed`.
- `10.3.8-C — Generic Planning Calculation Endpoints` is `VALIDATED`: independent HTTP/oracle validation confirmed authenticated `POST /api/v1/planning/projection`, `/target-achievement`, and `/required-contribution` delegate only to their certified engines without financial recalculation. `GOAL_CURRENT_AMOUNT` is resolved server-side through the owned Decimal Planning reader; missing/wrong-owner Goals are indistinguishable `404`, null Goal amounts are `422`, and portfolio source remains structurally unavailable. Decimal JSON remains strict and declared precision is preserved. Responses preserve complete certified timelines/statuses with Decimal strings. Focused HTTP coverage: `25 passed`; all Planning, Goals (`65 passed`), Health (`68 passed`) regressions passed; general unit is `465 passed, 2 historical Investments/MagicMock failures`. `10.3.8-D = READY / NOT STARTED`.
- `10.3.8-D — Owned Goal Planning Endpoint` is `VALIDATED`: final independent HTTP/domain validation proved `preflight_applicability()` and `evaluate()` share one internal lifecycle/type authority across every real `GoalStatus × GoalType` pair. The router invokes `lookup → preflight → source resolution → evaluate` only for ACTIVE eligible Goals and stops at preflight for non-projectable Goals, including available or unavailable Goal current amount. Non-projectable requests return `200 / NOT_APPLICABLE`; ACTIVE required-source absence remains `422`; malformed Decimal remains structural `422`. No dummy wealth, DB access in the domain, Goal mutation, persistence, Scenario endpoint, Required Contribution automation, or financial math was added. Focused Goal HTTP coverage: `39 passed`; Goal Planning domain `101`; foundation `41`; calculation endpoints `25`; other Planning `222`; Goals `65`; Health `68`; general unit `546 passed, 2 historical Investments/MagicMock failures`. `10.3.8-E = READY / NOT STARTED`.
- `10.3.8-E — Scenario Comparison Endpoint` is `VALIDATED`: independent HTTP/domain/OpenAPI validation confirmed explicit scenario/reference identity, ordered output, metadata-only archetypes, atomic Goal source resolution, no Goal Planning applicability leakage, resolved-horizon equivalence, ReturnType variation, target-pair semantics, one Comparison engine call, and direct mapping of certified deltas. Focused HTTP coverage: `42 passed`; Planning domain regressions `323`; Goals `65`; Health `68`; general unit `585 passed, 2 historical Investments/MagicMock failures`. Persistence remains `DEFERRED — TRANSIENT API FIRST`; `10.3.8-F = READY / NOT STARTED`.
- `10.3.8-F — Planning API Integration & Stabilization` has `AUTOMATED VALIDATION PASSED`: exactly five authenticated Planning routes have unique OpenAPI operation IDs; strict request Decimal/source constraints, non-enumerating Goal ownership, synchronous Planning reads, read-only execution, D reconciliation, E order/reference semantics, 1,200-month serialization, and deterministic responses remain intact. Integration `5`; B–E API `147`; Planning domain `323`; Goals `65`; Health `68` passed. General unit: `593 passed, 2 historical Investments/MagicMock failures`. No production fix was required. Swagger Authorize manual smoke is deferred by user as non-blocking debt and has not been recorded as passed.
- `10.3.9 — Planning Frontend Foundation` is `VALIDATED`: manual smoke passed for Nominal→Nominal, Real→Real, Nominal→Real, and correctly unavailable Real→Nominal. Swagger Authorize manual smoke remains deferred by user.
- `10.3.10 — Planning Analytical UI` is `VALIDATED`: the five certified capabilities and the chart-only Decimal rendering boundary passed technical and user validation. Broader visual/UX refinements were deliberately deferred by the user until after functional consolidation and are not a blocker.
- `10.3.10A — Investment Portfolio Source Contract & Ownership Audit` remains `CONTRACT LOCKED`. `10.3.10B1–B4` are `VALIDATED`; the macro is `VALIDATED / COMPLETE`. Independent adversarial validation confirmed the guarded one-user tenant invariant, semantic UUID ownership, complete scope/run consistency, latest-eligible-as-of selection, exact Decimal flow, source-only API selector, applicability-first Goal orchestration, atomic mixed-source comparison, and source-only frontend requests. The user confirmed Projection, Target, Required, Goal, Scenario Comparison, certified wealth/reference-month rendering, manual-field hiding, no fabricated daily date, and charts. `INVESTMENT_PORTFOLIO_SNAPSHOT` is certified end-to-end for Planning only as investment portfolio wealth in the current BRL guarded single-user/single-tenant mode; it is not net worth, real-time wealth, a full historical time-travel source, or a preview endpoint. `10.3.11 = VALIDATED / STABILIZED`; `10.3.12 = READY / NOT STARTED`.
- `10.3.11 — Planning Integration & Stabilization` is `VALIDATED / STABILIZED`: five authenticated APIs and five UI capabilities were reconciled against ADRs 019–023; all three source paths remain explicit and source-specific; no browser financial truth, backend write, persistence, capacity, FIRE, Portfolio Intelligence, or LLM path was found. Planning API `157`, Planning domain/resolver `339`, TypeScript, focused lint, and production build passed. General units remain `614 passed, 2` historical Investments/MagicMock failures.
- `10.3.12 — Planning Final Validation & Closure` is `VALIDATED / CLOSED`: representative closure checks passed (`269` focused API/domain/resolver tests), OpenAPI still has exactly five secured Planning POSTs, TypeScript/lint/build passed, and no production defect or new contract was found. Phase 10.3 is closed with its explicit deferred boundaries intact. ADR-024 governs the post-closure Planning UX/form/simplicity refinement.
- `POST-10.3-UX-B1 — pt-BR financial input/output primitives` is `VALIDATED`: `planningLocale.ts` provides exact string-safe money/rate display and parsing, civil-date/reference-month helpers, structured lexical errors, and `57` Node-only Vitest tests. Vitest `3.2.4` is dev-only. No Planning form or capability was migrated; `UX-B2 = READY / NOT STARTED`.
- `POST-10.3-UX-B2 — page chrome, copy reduction, and three intentions` is `VALIDATED`: the user confirmed a cleaner Planning entry, the three intentions and Objective submodes, intention navigation, title removal, minimal Health chrome, and no lost context. No form/value/request/financial contract changed.
- `POST-10.3-UX-B3 — smart defaults, Advanced options, and low-friction forms` is `VALIDATED`: user evidence is MyProfit simple/info `PASS`; manual and contribution BRL input `PASS`; `8,5` percentage input `PASS`; ambiguous `1000.50` rejection `PASS`; discreet Advanced `PASS`; NOMINAL→NOMINAL, REAL→REAL, NOMINAL→REAL + inflation `PASS`; REAL→NOMINAL blocked `PASS`; manual↔MyProfit switching `PASS`; Objective and Comparison consistency `PASS`.
- `POST-10.3-UX-B4 — Scenario Comparison shared context` is `VALIDATED`: date-base, horizon, output mode, fixed operational semantics, and optional target pair are declared once in a shared context and expanded into each ordered API scenario. Initial source, contribution, return, return type, conditional inflation, label, archetype, and manual provenance remain scenario-specific. Removing the selected reference clears it for explicit reselection. The pure suite has `64` tests; TypeScript, focused lint, and production build passed; no backend/API contract changed.
- `POST-10.3-UX-B5 — results, charts, visual hierarchy, and provenance` is `VALIDATED`: B1 string-safe BRL/rate/date/reference-month formatters present Planning responses; answer-first heroes, secondary facts, compact source details, and readable Recharts visuals preserve backend financial authority. Comparison cards identify an explicit reference neutrally, retain request order, and expose no technical IDs.
- `POST-10.3-UX-B5-R1 — Quiet Financial OS visual polish` is `VALIDATED` after the accepted manual visual review.
- `POST-10.3-UX-B6 — living states, skeletons, responsiveness, and accessibility` is `VALIDATED`: the user approved the manual review. First-submit skeletons, accessible loading labels, stale-result identification, recalculation preservation, CSS-only reduced-motion transitions, and responsive result surfaces add feedback without changing Planning truth.
- `POST-10.3-UX-B7 — independent validation and UX closure` is `VALIDATED / CLOSED`: independent source-of-truth, contract, static, frontend, focused Planning-backend, and secured OpenAPI checks passed. At that closure checkpoint, Phase 10.4 was `READY / NOT STARTED`; ADR-025 now supersedes that phase-status snapshot.
- `10.4-A — FIRE Contract & Source-of-Truth Audit` is `AUDIT COMPLETE`; its preserved evidence is `FIRE_CONTRACT_AUDIT.md`.
- `10.4-B — FIRE Contract Lock & ADR-025` is `CONTRACT LOCKED`. `FIRE_CONTRACT.md` is the canonical implementation contract and ADR-025 is accepted.
- `10.4-C — FIRE Implementation Decomposition & Execution Plan` is `IMPLEMENTATION DECOMPOSITION COMPLETE / AWAITING USER REVIEW`. `FIRE_IMPLEMENTATION_PLAN.md` maps the exact architecture, files, dependencies, tests, gates, risks, and seven-step D1–D7 execution order. No FIRE production code, endpoint, engine, test, migration, persistence, or frontend exists yet; implementation remains `NOT STARTED`.
