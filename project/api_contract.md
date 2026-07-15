# API Contract — FINANALYTICS V3

Documentação oficial da API após a Estabilização do Gate 10.11.

## DTOs Base e Response Models Globais
- `MessageResponse`: `{ "message": "string" }` - Padrão de respostas de deleção ou OK puro.

## Endpoints Consolidados e Catalogados

### DASHBOARD (GET /api/v1/investments/dashboard)
- `GET /dashboard` -> `Dict` com Summary, Allocation, Performance, Risk
- `GET /dashboard/summary` -> `PortfolioDashboardDTO`
- `GET /dashboard/allocation` -> `AllocationDashboardDTO`
- `GET /dashboard/performance` -> `PerformanceDashboardDTO`
- `GET /dashboard/risk` -> `RiskDashboardDTO`
> **Erros mapeados**: 500 (Erro Interno nas Engines)

### PORTFOLIO CORE (GET /api/v1/investments/...)
- `GET /portfolio` -> `WealthSummary`
- `GET /positions` -> `List[ValuationResult]`
- `GET /allocation` -> `List[AssetSummary]`
- `GET /institutions` -> `List[InstitutionSummary]`
- `GET /performance` -> `PerformanceSummary`
- `GET /performance/history` -> `PerformanceHistory`
- `GET /performance/analytics` -> `FinancialPerformanceDTO`

### INGESTÃO E AUDITORIA (POST/GET/DELETE /api/v1/investments/import)
- `POST /import/cei` (file: UploadFile) -> `ImportReport`
- `POST /import/open-finance` (file: UploadFile) -> `ImportReport`
- `GET /import/history` -> `List[ImportLogDTO]`
- `GET /import/{log_id}` -> `ImportLogDTO`
  - Erro mapeado: `404 Not Found` se não encontrar.
- `DELETE /import/{log_id}` -> `MessageResponse`
  - Erro mapeado: `404 Not Found` se não encontrar.
  - Erro mapeado: `409 Conflict` (ex: falha de soft delete se estivéssemos utilizando, ou regras).

### CONCILIAÇÃO
- `GET /reconciliation` -> `List[ReconciliationResult]`

Todas rotas do arquivo `router.py` cumprem o Swagger/OpenAPI v3 com descriptions, summary, response models bem definidos e tratamento de Response para Status Codes não-200.
