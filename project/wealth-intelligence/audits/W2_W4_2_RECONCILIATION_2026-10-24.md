# W2–W4.2 Repository Reconciliation — 2026-10-24

**Status:** `AUDIT / EVIDENCE — NON-NORMATIVE`

> **Checkpoint follow-up (2026-10-24):** the focused Git verification in
> `R4_C_CHECKPOINT_AND_R5_PREPARATION_2026-10-24.md` established that R4-C was
> already published at `14cb65db1cddd5466523eefdca54c78affb3eca7`. References
> below to an R4-C checkpoint pending are preserved as this report's original
> audit conclusion and are superseded only for that checkpoint status.

**Baseline inspected:** `develop` at `14cb65db1cddd5466523eefdca54c78affb3eca7`, with a pre-existing dirty worktree preserved.

**Purpose:** reconcile the current W2–W4.2 implementation with canonical owners
without changing accepted ADRs, locked contracts, financial Engines, migrations,
or official phase approvals. This report records evidence; it does not replace
`CURRENT_STATE.md`, `IMPLEMENTATION_ROADMAP.md`, or any concern owner.

## 1. Authority applied

Conflicts were resolved in this order:

1. accepted ADR or `LOCKED` contract for its explicit scope;
2. the canonical concern owner named by ADR-027 and `AGENTS.md`;
3. `CURRENT_STATE.md` for verified repository reality;
4. `MASTER_PLAN.md` for direction;
5. `IMPLEMENTATION_ROADMAP.md` for the active queue;
6. audits and research as evidence;
7. material marked `SUPERSEDED / HISTORICAL`.

ADR-011 is superseded by ADR-027 except as historical route intent. ADR-024 and
`PLANNING_UX_CONTRACT.md` remain the accepted Planning UX contract. ADR-023 owns
the investment-wealth source boundary. ADR-025 owns FIRE. ADR-028 owns Smart
Context. ADR-030 owns the non-operational AI runtime boundary.

## 2. Executive reconciliation

- Goals 10.1, Financial Health 10.2, Planning 10.3, POST-10.3 UX, FIRE 10.4,
  Smart Context R2, and the internal R4-A/R4-B/R4-C foundations exist and have
  direct code/test evidence.
- The current worktree contains a functional W2–W4.2 Wealth Intelligence
  experience that was missing from the tracking documentation: Wealth Home v2,
  governed Health/Goals/investment-wealth cards, temporal navigation, richer
  Goals/Health presentation, five Planning flows, three FIRE modes, and one
  memory-only selected Planning/FIRE response.
- That local product work is not proof that canonical R5 or R6 started or
  closed. The active roadmap still marks both `NOT STARTED`; R7 is not met.
- Existing Investments pages remain operational but are not certified Portfolio
  Intelligence. Wealth Home legitimately reuses only the guarded ADR-023 monthly
  aggregate investment-wealth fact.
- Portfolio Intelligence 10.5-B remains paused. No allocation, concentration,
  performance, benchmark, score, or recommendation authority was introduced.
- There is no operational Advisor. R4-A through R4-C are internal foundations;
  there is no AI endpoint, connected model, hybrid router, scheduler, or
  production inference path.

## 3. Public and internal implementation inventory

The generated OpenAPI contains 56 paths and 60 HTTP operations. Relevant
authenticated public operations are:

- Goals: five CRUD operations under `/api/v1/goals`;
- Financial Health: five reads under `/api/v1/financial-health` (`cashflow`,
  `history`, `categories`, `anomalies`, `trends`);
- Planning: five transient POST calculations under `/api/v1/planning`;
- FIRE: `POST /api/v1/fire/analysis` with the three contracted modes;
- Wealth Home: `GET /api/v1/wealth-home?reference_month=YYYY-MM`;
- Profile/Smart Context user actions: two Profile context operations and four
  recurring-income candidate/decision operations.

There is no Portfolio Intelligence or AI/Advisor public operation.

