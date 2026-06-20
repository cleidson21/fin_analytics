# Plano de Evolução do Banco de Dados (Database Evolution Plan)

Para garantir a total independência do sistema em relação ao Pierre e MyProfit pelos próximos 10 anos, o banco de dados deve ser reestruturado como um **Ledger Financeiro e de Investimentos** unificado e imutável. 

A arquitetura será dividida em domínios core baseada nos princípios de *Event Sourcing* para finanças (nunca apagar transações, apenas compensá-las) e normalização robusta.

---

## 1. Módulo Core (Banking & Identity)

Fundação para gerenciar de onde vem e para onde vai o dinheiro.

* `institutions`: Bancos, Corretoras (ex: Nubank, B3, XP).
* `accounts`: Contas pertencentes às instituições.
  * *Tipos*: Checking (Corrente), Credit (Cartão), Brokerage (Corretora).
* `categories`: Árvore hierárquica de categorias de despesas e receitas.
* `merchants`: Cadastro normalizado de contrapartes (ex: "Shopee", "Kaizen Gaming").

---

## 2. Módulo de Fluxo de Caixa (Cashflow)

O coração das finanças diárias. Substitui o extrato bruto do banco e a importação do Pierre.

* `transactions`: A tabela central. Toda movimentação de dinheiro é uma transação.
  * *Campos essenciais*: `id` (uuid original do banco), `account_id`, `date`, `amount`, `original_description`, `merchant_id`, `category_id`, `type` (IN/OUT), `status`.
* `transfers`: Associa duas `transactions` (uma saída e uma entrada) de mesma titularidade.
* `classification_rules`: Tabela para treinar a inteligência de categorização local (Regras Regex mapeando strings para `merchant_id` e `category_id`).

---

## 3. Módulo de Cartão de Crédito (Credit)

Para gerenciar o detalhamento de faturas que o Pierre esconde em um débito único.

* `credit_cards`: Representa o cartão físico/virtual associado a uma conta.
* `invoices`: A fatura do mês.
  * *Campos*: `credit_card_id`, `due_date`, `closing_date`, `total_amount`, `status` (OPEN, CLOSED, PAID).
* `invoice_items`: Os lançamentos individuais na fatura.
* `installment_plans`: Metadados de compras parceladas.
  * *Campos*: `merchant_id`, `total_amount`, `total_installments`.
* `installments`: As parcelas (1/6, 2/6, etc) vinculadas ao plano e mapeadas para as `invoices` futuras. Permite projeção de fluxo de caixa.

---

## 4. Módulo de Investimentos (Wealth)

Substitui integralmente o MyProfit. Modelado com base em liquidação oficial.

* `assets`: O catálogo de ativos (Tickers).
  * *Campos*: `ticker` (XPML11, BBAS3), `type` (Ação, FII, BDR, RDB), `sector`.
* `market_data_history`: Histórico de preços (fechamento diário), alimentado via `yfinance`.

### Execução (Trading)
* `broker_notes`: O documento da nota de corretagem.
  * *Campos*: `broker_id`, `date`, `note_number`, `clearing_fee` (taxa CBLC), `registration_fee` (registro), `brokerage_fee` (corretagem), `taxes` (ISS, PIS/COFINS, IRRF).
* `trades`: As execuções individuais dentro de uma nota.
  * *Campos*: `broker_note_id`, `asset_id`, `type` (BUY, SELL), `quantity`, `unit_price`, `total_value`.

### Eventos Corporativos
* `corporate_actions`: Desdobramentos (Splits), Grupamentos, Bonificações. Essencial para não distorcer o preço médio histórico.
* `dividends`: Rendimentos, JCP, Amortizações recebidos.
  * *Campos*: `asset_id`, `ex_date`, `payment_date`, `value_per_share`, `total_received`, `type` (DIVIDEND, JCP).

---

## 5. Módulo de Analytics (Snapshots)

Para otimização de performance. Ao invés de calcular a rentabilidade de 10 anos on-the-fly, o sistema deve gerar consolidações ("materialized views" ou tabelas de snapshot cronadas).

* `asset_positions`: A posição atual do usuário.
  * *Campos*: `asset_id`, `current_quantity`, `average_price`, `total_invested`.
* `portfolio_snapshots`: Fotografia diária ou mensal da carteira.
  * *Campos*: `date`, `total_equity`, `cost_basis`, `daily_return`, `cumulative_return`.
* `benchmark_snapshots`: O valor dos índices na mesma data (CDI acumulado, IBOV, IFIX, S&P 500).

---

## Processo de Transição / Migração

1. **V1 (Ingestão Básica)**: Criar o modelo *Banking* e importar os dados brutos do Nubank, ignorando Pierre. Usar Pierre apenas para treinar a tabela `classification_rules`.
2. **V2 (Faturas)**: Implementar lógica de *Credit Card*. Processar CSVs das faturas do Nubank. O pagamento da fatura (`transactions`) linca com a tabela `invoices`.
3. **V3 (Investimentos)**: Criar rotina de parse de Notas de Corretagem (PDFs ou integração B3). Calcular Preço Médio usando a tabela `trades`. Importar série histórica do MyProfit apenas como "Balanço Inicial" se houver notas antigas inacessíveis.
4. **V4 (Analytics)**: Integrar `yfinance`. Rodar job noturno preenchendo `portfolio_snapshots`. Cortar MyProfit em definitivo.
