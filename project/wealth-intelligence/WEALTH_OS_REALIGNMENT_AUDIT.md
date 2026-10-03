# Wealth OS Product Realignment Audit

**Phase:** 10.R0

**Date:** 2026-10-02

**Status:** `AUDIT COMPLETE`

**R1 outcome:** `ARCHITECTURE / DOCUMENTATION LOCKED`

**Canonical owners:** `MASTER_PLAN.md`, `ARCHITECTURE.md`,
`DATA_AND_SOURCE_OF_TRUTH.md`, `UI_UX_PLAN.md`, `AI_AND_LLM.md`, and
`IMPLEMENTATION_ROADMAP.md`

**Portfolio gate:** `10.5-B — PAUSED / PENDING WEALTH OS REALIGNMENT`

> This document is R0 evidence, not the permanent architecture specification.
> R1 converted its accepted direction into the canonical owners above. Preserve
> this audit for traceability; resolve current conflicts through the documented
> precedence order.

## 1. Status

The repository can evolve incrementally from modular calculators toward one
personal Wealth OS without discarding Goals, Financial Health, Planning, FIRE,
or the 10.5-A Portfolio Intelligence findings. No architecture inconsistency
requires a rewrite. The blocking product problem is ownership and composition:
validated engines exist, but navigation, context reuse, documentation, external
references, and future AI are not yet organized as one experience.

R0 changes documentation only. It creates no backend/frontend behavior,
contract, schema, route, provider, theme, detector, or Portfolio Intelligence
implementation. Phase 10.5-B remains paused, not cancelled.

## 2. Why Realignment Is Needed

- Top-level navigation reflects technical domains rather than user journeys.
- Goals, Planning, and FIRE are separate form-heavy surfaces with repeated
  wealth, contribution, return, inflation, horizon/date, and source choices.
- The Wealth Intelligence landing page is a directory of module cards, not a
  context-rich personal home.
- Existing facts are only partially reused. Portfolio wealth can already be
  selected server-side, while income, spending, goal intent, profile context,
  and macro references do not yet feed a shared context layer.
- Profile and Settings look complete but are mostly browser-local or transient.
- External data is provider-specific and unevenly governed; AI is planned but
  not implemented.
- Light/dark tokens exist, yet the live shell and many components hard-code the
  dark palette. Theme work alone would not solve product fragmentation.
- Product vision, roadmap, status, UX, AI, and research material overlap across
  root and project documents, including stale historical audits.

## 3. What Must Be Preserved

- Goals lifecycle and user-governed values.
- Financial Health certified transaction boundary and deterministic metrics.
- Planning projection, target, required-contribution, comparison, provenance,
  precision, and transient-scenario contracts.
- FIRE as a thin deterministic layer composed over Planning.
- 10.5-A findings: imported position value is the future MVP direction;
  aggregate wealth and position valuation remain distinct; performance and
  benchmarks remain deferred.
- Existing MyProfit, Pierre, yfinance, authentication, and governance paths
  until their replacements are explicitly contracted and validated.
- `Decimal`/string financial authority, explicit assumptions, provenance,
  read-only simulations, user ownership, and no AI-calculated truth.

## 4. Current Product Architecture

```text
Pierre / MyProfit / yfinance
        ↓
provider adapters + imports/cache
        ↓
governed database facts / certified queries
        ↓
deterministic Goals, Health, Planning and FIRE services
        ↓
FastAPI DTOs and read models
        ↓
Next.js module pages
```

The lower layers already support the intended authority model. The missing
product layer is shared context plus coherent journeys. There is no Smart
Context service, external-context normalization layer, provider-aware AI
runtime, tool registry, or integrated Wealth OS home today.

## 5. Current Navigation

| Current area | Real routes / tabs | Finding |
|---|---|---|
| Controle Financeiro | `/`, transactions, categories, installments | Functional domain; home is cashflow-centric rather than whole-wealth-centric |
| Investimentos | `/wealth`, patrimônio, alocação, dividendos, evolução | Mature surface, but several browser calculations are not certified Portfolio Intelligence authority |
| Wealth Intelligence | hub, `/goals`, health, planning, FIRE | Five separate destinations; the hub is a directory |
| Governança | overview, Pierre classification, MyProfit data/imports, audit | Operational/data-governance area presented as a primary product domain |
| Configurações | settings, profile, accounts | Correct reusable surfaces, but behaviors are partially placeholders/local-only |

