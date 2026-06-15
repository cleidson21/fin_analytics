# FINANCIAL CALCULATION CATALOG

Este catálogo mapeia todas as lógicas e fórmulas financeiras em uso pelo FinAnalytics V2. Todas as variáveis monetárias assumem a leitura em banco através da sufixação `_cents` e sua devida formatação flutuante apenas para memória.

---

## 1. Saldos e Fluxo de Caixa

### Balanço Mensal (Net Cashflow)
* **Origem:** `CashflowService`
* **Fórmula Atual:** `Soma(Receitas do Mês) - Soma(Despesas do Mês)`
* **Variáveis Usadas:** `Transaction.valor` e filtro `natureza == 'INCOME'` vs `natureza == 'EXPENSE'`.
* **Possíveis Inconsistências:** Cartão de crédito consolida na fatura (despesa futura) e pode mascarar o caixa real se não filtrado pelo regime de competência vs caixa.

### Pacing (Ritmo de Gasto Mensal - MoM)
* **Origem:** `CashflowService` (Dashboards)
* **Fórmula Atual:** `(Gasto Acumulado Mês Atual até Dia X) / (Gasto Acumulado Mês Anterior até o Mesmo Dia X) - 1`
* **Variáveis Usadas:** `valor_cents`, `data`.
* **Possíveis Inconsistências:** Fevereiro tem 28 dias; extrapolar Pacing do dia 31 projeta Erros Matemáticos (ZeroDivisionError se o dia anterior cair num feriado ou fim de mês não coincidente).

---

## 2. Patrimônio e Rentabilidade (Wealth)

### Preço Médio de Aquisição (PM)
* **Origem:** Staging e Broker Imports.
* **Fórmula Atual:** `(PM Anterior * Quantidade Anterior + Preço Nova Compra * Quantidade Nova) / (Quantidade Anterior + Quantidade Nova)`
* **Variáveis Usadas:** `preco_medio`, `quantidade`.
* **Possíveis Inconsistências:** O Sistema atual confia nos dados consolidados via corretora/B3 na tabela `Positions`. Se a importação não trouxer o PM, a falta de tabela de ordens ("Book") impede o recálculo do zero.

### Alpha (Excesso de Retorno da Carteira)
* **Origem:** `EvolutionService` / Wealth
* **Fórmula Atual:** `Rentabilidade_Acumulada_Carteira - Rentabilidade_Acumulada_Benchmark`
* **Variáveis Usadas:** `PortfolioEvolution.rentabilidade_acumulada_pct`, `Benchmark.value_pct`.
* **Possíveis Inconsistências:** A rentabilidade do CDI precisa ser anualizada e trazida a valor presente, comparar somatórias mensais de IBOV/CDI com carteiras dinâmicas (com saques/aportes no meio do mês) dilui a precisão matemática (Time-Weighted Return vs Money-Weighted Return).

### Yield On Cost (YOC)
* **Origem:** `DividendService`
* **Fórmula Atual:** `(Soma Dividendos Acumulados do Ticker / Total Investido do Ticker) * 100`
* **Variáveis Usadas:** `Dividend.valor_liquido`, `Position.total_investido`.
* **Possíveis Inconsistências:** O `total_investido` flutua com novos aportes. Se o investidor faz preço médio para baixo ou vende o principal e mantém as cotas marginais gratuitas, o YOC pode tender a infinito (divisão por zero) ou se tornar irreal.

---

## 3. Orçamento e Planejamento

### Asset Allocation (Pizza de Classe de Ativos)
* **Origem:** `AllocationService`
* **Fórmula Atual:** `(Soma do Patrimonio da Classe X / Patrimonio Total da Carteira) * 100`
* **Variáveis Usadas:** `Position.classe_ativo`, `Position.total_atual`.
* **Possíveis Inconsistências:** Atraso da Cotação afeta o valor da Pizza de forma desproporcional.

### Consumo de Meta (Goal Burn Rate)
* **Origem:** `GoalService`
* **Fórmula Atual:** `(Soma(Gastos na Categoria) / Limite_Cents_da_Meta) * 100`
* **Variáveis Usadas:** `Goal.limit_cents`, `Transaction.valor_cents`.
* **Possíveis Inconsistências:** Metas anuais particionadas vs metas puramente mensais em categorias flexíveis.
