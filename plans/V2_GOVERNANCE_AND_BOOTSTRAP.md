# FIN ANALYTICS V2 - GOVERNANCE AND BOOTSTRAP

Este documento consolida as diretrizes da respectiva categoria da Fase 10.

# SYSTEM FREEZE REPORT - FASE 10.2

Relatório oficial de validação e rastreamento do Congelamento Arquitetural (System Freeze). Todos os arquivos encontram-se selados sob a árvore Git e preparados para o processo de reconstrução segura (V2).

---

## 1. DADOS DO CONGELAMENTO

* **Commit SHA (HEAD):** `a13da534113198091e279e49ca97c951f800c550`
* **Data do Congelamento:** `Sun Jun 14 21:27:43 2026 -0300`
* **Branch Oficial de Selagem:** `main`

## 2. ARTEFATOS DE AUDITORIA PRESERVADOS

A Engenharia Reversa massiva (Fase 10) produziu documentos contratuais essenciais para a reescrita do sistema sem acesso aos arquivos `*.py` originais. Todos os 12 relatórios iniciais foram consolidados com sucesso em um pacote mestre e commitados de forma limpa:

* `SYSTEM_REBUILD_PACKAGE.md` (Contém a fusão de: Product Spec, Inventory Frontend/Backend, Database Spec, Feature Matrix, Business Rules, API Contracts, Rebuild Score, Bug Traceability, Dead Code, Flow Map, e V2 Requirements).
* `GIT_BASELINE_REPORT.md` (Rastreamento do lixo e *state* anterior à ramificação).
* `BRANCH_GOVERNANCE.md` (Contratos de trabalho entre as branches).
* `REBUILD_EXECUTION_PLAN.md` (Ordem cronológica da Fase 10.1).

## 3. ARQUIVOS FUNCIONAIS INCLUÍDOS (BASE LEGADA)

Todos os diretórios de código encontram-se travados na foto do Commit `a13da534...`. 
* `/frontend/src/` (Componentes estáticos, Views Tailwind, App Router).
* `/app/api/` (A camada monolítica V1 Python + FastAPI).
* `/database/` (Schemas SQLite e Migrations base).

*Observação:* A working tree está **limpa** (`nothing to commit, working tree clean`). Não há vazamento de escopo.


---

# BRANCH GOVERNANCE - FASE 10.1

Este documento estabelece as regras arquiteturais definitivas para o fluxo de reengenharia (V2) do Fin Analytics.

A branch `main` passa a atuar como um repositório imutável de consulta (System Freeze). Nenhuma feature será desenvolvida nela. Todo o ciclo de vida do novo produto ocorrerá de forma segmentada e orquestrada pelas novas ramificações.

---

## 1. ESTRUTURA E OBJETIVOS DAS BRANCHES

* **`main` (Congelada)**
  * **Objetivo:** Ponto de restauração absoluto e histórico documentado. Contém o pacote `SYSTEM_REBUILD_PACKAGE.md` e o código da fase de transição (V1.5).
  * **Responsabilidade:** Servir de espelho consultivo. Só recebe merges em caso de patches de segurança emergenciais em ferramentas documentais.

* **`legacy-v1`**
  * **Objetivo:** Arquivamento do MVP inicial. Útil para consultar lógicas superadas que foram depreciadas do modelo V2 (como a tabela `etl_runs_legacy`).
  * **Responsabilidade:** Apenas leitura.

* **`database-v2`**
  * **Objetivo:** Isolamento da primeira etapa da reengenharia. Modelação do novo banco, schemas, stored procedures (se aplicável) e fluxos estritos de integridade (`ON DELETE CASCADE`).
  * **Responsabilidade:** Time de Arquitetura / DBAs.

* **`backend-v2`**
  * **Objetivo:** Refatoração estrita da API. Seu trabalho é replicar integralmente o que está definido no `API_CONTRACT_FREEZE.md` e no `BUSINESS_RULES.md`, garantindo que os mesmos endpoints existam (com a mesma assinatura) mas escritos sob a nova fundação e conectado ao `database-v2`.
  * **Responsabilidade:** Time de Engenharia Backend (FastAPI / Outros).