This produces cognitive load between **Investments** and **Wealth
Intelligence**, and between **Goals**, **Planning**, and **FIRE**. Route changes
are not approved in R0.

## 6. Goals / Planning / FIRE Overlap

| Concern | Goals | Planning | FIRE | Product conclusion |
|---|---|---|---|---|
| Objective/target | Stores goal name, type, amount, date, status | Can project an existing Goal or a free target | Builds a specialized FI target | Keep separate domain ownership; compose one guided Plan journey |
| Current wealth | Manual `current_amount` | User, Goal-current, or portfolio selector | User or portfolio selector | Shared source chooser/context, never three independent truths |
| Contribution | Stored planned contribution | Scenario contribution / solved required contribution | Scenario or solved required contribution | Distinguish stored intent, selected assumption, and calculated result |
| Return/inflation | `assumptions_json` exists but is not Planning authority | Explicit scenario assumptions | Explicit scenario assumptions, composed through Planning | One reusable assumption editor; no automatic macro substitution |
| Horizon/date | Goal deadline | Horizon/target date/as-of | Horizon/desired FIRE date/as-of | Reuse context, preserve different semantics |
| Projection | No independent certified engine | Canonical projection and solvers | Delegates to Planning | Never duplicate engine math |

Target responsibility remains sound:

- **Goals:** objective lifecycle, stored intent, tracking.
- **Planning:** deterministic simulation/solver engine and advanced laboratory.
- **FIRE:** specialized independence experience that composes Planning.
- **Smart Context:** provides eligible facts/references without silently choosing
  assumptions.
- **AI:** drafts/explains/orchestrates after the user can review inputs.

## 7. Existing Profile

The real `/profile` page exposes name, authenticated e-mail, phone, birthdate,
CPF, occupation, employer, gross monthly income, tax regime, and employment
start. There is no profile API or extended backend model. Only `display_name`,
`occupation`, `company`, and `tax_regime` persist in
`fin_profile_extended`; old browser records are rewritten to remove sensitive
fields. Phone, birthdate, CPF, income, and employment start are transient and
explicitly not saved.

No Planning, FIRE, Health, or Goals path consumes this extended profile. The
page performs formatting but no authoritative validation. Authenticated name
and e-mail come from the login user object.

## 8. Existing Settings

The real `/settings` page contains Security, Notifications, Appearance, and
Data/System sections. Current behavior is limited:

- password change is a client-only success simulation with no API call;
- 2FA, e-mail notifications, weekly reports, anomaly alerts, theme, and locale
  are marked `Em breve`; toggles live only in component state;
- export downloads the browser profile key plus a timestamp, not all user data;
- clear removes only `fin_profile_extended`;
- there is no backend settings persistence or provider configuration UI.

Settings is nevertheless the correct canonical surface. Do not create
`Settings V2`, `Preferences`, or a separate `AI Settings` route.

## 9. Declared / Observed / External / Assumption Model

| Class | Meaning | Example | Authority rule |
|---|---|---|---|
| DECLARED | User states a personal fact or preference | profile income, goal | User-governed; never overwritten silently |
| OBSERVED | Governed event/fact seen in financial data | incoming transaction, portfolio snapshot | Preserve source, scope, date, completeness |
| DERIVED | Deterministic output from governed inputs | monthly average, savings rate | Backend engine/query authority |
| EXTERNAL OBSERVATION | Current/past third-party fact | quote, current SELIC | Source and observed-at/freshness required |
| EXTERNAL EXPECTATION | Third-party forecast | Focus inflation expectation | Label expectation, provider, date, horizon |
| ASSUMPTION | Scenario premise selected by user | expected portfolio return | Explicit, reviewable, scoped to analysis |
| USER OVERRIDE | User substitutes a reference/premise | chosen inflation for one run | Preserve both offered reference and chosen value |

The classes are not a global precedence ladder. Each feature must request the
semantically correct class. Observed salary may inform a Planning reference;
it does not overwrite declared employment context. Current CDI is not an
expected portfolio return.

## 10. Smart Context Opportunities

- Reuse the certified portfolio selector for eligible investment wealth.
- Offer observed monthly income/expense and derived savings capacity as
  labeled references after dedicated contracts; never auto-commit them.
- Carry Goal target/date/contribution as stored intent and offer explicit
  `Use` actions where semantics are approved.
- Offer external macro observations/expectations with source/date/freshness.
- Centralize as-of date, source, scope, currency, completeness, and provenance.
- Prefill common flows while retaining manual fallback and explicit override.

