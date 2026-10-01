# FINANALYTICS — Wealth Intelligence
**Repository:** fin_analytics_v2
**Version:** v3.1.0-investments (baseline audited)
**Documentation Status:** Phase 10.2 completed/merged; Phase 10.3 and post-10.3 UX validated/closed; Phase 10.4 FIRE validated/closed; Phase 10.5 ready/not started

---

## What is This?

FINANALYTICS is a personal financial intelligence platform. It integrates your bank transactions (via Pierre Finance / Open Finance), investment data (via MyProfit and B3), and real-time market data (via yfinance) into a single coherent view — and progressively adds AI-powered intelligence to help you understand and plan your financial future.

This is NOT a public product. This is a personal-use, self-hosted application.

---

## What Exists Today (v3.1.0)

| Module | Status | Description |
|--------|--------|-------------|
| Controle Financeiro | ✅ STABLE | Cashflow dashboard, transaction classification, Pierre sync |
| Investimentos | ✅ STABLE | Portfolio dashboard, dividends, allocation, performance (from MyProfit) |
| Governança | ✅ STABLE | Import pipeline, audit trail, AI classification DB scaffold |
| Metas | ✅ IMPLEMENTED / VALIDATED | CRUD, progress deterministic and functional UI |
| Financial Health | ✅ COMPLETE / MERGED | 10.2.0–10.2.10-C validated; independent release review passed; PR #2 merged into `main` |
| Wealth Intelligence | 🔵 IN PROGRESS | Planning 10.3, post-10.3 UX, and FIRE 10.4 are validated/closed; Portfolio Intelligence 10.5 is ready/not started |

---

## Documentation

All architectural documentation lives in `project/wealth-intelligence/`.

| Document | Purpose |
|----------|---------|
| README.md | This file |
| MASTER_PLAN.md | Vision, roadmap, phase status |
| CURRENT_STATE.md | Verified reality of the repository |
| ARCHITECTURE.md | Current and target architecture |
| AI_AND_LLM.md | LLM provider design, Ollama, prompt safety |
| DATA_AND_SOURCE_OF_TRUTH.md | Source of truth matrix, data authority rules |
| DECISION_LOG.md | Architecture Decision Records (ADRs) |
| IMPLEMENTATION_ROADMAP.md | Phase contracts and detailed scope |
| UI_UX_PLAN.md | Page designs and design system |
| PLANNING_UX_CONTRACT.md | Locked post-10.3 Planning simplicity, pt-BR input/output, comparison, and implementation contract |
| FIRE_CONTRACT_AUDIT.md | Preserved Phase 10.4-A source-of-truth and contract analysis |
| FIRE_CONTRACT.md | Locked Phase 10.4 FIRE MVP implementation contract under ADR-025 |
| FIRE_IMPLEMENTATION_PLAN.md | Phase 10.4-C execution decomposition and D1–D7 gates |
| SECURITY_AND_GOVERNANCE.md | Security, AI governance, prompt injection defense |
| INFRASTRUCTURE.md | Docker, Ollama, deployment strategy |
| TESTING_STRATEGY.md | Testing requirements per phase |
| CHANGELOG.md | Change history |
| audits/REPOSITORY_AUDIT.md | Full verified repository audit (Lote 10.0) |
| audits/EXTERNAL_DATA_ECOSYSTEM.md | External data source research and decisions |
| audits/ENV_VARIABLE_INVENTORY.md | Environment variable inventory |
| audits/DEPENDENCY_ROADMAP.md | Dependency installation plan per phase |
| audits/FINAL_PRODUCT_DEFINITION.md | Product vision and user experience narrative |

The repository-root `ESPECIFICACAO_PRODUTO_METAS.md` is a high-level product-vision and acceptance-gap input. It preserves desired outcomes but is not an executable micro-phase contract. Approved implementation contracts remain in this canonical directory, especially `DECISION_LOG.md` and `IMPLEMENTATION_ROADMAP.md`.

---

## Architecture Summary

**Backend:** FastAPI + SQLAlchemy (async) + SQLite + yfinance + Pierre API + MyProfit CSV
**Frontend:** Next.js 16 + React 19 + TypeScript + TailwindCSS 4 + Recharts + TanStack Query + Zustand
**AI (future):** Ollama (local, native on host) + Gemini (cloud fallback) + structured output via Pydantic
**Data:** Immutable transaction ledger + append-only corrections + governed investment imports + in-memory market cache

---

## Core Principle

**AI IS READ-ONLY WITH RESPECT TO FINANCIAL TRUTH.**

All financial calculations are deterministic (backend). The LLM interprets and explains — it never calculates, stores financial data, or overrides user-governed information.

---

## Getting Started (Development)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

**Note:** Existing investments/wealth module is stable. Do NOT modify it without explicit phase scope.

---

## Phase Status

See [MASTER_PLAN.md](MASTER_PLAN.md) for the full roadmap.

| Phase | Name | Status |
|-------|------|--------|
| 10.0 | Architecture & Product Design | ✅ COMPLETE |
| 10.1 | Goal Domain Foundation | ✅ IMPLEMENTED / VALIDATED |
| 10.2 | Financial Health Intelligence | ✅ COMPLETED / MERGED — 10.2.10-C VALIDATED |
| 10.3 | Planning & Projection | ✅ VALIDATED / CLOSED; 10.3.7-A DEFERRED; 10.3.8 AUTOMATED VALIDATION PASSED / Swagger smoke DEFERRED BY USER; 10.3.9–10.3.10 VALIDATED; 10.3.10A CONTRACT LOCKED; 10.3.10B VALIDATED / COMPLETE; 10.3.11–10.3.12 VALIDATED; ADR-024 post-closure UX cycle VALIDATED / CLOSED (UX-B1–UX-B7) |
| 10.4 | Retirement & Financial Independence (FIRE) | ✅ VALIDATED / CLOSED — A/B/C complete; D1–D5 implemented/validated; D6 validated/stabilized; D7 validated/closed |
| 10.5 | Portfolio Intelligence | 🔲 READY / NOT STARTED — BOUNDARY APPROVED |
| 10.6 | Rebalancing & Watchlist | 🔲 NOT STARTED |
| 10.7 | External Market Intelligence | 🔲 NOT STARTED |
| 10.8 | LLM Provider Foundation | 🔲 NOT STARTED |
| 10.9 | Wealth AI Briefing | 🔲 NOT STARTED |
| 10.10 | Advanced Orchestration (conditional) | 🔲 NOT STARTED |
| 10.11 | Docker & Operations | 🔲 NOT STARTED |
| 10.12 | Global UX Polish | 🔲 NOT STARTED |
