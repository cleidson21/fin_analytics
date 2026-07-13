# Benchmark Report — Gate 10.5

Data: 2026-07-13

## Configuração do Ambiente
- Python 3.14
- Sem banco de dados real (testes em memória pura)
- Hardware: Ambiente local Windows

## Resultados do Benchmark por Número de Trades

| Trades | Tempo (ms) | RAM Pico (KB) | Posições | Obs |
|-------:|-----------:|--------------:|:--------:|-----|
|     10 |       1.15 |         37.14 |        5 | Muito rápido |
|    100 |       2.17 |         34.20 |        5 | Linear |
|  1.000 |      32.33 |         44.10 |        5 | Aceitável |
| 10.000 |     142.16 |        214.72 |        5 | Bom para produção |

## Análise por Engine

### PositionEngine
- **Complexidade**: O(N log N) — Sort inicial de trades + O(N) de acúmulo
- **Bottleneck principal**: Sort por `(trade_date, created_at)` via `list.sort()`
- **RAM**: Apenas a lista de trades em memória — cresce linearmente
- **Observação**: Resultado determinístico garantido pelo sort duplo

### ValuationEngine
- **Complexidade**: O(P) onde P = número de posições
- **Bottleneck**: Lookup de `market_prices` por ticker — O(1) via dict
- **Observação**: Totalmente pura; nenhuma dependência de I/O

### WealthEngine
- **Complexidade**: O(P) onde P = posições
- **RAM**: O(A + I + C) onde A=ativos, I=instituições, C=classes
- **Observação**: Usa `dict` interno como agregador — muito eficiente

### PerformanceEngine
- **Complexidade**: O(1) para `calculate()` — apenas aritmética Decimal
- **Complexidade `generate_history()`**: O(N*M) onde M=meses
  - A cada mês, todos os trades até a data são repassados ao PositionEngine
  - **Gargalo identificado**: Este é o ponto de maior custo. Para 10 anos com 1.000 trades e 120 meses, o custo estimado é 120.000 operações
  - **Mitigação recomendada**: Implementar acumulação incremental de posição (manter estado entre iterações ao invés de filtrar todos os trades a cada mês)

### MarketDataService / MarketDataRepository
- **Complexidade de Busca**: O(log N) via bisect
- **Carregamento**: O(N) único na inicialização (Singleton)
- **RAM**: < 1 MB para 20 anos de dados diários (5.200 entradas * 6 índices)
- **Observação**: Cache em memória garante zero I/O depois do boot

### ImportService
- **Complexidade**: O(N) — processa cada trade uma vez
- **Bottleneck**: Hash SHA-256 por arquivo (única operação criptográfica)
- **Observação**: O custo principal está no banco de dados (INSERT...DO NOTHING)

### Reconciliação
- **Complexidade**: O(P log S) onde P=posições, S=snapshots
- **Observação**: Raramente chamada por usuário; aceitável em qualquer volume

## Projeção para 100.000 Trades
Com base nos dados observados (crescimento ~linear de ~1.4ms/1000 trades):
- Estimativa: ~1400ms — 1.4 segundos para o pipeline completo (sem geração de histórico)
- RAM estimada: ~2 MB
- **Recomendação**: Adicionar cache de resultado de posição para evitar recálculo completo a cada request

## Dívidas Técnicas
1. `generate_history()` faz O(N*M) em vez de O(N+M) — **ALTA PRIORIDADE**
2. `market_prices` para precificação histórica é sempre o preço atual — precisaria de série histórica de preços por ativo
3. Sem paginação nos endpoints `/positions` e `/portfolio` — pode ser problema com portfolios muito grandes