Candidate product principle: **If FinAnalytics already knows an eligible fact,
do not ask the user to type it again. Show what is known, its source and date,
and let the user choose when it is an assumption.**

### Smart Context matrix

| Context | Type | Existing source | Reliability | Auto-fill? | User override? | Provenance required |
|---|---|---|---|---|---|---|
| Investment wealth | Observed/governed fact | guarded monthly `portfolio_snapshots.patrimonio` | High at monthly investment-wealth grain | Offer/select now | Source choice, not fact overwrite | Yes: source, month, run/update, scope |
| Salary declared | Declared | Profile field is transient today | Low until governed persistence exists | No today | Yes | Yes: user + declared-at |
| Salary observed | Observed candidate | governed incoming transactions | Medium candidate; classification absent | No; offer only after R2 contract | Confirm/keep declared/edit | Yes: account/source, occurrences, period |
| Monthly expenses | Observed/derived | Financial Health certified query | High for governed period/scope | Offer as reference after contract | Yes for scenario assumption | Yes: period, scope, completeness |
| Savings capacity | Derived candidate | Health surplus/deficit history | Insufficient; 10.3.7-A deferred | No | Explicit scenario value only | Yes: method/window/currency |
| Inflation reference | External observation/expectation | no active certified reference read model | Unavailable today | No | Yes | Yes: semantic type, provider, date, horizon |
| SELIC | External observation | no active BCB adapter; schema/research only | Unavailable today | No | Yes when used as a reference | Yes: series, provider, observed-at/freshness |
| Expected return | Assumption | user input | Explicit but not factual | Never automatic | Yes, required | Yes: user-selected and analysis scope |
| Goal target | Declared/governed fact | Goals database | High | Yes when Goal is selected | Edit through Goals, not hidden override | Yes: Goal identity/version/date |
| FIRE spending | Assumption | user input; no Health prefill contract | Explicit | No today; future reference only | Yes, required | Yes: selected value and reference if offered |
| Portfolio positions | External-to-governed observation | MyProfit position snapshots | Partial; current valuation coverage incomplete | No value-weighted prefill until 10.5 contract | No silent replacement; source selection only | Yes: snapshot, valuation basis, completeness |

## 11. Recurring Income Feasibility

The live governed ledger contains the required raw signals: provider,
transaction identity, account, description/original description, amount,
currency, date, type/status, category, payer/receiver, and economic
classification. The read-only R0 inspection found 1,462 transactions across 18
months, including 349 classified incoming entries. Repeated incoming
descriptions exist across many months, but include investments and ambiguous
transfers with variable values and dates.

Therefore a future deterministic candidate detector is feasible but not yet
authoritative. It must:

- normalize source/description without exposing unnecessary counterpart PII;
- cluster by account/source, amount band, and cadence window;
- tolerate end-of-month / beginning-of-next-month calendar shifts;
- expose observed months, first/last occurrence, latest amount, amount band,
  cadence evidence, and confidence inputs;
- exclude investment income and transfers without sufficient semantics;
- require user confirmation before becoming a declared planning reference.

`RecurringIncomeCandidate` is a concept only; R0 locks no schema or algorithm.

## 12. External Data Current State

| Source | Current state | Semantic limitation |
|---|---|---|
| Pierre Finance | Active import/API for accounts and transactions | Imported external observations become governed ledger facts after ingestion |
| MyProfit CSV | Active positions, monthly portfolio evolution, dividends, provenance | Snapshot grains differ; provider return/benchmark methodology is not locally certified |
| yfinance | Active quote/history/fundamental adapter with in-memory TTL cache | Provider-specific; partial coverage; float paths; hard-coded FX fallback; current FX reused historically |
| Market/benchmark tables | Schema exists | No general certified current macro provider/read model |
| BCB/SGS | Researched/planned only | No active normalized adapter/cache/freshness contract |
| News | Absent | No provider, relevance, provenance, or injection boundary |
| Gemini/OpenAI/Ollama | Config keys/stubs/plans only | No runtime or calls |

## 13. AI Current State

- No Advisor service, insight generator, Copilot, scheduler, Ollama, OpenAI
  client, or provider abstraction exists in production.
- The three Gemini integration files are empty.
- `GEMINI_API_KEY` and `OPENAI_API_KEY` are server environment settings.
- `google-generativeai` is installed.
- AI classification/prompt/run tables provide schema/audit scaffolding, but no
  active AI classification or `ai_insights` runtime was found.
- Existing `AI_AND_LLM.md` and security documents are proposals, not running
  architecture.

