# Architecture — FINANALYTICS Wealth Intelligence
**Status:** PROPOSED (based on VERIFIED audit of v3.1.0-investments)
**Date:** 2026-09-08

---

## 1. Current Architecture [VERIFIED]

```
Browser (Next.js 16 App Router)
    ↓ HTTP/JSON
FastAPI Backend (Uvicorn, async)
    ↓
SQLite Database (WAL mode, aiosqlite)
    ↓                ↓
Pierre Finance API   MyProfit CSVs
(Open Finance)       (Investment data)

+ yfinance (market data, in-memory cache)
+ google-generativeai SDK (installed, not used yet)
```

### Key Architectural Characteristics [VERIFIED]
- **Clean Architecture layers:** domain → application → infrastructure
- **DI via Composition Root** (`core/container.py`, 211 lines)
- **Dual session strategy:** async SQLAlchemy for investments/auth + sync `SessionLocal` for Pierre/dashboard queries
- **Immutable transaction ledger** — no UPDATE/DELETE on transactions
- **Append-only corrections** — data_corrections table
- **Provider Protocol abstraction** — MarketDataProvider (already exists)
- **Goal CRUD** — minimal, no calculation engine

---

## 2. Target Architecture [PROPOSED] — Wealth Intelligence

```
Browser (Next.js)
    ↓
FastAPI Backend
    ├── Existing Routers (DO NOT MODIFY)
    │   ├── /investments — Wealth dashboard
    │   ├── /dashboard — Cashflow KPIs
    │   └── /governance — Classification
    │
    └── NEW Wealth Intelligence Routers (future phases)
        ├── /goals — enriched goal engine
        ├── /planning — retirement + simulation
        ├── /portfolio-intelligence — attribution + rebalancing
        ├── /market-radar — signals + watchlist
        └── /wealth-ai — briefings + insights
            ↓
        LLMProvider (abstraction)
            ├── OllamaProvider (local, phase 10.8)
            ├── GeminiProvider (cloud, phase 10.8)
            └── OpenAIProvider (cloud, phase 10.8)

Data Pipeline:
USER DATA
  ↓ (Pierre/MyProfit import — existing)
CERTIFIED READ MODELS (existing DB tables)
  ↓
DETERMINISTIC ANALYTICAL SERVICES (new — phases 10.3, 10.4, 10.5)
  ↓
WEALTH CONTEXT BUILDER (new — phase 10.9)
  ├── portfolio snapshot
  ├── goal progress
  ├── cashflow summary
  ├── market data enrichment (existing yfinance)
  ├── external news (future phase 10.7)
  └── macro indicators (future phase 10.7)
  ↓
LLM (Ollama local / Gemini cloud)
  ↓
STRUCTURED OUTPUT (Pydantic validation)
  ↓
VALIDATION LAYER (reject if schema invalid)
  ↓
READ-ONLY INSIGHTS (ai_insights table — future)
  ↓
FRONTEND
```

---

## 3. Data Pipeline — Layer Definitions [PROPOSED]

### Layer 1: User Data (existing)
- Pierre Finance transactions (imported via API)
- MyProfit investment data (imported via CSV)
- Manual corrections (governance)
- Goal definitions (user-created)
- **Synchronous or async import triggers**

### Layer 2: Certified Read Models (existing DB)
- transactions, categories, accounts
- position_snapshots, portfolio_snapshots, income_events, assets
- classification_rules, data_corrections
- **Source of truth for all financial calculations**

### Layer 3: Deterministic Analytical Services (NEW — phases 10.3+)
- GoalCalculationService — progress, projections, required contribution
- RetirementProjectionService — compound interest, scenarios, gap analysis
- SimulationEngine — what-if scenarios
- PortfolioAttributionService — winners/losers, sector exposure, contribution
- RebalancingEngine — target vs current allocation
- ExpenseIntelligenceService — rolling averages, anomaly detection, savings rate
- **All calculations are deterministic — same inputs always produce same outputs**
- **LLM does NOT participate in these calculations**

### Layer 4: External Market Data (existing yfinance + future BCB/news)
- yfinance: quotes, history, fundamentals (existing, 15-min cache)
- BCB/SGS: CDI, SELIC, IPCA (future, phase 10.7)
- News: Google News RSS or similar (future, phase 10.7)
- Analyst consensus: yfinance .info where available (future)
- **All external data is timestamped and labeled as external**
- **No external data is treated as financial truth**

### Layer 5: Wealth Context Builder (NEW — phase 10.9)
- Aggregates output from Layers 2, 3, 4
- Builds structured context object for LLM consumption
- Sanitizes external content (prevents prompt injection)
- Stamps data timestamps and provenance
- Limits context size to LLM constraints
- **Stateless — context built fresh per insight request**

