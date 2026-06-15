import os
import re

base_dir = r"C:\Users\Cleidson\Pictures\fin_analytics_v2"
frontend_map_path = os.path.join(base_dir, "FRONTEND_DEPENDENCY_MAP.md")

with open(frontend_map_path, 'r', encoding='utf-8') as f:
    frontend_map = f.read()

# We will manually map the endpoints based on the frontend map and backend code
# Since parsing FastAPI perfectly is complex, we will generate the known contract structure
# using a python script to write out the markdown file.

markdown_content = """# API CONTRACT FREEZE - FASE 10D

Documentação de contratos obrigatórios (Swagger/OpenAPI) cruzando o Backend FastAPI com o Frontend (FinAnalytics V2).
Gerado a partir do código backend e do documento `FinAnalytics V2 - localhost_8000_docs.pdf`.

---

## 1. Dashboard & Resumos

### `GET /dashboard/summary-v2`
* **Request**: `month` (query param, opcional)
* **Response**: `DashboardSummaryV2`
* **Status Codes**: `200 OK`, `401 Unauthorized`
* **Consumidores**:
  * **Hook**: `fetchFromAPI` (nativo via `useEffect`)
  * **Componente**: `DashboardPage`, `SummaryCards`
  * **Página**: `src/app/page.tsx`

### `GET /dashboard/pacing-v2`
* **Request**: `month` (query param, opcional)
* **Response**: `PacingV2`
* **Status Codes**: `200 OK`, `401 Unauthorized`
* **Consumidores**:
  * **Hook**: `fetchFromAPI`
  * **Componente**: `DashboardPage`, `PacingCard`
  * **Página**: `src/app/page.tsx`

### `GET /dashboard/heatmap`
* **Request**: `month` (query param, opcional)
* **Response**: `HeatmapDay[]`
* **Status Codes**: `200 OK`
* **Consumidores**:
  * **Hook**: `fetchFromAPI`
  * **Componente**: `DashboardPage`, `LineChart`
  * **Página**: `src/app/page.tsx`

### `GET /dashboard/categories`
* **Request**: `month` (query param)
* **Response**: `CategoryBreakdown[]`
* **Status Codes**: `200 OK`
* **Consumidores**:
  * **Hook**: `fetchFromAPI`
  * **Componente**: `DashboardPage`, `CategoriesCard`
  * **Página**: `src/app/page.tsx`

### `GET /dashboard/subscriptions`
* **Request**: `month` (query param)
* **Response**: `SubscriptionsSummary`
* **Status Codes**: `200 OK`
* **Consumidores**:
  * **Hook**: `fetchFromAPI`
  * **Componente**: `SubscriptionsPage`
  * **Página**: `src/app/subscriptions/page.tsx`

---

## 2. Transações e Catálogo

### `GET /transactions`
* **Request**: `limit`, `sortBy`, `sortOrder`, `page`, etc. (query params)
* **Response**: `TransactionListResponse` (Paginado)
* **Status Codes**: `200 OK`, `401 Unauthorized`
* **Consumidores**:
  * **Hook**: `useTransactions` (via `useAdminCRUD` ou nativo)
  * **Componente**: Tabela de Transações, `TransactionsPageBody`
  * **Página**: `src/app/transactions/page.tsx`

### `GET /catalog`
* **Request**: Nenhum (parâmetros de paginação padrão)
* **Response**: `CatalogResponse`
* **Status Codes**: `200 OK`
* **Consumidores**:
  * **Hook**: `fetchFromAPI`
  * **Componente**: Modais de edição/classificação
  * **Página**: `src/app/transactions/page.tsx`

---

## 3. Wealth (Evolução e Rentabilidade)

### `GET /investments/evolution/summary`
* **Request**: `period` (query param, ex: "YTD", "1Y", "ALL")
* **Response**: `PortfolioEvolutionSummary`
* **Status Codes**: `200 OK`, `401 Unauthorized`, `500 Internal Server Error`
* **Consumidores**:
  * **Hook**: `useGrowthData`, `useDividendsData`, `useAlphaData`
  * **Componente**: `WealthKpiCard`
  * **Página**: `src/app/wealth/page.tsx`, `src/app/wealth/patrimonio/page.tsx`, `src/app/wealth/evolution/page.tsx`

### `GET /investments/evolution/history`
* **Request**: `period` (query param)
* **Response**: `PortfolioEvolutionPoint[]`
* **Status Codes**: `200 OK`
* **Consumidores**:
  * **Hook**: `useGrowthData`, `useAlphaData`
  * **Componente**: `GrowthComposedChart`, `AdvancedAlphaChart`
  * **Página**: `src/app/wealth/page.tsx`, `src/app/wealth/patrimonio/page.tsx`, `src/app/wealth/evolution/page.tsx`

---

## 4. Wealth (Alocação e Posições)

### `GET /investments/allocation`
* **Request**: `period` (opcional)
* **Response**: `AssetAllocation[]`
* **Status Codes**: `200 OK`
* **Consumidores**:
  * **Hook**: `useAllocationData`
  * **Componente**: `AllocationDonut`, `AllocationTreemap`, `DiversificationGauge`
  * **Página**: `src/app/wealth/allocation/page.tsx`, `src/app/wealth/page.tsx`, `src/app/wealth/patrimonio/page.tsx`

### `GET /investments/positions`
* **Request**: `period` (opcional)
* **Response**: `PositionDetail[]`
* **Status Codes**: `200 OK`
* **Consumidores**:
  * **Hook**: `useAllocationData`, `usePositionsAdmin`
  * **Componente**: `WealthTable`, `PositionsTab`
  * **Página**: `src/app/wealth/allocation/page.tsx`

---

## 5. Wealth (Dividendos)

### `GET /investments/dividends/history`
* **Request**: Nenhum / `period`
* **Response**: `DividendHistory[]`
* **Status Codes**: `200 OK`
* **Consumidores**:
  * **Hook**: `useDividendsData`
  * **Componente**: `DividendFlowChart`, `DividendYoYChart`
  * **Página**: `src/app/wealth/dividends/page.tsx`, `src/app/wealth/page.tsx`

### `GET /investments/dividends/breakdown`
* **Request**: Nenhum / `period`
* **Response**: `DividendBreakdown[]`
* **Status Codes**: `200 OK`
* **Consumidores**:
  * **Hook**: `useDividendsData`
  * **Componente**: `WealthTable`
  * **Página**: `src/app/wealth/dividends/page.tsx`, `src/app/wealth/page.tsx`

---

## 6. Dinâmicos (Ativo Específico)

### `GET /investments/asset/{ticker}`
* **Request**: Path param `ticker` (string)
* **Response**: `AssetDetails`
* **Status Codes**: `200 OK`, `404 Not Found`
* **Consumidores**:
  * **Hook**: Nativo (`fetch` direto)
  * **Componente**: `AssetDetail`
  * **Página**: `src/app/wealth/asset/[ticker]/page.tsx`

---

## 7. Administração & Autenticação

### `POST /token`
* **Request**: `username`, `password` (Form Data / OAuth2PasswordRequestForm)
* **Response**: `Token` (`access_token`, `token_type`)
* **Status Codes**: `200 OK`, `401 Unauthorized`
* **Consumidores**:
  * **Hook**: `useAuth`
  * **Componente**: Login Form
  * **Página**: Contexto Global (`AuthContext.tsx`)

### `GET /me`
* **Request**: Bearer Token (Header)
* **Response**: `UserInDB` / `UserBase`
* **Status Codes**: `200 OK`, `401 Unauthorized`
* **Consumidores**:
  * **Hook**: `useCurrentUser`, `useAuth`
  * **Componente**: `AuthRequiredCard`, `TopNav`
  * **Página**: Layouts Globais
"""

out_path = os.path.join(base_dir, "API_CONTRACT_FREEZE.md")
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(markdown_content)