This should be reused as governance/research input. Do not build a second AI
architecture around the empty stubs.

## 14. Design / Theme Current State

Tailwind/shadcn variables define both `:root` light tokens and `.dark` tokens,
but the root layout does not apply `.dark`; instead `body`, `AppShell`, and
many components directly use `bg-zinc-950`, `text-zinc-*`, `border-white/*`,
and other dark-only values. At least 74 TSX files contain dark-specific utility
patterns. Settings shows a non-functional dark-theme placeholder.

The target should be **System / Light / Dark** using shared semantic tokens,
implemented incrementally. Cost is moderate-to-high because primitives/tokens
exist, but component migration and chart/accessibility review are broad.

## 15. UX Problems vs Theme Problems

| UX/product problem | Theme/design problem |
|---|---|
| Repeated forms and assumptions | Hard-coded dark colors |
| Module-directory home | Incomplete semantic token adoption |
| Weak cross-module context | No working theme preference/system detection |
| No visible freshness/reference layer | Charts and status colors need dual-theme contrast review |
| Limited discovery/search and comparison | Visual hierarchy varies across legacy areas |
| Placeholder settings/profile behavior | Responsive/mobile debt |

Light mode will not fix fragmentation. Context, task composition, provenance,
and interaction must be designed before or alongside visual migration.

## 16. Product Reference Analysis

The canonical reference matrix is `PRODUCT_REFERENCES.md`. The reusable
patterns are search-first discovery, progressive disclosure, shared parameters,
inline scenario controls, side-by-side comparison, saved criteria with a real
lifecycle, visible composition, and source/freshness labels.

Investidor10 demonstrates breadth and discovery but also shows why not every
feature belongs in the initial roadmap. Portfolio manager, tracker/watchlist,
dividend agenda, comparator, results/material-facts calendar, and search are
valuable candidates. Target prices, recommended portfolios, rankings, Small
Cap/IPO lists, and radars require separate authority/value decisions.

Mais Retorno supports a coherent tools model: asset/fund comparator, portfolio
simulator, and saved comparisons. FinAnalytics should adapt the interaction
pattern, not commercial/proprietary analytics.

The Valor pattern supports reference-first calculators with editable
assumptions. ETFs Brasil supports shared parameters and up to three visible
portfolios with allocation totals and side-by-side scenarios. Neither source
defines FinAnalytics formulas.

## 17. Target Information Architecture

This is a candidate map for R1, not an approved route contract.

| Area | Purpose | Existing reuse | Future modules | Data dependencies | AI role | External-data role |
|---|---|---|---|---|---|---|
| Home | Personal financial command center | dashboards, Goals, Health, FIRE, wealth facts | alerts, briefing, next actions | certified cross-domain summaries | concise briefing/explanation | freshness/context only |
| Plan | Goals and guided future decisions | Goals, Planning, FIRE | composed journeys | Smart Context + deterministic engines | draft/review assumptions; explain | optional macro references |
| Portfolio | Current investment position and intelligence | `/wealth`, MyProfit | certified Portfolio Intelligence, rebalance | position/portfolio facts | explain certified facts | quotes/fundamentals with labels |
| Explore | Find and compare assets/opportunities | asset detail, yfinance | search, watchlist, comparator, screener, rankings | external normalized catalog | summarize/compare sourced facts | primary input |
| Income | Cash inflows and passive-income context | cashflow, dividends | recurring-income candidates, agenda | governed transactions/income events | explain patterns | event calendars where sourced |
| Monitor | Health, goals drift, alerts | Financial Health, anomalies | alert rules/status center | certified trends and rule outputs | explain attention items | relevant freshness/events |
| Market | Macro and relevant news/events | imported benchmarks | macro context, news, calendars | External Context Layer | summarize with citations | primary input |
| Copilot | One conversational orchestration surface | none | global and contextual ask/briefing | approved read-only tools | orchestrate and interpret | through approved tools only |
| Tools | Advanced standalone laboratories | Planning/FIRE advanced modes | fixed income, comparator, portfolio simulator | deterministic engines + explicit assumptions | assistance, not calculation | visible references |
| Profile | Declared personal context | current Profile | governed declared context/preferences | user-owned profile service | minimal eligible context | none by default |
| Settings | System/user/provider preferences | current Settings | privacy, integrations, AI/providers, market sources | settings + secret/status backend | provider status only | integration configuration |
| Data & Governance | Import, classify, audit, provenance | current Governance | source health/reconciliation | raw/governed pipelines | no direct truth writes | provider operations |

