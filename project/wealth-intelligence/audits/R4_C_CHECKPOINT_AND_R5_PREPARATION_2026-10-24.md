# R4-C Checkpoint Decision and R5 Preparation

**Date:** 2026-10-24
**Classification:** factual checkpoint reconciliation plus non-normative R5 proposal
**R4-C decision:** `CLOSED / PUSHED`
**R5 decision:** `NOT STARTED / EXPLICIT AUTHORIZATION REQUIRED`

This report is traceability evidence. It does not replace ADR-030,
ADR-024, `PLANNING_UX_CONTRACT.md`, `UI_UX_PLAN.md`, or the active roadmap.
It uses the W2–W4.2 reconciliation as its product baseline and does not repeat
the repository-wide audit.

## 1. Checkpoint decision

R4-C is closed. The implementation checkpoint
`14cb65db1cddd5466523eefdca54c78affb3eca7` is the current `HEAD` and is also
contained by the local `origin/develop` tracking ref. The commit contains the
R4-C audit/telemetry contracts, ports, service, volatile test sinks, focused
tests, and contemporaneous tracking updates.

The exact focused selection was rerun from the current worktree:

```text
.\.venv\Scripts\python.exe -m pytest tests\unit\test_ai_runtime_audit_telemetry.py tests\unit\test_ai_runtime_contracts.py tests\unit\test_ai_runtime_tools.py -q --basetemp=.pytest_tmp\r4c-checkpoint-20261024

77 passed in 1.01s
```

No runtime correction was necessary. The discrepancy was confined to tracking
documents that still described the already published checkpoint as pending.

## 2. R4-C requirement traceability

| Requirement | Evidence | Result |
|---|---|---|
| Typed, immutable, versioned, minimized audit events | `backend/application/ai_runtime/audit.py`; immutability, UTC, schema, and sensitive-field negative tests | Met |
| Pseudonymous user scope and authorization isolation | HMAC scope factory; R4-B server-derived active-principal and wrong-owner tests | Met for the approved internal boundary |
| Read-only, deny-by-default tools | immutable five-tool registry; forged scope, unknown tool, extra argument, budget, timeout, and inactive-principal negative tests | Met |
| Independent audit and optional telemetry | separate ports and emission outcomes; telemetry failure cannot claim or invalidate mandatory audit | Met |
| Fail closed when the required audit guarantee is absent | remote or tool-enabled events require `DURABLE`; volatile sink and sink-failure tests raise safe typed errors | Met inside the R4-C emission boundary |
| No sensitive payload or arbitrary metadata | no prompt, response, financial context, transaction description, tool argument, credential, header, or raw provider-message fields; malicious metadata rejected | Met |
| Exact optional cost and honest missing metrics | Decimal cost, including zero, preserved; unknown provider/model/token/cost remains absent | Met |
| No persistence, database, migration, network, endpoint, provider, or scheduler | in-memory sinks are explicitly `VOLATILE`; no database/network-call test passes | Met by intentional scope |
| Published implementation checkpoint | `HEAD == origin/develop == 14cb65d…` in the local Git evidence | Met |

Independent review remains `0 BLOCKING / 0 MATERIAL` active findings.

## 3. Preserved future activation gates

These items do not reopen R4-C, but they prohibit operational provider or tool
dispatch until separately authorized and implemented:

- `MAT-R4C-01`: R4-F must integrate and test a **pre-execution** guard. The
  existing emitter validates an event at emission time; its existence alone
  does not prove that execution is prevented before dispatch.
- A remote, tool-enabled, or tool-executing path requires a `DURABLE` audit
  guarantee. The in-memory sink is never sufficient evidence.
- `INF-R4C-01`: secret/config ownership, HMAC key rotation, and key-ID
  governance require a separate approved contract.
- Durable sink choice, retention, access, deletion, failure recovery, and use
  or replacement of historical `ai_runs` remain undecided and unauthorized.
- R4-D technical-candidate evidence is not provider activation or production
  certification. R4-E through R4-H retain their own gates.

No policy for these items is invented by this checkpoint reconciliation.

## 4. R5 executable proposal

### 4.1 Proposed scope

