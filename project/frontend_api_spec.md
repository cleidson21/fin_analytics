# Frontend API Specification

Especificação completa para consumo da REST API do FINANALYTICS V3 pelo ecossistema Frontend (Web, Mobile, Next.js).

## Informações Base
- **Base URL**: `/api/v1/investments`
- **Content-Type**: `application/json` (Exceto POST de Uploads que são `multipart/form-data`)
- **Autenticação**: Bearer Token no cabeçalho `Authorization: Bearer <token>` (se ativado no Gateway).

## Paginação
Rotas que retornam listas (ex: `/import/history`, `/positions`, `/allocation`) foram envelopadas utilizando o padrão `PaginatedResponse`.
```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 50
}
```
**Parâmetros de Query:** `?page=1&page_size=50`

## Endpoints

### 1. Dashboard Global
`GET /dashboard`
- **Descrição**: Traz todo o panorama financeiro de uma vez. Ideal para o initial load (reduz RTT).
- **Response**: `DashboardFullDTO` (Contém summary, allocation, performance, risk).
- **Exemplo**:
```json
{
  "summary": { "current_wealth": 22930.0, "twr": 12.5 },
  "allocation": { "by_asset": [...] },
  "performance": { "monthly_return": 1.2 },
  "risk": { "volatility": 15.2 }
}
```

### 2. Importação e Ingestão
`POST /import/cei`
- **Descrição**: Envia arquivo B3.
- **Body**: `multipart/form-data` (key: `file`)
- **Response**: `ImportReport` (200 OK)

`GET /import/history`
- **Descrição**: Histórico paginado das importações.
- **Filtros (Query)**: `?status=SUCCESS&parser=CEI`

`DELETE /import/{log_id}`
- **Descrição**: Desfaz uma importação.
- **Response**: `{ "message": "Deletado com sucesso" }`

### 3. Core Financeiro
`GET /portfolio` -> Traz a fotomontagem (`WealthSummary`).
`GET /positions` -> Posições paginadas e validadas Mark-to-Market (`ValuationResult`).
`GET /reconciliation` -> Lista de conciliação.
`GET /performance/analytics` -> Traz TWR, MWR, Sharpe, Beta, Max Drawdown via `FinancialPerformanceDTO`.

## Tratamento de Erros
Leia também o `error_catalog.md`. O frontend deve escutar chamadas não-2xx e apresentar Toast Messages usando a chave `detail` do Response.
Ex: HTTP 404
```json
{
  "detail": "Log não encontrado"
}
```
