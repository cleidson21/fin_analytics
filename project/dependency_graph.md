# Dependency Graph — Gate 10.5

Data: 2026-07-13

## Grafo Completo de Dependências

```mermaid
flowchart TD

    subgraph DATA["Dados de Entrada"]
        CSV_BENCH["CSV Benchmarks<br/>(ibov/cdi/ifix/ipca/sp500/idiv)"]
        CSV_TRADES["Upload do Usuário<br/>(CEI / Open Finance / OFX)"]
        DB[("SQLite/PostgreSQL<br/>(trades, snapshots, import_logs)")]
    end

    subgraph PARSERS["Parsers"]
        B3Parser["B3MovementsParser"]
        CSVParser["CSVTradeParser"]
        OFParser["OpenFinanceParser"]
        OFXParser["OFXParser"]
    end

    subgraph REPOS["Repositories"]
        TradeRepo["TradeRepository"]
        SnapRepo["SnapshotRepository"]
        ImportLogRepo["ImportLogRepository"]
        MarketRepo["MarketDataRepository"]
    end

    subgraph SERVICES["Services"]
        ImportSvc["ImportService"]
        ReconcSvc["ReconciliationService"]
        MarketSvc["MarketDataService"]
    end

    subgraph ENGINES["Engines"]
        PosEng["PositionEngine"]
        ValEng["ValuationEngine"]
        WealthEng["WealthEngine"]
        PerfEng["PerformanceEngine"]
    end

    subgraph API["FastAPI Router"]
        RTR["/api/v1/investments/*"]
    end

    subgraph FRONTEND["Frontend"]
        Hook_Perf["usePerformanceData"]
        Hook_Alpha["useAlphaData"]
        Hook_Growth["useGrowthData"]
        Hook_Import["useImportHistory"]
    end

    subgraph PAGES["Pages"]
        PagePerf["/wealth/performance"]
        PageEvol["/wealth/evolution"]
        PageImport["/wealth/import"]
    end

    %% Data → Parsers
    CSV_TRADES --> B3Parser
    CSV_TRADES --> CSVParser
    CSV_TRADES --> OFParser
    CSV_TRADES --> OFXParser

    %% Parsers → ImportService
    B3Parser --> ImportSvc
    CSVParser --> ImportSvc
    OFParser --> ImportSvc
    OFXParser --> ImportSvc

    %% ImportService → Repos
    ImportSvc --> TradeRepo
    ImportSvc --> ImportLogRepo

    %% Repos → DB
    TradeRepo --> DB
    SnapRepo --> DB
    ImportLogRepo --> DB

    %% CSV Benchmarks → MarketDataRepository (Singleton, in-memory)
    CSV_BENCH --> MarketRepo

    %% MarketRepo → MarketDataService
    MarketRepo --> MarketSvc

    %% DB/Repos → Engines
    TradeRepo --> PosEng
    SnapRepo --> PosEng
    PosEng --> ValEng
    ValEng --> WealthEng
    WealthEng --> PerfEng
    MarketSvc --> PerfEng

    %% ReconciliationService
    TradeRepo --> ReconcSvc
    SnapRepo --> ReconcSvc
    PosEng --> ReconcSvc

    %% Engines → Router
    PosEng --> RTR
    ValEng --> RTR
    WealthEng --> RTR
    PerfEng --> RTR
    ReconcSvc --> RTR
    ImportLogRepo --> RTR
    ImportSvc --> RTR

    %% Router → Frontend Hooks
    RTR --> Hook_Perf
    RTR --> Hook_Alpha
    RTR --> Hook_Growth
    RTR --> Hook_Import

    %% Hooks → Pages
    Hook_Perf --> PagePerf
    Hook_Alpha --> PageEvol
    Hook_Growth --> PageEvol
    Hook_Import --> PageImport
```

## Verificação de Dependências Circulares

| Módulo A | Módulo B | Circular? | Detalhe |
|----------|----------|-----------|---------|
| `PerformanceEngine` | `PositionEngine` | Não | PE importa PosEng internamente (sentido único) |
| `Router` | `Engines` | Não | Router chama engines, engines não conhecem o router |
| `Services` | `Repositories` | Não | Services dependem de Repos, nunca o contrário |
| `MarketDataService` | `MarketDataRepository` | Não | Service usa Repo como dependência |
| `PerformanceEngine` | `MarketDataService` | Não | PE importa MDS localmente (sentido único) |

**Conclusão**: Nenhuma dependência circular detectada no grafo atual.

## Camadas de Abstração

```
┌──────────────────────────────────────────────────────┐
│  FRAMEWORK (FastAPI, SQLAlchemy, Pandas)             │
├──────────────────────────────────────────────────────┤
│  INTERFACE ADAPTERS (Router)                         │
├──────────────────────────────────────────────────────┤
│  SERVICES (ImportService, MarketDataService,         │
│            ReconciliationService)                    │
├──────────────────────────────────────────────────────┤
│  ENGINES (PositionEngine, ValuationEngine,           │
│           WealthEngine, PerformanceEngine)           │
├──────────────────────────────────────────────────────┤
│  REPOSITORIES (TradeRepo, SnapRepo, MarketRepo,      │
│                ImportLogRepo)                        │
├──────────────────────────────────────────────────────┤
│  ENTITIES / DTOs (TradeDTO, PerformanceHistory,      │
│                   MarketDataPoint, ...)              │
└──────────────────────────────────────────────────────┘
```

As setas de dependência sempre apontam de cima para baixo (camadas superiores dependem de inferiores). Nenhuma camada inferior conhece camadas superiores.
