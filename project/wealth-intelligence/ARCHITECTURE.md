# Architecture — FINANALYTICS Wealth OS

**Status:** `10.R1 ARCHITECTURE LOCKED / 10.R2-A CONTEXT BOUNDARY LOCKED`

**Date:** 2026-10-03

**Canonical responsibility:** cross-cutting system architecture, target product
information architecture, capability placement, and migration boundaries.
Detailed financial semantics remain in accepted ADRs and locked phase
contracts. Data semantics live in `DATA_AND_SOURCE_OF_TRUTH.md`.

## 1. Current architecture

```text
Pierre / MyProfit / yfinance
        -> provider adapters and import/cache paths
        -> governed database facts and certified queries
        -> deterministic Goals, Health, Planning, and FIRE services
        -> authenticated FastAPI DTOs/read models
        -> Next.js module pages
```

Verified current facts:

- Goals, Financial Health, Planning, and FIRE exist and are validated.
- Planning and FIRE preserve deterministic Decimal-first authority and explicit
  provenance.
- Investments contains operational import, position, asset, allocation,
  dividend, evolution, and performance-like surfaces; those surfaces are not a
  certified Portfolio Intelligence engine.
- Profile is browser-local and only four non-sensitive extended fields persist.
- Settings is the existing configuration surface but most controls are
  placeholders.
- yfinance is provider-specific market context, not a shared External Context
  Layer.
- There is no Smart Context service, normalized external-context layer,
  provider-aware AI runtime, tool registry, integrated Wealth Home, or
  Portfolio Intelligence runtime today.

## 2. Target architecture

```text
INTERNAL SOURCES                 EXTERNAL PROVIDERS
Pierre / MyProfit / user data   market / macro / news / events
           |                               |
           v                               v
governed facts and readers       adapters -> normalization -> cache/observation
           |                               |
           +---------------+---------------+
                           v
              provenance-aware context sources
                           |
            +--------------+----------------+
            |                               |
            v                               v
deterministic engines/tools             AI runtime
Goals / Health / Planning / FIRE        approved tools only
Portfolio Intelligence (future)         minimum context
            |                               |
            +---------------+---------------+
                            v
             composed Wealth OS experiences
```

The target adds product composition and governed context around the validated
core. It does not collapse the layers into one service.

## 3. Architectural rules

1. **Incremental composition refactor.** Existing engines stay operational
   while context and product layers are introduced.
2. **One capability, one authority.** Embedded journeys and standalone tools
   may reuse an engine; they do not fork its mathematics.
3. **Facts precede interpretation.** Governed readers and deterministic services
   produce financial truth. UI and AI consume it.
4. **Context is typed.** Declared, observed, derived, external observation,
   external expectation, assumption, and user override are not interchangeable.
5. **No universal source precedence.** Each feature selects the semantically
   correct category under an explicit contract.
6. **Simulation is isolated.** Scenarios, saved comparisons, and tool state do
   not mutate portfolio reality or goals implicitly.
7. **Routes migrate deliberately.** R1 locks concepts, not URLs. Existing routes
   and deep links remain until a later implementation contract changes them.

### Smart Financial Context placement (ADR-028)

R2 implementation will introduce one internal, feature-specific composition boundary between
governed sources and consumers. It exposes only context approved for the named
feature and authenticated user; it is not a global user dump, a second
financial engine, an AI memory, or an arbitrary database facade.

Declared monthly gross income remains owned by Profile. Recurring-income
candidates are deterministic observations and require an explicit user
decision before they become confirmed context. Health retains authority over
certified aggregate cashflow, Goals over objective lifecycle, Planning over
projection mathematics and source resolution, and FIRE over its explicit
assumptions composed through Planning. Exact semantics are locked in
`SMART_FINANCIAL_CONTEXT_CONTRACT.md`.

## 4. Target information architecture

The following areas are conceptual product owners, not approved routes or exact
widget specifications.

### Home

- **Purpose:** personal financial command center.
- **Primary questions:** Where am I? What changed? Am I progressing? What needs
  attention? What can I explore next?
- **Reuse:** dashboard summaries, Goals, Health, FIRE, and eligible wealth facts.
- **Future:** cross-domain briefing, alerts, next actions, and contextual entry.
- **Dependencies:** certified summaries, Smart Context, freshness, and
  completeness.
- **AI role:** explain and prioritize approved facts through read-only tools.
- **Excludes:** input-heavy setup, a card directory, invented net worth, or
  unsupported performance.

### Plan

- **Purpose:** one contextual entry over objectives and future decisions.
- **Primary question:** What am I trying to achieve, and what do explicit
  scenarios imply?
