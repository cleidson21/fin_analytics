# FIN ANALYTICS V2 - ARCHITECTURE MASTER PLAN

Este documento consolida as diretrizes da respectiva categoria da Fase 10.

# V2 DOMAIN ARCHITECTURE - FASE 10.3

Este documento estabelece o mapeamento de Bounded Contexts (Contextos Delimitados) seguindo princípios de Domain-Driven Design (DDD). O sistema Fin Analytics V2 abandona a estrutura monolítica plana e abraça uma modularidade severa baseada em quatro domínios principais.

---

## 1. CORE FINANCE DOMAIN
Domínio responsável pelas movimentações diárias, orçamento e controle transacional clássico.

### Subdomínios e Entidades
* **Transactions:** Livro-razão (ledger) estrito de entradas e saídas consolidadas. Entidades não podem ser alteradas sem rastro de auditoria.
* **Accounts (Futuro):** Agrupador lógico para fontes pagadoras/recebedoras (Nubank, Pierre, Banco do Brasil).
* **Categories:** Hierarquia padronizada (`macro_categoria`, `sub_categoria`, `natureza`, `perfil`).
* **Cashflow (Fluxo de Caixa):** Agregação matemática diária e mensal para o painel de Pacing.
* **Installments (Parcelamentos):** Motor de Agrupamento. Regras baseadas em Regex sobre `Transactions` para projetar fluxo de passivo futuro.
* **Subscriptions (Assinaturas):** Motor que identifica e projeta o custo anual de categorias específicas (`macro_categoria='ASSINATURAS'`).
* **Goals (Metas):** Limites estabelecidos sobre o Cashflow com métricas de Severidade (Good/Warning/Danger).

---

## 2. WEALTH DOMAIN
Domínio responsável por ativos de investimento, exposição a mercado e renda passiva (B3, Renda Fixa).

### Subdomínios e Entidades
* **Positions (Posições em Aberto):** A carteira atual. Fotografia de quantidade, preço médio e capital aplicado.
* **Portfolio Evolution (Evolução):** Registro longitudinal (timeline mensal) do tamanho do patrimônio, deltas e rentabilidade.
* **Dividends (Proventos):** Direitos declarados e recebidos de ativos (Rendimentos, JCP, Dividendos).
* **Allocation:** Motor de agrupamento por Classes e Subclasses gerando pesos percentuais (%) contra o Capital Total da Carteira.
* **Asset Detail:** Visão agnóstica de um Ticker combinando histórico de preços (Market Data externa) com a Posição Pessoal e Timeline.
* **Benchmarks:** Dados macroeconômicos independentes da carteira (CDI, IBOV, S&P500, IPCA) usados para subtração aritmética (`Alpha`).

---

## 3. GOVERNANCE DOMAIN
O motor blindado de integridade, ingestão e saneamento. Este domínio é o gatekeeper: NENHUM dado entra no `Core Finance` ou no `Wealth` sem passar por ele.

### Subdomínios e Entidades
* **Imports (Run & Status):** O lote de importação. Representa a sessão de um upload.
* **Staging:** A "Área de Quarentena". Tabelas espelho (`staging_imports`, `staging_positions`, `staging_dividends`) que aguardam aprovação manual antes da efetivação atômica.
* **Reconciliation:** Motor de fusão. Conecta extratos diferentes. Exemplo clássico: Liga o recebimento de extrato bancário com a nota de dividendo da corretora usando janela de `±3 dias` (Fuzzy Logic).
* **Audit:** Trilha de logs de qualquer alteração de estado nos domínios.
* **Database Admin:** Execução e monitoramento contínuo de otimizadores da base (`VACUUM`, `ANALYZE`).

---

## 4. AI LAYER DOMAIN
A camada inteligente autônoma de categorização semântica e treinamento iterativo.

### Subdomínios e Entidades
* **Rules (Motor de Regras Estáticas):** O coração de categorização do sistema. Padrões JSON com descrições (`description_matches`) traduzindo entradas para classificações. Prioridade 1 antes da Inteligência Artificial Gen AI.
* **Prompt Versions (Governança de IA):** Controle de versão de *System Prompts* para evitar degradação do modelo (LLM Drift).
* **AI Runs:** Log financeiro e contábil sobre requisições ao LLM (tokens, custo, falhas de schema JSON).
* **Classification Engine:** Motor orquestrador do funil: `Reconciliation -> Regras -> IA Gen -> Fallback`.
* **Learning Engine:** Exportador implícito de transações humanas aprovadas que geram retroalimentação (Few-Shot Generation) para novas subidas de LLM.


---

# V2 DATABASE ARCHITECTURE - FASE 10.3

