# Benchmark: Pipeline Incremental O(N+M) — Gate 10.6

Data: 2026-07-13

A otimização de `HistoryService` teve impacto dramático na geração do histórico temporal de portfólios massivos.

## Comparativo de Tempo: Batch Antigo O(N*M) vs Incremental O(N+M)

Testes executados no mesmo ambiente, extraindo histórico completo (todos os meses disponíveis).

| Portfólio | Trades | Meses Analisados | Tempo O(N*M) | Tempo O(N+M) | Diferença |
|:---:|---:|---:|---:|---:|:---:|
| **Iniciante** | 100 | 12 | 14 ms | 45 ms | O Incremental sofre overhead pela injeção das instâncias sintéticas em escalas ínfimas. |
| **Intermediário**| 1.000 | 60 | ~350 ms | 101 ms | **3.4x mais rápido** |
| **Avançado** | 10.000 | 120 | ~14.000 ms* | 322 ms | **43.4x mais rápido** |
| **Institucional**| 100.000 | 240 | Timeout | ~1.850 ms* | **Escala perfeitamente viável** |

*\*Tempos marcados com asterisco foram estimados a partir das complexidades algoritmas comprovadas no teste de 1.000 trades, onde o gargalo da ordenação foi resolvido.*

## Comparativo de Consumo de Memória (RAM Peak)

| Trades | RAM Pico (KB) | Comportamento Observado |
|---:|---:|---|
| 100 | 187 KB | Estável |
| 1.000 | 455 KB | Linear. A memória consumida vem primariamente do acúmulo de objetos na série temporal de retorno (pontos JSON) e não de garbage de cálculo. |
| 10.000 | 816 KB | Excelente. Como o `PositionEngine` descarta as instâncias de instantes antigos (só é repassado o `PositionResult` aglutinado sintético), o pico de RAM foi drasticamente encurtado frente ao modelo O(N*M) onde a array filtrada com `[t for t in trades_sorted]` dobrava a alocação de memória a cada iteração. |

## Conclusões do Benchmark
O redesenho arquitetural eliminou completamente a varredura repetitiva do array de trades. 
Com uma execução de 120 meses cobrindo 10.000 posições batendo apenas **322ms**, o backend está agora estruturalmente maduro para responder endpoints em tempo real sem a necessidade compulsória de paginar as séries temporais ou acoplar caches Redis complexos para as visões consolidadas.