R5 is a frontend-only design/navigation/theme increment. It absorbs the
verified W2–W4.2 work as baseline evidence without treating that work as prior
R5/R6 closure. It must not change financial engines, public DTO semantics,
database state, authentication, scenario persistence, Portfolio Intelligence,
or AI runtime behavior.

The formal contract should contain four bounded work packages:

1. **R5-0 — Baseline and route contract**
   - freeze current supported routes and define redirects/deep-link behavior;
   - inventory hard-coded visual values in the shell and shared primitives;
   - record current desktop/tablet/mobile states and known accessibility debt.
2. **R5-1 — Semantic tokens and appearance**
   - define or verify semantic color, typography, spacing, elevation, chart,
     focus, and status tokens;
   - implement System/Light/Dark in the shell and shared primitives;
   - persist only the appearance preference, never financial state.
3. **R5-2 — Navigation and Planning reconciliation**
   - preserve existing route compatibility and browser history;
   - expose ADR-024's three Planning intentions while retaining all five
     deterministic capabilities:
     - `Simular` → `POST /api/v1/planning/projection`;
     - `Objetivo / Quando alcanço?` → `POST /api/v1/planning/target-achievement`;
     - `Objetivo / Quanto aportar?` → `POST /api/v1/planning/required-contribution`;
     - `Objetivo / Meta existente` → `POST /api/v1/planning/goals/{goal_id}/projection`;
     - `Comparar` → `POST /api/v1/planning/scenarios/compare`;
   - keep the inner Objective task in URL/navigation state without placing
     financial values or a persisted scenario in the URL.
4. **R5-3 — Responsive, accessible, localized stabilization**
   - migrate the shell, shared controls, charts, tables, dialogs, and living
     states to semantic tokens;
   - validate pt-BR money/rate/date presentation through existing string-safe
     adapters;
   - validate keyboard use, visible focus, semantics, contrast, reduced motion,
     narrow/wide reflow, and source/freshness visibility.

### 4.2 Acceptance criteria

R5 is accepted only when all of the following are evidenced:

- System, Light, and Dark work from the live shell, including persisted user
  preference and correct system-preference behavior.
- No migrated shared surface depends on hard-coded dark-only values where a
  semantic token is required.
- Existing routes and deep links either remain operational or have explicit,
  tested redirects; Back/Forward and refresh preserve non-financial UI state.
- Planning presents exactly three top-level intentions and maps to the five
  existing endpoints/result contracts without frontend financial calculation.
- No calculation runs merely because a page, tab, theme, or route opens.
- Governed, transient, demonstrative, unavailable, stale, partial, loading,
  and error states remain distinguishable and accessible.
- Desktop, tablet, and mobile reflow without hiding critical facts or relying
  on horizontal compression.
- Keyboard, focus, semantics, contrast, reduced motion, and accessible chart
  alternatives pass the approved component/manual checks.
- Goals, Health, Planning, FIRE, Investments, authentication, ownership,
  Decimal-string payloads, and provenance retain their existing regression
  behavior.
- Vitest/component tests, TypeScript, focused ESLint, production build, focused
  backend contract regressions, and `git diff --check` pass. Browser automation
  or new dependencies require separate authorization.

### 4.3 Explicit exclusions

- R6 product recomposition or a declaration that W2–W4.2 already closed R6;
- new financial metrics, formulas, engines, endpoints, or DTOs;
- scenario/result persistence or financial values in browser storage;
- Portfolio Intelligence 10.5-B;
- Advisor/provider dispatch, durable audit persistence, HMAC operations, or
  any R4-F implementation;
- database migrations, external calls, deployment, or production activation.

## 5. Approval required before R5 starts

The roadmap's main path is sequential, although it explicitly permits R5
token/visual audits to overlap after their inputs stabilize. Starting R5 now
therefore requires an explicit decision with this meaning:

> Authorize the bounded R5 frontend contract above as the next product work,
> while leaving R4-D through R4-H operational activation gates unchanged and
> without treating R4 as a production-complete Advisor runtime.

Approval of that statement authorizes contract finalization and R5
implementation only. It does not authorize R6, Portfolio Intelligence,
provider dispatch, durable audit persistence, downloads, migrations, deploy,
commit, or push.
