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
- Wealth OS 10.R5: `IMPLEMENTED / AUTOMATED GATES PASSED / USER VISUAL ACCEPTANCE APPROVED FOR CURRENT BASELINE / CLOSED`
- Wealth OS 10.R6 general gate: `SATISFIED`
- Wealth OS 10.R6.1: `IMPLEMENTED / AUTOMATED GATES PASSED / USER MANUAL ACCEPTANCE REPORTED / COMMITTED / PUSHED`
- Wealth OS 10.R6.2: `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED`
- Wealth OS 10.R6.3–R6.4: `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED`
- Wealth OS 10.R6.5-A: `CONTRACT APPROVED`
- Wealth OS 10.R6.5-B: `IMPLEMENTED / FOCUSED TESTS PASSED / COMMITTED / PUSHED`
- Wealth OS 10.R6.5-C: `IMPLEMENTED / AUTOMATED GATES PASSED / USER ACCEPTED / PUBLICATION PENDING`
- Wealth Intelligence W2–W4.2: `IMPLEMENTED / ABSORBED INTO CLOSED R5 BASELINE / NOT AN R6 PHASE CLOSURE`

The realignment is an incremental composition refactor. R2 now provides the
validated Smart Financial Context foundation, R3 provides the approved External
Context foundations, and R4-A through R4-C provide internal AI contracts,
read-only tools, and audit/telemetry boundaries without an operational Advisor.
The published baseline contains the W2–W4.2 Wealth Intelligence product
increments and the bounded R5 consolidation. R5 automated gates passed and the
project owner accepted the current visual baseline on 2026-10-27 without
claiming an exhaustive browser, viewport, or state matrix. R5 is closed. The
general R6 sequencing gate is satisfied, but each later increment still needs
an explicit contract and authorization.

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
  result sharing, and R5 themes are published and user-accepted as the current
  baseline; broader manual matrix coverage remains future validation work;
- R6.1–R6.4 are published at checkpoint
  `40a23566b3b068e26cb8bd3ae94bc7ed060ec4b0`. Their context, progress,
  count-only overview, and required-contribution batch preview are foundations
  for the limited-budget multi-Goal journey. R6.5-A closes its approved
  [budget contract](project/wealth-intelligence/GOAL_BUDGET_PREVIEW_CONTRACT.md);
  its backend now compares equal-total nominal A/B allocations through certified
  per-Goal comparisons, with exact budget/excess accounting and no writes.
  R6.5-B is published at `b59e2af63fbc6a093bafa4a50a375571a1877ab6`.
  The R6.5-C interface is implemented and user accepted under Objetivo → Meta
  cadastrada → Distribuir orçamento. Journey A is functionally accepted;
  publication requires separate authorization.

The single journey-oriented queue and the R6.5-C acceptance record live in
[IMPLEMENTATION_ROADMAP.md](project/wealth-intelligence/IMPLEMENTATION_ROADMAP.md).
Local/online AI development is explicitly included, without activating providers
or promoting laboratory evidence to real-data approval.

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

### Windows runtime (default)

The validated Python 3.14 runtime lives outside the repository:

```powershell
$Py = Join-Path $env:LOCALAPPDATA 'FinAnalytics\runtimes\sec-dep-c-py314-0803511\Scripts\python.exe'
```

Backend, from the repository root (127.0.0.1:8080, no reload):

```powershell
& $Py -m uvicorn backend.main:app --host 127.0.0.1 --port 8080
```

Or use the launcher, which resolves the runtime itself, refuses to start if
port 8080 is taken, and also starts the frontend:

```powershell
.\scripts\start_dev.ps1
```

Set `FINANALYTICS_PYTHON` to override the interpreter explicitly. The script
never falls back to `.venv`. Add `--reload` manually to the command above only
when you need it.

Check the port (read-only):

```powershell
Get-NetTCPConnection -LocalPort 8080 -State Listen | Select-Object LocalAddress, LocalPort, OwningProcess
```

Stop a backend you started manually: press `Ctrl+C` in its terminal, or, after
confirming the PID belongs to it, `Stop-Process -Id <PID>`.

Rollback to the legacy environment (temporary, explicit):

```powershell
$env:FINANALYTICS_PYTHON = (Resolve-Path .\.venv\Scripts\python.exe).Path
.\scripts\start_dev.ps1
```

The legacy `.venv` is no longer the recommended default: it predates the
dependency remediation (SEC-DEP) and does not match the validated runtime.
It is kept only for rollback.

In Antigravity, run `Python: Select Interpreter` and pick (or enter manually)
the runtime `python.exe` above. This is a local `.vscode/` preference, not
versioned, and does not change commands that name the interpreter explicitly.

Frontend:

```powershell
cd frontend
npm.cmd run dev
```

## Validate

Backend tests run from the repository root with the approved runtime:

```powershell
& $Py -m pytest
```

Frontend validation commands are defined in `frontend/package.json` and in the
applicable phase contract.

## Core rule

**Governed data exposes facts. Deterministic engines calculate. Frontend
presents. AI interprets and orchestrates approved capabilities.**

Financial values retain provenance and exact Decimal/string authority. External
data never silently replaces internal facts, assumptions stay explicit, and
secrets remain server-side.