Governance should remain accessible but may move out of primary consumer
navigation after R1 validates operator workflows.

## 18. Page vs Tool vs Engine Classification

| Capability | Classification | Future product placement |
|---|---|---|
| Goals | Primary experience + context source | Plan |
| Financial Health | Primary experience + context source | Monitor/Home |
| Planning | Engine + advanced tool + embedded flow | Plan and Tools |
| FIRE | Primary specialized experience + Planning composition | Plan; advanced controls in Tools |
| Portfolio Intelligence | Primary experience + context source | Portfolio/Home |
| Comparator | Tool | Explore/Tools |
| Screener | Tool | Explore |
| Rankings | Discovery tool | Explore, only with governed methodology |
| Fixed-income calculator | Deterministic tool | Tools |
| Dividend agenda | Supporting experience/context source | Income/Monitor |
| Watchlist | Primary monitoring experience | Explore/Monitor |
| Market news | Context source/background service | Market/Home |
| Copilot | Global experience/orchestrator | Global entry + contextual ask actions |

Engines remain reusable and should not each require a permanent top-level page.

### Functional capability matrix

| Capability | Exists Today | Current Owner | Future Experience | Reuse / Refactor / New | Phase |
|---|---|---|---|---|---|
| Goals | Yes, validated | Goals model/router/UI | Objective lifecycle and tracking inside Plan | Reuse + product refactor | 10.R6 |
| Health | Yes, validated | Health query/services/API/UI | Monitor/Home financial-health context | Reuse | 10.R2 / 10.R6 |
| Planning | Yes, validated | Planning engines/APIs/UI | Embedded guidance plus advanced laboratory | Reuse + product refactor | 10.R6 |
| FIRE | Yes, validated | FIRE thin domain/service/UI | Specialized independence journey using Planning | Reuse + product refactor | 10.R6 |
| Portfolio Intelligence | Audit only | 10.5-A evidence | Certified composition/concentration in Portfolio/Home | New contract/implementation; reuse facts | 10.5-B+ |
| Profile | Partial/local | `/profile` + auth user | Canonical declared personal context | Refactor/reuse | 10.R2 |
| Settings | Partial/placeholders | `/settings` | Canonical security, privacy, appearance, integrations, AI/provider settings | Refactor/reuse | 10.R1 / 10.R5 |
| Market Data | Partial | yfinance protocol/service | Shared external reference context | Refactor/extend | 10.R3 |
| Advisor | No runtime | None | Contextual explanation through Copilot/tools | New | 10.R4 / 10.R6 |
| Insights | No runtime | AI DB scaffolding only | Structured, sourced interpretations | New; reuse audit schema if suitable | 10.R4+ |
| Watchlist | No | None | Saved monitoring criteria in Explore/Monitor | New | After 10.5 |
| Comparator | No certified capability | None | Search-first side-by-side tool | New | 10.R3 / after 10.5 |
| Rankings | No | None | Optional discovery view with governed methodology | New/defer | After 10.5 |
| Screener | No | None | Filtered discovery tool | New/defer | After 10.5 |
| Dividend Agenda | Partial event facts | income events / Dividends | Income/Monitor calendar without duplicate yield math | Reuse + refactor | 10.R3 / after 10.5 |
| News | No | None | Relevant sourced feed/context | New | 10.R3 |
| Alerts | Partial anomaly facts, no unified service | Health + UI fragments | Rule-based cross-domain attention center | Reuse + new composition | 10.R2 / 10.R6 |
| Copilot | No | None | Global conversation, contextual ask actions, briefing | New | 10.R4 / 10.R6 |
| Calculators | Planning/FIRE exist; fixed-income absent | deterministic engines | Consolidated Tools area with reusable engines | Reuse + selective new tools | 10.R6+ |

## 19. Smart Defaults Principle

Candidate principle:

> Known eligible data should prefill or be offered for use, with source,
> reference time, scope, freshness, and completeness visible. Facts are not
> silently converted into assumptions, and user override remains explicit.

An empty form is the fallback for unavailable/ineligible context, not the
normal entry state. This applies first to Planning/FIRE sources, Goal facts,
income/expense references, as-of dates, and future macro reference cards.

## 20. Profile Future Role

Reuse `/profile` as the canonical **Declared User Context** surface with
sections for Identity, Personal Context, Work Context, Declared Income,
Financial Preferences, and Planning Preferences. Backend persistence,
validation, retention, and consent must be contracted before expanding use.

