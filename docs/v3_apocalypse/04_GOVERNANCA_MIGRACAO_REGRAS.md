# 4. Governança, Migração e Regras de Negócio

Este documento cobre a **Etapa 7** e os **Entregáveis 4 e 5** do FinAnalytics V3.

---

## 1. Governança e Rastreabilidade

O FinAnalytics V3 não permite a edição arbitrária (UPDATE) do passado em tabelas de Ledger (Transações e Trades) sob pretexto nenhum, garantindo qualidade nível institucional.

* **Auditoria Completa**: A tabela `import_runs` registra exatamente qual usuário fez o upload de qual documento (`import_artifacts`), em qual momento, e quais UUIDs de transações foram gerados por ele.
* **Rollback Seguro**: Se uma importação der erro ou trouxer dados corrompidos, o sistema executa um *Hard Delete* ou *Soft Delete* condicionado ao ID da `import_run`. `DELETE FROM transactions WHERE run_id = X`.
* **Reprocessamento Transparente**: Se o usuário decidir corrigir manualmente uma categoria definida por erro pela IA, uma linha entra na tabela `classification_feedback`. O sistema dispara um reprocessamento em background nas `transactions` retroativas baseadas no mesmo *merchant* utilizando a nova instrução.

---

## 2. Plano de Migração (Cortando o Cordão Umbilical)

Para garantir que o código legado morra sem perdas patrimoniais, o seguinte plano "Zero-Downtime" será executado em 4 fases:

### FASE 1: Ingestão Passiva (Shadow Mode)
* O banco de dados V3 (`fin_analytics_v3`) é instanciado em PostgreSQL.
* O sistema consome os mesmos extratos do Nubank que o Pierre processava.
* A base do MyProfit (`Acoes.csv`, `Proventos.csv`) será ingerida em um script de conversão one-off, transformando o saldo estático em eventos sintéticos (`TRADES` históricos) para criar o "Balancete de Abertura" da carteira.
* **Validação**: Verifica se a Cota V3 e Patrimônio V3 bate 100% com o CSV do MyProfit.

### FASE 2: Habilitação do Ledger V3
* O pipeline do banco passa a ingerir dados brutos novos (Faturas CSV e Extrato).
* O motor de IA é ativado e começa a treinar. Pierre é desligado e desativado da arquitetura.

### FASE 3: Motor de Corretagem Nativo
* O usuário para de usar o MyProfit. Passa a fazer o upload do PDF da Nota de Corretagem da B3 diretamente no V3.
* O sistema fará o parse. O Preço Médio passará a ser gerenciado 100% *in-house*.
* O `yfinance` e `BCB (SGS)` são configurados no CRON para rodar às 23h, atualizando a `portfolio_snapshots`.

### FASE 4: Sunset do Legado
* Banco `.db` legado do SQLite deletado. Código Python antigo deletado. V3 se torna a fonte exclusiva da verdade.

---

## 3. Regras de Negócio Definitivas (Business Rules)

Estas regras pautam a lógica dos backend services e garantem que o sistema seja impermeável a bugs comuns de finanças.

### Regra 1: "Conservação de Massa" Financeira
Nenhuma categoria de despesa, por mais customizada que seja, pode distorcer a soma do extrato bruto. A soma das categorias dentro de um mês (incluindo "Ignoradas" e "Transferências") **DEVE SER ESTRITAMENTE IGUAL** à soma das entradas e saídas reportadas pelo banco.

### Regra 2: Isolamento de Contas Correntes vs Contas de Custódia
O dinheiro enviado do Nubank para a corretora (NuInvest) é categorizado estritamente como **TRANSFERÊNCIA ENTRE CONTAS MÚTUAS** (Internal Transfer). Isso tira o montante do gráfico de despesas. A aquisição do ativo (Ação) na conta NuInvest deduz o saldo da conta corretora, trocando *Liquidez* por *Ativo Financeiro*. O patrimônio total do usuário não altera durante a transferência, só a alocação.

### Regra 3: Custos Embutidos no PM (Preço Médio)
É proibido separar a taxa da B3 e a taxa de corretagem como uma despesa contábil no Ledger de Despesas Pessoais do usuário. Esses custos **pertencem** ao preço médio do ativo e reduzem o lucro tributável para fins de Receita Federal. O gasto com corretagem não afeta o balanço pessoal mensal de "Saúde Financeira".

### Regra 4: Tratamento de IRRF sobre Proventos e Fundos
Dividendos de FIIs não têm IRRF, mas JCP de ações têm (15%). O valor registrado no Ledger deve ser SEMPRE o valor **Líquido** (creditado em conta). O imposto retido na fonte deve ser gravado nas tabelas de Investimento caso necessário, mas o fluxo de caixa opera exclusivamente em regime de caixa (líquido).

### Regra 5: Faturas de Cartão não são Fluxo de Caixa Direto
Quando o usuário passa o cartão de crédito em um restaurante em Maio, a transação não abate o saldo de caixa do usuário em Maio. Ela afeta o saldo devedor do passivo (Fatura). O saldo do caixa (Cashflow) só será afetado no momento do pagamento efetivo da Fatura em Junho. O motor de Analytics é responsável por visualizar as despesas sob duas óticas separadas: Regime de Competência (quando passou o cartão) e Regime de Caixa (quando pagou a fatura).
