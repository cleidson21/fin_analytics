# GATE 10.13 — RELATÓRIO DE RECONCILIAÇÃO ARQUITETURAL E INTEGRAÇÕES

## ETAPA 1 — AUDITORIA ARQUITETURAL COMPLETA

### 1. Mapa Completo da Arquitetura Atual

A base de código atual divide-se em duas abordagens de persistência e orquestração:

**Módulos utilizando Banco Oficial V3 (SQLite Físico - `database/fin_analytics_v3.db`)**
- `domains/identity` (Tabela `users`)
- `domains/banking` (Tabelas `transactions`, `accounts`, `categories`)
- `domains/credit` (Proxy via categorias na tabela `transactions`)
- `domains/imports` (Tabela `import_runs`, `staging_items` - Estrutura física mapeada no DB, mas subutilizada pelas Engines)

**Módulos utilizando SQLite V3 de forma adaptada (Sprint 7 - Engines)**
- `domains/investments/repositories/trade_repository.py`
  - Utiliza o Banco Oficial V3 (`trades`, `assets`, `accounts`), porém o faz convertendo *DataFrames/Mocks* em DTOs durante o tráfego da API, ignorando as *migrations* avançadas de consolidação do V3.
- `domains/investments/repositories/snapshot_repository.py`
  - Idem. Salva na tabela `position_snapshots` do V3, mas não lê de forma unificada com a camada analítica.
- `domains/investments/engines/*`
  - Todos os cálculos (TWR, MWR, Valuation) acontecem In-Memory com base em DTOs carregados do banco, ignorando as tabelas analíticas nativas do V3 (`asset_valuations`, `portfolio_snapshots`, `benchmarks`).

### 2. Duplicação de Arquitetura Identificada

**Duplicação 1: Valuations (MTM)**
- **Como está:** `PositionEngine` → `ValuationEngine` → Retorna `ValuationResult` (Memória) → Router.
- **Como deveria ser:** `PositionEngine` → Salva na tabela `asset_valuations` (V3) → Router lê do V3.

**Duplicação 2: Fechamento de Riqueza (Patrimônio)**
- **Como está:** `ValuationEngine` → `WealthEngine` → Retorna `WealthSummary` (Memória) → Router.
- **Como deveria ser:** `WealthEngine` → Salva na tabela `portfolio_snapshots` (V3) → Router lê do V3.

**Duplicação 3: Histórico de Dividendos**
- **Como está:** Calculado In-Memory pela `PerformanceEngine` somando cashflows por data.
- **Como deveria ser:** Inserido na tabela `dividends` do V3 pela `ValuationEngine` → Router lê do V3.

### 3. Matriz de Dependências (Árvore de Execução)

A árvore abaixo ilustra o acoplamento do Dashboard às Engines em Memória:

```mermaid
graph TD
    A[Router: /investments/dashboard] --> B[PortfolioDashboardService]
    B --> C[PortfolioApplicationService]
    C --> D[TradeRepository (Lê V3)]
    C --> E[SnapshotRepository (Lê V3)]
    C --> F[PositionEngine (Memória)]
    F --> G[ValuationEngine (Memória)]
    G --> H[WealthEngine (Memória)]
    C --> I[PerformanceEngine (Memória)]
    I --> B
    B --> A
```

**Correção Necessária:** O `PortfolioDashboardService` deve ler de `WealthRepository` e `PerformanceRepository` diretamente do V3.

### 4. Matriz de Riscos

| Risco | Componente | Descrição | Nível |
|---|---|---|---|
| **Risco de Gargalo de Memória** | `PerformanceEngine` | Recalcular todo o histórico In-Memory para cada GET é insustentável. O(N+M) estoura RAM. | 🔴 CRÍTICO |
| **Risco de Consistência** | `ValuationEngine` | O V3 tem a tabela `asset_valuations`. Não populá-la significa perder histórico imutável. | 🔴 CRÍTICO |
| **Risco Funcional** | `API / Frontend` | Endpoints reais requeridos pelo Front (ex: `/dashboard/summary-v2`) não existem, quebrando UI. | 🟠 ALTO |
| **Risco Operacional** | `Integrações` | Benchmarks hardcoded. Sem yfinance, o sistema simula preços incorretos. | 🟠 ALTO |

---

## ETAPA 2 — PLANO DE RECONCILIAÇÃO

**FASE R1 — Reconectar Infraestrutura Base ao V3**
- Criar `ValuationRepository`, `WealthRepository` e `DividendRepository` com SQLAlchemy Core.
- Modificar o `PortfolioApplicationService` para que, ao instanciar as Engines, os resultados sejam PERSISTIDOS nestas tabelas do V3 antes de serem retornados ao usuário.
- *Gate: Testes E2E de gravação. Auditoria de Banco.*

**FASE R2 — Otimização de Leitura (Desacoplar Dashboard das Engines)**
- Modificar `PortfolioDashboardService` para ler os agregados analíticos das tabelas do V3 (ex: `portfolio_snapshots`, `asset_valuations`) ao invés de acionar as Engines em realtime.
- Implementar as tabelas faltantes (se necessário) ou adaptar DTOs de leitura ao schema estrito V3.
- *Gate: Testes de Latência (Tempo de Resposta < 200ms). Auditoria Arquitetural.*

