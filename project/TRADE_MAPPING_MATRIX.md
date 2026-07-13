# Matriz de Mapeamento B3 → CEI Trade (Etapa 8)

Esta tabela mapeia o dicionário de-para (ETL base) exigido pelo Parser para transformar as colunas brutas lidas do `Exemplo_Negociacao_B3.xlsx` nas entidades canônicas (Trade) do projeto.

*Origem: samples/Exemplo_Negociacao_B3.xlsx | Aba: Negociação*

| Campo Original B3 (XLSX) | Tipo Original (Pandas) | Campo Interno (DTO) | Tipo Interno (Python) | Obrigatório | Validação Específica | Destino Funcional |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **Data do Negócio** | `str` (DD/MM/YYYY) | `trade_date` | `datetime.date` | Sim | Passar no `%d/%m/%Y`. Não ser futuro. | Chave temporal do Trade. |
| **Tipo de Movimentação**| `str` | `operation_type` | `Enum (TradeType)` | Sim | Restrito a `Compra`, `Venda` (e derivados B3). | Define sinal do fluxo de caixa (+ ou -). |
| **Mercado** | `str` | `market_type` | `str` | Não | | Informativo (Opções, Vista, Termo). |
| **Prazo/Vencimento** | `str` (hífens comuns) | `expiration_date` | `datetime.date / None`| Não | Tratar `"-"` como nulo. | Derivativos / Renda Fixa. |
| **Instituição** | `str` | `broker` | `str` | Sim | | Usado no Hash de Idempotência. |
| **Código de Negociação**| `str` | `ticker` | `str` | Sim | Limpar sufixo `F` (se mercado a vista). | Identificador do Ativo (`asset_id`). |
| **Quantidade** | `int64` (ou float64) | `quantity` | `Decimal` | Sim | Maior que Zero. | Multiplicador da posição. |
| **Preço** | `float64` | `unit_price` | `Decimal` | Sim | Maior que Zero. | Preço de execução bruto. |
| **Valor** | `float64` | `total_value` | `Decimal` | Sim | Corresponder (prox.) a Qtde * Preço. | Volume financeiro bruto. |

## Observações de Conversão
1. A conversão de strings monetárias (vírgula para ponto) costuma ser nativa no openpyxl, resultando em `float64`, contudo o Parser deve forçar o casting para `Decimal` para evitar perda de precisão financeira.
2. A Data do Negócio no `openpyxl` frequentemente é capturada como objeto DateTime nativo do excel. O Parser testará se já é DateTime; do contrário, converterá do padrão texto BR.