Observed transactions do not become Profile data automatically. The UI should
show declared income alongside a confirmed observed-income reference. CPF,
telephone, employment identifiers, and birthdate stay outside AI/Planning by
default unless a feature has an explicit need.

## 21. Settings Future Role

Reuse `/settings` as the canonical settings surface:

- Security;
- Notifications;
- Appearance;
- Data & Privacy;
- Integrations;
- AI & Providers;
- Market Data / External Sources.

Settings may display provider availability, scopes, last success, freshness,
and a masked identifier. It must not store secrets in the browser. Placeholder
controls should not imply successful persistence or account actions.

## 22. External Context Layer Direction

Candidate dependency flow:

```text
External provider
  -> provider adapter
  -> normalization/semantic classification
  -> cache or governed observation store
  -> freshness/completeness/status
  -> reference context service
  -> deterministic feature or approved AI tool
```

Every record needs source, observed/retrieved time, freshness, unit/currency,
semantic type, status, and provider metadata when useful. Pages must not call
providers independently. Current yfinance protocol/cache is reusable evidence,
not yet the complete shared layer.

## 23. AI Runtime Direction

Evolve the existing planned architecture into one provider-aware runtime for
Ollama, Gemini, and OpenAI, with server-side credentials and structured output.
AI invokes approved services/tools; it does not query arbitrary tables.

Conceptual tool feasibility:

| Tool concept | Deterministic capability today | R0 assessment |
|---|---|---|
| `get_financial_context` | Partial dashboards/ledger | Needs composed certified context |
| `get_health_context` | Yes | Reuse Health APIs/services |
| `get_goals` | Yes | Reuse authenticated Goals query |
| `run_planning_projection` | Yes | Reuse five Planning capabilities; explicit assumptions |
| `run_fire_analysis` | Yes | Reuse FIRE analysis; explicit assumptions |
| `get_portfolio_intelligence` | No | Wait for 10.5 contract/implementation |
| `get_market_context` | Partial yfinance only | Wait for External Context Layer |
| `get_watchlist` | No | Future |
| `compare_assets` | No certified comparator | Future |
| `get_relevant_news` | No | Future external/news contract |

No tool schema or registry is locked in R0.

## 24. Security / Secrets Direction

- JWT access token and user JSON currently persist in `localStorage`; this is
  known browser-exposure debt for future auth hardening.
- Profile persistence is intentionally restricted to four non-secret fields;
  Settings export/clear operates only on that browser record.
- Gemini, OpenAI, Pierre, and MyProfit credentials are server environment
  settings and must remain server-side.
- Future Settings configuration requires a backend/env/secret-store workflow;
  the browser receives status and masked identifiers, never plaintext secrets.
- AI receives the minimum tool output needed for the question. Exclude CPF,
  phone, tokens, credentials, full account identifiers, and unrelated work
  context by default.

## 25. Documentation Inventory

| Group | Documents | Current role / finding |
|---|---|---|
| Entry/status | root `README.md`, WI `README.md`, `MASTER_PLAN.md`, `CURRENT_STATE.md`, `IMPLEMENTATION_ROADMAP.md` | Necessary owners, but status/vision/roadmap duplication exists |
| Authority | `ARCHITECTURE.md`, `DATA_AND_SOURCE_OF_TRUTH.md`, `DECISION_LOG.md`, `SECURITY_AND_GOVERNANCE.md`, `TESTING_STRATEGY.md` | Keep as canonical concern owners |
| Locked evidence | `PLANNING_UX_CONTRACT.md`, FIRE audit/contract/plan, Portfolio audit | Preserve; do not fold locked semantics into generic plans |
| Product/UX | root `ESPECIFICACAO_PRODUTO_METAS.md`, `UI_UX_PLAN.md`, `audits/FINAL_PRODUCT_DEFINITION.md` | High overlap; vision is valuable, specific page plan is partly stale |
| AI/external/infra | `AI_AND_LLM.md`, `INFRASTRUCTURE.md`, external-data, env, dependency audits | Mix of proposal and research; canonical ownership needs clearer links/status |
| Historical evidence | repository/dependency audits, `CHANGELOG.md` | Preserve; historical facts must not be treated as current state |
| Legacy global docs | `docs/` index, domain, source-of-truth, frontend, roadmap, decisions, testing | Broader/legacy system documentation; not WI architecture authority under ADR-003 |
| Agent guidance | `frontend/AGENTS.md` | Next.js-specific; root operational governance was missing |

## 26. Documentation Ownership Matrix

