# Historical Price Engine — Gate 10.7

Data: 2026-07-13

A introdução de `HistoricalPriceService` e `HistoricalPriceRepository` muda a qualidade dos relatórios do sistema de estáticos para dinâmicos e precisos ao longo do tempo (Time-Series Accuracy).

## 1. O Problema Original (DT-02)
Na arquitetura antiga (antes deste Gate), o patrimônio histórico era projetado no passado sempre multiplicando a quantidade possuída no passado pelo preço de tela **atual**.
- **O que acontecia:** Se PETR4 estava a R$ 10 em 2010 e hoje está R$ 40, o sistema diria que em 2010 o cliente tinha R$ 4.000 em vez de R$ 1.000 (assumindo 100 ações).
- **Consequência:** Linha temporal matemática inválida para cálculo de rentabilidade (TWR / MWR) em janelas longas.

## 2. Nova Arquitetura de Preços Históricos

### HistoricalPriceRepository
Responsável por interagir com o File System em `/database/prices/` para carregar as cotações de fechamento diárias, mantendo total isolamento da rede durante os processamentos de portfolio O(N+M).
- **Estrutura de Armazenamento:** Arquivos CSV planos.
- **Cache Local:** Ao ser instanciado, os CSVs são carregados, limpos e as datas convertidas. Armazena-se tudo em uma série temporal de classe `Tuple[date, Decimal]`.
- **Complexidade de Carga:** `O(D * A)`, onde D = Dias úteis, A = Ativos. Feita estritamente de maneira preguiçosa (Lazy Singleton).

### HistoricalPriceService
Expõe uma interface `get_price_for_date(ticker, date)`.
- **Busca:** Utiliza `bisect.bisect_right` na árvore binária nativa de arrays do Python.
- **Fallback (Regra de Negócio):** Se a data procurada cai em um fim de semana (ex: Sábado) ou feriado sem pregão, o ponteiro de inserção do `bisect_right` aponta naturalmente para o índice sucessor. Subtraindo 1, obtemos de brinde a cotação exata do pregão imediatamente anterior sem nenhum custo algorítmico extra, satisfazendo a regra de **"Nunca usar preço do futuro"**.
- **Complexidade de Busca:** `O(log D)` por acesso. Extremamente leve e pode ser chamado milhares de vezes por segundo no looping de patrimônio.

### Acoplamento na ValuationEngine
A `ValuationEngine` continua recebendo um dict de `market_prices` (que seriam as cotações live/spot atuais), porém agora sua assinatura aceita opcionalmente um `reference_date`.
- Quando operando para renderizar a página principal (Current Portfolio), `reference_date` é nulo, e a marcação a mercado ocorre como esperado com o preço de hoje.
- Quando instanciada no loop do `HistoryService`, a engine identifica `is_historical = True` e invoca o serviço histórico para buscar o valor temporal fidedigno àquela janela.

## 3. Benefícios Destravados
1.  **Precisão Algorítmica Absoluta:** Agora o cálculo de Drawdowns, Volatilidade e Rentabilidade temporal baterão perfeitamente com a B3.
2.  **Infraestrutura Habilitadora (Enabler):** Sem esta engine, as métricas avançadas previstas para o próximo gate (Gate 10.8) seriam inviáveis.
