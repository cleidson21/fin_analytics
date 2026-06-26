# FINANALYTICS V3 — INVESTMENTS CONTRACT
> Documento crítico de mapeamento. Deve ser concluído antes da implementação da Fase 6.
> Define a relação exata entre o schema de banco de dados, a API e o Frontend no contexto de Investimentos.

---

## 1. Mapeamento de Entidades Core

### 1.1 Assets
| Banco de Dados (Schema V3) | API Endpoint Esperado | Hook Frontend | Componente Consumidor |
|---|---|---|---|
| `assets` | `GET /api/v1/investments/asset/{ticker}` | N/A (inline fetch via api.ts) | `AssetDetailPage` |

### 1.2 Asset Types / Classes
| Banco de Dados (Schema V3) | API Endpoint Esperado | Hook Frontend | Componente Consumidor |
|---|---|---|---|
| `asset_class` (Enum/Tabela) | `GET /api/v1/investments/allocation` | `useAllocationData` | `AllocationPage`, `AllocationChart`, `AllocationDonut`, `AllocationTreemap` |

### 1.3 Exchanges / Market Data
| Banco de Dados (Schema V3) | API Endpoint Esperado | Hook Frontend | Componente Consumidor |
|---|---|---|---|
| `asset_prices` | `GET /api/v1/investments/asset/{ticker}` (dentro do objeto `market_data.history`) | N/A (inline fetch) | `AssetHistoryChart`, `AssetDetailPage` |

### 1.4 Benchmarks
| Banco de Dados (Schema V3) | API Endpoint Esperado | Hook Frontend | Componente Consumidor |
|---|---|---|---|
| `benchmarks`, `benchmark_prices`, `benchmark_snapshots` | `GET /api/v1/investments/evolution/history` | `useGrowthData`, `useAlphaData` | `AdvancedAlphaChart`, `EvolutionPage`, `AllocationPage` |

### 1.5 Positions
| Banco de Dados (Schema V3) | API Endpoint Esperado | Hook Frontend | Componente Consumidor |
|---|---|---|---|
| `asset_positions` (Calculado via WAC pelo PositionEngine) | `GET /api/v1/investments/positions` | `useAllocationData`, `usePositionsAdmin` | `PatrimonioPage`, `PositionsTab`, `PositionEditDialog` |
| `asset_positions` (CRUD admin) | `GET/PUT /api/v1/governance/positions` | `usePositionsAdmin`, `usePositionAdmin` | `PositionsTab`, `PositionEditDialog` |

### 1.6 Dividends
| Banco de Dados (Schema V3) | API Endpoint Esperado | Hook Frontend | Componente Consumidor |
|---|---|---|---|
| `dividends` | `GET /api/v1/investments/dividends/history`, `GET /api/v1/investments/dividends/breakdown` | `useDividendsData` | `DividendsPage`, `DividendFlowChart`, `DividendYoYChart` |
| `dividends` (CRUD admin) | `GET/PUT /api/v1/governance/dividends` | `useDividendsAdmin`, `useDividendAdmin` | `DividendsTab`, `DividendEditDialog` |

### 1.7 Valuations / Portfolio Snapshots
| Banco de Dados (Schema V3) | API Endpoint Esperado | Hook Frontend | Componente Consumidor |
|---|---|---|---|
| `asset_valuations`, `portfolio_snapshots` (Calculados via TWR pelo WealthEngine) | `GET /api/v1/investments/evolution/summary`, `GET /api/v1/investments/evolution/history` | `useGrowthData` | `EvolutionPage`, `GrowthComposedChart`, `DiversificationGauge` |

---

## 2. Regras de Processamento Obrigatórias

- **PositionEngine (WAC)**: O Backend DEVE recalcular o Preço Médio (WAC) sempre que eventos transacionais ou corporate actions modificarem a posição. Não deve ser editado diretamente sem trigger.
- **WealthEngine (TWR)**: A rentabilidade histórica (TWR) DEVE considerar os aportes/retiradas para não distorcer o rendimento percentual do mês.
- **DividendEngine (YOC)**: O `Yield on Cost` deve ser exposto considerando os proventos dos últimos 12 meses sobre o custo médio investido da posição atual.

---

## 3. Estruturas Complexas Esperadas pelo Frontend

O endpoint `GET /api/v1/investments/asset/{ticker}` tem o contrato mais complexo do sistema. O Backend deve montar o seguinte JSON:

```typescript
{
  position: { 
    ticker: string, 
    quantidade: number, 
    preco_medio: number, 
    valor_investido: number, 
    preco_atual: number, 
    valor_atual: number, 
    ganho: number, 
    asset_class: string, 
    asset_subclass: string, 
    peso: number 
  },
  market_data: { 
    available: boolean, 
    history: Array<{ date: string, close: number, adjusted_close: number, volume: number }> 
  },
  indicators: { 
    available: boolean, 
    indicators: Record<string, string> // Ex: { "P/VPA": "0.95", "Volatilidade 12m": "15%" }
  },
  dividends: { 
    items: Array<Dividend>, 
    kpis: { total: number, last_12m: number, yoc: number } 
  },
  timeline: Array<{ date: string, title: string, description: string, type: string }>
}
```
