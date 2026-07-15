# FINANALYTICS V3 — CURRENT PHASE
> Documento pequeno e sempre atual. Atualizado ao início e fim de cada fase.
> **Leia este arquivo primeiro ao retomar o projeto em uma nova conversa.**
> Última atualização: 2026-07-14 — Fase R0 (Reconciliação Documental)

---

## ⚡ FASE ATUAL: 7 — Engines Analíticas & Pipelines

**Status:** 🔄 Em andamento
**Iniciada em:** 2026-07-13
**Objetivo:** Conectar as Engines analíticas (Position, Valuation, Wealth, Performance, History, FinancialAnalytics) ao Banco de Dados oficial V3, construir os endpoints faltantes e certificar o Frontend end-to-end sem mocks.

---

## Gates Concluídos (Sprint 7)

Todos os Gates abaixo foram concluídos durante a Sprint 7 e pertencem à Fase 7 do Master Plan.
Os Gates foram originalmente identificados com prefixo "10.x" — nomenclatura interna da Sprint, não uma fase separada.

| Gate | Descrição | Status |
|---|---|---|
| 10.1 | Pipeline Real de Importação (CSV, OFX, JSON) | ✅ Concluído |
| 10.2 | Ledger de Importações e Auditoria Permanente | ✅ Concluído |
| 10.3 | Séries Temporais e Performance Histórica | ✅ Concluído |
| 10.4 | Market Data Engine | ✅ Concluído |
| 10.5 | Validação End-to-End das Engines | ✅ Concluído |
| 10.6 | History Engine Incremental (O(N+M)) | ✅ Concluído |
| 10.7 | Historical Asset Pricing Engine | ✅ Concluído |
| 10.8 | Financial Analytics Engine (TWR, MWR, Sharpe, Beta) | ✅ Concluído |
| 10.9 | Application Service Layer & Dependency Injection | ✅ Concluído |
| 10.10 | Portfolio Dashboard API Layer | ✅ Concluído |
| 10.11 | API Contract & Backend Stabilization | ✅ Concluído |
| 10.12 | Frontend Readiness | ✅ Concluído |
| 10.13 | Auditoria Arquitetural de Reconciliação | ✅ Concluído (auditoria e planejamento) |

---

## Situação pós-Gate 10.13 — O que falta na Fase 7

O Gate 10.13 identificou as seguintes pendências críticas que **DEVEM** ser resolvidas antes do Gate final da Fase 7:

### Problema 1 — Engines In-Memory (🔴 CRÍTICO)
As Engines financeiras (Position, Valuation, Wealth, Performance) rodam em SQLite In-Memory, ignorando as tabelas físicas do V3 (`asset_valuations`, `portfolio_snapshots`, etc.).
- **Solução:** Criar `ValuationRepository`, `WealthRepository`, `DividendRepository` e conectar as Engines ao V3.

### Problema 2 — Endpoints Faltantes (🟠 ALTO)
9+ endpoints requeridos pelo Frontend estão ausentes:
- `GET /dashboard/summary-v2`, `pacing-v2`, `heatmap`, `categories`
- `GET /investments/evolution/summary`, `evolution/history`
- `GET /investments/dividends/history`, `dividends/breakdown`
- `GET /investments/asset/{ticker}`
- Rotas de `/governance/` (staging, confirm, rollback, learning)

### Problema 3 — Integrações Externas (🟠 ALTO)
Ausentes: yfinance (preços reais), Banco Central (CDI), Gemini AI.

---

## Próximas Tarefas da Fase 7

> Estas são tarefas da Fase 7, não fases independentes.
> Consulte `09_IMPLEMENTATION_QUEUE.md` para o detalhamento completo.

| Tarefa | Descrição | Prioridade |
|---|---|---|
| R1 | Reconectar Repositories de Valuation, Wealth e Dividends ao Banco Oficial V3 | 🔴 P1 |
| R2 | Otimizar leitura do Dashboard (desacoplar Engines da leitura em realtime) | ✅ Concluída |
| R3 | Construir endpoints de Evolução e Dividendos faltantes | ✅ Concluída |
| R4 | Certificação Frontend E2E sem mock | ✅ Concluída |
| R5 | Gate de Fechamento e Certificação da Fase 7 | ✅ Concluída |
| INT | Implementar yfinance, Banco Central, Gemini, APScheduler | 🟡 P2-P3 |

---

## O que vem após a Fase 7

### FASE 8 — AI & Learning
Com as Engines conectadas ao V3 e os endpoints construídos, será iniciada a implementação do motor de IA para classificação e aprendizado.
- Gate: `GET /governance/learning/rules` retorna regras com métricas

### FASE 9 — Validação E2E & Hardening
Gate final: todas as 18 telas respondem com dados reais, zero Network Error no console.

---

> Para contexto histórico sobre os desvios de nomenclatura corrigidos na Fase R0, consulte `34_ARCHITECTURE_RECONCILIATION.md`.
