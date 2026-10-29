# Implementation Roadmap — Wealth OS
**Status:** `ACTIVE QUEUE — R6.5-A CONTRACT APPROVED / R6.5-B IMPLEMENTED — FOCUSED TESTS PASSED — CHECKPOINT PENDING / R6.5-C PLANNED / R4 SEPARATELY GATED — SEQUENCED / R7 NOT STARTED`
**Date:** 2026-10-29

---

## Single delivery queue — 2026-10-28 realignment

This is the only execution queue. The project owner authorized this documentary
reconciliation and R6.5's functional objective on 2026-10-28, then separately
authorized only R6.5-B backend implementation on 2026-10-29. Existing
accepted ADRs and locked contracts remain binding. The phase inventory below
is dependency/history context, not a competing queue. One main task runs at a
time; an unmet gate stops that task rather than silently selecting another phase.

### Next five concrete deliveries

| Order | Existing ID / bounded work package | Deliverable and exit | State / next action |
|---:|---|---|---|
| 1 | R6.5-A — contract definition | D1–D3 approved; exact equal-total A/B nominal budget contract in `GOAL_BUDGET_PREVIEW_CONTRACT.md` | `CONTRACT APPROVED / READY FOR BACKEND`; documentary gate complete, no implementation |
| 2 | R6.5-B — backend | One transient orchestration of owned Goals, explicit equal-total allocations, budget accounting, and certified per-Goal scenario effects | `IMPLEMENTED / FOCUSED TESTS PASSED / CHECKPOINT PENDING`; 192 new tests and 946 relevant regression tests passed (192 included); no commit/push/deploy |
| 3 | R6.5-C — product integration | Select Goals → distribute budget → compare effects → review transient result in the existing minimal journey | `PLANNED / NOT STARTED`; backend accepted plus explicit UI contract/task; manual acceptance, no new topbar or fourth Planning intention |
| 4 | R4-C/F activation prerequisites + R4-G pilot specification | Resolve durable audit/retention/HMAC and pre-dispatch guard contract; fix the equivalent synthetic local/online fixture set, budgets, stop rules, and provider permissions | `CONTRACT REQUIRED`; no new persistence, provider call, or benchmark until separately authorized |
| 5 | R4-D / D.3 — local adapter and bounded offline validation | One provider-neutral Ollama adapter; Qwen 3.5 4B baseline tested on certified synthetic Planning results; exact digest/config and failures recorded | `NOT STARTED` as adapter; separate code/call authorization; isolated adapter test is not product activation |

Then, sequentially: R4-E Gemini adapter (mocks first) → R4-F guarded dispatch
and approved durable audit implementation → R4-G equivalent offline/online
pilot → bounded R6 Health/Smart Context and contextual AI integration → R7
independent closure → 10.5-B contract lock → contracted 10.5 delivery → 10.6
watchlist/conditions and 10.7 Market/news → full Copilot/10.9 briefing.
Each arrow requires the preceding applicable gates and a bounded authorization.
Online pilot execution follows its safety gates; it is not postponed until
Portfolio Intelligence and cannot bypass R4-F just to satisfy a calendar.
R4-D/E mocked adapter work can prepare without operational dispatch.

The desired earlier AI tests after the R6.5 UI are represented by items 4–5:
the real safety prerequisites, not another financial feature, are next. R4-G's
protocol can be specified at item 4, but live comparison waits for its eligible
adapters/guard. No R6.6/R6.7 or new R7 feature number is invented. Named work
packages under an existing phase are not new normative phases.

### Original vision → verified delivery matrix

Historical 10.x mapping comes from the preserved phase records and product
specification; Rn mapping denotes composition/dependencies, not equivalence or
blanket authorization. Repository paths are relative to the repository root.

| Original objective | Original phase | Current correspondence | Existing capability | Implementation evidence | Real gap | Dependency | Canonical status | Next delivery milestone |
|---|---|---|---|---|---|---|---|---|
| Metas: create and follow objectives | 10.1 | R6.1–R6.5 | CRUD, context/deep link, progress, count-only overview, required-contribution preview | `backend/api/routers/goals.py`; `backend/domains/planning/goal_progress.py`, `goal_monitoring.py`, `goal_batch_contribution.py`; `tests/unit/test_planning_goal_batch_contribution_api.py` | No limited-budget multi-Goal journey; cadastral progress is not synchronized investments | R6.5 contract | R6.1–R6.4 `COMMITTED/PUSHED` | A / R6.5 |
| Saúde Financeira: understand receipts, spending and surplus | 10.2 | R2 + R6 | Observed cashflow, history, trends, anomalies | `backend/domains/health/service.py`; `backend/api/routers/financial_health.py` | Historical surplus does not certify future affordability | ADR-028; 10.3.7-A decision | Core `IMPLEMENTED/VALIDATED`; capacity `CONTRACT REQUIRED` | B / context presentation, then separate capacity decision |
| Planning: test contribution alternatives | 10.3 | R6.1/R6.4/R6.5 | Five certified POSTs, R6.4 batch inverse solve and R6.5-B budget preview | `backend/api/routers/planning.py`; `backend/domains/planning/goal_budget.py`, `scenario_comparison.py` | Backend budget accounting/comparison implemented; minimal product integration remains absent | ADR-020/021/023/024; approved R6.5 microcontract | Core closed; R6.5-A approved; B `IMPLEMENTED / FOCUSED TESTS PASSED / CHECKPOINT PENDING` | A / R6.5-C after backend checkpoint/validation |
| FIRE: understand independence conditions | 10.4 | R5 + R6 | Summary, projected date, required contribution; transient Home result | `backend/api/routers/fire.py`; `frontend/src/app/wealth-intelligence/fire/page.tsx`; `FIRE_CONTRACT.md` | No approved Goal wealth linkage or Health-inferred retirement spending | ADR-025; explicit separate amendment before financial linkage | Core `VALIDATED/CLOSED` | B / contextual navigation and explicit assumptions only |
| Smart Context: reuse known facts | Later realignment; not an original numbered 10.x capability | R2 → R6/R4 | B5/B7 purpose-limited composition and consumer methods | `backend/application/services/smart_financial_context_service.py`, `smart_context_consumer_foundation.py`; related unit tests | Consumer foundations do not create effective solver inputs | ADR-028; consumer-specific contract | R2 `CLOSED` | B / source-aware context, no generic context API |
| External Context: sourced economic references | 10.7 foundation | R3 → R6/Market | BCB/SGS ingestion/store and point-in-time reference service | `backend/domains/external_context/`; `backend/application/services/external_reference_context.py`; `tests/unit/test_external_reference_context.py` | No activated Market consumer; Focus deferred; yfinance remediation gated | ADR-029 purpose matrix; R3-G before yfinance admission | Foundation independently approved; later scope gated | E / approved Market consumer, never auto-return input |
| IA local: usable private interpretation | 10.8 | R4-D/F/G | Provider-neutral contracts, fake, tools/audit; synthetic Ollama lab | `backend/integrations/ai/fake_provider.py`; `tests/unit/test_ai_runtime_contracts.py`; ignored lab reports cited in `AI_AND_LLM.md` | No operational Ollama adapter; factual/schema failures remain | ADR-030; adapter, guard, exact model evidence | `LAB TESTED`, not product-integrated | C / R4-D.3 |
| IA online: governed remote option | 10.8 | R4-E/F/G | Approved Gemini direction; empty historical scaffold | `backend/integrations/gemini/classifier.py`, `models.py`, `prompts.py`; R4-A policy tests | No Gemini runtime or equivalent online pilot evidence | Remote authorization, paid-policy gate for real data, durable audit | `NOT STARTED` adapter | C / R4-E then guarded R4-G |
| Portfolio Intelligence: understand composition/concentration | 10.5-A/B | R7 prerequisite, then 10.5-B | Operational Investments, certified aggregate investment wealth | `PORTFOLIO_INTELLIGENCE_CONTRACT_AUDIT.md`; `backend/application/services/planning_portfolio_source_resolver.py` | Position valuation completeness/reconciliation; no certified portfolio-analysis service | R7 closure; preserved `total_atual` decision | 10.5-A resolved; 10.5-B `PAUSED` | D / 10.5-B, not another audit |
| Watchlist: track chosen assets | 10.6 | Post-R7/10.5, no new Rn assigned | Asset detail/market infrastructure only | `frontend/src/app/wealth/`; current-state absence record | No governed watchlist lifecycle/CRUD | 10.5 completion; ownership/persistence contract | `NOT STARTED` | E / 10.6 contract |
| Mercado e notícias: sourced events and context | 10.7 | R3 foundation; later Market product | Existing yfinance and BCB/reference foundations, not news runtime | `backend/domains/external_context/`; ADR-006/012/029 | News acquisition, rights, sanitization, relevance and consumer contract | 10.5 completion for historical 10.7 product; R3-G only if yfinance admitted | Foundation exists; product `CONTRACT REQUIRED` | E / 10.7 |
| Alertas: surface an explicit condition | 10.6, later 10.9 scheduling | Monitor after dependencies, no Rn invented | Health anomalies and Goal data flags only | Health service; `backend/domains/planning/goal_monitoring.py` | No persistent alert rules, delivery or acknowledgement lifecycle | Sourced facts; rule/lifecycle contract | `NOT STARTED` alert product | E / objective UI conditions before push/scheduler |
| Copilot: ask and explain certified results | 10.8–10.10 vision | R4 foundation + bounded R6 entry; full product later | Five internal read-only tools; no conversational product | `backend/application/services/read_only_ai_tools.py`, `minimal_ai_context.py`; `tests/unit/test_ai_runtime_tools.py` | Adapter/guard, approved result/tool schema and user experience | R4 security/quality gates; domain capability must exist | `NOT STARTED` product | F / one bounded explanation before full Copilot |
| Briefing: periodic attributable synthesis | 10.9 | Later Copilot/Monitor, no Rn invented | No generator/scheduler; legacy schema is scaffolding | `AI_AND_LLM.md`; R4-C audit boundary | Authorized sources, delivery, retention, staleness and schedule | R4 + accepted product scopes; 10.5 for portfolio briefing | `CONTRACT REQUIRED / NOT STARTED` | F / on-demand sourced briefing before scheduling |

### Milestone cards and closure criteria

Future implementation cards below are **planned work**, not authorization.
R6.5-A's contract is approved; separately authorized R6.5-B is now implemented
and tested with its checkpoint pending. Its UI remains unimplemented.
`READY` requires its named contract, dependencies, and explicit task approval.
`TESTED` requires recorded commands/results; `USER ACCEPTED` records actual
scope of manual acceptance; `COMMITTED/PUSHED` requires separate Git evidence.
No percentage of completion is used. Existing test reports are historical
evidence, not tests rerun by this realignment.

#### R6.5 — Journey A / contract, backend, then product

- **User objective / concrete delivery:** allocate a limited explicit monthly
  budget across selected Goals and compare certified effects; deliver the entry
  contract below, bounded backend orchestration, then the existing minimal UI.
- **Prerequisites / source / contract:** published R6.1–R6.4; owned Goal facts
  plus user assumptions; approved D1–D3 and `GOAL_BUDGET_PREVIEW_CONTRACT.md`.
  No Health or portfolio source.
- **Main implementation:** existing batch reader and the R6.5-B orchestrator; compare
  distributions per Goal through `ScenarioComparisonEngine`. No engine rewrite.
- **Tests / manual validation:** budget arithmetic oracle, null/zero, ownership,
  comparison equivalence, no writes/N+1, route compatibility; manually select two
  Goals, edit allocations, exceed budget, compare, cancel edits and switch user.
- **Acceptance / AI / state / next action:** exact certified results and visible
  budget states with no recommendation or real-Goal changes; no AI dependency;
  `R6.5-A CONTRACT APPROVED / B IMPLEMENTED — FOCUSED TESTS PASSED — CHECKPOINT PENDING / C PLANNED — NOT STARTED`;
  backend checkpoint requires separate authorization; R6.5-C follows backend
  validation/publication under its own scoped UI task.

#### R6 — Journey B / Health–Smart Context–Planning–FIRE composition

- **User objective / delivery:** inspect observed monthly facts beside explicit
  planning assumptions and navigate to FIRE without retyping eligible context.
- **Prerequisites / source / contract:** R6.5 journey accepted; Health source
  period/completeness, R2 B5/B7 allowlists and single-user guard; consumer contract
  required. 10.3.7-A remains deferred; source expansion needs explicit approval.
- **Implementation:** offer eligible facts through existing authorities, never
  infer an effective budget, retirement spending or `GOAL_CURRENT_AMOUNT` for
  FIRE. A Goal–FIRE financial link requires a separate ADR-025 reconciliation.
- **Tests / manual:** partial/closed months, gross-vs-observed income, stale and
  missing data, source switching, explicit Use/override, two identities; verify
  that a reference is never represented as guaranteed forward affordability.
- **Acceptance / AI / state / next:** provenance and assumptions remain distinct;
  no AI required; `CONTRACT REQUIRED`; approve one bounded consumer task, not a
  sustainable-capacity formula by implication.

#### R4-C/F prerequisite — Journey C / operational safety contract

- **User objective / delivery:** provider/tool execution can be refused safely
  before data leaves the authorized boundary; define durable audit and HMAC
  operations, retention, access, deletion, and recovery before choosing storage.
- **Prerequisites / source / contract:** closed R4-A/B/C and ADR-030;
  `MAT-R4C-01` and `INF-R4C-01`; separate persistence approval if needed. A
  volatile test sink and legacy `ai_runs` are not an approved durable design.
- **Implementation / tests:** later R4-F guard uses the existing audit port;
  fault-inject sink outage, authorization failure, key failure and cancellation,
  proving zero provider/tool dispatch when required audit cannot be guaranteed.
- **Manual / acceptance / AI / state / next:** inspect redacted evidence and
  refusal before any live operational call; no secrets/raw financial payloads;
  prerequisite for operational AI; `CONTRACT REQUIRED`; obtain bounded approval.

#### R4-D and D.3 — Journey C / local runtime candidate

