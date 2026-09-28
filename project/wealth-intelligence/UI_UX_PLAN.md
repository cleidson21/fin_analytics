# UI/UX Plan — Wealth Intelligence
**Status:** PROPOSED / ADR-024 PLANNING ADDENDUM LOCKED
**Date:** 2026-09-08

> **Authoritative post-10.3 Planning addendum (2026-09-26):** ADR-024 and
> `PLANNING_UX_CONTRACT.md` supersede this document wherever the older proposed
> Planning/page-chrome design conflicts. The locked direction is `Quiet Financial
> OS`: three intentions (`Simular`, `Objetivo`, `Comparar`), exact pt-BR string-safe
> financial input/output, shared Scenario Comparison context, answer-first results,
> compressed provenance, and restrained motion. Financial Health reuses the minimal
> page-chrome pattern only. UX-B1–UX-B6 are validated after accepted manual reviews;
> UX-B7 independently validated the complete UX cycle and closed it. The broader phase
> designs below remain future proposals.

---

## 1. Design Principles

### From the audit
- Current design: dark glassmorphism, zinc-950, emerald accent
- No Google Fonts (system fonts only) — upgrade needed
- Recharts with custom dark theme — KEEP
- No light mode — keep dark-only for now

### Wealth Intelligence Visual Identity [PROPOSED]
- **Typography:** Add Inter or Plus Jakarta Sans (Google Fonts) — professional financial feel
- **Color palette:** Expand beyond emerald — introduce a richer financial palette:
  - Primary: emerald-400 (existing) — positive, growth
  - Negative: rose-400 (upgrade from #e97070)
  - Warning: amber-400
  - Information: sky-400
  - Neutral: zinc-400
  - AI accent: violet-400 (for AI-generated content)
- **Density:** Medium — financial dashboards need data density without feeling cluttered
- **Cards:** Keep glassmorphism but add hierarchy (primary cards vs secondary cards)
- **Charts:** Recharts existing — add area charts, sparklines, waterfall charts
- **Tables:** Add sortable, filterable tables for positions and goals
- **Status badges:** Color-coded: green=positive, red=negative, amber=warning, violet=AI
- **AI Content marker:** All AI-generated text marked with violet accent + brain icon

---

## 2. Navigation Architecture [PROPOSED]

### Current Navigation
```
Sidebar:
- Controle Financeiro (/)
- Investimentos (/wealth)
- Metas (/goals)
- Governança (/governance)
```

### Proposed Navigation
```
Sidebar:
- Controle Financeiro (/)        [existing — DO NOT CHANGE]
- Wealth Intelligence            [NEW — top-level section]
  Sub-tabs: Overview | Saúde Financeira | Metas | Previdência | Simulações
- Investimentos (/wealth)        [existing — DO NOT CHANGE]
  Sub-tabs: Resumo | Patrimônio | Alocação | Dividendos | Evolução
- Portfolio Intelligence         [NEW in phase 10.5]
  Sub-tabs: Visão Geral | Rebalanceamento | Watchlist
- Market Radar                   [NEW in phase 10.7]
  Sub-tabs: Radar | Notícias & Eventos
- Wealth AI                      [NEW in phase 10.9]
  (Briefing / executive summary)
- Governança (/governance)       [existing — DO NOT CHANGE]
```

**Note:** The /goals stub page will be replaced by the Wealth Intelligence section. The existing /goals URL should redirect to /wealth-intelligence/goals.

---

## 3. Module Designs [PROPOSED]

### Page 1: Wealth Intelligence Overview
**Purpose:** High-level answer to "How am I doing financially?"
**User question:** Where am I? Am I on track? What changed? What needs attention?

**Layout:** 3-column grid on desktop, 1-column on mobile
- **Top row (hero):** Net Worth + month change, Investments total, Monthly cashflow, Savings rate
- **Second row:** Goal progress (mini cards), FI progress indicator, Passive income KPI
- **Third row (wide):** Wealth evolution chart (12 months), Portfolio contributors chart
- **Fourth row:** Financial health score, Recent AI insights (last 3), Market alerts (if any)
- **Bottom:** Executive AI briefing card (violet accent, clearly labeled "Powered by AI")

**Empty state:** Welcome screen with setup wizard (connect Pierre, import MyProfit, create first goal)
**Loading:** Skeleton cards with shimmer effect
**Error:** Graceful per-card errors (one card failure doesn't break the page)

---

### Page 2: Financial Health / Expense Intelligence
**Purpose:** "How is my spending?"
**User question:** Am I spending too much? Where is money going? Is my savings rate healthy?

**Components:**
- Monthly income vs expenses comparison (bar chart or butterfly chart)
- Savings rate indicator and factual closed-month direction
- Expense breakdown by category (donut + table)
- Fixed vs variable expenses (if data supports)
- Deterministic closed-month global trend facts for income, expense, net cashflow, and savings rate
- Deterministic exact-label category trends (`INCREASED`, `DECREASED`, `UNCHANGED`, `NEW`, `DISAPPEARED`)
- Spending anomalies produced by the ADR-015 deterministic engine
- Factual budget-pressure context from top share/rank, category trend, and anomaly status; no pressure score

**AI Role:** Future interpretation may explain certified metrics and trends, always labeled. AI does not calculate trends, anomaly states, category identity, or financial values.

---

### Page 3: Goals Engine
**Purpose:** "What am I saving toward? Am I on track?"
**User question:** Progress, projected date, what do I need to change?

**Components:**
- Goal cards with progress bar (actual/target, pct, projected date)
- Create/edit goal modal (type, amount, date, monthly contribution, account link)
- Priority ranking (drag to reorder)
- Per-goal projection chart (bar or area — time vs amount)
- "What needs to happen" card (required monthly contribution)
- Goal health status badge (ON_TRACK | AT_RISK | BEHIND | COMPLETED)
- AI suggestion card: "To reach [goal] by [date], you need R$ X/month" — labeled AI

**Goal Types:**
- EMERGENCY_RESERVE (existing)
- RETIREMENT (existing — replaces by dedicated page eventually)
- TRAVEL (existing)
- PURCHASE (existing)
- CUSTOM (existing)
- WEALTH_TARGET (new)
- INVESTMENT_TARGET (new)
- DIVIDEND_INCOME (new)
- FINANCIAL_INDEPENDENCE (new)

**Missing fields to add (Phase 10.1):** current_amount, priority, monthly_contribution, linked_account_id, assumptions_json

---

### Page 4: Retirement / Financial Independence
**Purpose:** "When can I retire? Am I on track?"
**User question:** How far am I from FI? What do I need to change?

**Components:**
- FI Progress bar (current wealth / target portfolio)
- Projected FI date (primary KPI)
- Required portfolio at target age (calculated, not AI)
- Inputs panel: age, retirement age, expenses/month, expected return, inflation, contributions, expected passive income
- Scenario comparison (conservative/baseline/optimistic — 3 projected lines on chart)
- Gap analysis (what's missing: contribution, return, time)
- Sensitivity table: "if return is X%, FI date is..."
- Passive income projection (dividends + withdrawal rate)

**AI Role:** Explain the numbers in natural language. "At your current contribution rate, the projection suggests..." — clearly labeled.

---

### Page 5: Simulations
**Purpose:** "What if I change something?"
**User question:** What is the impact of different decisions?

**Components:**
- Scenario builder panel (adjust: monthly contribution, return, expenses, lump sum, horizon)
- Side-by-side comparison: Base scenario vs Alternative scenario
- Impact summary: "This change moves your projected FI date by X years"
- Contribution effectiveness chart
- Sensitivity slider UI

**Scenarios:**
- +R$500/month contribution
- 10% expense reduction
- 1-year contribution pause
- Retirement 5 years earlier
- Lower expected return
- Additional lump sum

---

### Page 6: Portfolio Intelligence
**Purpose:** "What is happening with my investments?"
**User question:** What is contributing? What is detracting? How am I allocated?

**Components:**
- Top movers this month (winners/losers table)
- Portfolio attribution chart (waterfall: contributions + price changes + dividends = total change)
- Asset class allocation vs benchmark/target
- Geographic/currency exposure
- Concentration risk indicators
- Dividend contribution analysis
- Benchmark comparison (IBOV, CDI, IFIX, S&P500)
- Volatility indicator per asset
- Portfolio health score

**AI Role:** Explain attribution. "The portfolio's loss of R$X this month was primarily driven by Y and Z." — labeled.

---

### Page 7: Rebalancing
**Purpose:** "Is my portfolio aligned with my target?"
**User question:** Am I overexposed anywhere? What should I do?

**Components:**
- Target allocation editor (user sets % per asset class)
- Current vs target table with deviation column
- Deviation severity badge (within tolerance / needs attention / significant drift)
- Hypothetical rebalancing suggestion (how much to add/reduce per class — NOT auto-execute)
- Cost estimate for rebalancing (if trade data available)

**AI Role:** Explain deviations. "Your FII exposure has drifted significantly above target. This may increase your income but also concentration risk." — labeled.

---

### Page 8: Market Radar
**Purpose:** "What is happening in markets relevant to me?"
**User question:** What signals deserve my attention?

**Components:**
- Portfolio asset status board (each asset: price, 1d/1m change, status badge)
- Unusual movement alerts (> threshold % in a day)
- Technical signals table (RSI, moving average crossings)
- Valuation indicators (P/L, P/VP from yfinance.info where available)
- Benchmark performance comparison
- Currency alert (USD/BRL significant move)
- BCB/SELIC rate information

**Signal labeling (MANDATORY):**
- FACT: "RSI is 28"
- SIGNAL: "RSI below 30 (traditionally oversold)"
- INTERPRETATION: "This may indicate selling pressure has exceeded fundamentals" [AI-labeled]

---

### Page 9: Watchlist
**Purpose:** "Track assets I'm monitoring but don't own yet"
**User question:** Has anything changed on assets I'm watching?

**Components:**
- Watchlist table (ticker, name, current price, thesis, target price, alerts)
- Add/remove items
- Alert configuration (price threshold, % change, news mention)
- Notes field per asset

---

### Page 10: News & Events
**Purpose:** "What is happening in the news relevant to my portfolio?"

**Components:**
- News feed (retrieved from Google News RSS + filtered for portfolio assets)
- Event calendar (COPOM meetings, earnings, dividend ex-dates)
- Per-news: source, title, URL, publication time, retrieved time
- AI summary of news relevance (labeled) — max 2 sentences

**MANDATORY:** All news items link to original source. AI never invents news.

---

### Page 11: Wealth AI Briefing
**Purpose:** Executive financial intelligence briefing
**NOT a chatbot.** Structured, scheduled briefings.

**Components:**
- Daily/Weekly/Monthly briefing selector
- Latest briefing card (with generated_at timestamp, violet AI badge)
- Briefing sections: Portfolio, Cashflow, Goals, Market, Risk/Opportunity
- Regenerate button (manual trigger)
- Historical briefings list
- Data freshness indicators (when was each data source last updated)

**Visual language for AI content:**
- Violet left border on all AI-generated cards
- Brain icon (Lucide: BrainCircuit or Sparkles)
- "Generated by AI · [timestamp]" footer on every AI section
- is_ai_interpretation ensures this labeling is always present

---

## 4. UI Development Strategy

**Approach (as requested):**
1. Implement functional UI first (data flows, calculations, basic layout)
2. Local visual refinement per page (polish individual pages)
3. Final global visual consistency pass (Phase 10.12)

**Per phase:** Each implementation phase includes basic functional UI. Not a polished UI phase. Polishing is Phase 10.12.

---

## 5. Mobile Behavior

- All pages: mobile-first responsive (single column on small screens)
- Wealth Intelligence Overview: collapsible sections on mobile
- Charts: use smaller chart height on mobile, touch-friendly tooltips
- Tables: horizontal scroll on mobile
- Goal cards: full-width on mobile
- Navigation: existing sidebar collapses to hamburger on mobile (if not already implemented)

---

## 6. Loading & Error States

**All pages must implement:**
- Skeleton loading (shimmer) for every data region
- Per-card error states (card shows error without breaking neighbors)
- Empty states with actionable prompts ("Import your investments to see portfolio intelligence")
- AI loading state: "Generating briefing..." with spinner

**Connections:**
- API errors → show friendly message + retry button
- No data → show setup prompt
- Partial data → show what's available, indicate what's missing
