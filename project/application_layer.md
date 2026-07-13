# Application Service Layer

A camada de Application Services foi implementada para atuar como o maestro das regras de negócio encapsuladas nos Engines e Services do domínio. Ela cumpre os princípios do Domain-Driven Design (DDD) e separa a lógica transacional da camada de roteamento (Transport Layer/Router) e das complexidades de baixo nível das Engines financeiras.

## Estrutura da Camada
- `PortfolioApplicationService`: Orquestra o cálculo da posição atual, valuation e evolução histórica através do acionamento de `PositionEngine`, `ValuationEngine`, `WealthEngine`, `FinancialAnalyticsEngine` e `HistoryService`.
- `ImportApplicationService`: Orquestra todo o fluxo de ingestão de arquivos (B3, Kinvo, Clear), repassando ao `ImportService`, registrando os metadados de sucesso ou erro (via `ImportLogRepository`), e posteriormente acionando o `ReconciliationService`.
- `MarketApplicationService`: Centraliza interações puramente informativas sobre mercado de capitais (consultar os serviços e repositórios históricos ou ativos em cache).

## Vantagens Alcançadas
- O FastAPI (via `router.py`) foi limpo; agora apenas valida DTOs e repassa o controle.
- Regras de orquestração ("chamar A e, dependendo do resultado, chamar B") saíram do `router.py` e foram abrigadas na camada Application.
- A manutenibilidade do fluxo de negócio aumentou drasticamente.