- **User objective / delivery:** explain a supplied certified synthetic result
  offline through one Ollama adapter, with explicit unavailability on failure.
- **Prerequisites / source / contract:** R4-A/C, approved assisted D checklist;
  Qwen 3.5 4B initial baseline, exact runtime/digest/config verified at execution;
  no installed-state assumption from old reports or automatic downloads.
- **Implementation / tests:** adapter over `AIProvider`, bounded health/discovery,
  generation/cancellation/closure; mocked errors and authorized offline fixture
  replay, schema/numeric/source validation, resource and latency measurements.
- **Manual / acceptance / AI / state / next:** verify cloud disabled/loopback and
  operation offline; acceptance is a tested adapter and explicit limitations,
  not real-data approval. R4-F still gates operational dispatch. `LAB TESTED /
  ADAPTER NOT IMPLEMENTED`; authorize D.3 code and finite calls separately.

#### R4-E — Journey C / online adapter

- **User objective / delivery:** an explicit Gemini option, never automatic
  fallback from offline mode; one adapter, not another Advisor architecture.
- **Prerequisites / source / contract:** R4-A/C, remote policy, authorized
  server-side configuration; official SDK/model/policy verification at execution.
  Free-tier access never authorizes real financial data; no OpenAI default.
- **Implementation / tests:** one `google-genai` adapter; mocked 429/quota/503,
  deadline, cancellation, invalid output and SDK retry accounting. Live synthetic
  calls require explicit budget/quota permission and applicable audit gates.
- **Manual / acceptance / AI / state / next:** verify consent and provider identity,
  no key in UI/logs; compatible strict response with safe failure; AI-specific;
  `NOT STARTED`; approve adapter scope, then guarded online pilot.

#### R4-F — Journey C / guarded dispatch and optional hybrid routing

- **User objective / delivery:** predictable selection, bounded failures, and no
  silent remote transmission; `LOCAL_ONLY` default and `HYBRID` opt-in.
- **Prerequisites / source / contract:** D/E capability evidence, approved durable
  audit implementation, pre-execution guard and policy; evidence registries, not
  a model ranking guessed from lab pass totals.
- **Implementation / tests:** one retry controller, deadlines/budgets, approved
  read-only tools and mode gates; test consent/isolation, no provider fallback in
  local mode, durable-sink failure before dispatch and no financial writes.
- **Manual / acceptance / AI / state / next:** deliberately disable a provider
  and audit sink and inspect safe refusal; security gates passed before live
  product use; `BLOCKED` on prerequisites; implement only under a scoped task.

#### R4-G — Journey C / comparative offline and online evidence

- **User objective / delivery:** know which eligible configuration can faithfully
  explain certified results; one comparable synthetic pilot, not endless audits.
- **Prerequisites / source / contract:** approved call/token/cost ceilings and
  stop rules; D/E adapters and F gates for runtime-path tests; reuse immutable
  lab evidence and the test plan in `AI_AND_LLM.md`, not lab verdicts as certification.
- **Implementation / tests:** equivalent versioned fixtures/expected outputs,
  bounded runner and separate quality/security/availability/performance results;
  use backend-certified synthetic R6.4/R6.5 outputs after R6.5 is tested.
- **Manual / acceptance / AI / state / next:** review explanations blind where
  useful, without overriding numerical failures; complete reproducible pilot or
  explicit failed/inconclusive stop, never fabricated ranking. `EXECUTION NOT
  AUTHORIZED`; specify at queue item 4, execute after safety/adapter readiness.

#### R6 bounded AI entry and R4-H boundary — Journeys C/F

- **User objective / delivery:** ask for an explanation of a selected certified
  analysis, not a second chat per page or automatic financial recommendation.
- **Prerequisites / source / contract:** accepted R4 safety and pilot evidence,
  task-specific data approval, minimum certified result/source schema. R4-B's
  five read tools do not currently authorize a Planning/FIRE calculation tool;
  any registry extension requires its own contract. Historical Advisor proposals
  remain proposals, including the zero-tool interpretation option.
- **Implementation / tests:** one bounded contextual entry after authorization;
  exact source/numeric fidelity, abstention, injection, identity clearing,
  unavailable providers; no automatic scenario execution or persistence.
- **Manual / acceptance / AI / state / next:** user verifies cited results and
  limitations; `PRODUCT INTEGRATED` only after acceptance. `CONTRACT REQUIRED`;
  R4-H personalization/memory is not implicitly activated and needs its own
  disposition before declaring the selected R4 closure scope complete.

#### R7 — transversal closure, not Portfolio implementation

- **Journey / user objective / delivery:** A–C and bounded F; a coherent accepted
  baseline with one fresh-context independent validation report.
- **Prerequisites / source / contract:** R1–R6 closure evidence; operational R4
  blockers resolved or an explicit separately approved scope/gate amendment.
  A contract, lab pilot or endpoint alone never closes a product journey.
- **Implementation / tests / manual:** no feature implementation; review financial
  authority, context/provenance, auth/privacy, AI gates, regression evidence and
  the agreed responsive/accessibility/manual matrix without inventing coverage.
- **Acceptance / AI / state / next:** explicit closure decision with unresolved
  blockers visible; R4 validation is required, full future Copilot/Portfolio is
  not a circular prerequisite. `BLOCKED / NOT STARTED`; define the bounded
  closure checklist after the preceding accepted journeys. Only then 10.5-B.

#### 10.5-B and contracted 10.5 delivery — Journey D

- **User objective / delivery:** understand certified composition/concentration;
  first lock the preserved 10.5-A valuation and temporal contract, then implement
  its separately approved MVP.
- **Prerequisites / source / contract:** R7 closed; `total_atual` direction and
  deferred performance decision remain resolved; complete position valuation,
  ownership, currency and aggregate reconciliation rules still need contract.
- **Implementation / tests / manual:** governed read model only after approval;
  completeness, date mismatch, Decimal and ownership tests; manually inspect
  source/unavailable disclosures. No inferred Goal allocation or double counting.
- **Acceptance / AI / state / next:** source-backed composition without calling
  wealth evolution performance; AI not required; `PAUSED / BLOCKED`; resume
  10.5-B, do not repeat 10.5-A absent new contradictory evidence.

#### 10.6 and 10.7 — Journey E / watchlist, market and alerts

- **User objective / delivery:** follow chosen assets and sourced events; show
  the exact condition, time and facts behind an alert. Separate bounded tasks
  for watchlist, condition evaluation and Market/news; no bulk authorization.
- **Prerequisites / source / contract:** historical 10.5 completion gate; R3
  purposes/freshness, R3-G before eligible yfinance use, approved source rights,
  watchlist/rule lifecycle and notification contracts. Focus remains deferred.
- **Implementation / tests / manual:** reuse providers/read boundaries, no second
  yfinance system; test stale/missing data, source attribution, ownership, news
  injection and rule determinism; inspect UI-only conditions before any schedule.
- **Acceptance / AI / state / next:** factual conditions, no invented causes or
  trading advice; deterministic core has no AI dependency, summaries do;
  `CONTRACT REQUIRED / NOT STARTED`; activate only after preceding gates.

#### Copilot / 10.9 briefing / conditional 10.10 — Journey F

- **User objective / delivery:** explain what changed across certified domains,
  then an on-demand sourced briefing; scheduled delivery is a later bounded task.
- **Prerequisites / source / contract:** accepted R4 and bounded R6 entry, domain
  availability (10.5 for portfolio claims), Market for news claims; explicit
  aggregation/minimization, retention, delivery and scheduling contracts.
- **Implementation / tests / manual:** reuse one runtime and approved capabilities;
  no arbitrary SQL or financial recomputation; test traceability, abstention,
  permissions, injection, outages, freshness, and no unauthorized tool calls;
  user checks explanation usefulness and cited evidence.
- **Acceptance / AI / state / next:** attributable answer, no unsupported figures
  or recommendation; AI required; `CONTRACT REQUIRED / NOT STARTED`. No scheduler
  or memory by implication. 10.10 remains conditional on demonstrated need,
  not the default way to build Copilot.

### R6.5 approved contract and next executable task

TSK-R6.5-A expressly approved D1–D3, adding exact equal allocated totals in A/B.
The phase-specific owner is
[`GOAL_BUDGET_PREVIEW_CONTRACT.md`](GOAL_BUDGET_PREVIEW_CONTRACT.md), including
the complete R6.5-B implementation/test inventory. Its contract is compatible
with the existing Planning boundaries: one owned batch read and one certified
scenario comparison per Goal; no Engine changes. Separately authorized R6.5-B
now implements that boundary and passed 192 new domain/API tests plus a
946-test relevant regression selection (including those 192), on 2026-10-29.
Its status is `IMPLEMENTED / FOCUSED TESTS PASSED / CHECKPOINT PENDING`.
No commit, push or deploy occurred. R6.5-C is `PLANNED / NOT STARTED`.

#### Historical R6.5 entry proposal — superseded by the approved microcontract

The following proposal is preserved from the preceding realignment, not an
active specification or pending approval request. The approved microcontract
supersedes its provisional names, missing equal-total restriction and optional
inverse-solve baseline. In particular, R6.5 projects chosen contributions;
it does not execute the R6.4 required-contribution solve. Historical
`PROPOSED / PENDING` wording below describes only the earlier decision point.

**Authority:** objective and restrictions approved by the owner in
TSK-PRODUCT-ROADMAP-REALIGNMENT. The details below are `PROPOSED / PENDING D1–D3`,
not a locked API contract or permission to code. This section carries the entry
decision in the existing owner; no competing roadmap or architecture file is
created. After approval, the implementation task can lock a phase microcontract
and link here rather than duplicating this proposal.

**Reuse verified before choosing an API:** `GoalBatchContributionPreviewService`
uses `RequiredContributionSolver` and deliberately accepts no allocated
contribution: the inverse solver replaces its template contribution. Adding a
budget to that request would not evaluate a distribution. The existing
`POST /planning/scenarios/compare` accepts an optional **single shared target**;
it cannot compare several different Goals as if they were that same target.
Its `ScenarioComparisonEngine.compare` can, however, be invoked **once per
Goal**, comparing reference/alternative allocations for that same Goal and
preserving its certified deltas and target-achievement statuses.

The inspected public APIs have no limited-budget response. Proposed additive
endpoint: `POST /api/v1/planning/goals/budget-preview`; proposed DTOs:
`GoalBudgetPreviewRequestDTO` / `GoalBudgetPreviewResponseDTO`. This is one
orchestration, not another progress/context endpoint. Keep all R6.1–R6.4 and
five original Planning contracts unchanged; use direct services, no internal HTTP.

**Proposed bounded request:** ordered `goal_ids` (1–20 unique owned UUIDs),
`monthly_budget`, shared explicit R6.4 assumption fields (`as_of_date`,
`expected_return_rate`, `return_type`, `output_mode`, conditional
`inflation_rate`, `horizon_months` 1–1200, `rate_basis=EFFECTIVE_ANNUAL`,
`contribution_timing=END_OF_MONTH`), explicit `target_value_basis`, two ordered
scenarios with unique `scenario_id`, explicit `reference_scenario_id`, and one
`scenario_monthly_contribution` per selected `goal_id` per scenario. No target,
current wealth, portfolio selector, or provenance supplied by the client.
The rate is a finite Decimal annual fraction greater than -1, never an implicit
percentage/default. Missing/extra/duplicate allocations reject the request;
budget and allocations are finite nonnegative cent-scale Decimal strings,
including explicit zero. Null is invalid for required assumptions.

**Proposed output / arithmetic:** each scenario echoes its budget and ordered
allocations and returns `allocated_monthly_amount = sum(explicit allocations)`,
`remaining_monthly_amount = monthly_budget - allocated_monthly_amount` (signed),
`available_monthly_amount = max(remaining, 0)` and
`exceeded_monthly_amount = max(-remaining, 0)`, all Decimal strings. These are
budget-accounting identities, not a new projection engine. The total includes
allocations to an owned Goal whose projection is unavailable, so intended
spending is never hidden. No Goal `current_amount`, projected wealth, or required
contribution is summed into a portfolio/affordability total.

Each Goal returns cadastral source/provenance, availability/impediment, R6.4's
required contribution under the common assumptions, and each scenario's
certified final wealth, target status/time and same-Goal deltas from the existing
comparison result. No aggregate wealth ranking or automatic redistribution.
Unavailable Goal target/current facts retain R6.4's reasons; projection values
remain null, not zero. Missing or foreign IDs fail the whole request with the
same non-enumerating 404. Invalid collection/assumptions yield 422; unexpected
errors stay generic. Status/type facts do not acquire a new lifecycle rule.

**Orchestration and cost:** one `get_goals_by_ids` SQL ownership-filtered read;
reuse `current_amount_as_initial_wealth`; one R6.4 service invocation for the
required-contribution baseline and one comparison invocation per calculable
Goal. The proposed two-scenario cap bounds comparison work at 40 scenario
evaluations for 20 Goals (solvers may perform additional projections), in
addition to bounded inverse solves; it is a processing limit,
not financial policy. Preserve source precision, local Decimal context and
engine rounding; no formula duplication, writes, caches, migrations or external
calls. `target_date` is not a horizon. Initial wealth is only each Goal's own
`GOAL_CURRENT_AMOUNT`, never a combined Goal balance or MyProfit.

**Material decisions to approve before code:**

- **D1 — scenario envelope:** recommend exactly two distributions (reference
  and alternative), same Goal set, monthly budget, as-of, horizon, return and
  output basis; only allocation varies. More scenarios or per-Goal premises
  require an explicitly bounded contract, not an implementation default.
- **D2 — budget value basis:** recommend nominal-only V1 (`NOMINAL` return,
  output and target basis; no inflation input), preserving constant nominal
  allocations. If real output is required now, first define whether the budget
  and contributions are fixed purchasing power or nominal cashflows and their
  compatibility with the unchanged engine. Do not silently transform them.
