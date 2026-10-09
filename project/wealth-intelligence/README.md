# FINANALYTICS — Wealth OS Documentation

**Status:** `10.R2 IMPLEMENTED / VALIDATED / CLOSED`

**Next:** `10.R3-C DOMAIN, NORMALIZATION & EXECUTABLE REGISTRY — READY / NOT STARTED`

This directory is the canonical architectural and product documentation area
for FINANALYTICS Wealth Intelligence. FINANALYTICS is evolving into a personal
Wealth OS through incremental composition of its validated financial core.

## Current state

Goals, Financial Health, Planning, and FIRE are validated. The 10.5-A Portfolio
Intelligence audit and its user decisions remain valid. Phase 10.5-B is paused
until the Wealth OS realignment closes at R7.

R2-A locks declared financial context, deterministic recurring-income
candidates, human decisions, ownership, provenance, and feature-specific
composition. It changes documentation only and creates no backend, frontend,
test, migration, dependency, provider, runtime, or route behavior.

R2-B1 implements only the two approved persistence owners, user-scoped
repositories, a fail-closed local ownership guard, one migration, and focused
structural tests. APIs, detection, composition, and frontend work remain
unstarted.

R2-B2 exposes only authenticated declared Profile context through `GET` and
`PATCH /api/v1/profile/context`, with strict Decimal-string input, explicit
null clearing, safe ownership failure, and purpose-limited provenance. B2 itself
added no income detection, decisions API, composition, or frontend work.

R2-B3 adds the read-only governed-ledger adapter and pure recurring-evidence
engine. It emits only deterministic 3-of-6 candidates with opaque versioned
identity, exact Decimal evidence, and structured risk flags. It persists no
candidate, exposes no API, and does not classify any candidate as income.

R2-B4 composes that current evidence with durable B1 decisions and exposes the
four authenticated candidate review/confirm/reject/reset routes locked by the
contract. Confirm/reject revalidate an opaque evidence fingerprint, stale
decisions remain visible and reversible, and only decision rows are written.
No candidate evidence, Profile fact, transaction, frontend, or new schema is
mutated.

R2-B5 adds the internal authenticated `SmartFinancialContextService`, immutable
Smart Values, explicit allowlists for Profile, Home, Planning, Goal, and FIRE,
and thin adapters over the existing Profile, recurring-income, Health, Goals,
and ADR-023 portfolio authorities. Composition is read-only and preserves
provenance, exact Decimal values, source-specific time/freshness, unavailable
states, and explicit assumptions. It adds no public API, frontend, migration,
provider, AI behavior, or financial formula.

R2-B6 connects the existing `/profile` route to the declared-context and
recurring-income review APIs. Declared and observed facts remain visually and
semantically separate; saves, clears, confirmations, rejections, and resets are
explicit. No eligible legacy declared-income value exists in the historical
browser record, so initial load never uploads local data. The four approved
presentation/professional fields remain browser-local and are never sent to the
financial-context APIs.

The five material findings from the first independent B6 review are remediated:
candidate mutations and retries share a fail-safe interaction lock; stale
confirmed and rejected decisions remain distinguishable without presenting old
money as current; action feedback survives empty-list refreshes and reports
refresh failures accurately; offset-less repository timestamps are interpreted
as UTC separately from civil dates; and rendered Profile tests cover the page
orchestration. Independent delta re-review approved the remediation: M1–M5 are
closed, with no blocking or material findings.

R2-B7 adds typed, read-only internal foundations for future Home, Planning,
Goal, and FIRE consumers. They delegate to B5 with an explicit authenticated
owner, feature, and `as_of_date`; they preserve provenance and assumption states
without producing effective engine inputs, changing public APIs, or activating
R6 smart-prefill behavior. B8 independently approved the complete R2
foundation. MR1 diagnosed the physical-schema/Alembic-version drift; MR2 makes
runtime imports/startup DDL-inert, makes the configured database URL
authoritative, keeps Alembic as schema authority, and isolates pytest from the
active database. MR3 reconciled active Alembic bookkeeping to migration
`2d6b4f8a9c1e`; the subsequent upgrade was a no-op and preserved schema and
financial data. R2 is closed. R3 is ready but not started, and product
recomposition/smart prefills remain reserved for R6.

R3-A completed and approved the External Context architecture/source audit.
R3-B now provides a locked External Context contract, official BCB/SGS series
registry, accepted ADR-029, and a locked implementation plan. R3-B.1 replaced the
unsafe SQLite `NUMERIC(38,18)` exactness assumption with canonical fixed-scale
text and explicit `Decimal`, preserves `A -> B -> A` knowledge history, and
separates refresh, economic freshness, and acquisition health. Independent
review reported no findings and the user explicitly approved all ten material
decisions on 2026-10-09. R3-C is ready but not started; no R3 implementation
exists from this documentation checkpoint.