| Concern | Existing owner(s) | Problem | Canonical owner after realignment | Action |
|---|---|---|---|---|
| Product vision | `MASTER_PLAN`, root product spec, final-product audit, root README | Repetition and stale roadmap detail | `MASTER_PLAN.md` | MERGE in R1; link source vision |
| Current state | `CURRENT_STATE`, READMEs, old repository audit | Snapshot facts repeated | `CURRENT_STATE.md` | KEEP; historical audit stays evidence |
| Roadmap/status | `MASTER_PLAN`, `IMPLEMENTATION_ROADMAP`, READMEs | Same statuses in four places | `MASTER_PLAN` for phase status; `IMPLEMENTATION_ROADMAP` for queue | RECYCLE/trim mirrors in R1 |
| Architecture | `ARCHITECTURE`, several audits | Proposed layers spread out | `ARCHITECTURE.md` | KEEP/EXPAND in R1 |
| Source of truth/context | `DATA_AND_SOURCE_OF_TRUTH`, contracts | Missing unified context taxonomy | `DATA_AND_SOURCE_OF_TRUTH.md` | EXPAND in R1/R2 |
| Frontend UX/IA | `UI_UX_PLAN`, Planning UX contract | Generic page plan is stale; contract is scoped | `ARCHITECTURE.md` for IA; scoped locked contracts for behavior | RECYCLE; decide design owner in R5 |
| Design system/theme | CSS + UX docs | No canonical design contract | To be decided in R5 | No new R0 design doc |
| AI | `AI_AND_LLM`, security, env audit | Proposal can be mistaken for implementation | `AI_AND_LLM.md` | KEEP; mark verified/proposed sharply |
| External data | source-of-truth + external research audit | Research and canonical rules mixed | `DATA_AND_SOURCE_OF_TRUTH.md`; research audit as evidence | MERGE rules in R3 |
| Profile/Settings | root README + code only | UI claims exceed persistence reality | `CURRENT_STATE.md` then R2 contracts | DOCUMENT, then contract |
| Testing | global docs + WI strategy + contracts | General vs phase-specific overlap | `TESTING_STRATEGY.md` + contract acceptance | KEEP/link |
| Decisions | `DECISION_LOG.md` | Correct owner | `DECISION_LOG.md` | KEEP |
| Agent instructions | frontend guide only | No repository-wide safeguards | root `AGENTS.md` | CREATE |
| Product references | none | URLs/patterns had no owner | `PRODUCT_REFERENCES.md` | CREATE |
| R0 findings | none | No existing owner for transversal audit | this document | CREATE |
| Portfolio audit | 10.5-A audit | Correct evidence owner | existing audit | KEEP/FREEZE |

## 27. Documentation Consolidation Plan

### KEEP

`project/wealth-intelligence/README.md`, `MASTER_PLAN.md`, `CURRENT_STATE.md`,
`IMPLEMENTATION_ROADMAP.md`, `ARCHITECTURE.md`,
`DATA_AND_SOURCE_OF_TRUTH.md`, `DECISION_LOG.md`, `AI_AND_LLM.md`,
`SECURITY_AND_GOVERNANCE.md`, `INFRASTRUCTURE.md`, `TESTING_STRATEGY.md`,
`CHANGELOG.md`, and all locked/audit evidence for Planning, FIRE, and 10.5-A.

### MERGE / RECYCLE IN R1

- Merge durable product vision from `ESPECIFICACAO_PRODUTO_METAS.md` and
  `audits/FINAL_PRODUCT_DEFINITION.md` into `MASTER_PLAN.md`; preserve links and
  history, then mark source documents superseded rather than deleting them.
- Recycle valid target architecture/IA from `UI_UX_PLAN.md` into
  `ARCHITECTURE.md`; keep locked Planning details in its own contract.
- Move canonical external semantics/freshness rules from the research audit to
  `DATA_AND_SOURCE_OF_TRUTH.md`; keep vendor research as evidence.
- Reduce READMEs to onboarding/status summaries with links to owners.

### RENAME / DEPRECATE / ARCHIVE LATER

No rename or deletion occurs in R0. R1 may label stale audits as historical and
propose an archive location after references are checked. `docs/` remains the
broader legacy/global documentation set and must not silently compete with the
WI owners.

### CREATE

Only root `AGENTS.md`, `PRODUCT_REFERENCES.md`, and this R0 audit are justified.
No separate product vision, Smart Context, AI plan, or design-system document
is justified now.

## 28. AGENTS.md Role