- **D3 — excess budget:** recommend returning an over-budget scenario and its
  certified effects with explicit excess, rather than rejecting it or reducing
  allocations automatically. It remains a hypothetical comparison, not a claim
  of financial feasibility. Zero budget is valid and exposes any excess.

**Health/capacity decision:** no automatic Health-derived budget in R6.5.
The user's budget is an `ASSUMPTION`, not Profile gross income or certified
sustainable capacity. 10.3.7-A remains `DEFERRED — INSUFFICIENT CONTRACT / DATA`:
window, minimum history, partial months, deficits, anomalies, statistic,
currency and missing/zero rules require separate approval. Journey B can first
expose eligible references with provenance and explicit choice under its own
consumer contract; it cannot quietly bypass R2's allowlists or ADR-025.

**Acceptance tests:** independent Decimal budget oracle (under/equal/over,
zero budget, cents and large values); equivalence to existing R6.4/comparison
results per Goal; null/zero/unavailable facts; no cross-Goal target reuse;
reference equality; duplicate/missing IDs/allocations; two-user isolation and
uniform 404; rate/basis/horizon/collection limits; one Goal query; no writes,
MyProfit, persistence or new engine; OpenAPI and all prior routes unchanged.
The future UI must preserve edits/identity cleanup and transient result semantics,
show exact backend values, and await explicit execution. No frontend arithmetic
becomes financial authority. No LLM dependency, optimization or advice.

## Foundation and phase inventory (not a second execution queue)

| Order | Phase | Outcome | Status | Hard dependency |
|---:|---|---|---|---|
| — | 10.R2 | Smart Financial Context: Profile persistence, declared context, observed recurring-income candidates, human decisions, feature-specific composition, provenance | `IMPLEMENTED / VALIDATED / CLOSED` | R1 locked; ADR-028 and R2 contract |
| 1 | 10.R3 | External Context Layer: adapters, normalization, observation store/cache, semantic class, freshness/status, macro/reference provider foundations | `R3-C CLOSED / R3-D CLOSED / R3-E1 CLOSED / R3-E2 CLOSED / R3-E3 CLOSED / R3-E4 INDEPENDENTLY APPROVED / R3-F1 CLOSED / R3-I INDEPENDENTLY APPROVED` | R2 taxonomy and context boundary; ADR-029 |
| 3 | 10.R4 | AI Runtime Foundation: provider abstraction, approved read-only tools, privacy, auditability, errors/timeouts/cost telemetry, minimal surface | `R4.0 CONTRACT APPROVED / R4-A CLOSED / R4-B CLOSED / R4-C CLOSED / LATER OPERATIONAL INCREMENTS GATED` | R2 + R3 context semantics and deterministic tools; ADR-030 |
| 4 | 10.R5 | Design, navigation, and theme: semantic tokens, System/Light/Dark, shell/IA, responsive analytical and interactive patterns | `IMPLEMENTED / AUTOMATED GATES PASSED / TECHNICAL CHECKPOINT COMMITTED / PUSHED / USER VISUAL ACCEPTANCE APPROVED FOR CURRENT BASELINE / CLOSED` | R1 IA; R2/R3 context presentation requirements |
| 5 | 10.R6 general gate | Experience recomposition: Wealth Home, Goals, Planning, FIRE, and appropriate Profile/Settings integration | `SEQUENCING GATE SATISFIED / READY FOR EXPLICITLY CONTRACTED INCREMENTS` | R5 closed; relevant R2/R3 foundations available; operational AI still requires remaining R4 gates; every increment needs its own contract and authorization |
| 5.1 | 10.R6.1 | Goals → Planning integration governed by `PLANNING_GOAL_CONTEXT_READ_MODEL_PROPOSAL.md` | `IMPLEMENTED / AUTOMATED GATES PASSED / USER MANUAL ACCEPTANCE REPORTED / COMMITTED / PUSHED` | Historical project-owner sequencing exception; approved microcontract; all financial/security/auth/ownership/test gates preserved |
| 5.2 | 10.R6.2 | Deterministic Goal Progress read model governed by `GOAL_PROGRESS_READ_MODEL_CONTRACT.md` | `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED` | R5 closed; R6 gate satisfied; explicit project-owner authorization; existing owned Goal reader |
| 5.3 | 10.R6.3 | Consolidated Goal Monitoring read model governed by `GOAL_MONITORING_OVERVIEW_READ_MODEL_CONTRACT.md` | `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED` | R6.2 published; explicit project-owner authorization; existing owned Goal batch reader and certified R6.2 calculation |
| 5.4 | 10.R6.4 | Joint Goal contribution preview governed by `GOAL_BATCH_CONTRIBUTION_PREVIEW_CONTRACT.md` | `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED` | Published at `40a23566b3b068e26cb8bd3ae94bc7ed060ec4b0` |
| 5.5 | 10.R6.5-A/B/C | Limited monthly budget across owned Goals | A `CONTRACT APPROVED / READY FOR BACKEND`; B `IMPLEMENTED / FOCUSED TESTS PASSED / CHECKPOINT PENDING`; C `PLANNED / NOT STARTED` | `GOAL_BUDGET_PREVIEW_CONTRACT.md`; B separately authorized; no publication |
| — | Later R6 increments | Remaining bounded recomposition | `NOT AUTHORIZED` | Explicit contract and scoped task; no authorization inherited from R6.5 |
| 6 | 10.R7 | Fresh-context independent product, architecture, contract, privacy, UX, and regression validation | `NOT STARTED` | R1–R6 complete |
| 7 | 10.5-B | Resume Portfolio Intelligence contract lock using the realigned architecture | `PAUSED / PENDING WEALTH OS REALIGNMENT` | R7 closure; preserve 10.5-A |

R2 must not become an AI feature. R3 must not silently implement the final
Explore product. R4 is infrastructure, not the complete Copilot. R5 cannot
rewrite financial engines. R6 composes validated capabilities and may change
their interaction/presentation only within explicit contracts. R7 decides
realignment closure.

The user explicitly approved the bounded R5 contract on 2026-10-24. R5 reuses
the W2–W4.2 product increments as baseline evidence and implements only design,
navigation, theme, accessibility, responsive, and localization stabilization.
Its technical checkpoint is committed and pushed at
`1fae590fb316b4f9d9584aad23cdde4fe8f3af9b`. On 2026-10-27 the project owner
accepted the current visual baseline and deferred later UI/UX improvements to
backlog without claiming an exhaustive browser, viewport, state, or manual
accessibility matrix. R5 is closed and the general R6 gate is satisfied. This
does not satisfy the R7 gate or authorize 10.5-B.

The main implementation path follows the single delivery queue above. Published
deterministic R6 capabilities do not prove operational R4 completion. R4's
remaining adapter/security/test gates must be addressed before R7 closure;
research cannot change an authorization or dependency gate.

**R5 → R6 sequencing exception (2026-10-25):** the project owner explicitly
authorized only R6.1 Goals → Planning to begin before R5 visual acceptance. The
authorization is a sequencing exception, not R5 closure. R6.1 is now
`IMPLEMENTED / AUTOMATED GATES PASSED / USER MANUAL ACCEPTANCE REPORTED /
COMMITTED / PUSHED`. The acceptance report covers the experience tested by the
user and does not claim a complete manual matrix or independent R6 closure. On
2026-10-27 the later R5 visual acceptance resolved the general sequencing gate;
the exception remains historical evidence of why R6.1 began earlier. The
exception changes no
financial, Decimal, security, authentication, ownership, test, certification,
or R5 regression requirement, and no later phase or increment inherits it.

**R6.2 authorization (2026-10-27):** after the closure review established that
the placeholder itself authorized no implementation, the project owner supplied
the missing bounded task and approved `GOAL_PROGRESS_READ_MODEL_CONTRACT.md`.
R6.2 implements only nominal cadastral Goal progress through an authenticated,
owned, read-only endpoint over the existing Planning Goal reader. It uses
Decimal for signed gap and uncapped percentage, performs no writes or portfolio
reads, and changes no engine, persistence, legacy Goals contract, or Planning
POST. Focused tests passed and its checkpoint is committed/pushed at
`7828f64a2d8d0a25605bcb2c459775e176f99292`.

**R6.3 authorization (2026-10-27):** the project owner explicitly approved the
bounded `GOAL_MONITORING_OVERVIEW_READ_MODEL_CONTRACT.md`. R6.3 reuses the
existing owned batch Goal reader and certified R6.2 calculation to expose one
authenticated, ordered, read-only overview. It classifies each Goal exactly
once, emits factual data-quality flags, and aggregates counts only—never Goal
money, portfolio wealth, or contributions. Focused Goals/Planning tests pass;
its checkpoint is published at `1f743b297449d17064d68376891edab88432e1d2`.

**R6.4 authorization (2026-10-27):** the project owner explicitly approved the
bounded `GOAL_BATCH_CONTRIBUTION_PREVIEW_CONTRACT.md`. R6.4 accepts 1 through 20
unique owned Goal IDs plus an explicit horizon and rate assumptions, loads the
selection in one ownership-filtered query, and delegates each calculable item
to the certified Required Contribution solver using only
`GOAL_CURRENT_AMOUNT`. It returns ordered individual previews and factual
unavailable states, with no Goal-date horizon inference, Goal-wealth
aggregation, portfolio/MyProfit read, recommendation, persistence, migration,
or frontend. Focused Goals/Planning tests pass; its checkpoint is published at
`40a23566b3b068e26cb8bd3ae94bc7ed060ec4b0`. The later 2026-10-28 task authorizes
R6.5's objective and contract definition only, as recorded above.

R2 implementation is decomposed in
`SMART_FINANCIAL_CONTEXT_IMPLEMENTATION_PLAN.md` as B1 declared-context
persistence/ownership, B2 declared Profile API, B3 recurrence evidence engine,
B4 decision state/API, B5 feature-specific composition, B6 Profile experience,
B7 consumer foundations, and B8 stabilization/independent validation. B1 through
B7 are `IMPLEMENTED / VALIDATED`; B6 remediation is independently approved
with M1–M5 closed and no blocking or material findings. B7 adds only typed,
read-only consumer boundaries that delegate to B5 and leave effective inputs,
engines, public APIs, and product experiences unchanged. The active next task
was `10.R2-B8 — Stabilization & Independent Validation`, which is independently
approved. MR1 diagnosed the physical-schema/Alembic-version drift; MR2 removed
the runtime `create_all` root cause, made Alembic authoritative, and isolated
tests from the active database, then passed independent review. MR3 reconciled
the active Alembic bookkeeping to `2d6b4f8a9c1e`, verified `upgrade head` as a
no-op, and preserved schema and financial data. R2 is closed. R3 is in progress
through the closed R3-C and R3-D foundations; operational R3 persistence exists,
and R3-E2 now supplies a persistence-free provider path. R3-A completed the
source/architecture
audit. R3-B produced
`EXTERNAL_CONTEXT_CONTRACT.md`, `EXTERNAL_SERIES_REGISTRY.md`,
`EXTERNAL_CONTEXT_IMPLEMENTATION_PLAN.md`, and accepted ADR-029. R3-B.1
remediated SQLite decimal storage, revision/reversion identity, bitemporal
commit semantics, and refresh/freshness/acquisition separation. They are
approved and locked after independent review and explicit user approval on
2026-10-09. R3-B.2 closes the normative `content_fingerprint_v1` formula and
was independently verified on 2026-10-10 with 0 blocking, 0 material, 0 minor,
and 2 informational findings. R3-C implements and validates the pure domain,
strict normalization, executable allowlist, economic identity, typed errors,
and Content Fingerprint V1 boundary. Its independent implementation review
also returned 0 blocking, 0 material, 0 minor, and 2 informational findings.
R3-C is `IMPLEMENTED / VALIDATED / INDEPENDENTLY APPROVED / CLOSED`. The user
explicitly approved the R3-D.1 registry-version and UTC logical knowledge-time
decisions on 2026-10-10. Gemini 3.8 Flash High independently approved the
eight-document amendment delta (0 blocking, 0 material, 0 minor, 2
informational). R3-D.1 is `CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED
/ VERSIONED`. R3-D is implemented, validated on SQLAlchemy 2.0.21 and 2.0.51,
and independently approved by Gemini 3.8 Flash High (0 blocking, 0 material,
0 minor, 2 informational). Its migration, transaction, concurrency, and
regression gates used only disposable SQLite databases; the active database was
untouched. R3-D is `CLOSED / PUSHED` at baseline
`d62012413f7ec956b070c0fe21420be1f29403ff`. The user explicitly approved the
R3-E.0 decisions on 2026-10-11 and the Deferred Ingestion & Acquisition
Finalization V1 remediation on 2026-10-12. Gemini 3.8 Flash High approved the
targeted remediation review with 0 blocking, 0 material, 0 minor, and 2
informational findings. The amendment is `CONTRACT APPROVED / INDEPENDENTLY
VERIFIED / LOCKED / CHECKPOINT AUTHORIZED`; `MAT-R3E0-01`, `MIN-R3E0-01`,
`MIN-R3E0-02`, and `INF-R3E0-01` are resolved, with the latter retained as a
governed limitation. `INF-R3E0-02` (scalar discontinuous coverage) and
`INF-R3E0-03` (no persistent acquisition journal) remain explicit V1 risks.
Gemini 3.8 Flash High approved the R3-E1 independent adversarial code review
with 0 blocking, 0 material, 0 minor, and 3 informational findings:
`INF-R3E1-01` scalar durable coverage, `INF-R3E1-02` no persistent
journal/distributed idempotency, and `INF-R3E1-03` the unchanged
Investments/MagicMock baseline. `INF-R3D-01` and `INF-R3D-02` remain preserved.
R3-E1 is `CLOSED / PUSHED`. R3-E2 is `CLOSED / PUSHED`: it owns deterministic
DAILY multichunk planning, bounded sequential mocked-transport execution, strict SGS certification, and
typed external partial results without persistence. R3-E3 is `CLOSED / PUSHED`
at `686d64b49731a44a56e0d7fd8b44752ee1b663d8`: it adds only the internal application
orchestrator that binds explicit acquisition intent to the existing R3-E2
provider and R3-E1 deferred-ingestion/finalization boundary. R3-E4 now adds the
internal-only explicit trigger, pure eligibility policy, short-lived read-only
sync-state boundary, and typed manual result while delegating all acquisition
and finalization to R3-E3. It is `IMPLEMENTED / TESTED / INDEPENDENTLY APPROVED
/ IMPLEMENTATION CHECKPOINT`. No live BCB data has been acquired.