* **`frontend-v2`**
  * **Objetivo:** Otimização visual, atualização de pacotes (Next.js App Router) e eventual migração de componentes. Durante grande parte do tempo, atuará consumindo endpoints de mock baseados nos contratos V1 congelados.
  * **Responsabilidade:** Time de Engenharia Frontend.

* **`integration-v2`**
  * **Objetivo:** Atuar como o "novo Release Candidate". É a branch onde `backend-v2`, `database-v2` e `frontend-v2` se chocam para provar que a aplicação Fim-a-Fim está funcional sem regressões em relação à versão congelada.
  * **Responsabilidade:** Tech Lead / DevOps.

---

## 2. REGRAS DE MERGE E DEPLOYMENT

1. **Separação de Domínios:** É terminantemente proibido commitar alterações de UI na `backend-v2` ou alterações de schema na `frontend-v2`. Cada squad possui um pipeline cego.
2. **Pull Requests (PR) com Prova Contratual:** O Backend só pode dar Merge para `integration-v2` se todos os testes E2E do Swagger provarem consistência com o `API_CONTRACT_FREEZE.md`.
3. **Bloqueio da Main:** Não haverá Merges de features novas para a `main`. A `main` só será atualizada quando o produto da ramificação `integration-v2` for coroado como a versão estável final de produção (v2.0.0 Release).


---

# REBUILD EXECUTION PLAN - FASE 10.1

Este documento atua como o mapa tático definitivo de execução sequencial para a nova reengenharia. Devido ao rígido bloqueio contratual e de dependências estabelecido na Auditoria Fase 10, o processo de refatoração deve obedecer estritamente a cascata descrita abaixo.

---

## ORDEM DE RECONSTRUÇÃO V2

### 1. Database V2
* **Branch Base:** `database-v2`
* **Início Imediato:** Sim.
* **Ações:** 
  1. Erguer instâncias de persistência espelhando o `DATABASE_SPEC.md`.
  2. Implementar integridade rígida (Ex: Chaves estrangeiras com `ON DELETE CASCADE` da `import_runs`).
  3. Descartar definitivamente tabelas legadas contidas no `DEAD_CODE_REPORT.md` (como `etl_runs_legacy`).
* **Critério de Conclusão:** O schema.sql (ou migrations) deve rodar de ponta a ponta sem falhas em um container limpo.

### 2. Backend V2
* **Branch Base:** `backend-v2`
* **Início Imediato:** Pode começar as definições arquiteturais (Ex: Setup de containers, Swagger/OpenAPI Dummy), mas a conexão com o banco deve aguardar a conclusão da etapa `Database V2`.
* **Ações:**
  1. Desenvolver Mocks que correspondam nativamente às respostas do `API_CONTRACT_FREEZE.md`.
  2. Implementar as leituras de repositório (Wealth, Dashboard, Subscriptions).
  3. Reconstruir a inteligência pesada: Motor Fuzzy de Reconciliação e Prioridade de IA.
* **Critério de Conclusão:** Cobertura de testes comprovando as matemáticas exatas exportadas no `BUSINESS_RULES.md`.

### 3. Frontend V2
* **Branch Base:** `frontend-v2`
* **Início Imediato:** Pode iniciar readequações de CSS e componentes agnósticos de imediato. A reconstrução de hooks espera os "Mocks" do Backend V2.
* **Ações:**
  1. Migração de pacotes e limpeza de lixo visual.
  2. Manter amarrações idênticas aos `Hooks` descritos no `FEATURE_MATRIX.md`.
  3. Adaptar novos comportamentos (se houver), mas garantindo renderização exata dos gráficos (Recharts) com as chaves JSON.
* **Critério de Conclusão:** Navegação completa sem quebra de páginas em console (React Exceptions), utilizando dados fake.

### 4. Integration V2
* **Branch Base:** `integration-v2`
* **Início Imediato:** Não.
* **Ações:**
  1. É o estágio de "Release Candidate" da esteira DevOps. O banco novo hospeda a base populada. O Backend liga-se a ele. O Frontend liga-se ao novo Backend.
  2. Execução de bateria End-to-End (E2E) simulando a subida de extratos de bancários e testando o fluxo do Classifier para identificar regressões nas categorias criadas ou nas transações do livro-razão.
