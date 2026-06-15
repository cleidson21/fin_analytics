# API SURVIVAL REPORT

Este relatório é o levantamento detalhado das rotas existentes na versão anterior da aplicação (detectadas em `app/api/routes`), avaliando se as mesmas possuem aderência ao novo domínio, Repositórios e Serviços do Backend V3. 

A categorização segue os parâmetros: **MANTER**, **REFATORAR** (troca de injeção), **SUBSTITUIR** (nova URL ou conceito) ou **REMOVER** (conceito morto).

---

## 1. Módulo: Dashboard & Core Finance

| Rota Atual V1 | Classificação | Motivo / Próximo Passo na V3 |
| :--- | :--- | :--- |
| `GET /transactions` | **REFATORAR** | URL correta, mas deve abandonar SQLRaw/Model-return e devolver DTO paginado puxando do `TransactionRepository`. |
| `PATCH /transactions/{id}/reclassify` | **SUBSTITUIR** | A reclassificação não deve mutar a ledger direto, mas deve gerar trilha de auditoria via camada AI (`LearningService`). Rota deve ser `PUT` ou acionar `Governance`. |
| `GET /dashboard/pacing` | **SUBSTITUIR** | Temos no Backend V2 o `get_expense_pacing` e `get_pacing_v2`. Unificar em 1 rota final (ex: `GET /dashboard/pacing`). |
| `GET /dashboard/summary` | **REFATORAR** | Embutir a classe `CashflowService` (BE-02A) e integrar patrimônio via Wealth Domain. |

---

## 2. Módulo: Wealth (Investimentos)

| Rota Atual V1 | Classificação | Motivo / Próximo Passo na V3 |
| :--- | :--- | :--- |
| `GET /investments/dividends/history` | **CONSOLIDAR** | O V2 abstraiu via `DividendService`. Reduzir para `GET /wealth/dividends`. |
| `GET /investments/dividends/breakdown` | **REMOVER** | Função já envelopada pela lógica agnóstica de agregação no frontend ou via Query params da rota base. |
| `GET /investments/positions` | **REFATORAR** | Acoplar no novo `PositionService`. Mudar para `/wealth/positions`. |
| `GET /investments/evolution` | **REFATORAR** | Acoplar no `EvolutionService` (que calcula Alpha e Benchmark). Mudar para `/wealth/evolution`. |
| `GET /investments/allocation` | **REFATORAR** | Acoplar no `AllocationService`. Mudar para `/wealth/allocation`. |
| `GET /investments/asset/{ticker}` | **MANTER** | Rota útil de raio-x do ativo, apenas injetar `db: Session` com repositórios puros. |

---

## 3. Módulo: Governance (O Mais Caótico da V1)

A V1 continha 25+ rotas em `governance.py`. O `V2_GOVERNANCE_AND_BOOTSTRAP` purificou todo o ciclo de vida da aprovação em lote, invalidando dezenas de rotas isoladas.

| Rota Atual V1 | Classificação | Motivo / Próximo Passo na V3 |
| :--- | :--- | :--- |
| `POST /governance/import-pierre` | **REMOVER** | Substituído por `ImportService` Genérico do V2 que não atrela nome do broker/extrator na URL. |
| `POST /governance/import-myprofit` | **REMOVER** | Mesmo motivo. `POST /governance/imports` receberá parâmetro `source_type`. |
| `POST /governance/import-unified` | **MANTER** | Vira o Endpoint Padrão de Injeção: `POST /governance/imports`. |
| `GET /governance/imports/{run_id}` | **REFATORAR** | Apontar para `ImportRunRepository`. |
| `POST /governance/imports/{run_id}/confirm` | **REFATORAR** | Aciona internamente o `ApprovalService.approve_import(run_id)`. |
| `POST /governance/imports/{run_id}/rollback` | **REFATORAR** | A V2 usa Delete Cascade violento no DB. O endpoint apenas dispara `repo.delete(run_id)`. |
| `PUT /governance/transactions/{id}` | **REMOVER** | A ledger (transações) não é editada pela Governança, apenas a Staging. |
| `POST /governance/links/{link_id}/*` | **REMOVER** | Como visto no relatório de purificação do banco, o uso manual de `event_links` foi deprecado em prol do Fuzzy Matching em runtime via `ReconciliationService`. |

---

## 4. Módulo: AI Layer (Prompts e Learning)

| Rota Atual V1 | Classificação | Motivo / Próximo Passo na V3 |
| :--- | :--- | :--- |
| `POST /prompts/{id}/activate` | **REFATORAR** | Utilizar `PromptVersionService.activate_version()` que desliga concorrentes e respeita o singleton. |
| `GET /learning/rules` | **REFATORAR** | Injetar `RuleRepository`. |
| `GET /learning/metrics` | **SUBSTITUIR** | Fundir com `AIRunService.get_aggregated_report()` para extrair custo em dólares e tokenização. |

---

## Conclusão de Rotas
A nova API (V3) deve ser extremamente enxuta. A responsabilidade pesada migrou inteiramente para os Services e para as cascatas do Banco. 
Aproximadamente **40% das rotas HTTP antigas não farão mais sentido** e não devem ser reimplementadas.
