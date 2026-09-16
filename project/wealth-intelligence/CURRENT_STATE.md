# Current Repository State
**Updated:** 2026-09-16 (Phase 10.2 merged; Phase 10.3 planned)

This document reflects the VERIFIED reality of the repository as of the baseline audit.

---

## Module Status Matrix

| Module | Actual State | Verified In | Planned Next Step |
|--------|-------------|------------|-------------------|
| **Pierre / Cashflow** | STABLE | `domains/pierre/`, routers, migrations 001-003, 005b | DO NOT MODIFY |
| **Investments / Wealth** | STABLE | `backend/api/routers/investments.py`, `frontend/src/app/wealth/` | DO NOT MODIFY |
| **Market Data (yfinance)** | COMPLETE | `backend/integrations/yfinance/yfinance_provider.py` | Reuse existing |
| **Governance** | STABLE | `domains/pierre/governance_router.py`, migrations 006, 016 | DO NOT MODIFY |
| **AI Classification DB** | SCHEMA ONLY | Migrations 007, 011 | Activate in Phase 10.8 |
| **Gemini Integration** | EMPTY (0 bytes) | `integrations/gemini/` (3 files, all 0 bytes) | Implement in 10.8 |
| **Goals Backend** | IMPLEMENTED / VALIDATED | `api/routers/goals.py`, `use_cases/goal/`, `persistence/models/goal.py` | Complete |
| **Goals Frontend** | IMPLEMENTED / VALIDATED | `frontend/src/app/goals/`, `/wealth-intelligence` hub | Complete |
| **Financial Health** | **PHASE 10.2 COMPLETED / MERGED; 10.2.10-C VALIDATED** | `backend/domains/health/repository.py`, `domains/health/service.py`, `api/routers/financial_health.py`, `frontend/src/app/wealth-intelligence/health/` | Complete |
| **Planning Engine** | PLANNED / NOT STARTED | No production Planning code | 10.3.0 contract and data audit |
| **Retirement / FI** | NOT STARTED | — | Phase 10.4 |
| **Portfolio Intelligence** | NOT STARTED | — | Phase 10.5 |
| **Rebalancing** | NOT STARTED | — | Phase 10.6 |
| **Watchlist** | NOT STARTED | — | Phase 10.6 |
| **BCB / Macro Data** | NOT STARTED | — | Phase 10.7 |
| **News Integration** | NOT STARTED | — | Phase 10.7 |
| **LLM Provider** | NOT STARTED | — | Phase 10.8 |
| **Ollama** | NOT INSTALLED | — | Phase 10.8 |
| **AI Briefings / Insights** | NOT STARTED | — | Phase 10.9 |
| **Agent Orchestration** | NOT STARTED | — | Phase 10.10 (conditional) |
| **Docker** | NOT STARTED | — | Phase 10.11 |
| **Visual Polish** | NOT STARTED | — | Phase 10.12 |

---

## Database State

- Runtime database `database/fin_analytics.db` is operational and at the current Alembic head.
- All core tables exist and are operational
- **Financial Health ledger audit (read-only, 2026-09-14):** 1,420 transactions; 1,420 `CLASSIFIED`; 0 `PENDING`; 341 `ENTRADA`; 898 `SAIDA`; 181 `IGNORAR`. The current ledger covers every calendar month from `2025-05` through partial `2026-09`, including 16 continuous closed months through `2026-08`. Detailed monthly evidence is recorded in `DATA_AND_SOURCE_OF_TRUTH.md`.
- **RESOLVED (Lote 10.0-A):** The `position_snapshots` schema conflict was investigated and resolved:
  - The live DB uses the CORRECT Alembic schema: `id`, `account_id`, `asset_id`, `reference_date`, `quantity`, `avg_price`, `source_type`, `run_id`, `is_manual`, `current_value`
  - `snapshot_hash` column does NOT exist in the live DB — migration 013 was never applied (DB was bootstrapped via Alembic)
  - 53 rows, all `source_type = MYPROFIT_ATIVOS`
  - `alembic_version` = `f2915371d283` (head) — Alembic is in sync
  - Migration 013 (`snapshot_hash` schema) commented out in `create_db.py` with explanatory note