## 4. Single traceability matrix

| Original requirement | Canonical source | Canonical state | Code evidence | Test evidence | Concrete pending item | Functional impact | Priority | Dependency/blocker | Required action |
|---|---|---|---|---|---|---|---|---|---|
| Goals authenticated lifecycle and progress | Roadmap 10.1; Data owner § Goals | `IMPLEMENTED / VALIDATED` | `backend/api/routers/goals.py`; Goal use cases/repository; `frontend/src/app/goals/` | Goal backend suites; GoalCard component tests | Public Goal money/progress remains `float`; Planning safely bypasses it with its Decimal reader | Limits reuse of the public Goals DTO as financial authority | Medium | New Goals precision contract would be required | Preserve current CRUD; contract a Decimal-string Goals API before promoting it as cross-domain authority |
| Canonical Goals navigation | Roadmap 10.1; ADR-027 route continuity | Implemented locally, not an R5/R6 milestone | `/wealth-intelligence/goals` reuses `/goals`; `next.config.ts` redirects legacy route; navigation state recognizes both | `navigation.test.ts`; `nextConfig.test.ts`; production route build | None functionally; formal phase attribution is missing | Documentation/status only | Low | Canonical phase reconciliation | Keep compatibility and record the local increment without closing R5/R6 |
| Financial Health facts, anomalies, trends | ADR-015, ADR-017, ADR-018; Roadmap 10.2 | `IMPLEMENTED / VALIDATED` | five authenticated Health routes; Decimal DTOs; Health services; analytical page | Health backend suites; Health page/components | No new financial capability is pending in W2–W4.2 | None for the contracted scope | Low | Composite stability and sustainable capacity remain uncontracted | Preserve scope; do not infer contribution capacity |
| Health temporal comparison | ADR-018 | Closed-month comparison rules are authoritative | backend trend service and UI labels expose requested, target, and comparison months | Health service/API/page tests | Current screenshots must be read as `ago/26 → set/26` comparison while `out/26` is the displayed month | Prevents misreading a partial month as the trend target | High presentation clarity | None | Keep explicit period chips and neutral factual direction styling |
| Five Planning capabilities | ADR-019–023; Roadmap 10.3 | `VALIDATED / CLOSED` | five authenticated POSTs and five frontend capabilities | Planning backend suites; Planning frontend tests | No engine/result gap found | Users can execute all contracted deterministic questions | — | Scenario persistence remains deferred | Preserve transient/read-only execution |
| Planning visual information architecture | ADR-024 and `PLANNING_UX_CONTRACT.md` | Canonical contract says three visible intentions; current UI exposes five peer modes | `planning/page.tsx` maps five peer controls onto three query intentions | Planning navigation/page tests | Decide whether W4.2 intentionally supersedes ADR-024 presentation or UI must return to three intentions with an inner Objective switch | Canonical UX divergence, not financial-result corruption | High | Explicit user/canonical decision | Approve a contract amendment or realign the control hierarchy; do not change silently |
| Planning result visualization | ADR-024 | Certified series may be charted; no browser crossing/math | Planning result/chart components consume API periods | Planning component/form tests | None proven; browser review remains desirable | Visual comprehension only | Low | User visual QA | Retain rendering-only numeric boundary |
| FIRE three modes and explicit execution | ADR-025; `FIRE_CONTRACT.md` | `VALIDATED / CLOSED` | one endpoint; `SUMMARY`, `PROJECTED_DATE`, `REQUIRED_CONTRIBUTION`; conditional frontend forms | FIRE backend and frontend tests | None in contracted MVP | Functional deterministic FIRE journey exists | — | Persistence, Goal linkage, variants remain deferred | Preserve action-triggered execution and explicit assumptions |
| Governed monthly investment wealth | ADR-019/023 | Eligible read-only fact; not net worth | `PlanningPortfolioSourceResolver`; Wealth Home service/mapping/DTO | resolver and Wealth Home service/API tests | Contract/documentation must acknowledge its Home composition without calling it Portfolio Intelligence | Enables legitimate investment-wealth KPI | High documentation | Formal R6 incorporation | Keep source, month, BRL, run, freshness/completeness and no silent fallback |
| Legacy Investments product | 10.5-A audit; Portfolio audit §§ 25–40 | Operational, not certified Portfolio Intelligence | `backend/api/routers/investments.py`; `/wealth/*` | Investments tests, with two unchanged MagicMock timeline failures | Mixed valuation/browser heuristics and unsupported performance semantics remain | Cannot be reused as certified allocation/performance authority | High | 10.5-B paused until R7 | Preserve warning; do not expand under this scope |
| Wealth Home v2 composition | R2 Home consumer foundation; ADR-023; R6 direction | Implemented/tested locally; not canonically phase-closed | Wealth Home DTO/service/router/mapping; `WealthHomeExperience` | 15 backend Wealth Home tests; 12 component tests plus client tests | Public schema and R6 attribution are absent from canonical phase tracking | Product works, but governance status is ambiguous | High | Explicit canonical reconciliation | Accept as contract-preserving local increment or define the missing R6 contract before a checkpoint |
| Transient Planning/FIRE selection | ADR-021 transient-first; W4.1 local scope | Implemented in memory only | `TransientAnalysisContext`, typed union, Home panel | context, selector/button, Planning/FIRE tests | No persistence/lifecycle contract exists, by design | One selected result survives navigation but not refresh | Low | Persistence explicitly deferred | Keep memory-only isolation and clear on logout/token/user change |
| Smart Financial Context | ADR-028 and locked R2 contract | R2 `IMPLEMENTED / VALIDATED / CLOSED` | persistence, Profile API, recurring evidence/decisions, B5 composer, B7 consumers | Smart Context backend and Profile frontend suites | R6 smart-prefill/effective-input composition remains unimplemented | Existing context does not silently alter Planning/FIRE inputs | Medium future | R6 contract and explicit user actions | Reuse B7 only after the consumer contract is approved |
| Portfolio Intelligence | ADR-022/026/027; 10.5-A audit | 10.5-B `PAUSED` | No PI service, engine, endpoint, or page | No locked 10.5-B test contract | Source/precision/temporal/MVP contract and R7 gate are missing | Allocation/concentration/performance cannot be certified | Blocked | R7 closure or explicit later decision | Do not implement now |
| Advisor and AI runtime | ADR-030; AI owner | R4-A/B closed, R4-C checkpoint pending; no production runtime | provider-neutral contracts, five read-only tools, audit/telemetry; disabled experimental Home row | AI runtime unit suites | Pre-execution durable audit guard, operational adapter/router, authorization and privacy gates are absent | Advisor must remain disabled | Blocked | R4-F durable pre-execution guard and later explicit gates | Do not connect Ollama or expose an Advisor endpoint |
| Navigation/theme/recomposition phases | ADR-027; UI owner; active roadmap | R5/R6/R7 remain `NOT STARTED` canonically | Local Portuguese sidebar/top nav and dark responsive pages exist | navigation/component/build evidence | Local implementation and phase status are not reconciled; System/Light/Dark remains absent | Product is usable, but phase completion cannot be claimed | High governance | Explicit roadmap decision and R5 contract | Decide how local W2–W4.2 is absorbed; preserve dark-only limitation |
| Tracking documentation | ADR-027 documentation ownership | Stale before this audit | root/project README, Current State, Roadmap, Changelog | Repository/OpenAPI/test evidence | MASTER_PLAN and ARCHITECTURE status narratives also lag but are canonical owners, not simple tracking files | Readers could mistake implemented local product work for absence or approved R6 | High | Owner-level canonical decision | Tracking docs updated here; propose, do not auto-edit, owner-level status reconciliation |

