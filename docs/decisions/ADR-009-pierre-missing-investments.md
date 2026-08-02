# ADR-009: Pierre Missing Investment Data

**Motivação:** A auditoria rigorosa da documentação oficial da Pierre Finance (https://docs.pierre.finance/api-reference) revelou que a API é exclusivamente focada em *Banking* (Contas, Transações, Cartões e Limites). Não existe qualquer endpoint ou modelo referente a Investimentos, Posições, Dividendos ou Cripto.

**Impacto:** É impossível utilizar a Pierre como hub de Open Finance para a carteira de investimentos global ou nacional do FIN Analytics.

**Decisão:** O MyProfit deve assumir imediatamente a responsabilidade integral como *Source of Truth* de toda a malha patrimonial (Investimentos, Ações, FIIs, Dividendos e B3). A Pierre ficará restrita a ser a *Source of Truth* do caixa líquido (Banking, Transações e Cartões de Crédito). O Domínio e a Ingestão deverão ser divididos.
