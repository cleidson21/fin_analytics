# DOMAIN MASTER MAP

Este documento detalha o mapeamento funcional sistêmico do produto, dividindo os fluxos operacionais de entrada, processamento, saída e dependências, separados em cada um dos 4 domínios centrais (Bounded Contexts) do FinAnalytics V2.

---

## 1. CORE FINANCE

### Receitas & Despesas
* **Origem:** Transações Ledger (`transactions`).
* **Entrada:** Dados confirmados (id_economico, valor_cents, natureza="INCOME"|"EXPENSE", data).
* **Processamento:** Sumarização via `CashflowService._get_income_sum` e `_get_expenses_sum` filtrado por período.
* **Saída:** Valores formatados e numéricos para Dashboards.
* **Dependências:** `Governance` (Aprovação transfere staging para Ledger).

### Pacing (Ritmo de Gastos)
* **Origem:** `CashflowService`.
* **Entrada:** Mês-Alvo, Transações processadas (Mês-Atual), Transações antigas (Mês-Anterior).
* **Processamento:** Extrai a variação em % de gastos do mês atual contra o mesmo dia do mês anterior (`MoM`). Adiciona projeção do limite de gastos diários (burn rate).
* **Saída:** Percentual e métricas comparativas.
* **Dependências:** `TransactionRepository`, Módulo de Datas.

### Metas (Goals)
* **Origem:** Configuração do usuário (`goals`).
* **Entrada:** Limite de categoria (limit_cents), transações agrupadas.
* **Processamento:** Analisa saldo consumido daquela categoria vs `limit_cents`. Classifica em severidades (GOOD, WARNING, DANGER).
* **Saída:** Percentual consumido da meta.
* **Dependências:** `Category`, `Transaction`.

### Assinaturas (Subscriptions) e Parcelamentos
* **Origem:** Regras manuais em transações (`subscriptions`, column `parcelamento`).
* **Entrada:** Eventos de cartão de crédito.
* **Processamento:** Identificação proativa de "mês sobre mês" de transações recorrentes.
* **Saída:** Alertas de aumento de assinatura / Visualização futura (Cashflow projetado).
* **Dependências:** Extrato do cartão (Fatura) na Staging.

---

## 2. WEALTH

### Posições (Posição de Ativos)
* **Origem:** Corretora CEI/B3 (via `ImportRun`).
* **Entrada:** Ticker, Quantidade, Preço de Aquisição, Preço de Mercado.
* **Processamento:** Consolida `PositionService` puxando a posição do `data_snapshot` mais recente.
* **Saída:** Saldo acumulado (Patrimônio bruto investido vs Atual).
* **Dependências:** Fechamento de Cotações (Import).

### Dividendos (Yield / YOC)
* **Origem:** Eventos em dinheiro (`dividends`).
* **Entrada:** Pagamento líquido em dinheiro.
* **Processamento:** `DividendService` divide o lucro auferido pelo `total_investido` da Posição.
* **Saída:** Indicador Yield On Cost (YOC).
* **Dependências:** `Position` (para base do cálculo), `Transaction` (dividendos costumam bater em conta corrente).

### Rentabilidade e Evolução Mensal (Alpha e Benchmark)
* **Origem:** `PortfolioEvolution` e `Benchmark`.
* **Entrada:** Rentabilidades pontuais mensais (%), Índices (`CDI`, `IBOV`, `IPCA`).
* **Processamento:** `EvolutionService` subtrai a Rentabilidade da Carteira contra os indicadores macro.
* **Saída:** Geração do Alpha (Ex: CDI + 2%). Gráfico de evolução Patrimonial.
* **Dependências:** APIs/Imports externos p/ CDI/IPCA.

### Allocation
* **Origem:** `PositionService`.
* **Entrada:** Total consolidado de cada Ativo.
* **Processamento:** Agrupa por `classe_ativo` (Ação, FII, Renda Fixa) sobre o Total da carteira.
* **Saída:** Fatias de percentual (Pizza) de Asset Allocation.
* **Dependências:** Atributos de Classe preenchidos nos Tickers.

---

## 3. GOVERNANCE

### Importações & Staging
* **Origem:** Arquivos Ofx/Csv ou Integração B3/NuBank (`ImportService`).
* **Entrada:** Evento Bruto (RawEvent).
* **Processamento:** Joga transações para `StagingImport`, posições para `StagingPositions`. Aplica formatação bruta.
* **Saída:** Visão de Quarantine (Quarentena/Draft).
* **Dependências:** `import_artifacts` (armazenamento Blob/S3).

### Reconciliação (Fuzzy Matching)
* **Origem:** Regras do `ReconciliationService`.
* **Entrada:** Linha do Staging vs Transação Existente.
* **Processamento:** Tolerância financeira e Temporal (Janela de D±3 dias).
* **Saída:** Match confirmado (Impede duplicidade).
* **Dependências:** Data de compensação vs Data do evento.

### Aprovação
* **Origem:** Revisão humana ou AI (`ApprovalService`).
* **Entrada:** Lote da ImportRun.
* **Processamento:** Promove dados do `Staging` para a Tabela Principal (`Ledger` - Transactions/Positions). Atualiza status de PENDING para APPROVED.
* **Saída:** Fechamento do lote.
* **Dependências:** Sistema de rollback seguro via ON DELETE CASCADE (se falhar, cai tudo da staging ou da própria Ledger relacionada ao `import_run_id`).

---

## 4. AI LAYER

### Regras (Rule Engine)
* **Origem:** Regras cadastradas e priorizadas via `RuleEngineService`.
* **Entrada:** Descrição original do OFX.
* **Processamento:** Regex matching puro, respeita ranking de prioridade (`confidence_score`).
* **Saída:** Categoria Semântica determinística.
* **Dependências:** Nenhuma externa.

### Classificação Automática (Pipeline)
* **Origem:** Cascata de `ClassificationEngineService`.
* **Entrada:** Descrição Bruta sem Match de Regra e sem Match de Reconciliação.
* **Processamento:** Invoca AI Provider.
* **Saída:** Categorização Probabilística inferida.
* **Dependências:** Interface `AIProviderInterface` (Mock / OpenAI / Gemini).

### Aprendizado (Learning)
* **Origem:** Ajustes manuais efetuados pelo usuário na Ledger (`classificacao_fonte='USER'`).
* **Entrada:** Mudança de Categoria.
* **Processamento:** Gera novos pares de Descrição -> Categoria (Dataset).
* **Saída:** Geração de blocos *Few-Shot* injetados nos Próximos Prompts.
* **Dependências:** Core Finance (Transactions).

### Gestão de Prompts (e Custos)
* **Origem:** `PromptVersionService` e `AIRunService`.
* **Entrada:** Nova versão do template (Prompt) ou uso de token.
* **Processamento:** Bloqueia prompts inativos, mede `tokens_input` e `tokens_output`, multiplica pela tabela de preços do GPT.
* **Saída:** Custo estimado diário da Inteligência.
* **Dependências:** Conexão nativa com a Pipeline de Importação/Aprovação.