## 5. Visual evidence review

The supplied PDFs were rendered and every page inspected:

- `modelo/Visao Geral.pdf`: compact Home, three governed KPIs, explicit
  on-demand FIRE state, provenance drawer access, unavailable certified charts,
  and disabled Advisor row;
- `modelo/Metas.pdf`: one Goal with visible state/priority, target/current/
  contribution/date, progress bar, and edit/delete actions;
- `modelo/Planejamento.pdf`: five compact question-oriented modes and a
  conditional projection form;
- `modelo/FIRE.pdf`: three analysis modes, explicit wealth source, conditional
  assumptions, and submit-only execution;
- `modelo/Saude Financeira.pdf`: monthly KPIs, certified history, category
  ranking, anomalies, and category trends across three pages.

The review found no synthetic chart presented as governed data. It did find two
presentation defects corrected in this execution: Goals percent localization
and qualitative red/green coloring of factual Health deltas. No live browser or
new screenshot was produced; the PDFs are user-provided evidence, not proof of
the post-fix browser render.

## 6. Corrections implemented in this reconciliation

1. Goal progress now uses pt-BR percent formatting (`41,7%`) in visible and
   accessible text while preserving the backend-supplied percentage.
2. Health global/category deltas now use a neutral value color; direction badges
   still show `Aumentou`, `Reduziu`, etc. This follows ADR-018 and avoids calling
   every negative delta bad (for example, lower expense).