The R3-E.0 approval checkpoint is preserved. R3-E1 implements only its approved
store compatibility increment and its independent adversarial review is
approved. Gemini 3.8 Flash High independently approved R3-E2 with 0 blocking,
0 material, 0 minor, 2 new informational findings, and 5 preserved findings.
R3-E3 implementation and local validation are independently approved by Gemini
3.8 Flash High: 0 blocking, 0 material, 0 minor, 0 new informational findings,
and 7 preserved informational findings. Its controlled Git checkpoint is
published. Gemini 3.8 Flash High independently approved the R3-E4 adversarial
code review with 0 blocking, 0 material, 0 minor, 1 new informational finding,
and 7 preserved informational findings. `INF-R3E4-01` remains open: a future
authenticated caller exposing typed historical reconciliation must enforce
specific administrative authorization, validate intent/interval, and prevent
anonymous or cooldown-bypassing access. R3-E4 itself remains internal-only and
introduces no endpoint or RBAC change; it is ready for its implementation
checkpoint.

R3-F.0 decisions D1-D6 were explicitly approved on 2026-10-14 and are now
documented. They close the purpose enum to Market interest-rate, inflation, and
FX reference reads; restrict each purpose to its approved Registry V1 series;
and reserve consumption for a future internal Market context composer. The
contract requires explicit economic-date and UTC knowledge-time cuts, point
lookup only, deterministic bitemporal `reference_replay`, a separate current
`operational_state_snapshot`, conservative policy-derived freshness, explicit
absence, exact Decimal, provenance, and preservation of the original economic
period. R3-F1 is `CLOSED / PUSHED`: its
internal read-only service delegates only to the certified Store reads, has no
runtime consumer, and reports `28 passed` focused plus `100 passed` with the
minimal Registry/Store regression selection. Its published checkpoint is
`30c4df058fd80923c37243252f4ee8fc6fa76dce`, and independent review reported
0 blocking, 0 material, and 0 minor findings.

### 10.R3 locked microphase sequence

| Task | Outcome | Status | Dependency |
|---|---|---|---|
| R3-A | External Context architecture/source audit | `AUDIT COMPLETE / APPROVED` | R2 closed |
| R3-B | Contract, official series registry, temporal/persistence decisions, implementation plan | `CONTRACT APPROVED / LOCKED` | R3-A |
| R3-B.1 | Pre-lock Decimal/revision/freshness contract remediation | `REMEDIATED / INDEPENDENTLY APPROVED` | R3-B remediated contract |
| R3-B.2 | Content Fingerprint V1 contract amendment | `APPROVED / LOCKED / VERSIONED` | explicit user approval and independent delta review |
| R3-C | Domain, strict normalization, executable allowlisted registry, Content Fingerprint V1 | `CLOSED / LOCKED` | R3-B.2 locked; independent implementation review approved |
| R3-D.1 | Registry Version V1 and UTC logical knowledge-time contract amendment | `APPROVED / LOCKED / VERSIONED` | explicit user approval and independent delta review on 2026-10-10 |
| R3-D | Bitemporal observation store, sync state, cache/freshness | `CLOSED / PUSHED` | baseline `d62012413f7ec956b070c0fe21420be1f29403ff`; deployment remains separately gated |
| R3-E.0 | Deferred Ingestion & Acquisition Finalization V1 remediation of the pending amendment | `CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED / VERSIONED / PUSHED` | Gemini 3.8 Flash High targeted remediation approval; documentation only |
| R3-E1 | Store Compatibility Adapter | `CLOSED / PUSHED` | Gemini 3.8 Flash High: 0 blocking/material/minor; three informational findings preserved |
| R3-E2 | BCB Provider | `CLOSED / PUSHED` | Gemini 3.8 Flash High: 0 blocking/material/minor; `INF-R3E2-01` and `INF-R3E2-02` preserved; baseline `2ae5114` |
| R3-E3 | Governed Ingestion | `CLOSED / PUSHED` | checkpoint `686d64b49731a44a56e0d7fd8b44752ee1b663d8`; seven findings preserved |
| R3-E4 | Manual Refresh | `IMPLEMENTED / TESTED / INDEPENDENTLY APPROVED / IMPLEMENTATION CHECKPOINT` | Gemini 3.8 Flash High: 0 blocking/material/minor; `INF-R3E4-01` open and seven prior informational findings preserved |
| R3-F.0 | Purpose Contract Definition | `CONTRACT APPROVED / DOCUMENTED` | user approval of D1-D6 and three mandatory refinements on 2026-10-14 |
| R3-F1 | Point-in-time External Reference Read Boundary | `CLOSED / PUSHED` | checkpoint `30c4df058fd80923c37243252f4ee8fc6fa76dce`; independent review 0 blocking/material/minor; no runtime consumer |
| R3-G | Existing market/yfinance boundary remediation under ADR-006 | `SEPARATELY GATED / NOT STARTED` | focused impact approval + R3 foundations; required before yfinance admission |
| R3-H | Focus expectations | `FOCUS DEFERRED / NOT IMPLEMENTED` | separate activation decision |
| R3-I | Independent stabilization | `INDEPENDENTLY APPROVED / DOCUMENTATION RECONCILED` | 234 transversal tests passed; no new code finding; eight historical informational findings preserved |

The reordering from the R3-A draft places persistence/freshness before live
provider ingestion so knowledge-time, revision, deduplication, and
last-known-good semantics exist before network data becomes operational. This
order is locked by ADR-029. Mandatory BCB-only closure scope is R3-C/D/E/F/I.
R3-G requires separate legacy-impact approval and is
mandatory before yfinance admission, not before a BCB-only closure. R3-H stays
deferred and cannot be reported as implemented.

R3-I technically approved the activated BCB-only scope, and its documentation
is reconciled; R3-I is not yet `CLOSED / PUSHED`. R3-G was not
activated, R3-H remains deferred, and the current roadmap defines no R3-F2.

### 10.R4 planned increment sequence

R4.0 approved the architecture contract and decomposition without automatically
authorizing every increment. R4-A is closed and pushed at
`bea92edb18872bd3e3603dc10ebc62bed8de8100`. R4-B is closed and pushed at
`8149e3d27a75c76ed6cc7f46fab60aabebd96396` after independent approval with
`84 passed` and `0 BLOCKING / 0 MATERIAL / 0 MINOR` new findings. R4-C has an
independently approved no-persistence implementation and is closed/pushed at
checkpoint `14cb65db1cddd5466523eefdca54c78affb3eca7`. Independent review records `77 passed`, `0 BLOCKING`, and `0
MATERIAL` active findings. Historical `MAT-R4C-01` is adjudicated
`INFORMATIONAL / FUTURE ACTIVATION BLOCKER`: R4-F must integrate and validate a
pre-execution audit guard before any operational provider or tool dispatch; a
`VOLATILE` sink never meets the required `DURABLE` guarantee. `INF-R4C-01`
preserves the future HMAC key-configuration/rotation/key-ID governance gate.
R4-D local preparation and user-observed validation are in progress; R4-E
through R4-H are not implemented.

| Task | Planned outcome | Current status | Hard dependency or gate |
|---|---|---|---|
| R4-A | Provider-Neutral Contracts | `CLOSED / PUSHED` | checkpoint `bea92edb18872bd3e3603dc10ebc62bed8de8100`; internal application service and deterministic fake only |
| R4-B | Authorization, Tools & Minimal Context | `CLOSED / PUSHED` | checkpoint `8149e3d27a75c76ed6cc7f46fab60aabebd96396`; exact five-tool read-only registry over R2; `84 passed`; 0 new blocking/material/minor findings |
| R4-C | Audit & Telemetry Boundary | `CLOSED / PUSHED` | checkpoint `14cb65db1cddd5466523eefdca54c78affb3eca7`; `77 passed`; `0 BLOCKING`/`0 MATERIAL` active; `MAT-R4C-01` historical designation adjudicated `INFORMATIONAL / FUTURE ACTIVATION BLOCKER`; persistence, definitive retention, `ai_runs`, and migration not authorized |
| R4-D | Ollama Local Adapter | `R4-D.2 USER-OBSERVED VALIDATION RECORDED / TECHNICAL CANDIDATE ONLY` | R4-A/R4-C; Ollama 0.40.5 LOCAL_ONLY; Qwen 3.5 4B Q4_K_M `d8b0f5e9760c`; no FinAnalytics provider activation or production certification |
| R4-E | Gemini Resilient Adapter | `PLANNED / NOT AUTHORIZED` | R4-A/R4-C; current official SDK verification; adapter integration approval is separate from real-financial-data transmission approval |
| R4-F | Evidence-Based Hybrid Router | `PLANNED / NOT AUTHORIZED` | R4-D/R4-E capability and health evidence; mandatory pre-execution audit-guard integration/validation before operational provider or tool dispatch; `LOCAL_ONLY` default; explicit fallback policy |
| R4-G | Benchmark Harness | `PLANNED / EXECUTION NOT AUTHORIZED` | eligible model catalog; synthetic reference set; separate quota, schedule, download, provider-call, and budget approval |
| R4-H | Personalization & Memory Contract | `PLANNED / NOT AUTHORIZED` | authorized preferences and certified retrieval first; any persistence or training requires a separate gate |

R4-D contains an assisted internal checklist rather than new normative phases:

| Checklist | Scope | Current status |
|---|---|---|
| R4-D.0 — Hardware & Environment Preflight | Read-only OS, CPU, RAM, GPU, VRAM, driver, disk, and candidate-fit evidence | `COMPLETE / HARDWARE READY` |
| R4-D.1 — Assisted Ollama Installation | Current official instructions, service/PATH/version, cloud disabled, loopback and exposure checks | `0.40.5 INSTALLED / USER-OBSERVED LOCAL_ONLY` |
| R4-D.2 — Local Model Setup | Hardware-based selection, separately authorized download, digest/license/quantization and offline structured-output validation | `USER-OBSERVED VALIDATION RECORDED / TECHNICAL CANDIDATE / NOT PRODUCTION CERTIFIED` |
| R4-D.3 — Performance & Adapter Validation | Cold/warm, latency, tokens/s, resources, context, concurrency, and local-only adapter checks | `DEFERRED / FORMAL BENCHMARK AND ADAPTER VALIDATION NOT AUTHORIZED` |

The project must provide exact commands, expected evidence, side effects, and
objective success/stop criteria at each assisted R4-D gate. R4.0 authorizes no
installation, download, provider call, benchmark, expense, persistence,
endpoint, frontend, scheduler, or migration. Proposed models, retention
periods, circuit-breaker thresholds, and budgets are not operational settings.

The user-approved candidate order for the R4-D.2/R4-D.3 work
is Qwen 3.5 4B `Q4_K_M` first, Qwen 3.5 9B `Q4_K_M` second, and PrismML Bonsai
8B GGUF `Q1_0` third as an experimental candidate. Bonsai is Qwen3-8B-based,
not Qwen 3.5; its published approximately 8.19B parameters, 1.16 GB file, and
Apache 2.0 license do not prove total VRAM, quality, or Ollama `0.40.5`
compatibility. A compatible llama.cpp may require a separate gate, and adverse
external tool-calling evidence must be tested locally. The 9B candidate must be
evaluated for full-GPU fit versus CPU/GPU offload. The host's four declared
8 GB DDR4-2400 modules imply at most 76.8 GB/s theoretical bandwidth if
effective quad-channel operation is verified. Equivalent, entirely offline
synthetic financial tasks must compare Portuguese and financial interpretation,
structured JSON, Decimal/provenance preservation, tool selection, abstention,
grounding/hallucination, RAM, VRAM, GPU/CPU layer placement, latency, tokens/s,
context consumption, and quality; no candidate wins without evidence. Ollama
is the initial runtime and direct llama.cpp remains a future comparison. The
earlier candidate-planning update itself authorized no model download,
execution, runtime installation, or benchmark; subsequent actions remained
subject to their own explicit gates.

R4-D.2 user-observed evidence records Ollama `0.40.5` in `LOCAL_ONLY` mode,
Qwen 3.5 4B `Q4_K_M` model ID `d8b0f5e9760c`, CUDA execution on the RTX 5060
with `33/33` layers on GPU, context `4096`, and concurrency `1`. Thinking-off
synthetic tests produced syntactically valid JSON at approximately `80-84
tokens/s` warmed and approximately `3.5-4.9 seconds` for the tested warmed
responses. Source fidelity is not yet established; the model is a technical
candidate only and is not production certified.

Thinking on is `NOT APPROVED IN TESTED CONFIGURATION`: JSON with `1800` tokens
ended with no final answer and `done_reason=length`; without JSON and with
`3000` tokens, the final answer was partial with the same completion reason,
while generation remained near `81 tokens/s`. This result neither expands the
token budget automatically nor establishes a universal model defect. Initial
loads also showed intermittent GPU-discovery timeouts before successful
initialization. Future gated work must validate empty and partial responses,
sources, grounding, and financial conclusions rigorously. It must not activate
operational integration before R4-F integrates and validates the mandatory
pre-execution guard with `DURABLE` audit.

## Closed and preserved baseline

| Phase | Status |
|---|---|
| 10.1 Goals | `IMPLEMENTED / VALIDATED` |
| 10.2 Financial Health | `IMPLEMENTED / VALIDATED` |
| 10.3 Planning | `VALIDATED / CLOSED` |
| POST-10.3 UX | `VALIDATED / CLOSED` |
| 10.4 FIRE | `VALIDATED / CLOSED` |
| 10.5-A Portfolio audit | `AUDIT COMPLETE / USER DECISIONS RESOLVED` |
| 10.R0 | `AUDIT COMPLETE` |
| 10.R1 | `ARCHITECTURE / DOCUMENTATION LOCKED` |
| 10.R2 | `IMPLEMENTED / VALIDATED / CLOSED` |

