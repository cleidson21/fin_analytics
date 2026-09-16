# Dependency Installation Roadmap
**Status:** PROPOSED — do not install during Lote 10.0
**Date:** 2026-09-08

---

## Backend Dependencies

| Dependency | Purpose | Phase | Python | Required? | Alternative | Risk |
|------------|---------|-------|--------|-----------|-------------|------|
| **pydantic-settings** | Settings from .env | IMMEDIATE (fix) | YES | YES | python-dotenv | None |
| **aiosqlite** | Async SQLite driver | IMMEDIATE (fix) | YES | YES | — | None |
| **python-jose[cryptography]** | JWT tokens | IMMEDIATE (fix) | YES | YES | PyJWT | None |
| **passlib[bcrypt]** | Password hashing | IMMEDIATE (fix) | YES | YES | — | None |
| **python-bcb** | BCB/SGS macro data (CDI, SELIC, IPCA) | 10.7 | YES | YES | Direct HTTP | Low |
| **feedparser** | Google News RSS parsing | 10.7 | YES | YES | requests+lxml | Low |
| **pandas-ta** | Technical indicators (RSI, SMA, EMA) | 10.7 | YES | Preferred | manual numpy | Low |
| **brFinance** | CVM financial statements | 10.7 | YES | Optional | Direct CVM HTTP | Medium (maintenance) |
| **ollama** | Ollama Python SDK | 10.8 | YES | YES (if AI_PROVIDER=ollama) | Direct HTTP | Low |
| **openai** | OpenAI Python SDK | 10.8 | YES | Optional (if AI_PROVIDER=openai) | — | Low |
| **httpx** | Async HTTP client (for providers) | 10.8 | YES | Preferred | requests (sync) | Low |

### IMMEDIATE fixes (requirements.txt is incomplete)
These packages are already USED by the application but missing from requirements.txt:
- pydantic-settings
- aiosqlite
- python-jose[cryptography]
- passlib[bcrypt]

Action: Add these to requirements.txt in a maintenance PR before Phase 10.1.

---

## Frontend Dependencies

| Dependency | Purpose | Phase | Node | Required? | Alternative | Risk |
|------------|---------|-------|------|-----------|-------------|------|
| **@fontsource/inter** OR Google Fonts CSS | Typography upgrade | 10.12 | YES | Preferred | system fonts | None |
| No major new dependencies expected | — | — | — | — | — | — |

Existing frontend stack is sufficient through Phase 10.9. Recharts already handles all chart needs.

---

## Infrastructure Dependencies

| Tool | Purpose | Phase | Required? | Notes |
|------|---------|-------|-----------|-------|
| **Ollama** | Local LLM runtime | 10.8 | YES (if local AI) | Install natively on Windows |
| **Docker Desktop** | Containerization | 10.11 | Optional | For `docker compose up` |
| **NVIDIA drivers ≥ 550** | GPU for Ollama | 10.8 | YES (for GPU inference) | Windows host |

---

## Installation Order (when each phase begins)

### Before Phase 10.1 (maintenance)
```bash
# Fix requirements.txt — add missing packages
pip install pydantic-settings aiosqlite "python-jose[cryptography]" "passlib[bcrypt]"
```

### Phase 10.7
```bash
pip install python-bcb feedparser pandas-ta
# Optional (evaluate first):
pip install brfinance
```

### Phase 10.8
```bash
pip install ollama openai httpx
# Install Ollama on Windows (separately):
# Download from https://ollama.com/download/windows
ollama pull llama3.1:8b  # or configured model
```

### Phase 10.11 (Docker)
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop/
# Verify: docker compose up
```
