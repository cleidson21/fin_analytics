# FINANALYTICS

FINANALYTICS is a private, local-first **personal Wealth OS**. It combines
governed cashflow and investment data with deterministic Goals, Financial
Health, Planning, and FIRE capabilities. Future context and AI layers must
consume those capabilities without replacing their financial authority.

## Current milestone

- Goals 10.1: `IMPLEMENTED / VALIDATED`
- Financial Health 10.2: `IMPLEMENTED / VALIDATED`
- Planning 10.3: `VALIDATED / CLOSED`
- FIRE 10.4: `VALIDATED / CLOSED`
- Portfolio Intelligence 10.5-A: `AUDIT COMPLETE / USER DECISIONS RESOLVED`
- Portfolio Intelligence 10.5-B: `PAUSED / PENDING WEALTH OS REALIGNMENT`
- Wealth OS 10.R0: `AUDIT COMPLETE`
- Wealth OS 10.R1: `ARCHITECTURE / DOCUMENTATION LOCKED`
- Wealth OS 10.R2: `IMPLEMENTED / VALIDATED / CLOSED`
- Wealth OS 10.R3: `R3-I INDEPENDENTLY APPROVED / DOCUMENTATION RECONCILED`
- Wealth OS 10.R4-A/B: `CLOSED / PUSHED`
- Wealth OS 10.R4-C: `CLOSED / PUSHED`
- Wealth OS 10.R5: `IMPLEMENTED / AUTOMATED GATES PASSED / USER VISUAL ACCEPTANCE PENDING`
- Wealth Intelligence W2–W4.2: `IMPLEMENTED / TESTED IN CURRENT WORKTREE / ABSORBED INTO R5 / NOT AN R6 PHASE CLOSURE`

The realignment is an incremental composition refactor. R2 now provides the
validated Smart Financial Context foundation, R3 provides the approved External
Context foundations, and R4-A through R4-C provide internal AI contracts,
read-only tools, and audit/telemetry boundaries without an operational Advisor.
The current worktree also contains the W2–W4.2 Wealth Intelligence product
increments and the bounded R5 consolidation. R5 automated gates passed, but its
desktop/tablet/mobile visual acceptance remains assigned to the user. These
local increments are not an implied start or closure of canonical phase R6.

## What exists today

- FastAPI backend with authenticated Goals, Financial Health, Planning, FIRE,
  Investments, dashboard, transaction, account, and governance capabilities;
- Next.js frontend for cashflow, Investments, Governance, Goals, Health,
  Planning, FIRE, Profile, Settings, and Accounts;
- Pierre Finance and MyProfit ingestion/governance paths;
- yfinance market-data integration;
- SQLite persistence and deterministic Decimal-first Planning/FIRE boundaries.

Important current limitations:

- the existing Investments UI is not a certified Portfolio Intelligence or
  portfolio-performance engine;
- Profile is partly browser-local and Settings is mostly placeholder behavior;
- Smart Context and External Context foundations exist, but there is no
  production Advisor/Insights/Copilot, operational model adapter, hybrid router,
  AI endpoint, or AI scheduler;
- the W2–W4.2 Wealth Home, navigation, Planning/FIRE experience, transient
  result sharing, and R5 themes exist only in the current worktree and await
  final user visual acceptance before the Git checkpoint;
- R6 has not started, and R5 completion does not authorize it.

See the verified current-state owner for exact detail.

## Canonical documentation

Start at [Wealth Intelligence documentation](project/wealth-intelligence/README.md).

| Concern | Canonical owner |
|---|---|
| Product vision | [MASTER_PLAN.md](project/wealth-intelligence/MASTER_PLAN.md) |
| Current repository reality | [CURRENT_STATE.md](project/wealth-intelligence/CURRENT_STATE.md) |
| Active queue | [IMPLEMENTATION_ROADMAP.md](project/wealth-intelligence/IMPLEMENTATION_ROADMAP.md) |
| Architecture and product map | [ARCHITECTURE.md](project/wealth-intelligence/ARCHITECTURE.md) |
| Data semantics and source authority | [DATA_AND_SOURCE_OF_TRUTH.md](project/wealth-intelligence/DATA_AND_SOURCE_OF_TRUTH.md) |
| Frontend/UX direction | [UI_UX_PLAN.md](project/wealth-intelligence/UI_UX_PLAN.md) |
| AI boundary | [AI_AND_LLM.md](project/wealth-intelligence/AI_AND_LLM.md) |
| Accepted decisions | [DECISION_LOG.md](project/wealth-intelligence/DECISION_LOG.md) |
| External product inspiration | [PRODUCT_REFERENCES.md](project/wealth-intelligence/PRODUCT_REFERENCES.md) |

The root `ESPECIFICACAO_PRODUTO_METAS.md` and
`project/wealth-intelligence/audits/FINAL_PRODUCT_DEFINITION.md` are historical
inputs, not current vision or roadmap authorities.

## Run locally

Backend, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8080
```

Frontend:

```powershell
cd frontend
npm.cmd run dev
```

## Validate

Backend tests run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Frontend validation commands are defined in `frontend/package.json` and in the
applicable phase contract.

## Core rule

**Governed data exposes facts. Deterministic engines calculate. Frontend
presents. AI interprets and orchestrates approved capabilities.**

Financial values retain provenance and exact Decimal/string authority. External
data never silently replaces internal facts, assumptions stay explicit, and
secrets remain server-side.
