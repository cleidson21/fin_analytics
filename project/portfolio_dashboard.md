# Portfolio Dashboard Layer

A camada do Portfolio Dashboard é a apresentação final (Presentation Layer / View Model) dos dados calculados pelas complexas Engines de Domínio do FINANALYTICS.

## Objetivo
Atuar exclusivamente como orquestradora e agregadora da inteligência financeira provida pela Application Layer, mapeando resumos estruturados para facilitar a serialização e exposição REST. Nenhuma matemática acontece no Dashboard Service, as Engines mantêm o monopólio das regras de negócio.

## Estrutura de DTOs
O `backend/domains/investments/dashboard_dto.py` padroniza o output analítico em quatro facetas:
1. **PortfolioDashboardDTO (Summary)**: Agrega saldo patrimonial atual, ganho de capital (lucro e % unrealized), métricas avançadas (MWR, TWR) e rácios de risco (Sharpe, Sortino, Alpha, Beta).
2. **AllocationDashboardDTO (Allocation)**: Exibe como o capital está segmentado (Por Ativo, Classe, Instituição).
3. **PerformanceDashboardDTO (Performance)**: Simplifica os retornos temporais (rolling returns, mensal, anual) e inclui a performance contra o benchmark.
4. **RiskDashboardDTO (Risk)**: Destila indicadores puramente estatísticos e de rebaixamento de carteira (Drawdowns e Volatilidade).

## Serviços
O `PortfolioDashboardService` consome o `PortfolioApplicationService`, recebe os requests, e simplesmente empacota em DTOs a saída das Engines de Riqueza, Posição, Valuation, e Análise Financeira.