3. Wealth Home authenticated loading copy now describes all governed data rather
   than the obsolete Health-and-Goals-only W2 state.
4. Tracking docs now describe the current local implementation without changing
   R5/R6/R7 status or any accepted ADR/locked contract.

## 7. Validation evidence

- OpenAPI generation: 56 paths, 60 operations; all Goals, Health, Planning,
  FIRE, Profile/financial-context, and Wealth Home operations declare security.
- Governed backend selection excluding legacy Investments: `828 passed`.
- Broader selection including Investments: `834 passed`, the two already
  documented `test_investments_asset_detail` MagicMock/timeline failures, and
  one temporary `C:\tmp` permission error. The affected Smart Context migration
  test was rerun with a workspace-local `--basetemp` and passed (`1 passed`).
- Frontend Vitest: `206 passed` in 24 files.
- TypeScript: `npx tsc --noEmit` passed.
- Focused ESLint over all frontend files changed by this reconciliation passed.
- Next.js production build passed and generated 38 routes. The pre-existing
  Recharts SSR `width(-1)/height(-1)` warning remains.
- No Playwright/Puppeteer, download, real financial data, migration, deploy,
  commit, push, LLM execution, or benchmark was used.

## 8. Decisions still required

1. **Planning UX contract:** approve W4.2's five peer modes as a controlled
   amendment to ADR-024, or direct the UI back to three intentions with an inner
   Objective task switch.
2. **Canonical phase attribution:** decide whether W2–W4.2 is accepted as
   contract-preserving preparatory work to be absorbed into R5/R6, without
   claiming those phases are complete.
3. **Roadmap progression:** the active queue still has R4-C checkpoint pending
   and treats the main path as sequential. Moving to R5 while leaving later R4
   adapters/benchmarks gated requires an explicit roadmap decision.
4. **Owner documents:** `MASTER_PLAN.md` and `ARCHITECTURE.md` contain old
   implementation-status narratives. Their factual status sections should be
   reconciled only through an owner-level documentation task, without changing
   their product/architecture decisions.

## 9. Recommended next canonical milestone

Close the R4-C documentation/checkpoint decision, then explicitly authorize an
R5 contract and absorb the verified W2–W4.2 local work as evidence/input. R5
should reconcile the Planning control hierarchy, responsive shell, semantic
tokens, and System/Light/Dark boundary without touching financial Engines. R6
can then formally own the composed Home/Goals/Planning/FIRE journeys, followed
by R7 independent validation. Portfolio Intelligence 10.5-B remains after R7.
