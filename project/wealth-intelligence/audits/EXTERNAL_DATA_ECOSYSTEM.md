# External Data Ecosystem
**Status:** RESEARCHED + PROPOSED
**Date:** 2026-09-08

---

## 1. Current External Data [VERIFIED]

| Source | Data | Integration | Status |
|--------|------|-------------|--------|
| yfinance 0.2.31 | Quotes, history, fundamentals, FX | YFinanceProvider | ACTIVE |
| Pierre Finance API | Open Finance transactions | PierreClient | ACTIVE |
| MyProfit (CSV) | Investment positions, portfolio history, dividends | CSV import pipeline | ACTIVE |

---

## 2. Candidate External Data Sources [RESEARCHED]

### BCB/SGS — Banco Central do Brasil
| Attribute | Value |
|-----------|-------|
| Purpose | Macro indicators: CDI, SELIC, IPCA, IGPM |
| Cost | Free |
| API Key | No |
| Endpoint | https://api.bcb.gov.br/dados/serie/bcdata.sgs.{id}/dados |
| Python lib | python-bcb (PyPI) |
| Key series | CDI=4389, SELIC=432, IPCA=433, SELIC efetiva=11 |
| Reliability | High (official BCB) |
| Update freq | Daily |
| Limitations | 10-year window per query (March 2025+) |
| Recommendation | **USE — Phase 10.7** |

### brFinance (eudesrodrigo/brFinance)
| Attribute | Value |
|-----------|-------|
| Purpose | CVM financial statements (DFP, ITR) |
| Cost | Free |
| API Key | No (uses CVM public API) |
| Data | Balance Sheet, Income Statement, Cash Flow |
| Python | Async (CVMAsyncBackend) |
| Coverage | All B3-listed companies filing with CVM |
| Reliability | Medium (depends on CVM portal) |
| Maintenance | Community, not actively maintained |
| Use case | P/L, ROE, EBITDA for BR stocks |
| Recommendation | **USE AS ISOLATED ADAPTER — Phase 10.7** (not a direct dependency) |

### Fundamentus (scraping)
| Attribute | Value |
|-----------|-------|
| Purpose | BR stock ratios and indicators |
| Cost | Free |
| Legal | Grey area (web scraping) |
| Reliability | Low (layout changes break scrapers) |
| Recommendation | **DO NOT USE** — prefer brFinance (CVM official) or yfinance.info |

### Google News RSS
| Attribute | Value |
|-----------|-------|
| Purpose | News articles about assets, markets, companies |
| Cost | Free |
| API Key | No |
| Format | RSS feed |
| URL | https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-BR |
| Reliability | Medium (Google may change RSS access) |
| Latency | Real-time |
| License | Personal/non-commercial OK |
| Recommendation | **USE — Phase 10.7** (matches b3analysis pattern) |

### yfinance .info (fundamentals)
| Attribute | Value |
|-----------|-------|
| Purpose | P/L, P/VP, DY, Beta, Mkt Cap |
| Cost | Free |
| Already integrated | YES (get_indicators in YFinanceProvider) |
| Reliability | LOW for BR assets (frequent None values) |
| Recommendation | **KEEP but label as unreliable** — supplement with brFinance for BR stocks |

### IBGE/SIDRA API
| Attribute | Value |
|-----------|-------|
| Purpose | IPCA components, GDP |
| Cost | Free |
| API Key | No |
| Endpoint | https://servicodados.ibge.gov.br/api/v3/ |
| Recommendation | **Optional — Phase 10.7** if detailed inflation breakdown needed |

---

## 3. Analyst Consensus Coverage [RESEARCHED]

**Reality check:** Free public analyst consensus is very limited.

| Asset Type | yfinance consensus | Coverage | Reliability |
|------------|-------------------|----------|-------------|
| US Large Cap (SP500) | recommendationMean | Good | Medium |
| BR Large Cap STOCK | recommendationMean | Partial | Low |
| FIIs | None available | None | N/A |
| BDRs | Depends on underlying | Variable | Low |
| FIXED_INCOME | None | None | N/A |
| CRYPTO | None | None | N/A |

**Conclusion:** Do NOT present analyst consensus as a core feature. Where available via yfinance.info, display with clear "Data may be unavailable or outdated" disclaimer. Never fabricate.

---

## 4. Technical Indicators [PROPOSED]

### Approach: Calculate locally from price history

Using yfinance historical data (already available), calculate client-side:
- RSI (14-day): Relative Strength Index
- SMA (20/50/200 day): Simple Moving Averages
- EMA (12/26): Exponential Moving Averages
- MACD: Moving Average Convergence/Divergence
- Bollinger Bands (20 SMA ± 2 std dev)

**Library:** `pandas-ta` or `ta-lib` — evaluate in Phase 10.7

**IMPORTANT:** Technical indicators derived from historical data are **deterministic calculations**, not external data. They do not require external APIs.

---

## 5. Recommended External Data Stack [PROPOSED — Phase 10.7]

```
Data Layer Priority:

1. yfinance (EXISTING)
   → Quotes, history, FX, basic fundamentals

2. BCB/SGS (ADD in 10.7)
   → CDI, SELIC, IPCA — essential for Brazilian finance benchmarks

3. Google News RSS (ADD in 10.7)
   → News for portfolio assets and Brazilian market events

4. brFinance as isolated adapter (ADD in 10.7 — cautiously)
   → Balance sheets and income statements for BR stocks
   → Wrap in a dedicated CVM adapter, not a direct dependency

5. IBGE/SIDRA (OPTIONAL — post 10.7)
   → If detailed macro analysis is needed

6. yfinance .info (EXISTING — keep, label as unreliable)
   → Only show if value is non-null, always show data date
```

---

## 6. Dependency Matrix [PROPOSED]

| Dependency | Phase | Type | Risk | Alternative |
|------------|-------|------|------|-------------|
| yfinance | EXISTING | Python | Low | proprietary API |
| python-bcb | 10.7 | Python | Low | direct BCB HTTP |
| brFinance | 10.7 | Python | Medium (maintenance) | direct CVM HTTP |
| feedparser (RSS) | 10.7 | Python | Low | requests + lxml |
| pandas-ta | 10.7 | Python | Low | manual numpy |
| ollama (Python SDK) | 10.8 | Python | Low | HTTP directly |
| google-generativeai | EXISTING | Python | Low | — |
| openai | 10.8 | Python | Low | — |
| pydantic-settings | EXISTING (unlisted) | Python | None | — |
| aiosqlite | EXISTING (unlisted) | Python | None | — |

---

## 7. Data Freshness Policy [PROPOSED]

| Data | Max Age for Display | What to show if stale |
|------|--------------------|-----------------------|
| Market quotes | 60 min | "Price as of [timestamp]" |
| Portfolio value | Last MyProfit sync | "As of [sync date]" |
| BCB rates | 24 hours | "Rate as of [date]" |
| News items | 6 hours | "Retrieved [X hours ago]" |
| Fundamentals (yf.info) | 24 hours | "Fundamental data may be outdated" |
| AI insights | Until user refreshes | "Generated [timestamp]" |

Always display data timestamps. Never present stale data as current without disclosure.
