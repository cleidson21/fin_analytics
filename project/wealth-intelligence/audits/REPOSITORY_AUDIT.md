# Repository Audit — Lote 10.0
**Status:** VERIFIED
**Date:** 2026-09-08
**Baseline:** v3.1.0-investments

---

## 1. Backend Structure [VERIFIED]

### Stack
| Component | Library | Version |
|-----------|---------|---------|
| Web Framework | FastAPI | 0.103.2 |
| ASGI | Uvicorn | 0.23.2 |
| ORM | SQLAlchemy | 2.0.21 (async) |
| Validation | Pydantic | 2.4.2 |
| Data | Pandas | 2.1.1 |
| Market Data | yfinance | 0.2.31 |
| Scheduler | APScheduler | 3.11.3 |
| HTTP | requests | 2.34.2 |
| AI SDK | google-generativeai | 0.8.6 |

> **P2 FINDING:** `requirements.txt` is incomplete. `pydantic-settings`, `aiosqlite`, `python-jose`, `passlib` are used but not listed.

### Routers Registered [VERIFIED — from main.py]
| Router | Prefix | Sprint |
|--------|--------|--------|
| auth_router | /api/v1 | Core |
| pierre_router | /api/v1 | Sprint 1 |
| read_router | /api/v1 | Sprint 2 |
| installments_router | /api/v1/pierre | Sprint 3 |
| governance_router | /api/v1 | Sprint 2.8 |
| dashboard_router | /api/v1/dashboard | Dashboard |
| api_governance_router | /api/v1 | Governance |
| investments_router | /api/v1/investments | Investments |
| goals_router | /api/v1/goals | Lote 10.1 stub |

---

## 2. Database [VERIFIED]

### Engine: SQLite + WAL, file: database/fin_analytics.db (4.3 MB)
### Migrations: 17 versioned SQL scripts in database/migrations/

| # | File | Key Tables |
|---|------|------------|
| 001 | core_identity | users, institutions, accounts |
| 002 | cashflow_ledger | categories, merchants, transactions, transfers |
| 003 | credit_card | credit card structures |
| 004 | investments | assets, broker_notes, trades, corporate_actions, dividends |
| 005a | market_data | market price snapshots |
| 005b | open_finance | Pierre/Open Finance models |
| 006 | governance | import_runs, import_artifacts, audit_logs, data_corrections |
| 007 | ai_classification | classification_rules, learning_examples, ai_prompts, ai_runs, classification_feedback |
| 008 | analytics | asset_positions, asset_valuations, portfolio_snapshots (TWR/MWR/Sharpe), benchmark_snapshots, cashflow_summaries |
| 009 | fixed_income_events | fixed income events |
| 010 | ledger_events | ledger event log |
| 011 | ai_prompt_versioning | ai_prompt_versions (immutable), extends ai_runs |
| 012 | freeze_fixes | schema stabilization |
| 013 | position_snapshots | B3-style position_snapshots (snapshot_hash UNIQUE) |
| 014 | import_logs | import log extensions |
| 015 | macro_indicators | macro indicator stubs (349 bytes) |
| 016 | governance_sprint28 | GovernanceAuditLog |

### Key ORM Models (SQLAlchemy, backend/infrastructure/persistence/models/)
- **AssetModel** (assets): ticker (UNIQUE), name, asset_class, sector, currency, yfinance_ticker, is_active
- **PositionSnapshotModel** (position_snapshots): account_id+asset_id+reference_date (UNIQUE), quantity(18,8), avg_price(18,6), current_value, source_type, is_manual
- **PortfolioSnapshotModel** (portfolio_snapshots): account_id+reference_month (PK), patrimonio, pct_mensal, pct_acumulada, compras, vendas, proventos, IBOV/CDI/IPCA/IFIX/SP/IDIV benchmarks
- **IncomeEventModel** (income_events): account_id, asset_id, event_type, payment_date, ex_date, quantity, value_per_unit, gross_amount, yoc, dy
- **GoalModel** (goals): user_id, name, description, goal_type, target_amount, target_date, status

---

## 3. CRITICAL DISCOVERY — Dual position_snapshots Schema [BLOCKER]

Two incompatible schemas share the table name `position_snapshots`:

| Source | Primary Key | Purpose |
|--------|-------------|---------|
| Migration 013 | snapshot_hash (UNIQUE) | B3 Área do Investidor raw import |
| PositionSnapshotModel (ORM) | account_id+asset_id+reference_date | MyProfit-governed positions |

The ORM `Base.metadata.create_all()` on startup may silently conflict. Must verify live DB before any new migrations.

---

## 4. AI Infrastructure [VERIFIED — EMPTY]

