# DATABASE V2 MIGRATION PLAN

**Fase:** DB-04 — MIGRATION PLAN

Plano tático de reconstrução do banco de dados relacional. Este plano garante integridade referencial máxima durante a subida do novo ambiente, guiando a criação de *migrations* seguras e determinísticas.

---

## 1. ORDEM DE CRIAÇÃO DO SCHEMA (DDL - Data Definition Language)
A criação das tabelas no V2 obedecerá um rigoroso *Dependency Graph* (Grafo de Dependências) de chaves estrangeiras. Nenhuma tabela filha poderá ser erguida antes de sua dependência pai.

### A. Nível 0 (Raízes Independentes)
* `users`
* `categories` (Novo)
* `benchmarks` (Novo)
* `import_runs` (A Chave Mestra)

### B. Nível 1 (Dependentes Diretos da Raiz)
* `import_artifacts` (FK `import_runs.id`)
* `prompt_versions`
* `rules`
* `audit_log`
* `subscriptions` (FK `categories.id`)
* `goals` (FK `categories.id`)

### C. Nível 2 (Buffer de Ingestão)
* `raw_events` (FK `import_runs.id`)
* `staging_imports`
* `staging_positions`
* `staging_dividends`
* `staging_portfolio_evolution`

### D. Nível 3 (Ledger e Core Finance/Wealth)
* `transactions` (FK `import_runs.id`, FK `categories.id`)
* `positions` (FK `import_runs.id`)
* `dividends` (FK `import_runs.id`)
* `portfolio_evolution` (FK `import_runs.id`)

### E. Nível 4 (Eventos e Máquina de Estado)
* `event_links` (FK de duplo vínculo com `raw_events.id`)
* `ai_runs` (FK `prompt_versions.id`, FK `import_runs.id`)

## 2. ORDEM DE MIGRAÇÃO DE DADOS (DML - Data Manipulation Language)
Caso decida-se migrar os dados do arquivo SQLite `v1` para o novo modelo relacional `v2`:

1. **Dump Isolado:** Exportação CSV do banco congelado (`main`).
2. **Hidratação Raiz:** Inserir dados primários (`users` e a nova carga manual de `categories`).
3. **Carga Massiva (Sem Triggers):** Desligar temporariamente integridade e subir tabela `import_runs`.
4. **Resolução de Chaves:** Inserir `transactions` fazendo JOIN on-the-fly para converter as velhas strings textuais (`macro_categoria`) nos novos UUIDs da tabela `categories`.
5. **Religação:** Reativar Foreign Keys e rodar constraint checks nativos.

## 3. ESTRATÉGIA DE ROLLBACK
* **Alembic/Migration Downgrade:** Todos os scripts criados conterão as diretivas de `upgrade()` e `downgrade()` absolutas.
* **Isolamento de Ambiente:** O Database V2 rodará em um arquivo físico separado (ex: `fin_analytics_v2.db`). A base antiga `v1` atuará como *Cold Backup* isolado na pasta raiz para leitura pontual via script caso a migração do DML corrompa a integridade financeira.

## 4. BATERIA DE VALIDAÇÕES ESTABELECIDAS
Após a subida do schema e das migrations, o banco deverá passar ileso pela prova de fogo:

1. **Validação de Cascata:** Inserir uma `import_runs` FAKE contendo 1.000 `transactions` filhas -> Deletar o registro pai `import_runs` -> Confirmar se o `COUNT(transactions)` caiu para zero instantaneamente.
2. **Validação de Unicidade:** Tentar inserir um evento de `raw_events` com `semantic_id` já existente. Deve explodir erro `ConstraintViolation`.
3. **Validação de Hierarquia de Categorias:** Garantir que inserir uma transação apontando para uma categoria fantasma estoure erro de integridade referencial.
