# Master Plan — FINANALYTICS Wealth OS

**Status:** `ARCHITECTURE LOCKED / IMPLEMENTATION NEXT`

**Updated:** 2026-10-03 — Phase 10.R2-A contract lock

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
| 10.R2 | Smart Financial Context | `CONTRACT LOCKED / IMPLEMENTATION READY` |
| 10.R3 | External Context Layer | `NOT STARTED` |
| 10.R4 | AI Runtime Foundation | `NOT STARTED` |
| 10.R5 | Design, navigation, and System/Light/Dark | `NOT STARTED` |
| 10.R6 | Goals, Planning, FIRE, and Wealth Home recomposition | `NOT STARTED` |
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