**FASE R3 — Reconstrução dos Endpoints Faltantes**
- Mapear os endpoints faltantes de Governança (`/governance/*`) para os Services correspondentes.
- Mapear endpoints de `/investments/evolution/*` e `/investments/dividends/*` usando as novas tabelas V3 popuadas na R1.
- *Gate: Validação de Contrato OpenAPI vs Frontend.*

**FASE R4 — Frontend Certification**
- Teste E2E massivo acessando a UI React/Next.js com massa de dados real para comprovar o funcionamento sem mock.
- *Gate: Aprovação visual do usuário final.*

---

## ETAPA 3 — INTEGRAÇÕES EXTERNAS (MASTER PLAN)

| Integração | Categoria | Status Atual | Prioridade | Impacto | Dependência |
|---|---|---|---|---|---|
| **yfinance (Yahoo Finance)** | Mercado | ❌ Inexistente | P1 | Alto (TWR/MWR depende de preços reais) | FASE R1 |
| **Banco Central (SGS/CDI)** | Mercado | ❌ Inexistente | P1 | Alto (Cálculo de Alpha vs CDI) | Nenhuma |
| **Tesouro Direto / Anbima** | Mercado | ❌ Inexistente | P2 | Médio (Valuation de Renda Fixa) | yfinance implementado |
| **Gemini AI API (Google)** | Inteligência | ❌ Inexistente | P2 | Alto (Categorização automática na Ingestão) | python-dotenv |
| **python-dotenv** | Infra / Security | ❌ Inexistente | P1 | Crítico (Segurança e injeção de keys) | Nenhuma |
| **Cache TTL (Preços Hist.)** | Infra | ⚠️ Parcial | P1 | Alto (Evitar Rate Limits do yfinance) | Banco V3 (tabela `benchmark_prices`) |
| **APScheduler / Celery** | Infra / Cron | ❌ Inexistente | P3 | Médio (Atualização background D-1) | FASE R1 concluída |

---

## ETAPA 4 — COMPATIBILIDADE COM FRONTEND CONTRACT

| Endpoint Exigido pelo Frontend | Módulo | Implementado | DTO Compatível | Observações |
|---|---|---|---|---|
| `GET /dashboard/summary-v2` | Banking / Dash | ❌ Ausente | - | Falta plugar Banking Router |
| `GET /dashboard/pacing-v2` | Banking / Dash | ❌ Ausente | - | Falta plugar Banking Router |
| `GET /dashboard/heatmap` | Banking / Dash | ❌ Ausente | - | Falta plugar Banking Router |
| `GET /dashboard/categories` | Banking / Dash | ❌ Ausente | - | Falta plugar Banking Router |
| `GET /investments/evolution/summary` | Wealth | ❌ Ausente | - | Engine já calcula, falta Router exportar |
| `GET /investments/evolution/history` | Wealth | ❌ Ausente | - | Idem. Faltam endpoints separados. |
| `GET /investments/dividends/history` | Wealth | ❌ Ausente | - | Engine calcula global, falta quebra mensal |
| `GET /investments/dividends/breakdown` | Wealth | ❌ Ausente | - | Falta endpoint `breakdown` por ticker |
| `GET /investments/asset/{ticker}` | Wealth | ❌ Ausente | - | Falta drill-down específico |
| `GET /investments/allocation` | Wealth | ⚠️ Parcial | ❌ Não | Formato Backend diferente do Frontend |
| `GET /catalog` | Admin | ❌ Ausente | - | Necessário para combobox de edição |

---

## ETAPA 5 — GOVERNANÇA

O domínio de Governança está gravemente defasado. A API expõe rotas dentro de `/import/` no módulo de Investments, mas falha em prover o painel central administrativo que o Frontend exige.

**O que falta no domínio `/governance/`:**

1. **Dashboard de Governança:** `GET /governance/imports` e `GET /governance/dashboard` não existem. O Frontend precisa da lista de `ImportRun` e métricas.
2. **Sistema de Aprovação (Staging):** O pipeline de importação atual importa tudo de uma vez. O Frontend prevê 3 etapas: `staging` -> `confirm` ou `rollback`. Faltam os endpoints `/governance/imports/{id}/staging-items`, `/confirm` e `/rollback`.
3. **Uploaders Segregados:** Faltam os endpoints específicos `/governance/import-pierre` e `/governance/import-myprofit` (hoje existe apenas genéricos `/import/cei` e `/open-finance`).
4. **Learning AI (Fase 8):** O motor inteiro de IA está ausente (`/governance/learning/metrics`, `/rules`).
5. **Reconciliação:** O endpoint de reconciliação está em `/investments/reconciliation`, o Frontend espera `/governance/reconciliations`. As rotas `/links/{id}/confirm` e `/reject` estão ausentes.

---
**Status do Gate:** 🔒 AGUARDANDO APROVAÇÃO DO USUÁRIO PARA INICIAR FASE R1.
