# Infrastructure — Docker, Deployment, Ollama
**Status:** PROPOSED (based on VERIFIED audit — no Docker currently exists)
**Date:** 2026-09-08

---

## 1. Current State [VERIFIED]
- No Dockerfile found in repository
- No docker-compose.yml found
- No Ollama installation
- Application runs natively: `uvicorn backend.main:app` (backend) + `npm run dev` (frontend)
- Database: local SQLite file at `database/fin_analytics.db`
- `settings.DATABASE_URL` is the single runtime database authority; the sync and
  async SQLite engines are derived explicitly from it.
- Alembic is the schema-evolution authority. Importing or starting the
  application performs no `create_all`, migration, or other schema DDL.
- Pytest installs a repository-wide disposable SQLite URL before collection and
  refuses the active `database/fin_analytics.db` as `TEST_DATABASE_URL`.

---

## 2. Docker Architecture [PROPOSED — Phase 10.11]

### Recommended Strategy: App containerized, Ollama native on host

```yaml
# docker-compose.yml (PROPOSED)
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./database/fin_analytics.db
      - AI_PROVIDER=${AI_PROVIDER:-gemini}
      - AI_OLLAMA_BASE_URL=http://host.docker.internal:11434
    volumes:
      - ./database:/app/database
    depends_on: []

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
```

### Why Ollama runs NATIVELY on the host (Option A) [RESEARCHED]

**Docker GPU passthrough on Windows:**
- Requires WSL2 backend + NVIDIA Container Toolkit installed INSIDE WSL2
- Requires: `wsl --update`, NVIDIA driver ≥ 550, Docker Desktop WSL2 mode
- Works but adds significant setup complexity for a personal-use application
- If Docker Desktop updates or NVIDIA drivers change, GPU passthrough may break

**Host-native Ollama:**
- Installs directly on Windows, uses RTX 5060 natively without WSL2 overhead
- Accessible to Docker containers via `http://host.docker.internal:11434`
- Simpler to maintain and update
- Models persist at `%USERPROFILE%\.ollama\models`

**Recommendation: ADR-002 (EXISTING) — Ollama native on host, dockerized backend connects to host**

This is already recorded as ADR-002 (PROPOSED). This document confirms the recommendation.

### Alternative: Full Containerization (Option B)
If desired in the future:
```yaml
  ollama:
    image: ollama/ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
volumes:
  ollama_models:
```
This requires WSL2 NVIDIA Container Toolkit setup. Document as Phase 10.11 decision once Docker phase begins.

---

## 3. Online/Local Architecture [PROPOSED]

### The Privacy Challenge
If frontend and backend are deployed to cloud:
```
Browser → Online Frontend → Online Backend → Cloud DB
```
The cloud backend cannot access `localhost:11434` on the user's machine.

### Viable Options

**Option 1: Fully Local (simplest, most private)**
```
Browser (local) → Local Backend → Local SQLite → Local Ollama
```
- No cloud dependency
- Maximum privacy
- No public URL
- Suitable for personal finance

**Option 2: Cloud Frontend + Cloud Backend + Cloud LLM**
```
Browser → Vercel/Netlify → Railway/Fly.io → Gemini/OpenAI API
```
- Full cloud, accessible from anywhere
- Least private for AI context
- Financial data still in cloud DB

**Option 3: Cloud Frontend + Cloud Backend + Local LLM Bridge [COMPLEX]**
```
Browser → Cloud Frontend → Cloud Backend → [needs path to local Ollama]
                                          ← Tailscale/ngrok/VPN bridge
                                          ← Local machine with Ollama
```
- Private local AI, cloud-accessible frontend
- Complex: requires stable tunnel to home machine
- Tailscale is the most elegant solution for this

**Option 4: Hybrid — Cloud for data, local for AI**
```
Browser → Local App → Local/Cloud Backend → Local Ollama
                    → Cloud LLM as fallback when local unavailable
```

### Recommendation [PROPOSED]
For a **personal finance application** where privacy is important:

**Short/medium term:** Fully local (Option 1)
- `docker compose up` starts frontend + backend
- Ollama runs natively on the same machine
- SQLite DB on local disk
- No cloud exposure of financial data or AI context

**Long term (if remote access desired):** Option 3 via Tailscale
- Tailscale creates an encrypted mesh network
- Backend on Tailscale-accessible machine
- Ollama on same machine
- Access from anywhere as if local

---

## 4. SQLite vs PostgreSQL [PROPOSED]

Current: SQLite (single file, WAL mode)

For production with Docker and potential multi-container setup:
- SQLite with WAL works fine for single-container local use
- If backend scales to multiple workers: SQLite concurrency becomes a limitation
- Migration to PostgreSQL would require: new DATABASE_URL, migration runner update, no SQLite-specific pragmas

**Recommendation for Phase 10.11:** Keep SQLite for local personal use. Document PostgreSQL upgrade path as a future ADR if needed.

---

## 5. Ollama Setup Guide [PROPOSED — for Phase 10.8]

1. Download Ollama: https://ollama.com/download/windows
2. Install natively on Windows
3. Set NVIDIA driver ≥ 550
4. Pull model: `ollama pull llama3.1:8b` (or configured model)
5. Verify GPU: `ollama run llama3.1:8b` — check GPU utilization in Task Manager
6. Test API: `curl http://localhost:11434/api/tags`
7. Configure backend: `AI_PROVIDER=ollama`, `AI_OLLAMA_BASE_URL=http://localhost:11434`

Model storage: `%USERPROFILE%\.ollama\models\`
Typical size (Q4_K_M): Llama 3.1 8B ≈ 5 GB, Qwen 3 8B ≈ 5 GB
