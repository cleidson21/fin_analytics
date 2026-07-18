# Auditoria Geral de Governança - Inventário e UX

Este documento sumariza as Fases 1, 2, 3 e 5 da auditoria do módulo de Governança, identificando os contratos (DTOs) envolvidos no Frontend, Backend e SQLite, além das recomendações de UX.

---

## 1. Inventário do Frontend

### Rotas e Componentes
- `/governance`: Dashboard Principal (`DashboardMetrics`, `ImportRunItem`). Exibe cards de resumo e listagem das últimas execuções.
- `/governance/imports`: Nova Importação. Permite *Upload* via MyProfit ou inserção via texto para o Pierre.
- `/governance/review?run=ID`: Revisão da Importação. Lista staging items e exibe logs para aprovação final.
- `/governance/audit` e `/governance/audit/[id]`: Histórico de execuções (`AuditRun`) e rollbacks (`AuditRollback`).
- `/governance/database`: Controle do banco, exibe métricas (`DatabaseSummary`, `DatabaseHealth`) e permite comandos `VACUUM` e `ANALYZE`.
- `/governance/data`: Tabelas de apoio com paginação (`Position`, `Category`, `Dividend`).
- `/governance/learning`: Memória Financeira. Exibe IA, regras (`Rule`) e score de degradação.

### Comportamento Observado (UX/State)
- A tela exibe states de `loading` (ex: "Carregando detalhes...") com spinners.
- Empty states estão implementados ("Nenhum registro para exibir").
- As tabelas usam os Hooks customizados (`useTransactions`, `useDividendsAdmin`, `usePositionsAdmin`, `useCategoriesAdmin`, `useDatabaseAdmin`, `useAuditRuns`).
- Utiliza `fetchFromAPI` e lida com auth via `AuthRequiredCard`.

---

## 2. Inventário do Backend

### Rotas e Stubs no `router.py`
A maioria das rotas do domínio `/governance` se encontra no arquivo `router.py`. Constatou-se a seguinte situação:
- **Funcional**: `/imports` (TSK-02) e `/imports/{run_id}/confirm` (TSK-03).
- **Mocado (Stubs)**:
  - `GET /database/summary` -> Retorna JSON estático com `size_mb: 15.4`
  - `GET /database/health` -> Retorna "OK" para tudo.
  - `GET /database/tables` -> Retorna array fixo.
  - `GET /database/integrity` -> Retorna dict fixo.
  - `GET /audit` -> Retorna `[]`.
  - `GET /audit/rollbacks` -> Retorna `[]`.
  - `GET /positions` -> `{"items": [], "total": 0}`.
  - `GET /categories` -> `{"items": [], "total": 0}`.
  - `GET /dividends` -> `{"items": [], "total": 0}`.
- **Inexistente**: 
  - `GET /dashboard` (não existe mapeado, o frontend chama, e se falhar no gateway, não aparece).
  - Rotas de `VACUUM` e `ANALYZE` (`/database/vacuum`, `/database/recount`).
  - Todas as rotas de `learning` (`/learning/metrics`, `/learning/rules/top`, etc.).

---

## 3. Inventário do SQLite

### Tabelas Mapeadas para Governança
- `import_runs`: Registra o ID, arquivo e métricas. Faltam metadados específicos requeridos pela auditoria (ex: campos para identificar quem/quando fez rollback, pois no esquema de restrições de SQLite `status` = `ROLLBACKED` causará falha).
- `import_artifacts`: Mantém dados brutos do staging. A rota `/imports/{run_id}/staging-items` precisa ler daqui e formatar os campos de status de forma unificada para o frontend (pois os status antigos do Frontend eram `VALID`, `WARNING`, `CONFLICT` mas no banco são `PENDING`, `INSERTED`, `SKIPPED`, `ERROR`).
- `audit_logs`: Deveria ser a fonte para as views de auditoria do frontend.
- `classification_rules` e `learning_examples`: Fonte para a aba Memória Financeira. O banco suporta, mas as rotas não.

---

## 5. Análise de UX (Propostas)

### Nova Importação (`/governance/imports`)
**UX Atual**: A tela tem abas (Tabs) para "MYPROFIT" e "PIERRE".
**Sugerido**: Eliminar as abas isoladas. Criar um fluxo contínuo (Wizard-like) similar ao proposto:
1. **Nova Importação** -> Selecionar Origem em Cards (MyProfit, Pierre, Nubank Conta, Nubank Fatura, B3).
2. O formulário se adequa (Upload Arquivo vs Colar Texto) dependendo da origem escolhida.
3. Isso unifica a API para consumir um DTO genérico independentemente do parser, em vez de endpoints isolados (`/import-pierre`, `/import-myprofit`).

### Memória Financeira (`/governance/learning`)
A interface está bonita, com bons dashboards e indicadores de saúde. A divergência reside 100% em falta de contrato no backend. Recomendamos manter a UI.

### Banco de Dados (`/governance/database`)
O UX está excelente para Administração, porém o botão de "Estimar VACUUM" requer 2 POSTs (`/estimate` e depois executar). O Backend pode simplificar para um POST único que faz o vacuum e retorna os metadados poupando estado complexo na UI, ou manter a abordagem de 2 passos para prevenir que o backend trave muito tempo sem a intenção explícita do Admin.
