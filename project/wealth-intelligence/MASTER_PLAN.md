# Master Plan — FINANALYTICS Wealth OS

**Status:** `ARCHITECTURE LOCKED / JOURNEY-ORIENTED INCREMENTAL DELIVERY`

**Updated:** 2026-10-28 — Product roadmap realignment; no implementation authorization

## Product vision

FINANALYTICS is a **personal Wealth OS**: a private system that connects
financial reality, goals, planning, portfolio, income, market context,
monitoring, tools, and AI interpretation into coherent decision journeys. It is
not defined primarily by a collection of domain pages or disconnected
calculators.

The long-term product flow is:

```text
DATA
  -> CERTIFIED FACTS
  -> CONTEXT
  -> DIAGNOSIS
  -> PLANNING
  -> PROJECTION
  -> MONITORING
  -> EXTERNAL CONTEXT
  -> INTELLIGENCE
```

This is product direction, not permission to couple layers or bypass their
contracts.

## Product promise

The product should help the user answer, with evidence:

- Where am I financially?
- What changed, and what needs attention?
- Am I progressing toward my goals and financial independence?
- What happens if I change an explicit assumption?
- How is my investment wealth composed?
- Which external events are relevant, how fresh are they, and where did they
  come from?
- What can the system explain without inventing facts or advice?

## Non-negotiable product rules

1. Deterministic services own financial facts and calculations; AI consumes
   capabilities and interprets their results.
2. Internal facts, external observations, external expectations, and scenario
   assumptions remain semantically distinct.
3. Known eligible facts should prefill or be offered with source, scope, date,
   freshness, and an explicit override model. Empty forms are a fallback.
4. Profile is the declared-user-context surface. Settings is the configuration
   surface. Neither is duplicated into a V2 route.
5. Simulation and saved tool state never silently become financial reality.
6. Credentials remain server-side and minimum-necessary personal context is
   used.
7. Existing validated engines are composed incrementally; no big-bang rewrite
   is authorized.

## Validated core to preserve

| Capability | Status | Long-term responsibility |
|---|---|---|
| Goals 10.1 | `IMPLEMENTED / VALIDATED` | Objective lifecycle, stored intent, and tracking |
| Financial Health 10.2 | `IMPLEMENTED / VALIDATED` | Certified observed cashflow, trends, distribution, and anomalies |
| Planning 10.3 | `VALIDATED / CLOSED` | Deterministic projection and solver engine plus advanced tool |
| FIRE 10.4 | `VALIDATED / CLOSED` | Specialized financial-independence experience composed over Planning |
| Portfolio Intelligence 10.5-A | `AUDIT COMPLETE / USER DECISIONS RESOLVED` | Preserved evidence for a future certified portfolio-analysis contract |

Realignment changes composition, context, navigation, defaults, interaction,
and presentation. It does not reopen certified financial mathematics unless a
future explicit reconciliation task finds and contracts a defect.

## Target product areas

The conceptual information architecture is:

- **Home** — personal financial command center;
- **Plan** — contextual entry over Goals, Planning, and FIRE;
- **Portfolio** — portfolio truth and future Portfolio Intelligence;
- **Explore** — asset discovery and comparison;
- **Income** — investment-generated income context;
- **Monitor** — health, goals drift, watchlists, alerts, and tracked criteria;
- **Market** — macro, market, news, events, source, and freshness;
- **Copilot** — global AI interpretation and tool orchestration;
- **Tools** — reusable deterministic laboratories and calculators;
- **Profile** — declared user context;
- **Settings** — security, notification, appearance, privacy, integration, AI,
  and external-source configuration;
- **Data & Governance** — imports, classification, provenance, quality, and
  audit.

`ARCHITECTURE.md` owns the responsibilities and exclusions for each area.
Exact URLs and widgets remain implementation decisions for later contracts.

## Incremental realignment

### Product outcomes reaffirmed on 2026-10-28

The project owner reaffirmed six connected journeys, not a new architecture:

- **A — Goals and integrated planning:** distribute an explicit limited monthly
  budget across owned Goals, compare user-defined alternatives, and understand
  their certified consequences. R6.1–R6.4 are reusable foundations, not yet this
  complete multi-Goal experience.
- **B — Contribution capacity:** relate observed Health and declared Smart
  Context to planning with source, period, completeness, and explicit user
  choice. Historical surplus is not certified sustainable future capacity.
