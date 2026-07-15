# Postman / Insomnia Collection

Este documento serve como mapa mental para criação rápida de uma Collection HTTP para testes do Frontend.

## Environment Variables
- `{{base_url}}` = `http://localhost:8000/api/v1/investments`
- `{{auth_token}}` = `Bearer jwt_token`

## Ordem Ideal de Execução (Happy Path)

### 1. Ingestão (Setup de Dados)
- **POST** `{{base_url}}/import/cei`
  - Body: `form-data` -> `file: trades.csv`
- **GET** `{{base_url}}/import/history`
  - Testa a paginação e verifica se o status está `SUCCESS`.

### 2. Validação Patrimonial
- **GET** `{{base_url}}/positions`
  - Checa a lista de ativos, garantindo que o array de `items` está preenchido e precificado.
- **GET** `{{base_url}}/reconciliation`
  - Checa se Ledger == Snapshot.

### 3. Exibição de Dashboard (Core)
- **GET** `{{base_url}}/dashboard`
  - Traz tudo englobado. O Frontend idealmente fará apenas essa chamada ao carregar a Home.
- **GET** `{{base_url}}/dashboard/summary`
  - Chamada granular caso o frontend deseje usar React Suspense / SWR independente.

### 4. Casos de Erro a Testar
- **DELETE** `{{base_url}}/import/invalid-uuid`
  - Deve retornar `404 Not Found`.
- **POST** `{{base_url}}/import/cei` (sem enviar o arquivo)
  - Deve retornar `422 Unprocessable Entity` (Validação do FastAPI).