- **Reuse:** Goals lifecycle, Planning engines/tool, and FIRE experience.
- **Future:** context-aware starting points and guided transitions between the
  three capabilities.
- **Dependencies:** Smart Context, explicit assumptions, and certified source
  selection.
- **AI role:** structure intent, draft reviewable scenarios, and explain results.
- **Excludes:** merging the three engines, hidden assumptions, or autonomous Goal
  mutation.

### Portfolio

- **Purpose:** portfolio truth plus certified Portfolio Intelligence.
- **Primary questions:** What do I own? How is it composed and concentrated? How
  does investment wealth evolve?
- **Reuse:** governed MyProfit facts, `/wealth` operational data, Dividends facts,
  and the 10.5-A decisions.
- **Future:** deterministic composition and concentration read model after
  10.5-B.
- **Dependencies:** governed position valuation, temporal alignment,
  completeness, ownership, and Decimal contracts.
- **AI role:** explain certified facts only after the capability exists.
- **Excludes:** replacing imports/transactions, cost-as-market fallback,
  performance claims, scores, or recommendations without contracts.

### Explore

- **Purpose:** asset discovery and comparison.
- **Primary question:** What can I inspect or compare outside my current
  portfolio?
- **Reuse:** asset detail and existing market-provider evidence.
- **Future:** search, comparator, screener, tracker, and possibly rankings or
  target-price tools after method contracts.
- **Dependencies:** normalized external catalog, comparable dates/units,
  freshness, and methodology.
- **AI role:** summarize and compare sourced facts.
- **Excludes:** internal portfolio authority, opaque scores, or automatic advice.

### Income

- **Purpose:** income generated by investments.
- **Primary question:** What income has the portfolio generated, and what is
  scheduled or expected from sourced events?
- **Reuse:** Dividends and `income_events` as their existing fact owner.
- **Future:** agenda, history, events, and upcoming-payment context.
- **Dependencies:** event dates, payment semantics, source, and completeness.
- **AI role:** explain patterns without forecasting them as guarantees.
- **Excludes:** duplicated dividend/yield calculation or observed salary
  ownership.

### Monitor

- **Purpose:** tracked criteria, drift, alerts, and attention state.
- **Primary question:** What changed or crossed an explicit rule?
- **Reuse:** Health trends/anomalies and Goal lifecycle facts.
- **Future:** watchlists, alert rules, scheduled monitoring, and sourced event
  relevance.
- **Dependencies:** deterministic rules, saved-state lifecycle, and freshness.
- **AI role:** explain why a certified rule surfaced an item.
- **Excludes:** silent recommendations or AI-authored thresholds.

### Market

- **Purpose:** macro, market, news, event, and reference context.
- **Primary question:** What external context is relevant and how current is it?
- **Reuse:** yfinance and imported benchmark evidence.
- **Future:** normalized macro/reference providers, news, and calendars.
- **Dependencies:** External Context Layer, source, observed/retrieved time,
  status, and freshness.
- **AI role:** summarize cited external context.
- **Excludes:** user portfolio truth or silent replacement of governed facts.

### Copilot

- **Purpose:** global conversational interpretation and orchestration.
- **Primary question:** What do my approved facts and tools say about this
  question?
- **Reuse:** none today; future read-only deterministic capabilities.
- **Future:** global entry, contextual Ask AI, briefing, and smart-form help.
- **Dependencies:** R4 provider abstraction, tool registry, privacy, audit, and
  context minimization.
- **AI role:** interpret, explain, orchestrate, and structure intent.
- **Excludes:** financial calculation, arbitrary SQL, autonomous writes, secrets,
  and uncontracted investment advice.

### Tools

- **Purpose:** discoverable standalone deterministic utilities.
- **Primary question:** Which controlled analysis or comparison should I run?
- **Reuse:** Planning and FIRE engines.
- **Future:** fixed-income calculator, asset comparator, and portfolio simulator.
- **Dependencies:** explicit assumptions, reference provenance, and isolated
  scenario state.
- **AI role:** help configure and explain; never replace calculation.
- **Excludes:** the rule that every engine needs its own permanent page.

### Profile

- **Purpose:** canonical **Declared User Context** surface.
- **Primary question:** What personal context has the user deliberately stated?
- **Reuse:** current `/profile` and authenticated identity.
- **Future:** purpose-limited personal/work context, declared income, and
  planning preferences after R2 contracts persistence and consent.
- **Dependencies:** user ownership, validation, retention, and declared-at
  provenance.
- **AI role:** consume only minimum eligible fields for a specific question.
- **Excludes:** transaction observations, ledger facts, external data, and AI
  memory.

