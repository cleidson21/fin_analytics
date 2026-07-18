# Matriz de Compatibilidade Front ↔ Back ↔ Banco (Governança)

Esta matriz analisa as divergências entre os contratos (DTOs) que o Frontend envia/recebe, os DTOs que o Backend processa/fornece e a modelagem do SQLite, exclusivamente para as rotas da Governança.

---

## 1. Dashboard (`/governance`)

**Endpoint**: `GET /api/v1/governance/dashboard`

| Camada | Contrato / Estrutura | Status |
|--------|----------------------|--------|
| **Frontend** | `DashboardMetrics`: `total_runs`, `confirmed_runs`, `pending_runs`, `lines_inserted`, `lines_updated`, `lines_failed`, `last_import` | ❌ Divergência (Parcial) |
| **Backend** | O backend não possui um endpoint `GET /dashboard` implementado. O frontend tenta acessar `/governance/dashboard`. No `router.py`, o `@router.get("/dashboard")` não existe na raiz de Governança ou foi removido/esquecido. | ❌ Inexistente |
| **SQLite** | As informações poderiam ser derivadas de `import_runs`, calculando os `status`. As linhas deveriam ser somas de `rows_inserted`, `rows_errored` (o front pede `lines_failed`). | ❌ Divergência de Nomenclatura |

**Ação Necessária**: O backend precisa expor um endpoint oficial `GET /governance/dashboard` que faça as agregações reais em `import_runs` e adeque os nomes das colunas (`lines_failed` vs `rows_errored`).

---

## 2. Últimas Importações (`/governance` - Tabela)

**Endpoint**: `GET /api/v1/governance/imports?limit=10`

| Camada | Contrato / Estrutura | Status |
|--------|----------------------|--------|
| **Frontend** | Espera `ImportRunListResponse` com array de `ImportRunItem` (id, source_type, file_name, started_at, status, rows_read, rows_inserted, rows_failed). | ✅ Compatível (Mapeamento Existente) |
| **Backend** | Existe o endpoint `@router.get("/imports")` e ele retorna a lista usando paginação, lendo de `import_runs`. | ✅ Implementado |
| **SQLite** | Tabela `import_runs` possui todas essas colunas. No entanto, `rows_failed` no Frontend mapeia para `rows_errored` no banco. | ⚠️ Atenção (Nomenclatura) |

**Ação Necessária**: Garantir que o DTO do Backend mapeie `rows_errored` do banco para `rows_failed` no JSON de resposta, ou mudar o Frontend para ler `rows_errored`.

---

## 3. Revisão da Importação (`/governance/review`)

**Endpoint**: `GET /api/v1/governance/imports/{run_id}` e `GET /api/v1/governance/imports/{run_id}/staging-items`

| Camada | Contrato / Estrutura | Status |
|--------|----------------------|--------|
| **Frontend** | `/imports/{id}`: `ImportRunDetail` (id, source, file_name, checksum, started, finished, status, rows_read, rows_inserted, rows_updated, rows_failed, created_by, error_log, preview_summary). | ❌ Divergência |
| **Backend** | O DTO da rota GET não preenche corretamente `checksum` (deveria ser `file_hash`), `rows_updated` (não existe), `created_by` (possui `user_id`). A tabela não tem `error_log` (possui `error_message`). O `preview_summary` não existe nativamente. | ❌ Divergência Estrutural |
| **SQLite** | `import_runs` possui `file_hash`, `error_message`, `user_id`. | ❌ Divergência de Nomes |

**Endpoint**: `POST /api/v1/governance/imports/{run_id}/confirm` e `POST .../rollback`

| Camada | Contrato / Estrutura | Status |
|--------|----------------------|--------|
| **Frontend** | Botões que fazem POST nos endpoints sem body. | ✅ Compatível |
| **Backend** | Confirm implementado (OK). O Rollback atualiza o status para `ROLLBACKED` no SQLite (via código stub). | ❌ Violação de Constraint (Banco) |
| **SQLite** | Status permitido (`CHECK`) em `import_runs` são: 'PENDING','PROCESSING','SUCCESS','PARTIAL','FAILED'. Não existe 'ROLLBACKED'. | ❌ Falha no Banco |

**Ação Necessária**:
1. Ajustar o DTO do `ImportRunDetail` no backend para mapear `file_hash` -> `checksum`, `error_message` -> `error_log`.
2. Adicionar status `ROLLBACKED` ou `CANCELLED` no CHECK constraint do SQLite, ou alterar o Backend para definir como `FAILED` com mensagem explícita.

---

## 4. Auditoria (`/governance/audit`)

**Endpoint**: `GET /api/v1/governance/audit` e `GET /api/v1/governance/audit/rollbacks`

| Camada | Contrato / Estrutura | Status |
|--------|----------------------|--------|
| **Frontend** | `AuditRun` e `AuditRollback`. | ❌ Mocado no Backend |
| **Backend** | `@router.get("/audit")` e `/audit/rollbacks` estão retornando listas vazias (`[]`). | ❌ Stubs |
| **SQLite** | A listagem de runs lê de `import_runs`. Não há campo explícito na tabela para armazenar o timestamp de rollback, user de rollback ou reason. | ❌ Faltam Dados |

**Ação Necessária**:
1. Implementar o endpoint `/audit` (leitura paginada/filtrada de `import_runs`).
2. Para `/audit/rollbacks`, criar a modelagem do lado do Backend lendo os eventos da tabela `audit_logs` ou estender a tabela `import_runs`.

---

## 5. Banco de Dados (`/governance/database`)

**Endpoints**: `/database/summary`, `/database/health`, `/database/tables`, `/database/integrity`

| Camada | Contrato / Estrutura | Status |
|--------|----------------------|--------|
| **Frontend** | Mostra KPIs e aciona mutações (`/vacuum`, `/recount`). | ❌ Mocado no Backend |
| **Backend** | Retorna dicionários fixos com dados hardcoded. As mutações (`/vacuum`, `/recount`) não estão no `router.py`. | ❌ Stubs / Faltando |
| **SQLite** | Possui suporte a PRAGMAs e `VACUUM` nativos que não estão sendo chamados. | ❌ Desconectado |

**Ação Necessária**:
1. Substituir funções stub por queries reais de metadados SQLite.
2. Adicionar as rotas de mutação `POST /database/vacuum` e `POST /database/recount`.

---

## 6. Dados (`/governance/data`)

**Endpoints**: `/governance/positions`, `/governance/categories`, `/governance/dividends`

| Camada | Contrato / Estrutura | Status |
|--------|----------------------|--------|
| **Frontend** | Espera listagens com paginação. | ❌ Stubs |
| **Backend** | Retornam `{"items": [], "total": 0}`. | ❌ Stubs |
| **SQLite** | As tabelas estão populadas. | ❌ Não Implementado |

**Ação Necessária**:
1. Implementar as queries usando os Repositories existentes para popular a administração.

---

## 7. Memória Financeira (`/governance/learning`)

**Endpoints**: `/learning/metrics`, `/learning/rules/top`, `/learning/rules/problematic`, `/learning/rules`

| Camada | Contrato / Estrutura | Status |
|--------|----------------------|--------|
| **Frontend** | Consome várias métricas de IA e listagem de regras. | ❌ Inexistente |
| **Backend** | As rotas `/learning/*` simplesmente não existem no `router.py` da governança. | ❌ Inexistente |
| **SQLite** | `classification_rules` e `learning_examples` estão prontas no schema. | ❌ Desconectado |

**Ação Necessária**:
Criar o sub-router de `/learning` para alimentar a Memória Financeira.
