# Matemática de Portfólios — FINANALYTICS V3

Data: 2026-07-13

O **FinancialAnalyticsEngine** calcula métricas matemáticas fiduciárias de alto rigor a partir dos fluxos de caixa e séries de tempo processadas pela `HistoryService`.

## 1. Time-Weighted Return (TWR)
O TWR mede a rentabilidade composta do gestor sem ser penalizado por depósitos ou saques efetuados ao longo do percurso.
- **Como calculamos:** `TWR = [ Π (1 + R_t) ] - 1`
- `R_t = (Patrimonio_t - FluxosLiquidos_t) / Patrimonio_{t-1} - 1`
- Essa fórmula mitiga perfeitamente aportes grandes distorcendo a porcentagem final da carteira.

## 2. Money-Weighted Return (MWR) / XIRR
Considera o tamanho absoluto do capital alocado em cada instante de tempo (Taxa Interna de Retorno).
- **Como calculamos:** Utilizamos o algoritmo de **Newton-Raphson** que itera aproximando a taxa $r$ para a equação do Valor Presente Líquido (NPV):
- $NPV(r) = \sum \frac{C_t}{(1 + r)^{\frac{t - t_0}{365}}}$
- Encontramos a derivada $NPV'(r)$ e aproximamos $x_1 = x_0 - \frac{NPV(x_0)}{NPV'(x_0)}$.
- Uma trava $x_1 > -1.0$ foi adicionada para evitar números complexos em drawdowns absolutos.

## 3. Risco (Volatilidade e Drawdown)
- **Volatilidade Anualizada:** Desvio Padrão (`std_dev`) das rentabilidades periódicas mensais multiplicada por $\sqrt{12}$.
- **Drawdown:** $DD_t = \frac{Patrimonio_t - Peak}{Peak}$. Monitoramos a queda desde o pico máximo atingido no gráfico em qualquer instante do passado.
- **Max Drawdown:** O menor (mais negativo) valor obtido em $DD_t$.

## 4. Métricas vs Benchmark (IBOV)
- **Beta ($\beta$):** $\frac{Cov(R_p, R_b)}{Var(R_b)}$. Mostra o grau de correlação entre os retornos do portfólio e o Ibovespa.
- **Alpha de Jensen ($\alpha$):** $CAGR_p - (RiskFree + \beta \times (CAGR_b - RiskFree))$. Mostra se o portfólio entregou prêmio de risco verdadeiro frente a gestão passiva.
- **Tracking Error:** Desvio padrão da diferença mensal $[R_p - R_b]$. 

As equações garantem a acurácia de ferramentas de topo (Kinvo, Status Invest), colocando a plataforma na fronteira de eficiência.