The former 10.6–10.12 sequence is `SUPERSEDED / HISTORICAL` as an active queue.
Its useful intentions are represented by R2–R7 or remain post-10.5 candidates;
it does not independently authorize implementation.

## Historical roadmap overview (non-authorizing)

| Phase | Name | Status | Depends On | Est. Scope |
|-------|------|--------|-----------|------------|
| 10.0 | Architecture & Product Design | **COMPLETE** | — | Documentation only |
| 10.1 | Goal Domain Foundation | IMPLEMENTED / VALIDATED | 10.0 | DB migration, Goal model enrichment, CRUD, basic UI |
| 10.2 | Financial Health Intelligence | **COMPLETED / MERGED — 10.2.10-C VALIDATED** | 10.1 | Expense analytics, savings rate, spending trends |
| 10.3 | Planning & Projection | **VALIDATED / CLOSED.** 10.3.7-A remains deferred; 10.3.8 automated validation passed with Swagger smoke deferred; 10.3.10A contract locked; 10.3.10B complete; 10.3.11–10.3.12 validated. | 10.1, 10.2 | Generic deterministic projections, target solvers, Goals integration, explicit scenarios |
| 10.4 | Retirement & Financial Independence (FIRE) | **VALIDATED / CLOSED** — A/B/C complete; D1–D5 implemented/validated; D6 validated/stabilized; D7 validated/closed | 10.3 | Deterministic real-basis FIRE semantics over reusable 10.3 engines |
| 10.R0 | Wealth OS Product Realignment Audit | **AUDIT COMPLETE** | 10.4, 10.5-A | Cross-product evidence, target IA, ownership and dependency order |
| 10.R1–R7 | Wealth OS Realignment | R2 and R5 CLOSED; R3 foundation independently approved; R4-A/B/C CLOSED, operational R4 gated; R6.1–R6.4 COMMITTED/PUSHED; R6.5-A CONTRACT APPROVED, B IMPLEMENTED/TESTED/CHECKPOINT PENDING; R7 NOT STARTED | 10.R0 | Actual execution order is owned by the single delivery queue above |
| 10.5 | Portfolio Intelligence | **10.5-A COMPLETE; 10.5-B PAUSED / PENDING WEALTH OS REALIGNMENT** | existing Investments, 10.4, 10.R7 before resumption | Certified composition and concentration facts; exact MVP pending contract lock |
| 10.6 | Rebalancing & Watchlist | NOT_STARTED | 10.5 | Target allocation, watchlist |
| 10.7 | External Market Intelligence | NOT_STARTED | 10.5, BCB/News research | BCB, news, fundamentals |
| 10.8 | LLM Provider Foundation | NOT_STARTED | 10.7 | LLMProvider abstraction, Ollama + Gemini |
| 10.9 | Wealth AI Briefing | NOT_STARTED | 10.8, 10.4, 10.5 | Context builder, structured insights, briefing UI |
| 10.10 | Advanced Orchestration | NOT_STARTED | 10.9 — **CONDITIONAL** | Only if single-LLM approach proves insufficient |
| 10.11 | Docker & Operations | NOT_STARTED | All backend phases | Containerization, compose, ops guide |
| 10.12 | Global UX / Visual Polish | NOT_STARTED | All UI phases | Design system, typography, final visual pass |

The legacy 10.6–10.12 sequence remains historical planning input. R1 reconciled
its duplicated external-data, AI, and UX responsibilities into R2–R7; the
legacy sequence no longer authorizes implementation independently.

### R5 execution checkpoint

| Increment | Proven state | Evidence |
|---|---|---|
| R5-0 — routes and baseline | `VALIDATED` | five canonical Wealth Intelligence routes, tested `/goals` redirect, active hierarchy, month propagation, direct/deep-link normalization |
| R5-1 — tokens and themes | `IMPLEMENTED / AUTOMATED VALIDATED` | System/Light/Dark provider and bootstrap; appearance-only `fin_theme` persistence; semantic shell, status, financial, chart, focus, and surface tokens |
| R5-2 — Planning ADR-024 | `VALIDATED` | exactly `Simular`, `Objetivo`, and `Comparar`; nested `Quando alcanço?`, `Quanto aportar?`, and `Meta cadastrada`; five existing deterministic capabilities preserved |
| R5-3 — stabilization | `IMPLEMENTED / AUTOMATED VALIDATED / USER VISUAL ACCEPTANCE APPROVED FOR CURRENT BASELINE` | semantic Wealth surfaces, responsive controls, reduced motion, keyboard/focus-safe Goals dialogs, pt-BR regressions, accessible states and chart alternatives |

Validation on 2026-10-24: frontend Vitest `218 passed`; focused backend
Wealth Home/Goals/Planning/FIRE contracts `219 passed`; TypeScript and focused
ESLint passed; the 38-route Next.js production build passed. The build retains
the documented Recharts SSR dimension warning in the legacy
`/wealth/asset/[ticker]` route. Final visual acceptance across desktop, tablet,
and mobile is intentionally assigned to the user's local-browser review. No
backend implementation, engine, DTO, migration, database, R6, Portfolio
Intelligence, Advisor, provider, deployment, commit, or push was introduced.
The technical checkpoint was subsequently committed and pushed at
`1fae590fb316b4f9d9584aad23cdde4fe8f3af9b`. The project owner supplied the
separate current-baseline visual acceptance on 2026-10-27; it does not claim an
exhaustive manual matrix. The earlier R6.1 sequencing exception does not
retroactively classify any R6 implementation as part of R5.

---

## Historical execution records (non-authorizing)

The remainder of this file preserves completed phase contracts and former
10.6–10.12 proposals as historical evidence. Old `next` or `not started` labels
are point-in-time records and do not override the Active queue above.

### W2–W4.2 local product increments

The current worktree implements and tests a composed `/wealth-intelligence`
experience: the authenticated `wealth-home-v2` read model; monthly Health and
ADR-023 investment-wealth facts; current owned Goals; canonical nested routes;
month propagation to Health; five deterministic Planning flows; three explicit
FIRE modes; and one validated result selected into memory for the Home. The
state is not persisted and is cleared on refresh, logout, token change, or
identity change. No Portfolio Intelligence, operational Advisor, scenario
persistence, migration, or new financial engine is introduced.

This record reconciles repository reality without designating R5 or R6 as
started or closed. The traceability matrix and exact validation evidence are in
`audits/W2_W4_2_RECONCILIATION_2026-10-24.md`.

### Post-10.3 Planning UX implementation

This sequence is contract-preserving refinement, not a reopening of Phase 10.3
and not the start of FIRE. ADR-024 and `PLANNING_UX_CONTRACT.md` are authoritative.

| Microtask | Scope | Status |
|---|---|---|
| UX-B1 | pt-BR exact financial input/output adapters, field errors, executable parser/formatter tests | VALIDATED |
| UX-B2 | Minimal Planning/Health page chrome, copy reduction, three intentions | VALIDATED |
| UX-B3 | Submit-time context defaults, visible nominal standard state, Advanced options | VALIDATED |
| UX-B4 | Scenario Comparison shared context with per-scenario differentiators | VALIDATED |
| UX-B5 | Answer-first result hierarchy, chart formatting, compact provenance | VALIDATED |
| UX-B5-R1 | Quiet Financial OS static visual reconciliation | VALIDATED |
| UX-B6 | Skeletons, restrained microinteractions, responsive/accessibility stabilization | VALIDATED |
| UX-B7 | Independent validation and stabilization | VALIDATED / CLOSED |

Optional portfolio preview, assumption references, and Goal-derived presets are
separate backend mini-contracts and do not block UX-B1–UX-B7.

---

## Preserved phase records and historical scopes

The records below retain accepted core contracts and historical proposals.
They are **not another execution queue**. For 10.6 onward, scope lists and
dependency/package suggestions are historical inputs requiring a current
contract before implementation. In particular, the old 10.8 provider list,
automatic Ollama-to-Gemini fallback, and raw `ai_runs` reuse proposals are superseded
by ADR-030 and `AI_AND_LLM.md`; 10.9 does not authorize scheduling/persistence.
Nothing here supersedes a locked financial contract or the R7 → 10.5-B gate.

---

### PHASE 10.1 — Goal Domain Foundation

**Entry Criteria:**
- 10.0 documentation reviewed and approved
- `position_snapshots` schema conflict investigated and resolved
- `requirements.txt` updated with missing dependencies (P2 fix)

**Scope:**
- Add DB migration (018_goals_enriched.sql): current_amount, priority, monthly_contribution, linked_account_id, assumptions_json to goals table
- Add new GoalType values: WEALTH_TARGET, INVESTMENT_TARGET, DIVIDEND_INCOME, FINANCIAL_INDEPENDENCE
- Update GoalModel ORM to include new fields
- Update GoalCreateDTO, GoalResponseDTO
- Update GoalRepository: update_goal, get_goal_by_id
- Add PUT /api/v1/goals/{id} endpoint
- Add DELETE /api/v1/goals/{id} endpoint
- Replace /goals frontend stub with functional Goal cards + create/edit modal
- Add goal progress display (current_amount / target_amount)

**Out of Scope:**
- Goal projections (Phase 10.3)
- Retirement engine (Phase 10.4)
- AI integration
- Existing investments/wealth pages

**Files expected to change:**
- `database/migrations/017_goals_enriched.sql` [NEW]
- `backend/infrastructure/persistence/models/goal.py` [MODIFY]
- `backend/domain/enums/goal_type.py` [MODIFY]
- `backend/application/dtos/goal_dto.py` [MODIFY]
- `backend/infrastructure/persistence/repositories/goal_repository.py` [MODIFY]
- `backend/application/use_cases/goal/` [MODIFY + ADD]
- `backend/api/routers/goals.py` [MODIFY]
- `backend/core/container.py` [MODIFY — add new use case factories]
- `frontend/src/app/goals/page.tsx` → moved to `/wealth-intelligence/goals/page.tsx`
- New navigation item in `frontend/src/config/navigation.ts`

**Tests:**
- Unit: GoalModel fields, GoalType enum
- Unit: goal_repository CRUD
- Integration: POST, GET, PUT, DELETE /api/v1/goals
- Integration: user isolation (goal of user A not visible to user B)

**Acceptance Criteria:**
- User can create a goal with all new fields
- User can view goal list with progress displayed
- User can edit and delete goals
- User isolation enforced
- All new tests pass

---

### PHASE 10.2 — Financial Health Intelligence (Micro-Process Execution Plan)

**Entry Criteria:** 10.1 COMPLETE and validated
**Execution Strategy (ADR-016):**
- **Mode A (Sonnet):** May execute a coherent group of micro-processes sequentially if validation gates pass.
- **Mode B (Gemini):** Must execute **one micro-process at a time**. Stop, report (IMPLEMENTED, TESTS, REGRESSIONS, FILES CHANGED, LIMITATIONS, VALIDATION REQUIRED, NEXT), and await explicit user approval.
- **No Guessing Rule:** If existing data does not support a metric exactly, stop and report. DO NOT invent fields or logic.

#### Quality Gates
- **GATE A:** Repository / Architecture conformity (Source of Truth strictness).
- **GATE B:** Automated tests pass.
- **GATE C:** Regression verification (Pierre, Investments, Goals unharmed).
- **GATE D:** Manual validation (Frontend only).
- **GATE E:** Documentation / Handoff updated.

---

#### 10.2.0 — Contract and Data Audit
- **Status:** COMPLETED.
- **Objective:** Finalize the Financial Health data contract and validate provisional hypotheses. No code changes.
- **Scope:** Validate Pierre models, Governance (PENDING/CLASSIFIED/ENTRADA/SAIDA/IGNORAR), Dates, account boundaries, and query patterns.
- **Resolution status:** The operational baseline is three continuous closed months. The Spending Anomaly Engine contract is locked in ADR-015; API route naming remains reserved for 10.2.6.
- **Completed conclusions:** only `CLASSIFIED` transactions are eligible; `PENDING` and `IGNORAR` are excluded; `ENTRADA` and `SAIDA` aggregate using `abs(amount)` and `transactions.date`; scope is consolidated across all eligible accounts in the local tenant. The operational baseline is the three continuous closed months preceding the analysed month. The local SQLite architecture remains single-tenant and `transactions` has no `user_id`.

#### 10.2.1 — Financial Health Read Query Foundation
- **Status:** IMPLEMENTED / VALIDATED.
- **Objective:** Extend `GovernedFinancialQuery` (or create `HealthFinancialQuery`) to retrieve required certified data.
- **Data Dependencies:** `transactions` (`governance_status == 'CLASSIFIED'`).
- **Implementation:** Query aggregates total income/expense, historical baseline (period locked in 10.2.0), and handles `IGNORAR`/`PENDING` omissions. No persistence.
- **Automated Tests:** consolidated account scope, classified-only, ignored omissions, date boundaries.
- **Validated implementation:** `HealthFinancialQuery` provides `get_cashflow`, `get_monthly_totals`, and `get_category_expenses` using `[start_date, end_date)` boundaries. Automated tests cover classified-only, PENDING/IGNORAR exclusion, absolute values, date boundaries, category aggregation, and consolidated multi-account scope. SQL validation reproduced the September/2026 cashflow totals.