The new root guide is an operational governance layer, not a product spec. It
points agents to canonical documents; preserves locked contracts, dirty
worktrees, Decimal, authority boundaries, privacy, external data, AI tool use,
and explicit Git/stop gates. `frontend/AGENTS.md` remains scoped to Next.js.

## 29. Revised Roadmap Proposal

| Phase | Outcome | Dependency rationale |
|---|---|---|
| 10.R0 | Product realignment audit | Establish evidence and decisions to lock |
| 10.R1 | Product architecture, IA, documentation consolidation, governance lock | One owner/concern and target experience before contracts change |
| 10.R2 | Smart Financial Context | Internal facts first: Profile, observed income, eligibility, autofill/override contracts |
| 10.R3 | External Context Layer | Normalized provider/reference/freshness semantics after internal context |
| 10.R4 | AI Runtime Foundation | Provider abstraction and read-only tools consume deterministic/internal/external context |
| 10.R5 | Design System, navigation implementation, System/Light/Dark | Implement shell/tokens after information and context contracts are known |
| 10.R6 | Goals + Planning + FIRE product recomposition | Compose validated engines through Smart Context and new IA without rewrites |
| 10.R7 | Independent product/architecture validation | Adversarial validation of authority, privacy, UX, docs, and regression |
| Then 10.5-B | Resume Portfolio Intelligence contract lock | Re-enter under the locked Wealth OS architecture; preserve 10.5-A decisions |

Refinement to the candidate: R1 must lock information architecture and
documentation ownership, but not implement navigation; R5 implements the shell
and theme. R2 precedes external data because useful context already exists
internally. R4 follows R3 because AI tools should consume normalized,
provenance-aware context. R6 follows R5 to avoid recomposing forms twice.

## 30. What Happens to Phase 10.5

- `10.5-A = AUDIT COMPLETE / USER DECISIONS RESOLVED` and remains authoritative.
- `10.5-B = PAUSED / PENDING WEALTH OS REALIGNMENT`; it is not cancelled.
- The approved MyProfit `total_atual` direction and performance/benchmark defer
  decision remain valid.
- R phases may use 10.5-A findings as evidence but cannot implement Portfolio
  Intelligence or reopen its decisions implicitly.
- After R7, 10.5-B must lock its contract within the new Portfolio/Home/Context
  boundaries rather than creating another isolated page.

## 31. Risks

1. Documentation consolidation accidentally changes locked semantics.
2. “Smart” defaults blur facts, external references, and scenario assumptions.
3. Profile becomes a duplicate financial ledger or expands sensitive data use.
4. Observed-income matching mislabels transfers or investment proceeds.
5. Theme migration becomes a visual rewrite before product flows are composed.
6. AI receives raw database access or excessive personal/financial context.
7. Provider-specific code leaks into pages and duplicates caches/normalization.
8. Existing Investments browser heuristics are promoted to certified facts.
9. Navigation redesign hides governance/data-operability workflows.
10. R0 proposals are mistaken for locked schemas/routes/contracts.

## 32. User Decisions Required

No material decision is required to close R0. The audit has recommended
defaults and identified where decisions belong; R1 must not start without an
explicit user task. The following are future lock gates, not R0 blockers:

| Future question | Context | Options/trade-off | Recommended default |
|---|---|---|---|
| Target IA | Current modules compete with user journeys | Keep technical modules vs compose journey areas | Adopt the candidate map; keep Governance secondary |
| Documentation consolidation | Multiple vision/status copies | Leave duplication vs merge/link/archive later | One canonical owner per concern; no deletion until references are audited |
| Profile persistence/privacy | Current fields exceed persisted behavior | Persist all vs minimum useful declared context | Minimum governed context; CPF/phone excluded from finance/AI by default |
| Theme target | Tokens exist but components are dark-hard-coded | Dark only vs Light only vs System/Light/Dark | System/Light/Dark via incremental token migration |
| 10.5-B resume point | Portfolio context is valuable but realignment must govern it | Resume early vs after transversal validation | Resume after 10.R7 as proposed |

## 33. Recommended Next Step

Historical R0 recommendation, now satisfied by R1:

`PHASE 10.R1 — ARCHITECTURE / DOCUMENTATION LOCKED`

R1 should reconcile canonical owners, lock the target information architecture
and phase boundaries, label historical/proposed material, and define acceptance
gates. It must not implement Smart Context, external providers, AI runtime,
navigation, theme, Goals/Planning/FIRE recomposition, or 10.5-B.