## Read in this order

1. [CURRENT_STATE.md](CURRENT_STATE.md) — verified present reality;
2. [MASTER_PLAN.md](MASTER_PLAN.md) — product vision and long-term direction;
3. [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) — active queue and
   dependency gates;
4. [ARCHITECTURE.md](ARCHITECTURE.md) — cross-cutting architecture and product
   information architecture;
5. the concern owner or applicable locked phase contract.

## Canonical owners

| Concern | Owner |
|---|---|
| Product vision / Wealth OS direction | `MASTER_PLAN.md` |
| Current implementation and absences | `CURRENT_STATE.md` |
| Active phase order / dependencies | `IMPLEMENTATION_ROADMAP.md` |
| Cross-cutting architecture / product areas | `ARCHITECTURE.md` |
| Data classes / provenance / source authority | `DATA_AND_SOURCE_OF_TRUTH.md` |
| Frontend / UX principles | `UI_UX_PLAN.md` |
| AI current state and runtime boundary | `AI_AND_LLM.md` |
| Security / privacy / secrets | `SECURITY_AND_GOVERNANCE.md` |
| Infrastructure direction | `INFRASTRUCTURE.md` |
| Validation philosophy | `TESTING_STRATEGY.md` |
| Accepted architectural/product decisions | `DECISION_LOG.md` |
| Historical change evidence | `CHANGELOG.md` |
| External product inspiration | `PRODUCT_REFERENCES.md` |
| R2 Smart Financial Context contract | [SMART_FINANCIAL_CONTEXT_CONTRACT.md](SMART_FINANCIAL_CONTEXT_CONTRACT.md) |
| R2 implementation decomposition | [SMART_FINANCIAL_CONTEXT_IMPLEMENTATION_PLAN.md](SMART_FINANCIAL_CONTEXT_IMPLEMENTATION_PLAN.md) |
| R3 External Context locked contract | [EXTERNAL_CONTEXT_CONTRACT.md](EXTERNAL_CONTEXT_CONTRACT.md) |
| R3 official locked series registry | [EXTERNAL_SERIES_REGISTRY.md](EXTERNAL_SERIES_REGISTRY.md) |
| R3 locked implementation decomposition | [EXTERNAL_CONTEXT_IMPLEMENTATION_PLAN.md](EXTERNAL_CONTEXT_IMPLEMENTATION_PLAN.md) |
| R0 evidence | `WEALTH_OS_REALIGNMENT_AUDIT.md` |
| 10.5-A evidence | `PORTFOLIO_INTELLIGENCE_CONTRACT_AUDIT.md` |

Phase-specific locked contracts remain authoritative inside their explicit
scope, including `PLANNING_UX_CONTRACT.md`, `FIRE_CONTRACT.md`, and accepted
ADRs.

## Conflict precedence

1. accepted ADR or `LOCKED` phase contract;
2. canonical concern owner;
3. `CURRENT_STATE.md` for verified present reality;
4. `MASTER_PLAN.md` for direction;
5. `IMPLEMENTATION_ROADMAP.md` for queue;
6. audit/research evidence;
7. `SUPERSEDED / HISTORICAL` documents.

Audits preserve evidence; they are not permanent duplicate specifications.
Link to owners instead of copying them.

## Status vocabulary

Use `READY / NOT STARTED`, `IN PROGRESS`, `AUDIT COMPLETE`, `CONTRACT LOCKED`,
`IMPLEMENTED / VALIDATED`, `VALIDATED / CLOSED`, `PAUSED`, and
`SUPERSEDED / HISTORICAL` where applicable. Historical records need not be
mechanically rewritten, but they cannot override current owners.

## Product architecture at a glance

Target conceptual areas are Home, Plan, Portfolio, Explore, Income, Monitor,
Market, Copilot, Tools, Profile, Settings, and Data & Governance. R1 does not
change URLs. The current routes remain operational until later implementation
contracts migrate them.

Profile remains the declared-user-context surface. Settings remains the
configuration surface. Planning remains the deterministic engine/tool. FIRE
remains a specialized Planning consumer. Goals remains objective lifecycle.
Portfolio Intelligence remains paused.

## Active phase sequence

```text
R2-B1 through R2-B8 Smart Financial Context implementation
 -> R3 External Context
 -> R4 AI Runtime Foundation
 -> R5 Design / Navigation / System-Light-Dark
 -> R6 Experience Recomposition
 -> R7 Independent Validation
 -> resume 10.5-B
```

Do not begin the next phase merely because its documentation exists. Each phase
requires an explicit task and its own contract/decomposition gate.
