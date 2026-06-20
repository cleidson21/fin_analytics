# Catálogo de Fórmulas Financeiras V2 (Financial Formulas Catalog V2)

Para a construção do motor financeiro interno independente, este documento cataloga todas as fórmulas matemáticas e lógicas de negócio necessárias. O sistema base não dependerá mais do MyProfit para gerar esses indicadores.

---

## 1. Posição e Custos (Asset Valuation)

### 1.1 Preço Médio de Aquisição (Cost Basis / Average Price)
O cálculo do preço médio é fundamental para fins de imposto de renda e rentabilidade real.

* **Fórmula (Compra)**: 
  `Preço Médio Atual = ((Qtd_Anterior * Preço_Medio_Anterior) + (Qtd_Nova * Preço_Nova + Custos_Corretagem)) / (Qtd_Anterior + Qtd_Nova)`
* **Fórmula (Venda)**: 
  A venda *não altera* o preço médio de aquisição. Apenas reduz a quantidade no estoque.
* **Nota sobre Custos**: Custos de corretagem, taxa B3 (CBLC), ISS, emolumentos **somam** no custo de compra e **diminuem** no resultado da venda.

### 1.2 Posição Total Investida (Total Invested)
* **Fórmula**: `Posição Total Investida = Quantidade_Atual * Preço_Médio_Aquisição`

### 1.3 Posição Atual do Ativo (Current Value)
* **Fórmula**: `Posição Atual = Quantidade_Atual * Preço_Mercado_Atual (via yfinance)`

### 1.4 Lucro / Prejuízo Absoluto (Unrealized Gain/Loss)
* **Fórmula**: `Ganho Absoluto = Posição Atual - Posição Total Investida`

---

## 2. Rendimentos (Yield Metrics)

### 2.1 Dividend Yield (DY Atual)
Representa o retorno de dividendos frente ao preço atual de mercado da cota.
* **Fórmula**: `DY = (Total_Dividendos_Últimos_12_Meses / Preço_Mercado_Atual)`

### 2.2 Yield On Cost (YOC)
Representa o retorno dos dividendos frente ao valor que o usuário efetivamente pagou pela cota no passado.
* **Fórmula**: `YOC = (Total_Dividendos_Últimos_12_Meses / Preço_Médio_Aquisição)`
* **Vantagem**: Mostra o poder dos juros compostos; quem comprou barato tem um YOC absurdamente alto mesmo com o DY de mercado caindo.

---

## 3. Desempenho e Rentabilidade (Performance)

### 3.1 Rentabilidade Absoluta do Ativo (%)
* **Fórmula**: `Rentabilidade Ativo = ((Preço_Mercado_Atual / Preço_Médio_Aquisição) - 1) * 100`

### 3.2 Time-Weighted Return (TWR) - Rentabilidade da Carteira
A forma correta de calcular o retorno da carteira ignorando aportes e resgates (exclui o viés de quando o dinheiro foi injetado). A carteira é tratada como um sistema de Cotas (Cota do Fundo).
1. **Valor Inicial da Cota**: R$ 1,00.
2. No momento do aporte, `Novas_Cotas = Valor_Aportado / Valor_Cota_D-1`.
3. `Valor_Cota_D = Valor_Total_Carteira_D / Total_Cotas_Existentes`.
* **Rentabilidade Acumulada da Carteira**: `(Valor_Cota_Hoje / 1,00) - 1`.

### 3.3 Evolução Patrimonial (Equity Evolution)
A curva real de enriquecimento.
* **Fórmula**: `Patrimônio_T = Patrimônio_T-1 + Aportes_T - Resgates_T + (Ganho_Capital_T + Dividendos_Recebidos_T)`

---

## 4. Benchmarks e Análise de Risco

### 4.1 Benchmark de Retorno Relativo (Alpha)
O quanto a carteira está superando (ou perdendo para) o índice de referência (ex: CDI ou IBOV).
* **Fórmula**: `Alpha = Rentabilidade_TWR_Carteira - Rentabilidade_Benchmark`

### 4.2 Alocação de Carteira (Asset Allocation %)
O peso de um ativo ou setor na carteira total.
* **Fórmula**: `Peso_Ativo = (Posição_Atual_Ativo / Posição_Total_Carteira) * 100`

### 4.3 Beta da Carteira (Risco Sistêmico)
Mede a volatilidade da carteira em relação ao IBOV.
* **Fórmula**: `Beta = Covariância(Retornos_Carteira, Retornos_IBOV) / Variância(Retornos_IBOV)`
* *Beta > 1*: Carteira mais volátil que o mercado. *Beta < 1*: Carteira menos volátil.

### 4.4 Índice de Sharpe
Mede o retorno ajustado ao risco. Quanto de retorno a carteira gera para cada unidade de risco assumida acima da taxa livre de risco (Selic).
* **Fórmula**: `Sharpe = (Retorno_Médio_Carteira - Taxa_Livre_de_Risco) / Desvio_Padrão_Carteira`

---

## 5. Normalização de Eventos Corporativos

### 5.1 Desdobramento (Split) ex: 1 para 4
Quando uma ação de R$ 100 vira 4 de R$ 25.
* **Ajuste na Base**: 
  * `Quantidade_Nova = Quantidade_Antiga * 4`
  * `Preço_Médio_Novo = Preço_Médio_Antigo / 4`

### 5.2 Grupamento (Reverse Split) ex: 10 para 1
Quando 10 ações de R$ 1 viram 1 de R$ 10.
* **Ajuste na Base**:
  * `Quantidade_Nova = Quantidade_Antiga / 10`
  * `Preço_Médio_Novo = Preço_Médio_Antigo * 10`
