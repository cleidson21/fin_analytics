# Application Factory Design

Para viabilizar a Injeção de Dependências (DI) e garantir que a criação da árvore de objetos do domínio seja tratada de forma robusta e otimizada, adotamos o padrão de projeto `Factory` através do `ApplicationFactory`.

## Padrões Adotados
- **Singleton + Lazy Initialization:** A classe abstrata `ApplicationFactory` provê métodos estáticos com a função auxiliar `_get_or_create`. Ela garante que as engines e serviços sejam instanciados uma única vez na aplicação e apenas sob demanda.
- **Gerenciamento Seguro de Concorrência (Thread-Safety):** Alguns dos Repositórios da nossa aplicação, notavelmente o `MarketDataRepository` e o `HistoricalPriceRepository`, mantêm estruturas de Cache locais em memória (Stateful). Quando inicializados ou populados num ambiente assíncrono multi-threaded do `Uvicorn` ou `FastAPI`, eles podem sofrer Condições de Corrida. Por isso, a inicialização dos dados neles ocorre de forma Thread-Safe através do uso do módulo nativo `threading.Lock`.

## A Árvore de Instanciação
Quando o Router chama:
`app = ApplicationFactory.get_portfolio_application_service()`

A seguinte árvore é gerada (e retida em cache):
```
PortfolioApplicationService
 ├── PositionEngine
 ├── ValuationEngine
 │    └── HistoricalPriceService
 │         └── HistoricalPriceRepository (Singleton com Lock)
 ├── WealthEngine
 ├── FinancialAnalyticsEngine
 │    └── HistoricalPriceService
 └── HistoryService
      ├── PositionEngine
      └── ValuationEngine
```

O ApplicationFactory atua como o **IoC Container** da nossa plataforma, simplificando os testes unitários via injeção customizada, e servindo o router do FastAPI para uso em produção de maneira altamente acoplada mas arquiteturalmente livre.