### Settings

- **Purpose:** canonical preference and system-configuration surface.
- **Primary question:** How should the system behave and which providers are
  configured?
- **Reuse:** current `/settings`.
- **Future categories:** Security, Notifications, Appearance, Data & Privacy,
  Integrations, AI & Providers, and Market Data / External Sources.
- **Dependencies:** backend persistence and secret/status workflows.
- **AI role:** show provider status and masked identity only.
- **Excludes:** plaintext browser credentials, `Settings V2`, standalone AI
  settings, or provider-specific settings sprawl.

### Data & Governance

- **Purpose:** imports, provenance, classification review, quality, and audit.
- **Primary question:** Can the user inspect and repair how data entered the
  system?
- **Reuse:** current Governance and import/reconciliation flows.
- **Future:** source health and quality status without exposing technical
  complexity in normal journeys.
- **Dependencies:** governed pipelines and audit evidence.
- **AI role:** no direct truth writes; suggestions require governed confirmation.
- **Excludes:** primary consumer navigation prominence as an architectural
  requirement.

## 5. Investments and Portfolio boundary

**Investments** remains the operational/data-management experience for imports,
transactions, positions, asset detail, existing views, and governance.
**Portfolio** becomes the governed analytical experience that consumes certified
facts. They may share components and data, but permanent duplication is not the
target. Any later consolidation must preserve import and operator workflows and
must not promote current browser heuristics into authority.

## 6. Capability classification

| Capability | Architectural class | Product placement |
|---|---|---|
| Goals | Experience + declared context | Plan |
| Financial Health | Context + experience | Home / Monitor |
| Planning | Engine + tool + embedded flow | Plan / Tools |
| FIRE | Specialized experience + Planning consumer | Plan / Tools |
| Portfolio Intelligence | Deterministic analytical service + experience | Portfolio / Home |
| Profile | Declared context source + experience | Profile |
| Settings | Configuration experience | Settings |
| External Context | Background service + context source | Market / consumers |
| AI Runtime | Background service + orchestrator | Copilot / contextual actions |
| Comparator | Tool | Explore / Tools |
| Screener | Tool | Explore |
| Watchlist | Experience + monitoring service | Explore / Monitor |
| News | External context | Market / Home |
| Copilot | Global experience + orchestrator | Global and contextual access |

## 7. External Context placement

```text
Provider
  -> Adapter
  -> Normalization and semantic classification
  -> Cache or governed observation
  -> Freshness, completeness, and status
  -> Reference Context
  -> Feature, deterministic tool, or approved AI tool
```

Pages must not independently invent provider logic. External observation and
external expectation stay distinct through API and UI. A live external value
does not overwrite an internal certified snapshot unless a feature contract
explicitly chooses that authority.

## 8. AI placement

The future runtime is provider-aware and may support OpenAI, Gemini, and Ollama
through an abstraction. R1 does not lock an interface, required parity, default
provider, fallback order, model, or deployment. AI calls capabilities such as
read context or run certified Planning/FIRE services; it does not reproduce
their calculations.

Detailed runtime, tool, audit, timeout, error, cost, and provider contracts
belong to R4 and `AI_AND_LLM.md`.

## 9. Experience architecture

- Home defaults to information and contextual actions, not setup forms.
- Tools are discoverable through navigation, search, and contextual actions.
- Search-first is preferred for discovery/comparison, not for every page.
- Contextual actions alter context, scenario, comparison, monitoring, analysis,
  or navigation. Animation alone is not interaction.
- Global Copilot, contextual Ask AI, briefing/explanation, and smart-form help
  are valid channels. A full chat duplicated on every page is not.
- Saved watchlists, comparisons, scenarios, and preferences remain separate
  from financial truth until explicit persistence contracts say otherwise.

## 10. Migration and dependency order

The deterministic main path is:

```text
R1 architecture/docs
 -> R2 internal Smart Context
 -> R3 External Context
 -> R4 AI Runtime foundation
 -> R5 design/navigation/theme
 -> R6 experience recomposition
 -> R7 independent validation
 -> resume 10.5-B
```

R2 precedes R3 so internal semantic authority is established before references
are added. R4 follows both context layers so AI tools receive normalized,
provenance-aware inputs. R5 can research tokens and visual migration in parallel
with late R3/R4 work, but its implementation must preserve the locked IA and
context contracts. R6 follows the foundations to avoid recomposing flows twice.
R7 closes the transversal gate before Portfolio Intelligence resumes.

Parallel research is permitted where dependencies are absent; the official
implementation queue remains sequential and is owned by
`IMPLEMENTATION_ROADMAP.md`.