- **C — Local and online AI:** test and integrate one governed R4 runtime,
  initially evaluating Qwen 3.5 4B locally and Gemini remotely with synthetic
  equivalent fixtures. Local-first, remote opt-in, and financial authority
  remain binding; laboratory success is not production approval.
- **D — Portfolio Intelligence:** after R7, resume 10.5-B using the preserved
  10.5-A decisions, without conflating investment wealth with net worth or
  automatically attributing the same investments to several Goals.
- **E — Market and alerts:** sourced market/news/event context, watchlists and
  explicit objective conditions, under their own data and lifecycle contracts.
- **F — Copilot and briefing:** explain certified results and orchestrate only
  authorized capabilities; periodic briefings require a separate lifecycle and
  scheduling gate. Neither the LLM nor the browser owns financial mathematics.

R6.5-A closes the approved contract in `GOAL_BUDGET_PREVIEW_CONTRACT.md`;
R6.5-B is ready but not implemented. No code is authorized by the contract task.
The sole executable queue, original-to-current traceability matrix, milestone
acceptance gates, and the link to R6.5's executable contract are in
`IMPLEMENTATION_ROADMAP.md`. That owner orders remaining work by actual
dependencies; the historical macro sequence below is not a claim that R4
operational integration has already closed. No new R6.x IDs are allocated here.

The official strategy is **incremental composition refactor**:

1. lock architecture and documentation ownership;
2. establish internal Smart Context;
3. normalize external context;
4. add a provider-aware AI runtime over approved tools;
5. implement navigation, design foundations, and System/Light/Dark;
6. recompose Goals, Planning, FIRE, and Wealth Home;
7. validate independently;
8. resume Portfolio Intelligence 10.5-B under the new boundaries.

Existing routes remain operational until an implementation phase explicitly
migrates them. Deep links must not be broken incidentally.

## Official phase status

| Phase | Outcome | Status |
|---|---|---|
| 10.R0 | Product and documentation audit | `AUDIT COMPLETE` |
| 10.R1 | Product architecture and documentation consolidation | `ARCHITECTURE / DOCUMENTATION LOCKED` |
| 10.R2 | Smart Financial Context | `IMPLEMENTED / VALIDATED / CLOSED` |
| 10.R3 | External Context Layer | BCB/reference foundation independently approved; R3-G separately gated; R3-H deferred |
| 10.R4 | AI Runtime Foundation | R4-A/B/C `CLOSED / PUSHED`; real adapters/router not implemented |
| 10.R5 | Design, navigation, and System/Light/Dark | `USER ACCEPTED / CLOSED` for the current baseline |
| 10.R6 | Goals, Planning, FIRE, and Wealth Home recomposition | R6.1–R6.4 `COMMITTED / PUSHED`; R6.5-A `CONTRACT APPROVED`; R6.5-B `READY / NOT STARTED`; R6.5-C planned; R6 not closed |
| 10.R7 | Independent product/architecture validation | `NOT STARTED` |
| 10.5-B | Portfolio Intelligence contract lock | `PAUSED / PENDING WEALTH OS REALIGNMENT` |

`IMPLEMENTATION_ROADMAP.md` owns the active queue and dependency gates. It must
not be duplicated here.

## Product boundaries

- Portfolio is not a replacement for operational Investments imports,
  transactions, positions, asset details, or governance.
- Market and Explore are not sources of internal portfolio truth.
- Copilot is not a calculator, autonomous record writer, or arbitrary database
  interface.
- Rankings, scores, target-price methods, recommendation portfolios, and
  prescriptive investment advice require separate future contracts.
- Historical wealth evolution is not portfolio performance.

## Canonical supporting owners

- present reality: `CURRENT_STATE.md`;
- architecture and target information architecture: `ARCHITECTURE.md`;
- data classes, provenance, and source authority:
  `DATA_AND_SOURCE_OF_TRUTH.md`;
- frontend/UX principles: `UI_UX_PLAN.md`;
- AI direction and current runtime truth: `AI_AND_LLM.md`;
- external product inspiration: `PRODUCT_REFERENCES.md`;
- accepted decisions: `DECISION_LOG.md`.

The repository-root `ESPECIFICACAO_PRODUTO_METAS.md` and
`audits/FINAL_PRODUCT_DEFINITION.md` are preserved as historical product input.
They no longer own current vision, status, roadmap, or implementation promises.