#### 10.2.2 — Cashflow Metrics Engine
- **Status:** IMPLEMENTED / VALIDATED.
- **Objective:** Calculate deterministic Net Cashflow, Savings Amount, and Savings Rate.
- **Implementation:** `CashflowMetricsService` receives certified cashflow and monthly totals from the read layer and returns `CashflowSummaryDTO`; it does not query transactions or the database.
- **Metric Contract:** `net_cashflow = total_income - total_expense`; `savings_amount = net_cashflow`; `savings_rate = savings_amount / total_income`, or `None` when total income is zero. Monthly averages are calculated only from the supplied collection; an empty collection returns `None` averages.
- **Precision:** `HealthFinancialQuery` normalizes SQLite `SUM(ABS(amount))` aggregates to `Decimal` at the certified `NUMERIC(12,2)` transaction scale before supplying the Engine. Monetary values then remain exact `Decimal`; rates are fractional analytical `Decimal` values (for example, `0.4` = 40%) without cent quantization.
- **Trend:** The contract was absent when 10.2.2 was implemented. ADR-018 later locked deterministic month-over-month semantics, now implemented by `FinancialTrendService` in 10.2.10-B.
- **Automated Tests:** Positive, deficit, zero-income, zero-value, equal-value, single/multiple-month, empty-month collection, and Decimal precision scenarios.

#### 10.2.3 — Historical Financial Metrics
**Status:** VALIDATED.
- **Objective:** Provide a deterministic, typed series of certified monthly Financial Health metrics.
- **Implementation:** `HistoricalFinancialMetricsService` receives certified monthly totals, applies `CashflowMetricsService` to each supplied month, and returns chronological `MonthlyFinancialMetricsDTO` records. The series neither queries SQLite nor fills absent months.
- **Contract:** `reference_month` uses `YYYY-MM`; explicit zero-value months remain records; empty input returns an empty series; duplicate reference months raise `ValueError` rather than being silently aggregated. The caller remains responsible for selecting closed-month baselines and may include a current partial month when explicitly supplied.
- **Acceptance extension:** ADR-018 defines consecutive closed-month comparisons, directions, deltas, and insufficient-data behavior, implemented in 10.2.10-B. Rolling averages remain outside the locked acceptance contract.
- **Automated Tests:** chronological ordering, monthly metrics, deficit and zero-income behavior, empty history, gap preservation, explicit zero month, Decimal precision, and duplicate-month rejection.

#### 10.2.4 — Category Expense Intelligence
**Status:** VALIDATED.
- **Objective:** Provide deterministic expense-distribution metrics from certified category totals.
- **Implementation:** `CategoryExpenseIntelligenceService` receives pre-consolidated `CategoryExpenseTotalDTO` values, calculates total expense and analytical shares, and returns ranked `CategoryExpenseMetricDTO` values with a deterministic top category. It does not query SQLite or alter labels.
- **Contract:** `total_expense` is the exact sum of supplied category totals. Categories are ordered by expense descending and then lexicographically by their received label; ranks are sequential. Empty input returns total `Decimal('0.00')`, no categories, and no top category. Explicit zero categories remain records with `share_of_expenses = None`. Duplicate category input raises `ValueError`.
- **Precision and labels:** expense totals remain cent-scale `Decimal`; shares remain analytical `Decimal` without presentation rounding. Governed labels, including `Uncategorized`, are preserved exactly.
- **Acceptance extension:** ADR-018 exact-label category trends are implemented in 10.2.10-B and can later support factual budget-pressure composition. Extra concentration scores, category normalization, and aliases remain outside scope; anomaly semantics remain separately locked by ADR-015.
- **Automated Tests:** ranking, shares, total consistency, top category, unordered input, stable ties, empty input, zero total, Decimal precision, uncategorized preservation, and duplicate rejection.

#### 10.2.5 — Spending Anomaly Engine
**Status:** VALIDATED.
- **Objective:** Implement the approved deterministic anomaly contract in ADR-015. No ML/LLM.
- **Locked rules:** Require three continuous closed baseline months. A category with presence in at least two baseline months uses the arithmetic mean of certified present values (explicit zero is present) as its baseline; it is eligible for `SPIKE` only when the baseline is `>= Decimal('50.00')` and current expense is strictly greater than baseline times `Decimal('1.5')`. A category absent in all three baseline months is `NEW_EXPENSE` only when current expense is `>= Decimal('100.00')`.
- **States:** `NORMAL`, `SPIKE`, `NEW_EXPENSE`, `INSUFFICIENT_HISTORY`, `BELOW_BASELINE_FLOOR`, `NEW_EXPENSE_BELOW_THRESHOLD`, and global `INSUFFICIENT_BASELINE`. Only `SPIKE` and `NEW_EXPENSE` are anomalies.
- **Implementation:** `SpendingAnomalyService` consumes only prepared `CategoryExpenseMonthDTO` values. It has no SQLite, transaction, RAW, Pierre, persistence, API, or AI access; `SpendingAnomalySummaryDTO` exposes global status, evaluations, and only `SPIKE`/`NEW_EXPENSE` signals in `anomalies`.
- **Automated Tests:** all rule boundaries, two-of-three versus one-of-three history, explicit-zero versus absence, empty current/baseline, multiple categories, exact category matching, and Decimal precision.
- **Real-data validation:** September/2026 against June-August/2026 independently reproduced every category evaluation; `Transferências` and `Serviços` were the only `SPIKE` signals.

#### 10.2.6 — Financial Health API
**Status:** VALIDATED.
- **Objective:** Expose certified Financial Health results through authenticated FastAPI endpoints without financial calculations in the router.
- **Endpoints:** `GET /api/v1/financial-health/cashflow`, `/history`, `/categories`, and `/anomalies`, each requiring `reference_month=YYYY-MM`; there are no account filters.
- **Implementation:** The read-only router orchestrates `HealthFinancialQuery` and existing deterministic services, then serializes typed Pydantic responses. `Decimal` values are JSON strings; domain `None` values serialize as JSON `null`.
- **Automated Tests:** authentication, valid/invalid reference month, Decimal serialization, historical gaps/null rate, categories/ranking, anomaly results, and insufficient baseline.
- **Historical live reconciliation:** The authenticated API, `HealthFinancialQuery`, and independent SQLite Decimal aggregation reconciled when 10.2.6 was validated. Those September/2026 values and signals were point-in-time evidence, not fixtures. The later 10.2.10-A audit supersedes the incomplete-classification assumption: the current database has no `PENDING` transactions and its current totals must always be read live.

#### 10.2.7 — Financial Health Frontend Foundation
**Status:** VALIDATED.
- **Route and integration:** `/wealth-intelligence/health` uses the existing authenticated `fetchFromAPI` helper to load the four Financial Health API endpoints with an explicit `reference_month=YYYY-MM` selector. The configured API base already contains `/api/v1`; endpoint paths do not duplicate it.
- **Foundation states:** typed Decimal-string responses, local month selection, loading placeholders, retryable error state, empty history/categories/anomalies states, and `INSUFFICIENT_BASELINE` are implemented. The browser only formats certified values and does not calculate financial metrics, shares, ranks, or anomaly rules.
- **Intentional limitation:** the page uses simple lists and summary values only. Charts, visual comparisons, refined responsive behavior, and analytical polish remain in 10.2.8.
- **Manual Validation:** Completed with the real backend and frontend. Authentication, month selection, all four API-backed sections, consolidated values, anomaly signals, UTF-8 labels, and Wealth Intelligence navigation were confirmed in the browser.

#### 10.2.8 — Financial Health Analytical UI
**Status:** VALIDATED.
- **Objective:** Present the certified Financial Health data with useful hierarchy, visual context, and responsive analytical sections.
- **Implementation:** The route now uses reusable summary, history, category, and anomaly components. Summary cards include the API-provided recent averages; the Recharts history view uses independent monthly bars so gaps are not visually bridged and retains an exact-value table; category shares are represented as proportional ranked bars; anomaly cards expose current value, baseline reference, analytical ratio, and months used, with non-anomaly evaluations available as secondary detail.
- **States and accessibility:** Layout-shaped skeletons, retryable error messaging, empty sections, and `INSUFFICIENT_BASELINE` are retained and refined. Semantic headings, table headers/caption, form labeling, focus styles, textual legends, and non-color status labels provide basic accessible interpretation.
- **Constraint:** The frontend formats and visualizes API-certified values only. It does not recalculate financial totals, averages, shares, ranks, baselines, statuses, or thresholds; no AI/LLM was introduced.
- **Technical Validation:** Targeted ESLint and `npx tsc --noEmit` pass. The production Next.js build passes; the existing repository-wide Recharts SSR dimension warning remains non-blocking.
- **UI Polish (10.2.8-A):** The chart displays the latest six returned records while the table retains the complete returned history. Anomaly metadata reflows without overlap, long labels are protected, the Health TopNav marker follows the established color-dot pattern, and the Wealth Intelligence hub card uses a consistent icon.
- **Manual Validation:** Completed successfully for September/2026, another populated month, an empty certified month, chart/table windows, anomaly-card reflow, long labels, TopNav, hub icon, and browser console. No backend change was required.

#### 10.2.9 — Integration and Stabilization
**Status:** VALIDATED.
- **Objective:** Final code quality checks.
- **Integration audit:** Governed transactions flow through the certified query boundary, Decimal normalization, deterministic metrics/history/category/anomaly services, authenticated read-only API, typed frontend client, and analytical UI without responsibility leakage. Backend response models and frontend types match field by field.
- **Freshness:** Health endpoints query the current classified ledger on every request; the frontend uses `cache: "no-store"`. New governance classifications are reflected on the next request without snapshots, rebuild, reimport, or restart.
- **Frontend stabilization:** Rapid reference-month changes now use request sequencing so an older four-request batch cannot overwrite a newer month. History remains complete in the API/table and limited to the latest six returned records only in the chart.
- **Validation:** 47 Health tests pass. The general unit suite has 118 passes and only the two historical Investments mock/timeline failures. TypeScript, targeted Health lint, production build, authenticated real-data HTTP smoke, and OpenAPI route checks pass.
- **Known non-blockers:** ADR-014 Alembic FK mismatch, global mobile responsiveness debt, repository-wide lint debt, and the existing Recharts SSR dimension warning remain outside Financial Health stabilization.

#### 10.2.10 — Acceptance Completion and Final QA
**Status:** COMPLETED.
- **10.2.10-A — Financial Trend, Stability Readiness & Acceptance Contract Lock:** `VALIDATED`. The read-only ledger audit confirmed 1,420/1,420 transactions classified, `PENDING = 0`, and 17 continuous calendar months (`2025-05` through partial `2026-09`). ADR-018 locks global/category trend semantics, factual budget pressure, the Health/Planning boundary, and stability readiness. No code or data changed.
- **10.2.10-B — Deterministic Global & Category Trend Engine:** `VALIDATED`. Independent read-only SQLite plus Python `Decimal` reconciliation on 2026-09-15 matched all four Jul→Aug/2026 global facts and the complete 24-category union, including cross-year, insufficient-data, gap, zero, negative, invalid-input, and duplicate-input checks. `FinancialTrendService` consumes certified `MonthlyFinancialMetricsDTO` and `CategoryExpenseMonthDTO` collections without DB access. It exposes separate global/category summaries, resolves a requested current partial month to the previous closed month using an explicit caller-supplied current reference, requires the exact preceding calendar month, and returns valid empty `INSUFFICIENT_DATA` summaries rather than skipping gaps.
- **Global implementation:** income, expense, net cashflow, and savings-rate comparisons expose exact Decimal current/previous values, absolute and percentage deltas, and ADR-018 directions. Previous zero yields no percentage; an undefined savings rate yields metric-level `INSUFFICIENT_DATA` and no artificial zero.
- **Category implementation:** exact-label union with `INCREASED`, `DECREASED`, `UNCHANGED`, `NEW`, and `DISAPPEARED`; explicit zero remains presence. Target-present categories are ordered by current expense descending then label, followed by disappeared categories ordered by previous expense descending then label. This is deterministic presentation order, not a new financial ranking.
- **Validation:** 13 new tests cover the 22 required global/category/precision behaviors. The full Health suite passes (`60 passed`). Read-only production-query versus independent SQLite Decimal validation reconciled all four Jul→Aug metrics and all 24 categories in the union; Dec/2025→Jan/2026 and insufficient 2025-05 also passed. General baseline remains `118 passed, 2 failed`, exclusively the known Investments timeline mocks.
- **Stability:** `NOT IMPLEMENTED — CONTRACT PENDING`. No stability fact, variability calculation, or score was added.
- **10.2.10-C — Trend Exposure and Stability Decision:** `VALIDATED`. Authenticated `GET /api/v1/financial-health/trends?reference_month=YYYY-MM` exposes the already validated ADR-018 global and category facts using Decimal JSON strings/null. The router builds only certified history/category inputs, supplies the local current month at the API boundary, and delegates all trend arithmetic to `FinancialTrendService`. The Health UI fetches the endpoint in its existing race-protected batch. The UX polish consolidates temporal context, turns global/category trends into compact visual KPIs, and paginates the existing history array at 12 months per page with the latest records shown first. M-01 corrected the visual period direction to chronological `comparison_month → trend_target_month`. No API/UI layer recalculates financial facts.
- **Final manual QA:** completed. Functional browser validation and the independent release review found no blockers or HIGH findings; the verdict was `PASS WITH NON-BLOCKING NOTES` with LOW release risk.
- **Gate:** satisfied. Phase 10.2 is `COMPLETED` after explicit user sign-off and M-01 validation.

**Phase boundary:** Financial Health owns observed facts, realized surplus/deficit, comparisons, trends, distribution, and anomalies. Sustainable contribution capacity is deferred to Planning; investment capacity is deferred to Planning/Portfolio Intelligence; composite financial stability remains deferred until a deterministic contract is approved. These are planned boundaries, not Phase 10.2 failures. The root product specification is high-level vision, while ADR-018 is the executable trend contract.

---

### PHASE 10.3 — Planning & Projection

**Status:** `VALIDATED / CLOSED`. `10.3.0–10.3.6 = VALIDATED`; `10.3.7-A = DEFERRED — INSUFFICIENT CONTRACT / DATA`; `10.3.8-A = API CONTRACT LOCKED / PERSISTENCE DEFERRED`; `10.3.8-B–E = VALIDATED`; `10.3.8-F = AUTOMATED VALIDATION PASSED`; Swagger manual smoke is `DEFERRED BY USER`; `10.3.9–10.3.10 = VALIDATED`; `10.3.10A = CONTRACT LOCKED`; `10.3.10B1–B4 = VALIDATED`; `10.3.10B = VALIDATED / COMPLETE`; `10.3.11 = VALIDATED / STABILIZED`; `10.3.12 = VALIDATED / CLOSED`. ADR-024 governs the post-closure Planning UX refinement: `UX-B1–UX-B7 = VALIDATED`; POST-10.3 UX is `VALIDATED / CLOSED`. Planning now remains the reusable projection/solver authority under the locked Phase 10.4 FIRE contract.

