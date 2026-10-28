# FINANALYTICS — Wealth OS Documentation

**Status:** `10.R5 IMPLEMENTED / AUTOMATED GATES PASSED / USER VISUAL ACCEPTANCE APPROVED FOR CURRENT BASELINE / CLOSED`

**R5 technical checkpoint:** `COMMITTED / PUSHED` at
`1fae590fb316b4f9d9584aad23cdde4fe8f3af9b`

**Sequencing gate:** `R6 GENERAL GATE SATISFIED / R6.1-R6.3 COMMITTED / PUSHED / R6.4 BATCH CONTRIBUTION PREVIEW IMPLEMENTED — FOCUSED TESTS PASSED — CHECKPOINT PENDING / R6.5+ NOT AUTHORIZED`

This directory is the canonical architectural and product documentation area
for FINANALYTICS Wealth Intelligence. FINANALYTICS is evolving into a personal
Wealth OS through incremental composition of its validated financial core.

## Current state

Goals, Financial Health, Planning, and FIRE are validated. R2 is closed; R3-I is
independently approved and documentation-reconciled; R4-A and R4-B are closed;
R4-C is closed and pushed at checkpoint
`14cb65db1cddd5466523eefdca54c78affb3eca7`. The 10.5-A
Portfolio Intelligence audit and its user decisions remain valid. Phase 10.5-B
is paused until the Wealth OS realignment closes at R7.

The published R5 checkpoint contains the W2–W4.2 Wealth Intelligence increments
and the bounded R5 consolidation: an authenticated Wealth Home read model, governed
Health/Goals/investment-wealth cards, month-aware navigation, five deterministic
Planning capabilities organized under the three ADR-024 intentions, three FIRE
modes, user-selected transient results held only in memory, semantic tokens, and
Dark/Light/System themes. Automated R5 gates passed; desktop/tablet/mobile
visual acceptance was explicitly approved by the project owner on 2026-10-27
for the current baseline. This approval does not claim an exhaustive browser,
viewport, state, or manual-accessibility matrix. With the automated gates and
published technical checkpoint already satisfied, R5 is closed and the general
R6 sequencing gate is satisfied. The earlier ADR-027 exception remains part of
the historical record. R6.1 Goals → Planning is implemented, accepted for the
scope tested, and committed/pushed at
`1b0a1c6fa538ad69c415c29f77c8f91b68f4dd0b`. The project owner subsequently
authorized the bounded R6.2 Goal Progress read model, published at
`7828f64a2d8d0a25605bcb2c459775e176f99292`. The explicitly authorized R6.3
Goal Monitoring overview is published at
`1f743b297449d17064d68376891edab88432e1d2`. R6.4 now implements the bounded,
authenticated joint Goal contribution preview governed by
`GOAL_BATCH_CONTRIBUTION_PREVIEW_CONTRACT.md`. It reuses the certified Required
Contribution solver for each owned Goal, performs one batch Goal read, and
persists nothing. Focused tests pass, but the R6.4 checkpoint is not staged,
committed, pushed, or deployed. R6.5+, R7, Advisor, and Portfolio Intelligence
remain unauthorized.

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
financial data. R2 is closed. R3-D through R3-F1 and R3-I have progressed as
recorded in `CURRENT_STATE.md`; product recomposition/smart prefills remain
governed by R6.

R3-A completed and approved the External Context architecture/source audit.
R3-B now provides a locked External Context contract, official BCB/SGS series
registry, accepted ADR-029, and a locked implementation plan. R3-B.1 replaced the
unsafe SQLite `NUMERIC(38,18)` exactness assumption with canonical fixed-scale
text and explicit `Decimal`, preserves `A -> B -> A` knowledge history, and
separates refresh, economic freshness, and acquisition health. Independent
review reported no findings and the user explicitly approved all ten material
decisions on 2026-10-09. R3-B.2 subsequently locked Content Fingerprint V1.
R3-C now implements and validates the pure immutable domain, five-series
executable registry, strict Decimal/civil-period normalization, economic
identity, structured errors, and fingerprint boundary without network,
persistence, API, frontend, or engine changes. Independent implementation
review approved R3-C with 0 blocking, 0 material, 0 minor, and 2 informational
findings. Its historical status is
`IMPLEMENTED / VALIDATED / INDEPENDENTLY APPROVED / CLOSED`; later R3 status is
owned by `CURRENT_STATE.md` and `IMPLEMENTATION_ROADMAP.md`.

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
| R6.1 Goals → Planning microcontract | [PLANNING_GOAL_CONTEXT_READ_MODEL_PROPOSAL.md](PLANNING_GOAL_CONTEXT_READ_MODEL_PROPOSAL.md) |
| R6.2 Goal Progress microcontract | [GOAL_PROGRESS_READ_MODEL_CONTRACT.md](GOAL_PROGRESS_READ_MODEL_CONTRACT.md) |
| R6.3 Goal Monitoring microcontract | [GOAL_MONITORING_OVERVIEW_READ_MODEL_CONTRACT.md](GOAL_MONITORING_OVERVIEW_READ_MODEL_CONTRACT.md) |
| R6.4 Goal Batch Contribution microcontract | [GOAL_BATCH_CONTRIBUTION_PREVIEW_CONTRACT.md](GOAL_BATCH_CONTRIBUTION_PREVIEW_CONTRACT.md) |
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
requires an explicit task and its own contract/decomposition gate. R6.1 Goals →
Planning began under the historical ADR-027 sequencing exception and is now
published. R6.2 through R6.4 were later defined and explicitly authorized by
their bounded microcontracts; no later increment inherits those authorizations.