### What EXISTS:
- google-generativeai==0.8.6 in requirements
- GEMINI_API_KEY + OPENAI_API_KEY in config
- Database tables: ai_prompts, ai_prompt_versions, ai_runs, classification_rules, learning_examples, classification_feedback

### What DOES NOT EXIST:
- `integrations/gemini/classifier.py` — **0 bytes**
- `integrations/gemini/models.py` — **0 bytes**
- `integrations/gemini/prompts.py` — **0 bytes**
- No LLMProvider abstraction
- No AI service implementation
- No insight generation
- No scheduled AI tasks
- No Ollama integration

**CONCLUSION:** No AI runs in production. Database scaffolding only.

---

## 5. Market Data Infrastructure [VERIFIED — COMPLETE]

### YFinanceProvider (`backend/integrations/yfinance/yfinance_provider.py`)
Methods: get_quote, get_history, get_indicators

**Ticker normalization:**
| Asset Class | Yahoo Symbol |
|-------------|-------------|
| STOCK, FII | {ticker}.SA |
| BDR (with digit) | {ticker}.SA (B3) |
| BDR (no digit) | {ticker} (US) |
| ETF_GLOBAL | {ticker} (US) |
| CRYPTO | {ticker}-USD |
| FIXED_INCOME | None (unsupported) |

**FX:** USD→BRL via BRL=X with 1-hour in-memory cache, fallback 5.0

**Cache (MarketDataService):**
| Type | TTL Success | TTL Failure |
|------|------------|-------------|
| Quote | 15 min | 2 min |
| History | 60 min | 5 min |
| Indicators | 24 hours | 5 min |

**Cache type:** In-memory dict with threading.Lock — not persistent, lost on restart

**MarketDataProvider Protocol** — correct extension point for future providers

**Limitations:** No retry, no circuit breaker, no persistent cache, FIXED_INCOME unsupported, yf.info unreliable for many BR assets

---

## 6. Frontend [VERIFIED]

### Stack: Next.js 16.2.6 + React 19 + TypeScript 5 + TailwindCSS 4 + Recharts + TanStack Query 5 + Zustand 5 + Shadcn/Radix

### Active Pages:
- Controle Financeiro: /, /transactions, /categories, /cashflow, /installments
- Investimentos: /wealth, /wealth/patrimonio, /wealth/allocation, /wealth/dividends, /wealth/evolution, /wealth/asset, /wealth/performance, /wealth/positions
- Governança: /governance, /governance/classify, /governance/data, /governance/imports, /governance/audit
- Settings: /settings, /accounts, /profile
- /login

### Stub Pages (no real UI):
- /goals — 85-line stub with test-create button only

### Design: dark glassmorphism, zinc-950 bg, emerald accent, Recharts dark charts, no Google Fonts, no light mode

---

## 7. Goals Domain Gaps

| Field | Exists | Required for WI |
|-------|--------|----------------|
| id, user_id, name, goal_type, target_amount, target_date, status | YES | YES |
| current_amount | NO | Required |
| priority | NO | Required |
| monthly_contribution | NO | Required |
| linked_account_id | NO | Optional |
| assumptions_json | NO | Required for projections |
| progress_pct (calculated) | NO | Required for UI |
| projected_completion | NO | Required for WI |

GoalType enum: EMERGENCY_RESERVE, RETIREMENT, TRAVEL, PURCHASE, CUSTOM
(Missing: WEALTH_TARGET, INVESTMENT_TARGET, DIVIDEND_INCOME, FINANCIAL_INDEPENDENCE)

---

## 8. Summary Table

| Area | Status | Notes |
|------|--------|-------|
| Backend FastAPI | STABLE | 9 routers, clean DI |
| Database | STABLE | 17 migrations applied |
| Pierre / Open Finance | COMPLETE | Full implementation |
| MyProfit integration | COMPLETE | CSV import + governance |
| yfinance market data | COMPLETE | Provider protocol + cache |
| Investments Wealth | STABLE | DO NOT MODIFY |
| Goals backend | STUB | CRUD only, missing fields |
| Goals frontend | STUB | No real UI |
| AI infrastructure | EMPTY | DB schema only, no code |
| LLM provider abstraction | NOT EXIST | Create in 10.8 |
| Retirement engine | NOT EXIST | Phase 10.4 |
| Simulation engine | NOT EXIST | Phase 10.5 |
| Watchlist | NOT EXIST | Phase 10.6 |
| News integration | NOT EXIST | Phase 10.7 |
| Docker | NOT EXIST | Phase 10.11 |
| position_snapshots conflict | BLOCKER | Must resolve before migrations |