**Entry Criteria:** 10.1 and 10.2 are complete, validated, merged, and available as certified inputs. Satisfied by PR #2 merge commit `b7ce8b8`.

**Responsibility:** Planning combines certified current facts, user-governed Goals, and explicit user assumptions to produce generic deterministic forward projections, future wealth, target dates, required contributions, scenario comparisons, inflation-aware nominal/real results, Goal timing facts, and other conditional Planning results. Projections are conditional outputs, never guaranteed returns.

**Out of Scope:** FIRE/retirement-specific target wealth, withdrawal rates, retirement income sustainability, asset selection, portfolio rebalancing, trades, market forecasts, recommendation engines, and LLM calculation. Phase 10.4 owns FIRE/retirement semantics; Phase 10.5 owns portfolio intelligence. A future LLM may explain certified Planning results but never calculate them.

#### Verified Reuse Baseline

| Existing Component | Reuse in Planning | Read-only? | Notes |
|---|---|---:|---|
| Goals model/repository/API | Target amount/date, current amount, planned contribution, type, status, priority | Yes | Persisted `Numeric` values are currently converted to `float` by Goal entity/repository/DTOs. Planning must establish a Decimal-safe boundary and must not execute opaque `assumptions_json` without a new contract. |
| `HealthFinancialQuery` | Certified classified monthly income/expense facts | Yes | Reuse through an application/read boundary, not router SQL duplication. |
| `HistoricalFinancialMetricsService` | Realized net cashflow and savings facts over supplied months | Yes | Historical realized surplus is context; it is not sustainable contribution capacity. |
| `FinancialTrendService` | Closed-month factual direction/context | Yes | Useful as context only; trends are not return or contribution forecasts. |
| Health categories/anomalies | Optional factual spending context | Yes | Not a default projection input and never a source of automatic advice. |
| `PortfolioSnapshotModel` | Candidate current investment wealth and monthly investment history | Yes | `patrimonio` is MyProfit investment-portfolio wealth, not proven consolidated net worth. Current Investments endpoints return dynamic dictionaries and convert values to `float`; Planning needs a typed Decimal read boundary if this source is approved. |
| `PositionSnapshotModel` + asset valuations | Reconciliation or scoped investment facts | Yes | Do not sum positions inside Planning when an approved portfolio total exists. Current value freshness and account scope must be contracted. |
| `IncomeEventModel` | Historical dividend context | Yes | Not guaranteed future income. Future-dated rows require explicit semantics before use. |
| Portfolio snapshot benchmarks | Historical CDI/IPCA/IBOV context | Yes | Historical external facts must not become future return/inflation assumptions automatically. |
| `MarketDataService` / yfinance | Current external quote context | Yes | External and cached; not a projection-rate authority. |
| Existing Goals/Health/Investments APIs | Contract reference for frontend integration | Yes | Backend Planning orchestration must reuse repositories/services, not call its own HTTP endpoints. |

#### Planning Data Lineage

```text
Certified investment wealth + certified Health facts + user-governed Goals
                              + explicit user assumptions
                                      ↓
                         Planning input/read boundary
                   (source, as-of date, scope, Decimal)
                                      ↓
                    Deterministic Planning engines
                                      ↓
                 Typed Planning results and provenance
                                      ↓
                           Authenticated API
                                      ↓
                         Read-only frontend UI
                                      ↓
                 Future LLM interpretation only
```

#### Locked Contract Summary

ADRs 019–023 are the detailed source of truth. The approved implementation constraints are:

1. **Typed inputs:** initial wealth declares exactly one origin (`GOAL_CURRENT_AMOUNT`, `INVESTMENT_PORTFOLIO_SNAPSHOT`, or `USER_PROVIDED_SCENARIO`) with scope/as-of/provenance; sources are never summed automatically. MyProfit `patrimonio` is investment wealth, not consolidated net worth.
2. **Decimal boundary:** 10.3.1 must bypass the existing Goal float path through read-only Decimal adapters. No projection math belongs in 10.3.1.
3. **Monthly math:** period zero is `as_of_date`; the next complete calendar month is period one; contributions use `END_OF_MONTH` timing.
4. **Rates:** explicit finite effective annual Decimal rates accept every value `> -1`, with no arbitrary positive cap. Monthly conversion is compound-equivalent, never annual/12.
5. **Nominal/real:** the approved matrix applies inflation exactly once when converting nominal return to real output. `REAL` return to `NOMINAL` output is unsupported initially. Goal integration must declare `target_value_basis`.
6. **Horizon and precision:** exactly one horizon selector; 1–1,200 full months; month-level target dates; 34-digit context; monthly rate with at least 18 decimal places; cent-scale `ROUND_HALF_EVEN` monetary recurrence.
7. **Solvers:** both reuse the Forward Projection Engine. Required contribution uses monotonic cent-based binary search and returns the smallest satisfying cent value.
8. **Scenarios:** archetypes are editable labels without hardcoded rates; historical data is never an automatic forecast; scenarios are transient first.
9. **Boundaries:** sustainable contribution capacity remains deferred in 10.3.7; Retirement/FIRE is Phase 10.4; Portfolio Intelligence is Phase 10.5.

#### Microprocess Roadmap

| ID | Name | Objective | Depends On | Produces Code? |
|---|---|---|---|---:|
| 10.3.0 | Planning Contract & Data Audit | **VALIDATED.** Domain/data audit completed and contracts locked by ADRs 019–022. No engine. | 10.1, 10.2 | No |
| 10.3.1 | Planning Read Foundation | **VALIDATED.** Immutable typed facts; Decimal-safe owned Goal reads; explicit-account latest portfolio snapshot reads; certified Health query/service reuse; typed source/scope/as-of/provenance; no automatic source selection or aggregation. No projection math. | 10.3.0 | Yes |
| 10.3.2 | Projection Assumptions Boundary | **VALIDATED.** Immutable typed assumptions enforce Decimal-only contribution/rates, the nominal/real matrix, explicit constants, and one calendar-month horizon source. Independent validation confirmed strict boundaries without rate conversion, Fisher calculation, or projection math. | 10.3.0, 10.3.1 | Yes |
| 10.3.3 | Deterministic Forward Projection Engine | **VALIDATED.** Pure immutable Decimal engine with magnitude-derived adaptive local precision, effective annual → monthly equivalent conversion, one-time Fisher when applicable, `END_OF_MONTH` contributions, cent-scale monthly `ROUND_HALF_EVEN`, month-end timeline, provenance, and exact cumulative totals. Independent V2 revalidation matched an 800-digit oracle across extreme and cross-mode cases and proved both sides of the former precision bug are regression-protected. No solver or Goal coupling. | 10.3.2 | Yes |
| 10.3.4 | Target & Required Contribution Solvers | **VALIDATED.** `10.3.4-A = VALIDATED`: strict target input, period-zero semantics, first crossing, conservative `UNREACHABLE`, output-basis neutrality, provenance, immutability, and Decimal magnitude. `10.3.4-B = VALIDATED`: independent cent-grid and 500-digit oracles proved template-contribution independence, monotonicity including negative `ROUND_HALF_EVEN` ties and near-`-1`, the constructive target upper bound, logarithmic integer-cent search, and exact `C`/`C - 0.01` minimality without sustainability semantics. | 10.3.3 | Yes |
| 10.3.5 | Goal Planning Integration | **VALIDATED** (TSK-10.3.5-V3). Final independent validation confirmed ACTIVE-only positive eligibility, applicability before target basis/output, Goal-current-amount provenance, and deadline validation, zero solver calls for non-projectable Goals, strict ACTIVE validation, and separation between lifecycle `ACHIEVED` and mathematical `ALREADY_ACHIEVED`. 63 tests. | 10.3.1, 10.3.3, 10.3.4 | Yes |
| 10.3.6-A | Scenario Comparison Contract & Architecture Lock | **CONTRACT LOCKED.** Explicit unique scenario/reference IDs; BASE is not automatic reference; minimum two ordered scenarios; shared as-of/resolved horizon/output mode/timing; optional shared target; certified engine reuse; exact delta/month semantics; atomic prevalidation; transient, non-advisory output. | 10.3.3, 10.3.4, 10.3.5 | No |
| 10.3.6-B | Scenario Comparison Engine Implementation | **VALIDATED.** Independent contract/code/oracle validation confirmed immutable pure-domain comparison over `ForwardProjectionEngine` and `TargetAchievementSolver`, explicit references, atomic comparability validation, optional shared target, exact Decimal deltas, certified-result preservation, and no second financial math, persistence, Goal auto-integration, Required Contribution automation, ranking, or advice. Focused suite: `37 passed`; all Planning/Goals/Health regressions passed; general unit: `403 passed, 2 historical Investments/MagicMock failures`. | 10.3.6-A | Yes |
| 10.3.7-A | Sustainable Contribution Capacity Contract Decision | **DEFERRED — INSUFFICIENT CONTRACT / DATA.** Certified Health provides realized history, not recurring forward affordability. No approved window, minimum history, partial-month, deficit, anomaly/outlier, statistic, negative-result, currency, or missing/zero policy supports the word `sustainable`. No formula or implementation was created. | 10.3.0, validated Health facts | No; implementation remains gated |
| 10.3.8-A | Planning API & Scenario Persistence Contract Audit | **API CONTRACT LOCKED / PERSISTENCE DEFERRED — TRANSIENT API FIRST.** Five authenticated capability endpoints are locked under `/api/v1/planning`; request facts cannot impersonate certified sources; Goal ownership is enforced server-side; portfolio API sourcing is deferred because snapshot accounts lack user ownership; JSON money/rates are strings; persistence lacks lifecycle/versioning/provenance/staleness contracts. | 10.3.3–10.3.6; 10.3.7-A decision | No |
| 10.3.8-B | Planning API Foundation | **VALIDATED.** Independent review confirmed the empty registered `/planning` router, existing-JWT and synchronous-reader dependency annotations, real-JSON strict Decimal strings, secure selectors, pure builders/mappers, local error translation, and OpenAPI/startup safety. No financial endpoint, engine call, persistence, or portfolio source was added. | 10.3.8-A | Yes |
| 10.3.8-C | Generic Planning Calculation Endpoints | **VALIDATED.** Independent HTTP validation confirmed exactly three authenticated transient routes, strict Decimal-string request/response fidelity, server-owned Goal-current-amount resolution and 404 non-enumeration, exact engine delegation, domain-status preservation, local errors, OpenAPI scope, and no financial recomputation, write, persistence, or out-of-scope endpoint. Focused suite: `25 passed`; general unit: `465 passed, 2 historical Investments/MagicMock failures`. | 10.3.8-B | Yes |
| 10.3.8-D | Goal Planning Endpoint | **VALIDATED.** Final independent validation proved the pure preflight and evaluate path share one lifecycle/type authority across all real status/type pairs. Non-projectable Goals do not consume selected Goal current amount; ACTIVE eligible Goals still return `422` when that fact is required and absent. No dummy wealth, DB access in domain, or router eligibility duplication. Focused suite: `39 passed`; Goal Planning domain: `101`; general unit: `546 passed, 2 historical Investments/MagicMock failures`. | 10.3.8-B, 10.3.8-C | Yes |
| 10.3.8-E | Scenario Comparison Endpoint | **VALIDATED.** Independent HTTP/domain/OpenAPI validation confirmed explicit scenario/reference IDs, input-order preservation, metadata-only archetypes, server-owned Goal resolution, atomic source failure, resolved-horizon equivalence, ReturnType variation, target-pair strictness, one Comparison engine call, certified delta mapping, and no ranking/recommendation/persistence/portfolio source. Focused HTTP suite: `42 passed`; Planning domain regressions: `323 passed`; Goals `65`; Health `68`; general `585 passed, 2 historical Investments/MagicMock failures`. | 10.3.8-B, 10.3.8-C | Yes |
| 10.3.8-F | API Integration & Independent Validation | **AUTOMATED VALIDATION PASSED.** Cross-endpoint validation confirms exact authenticated OpenAPI route set, strict Decimal/source consistency, Goal ownership, read-only dependency boundaries, D/E regressions, deterministic 1,200-month serialization, and no persistence/advice/math duplication. Swagger Authorize manual smoke is deferred by user. | 10.3.8-C–10.3.8-E | Validation/fixes only |
| 10.3.9 | Planning Frontend Foundation | **VALIDATED.** Manual smoke passed for Nominal→Nominal, Real→Real, Nominal→Real, and unavailable Real→Nominal. | 10.3.8 | Yes |
| 10.3.10 | Planning Analytical UI | **VALIDATED.** Five certified capabilities share string-only assumptions/source inputs; certified results and chart-only period visualizations are displayed without browser financial calculation or persistence. Technical and manual validation passed; broader visual/UX refinements were deferred by the user. | 10.3.9 | Yes |
| 10.3.10A | Investment Portfolio Source Contract & Ownership Audit | **CONTRACT LOCKED.** ADR-023 formalizes guarded single-tenant ownership, one canonical MyProfit scope, source-only request shape, no-look-ahead as-of selection, Decimal/BRL/provenance boundaries, all-five-endpoint coverage, and no migration for this constrained mode. | 10.3.10 | No |
| 10.3.10B1 | Investment Portfolio Source Resolver & Reader Foundation | **VALIDATED.** Internal read-only ADR-023 resolver validates the exact one-user tenant invariant, semantic UUID ownership, complete MyProfit scope/run provenance, deterministic zero/one/many outcomes, strict `YYYY-MM` buckets, and latest-eligible-as-of Decimal fact construction without a fabricated `observed_at`. No public selector, router, frontend, engine, migration, or persistence was added. | 10.3.10A | Yes |
| 10.3.10B2 | Planning API Portfolio Source Integration | **VALIDATED.** The strict source-only public selector is wired through Projection, Target Achievement, Required Contribution, Goal Planning after domain preflight, and Scenario Comparison before its atomic engine call. B1 remains the only portfolio resolver; source errors are safe `422`; no frontend, migration, schema, engine, or write path was added. | 10.3.10B1 | Yes |
| 10.3.10B3 | Planning Frontend Portfolio Source Integration | **VALIDATED.** The shared Planning UI sends source-only portfolio requests and renders certified amount/month/provenance without preview, account selection, client-certified facts, or UI financial math. User smoke passed for all five capabilities. | 10.3.10B2 | Yes |
| 10.3.10B4 | Planning Portfolio Source Independent Validation | **VALIDATED.** Adversarial end-to-end validation confirmed ownership, temporal, Decimal, trust, read-only, API, frontend, and documentation gates. Macro `10.3.10B = VALIDATED / COMPLETE`. | 10.3.10B3 | No |
| 10.3.11 | Integration & Stabilization | **VALIDATED / STABILIZED.** Five APIs/capabilities, all approved sources, Decimal, provenance, auth, source switching, status/error/loading states, static boundaries, and regressions reconciled without a new Planning contract or production fix. | 10.3.5–10.3.10B | Yes, fixes only |
| 10.3.12 | Manual Validation & Phase Closure | **VALIDATED / CLOSED.** Consolidated accepted manual evidence with proportional final backend/frontend/OpenAPI/static checks; no production fix, feature, or contract change required. Do not start 10.4 automatically. | 10.3.11 | Documentation/validation only |