Projeto definitivo do Schema de Persistência, pautado na especificação original (`DATABASE_SPEC.md`), com refinamento para mitigar riscos de integridade.

---

## 1. TABELAS MANTIDAS (Core V2)

Estas tabelas representam o alicerce insubstituível. Suas estruturas originais e chaves primárias/tipagens estão homologadas.

1. **`users`**: Base de autenticação e perfis globais.
2. **`import_runs`**: Tabela-Mestra. É a chave primária que amarra toda a cascata do sistema.
3. **`raw_events`**: Hash de deduplicação semântica. Única porta de entrada de Parser.
4. **`transactions`**: O Livro-Razão universal. Herda tudo com Foreign Key de `import_runs`.
5. **`positions`** e **`dividends`**: Core isolado do Wealth.
6. **`portfolio_evolution`**: Snapshot da evolução e comparativo de mercado (Benchmarks).
7. **`rules`**, **`ai_runs`**, e **`prompt_versions`**: Repositório persistente do aprendizado de máquina.
8. **As 4 Tabelas de Staging**: (`staging_imports`, `staging_positions`, `staging_dividends`, `staging_portfolio_evolution`). Buffer vital para aprovação humana.
9. **`event_links`**: Persistência orgânica do motor de Reconciliação (Fuzzy Matches).
10. **`audit_log`**: Trilha inalterável de governação administrativa.

## 2. RELACIONAMENTOS, FOREIGN KEYS E CASCATAS ESTRITAS

A reconstrução do Database V2 **exige** a implementação cirúrgica dos relacionamentos em banco relacional:

* **Espinha Dorsal de Deleção:** A tabela `import_runs` possui um ID UUID. 
* **Regra de Diamante (ON DELETE CASCADE):** As tabelas `transactions`, `positions`, `dividends` e as `staging_*` DEVEM possuir o foreign key `import_run_id` referenciando `import_runs(id) ON DELETE CASCADE`. Isso assegura que cancelar uma importação expurgue o dado por toda a capilaridade da infraestrutura.
* **Integridade Limite:** `raw_events` DEVE estar protegido por `UNIQUE(semantic_id)` para impedir duplicação via importações consecutivas idênticas.

## 3. VIEWS E ÍNDICES (Otimizações Mandatórias)

### Índices Primários (B-Tree Recomendado)
* `transactions(data)` e `transactions(natureza)` (Crítico para a performance dos endpoints de Pacing e Dashboard Sumário).
* `positions(ticker)` e `dividends(ticker)` (Crítico para endpoints de Detalhe de Ativo).

### Materialized Views & Views
A `V2` consolidará a visão de treinamento de IA de forma isolada do código Python.
* **VIEW Obrigatória (`vw_rules_training_dataset`)**: View conectando as descrições em `transactions` com as classificações curadas manualmente pelo usuário para alimentar a tabela `ai_runs` e treinar as `prompt_versions`. Não se aplica Materialized View no SQLite, mas se a reconstrução adotar PostgreSQL, esta deve ser materializada e ter atualização programada.

## 4. TABELAS ELIMINADAS (Depreciadas / Código Morto)
O documento `DEAD_CODE_REPORT.md` já listou o expurgo obrigatório.
* **ELIMINAR:** `etl_runs_legacy`.
  * *Motivo:* Resquício obsoleto do MVP de ETL v1. Substituída inteiramente pelas engrenagens acopladas a `import_runs`.


---

# V2 BACKEND ARCHITECTURE - FASE 10.3

Desenho arquitetural da API (Backend V2), projetado para substituir o monólito anterior mantendo os rígidos contratos OpenAPI.

---

## 1. DTOs E SCHEMAS (API_CONTRACT_FREEZE.md)
* **Status:** Imutáveis. As camadas DTO (`DashboardSummaryV2`, `PacingV2`, `InstallmentsSummary`, `CategoryComparison`, `AssetAllocation`) não podem sofrer *camelCasification* ou mudanças de tipo primitivo sem gerar catástrofe visual no Frontend. As rotas descritas na Matriz de Contrato devem ser implementadas *byte* por *byte*.

## 2. CAMADAS DE ISOLAMENTO (Arquitetura Hexagonal recomendada)
A V2 precisa quebrar o modelo espaguete e isolar responsabilidades nos seguintes pilares:

### A. Repositories (Persistência Agnóstica)
* `FinancialRepository`: Agrupador de operações SELECT em `transactions`, `positions`, e `dividends`. Exposto à camada superior sem amarrações de ORM complexas.
* `GovernanceRepository`: Operador exclusivo das tabelas `staging_*`, `import_runs`, `raw_events` e `audit_log`.

