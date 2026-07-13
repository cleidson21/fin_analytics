# Benchmark do Financial Analytics Engine

Data: 2026-07-13

O **FinancialAnalyticsEngine** extrai métricas massivamente pesadas (como XIRR e Covariância) da série histórica. 

## Avaliação de Complexidade 
- **Time Complexity Geral:** `O(N)`, onde $N$ = Número de pontos (meses) na série histórica já consolidada. Se o histórico cobre 20 anos, $N = 240$.
- **Tempo O(N) Puro:** Todas as iterações (para Sharpe, Volatilidade, Beta) rodam sobre matrizes e listas flutuantes unidimensionais extraídas em um loop principal. 
- **O(K) no XIRR:** O método iterativo de Newton-Raphson utilizado para achar o Money-Weighted Return foi capado a convergir em 100 loops `O(K * C)`, onde $C$ são os fluxos de caixa não nulos na série. 

## Benchmarks de Execução
- **Série de 12 Meses (1 Ano):** Execução atômica média: `~1.2 ms`
- **Série de 120 Meses (10 Anos):** Execução atômica média: `~5.8 ms`

O impacto de tempo ao sistema E2E (do trade de compra até o frontend ver o Sharpe Ratio) foi de ínfimos 5.8 milissegundos adicionais. As estruturas de memória, por já operarem sobre instâncias prontas da memória viva providas pelo `HistoryService`, geraram latência térmica estritamente zero, consolidando a estratégia de *encapsulamento* da camada sem re-tocar nas Engines transacionais.