#### 10.3.10B Locked Implementation Order

A. **Schema/migration:** no migration in the ADR-023 single-tenant mode; verify the locked invariant at runtime rather than introducing a partial ownership schema.
B. **Reader/resolver:** add an ownership-aware application resolver plus an as-of-aware, read-only Decimal portfolio reader.
C. **Domain/API selector:** expose only the portfolio source discriminant; reuse the existing source, scope, fact, and public provenance contracts.
D. **Endpoint integration:** wire the selector into Projection, Target Achievement, Required Contribution, Goal Planning after applicability preflight, and atomically into Scenario Comparison.
E. **Tests:** execute the ADR-023 ownership, cardinality, temporal, Decimal, provenance, endpoint, atomicity, and existing-source regression matrix.
F. **Frontend source selector:** add the explicit portfolio option to existing Planning contracts and controls without accepting or calculating an amount in the browser.
G. **Focused UI integration:** display only the returned certified amount and provenance dates; do not add a preview endpoint or broader UX redesign.
H. **Independent validation:** adversarially validate the complete boundary before advancing to 10.3.11.

#### Acceptance Question Ownership

| User Question | Owner | Required Engine | Microtask |
|---|---|---|---|
| Quanto terei em 5, 10 e 20 anos? | Planning | Forward projection | 10.3.3 |
| Quando atinjo R$ 1 milhão? | Planning | Target-date solver | 10.3.4 |
| Quanto preciso investir por mês para atingir minha meta? | Planning | Required-contribution solver | 10.3.4 generic capability; explicit invocation only, not a 10.3.5 timing side effect |
| Se aumentar meu aporte em R$ 500, o que muda? | Planning | Scenario comparison | 10.3.6 |
| Minha meta está no caminho certo? | Planning + Goals | Goal integration over projection/solver facts | 10.3.5 |
| Quanto posso aportar de forma sustentável? | Planning, contract-gated | Sustainable capacity engine only if approved | 10.3.7 |
| Quanto preciso para viver de renda? | Phase 10.4 FIRE | FIRE target/withdrawal-income contract | 10.4, not 10.3 |

#### Test Strategy Gate

- Known-output unit tests for zero contribution/return, positive return, supported negative return, zero initial wealth, target already achieved, impossible/invalid targets, cross-year and long horizons.
- Exact Decimal, rate-conversion, timing, quantization, solver-tolerance, deterministic-repeatability, scenario-equality, and scenario-delta tests.
- Missing/stale source facts, account scope, provenance, Goal eligibility/integration, auth/user isolation, JSON string/null serialization, and transient/persisted scenario lifecycle tests as applicable.
- Independent spreadsheet or separate Decimal oracle validation for projection and inverse-solver cases; the production engine cannot be its own oracle.
- Frontend contract/type/build/lint validation plus proof that the browser does not recalculate projections.

**Execution Gate:** Phase 10.3 is `VALIDATED / CLOSED`. 10.3.7-A remains `DEFERRED — INSUFFICIENT CONTRACT / DATA`; `10.3.8-F = AUTOMATED VALIDATION PASSED` and Swagger Authorize manual smoke remains `DEFERRED BY USER`; `10.3.10A = CONTRACT LOCKED`; macro `10.3.10B = VALIDATED / COMPLETE`; `10.3.11 = VALIDATED / STABILIZED`; `10.3.12 = VALIDATED / CLOSED`. Persistence remains prohibited until a separate owner/lifecycle/versioning/provenance/staleness contract is approved. ADR-024 governs the separate UX-B1–UX-B7 implementation sequence.

---

### PHASE 10.4 — Retirement & Financial Independence (FIRE)

**Entry Criteria:** 10.3 COMPLETE

**Status:** `VALIDATED / CLOSED`

| Microtask | Scope | Status |
|---|---|---|
| 10.4-A | FIRE contract and source-of-truth audit | AUDIT COMPLETE |
| 10.4-B | FIRE contract lock and ADR-025 | CONTRACT LOCKED |
| 10.4-C | Implementation decomposition | IMPLEMENTATION PLAN COMPLETE |
| 10.4-D1 | FIRE Domain Core | IMPLEMENTED / VALIDATED — pure Decimal summary core; 27 focused tests passed |
| 10.4-D2 | FIRE Application Orchestration | IMPLEMENTED / VALIDATED — one wealth resolution, canonical target handoff, REAL Planning composition, provenance continuity |
| 10.4-D3 | FIRE API | IMPLEMENTED / VALIDATED — authenticated discriminated endpoint, strict Decimal strings, safe mapping/OpenAPI |
| 10.4-D4 | FIRE Frontend Foundation | IMPLEMENTED / VALIDATED — typed client, strict builders, pt-BR form inputs, mode disclosure, minimal entry points |
| 10.4-D5 | FIRE Results & UX | IMPLEMENTED / VALIDATED — target-first presentation, provenance, living result states, accessibility, and string-safe rendering |
| 10.4-D6 | Integration & Stabilization | VALIDATED / STABILIZED — consolidated backend/frontend, OpenAPI, authority, read-only, and regression evidence |
| 10.4-D7 | Independent Validation & Closure | VALIDATED / CLOSED — fresh-context contract, implementation, oracle, regression, OpenAPI, frontend, and boundary review passed |

**Authority:** ADR-025 and `FIRE_CONTRACT.md`.

**Locked MVP boundary:** FIRE is a thin deterministic orchestration layer over Planning. It constructs a real FIRE target from explicit monthly retirement spending and an explicit assumed annual withdrawal rate, reports summary progress and conditional withdrawal capacity, and delegates projected date and required contribution to the existing Planning solvers. It accepts exactly one of the certified portfolio selector or a user-provided Planning wealth scenario. Investment wealth is not net worth.

The one future authenticated endpoint has three contracted modes: `SUMMARY`, `PROJECTED_DATE`, and `REQUIRED_CONTRIBUTION`. Output is real; return input may be real, or nominal with explicit inflation and one Planning-owned Fisher conversion. Health inference, dividends, external income, Goal linkage, persistence, taxes, longevity, Monte Carlo, FIRE variants, scenario comparison, and portfolio advice are outside the MVP.

`FIRE_IMPLEMENTATION_PLAN.md` remains the decomposition authority for D1–D7. `10.4-D1` through `10.4-D5` are implemented and validated; D6 is validated/stabilized; D7 independently validated and closed the phase without reopening locked semantics. Phase 10.5-A subsequently completed its audit; 10.5-B is paused by the Wealth OS realignment gate.

---

### PHASE 10.5 — Portfolio Intelligence

**Entry Criteria:** 10.4 COMPLETE, existing Investments stable

**Status:** `10.5-A AUDIT COMPLETE / USER DECISIONS RESOLVED; 10.5-B PAUSED / PENDING WEALTH OS REALIGNMENT`

| Microtask | Scope | Status |
|---|---|---|
| 10.5-A | Portfolio Intelligence contract and source-of-truth audit | AUDIT COMPLETE / USER DECISIONS RESOLVED |
| 10.5-B | Portfolio Intelligence contract lock | PAUSED / PENDING WEALTH OS REALIGNMENT |

**Approved boundary only (ADR-022):** Future allocation, concentration, diversification, attribution, rebalance analysis, portfolio quality, and asset-level intelligence. Planning does not select assets, recommend investments, or infer future returns from portfolio composition/history.

The 10.5-A evidence is preserved in `PORTFOLIO_INTELLIGENCE_CONTRACT_AUDIT.md`. It found a certified aggregate monthly investment-wealth fact, but no currently reconciled position-valuation authority and no locally certified portfolio-performance engine. No Portfolio Intelligence implementation is authorized before 10.5-B locks the source, temporal, precision, ownership, and MVP metric contracts. Existing `/wealth` remains unchanged by 10.5-A.

**Tests:** To be locked in 10.5-B; no attribution or performance test contract is accepted by 10.5-A.

---

### PHASE 10.6 — Rebalancing & Watchlist

**Entry Criteria:** 10.5 COMPLETE

**Scope:**
- TargetAllocation model (user defines % per asset class)
- Rebalancing engine (deviation calculation)
- Rebalancing UI (target editor + deviation table)
- Watchlist model + CRUD endpoints
- Watchlist frontend page
- Basic threshold alerts (not push notifications — display in UI only)

---

### PHASE 10.7 — External Market Intelligence

**Entry Criteria:** 10.5 COMPLETE, bcb and news research validated

**Scope:**
- BCBAdapter: CDI, SELIC, IPCA from BCB/SGS API
- NewsService: Google News RSS retrieval + sanitization
- brFinance adapter (isolated): CVM fundamentals for BR stocks
- Technical indicators service: RSI, SMA, EMA from yfinance history
- Market Radar frontend page
- News & Events frontend page
- All external data labeled with timestamps and source

**Dependency additions:** python-bcb, feedparser (or requests+lxml), pandas-ta
**Tests:** BCB integration tests (mock HTTP), news sanitization tests (injection patterns)

---

### PHASE 10.8 — LLM Provider Foundation

**Entry Criteria:** 10.7 COMPLETE, Ollama installed on host

**Scope:**
- LLMProvider Protocol + OllamaProvider + GeminiProvider + OpenAIProvider
- LLMProviderFactory (reads AI_PROVIDER env var)
- Structured output with Pydantic schema enforcement
- InsightResponse model + validation pipeline
- Prompt injection sanitization utility
- ai_insights DB table (new migration)
- Fallback chain: Ollama → Gemini (if local unavailable)
- Observability: ai_runs integration with new provider

**Environment variables added (to .env.example):**
- AI_PROVIDER, AI_MODEL, AI_OLLAMA_BASE_URL, AI_TEMPERATURE, AI_MAX_TOKENS, AI_TIMEOUT_SECONDS, AI_FALLBACK_PROVIDER

**Tests:** Unit tests for each provider (mocked HTTP), structured output validation tests, prompt injection tests

---

### PHASE 10.9 — Wealth AI Briefing

**Entry Criteria:** 10.8 COMPLETE, 10.4 COMPLETE, 10.5 COMPLETE

**Scope:**
- WealthContextBuilder: aggregates portfolio, cashflow, goals, market, news into structured context
- BriefingService: DAILY, WEEKLY, PORTFOLIO, GOAL, EXPENSE insight generation
- APScheduler jobs: daily briefing at 7AM (configurable)
- Wealth AI frontend page: briefing display, historical list, data freshness indicators
- All AI content labeled with violet accent + generated_at timestamp

**Tests:** Context builder unit tests, briefing validation tests (schema), scheduling tests, prompt injection defense tests

---

### PHASE 10.10 — Advanced Orchestration [CONDITIONAL]

**Entry Criteria:** 10.9 COMPLETE + demonstrated quality gap
**Status:** Only start this phase if single-LLM briefings are demonstrably insufficient.

If started:
- Evaluate sequential agent approach for specific insight types
- Document quality delta vs single LLM
- No external agent framework (custom orchestration only)

---

### PHASE 10.11 — Docker & Operations

**Entry Criteria:** All backend phases stable

**Scope:**
- Dockerfile for backend
- Dockerfile for frontend (Next.js production build)
- docker-compose.yml (backend + frontend + optional services)
- Environment variable documentation
- Startup guide for `docker compose up`
- CORS configuration for production
- Ollama native setup guide

---

### PHASE 10.12 — Global UX / Visual Polish

**Entry Criteria:** All functional phases complete

**Scope:**
- Google Fonts integration (Inter or Plus Jakarta Sans)
- Expanded color system
- Typography scale standardization
- Consistent card hierarchy
- Animation/transition review
- Mobile responsiveness audit
- Accessibility audit (aria labels, keyboard navigation)
- Visual consistency pass across all pages (existing + new)

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| position_snapshots schema conflict | HIGH | HIGH | Must verify and fix BEFORE 10.1 migration |
| Ollama model doesn't fit in 8GB VRAM | MEDIUM | MEDIUM | Test before committing, use quantized models |
| yfinance rate limiting at scale | MEDIUM | LOW | Persistent cache in future |
| brFinance maintenance/reliability | MEDIUM | LOW | Wrap in adapter, fallback to yfinance.info |
| BCB API changes | LOW | MEDIUM | Version API calls, document series IDs |
| Google News RSS access removed | MEDIUM | LOW | Have alternate news source |
| requirements.txt incomplete | HIGH | MEDIUM | Fix immediately (P2) |
| GoalModel missing fields | HIGH | HIGH | Phase 10.1 migration |