* **Critério de Conclusão:** O painel reflete o espelho idêntico da versão V1 em produção, momento em que o PR final é liberado.


---

# REBUILD PIPELINE - FASE 10.2

Cronograma e esteira de entregas (Pipeline) projetado para a reengenharia do Fin Analytics V2, pautado em camadas de infraestrutura.

---

## FASE 1: Architecture Review
* **Foco:** Validação de todos os artefatos de auditoria congelados na Fase 10.
* **Ações:** 
  1. Revisão do `SYSTEM_REBUILD_PACKAGE.md` pelo comitê técnico.
  2. Setup inicial do ambiente docker/local.
  3. Confirmação do `API_CONTRACT_FREEZE.md` como imutável (Design-First).

## FASE 2: Database V2
* **Foco:** Persistência pura.
* **Ações:** 
  1. Reescrita das tabelas SQL, chaves primárias e views na branch `database-v2`.
  2. Implementação das travas de cascata rígidas documentadas (Governança e Deleção Segura).
  3. Descarte de tabelas legadas provadas mortas.

## FASE 3: Backend V2
* **Foco:** O coração matemático e lógico (FastAPI/Services).
* **Ações:** 
  1. Construção das rotas Dummy que respeitem os contratos JSON.
  2. Acoplamento de ORM ou Query Raw do DB ao serviço.
  3. Reconstrução do Motor de ETL, Categorizador de IA e Regex de Parcelamentos (conforme documentado no `BUSINESS_RULES.md`).

## FASE 4: Frontend V2
* **Foco:** Restauração Visual e Fluxos.
* **Ações:** 
  1. Refatoração UI (Next.js / App Router).
  2. Limpeza de pacotes obsoletos.
  3. Acoplamento transparente dos Hooks React às novas rotas (sem quebras, graças ao congelamento dos JSONs originais).

## FASE 5: Develop V2 Integration
* **Foco:** Colisão e Teste Cruzado.
* **Ações:** 
  1. Mescla de todas as branches na branch de choque (`develop-v2`).
  2. O Front invoca a API rodando conectada ao novo Banco V2. Testes manuais do fluxo E2E, importação de arquivo Nubank até o painel Dashboard.

## FASE 6: Certification
* **Foco:** Validação Estável Final (Release Candidate).
* **Ações:** 
  1. O comitê de Qualidade (QA) valida os deltas (Ritmo, YOC, Alocação). 
  2. Aprovando, inicia-se o Pull Request de `develop-v2` contra a sagrada `main`. A nova Era V2 inicia.


---

# MERGE POLICY - FASE 10.2

Regras absolutas de contribuição de código (Pull Requests) para garantir proteção inquebrável ao histórico original durante o processo de reconstrução do Fin Analytics.

---

## 1. REGRAS GERAIS DE BRANCHING
* O desenvolvimento direto de *features* é estritamente proibido nas branches `main` e `develop-v2`.
* As squads devem trabalhar ramificadas a partir da sua respectiva branch macro (`database-v2`, `backend-v2`, `frontend-v2`). Exemplo: `feat/backend-v2-auth`.

## 2. POLÍTICA DE DESTINO E INTEGRAÇÃO (O FUNIL)

A mescla do trabalho obedece ao seguinte funil unidirecional:

### Nível 1: As Especializadas
As branches arquiteturais atuam de forma isolada, agrupando todo o escopo antes da montagem.
* Todo o schema e governança de dados deve transitar apenas de e para **`database-v2`**.
* Toda a API FastAPI, IA e Services trafegam para **`backend-v2`**.
* Toda a reestruturação Next.js (UI/Hooks) transita para **`frontend-v2`**.

### Nível 2: O Choque (`develop-v2`)
* A branch `develop-v2` é o ponto focal e arena de teste.
* Os fluxos de mescla autorizados (Pull Requests Integrados) em ordem de cronograma são:
  * `database-v2`  ↓  `develop-v2`
  * `backend-v2`  ↓  `develop-v2`
  * `frontend-v2`  ↓  `develop-v2`