### Layer 6: LLM Provider (NEW — phase 10.8)
- LLMProvider abstraction (see AI_AND_LLM.md)
- Receives structured context (not raw financial data)
- Produces structured output (InsightResponse Pydantic model)
- **Sync for simple requests, async for complex briefings**

### Layer 7: Validation (NEW — phase 10.8)
- Validates LLM output against expected schema
- Rejects or flags malformed responses
- Strips any numerical claims that cannot be verified
- Ensures all cited sources exist in the context

### Layer 8: Read-Only Insights (NEW — phases 10.9+)
- Stored in `ai_insights` table (future migration)
- Immutable once stored
- Linked to the context version that generated them
- **NEVER modified by subsequent LLM calls**

### Synchronous vs Asynchronous
| Operation | Mode | Reason |
|-----------|------|--------|
| Portfolio KPIs | Sync (on demand) | Fast, from DB |
| Goal progress | Sync (on demand) | Simple calculation |
| Retirement projection | Sync (on demand) | Deterministic math |
| Simulation scenarios | Sync (on demand) | Math-only |
| Market quotes | Async (cached) | yfinance network call |
| Daily AI briefing | Async (background) | LLM latency |
| Weekly portfolio review | Async (scheduled) | APScheduler |
| News retrieval | Async (background) | Network + volume |
| BCB macro data | Async (daily scheduled) | Rate limiting |

### Caching Strategy [PROPOSED]
| Data | Cache Location | TTL | Notes |
|------|---------------|-----|-------|
| Market quotes | In-memory (existing) | 15 min | Upgrade to persistent in production |
| Price history | In-memory (existing) | 60 min | Same |
| Fundamentals | In-memory (existing) | 24 hr | Same |
| FX rate | In-memory (existing) | 1 hr | Same |
| BCB data | DB or file cache | 24 hr | Low update frequency |
| News items | DB (retrieved) | 6 hr | Stored with timestamp |
| AI insights | DB (ai_insights) | Until invalidated | User-controlled refresh |
| Retirement projections | No cache (fast math) | N/A | Recompute on demand |

---

## 4. Module Structure — Future [PROPOSED]

### New Backend Structure (phases 10.1 onward)
```
backend/
├── domains/
│   ├── wealth_intelligence/    # NEW
│   │   ├── goals/              # Phase 10.1
│   │   ├── planning/           # Phase 10.3, 10.4
│   │   ├── portfolio/          # Phase 10.5
│   │   ├── market_radar/       # Phase 10.7
│   │   └── ai/                 # Phase 10.8, 10.9
│   └── [existing unchanged]
├── integrations/
│   ├── llm/                    # NEW (Phase 10.8)
│   │   ├── provider.py         # LLMProvider Protocol
│   │   ├── ollama_provider.py  # OllamaProvider
│   │   ├── gemini_provider.py  # GeminiProvider
│   │   └── openai_provider.py  # OpenAIProvider
│   ├── bcb/                    # NEW (Phase 10.7)
│   ├── news/                   # NEW (Phase 10.7)
│   └── [existing yfinance, market_data unchanged]
```

### New Frontend Structure (phases 10.1 onward)
```
frontend/src/app/
├── wealth-intelligence/        # NEW top-level section
│   ├── page.tsx                # Overview dashboard (Phase 10.9)
│   ├── health/page.tsx         # Financial Health (Phase 10.2)
│   ├── goals/page.tsx          # Goals Engine (Phase 10.3) [replaces /goals stub]
│   ├── retirement/page.tsx     # Retirement/FI (Phase 10.4)
│   ├── simulations/page.tsx    # Simulations (Phase 10.5)
│   ├── portfolio/page.tsx      # Portfolio Intelligence (Phase 10.5)
│   ├── rebalancing/page.tsx    # Rebalancing (Phase 10.6)
│   ├── market-radar/page.tsx   # Market Radar (Phase 10.7)
│   ├── watchlist/page.tsx      # Watchlist (Phase 10.6)
│   ├── news/page.tsx           # News & Events (Phase 10.7)
│   └── briefing/page.tsx       # Wealth AI Briefing (Phase 10.9)
└── [existing routes unchanged]
```

---

## 5. Non-Negotiable Constraints

1. **The existing Investments module (/wealth, /api/v1/investments) is STABLE. DO NOT MODIFY.**
2. **The Pierre/Governance pipeline is STABLE. DO NOT MODIFY.**
3. **The transaction ledger is IMMUTABLE. LLM cannot write to it.**
4. **All financial calculations are performed by the backend, not the LLM.**
5. **External data is always timestamped and clearly labeled as external.**
6. **AI output is always validated against a Pydantic schema before storage.**
7. **Prompt injection defenses must be in place before any external content reaches the LLM.**
