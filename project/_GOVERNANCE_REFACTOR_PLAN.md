# Plano de Refatoração da Governança (Fila de Implementação)

Com base na matriz de compatibilidade e na auditoria visualizada, foi estabelecida a seguinte fila de tarefas (Sprint Backlog) para a correção sistemática e progressiva do módulo de Governança.

O princípio é avançar um endpoint/tela por vez, integrando o fluxo real do banco de dados (SQLite) para substituir os *stubs* hardcoded no backend, sem modificar o contrato ou interface do Frontend (apenas reparos de mapeamento, quando estritamente necessário).

---

## 📋 TSK-GOV-01: Integração Real — Dashboard e Importações Básicas
**Status Inicial**: 40% (Rotas existem mas contêm divergências ou não estão plugadas nas tabelas)
- **Problemas Encontrados**: 
  - `GET /governance/dashboard` não existe mapeado na rota. O frontend chama um endpoint inexistente.
  - O DTO do `ImportRunListResponse` e `ImportRunDetail` sofre de desalinhamento em colunas: O front pede `lines_failed`, `checksum`, `error_log`, mas o banco usa `rows_errored`, `file_hash`, `error_message`. O Frontend também espera `rows_updated`, `preview_summary` (que o banco não armazena nativamente).
- **Correção Estimada**:
  - Criar o endpoint `GET /dashboard` e mapear cálculos (sum) de métricas oficiais sobre `import_runs`.
  - Refatorar DTOs para mapeamento JSON entre snake_case do SQLite e os campos que o Front espera.

## 📋 TSK-GOV-02: Integração Real — Revisão e Staging
**Status Inicial**: 50% (Endpoint Confirmar OK, Rollback quebrado, Itens Desalinhados)
- **Problemas Encontrados**:
  - O endpoint `/staging-items` precisa extrair dados de `import_artifacts` usando os novos artefatos brutos JSON. 
  - Status divergentes: Frontend exibe validações (`VALID`, `WARNING`, `ERROR`, `CONFLICT`) mas o schema usa `PENDING`, `INSERTED`, `SKIPPED`, `ERROR`.
  - Endpoint de Rollback aciona um `UPDATE import_runs SET status = 'ROLLBACKED'`, mas o `CHECK` constraint do SQLite só aceita `PENDING, PROCESSING, SUCCESS, PARTIAL, FAILED`.
- **Correção Estimada**:
  - Criar mapeador para a lista de itens `/staging-items`.
  - Modificar constraint ou definir status como `FAILED` com justificativa no campo de erro para evitar quebra no SQLite.

## 📋 TSK-GOV-03: Integração Real — Auditoria (Histórico e Rollbacks)
**Status Inicial**: 0% (Totalmente Mocado)
- **Problemas Encontrados**:
  - Endpoints `/audit` e `/audit/rollbacks` retornam array vazio `[]` fixo.
  - A tabela `audit_logs` suporta entidades e import_runs, mas faltam consultas SQLAlchemy reais.
- **Correção Estimada**:
  - Implementar queries que listem `import_runs` ordenadas decrescentemente e, para rollbacks, procurar logs com a tag `ROLLBACK` (ou a métrica correspondente adotada) nas auditorias do banco.

## 📋 TSK-GOV-04: Integração Real — Admin do Banco de Dados
**Status Inicial**: 0% (Stubs puros)
- **Problemas Encontrados**:
  - A aba Banco de Dados consome APIs vazias (`/database/summary`, `health`, `tables`, `integrity`).
  - Mutações operacionais (`vacuum`, `vacuum/estimate`, `recount`) inexistentes no `router.py`.
- **Correção Estimada**:
  - Usar SQLAlchemy e driver SQlite raw para inspecionar `sqlite_master` (count das tables, index info) e `PRAGMA integrity_check`.
  - Implementar suporte aos endpoints POST executando `VACUUM`.

## 📋 TSK-GOV-05: Integração Real — Tabelas de Dados
**Status Inicial**: 20% (Tabelas existem no DB, mas endpoints não integrados à Governança)
- **Problemas Encontrados**:
  - `/positions`, `/categories`, `/dividends` na governança retornam `{"items": [], "total": 0}`.
- **Correção Estimada**:
  - Ligar esses endpoints no `router.py` aos `Repositories` oficiais (ou serviços do domínio `investments` e `banking`) apenas limitando a busca, fornecendo paginação com paginação real do banco de dados (SQLite `LIMIT` / `OFFSET`).

## 📋 TSK-GOV-06: Integração Real — Memória Financeira (Learning)
**Status Inicial**: 0% (Telas Desconectadas)
- **Problemas Encontrados**:
  - Os hooks do frontend fazem polling em `/learning/metrics` e afins. O backend de Governança desconhece essas rotas.
  - A arquitetura prevê IA (`classification_rules`), mas não há roteador para gerir esses feedbacks via painel.
- **Correção Estimada**:
  - Criar `backend/domains/governance/learning_router.py` apontando para o DB real (tabelas `classification_rules` e `learning_examples`). Expor endpoints de sumarização, Top Regras, e degradadas, para popular a UI com vida.

---

*(Nenhuma correção de código deve ser feita antes da avaliação deste plano pelo usuário).*

---

## 🛠 UX WIZARD: Novo Assistente de Importação

Foi decidido na Sprint H1 alterar o modelo mental de upload para um assistente passo-a-passo guiado:

**Fluxo Unificado (Assistente):**
1. **Nova Importação**
2. **Escolha a origem** (Nubank Conta, Nubank Fatura, MyProfit, Pierre, B3)
3. **Como deseja importar?** (Arquivo ou Colar Texto)
4. **Upload** (Submissão do componente)
5. **Pré-processamento** (Execução de Reader e Parser)
6. **Validação** (Mensagens contextualizadas por origem)
7. **Preview** (Exibição dos dados cacheados na tabela de Staging)
8. **Confirmação** (Commit no banco de dados nas tabelas finais)
9. **Resultado** (Página de Sucesso / Histórico)

Isso permite que Pierre, B3 e MyProfit usem exatamente o mesmo fluxo com instruções e validações parametrizadas por origem, eliminando telas poluídas.
