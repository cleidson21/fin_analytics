markdown_content = """# FRONTEND DEPENDENCY MAP - FASE 10B

Mapeamento de dependências e fluxo de dados do frontend gerado via engenharia reversa.

---

## 1. Dashboard Principal

**Página**: `src/app/page.tsx`
↓
**Componente**: `DashboardPage`
↓
**Hook**: Hooks nativos (`useEffect`, `useState`, `useMemo`) com `fetchFromAPI`
↓
**Store**: Estado local nativo
↓
**Endpoints**:
* `GET /dashboard/summary-v2`
* `GET /dashboard/pacing-v2`
* `GET /dashboard/heatmap`
* `GET /dashboard/categories`
* `GET /transactions?limit=5&sortBy=date&sortOrder=desc`
↓
**DTO Esperado**:
* `DashboardSummaryV2`
* `PacingV2`
* `HeatmapDay[]`
* `CategoryBreakdown[]`
* `TransactionListResponse`
↓
**Estado Renderizado**:
* `SummaryCards`
* `PacingCard`
* `CategoriesCard`
* `InstallmentCard`
* Gráficos (`LineChart`, `DeltaBadge`) e Tabelas recentes.

---

## 2. Assinaturas (Subscriptions)

**Página**: `src/app/subscriptions/page.tsx`
↓
**Componente**: `SubscriptionsPage`
↓
**Hook**: Hooks nativos (`useEffect`, `useState`) com `fetchFromAPI`
↓
**Store**: Estado local nativo
↓
**Endpoint**:
* `GET /dashboard/subscriptions?month={month}`
↓
**DTO Esperado**:
* `SubscriptionsSummary`
↓
**Estado Renderizado**:
* Cartões totalizadores de gastos fixos
* Tabela analítica de pacotes de assinaturas ativas

---

## 3. Transações (Transactions)

**Página**: `src/app/transactions/page.tsx`
↓
**Componente**: `TransactionsPageBody` (englobado por Suspense e layout próprio)
↓
**Hook**: Hooks nativos (`useEffect`, `useMemo`, `useState`) com `fetchFromAPI`
↓
**Store**: Estado local nativo (Filtros, Buscas, Paginação)
↓
**Endpoints**:
* `GET /catalog`
* `GET /transactions?{queryParams}`
* *Mutations detectadas via fetchFromAPI direto no submit (reclassificação/salvar).*
↓
**DTO Esperado**:
* `CatalogResponse`
* `TransactionListResponse`
↓
**Estado Renderizado**:
* Tabela principal de transações
* Modais de reclassificação / edição (via formulários iterativos em `TransactionsPageBody`)

---

## 4. Visão Geral de Patrimônio (Wealth Root)

**Página**: `src/app/wealth/page.tsx`
↓
**Componente**: `WealthPage` (Englobado por layout genérico de Wealth)
↓
**Hook**: `useGrowthData`, `useDividendsData`, `useAllocationData`, `useAlphaData`
↓
**Store**: `useWealthStore` (estado global via Zustand para período)
↓
**Endpoints**:
* `GET /investments/evolution/summary`
* `GET /investments/evolution/history`
* `GET /investments/dividends/history`
* `GET /investments/dividends/breakdown`
* `GET /investments/allocation`
* `GET /investments/positions`
↓
**DTO Esperado**:
* `PortfolioEvolutionSummary`
* `PortfolioEvolutionPoint[]`
* `DividendHistory[]`
* `DividendBreakdown[]`
* `AssetAllocation[]`
* `PositionDetail[]`
↓
**Estado Renderizado**:
* `WealthPeriodToggle`
* Multiplos `WealthKpiCard`
* `WealthChartCard`
* `RechartsPie` (gráfico consolidado na raiz)

---

## 5. Alocação de Ativos (Allocation)

**Página**: `src/app/wealth/allocation/page.tsx`
↓
**Componente**: `AllocationPage`
↓
**Hook**: `useAllocationData`
↓
**Store**: Não há consumo direto de store neste escopo específico
↓
**Endpoints**:
* `GET /investments/allocation`
* `GET /investments/positions`
↓
**DTO Esperado**:
* `AssetAllocation[]`
* `PositionDetail[]`
↓
**Estado Renderizado**:
* `DiversificationGauge`
* `WealthKpiCard`
* `AllocationDonut`
* `AllocationTreemap`
* `WealthTable`

---

## 6. Ativo Específico (Asset Ticker Dinâmico)

**Página**: `src/app/wealth/asset/[ticker]/page.tsx`
↓
**Componente**: `AssetDetail`
↓
**Hook**: Nativos (`useParams`, `useRouter`, `useEffect`) invocando fetch API do Browser nativa (*Hardcoded*)
↓
**Store**: Estado local nativo
↓
**Endpoint**:
* `GET http://127.0.0.1:8000/api/v1/investments/asset/{ticker}`
↓
**DTO Esperado**:
* `AssetDetails`
↓
**Estado Renderizado**:
* `WealthKpiCard` para cotação e variação
* `WealthChartCard` e `BarChart` para gráficos individuais de histórico
* `ClipboardList` para detalhamento de metadados do ativo

---

## 7. Dividendos (Dividends)

**Página**: `src/app/wealth/dividends/page.tsx`
↓
**Componente**: `DividendsPage`
↓
**Hook**: `useDividendsData`
↓
**Store**: Consumo implícito de período se associado à raiz, mas encapsulado no custom hook
↓
**Endpoints**:
* `GET /investments/dividends/history`
* `GET /investments/evolution/summary`
* `GET /investments/dividends/breakdown`
↓
**DTO Esperado**:
* `DividendHistory[]`
* `PortfolioEvolutionSummary`
* `DividendBreakdown[]`
↓
**Estado Renderizado**:
* `WealthKpiCard` (Sumários e Yield)
* `DividendFlowChart`
* `DividendYoYChart`
* Múltiplos `WealthTable` para histórico descritivo

---

## 8. Evolução (Evolution / Alpha)

**Página**: `src/app/wealth/evolution/page.tsx`
↓
**Componente**: `EvolutionPage`
↓
**Hook**: `useAlphaData`
↓
**Store**: `useWealthStore` (period)
↓
**Endpoints**:
* `GET /investments/evolution/history`
* `GET /investments/evolution/summary`
↓
**DTO Esperado**:
* `PortfolioEvolutionPoint[]`
* `PortfolioEvolutionSummary`
↓
**Estado Renderizado**:
* `WealthPeriodToggle`
* `WealthKpiCard`
* `AdvancedAlphaChart` (Comparações Ibov, CDI, etc)
* `CashflowBarChart`
* `WealthTable`

---

## 9. Patrimônio Líquido (Patrimonio)

**Página**: `src/app/wealth/patrimonio/page.tsx`
↓
**Componente**: `PatrimonioPage`
↓
**Hook**: `useGrowthData`, `useAllocationData`
↓
**Store**: `useWealthStore` (period)
↓
**Endpoints**:
* `GET /investments/evolution/summary`
* `GET /investments/evolution/history`
* `GET /investments/allocation`
* `GET /investments/positions`
↓
**DTO Esperado**:
* `PortfolioEvolutionSummary`
* `PortfolioEvolutionPoint[]`
* `AssetAllocation[]`
* `PositionDetail[]`
↓
**Estado Renderizado**:
* `WealthPeriodToggle`
* Multiplos `WealthKpiCard` (Progresso de metas, Saldo)
* `GrowthComposedChart` (Gráfico misto de área e barras)
* `WealthTable`

"""

with open(r'C:\Users\Cleidson\Pictures\fin_analytics_v2\FRONTEND_DEPENDENCY_MAP.md', 'w', encoding='utf-8') as f:
    f.write(markdown_content)
