# Architecture Validation — Gate 10.5

Data: 2026-07-13

## Existe código duplicado?

| Local | Descrição | Status |
|-------|-----------|--------|
| `router.py` → `get_portfolio()` | Chamado por `get_performance()`, `get_allocation()`, `get_institutions()` — reutilização adequada | OK |
| `PositionEngine` usado em `router.py` e em `PerformanceEngine.generate_history()` | Instanciação redundante a cada request na geração de histórico | ⚠️ ATENÇÃO |
| Lógica de cálculo de custo médio | Centralizada no `PositionEngine`, sem duplicação | OK |

**Conclusão**: Duplicação mínima. A instanciação múltipla de engines a cada request de histórico é ineficiente mas não constitui duplicação de lógica.

---

## Existe responsabilidade misturada?

| Local | Descrição | Status |
|-------|-----------|--------|
| `PerformanceEngine.generate_history()` | Chama `PositionEngine`, `ValuationEngine`, `WealthEngine`, `MarketDataService` internamente | ⚠️ Orquestração interna: poderia ser responsabilidade do Router ou de um Service dedicado |
| `ImportService` | Faz parsing, persiste, loga — múltiplas responsabilidades | ⚠️ Moderado — poderia ser extraído |
| `MarketDataRepository` | Carrega CSV e realiza lookups — responsabilidade mista de I/O e busca | Aceitável para esta fase |

**Conclusão**: A `generate_history()` acumula orquestração que, em produção, deveria estar num `HistoryService`. Dívida técnica documentada.

---

## Existe violação SOLID?

### Single Responsibility Principle (SRP)
- **PerformanceEngine**: Viola parcialmente. `calculate()` é pura e correta. `generate_history()` tem múltiplas responsabilidades (orquestração + cálculo).
- **ImportService**: Viola parcialmente. Parseia, persiste, e audita. Aceitável para uma fase inicial.

### Open/Closed Principle (OCP)
- Engines são abertas para extensão (herança/composição) e fechadas para modificação — respeitado.
- Novos tipos de ativo ou operação: basta adicionar ao Enum e às regras do `PositionEngine`.

### Liskov Substitution (LSP)
- Não há hierarquia de herança significativa. Não aplicável.

### Interface Segregation (ISP)
- Não há interfaces formais (Python não força). Os contratos são implícitos via duck typing.

### Dependency Inversion (DIP)
- `PerformanceEngine.generate_history()` instancia diretamente `PositionEngine`, `ValuationEngine`, etc. Deveria receber esses objetos via injeção. **Violação leve.**
- `MarketDataService` é criado dentro da Engine em vez de ser injetado.

**Conclusão**: Violações leves de SRP e DIP em `generate_history()`. Sem violações críticas.

---

## Existe violação Clean Architecture?

| Camada | Diagnóstico |
|--------|-------------|
| **Entities** (DTOs) | Corretos — puros, sem dependências externas |
| **Use Cases** (Engines) | Parcialmente violados — `generate_history()` importa outros módulos internamente |
| **Interface Adapters** (Router) | Corretos — mapeiam HTTP para use cases |
| **Frameworks & Drivers** (SQLAlchemy, FastAPI) | Isolados adequadamente |

**Conclusão**: Arquitetura limpa respeitada em sua maior parte. O `generate_history()` representa uma fronteira de use case que está na engine em vez de num service, o que é uma violação tolerável nesta fase.

---

## Existe acoplamento indesejado?

| Par Acoplado | Tipo | Risco |
|---|---|---|
| `PerformanceEngine` ↔ `PositionEngine` | Direto (via import local) | Médio |
| `PerformanceEngine` ↔ `MarketDataService` | Direto (via import local) | Baixo |
| `Router` ↔ `get_portfolio()` (função interna) | Direto | Baixo — helper reutilizável |
| `ImportService` ↔ todos os parsers | Alto — instanciação condicional | Médio — considerar factory |

---

## Existe gargalo?

| Gargalo | Severidade | Causa | Mitigação |
|---------|-----------|-------|-----------|
| `generate_history()` O(N*M) | ALTO | Recalcula posições do zero a cada mês | Acumulação incremental de estado |
| Sort de trades por `(trade_date, created_at)` | MÉDIO | Acontece a cada chamada da PositionEngine | Cache de posição ou processamento incremental |
| Sem cache HTTP | BAIXO | Cada request recalcula tudo | Redis ou cache in-process com TTL |
| Sem índice na tabela de trades | MÉDIO | Full table scan no `TradeRepository.list_all()` | Adicionar índice em `(broker, ticker, trade_date)` |

---

## Existe risco?

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Overflow numérico em portfólios com bilhões de reais | Baixa | Alto | Decimal já mitiga — mantido |
| Race condition no Singleton de `MarketDataRepository` | Baixa | Baixo | Não há threads simultâneas atualmente |
| CSVs de benchmark não atualizados | Alta | Médio | Documentar processo de atualização |
| `dateutil` não instalado em produção | Médio | Alto | Adicionar ao `requirements.txt` |

---

## Existe dívida técnica?

| ID | Descrição | Prioridade |
|----|-----------|-----------|
| DT-01 | `generate_history()` é O(N*M) — implementar acumulação incremental | ALTA |
| DT-02 | `generate_history()` usa preço atual para todos os meses — falta série de preços histórica por ativo | ALTA |
| DT-03 | `dateutil` não está no `requirements.txt` | MÉDIA |
| DT-04 | Sem injeção de dependência nas engines (viola DIP) | MÉDIA |
| DT-05 | CSVs de benchmark atualizados manualmente | MÉDIA |
| DT-06 | Sem paginação nos endpoints de posições e portfólio | BAIXA |
| DT-07 | `MarketDataRepository._loaded` é variável de classe — pode causar estado compartilhado inesperado em testes | BAIXA |
| DT-08 | `ImportService` mistura parse, persistência e auditoria — considerar separar em `ParseService` + `PersistenceService` | BAIXA |