- **KNOWN (ADR-014):** `alembic check` fails due to FK `accounts.id` not existing (Pierre accounts uses composite PK). Pre-existing condition, no runtime impact.

---

## Backend Facts

- FastAPI 0.103.2 with 10 registered routers
- SQLAlchemy 2.0.21 async ORM
- yfinance 0.2.31 with in-memory TTL cache
- google-generativeai 0.8.6 installed but not called
- **FIXED (Lote 10.0-A):** `requirements.txt` updated with verified missing dependencies:
  - `pydantic-settings==2.14.2` (used in `backend/core/config.py`)
  - `aiosqlite==0.22.1` (used in `backend/database/engine.py`)
  - `python-jose[cryptography]==3.5.0` (used in `backend/infrastructure/security/jwt_service.py`)
  - `httpx==0.28.1` (used in `backend/infrastructure/http/pierre_client.py`)
  - `alembic==1.18.5` (used for migrations)
  - **NOTE:** `passlib` was NOT added — no import found in codebase (audited and confirmed)

---

## Frontend Facts

- Next.js 16.2.6 App Router
- React 19.2.4
- TailwindCSS 4
- Recharts 3.8.1
- TanStack Query 5.101
- Zustand 5.0.14
- Active wealth pages: /wealth, /wealth/patrimonio, /wealth/allocation, /wealth/dividends, /wealth/evolution, /wealth/asset, /wealth/performance, /wealth/positions
- Active Wealth Intelligence pages: /wealth-intelligence, /wealth-intelligence/health, /goals

---

## Known Technical Debt

- **HISTORICAL:** Two Investments asset-detail unit tests fail because their incomplete `MagicMock` session supplies a mock date that is sorted together with timeline strings. This is outside Financial Health and remains unchanged.
- **HISTORICAL:** `alembic check` still raises the ADR-014 `NoReferencedColumnError` for logical FK `position_snapshots.account_id -> accounts.id`; the legacy Pierre `accounts` table has a composite key and no `id` column.
- **GLOBAL / NON-BLOCKING:** Mobile responsiveness remains incomplete across multiple legacy FinAnalytics areas. It requires a transversal UX/polish phase and is not a Financial Health blocker.
- **GLOBAL / NON-BLOCKING:** Repository-wide frontend lint debt and the existing Recharts SSR dimension warning remain outside this microprocess. Health-targeted lint and the production build pass.
- **INFRASTRUCTURE / ACCEPTED:** CORS wildcard, JWT storage in `localStorage`, category-trend N+1 queries, and global `console.error` behavior remain tracked backlog; none blocks Phase 10.2.
- **UX / ACCEPTED:** Minor pagination polish remains backlog alongside the global mobile-responsiveness and Recharts SSR items.

---

## What the System Does NOT Do (verified)

- No real-time market data streaming (15-min cache only)
- No retirement projection calculations
- No Planning-derived sustainable contribution-capacity calculation; deferred to Phase 10.3.
- No investment-capacity calculation; deferred to Planning / Portfolio Intelligence.
- No composite financial-stability metric or score; deferred until a deterministic contract is approved.
- No AI insight generation (empty files)
- No LLM integration of any kind
- No external news integration
- No BCB macro data
- No rebalancing engine
- No watchlist
- No Docker containerization
- No production deployment configuration

---

## Post-Merge Checkpoint

- GitHub PR #2 (`develop` → `main`) merged the approved Goals 10.1 and Financial Health 10.2 work.
- `main`, `develop`, `origin/main`, and `origin/develop` were synchronized at merge commit `b7ce8b8` on 2026-09-16.
- Phase 10.3 has a documented microprocess plan but no production code, schema, migration, endpoint, or UI implementation.
