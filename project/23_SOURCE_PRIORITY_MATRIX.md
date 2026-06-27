# SOURCE PRIORITY MATRIX (A CONSTITUIÇÃO DA VERDADE FINANCEIRA)

Este documento atua como a constituição absoluta do sistema em relação a conflitos de fontes de dados. Quando múltiplas fontes (documentos ou APIs) informam valores divergentes para o mesmo evento financeiro (mesmo Canonical Event), a regra abaixo define quem vence o conflito.

## Quem Vence Quem

- **Conta (Banco) VENCE Pierre/Agregadores**
  *Motivo:* O extrato bancário reflete o lançamento efetivo, centavo a centavo. Agregadores podem errar ou desconsiderar IOF/Taxas.
- **Conta (Banco) VENCE Nota de Corretagem (No fluxo de Caixa)**
  *Motivo:* Se a nota diz que você pagou R$ 1.000,00, mas da conta foi debitado R$ 1.000,50 (devido a IOF ou falha de sistema da corretora), o caixa da Conta é a verdade final de tesouraria.
- **Nota de Corretagem VENCE Custódia B3/Corretora (Nos Custos)**
  *Motivo:* A custódia não detalha os emolumentos, taxas de liquidação e ISS pagos na execução da ordem. A Nota é o documento oficial e incontestável para fins de Imposto de Renda.
- **B3 VENCE MyProfit (Na Quantidade)**
  *Motivo:* A Bolsa é a câmara de compensação (clearing) final. Se o MyProfit divergir da B3 em quantidade de ativos custodiados, o MyProfit está errado.
- **MyProfit VENCE Conta (Em Metadados de Proventos)**
  *Motivo:* O extrato da Conta mostra apenas "Depósito Rendimentos R$ 10,00", sem explicar Data-COM ou Yield. MyProfit ou fontes especializadas vencem fornecendo a riqueza do metadado.

## Resumo Estrutural
- **Caixa & Liquidez:** Origem Bancária Oficial > Fatura Cartão Oficial > Restante.
- **Preço e Custos (Trading):** Nota de Negociação PDF > B3 > Restante.
- **Quantidade Patrimonial:** Custódia B3 > Extrato Corretora > Restante.
- **Categorização / Semântica:** Usuário > Pierre (Teacher IA) > Regex Padrão.
