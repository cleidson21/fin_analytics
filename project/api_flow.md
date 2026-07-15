# API Flow (Data Pipeline)

Este documento elucida o caminho que um dado percorre desde a requisição no Frontend até o banco de dados.

## Fluxograma Textual Top-Down

```text
1. [Frontend] 
   O aplicativo React/Next.js invoca uma requisição HTTP REST via Fetch ou Axios (ex: `GET /api/v1/investments/dashboard`).
      ↓
2. [Router (FastAPI)] 
   Recebe o Request HTTP, valida a tipagem dos Query Params e resolve as Dependências (Injeção de BD). Se o Payload for inválido, devolve `422 Unprocessable Entity`. Se passar, delega ao Dashboard Service.
      ↓
3. [Portfolio Dashboard Service] 
   A camada de Apresentação ("Dumb View"). Ela ignora matemática, e simplesmente coordena os DTOs para orquestrar o Frontend. Ela passa as chamadas para a camada de Aplicação.
      ↓
4. [Portfolio Application Service] 
   O Cérebro orquestrador (Application Layer). É responsável por chamar as Múltiplas Engines e transacionar o workflow de negócio.
      ↓
5. [Engines de Domínio] 
   `PositionEngine`, `ValuationEngine`, `WealthEngine`, `HistoryService`, `FinancialAnalyticsEngine`. 
   Executam as fórmulas matemáticas complexas (MWR, CAGR, Volatilidade) 100% In-Memory de forma otimizada.
      ↓
6. [Repositories] 
   Abstrações do banco de dados (Ex: `TradeRepository`, `SnapshotRepository`). Realizam mapeamento Objeto-Relacional (ORM) resgatando do SQLite In-Memory.
      ↓
7. [SQLite In-Memory] 
   A persistência subjacente, retornando os Datasets brutos de volta pela cadeia, até serem empacotados nos DTOs que chegam ao Frontend.
```
