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
