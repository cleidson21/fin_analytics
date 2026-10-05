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
- Wealth OS 10.R2-A: `CONTRACT LOCKED / IMPLEMENTATION READY`
- Wealth OS 10.R2-B1: `IMPLEMENTED / VALIDATED`
- Wealth OS 10.R2-B2: `IMPLEMENTED / VALIDATED`
- Wealth OS 10.R2-B3: `READY / NOT STARTED`

The realignment is an incremental composition refactor. It preserves validated
financial engines while adding Smart Context, normalized external context, a
provider-aware AI runtime, coherent navigation/design foundations, and composed
product journeys in later phases. R2-A locks the Smart Financial Context
contract. R2-B1 adds only its persistence and fail-closed ownership foundation;
R2-B2 adds the authenticated declared Profile context API. No recurring-income
detector, composition service, or frontend integration exists yet.

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
- there is no Smart Context service, normalized External Context Layer,
  production Advisor/Insights/Copilot, OpenAI/Ollama runtime, working Gemini
  runtime, or AI scheduler;
- the live UI is dark-specific despite light/dark CSS tokens.

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