### B. Services (Business Logic Pura)
* `AnalyticsService`: Especialista em cálculos do Core Finance (Pacing, Categorização e Buckets de Parcelamento). Responsável por extrair do Repository e empacotar no DTO estático.
* `WealthAnalyticsService`: Especialista em Rentabilidade e Alpha. Processa as subtrações complexas de `ibov_acumulado` vs `rentabilidade_acumulada`.
* `ETLService` (Reconciler/Classifier): A máquina de ingestão e agrupamento difuso (`Fuzzy Logic`). Deve atuar isolada em *Workers* paralelos caso possível.

## 3. ACOPLAMENTOS E DESACOPLAMENTOS CRÍTICOS

### Pontos de Risco (Acoplamento Perigoso)
* **`WealthAnalyticsService` vs `positions/dividends`**: Na V1, a arquitetura cruza dados em memória somando Arrays massivos. 
* **O Reconciler & Banco**: Atualmente, as janelas Fuzzy do Classificador processam lógicas cruzadas on-the-fly (`± 3 dias`).

### Pontos que DEVEM ser Desacoplados na V2
1. **Inteligência Artificial (LLMs):** A chamada ao provedor OpenAI/Gemini deve rodar via fila assíncrona (ex: Celery ou BackgroundTasks do FastAPI). Transações do usuário não podem ficar penduradas em _timeout_ de rede aguardando resposta de tokens do LLM.
2. **Cálculo de Parcelamento (Installment Engine):** O algoritmo de Regex e Bucket deve ser abstraído em uma classe Helper separada do `AnalyticsService` principal, devido a sua complexidade intrínseca, permitindo Unit Tests isolados apenas da Matemática e do Motor de Exclusão de Meses.

## 4. MAPEAMENTO DE ROTAS (Controllers Principais)
* **`/dashboard/*`**: O escopo unificado de leituras do mês de contexto e pacings de consumo (Transactions, Subscriptions, Installments).
* **`/investments/*`**: Exposição pura de alocação de risco (Asset Details, Evolution, Allocation).
* **`/governance/*`**: Os POSTs críticos de aprovação humana de lotes da tabela staging (`/imports/{run_id}/confirm`) e as funções utilitárias do DBA (`/vacuum`).


---

# V2 FRONTEND ARCHITECTURE - FASE 10.3

O layout final do Next.js (React) na reengenharia da camada visual.

---

## 1. PACOTES E ESTRUTURA DE PASTAS (App Router)

A nova hierarquia do sistema Next.js deve banir diretórios flutuantes e segregar os módulos de visualização estritos.

* **`/src/app/`**: A camada pura de roteamento (`page.tsx`) e agrupamento estrutural (`layout.tsx`). Nenhuma lógica de fetch complexa ou componentes visuais massivos devem residir diretamente na raiz desses arquivos.
  * `/app/(core)/dashboard`
  * `/app/(core)/transactions`
  * `/app/(core)/subscriptions`
  * `/app/(wealth)/investments`
  * `/app/(wealth)/dividends`
  * `/app/(admin)/governance`

* **`/src/components/`**: A camada de apresentação visual pura. 
  * `/components/ui/` (Botões, Inputs Genéricos - Shared).
  * `/components/domain/wealth/` (Gráficos Recharts Específicos, Ex: `AllocationDonut`, `GrowthComposedChart`).
  * `/components/domain/dashboard/` (Ex: `PacingCard`, `CategoriesCard`).

* **`/src/hooks/`**: O motor reativo atrelado aos JSONs.
  * Onde os fetchs `useTransactions`, `useGrowthData` ou `useAllocationData` operam de maneira encapsulada via SWR ou React Query.

* **`/src/stores/`**: Gerenciador de estado global.
  * Isolado primariamente em `wealthStore` (Zustand ou Context API) para evitar a prop-drilling excessiva das abas do sistema Patrimonial.

## 2. SEPARAÇÃO ARQUITETURAL REACT

A refatoração visual na V2 DEVE respeitar limites agressivos:
* **Componentes de Domínio:** Não podem conter CSS Hardcoded de cor global (devem referenciar tokens do Tailwind). Respondem a um DTO mapeado (Ex: Passa-se o objeto inteiro `DashboardSummaryV2` para o componente).
* **Componentes Compartilhados (Shared/UI):** Devem ser burros (Dumb Components). Tabelas genéricas, Dropdowns e Formulários não podem ter dependência de Hooks de Negócio como o `useAuth` ou de pacotes Recharts importados acidentalmente.
* **Layouts & Providers:** A ingestão primária (TopNav, Sidebar, DarkMode) deve ser envelopada apenas nos layouts globais limitados às necessidades do Módulo (O Wealth Layout possui a aba de Patrimônio/Renda, o Core Dashboard tem outras).


