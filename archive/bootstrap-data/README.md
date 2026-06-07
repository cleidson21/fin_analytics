# Bootstrap Data (Fixtures Originais)

Esta pasta abriga os arquivos fundamentais que validaram o comportamento inicial e testes do sistema.
**Regra de Ouro:** Estes arquivos NUNCA devem ser deletados, editados ou sofrer merge manual. Eles representam a fonte de verdade imutável ("Fixtures") para todos os testes de regressão de parsers.

## Estrutura
- `myprofit/` -> Arquivos originais exportados do MyProfit (Provento, Evolucao, tableExport). Utilizados para testar a extração (Parser) e a consolidação de posições da B3.
- `nubank/` -> Amostras de faturas e consolidações cruas.
- `Extrato_Pierre_Auditado.csv` -> A base fundamental auditada contendo toda a classificação inicial do projeto, que treina e consolida a taxonomia de categorias do categorizador.