### Nível 3: Produção Congelada (`main`)
* NENHUMA branch de desenvolvimento tem permissão para fazer merge direto com a `main`. Nem mesmo a de backend ou front-end.
* O ÚNICO merge autorizado a tocar a raiz imutável do sistema é:
  * `develop-v2` ↓ `main` *(Apenas mediante aprovação total na Fase 6 de Certificação do Pipeline)*.

## 3. O ARQUIVO INTOCÁVEL
* A branch **`legacy-v1`** está em Lockdown absoluto (Read-Only). 
* Nenhum PR poderá ter esta branch como "Target" de Merge. Ela serve apenas como cápsula do tempo arqueológica para o MVP original, sendo autorizada a realizar "Checkout" para estudos de código velho.


---

# REBUILD RISKS ANALYSIS - FASE 10.2

Documento de rastreabilidade de passivos estruturais e riscos altos levantados no planejamento da reconstrução do Fin Analytics V2.

---

## 1. RISCOS DA RECONSTRUÇÃO
* **Perda da "Fotografia do Passado":** Ao recriar a arquitetura, pode haver corrupção do formato consolidado de histórico. O risco engloba a quebra de tipagem (`camelCase` vs `snake_case`) destruindo todos os Gráficos de Evolução Patrimonial (Recharts) que dependem visceralmente do DTO espelhado no Frontend.
* **Corrupção por Cascata Incompleta:** O sistema de governança é pautado no Lote de Importação (`import_runs`). Se o time subestimar a importância da Foreign Key com `ON DELETE CASCADE`, qualquer rejeição de importação futura vazará na tela como "Gasto Morto".

## 2. DEPENDÊNCIAS CRÍTICAS
* **ETL Pipeline & Governança:** Este é o coração do sistema. O banco de dados NÃO pode assumir dados injetados de fora do processo da Staging (Auditoria). Toda via deve passar por `Importação (Parser)` -> `Raw (Deduplicação Hash)` -> `Staging (Buffer)` -> `Aprovação Humana` -> `Ledger (Core)`.
* **API_CONTRACT_FREEZE.md:** O arquivo absoluto de limites (Boundary Contract). A branch de Frontend V2 depende 100% que as rotas mapeadas lá sejam mantidas sob as mesmas URIs sem modificação no comportamento.

## 3. COMPONENTES DE ALTO ACOPLAMENTO (Forte Fragilidade)
* **`WealthAnalyticsService` (Backend) & Banco de Dados Core:** Este serviço realiza cruzamentos orgânicos densos. Ele junta simultaneamente a tabela `positions`, o histórico `portfolio_evolution` e puxa lógicas de YOC sob a `dividends`. Refatorar as queries brutas deste serviço exige cautela máxima.
* **`EventReconciler` e `EventClassifier` (ETL IA):** Ambos agem entrelaçados. O Classifier acata a ordem imperativa de *Negative Match* e *Fuzzy Links* gerados no Reconciler. Alterar a matemática de qualquer um dos módulos destrói a Categorização visual de gastos, empurrando lançamentos bancários valiosos para o limbo do "Indefinido".

## 4. MÓDULOS QUE EXIGEM VALIDAÇÃO MATEMÁTICA ESTRITA
Qualquer squad assumindo a reengenharia deve cravar 100% de cobertura nos seguintes testes de função:
1. **Delta de Alpha:** Validar se a subtração aritmética do rendimento diário contra o IBOV/CDI permanece estática, conforme regras extraídas.
2. **Pacing de Gastos Mensais (`% Delta`):** A matemática de "Trending Up/Down" exige testes focados para cenários onde a despesa do Mês Anterior foi `0` (ZeroDivisionError protection).
3. **Bucket de Parcelamentos:** O agrupamento iterativo das parcelas usando a tolerância dividida (`round(amount/10)`) é vital para que compras do mesmo nome com variação de centavos no banco não explodam como "Novas Compras".
4. **Data de Contexto Estático:** Nenhum destes módulos pode avaliar `is_active` invocando relógio do servidor, mas sim atrelando-se eternamente a `max(data) importada` pela Governança.


---

# V2 BOOTSTRAP REPORT - FASE 10.4

Relatório oficial de bootstrap do ambiente Git para início do ciclo de desenvolvimento V2.

---

