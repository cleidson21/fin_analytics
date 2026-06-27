# 5.6 Reconciliation Engine

## Objetivo
Motor proprietário e núcleo cognitivo do FinAnalytics. Ele cruza todas as fontes de dados normalizadas para resolver litígios e estabelecer a verdade financeira.

## Arquitetura e Fluxo
A engine cruza Conta, Cartão, Pierre, MyProfit, B3, Notas e (futuramente) Open Finance.
Decide ativamente sobre cada Canonical Event, determinando se ele é:
- **Igual:** (Ex: Nota de Negociação D+2 e Extrato Nubank D+2 coincidem perfeitamente).
- **Complementar:** (Ex: O evento existe no Nubank, e o Pierre providencia a categoria).
- **Duplicado:** (Ex: Uma segunda tentativa de importar o mesmo CSV).
- **Atualização:** (Ex: Preço médio que chega via B3 e consolida sobre o anterior).
- **Conflito:** (Ex: Nota B3 diz que sobrou R$ 10.00, Nubank diz que sobrou R$ 8.00).

## Regras e Referências
Esta camada deve continuar como **código estritamente proprietário**. Jamais substituir por uma biblioteca externa pronta, pois o diferencial do sistema está aqui.
- Projetos referência para estudo: **beancount** (reconciliação de dupla entrada) e **hledger**.
