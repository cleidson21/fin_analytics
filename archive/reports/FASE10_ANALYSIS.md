# FASE 10 — BUSINESS VALUE EXPANSION & FINANCIAL INTELLIGENCE

## ETAPA 1 — AUDITORIA DE CAPACIDADES EXISTENTES

### 1. Serviços e Endpoints Financeiros Atuais
- **FinancialService & Endpoints:** Gestão de Transações, Sumário de Contas, Fluxo de Caixa (Receitas vs Despesas), Patrimônio Líquido atual.
- **WealthAnalyticsService & Endpoints:** Evolução Patrimonial, Distribuição de Alocação por Classe de Ativo, Resumo de Dividendos, Rentabilidade Mensal e Acumulada.
- **AnalyticsService:** Agregação de despesas por categoria, rateio mensal.
- **GovernanceService:** Rastreabilidade de importações, curadoria de regras, auditoria de modificações.

### 2. Dados Disponíveis (Unexploited Value)
- **Transactions:** Histórico completo com data, valor e categoria. (Atualmente usado apenas para extrato e gráficos passivos).
- **Positions:** Quantidade, preço médio, cotação atual e valor investido. (Atualmente usado apenas para montar o dashboard de alocação estático).
- **Dividends:** Proventos recebidos com data e valor. (Atualmente usado apenas para histórico de barras estático).
- **Portfolio Evolution:** Patrimônio histórico mês a mês e IBOV/CDI. (Usado para gráfico linear simples).
- **Governance:** Regras de categorização, prompts versionados, datasets isolados (`vw_rules_training_dataset`).

---

## ETAPA 2 — GAP ANALYSIS (Oportunidades Latentes)

Ao analisar os dados existentes *vs* o que o usuário consome, identificamos que o sistema atual é **descritivo** (mostra o passado e presente), mas ainda não é **prescritivo** (sugere o que fazer) nem **preditivo** (projeta o futuro).

| Funcionalidade Potencial | Impacto | Complexidade | Dependências | Precisa IA? |
|--------------------------|---------|--------------|--------------|-------------|
| Rebalanceamento de Carteira | ALTO | BAIXA | Apenas tabela `positions` (já existe) | NÃO |
| Concentração de Risco | ALTO | BAIXA | Apenas tabela `positions` (já existe) | NÃO |
| Projeção de Dividendos | ALTO | BAIXA | Apenas tabela `dividends` (já existe) | NÃO |
| Metas Financeiras (Goals) | ALTO | MÉDIA | Criar nova tabela `goals` | NÃO |
| Insights Automáticos | ALTO | MÉDIA | Heurísticas em `transactions`/`positions` | NÃO |
| Score Financeiro (Health) | MÉDIO | MÉDIA | Fórmulas sobre `transactions` | NÃO |
| Categorização de Staging | ALTO | ALTA | Endpoint API LLM (ex: Gemini) | SIM |
| Análise Comportamental | ALTO | ALTA | Agregação complexa + LLM | SIM |

---

## ETAPA 3 — DEFINIÇÃO DA PRÓXIMA ONDA DE PRODUTO

### Categoria A — Alto valor / Baixa complexidade (Prioridade Imediata)
*Utiliza 100% da arquitetura atual, necessitando apenas da criação de lógicas em novos arquivos no nível de Service, sem mexer no banco de dados.*
- **Rebalanceamento de Carteira (`RebalanceService`):** O usuário define pesos alvos (ex: 30% FIIs, 70% Ações). O serviço lê `positions`, compara com a cotação atual e gera a lista de "Onde aportar este mês".
- **Concentração de Carteira:** Analisar risco informando se algum ativo único representa mais de X% do patrimônio.
- **Projeção de Renda Passiva:** Calcular a média de dividendos dos últimos 12 meses, calcular o *Yield on Cost* (YOC) atual e projetar a renda dos próximos 12 meses passivamente.

### Categoria B — Alto valor / Média complexidade (Prioridade Secundária)
*Exige novas tabelas pequenas ou agregação lógica pesada.*
- **Metas Financeiras (Goal Planning):** Tabelas de metas (ex: Trocar de carro, Reserva de Emergência) integradas com o `FinancialService` para mostrar o % de completude.
- **Insights Automáticos Genéricos:** Motor de heurísticas rodando sob demanda. (Ex: *"Você gastou 30% a mais com Restaurantes este mês comparado à sua média"*, ou *"Sua reserva de emergência está abaixo de 6 meses do seu custo de vida"*).

### Categoria C — Inteligência Artificial (Prioridade de Automação)
*Exige chamadas externas (latency) e integrações assíncronas.*
- **Categorização Automática:** Integrar LLM no Staging para não precisar mais de classificação manual em transações desconhecidas.
- **Copilot Financeiro:** RAG simples onde a IA lê os metadados do repositório financeiro para responder: "Por que não bati minha meta de economia este mês?".