## 1. ÁRVORE DE BRANCHES CONFIRMADA
O repositório realizou um split exato a partir da `main` congelada.
* `main` (Origem/Espelho Congelado)
  * `develop-v2` (Branch de Colisão e Release Candidate)
    * `database-v2` (Persistência)
    * `backend-v2` (Lógica e API)
    * `frontend-v2` (UI e Hooks)

## 2. FLUXO DE MERGE
Conforme a `MERGE_POLICY.md`, a estratégia de *Pull Requests* será bottom-up:
* Nenhuma ramificação `v2` faz push ou merge para a `main`.
* `database-v2`, `backend-v2`, e `frontend-v2` fecham seus ciclos de entrega abrindo PR exclusivamente contra `develop-v2`.
* `develop-v2` apenas tocará a `main` ao fim de todo o ecossistema estar testado.

## 3. ORDEM DE EXECUÇÃO
O gargalo estrutural exige a seguinte ordem estrita (Pipeline):
1. **Primeiro a mover:** `database-v2` (Criação de models, views e Foreign Keys).
2. **Dependente Primário:** `backend-v2` (Precisa do banco V2 pronto para amarrar Repositories, ou deve começar criando endpoints "Mocks" isolados).
3. **Consumidor Final:** `frontend-v2` (Requer os endpoints Mocks do Backend para plugar as views sem quebrar).

## 4. RISCOS INICIAIS E DEPENDÊNCIAS ENTRE SQUADS
* **Risco de Contrato:** Se o Backend V2 não emular o Mock idêntico ao `API_CONTRACT_FREEZE.md` já no primeiro dia, o time de Frontend V2 ficará completamente paralisado e com erros de console (undefined property).
* **Dependência de Banco:** O time de Backend não poderá salvar o roteamento do Reconciler até que o time do Banco V2 libere a constraint vital `ON DELETE CASCADE` da `import_runs`.


---

# SPRINT V2.1 - DATABASE BACKLOG

**Responsável:** Squad Database-V2
**Objetivo da Sprint:** Construir a camada de persistência fundamental garantindo integridade referencial rígida a partir do `DATABASE_SPEC.md`.

---

## 1. EPIC: Infraestrutura de Persistência Core
* **TASK-01:** Inicializar configuração do motor de persistência (SQLAlchemy/Alembic ou Pure SQL SQLite).
* **TASK-02:** Mapear a tabela raiz de governança `import_runs` com ID em formato UUID ou Hash, com travas de estado (`status: PENDING, CONFIRMED, REJECTED`).
* **TASK-03:** Criar as meta-tabelas de usuário e sessão para isolamento de tenants (se aplicável).

## 2. EPIC: Livro-Razão (Ledger) e Cascata
* **TASK-04:** Modelar a tabela `transactions`. 
  * *Critério de Aceite:* Deve obrigatoriamente possuir `import_run_id` apontando para `import_runs(id)` com a constraint `ON DELETE CASCADE`.
* **TASK-05:** Modelar tabelas de Wealth (`positions`, `dividends`, `portfolio_evolution`).
  * *Critério de Aceite:* Herdar constraint `ON DELETE CASCADE` da `import_runs`.

## 3. EPIC: Staging e ETL Buffer
* **TASK-06:** Modelar `raw_events`.
  * *Critério de Aceite:* Implementar `UNIQUE(semantic_id)` para impedir falhas de duplicidade no Parser.
* **TASK-07:** Modelar as áreas de quarentena (`staging_imports`, `staging_positions`, `staging_dividends`).
* **TASK-08:** Modelar tabela orgânica do Reconciler (`event_links`).

## 4. EPIC: Camada de IA e Aprendizado
* **TASK-09:** Modelar o repositório de regras (`rules`) via JSON field ou Regex patterns.
* **TASK-10:** Modelar auditoria inquebrável (`audit_log`) e tracking do provedor LLM (`ai_runs`, `prompt_versions`).

## 5. EPIC: Debt Cleanup (Expurgos Confirmados)
* **TASK-11:** Assegurar via Pull Request review que a tabela `etl_runs_legacy` (código morto) **não** foi escrita nos models V2.

**Fim da Sprint V2.1:** Um banco relacional em container/arquivo local capaz de rodar uma bateria de mock sem falhas de chaves estrangeiras.


---

