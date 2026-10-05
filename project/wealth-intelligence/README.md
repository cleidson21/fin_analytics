# FINANALYTICS — Wealth OS Documentation

**Status:** `10.R2 IMPLEMENTATION IN PROGRESS — B1/B2 VALIDATED`

**Next:** `10.R2-B3 — RECURRING INCOME EVIDENCE ENGINE — READY / NOT STARTED`

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
null clearing, safe ownership failure, and purpose-limited provenance. Income
detection, decisions API, composition, and frontend work remain unstarted.

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
