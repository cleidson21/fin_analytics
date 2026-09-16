# Environment Variable Master Inventory
**Status:** PROPOSED (do not modify .env yet)
**Date:** 2026-09-08

---

## Current Variables [VERIFIED from .env.example and config.py]

| Variable | Purpose | Required | Example | Secret | Stage |
|----------|---------|----------|---------|--------|-------|
| ENVIRONMENT | dev/prod switch | No | development | No | All |
| DATABASE_URL | SQLAlchemy connection string | No (has default) | sqlite+aiosqlite:///./database/fin_analytics.db | No | All |
| JWT_SECRET | JWT signing secret | YES | (random 32-char string) | YES | All |
| JWT_EXPIRE_MINUTES | Token TTL | No | 60 | No | All |
| PIERRE_API_KEY | Pierre Finance API key | No (disables Pierre sync if absent) | pk_... | YES | Production |
| GEMINI_API_KEY | Google Gemini API key | No (disables Gemini if absent) | AIza... | YES | Cloud AI |
| OPENAI_API_KEY | OpenAI API key | No (disables OpenAI if absent) | sk-... | YES | Cloud AI |
| MYPROFIT_USERNAME | MyProfit login | No (disables auto-import) | user@email.com | YES | Optional |
| MYPROFIT_PASSWORD | MyProfit password | No | ... | YES | Optional |
| YFINANCE_ENABLED | Enable/disable yfinance calls | No | true | No | All |

---

## Proposed Future Variables [PROPOSED — do not add yet]

### AI Provider
| Variable | Purpose | Required | Example | Secret | Phase Introduced |
|----------|---------|----------|---------|--------|-----------------|
| AI_PROVIDER | Primary LLM: ollama, gemini, openai | No (default: gemini) | ollama | No | 10.8 |
| AI_MODEL | Model identifier | No (provider default) | llama3.1:8b | No | 10.8 |
| AI_OLLAMA_BASE_URL | Ollama HTTP base URL | If AI_PROVIDER=ollama | http://localhost:11434 | No | 10.8 |
| AI_TEMPERATURE | LLM temperature | No | 0.0 | No | 10.8 |
| AI_MAX_TOKENS | Max output tokens | No | 2048 | No | 10.8 |
| AI_TIMEOUT_SECONDS | LLM call timeout | No | 60 | No | 10.8 |
| AI_FALLBACK_PROVIDER | Fallback if primary unavailable | No | gemini | No | 10.8 |

### External Data
| Variable | Purpose | Required | Example | Secret | Phase |
|----------|---------|----------|---------|--------|-------|
| BCB_ENABLED | Enable BCB/SGS data fetch | No | true | No | 10.7 |
| NEWS_ENABLED | Enable Google News RSS fetch | No | true | No | 10.7 |
| NEWS_ITEMS_MAX | Max news items per briefing | No | 5 | No | 10.7 |
| NEWS_ITEM_MAX_CHARS | Max chars per news item | No | 500 | No | 10.7 |

### Scheduler
| Variable | Purpose | Required | Example | Secret | Phase |
|----------|---------|----------|---------|--------|-------|
| SCHEDULER_ENABLED | Enable APScheduler | No | true | No | 10.9 |
| DAILY_BRIEFING_HOUR | Hour for daily briefing (0-23) | No | 7 | No | 10.9 |
| WEEKLY_BRIEFING_DAY | Day of week for weekly (0=Mon) | No | 0 | No | 10.9 |

### Docker / Production
| Variable | Purpose | Required | Example | Secret | Phase |
|----------|---------|----------|---------|--------|-------|
| FRONTEND_URL | Allowed CORS origin | Production only | https://app.example.com | No | 10.11 |
| LOG_LEVEL | Logging verbosity | No | INFO | No | 10.11 |

---

## Notes

- All SECRET variables must never be committed to git
- All optional variables have sensible defaults in `config.py`
- When AI_PROVIDER=ollama, GEMINI_API_KEY and OPENAI_API_KEY are not required
- When AI_PROVIDER=gemini, GEMINI_API_KEY is required
- MYPROFIT_* variables are unused if user imports CSV manually via UI

## Naming Convention [PROPOSED]
- Uppercase, underscore-separated
- Prefix: service group (AI_, BCB_, NEWS_) for clarity
- No nesting (e.g., no JSON in env vars)

## .env.example Updates (do not modify yet — Phase 10.8)
When Phase 10.8 begins, add the AI Provider variables to `.env.example` with clear comments.
