# Master Plan & Status — FINANALYTICS Wealth Intelligence
**Updated:** 2026-09-26 (Phase 10.3 validated / closed)

---

## Vision

Evolve FINANALYTICS from a system that **explains the financial past** into a **personal financial intelligence platform** that supports decisions about the financial future.

The platform provides:
1. **Visibility** — complete, current picture of wealth across all assets and accounts
2. **Intelligence** — pattern recognition and anomaly detection in cashflow and investments
3. **Planning** — deterministic projections for goals, retirement, and financial independence
4. **Context** — relevant market and economic context, clearly labeled as external
5. **Synthesis** — AI-generated briefings from verified data, never as financial authority

---

## Governance Rules (Non-Negotiable)

1. **AI IS READ-ONLY WITH RESPECT TO FINANCIAL TRUTH**
2. All financial arithmetic is performed by deterministic backend services
3. The existing Investments module is STABLE — do not modify without explicit scope
4. New phases do not modify existing passing tests
5. Every phase ends with a formal acceptance checklist sign-off
6. External data is always timestamped and labeled
7. All AI output is validated against Pydantic schema before storage

---

## Phase Roadmap

| Phase | Name | Status | Preconditions |
|-------|------|--------|--------------|
| 10.0 | Architecture & Product Design | **COMPLETE** | — |
| 10.1 | Goal Domain Foundation | IMPLEMENTED / VALIDATED | Complete |
| 10.2 | Financial Health Intelligence | **COMPLETED / MERGED — 10.2.10-C VALIDATED** | 10.1 complete |
| 10.3 | Planning & Projection | **VALIDATED / CLOSED.** 10.3.1–10.3.6, 10.3.9–10.3.12 validated; 10.3.7-A deferred; 10.3.8 automated validation passed / Swagger smoke deferred; 10.3.10A contract locked; 10.3.10B complete. ADR-024 post-closure UX contract implemented / validated; UX-B1–UX-B7 validated; POST-10.3 UX closed. | 10.1 and 10.2 complete |
| 10.4 | Retirement & Financial Independence (FIRE) | READY / NOT STARTED — BOUNDARY APPROVED | 10.3 complete |
| 10.5 | Portfolio Intelligence | NOT STARTED — BOUNDARY APPROVED | Stable investments, 10.3 complete |
| 10.6 | Rebalancing & Watchlist | NOT STARTED | 10.5 complete |
| 10.7 | External Market Intelligence | NOT STARTED | 10.5 complete, BCB/news validated |
| 10.8 | LLM Provider Foundation | NOT STARTED | 10.7 complete, Ollama installed |
| 10.9 | Wealth AI Briefing | NOT STARTED | 10.8, 10.4, 10.5 complete |
| 10.10 | Advanced Orchestration | NOT STARTED (CONDITIONAL) | 10.9 quality gap demonstrated |
| 10.11 | Docker & Operations | NOT STARTED | All backend phases stable |
| 10.12 | Global UX / Visual Polish | NOT STARTED | All UI phases complete |

---

## Pre-Work Resolution (Before 10.1)

### RESOLVED: position_snapshots schema investigation
Migration 013 creates a SQL table `position_snapshots` with `snapshot_hash` UNIQUE key.
The ORM `PositionSnapshotModel` maps to the same table name with a different schema.
**Resolution:** The live DB was inspected and the Alembic-compatible schema is active. The remaining `alembic check` FK issue is documented in ADR-014 and is non-blocking for the current phase.

### RESOLVED: requirements.txt
The active dependencies `pydantic-settings`, `aiosqlite`, `python-jose[cryptography]`, and `bcrypt` are listed in `requirements.txt`.

---

## Key Architecture Decisions

| Decision | ADR | Status |
|----------|-----|--------|
| Deterministic calculations first, LLM interprets | ADR-001 | APPROVED |
| Ollama runs native on Windows host | ADR-002 | CONFIRMED |
| Single documentation source | ADR-003 | APPROVED |
| No agent frameworks until justified | ADR-004 | APPROVED |
| External consensus clearly labeled | ADR-005 | APPROVED |
| No second yfinance system | ADR-006 | APPROVED |
| Single LLM + deterministic context (Option D) | ADR-007 | PROPOSED |
| SQLite retained for local use | ADR-008 | PROPOSED |
| position_snapshots conflict is a BLOCKER | ADR-009 | BLOCKER |
| brFinance as isolated adapter | ADR-010 | PROPOSED |
| Navigation restructure in 10.1 | ADR-011 | PROPOSED |
| Google News RSS as news source | ADR-012 | PROPOSED |
| AI insights immutable after storage | ADR-013 | APPROVED |
| accounts PK incompatibility documented | ADR-014 | DOCUMENTED |
| Deterministic anomaly specification | ADR-015 | APPROVED |
| Financial Health consolidated account scope | ADR-017 | APPROVED |
| Financial trend and stability readiness | ADR-018 | APPROVED |
| Planning input and source boundary | ADR-019 | APPROVED |
| Planning mathematical contract | ADR-020 | APPROVED |
| Planning scenario semantics and lifecycle | ADR-021 | APPROVED |
| Retirement/FIRE and Portfolio Intelligence boundary | ADR-022 | APPROVED |
| Investment portfolio initial-wealth source | ADR-023 | APPROVED |

---

## Target Product Summary

When complete, the user experience includes:

1. **Wealth Intelligence Overview** — net worth, investments, savings rate, goal progress, FI timeline, daily alerts
2. **Financial Health** — observed cashflow, spending distribution, deterministic historical trends, and anomaly detection
3. **Goals Engine** — goal tracking, projections, required contributions, scenarios
4. **Retirement & Financial Independence (FIRE)** — retirement/FI modes over reusable Planning engines, gap analysis, income/withdrawal assumptions, and sensitivity
5. **Portfolio Intelligence** — attribution, exposure, concentration risk
6. **Rebalancing** — target vs current, deviation alerts
7. **Market Radar** — asset signals, technical indicators, BCB macro data
8. **Watchlist** — monitor assets not yet in portfolio
9. **News & Events** — relevant news for owned assets
10. **Wealth AI Briefing** — daily/weekly structured briefing from verified data
