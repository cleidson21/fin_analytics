# History Algorithm O(N+M) — Gate 10.6

Data: 2026-07-13

A geração de série temporal de um portfólio (histórico) requer o cálculo mês a mês (ou dia a dia) do patrimônio e da rentabilidade. 

## O Problema Original (O(N * M))
No antigo `PerformanceEngine.generate_history`, para cada mês $M$, a engine extraía todos os trades do histórico inteiro do cliente (até aquele mês) e repassava-os à `PositionEngine`.

Se um cliente tinha 10.000 trades distribuídos em 10 anos (120 meses), o algoritmo precisava processar:
- Mês 1: 83 trades
- Mês 2: 166 trades
- ...
- Mês 120: 10.000 trades
**Total de processamento**: Cerca de 600.000 avaliações de trades para 1 único request. Escala quadrática (ou O(N*M)).

## A Solução Incremental (O(N + M))

Para evitar a duplicação de lógica, reaproveitamos o motor atual (`PositionEngine`) adotando injeção de estado.

### 1. Injeção de Estado Sintético (INITIAL_POSITION)
A `PositionEngine` é pura: recebe `List[TradeDTO]` e calcula uma nova posição.
Para processar o mês 2 sem recalcular o mês 1:
- A `HistoryService` extrai a `PositionResult` final do Mês 1.
- Ela converte cada posição em um `TradeDTO` com a operação `INITIAL_POSITION`.
- A quantidade, preço médio e valor investido da posição são injetados nesse trade sintético.
- A `PositionEngine` processa o Mês 2 recebendo as `INITIAL_POSITION` do Mês 1 + `BUY/SELL` originais do Mês 2.

### 2. O Algoritmo
```python
current_positions = []
trades_ordenados = ordenar(trades_reais)

para cada mês em (inicio..fim):
    trades_do_mes = extrair_trades(trades_ordenados, mes)
    
    # 1. Monta o estado inicial
    trades_iniciais = []
    para pos em current_positions:
        se pos.quantidade > 0:
            trades_iniciais.add(TradeDTO(INITIAL_POSITION, qty=pos, price=pos.avg))
            
    # 2. Chama PositionEngine de forma delimitada
    current_positions = PositionEngine.calculate(trades_iniciais + trades_do_mes)
    
    # 3. Avança o pipeline estático
    valuations = ValuationEngine.calculate(current_positions)
    wealth = WealthEngine.calculate(valuations)
    
    # 4. Grava ponto
    salvar_historico(mes, wealth)
```

## Ganhos Arquiteturais
- **SRP Reestabelecido**: A `PerformanceEngine` passa a ser um motor de cálculos estáticos. A responsabilidade da *linha do tempo* fica contida na nova `HistoryService`.
- **Zero Modificações no Core**: A `PositionEngine` não foi alterada. Ela trata `INITIAL_POSITION` nativamente. O risco de quebrar a fórmula de Custo Médio foi completamente mitigado por reutilização estrutural.
- **DIP (Dependency Inversion)**: A nova arquitetura isola o processamento orquestrado fora das entidades base.
