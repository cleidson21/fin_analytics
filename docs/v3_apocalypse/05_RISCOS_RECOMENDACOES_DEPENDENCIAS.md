# 5. Riscos, Recomendações e Dependências

Este documento cobre os **Entregáveis 8, 9 e 10** da reconstrução FinAnalytics V3, oferecendo a visão de risco a longo prazo para o Arquiteto e o Engenheiro de Produto.

---

## 1. Mapa de Dependências Externas (V3)

O sistema foi arquitetado para não depender de lógicas SaaS de terceiros. As dependências que sobraram são utilitárias e comoditizadas.

| Ferramenta / Serviço | Função | Tipo de Dependência | Estratégia de Fallback (Plano B) |
|---|---|---|---|
| **yfinance (Python)** | Cotações diárias e fechamento da B3, S&P 500. | API Pública Gratuita | Se a API do Yahoo quebrar, usar a biblioteca `investpy` (Investing.com) ou API da AlphaVantage. |
| **Banco Central (SGS)** | Séries temporais oficiais do CDI e IPCA. | API Governamental | Raspagem manual de site ou serviço HG Brasil. O BCB tem um uptime de 99,99%. |
| **OpenAI / Anthropic** | Fallback de NLP para transações bancárias. | API de LLM (Paga) | Usar modelos open-source `Ollama` / `Llama 3` no servidor local, ou treinar exclusivamente a camada Vector Database (Embeddings). |
| **PostgreSQL & pgvector** | Armazenamento de dados e busca semântica vetorial. | Banco de Dados Core | Nenhuma. Essa é a fundação. Deve ser instanciado em nuvem gerenciada ou backup pesado. |

---

## 2. Mapa de Riscos (Risk Assessment)

Nenhuma arquitetura é perfeita. Os principais riscos e trade-offs assumidos nesta reconstrução foram:

* **Risco 1: Mudança no Layout dos PDFs da B3**
  * *Natureza*: As corretoras de tempos em tempos mudam a disposição do texto no PDF das Notas de Corretagem.
  * *Impacto*: O parser que extrai as ordens (`TRADES`) pode quebrar, impedindo a atualização automatizada do patrimônio.
  * *Mitigação*: Criar alertas de erro de extração (`import_runs.status = FAILED`) e permitir que o usuário digite os inputs cruciais da nota via interface web em modo "Fallback Manual".
* **Risco 2: Aumento Explosivo no Banco de Dados (Time-Series Bloat)**
  * *Natureza*: Salvar o Snapshot diário do portfólio para os próximos 10 anos pode gerar milhões de linhas na tabela `portfolio_snapshots`.
  * *Impacto*: Lentidão nos gráficos de evolução.
  * *Mitigação*: Implementar rotinas de consolidação automática. Exemplo: Para anos anteriores a D-365, guardar apenas o Snapshot semanal, deletando os diários, ou migrar tabelas analíticas para partições por ano.
* **Risco 3: Falta de Dados Históricos Detalhados (O Efeito MyProfit)**
  * *Natureza*: Ao importar os dados do MyProfit para a V3, não temos as Notas de Corretagem dos últimos anos. Temos apenas `Qtd` e `Preço Médio`.
  * *Impacto*: A rentabilidade retroativa pode sofrer distorções se houverem vendas antigas ou taxas embutidas não mapeáveis.
  * *Mitigação*: Tratar a primeira importação como um "Balanço Inicial Solidificado", onde não recalculamos o passado, assumindo os dados do MyProfit no dia 1 como a verdade absoluta inaugural do V3.

---

## 3. Recomendações Definitivas (Veredito Arquitetônico)

Estas são as recomendações inegociáveis para o desenvolvimento do backend V3 a partir de amanhã:

1. **Abandone o SQLite**: O SQLite e o DuckDB não são suportam eficientemente vetores (`pgvector`) nem oferecem o rigor multi-conexão necessário para processar motor de carteira + IA paralelamente. A stack definitiva deve ser **PostgreSQL**.
2. **Separe o Worker do WebServer**: O parse de Notas de Corretagem, chamadas ao LLM e o recalculo do Sharpe Ratio são operações bloqueantes pesadas de CPU/Rede. Elas não podem rodar síncronas na rota HTTP do usuário. Use **Celery + Redis** ou Background Tasks nativas do framework web (ex: FastAPI Background Tasks, RQ).
3. **Mantenha o Front-end Burro (Dumb Frontend)**: Toda a regra contábil, cálculos complexos e formatação monetária pertencem ao Backend. O Front-end só pode receber JSON com os dados e exibi-los. Não faça contas de Preço Médio no Javascript.
4. **Adote UUID nativo**: Utilize IDs não sequenciais (`uuid v4` ou `v7`) no Postgres. Facilita muito integrações com arquivos externos e impede ataques de enumeração (IDOR).
5. **Teste de Cobertura Implacável no Motor Financeiro**: Você pode errar o layout CSS, mas não pode errar o motor de cotas de TWR ou o Preço Médio. O módulo `core_finance_engine` deve ter **100% de Test Coverage (Unit Tests)**, incluindo *edge-cases* extremos (desdobramento fracionário, juros sobre capital próprio retidos).

---
**Declaração de Encerramento do Arquiteto:**
A especificação `FinAnalytics V3 - Apocalypse Rebuild` está oficializada. Os preceitos estabelecidos garantem escalabilidade para gerir milhões, modularidade para integrações futuras e independência total das startups e APIs fintecheiras perecíveis. O foco agora deve ser 100% transição técnica e execução da Fase 1 de Migração.