---

# V2 MIGRATION PLAN - FASE 10.3

O plano estratégico de reconstrução progressiva respondendo as garantias de mitigação de risco de transição do código.

---

## 1. O que pode ser reaproveitado?
* **O Frontend Visual Base (Tailwind + Recharts):** Como os contratos DTO estáticos do Backend garantem a estabilidade dos dados expostos, praticamente todos os componentes "Dumb" (cards, tabelas, gráficos) construídos no `frontend/src/components` são reaproveitáveis quase na íntegra.
* **Os Parsers de PDF/CSV (MyProfit / Nubank):** O processamento puramente algorítmico e bruto (transformação de um extrato do banco XYZ para dicionário Raw) independe da lógica de banco de dados e pode ser portado como módulo utilitário isolado (Helper).

## 2. O que deve ser descartado?
* O arquivo monolítico de regras do `Categorizer` se ele não for traduzível para o formato contínuo de Regex JSON da nova tabela `rules`.
* Funções e rotas utilitárias descritas no `DEAD_CODE_REPORT.md` (rotas legadas que não possuíam conexão com o React Frontend e rotas de limpeza órfã `orphan-cleanup` que foram centralizadas).
* As dependências de Framework excessivamente amarradas na Base de Dados (qualquer consulta SQL string embarcada diretamente num *Controller* API).

## 3. O que deve ser reescrito?
* Toda a camada relacional e as ORMs/Queries do Banco. Elas precisam receber as amarrações do UUID novo (`import_runs_id`) para herdar a funcionalidade da exclusão em Cascata em caso de reprovação governamental na Interface (ON DELETE CASCADE).
* A Governança e o funil ETL devem atuar de modo totalmente autônomo através de rotinas isoladas de *BackgroundTasks*, sem congelar a requisição de API do Front End no momento da Ingestão.

## 4. O que pode ser copiado sem risco?
Apenas regras matemáticas e estáticas da inteligência de domínio (`BUSINESS_RULES.md`):
* A fórmula de Yield on Cost.
* O cálculo Linear do Alpha (Benchmark Delta).
* As lógicas de "±3 dias Fuzzy" e as tolerâncias percentuais (`0.01 / 0.02`) do Event Reconciler.
* A RegEx Estrita e o Pacing Matemático com detecção Mês vs Mês anterior, substituindo apenas a extração direta do Banco SQL pelas abstrações dos novos Repositórios criados.


---

# V2 DEBT ELIMINATION PLAN - FASE 10.3

Comando final de higienização arquitetural e isolamento de dívidas técnicas mapeadas que foram catalogadas mas não serão portadas.

---

## 1. CÓDIGO MORTO (Dead Code)
* Eliminar toda invocação à tabela legado `etl_runs_legacy`. O sistema V2 não migrará esta tabela e usará a raiz `import_runs` com status nativo (PENDING, CONFIRMED).

## 2. CÓDIGO LEGADO A DESCARTAR
* O endpoint monolítico `/import-unified` foi abandonado pelo Frontend e deve ser cortado do escopo.
* O endpoint `/categories/comparison`. Apenas a leitura de Categorização direta será provida ao Front, o qual renderizará os Comparisons através de hooks independentes ou de DTO reescrito sem depender da aba órfã na API.

## 3. SERVIÇOS ACOPLADOS DEMAIS
A reconstrução tem como dever fatiar o atual `WealthAnalyticsService`, que centraliza toda a lógica de investimentos numa classe monstruosa. A reengenharia V2 dividirá entre:
* `PositionService` (Pesos e Alocações da Fotografia Atual).
* `DividendService` (Proventos, Yield e Históricos Anuais).
* `EvolutionService` (Os gráficos em Delta, capturando o patrimônio mensal contra Benchmarks como CDI/IBOV).

## 4. ENDPOINTS REDUNDANTES E DE GOVERNANÇA OBSOLETA
* Eliminar a interface crua de logs passivos `GET /audit-logs/{log_id}` (Substituída por `GET /governance/audit` unificado da nova Governança).
* Eliminar a requisição `POST /database/orphan-cleanup`. Na V2, o saneamento atômico e re-indexação ocorrerá em apenas um lugar: `/governance/vacuum` que invoca os otimizadores atômicos (VACUUM/ANALYZE), prevenindo rotas soltas que operem destrutivamente sem registro global da Auditoria.

## 5. TABELAS REDUNDANTES
* Conforme apontado pelo Database Spec e Dead Code Reports, todas as Views não materializadas que tentarem imitar cruzamentos voláteis pesados devem ser otimizadas pela via do Frontend e a tabela `etl_runs_legacy` abandonada integralmente na migração.


---

