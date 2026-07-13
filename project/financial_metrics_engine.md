# Motor de Métricas Financeiras — FINANALYTICS V3

Data: 2026-07-13

A **FinancialAnalyticsEngine** preenche o papel de camada final no fluxo de dados de investimentos (Clean Architecture). Ela recebe o output de histórico financeiro gerado pela orquestração do `HistoryService` e injeta a profundidade analítica necessária.

## Encapsulamento
Conforme estabelecido no Gate 10.8, a engine vive fora do fluxo vital da `PositionEngine`. Nenhuma operação aqui recalcula posições ou gera latência de trade. As métricas avançam em um único passe linear O(N) no array de pontos da história (que já possui no máximo ~120 ou 240 nós temporais, independente se o cliente tinha 1.000.000 de ordens em banco).

## Principais Outputs DTO
O `FinancialPerformanceDTO` entrega:
- Rentabilidade Líquida Verdadeira (`twr` e `mwr`).
- Trajetória de Risco (`volatility`, `sharpe`, `sortino`, `current_drawdown`, `max_drawdown`).
- Janelas Móveis (`rolling_returns`).
- Correlações de Mercado (`beta`, `alpha`, `tracking_error`, `information_ratio`).

Os retornos baseiam-se numa extração assíncrona O(log N) aos históricos do Benchmark (`IBOV` modelado nativamente) através do `HistoricalPriceService`.
