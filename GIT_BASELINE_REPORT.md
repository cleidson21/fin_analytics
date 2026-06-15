# GIT BASELINE REPORT - FASE 10.1

Relatório situacional do repositório antes do SYSTEM FREEZE e inicialização da reconstrução V2.

---

## ESTADO GERAL DO REPOSITÓRIO

* **Branch Atual:** `main`
* **Commit Pendente (HEAD Atual):** `907168d2194bf66abe4ea59cedcbe5f2d23ab74e` (Autor: cleidson21 - "feat: implement comprehensive ETL pipeline and full-stack frontend governance and wealth modules")
* **Status com o Remote:** A branch atual está atualizada com a `origin/main`.

### Branches Existentes (Locais e Remotas)
* `* main`
* `legacy/v1`
* `remotes/origin/main`
* `remotes/origin/legacy/v1`
* `remotes/origin/copilot/audit-fin-analytics-repository`

---

## INVENTÁRIO DO WORKING DIRECTORY

Abaixo segue o espelho do diretório com as modificações acumuladas das Sprints e Auditorias anteriores que ainda não haviam sido "congeladas" na ramificação principal.

### 1. Arquivos Modificados (Tracked mas não commitados)
* `ROADMAP.md`
* `app/api/deps.py`
* `app/api/main.py`
* `app/api/routes/accounts.py`
* `app/api/routes/audit.py`
* `app/api/routes/auth.py`
* `app/api/routes/catalog.py`
* `app/api/routes/dashboard.py`
* `app/api/routes/database_admin.py`
* `app/api/routes/governance.py`
* `app/api/routes/learning.py`
* `app/api/routes/prompts.py`
* `app/api/routes/transactions.py`
* `app/api/services/analytics.py`
* `app/api/services/market_data.py`
* `app/api/services/wealth.py`
* `app/scripts/seed_admin.py`
* `database/config.py`
* `database/schema.sql`
* `frontend/src/app/governance/database/page.tsx`
* `frontend/src/app/governance/learning/page.tsx`
* `frontend/src/app/layout.tsx`
* `frontend/src/components/layout/AppShell.tsx`
* `frontend/src/lib/api.ts`

### 2. Arquivos Deletados (Tracked)
* `database/queries.py`
* `database/repository.py`
* `frontend/src/app/imports/page.tsx`
* `requirements.txt`

### 3. Arquivos Não Rastreados (Untracked)
Esses arquivos foram produzidos durante testes pontuais, correções e durante a nossa Engenharia Reversa (Auditoria Fase 10).
* `SYSTEM_REBUILD_PACKAGE.md` (Nosso pacote de auditoria mestre)
* `app/api/routes/internal.py`
* `app/api/services/auth_service.py`
* `app/api/services/financial_service.py`
* `app/api/services/governance_service.py`
* `app/api/services/import_service.py`
* `app/core/observability.py`
* `database/baseline.txt`
* `database/bootstrap_governance.py`
* `database/financial_repository.py`
* `database/governance_repository.py`
* `database/governance_schema.sql`
* `database/migrations/002_fix_orphans_and_fks.py`
* `database/migrations/fix_staging_orphans.py`
* Diretórios transitórios: `docs/`, `exports/`, `tests/`
* Outros: `frontend/src/all_files.txt`, `trans.json`

---

**NOTA DE RISCO:** O working tree apresenta grande quantidade de lixo em código e artefatos em staging pendente. O "Congelamento" (System Freeze) englobará obrigatoriamente estes arquivos para blindar todo o histórico, isolando-o de desenvolvimentos subsequentes.
