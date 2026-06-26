# FINANALYTICS V3 — TEST PLAN
> Plano global de testes. Cada fase aponta para seus testes obrigatórios.
> Testes devem ser executados e evidenciados antes da aprovação de qualquer gate.

---

## Convenções

- **[MANUAL]** — executado manualmente via browser ou curl
- **[AUTO]** — executado via pytest (quando disponível)
- **[GATE]** — obrigatório para aprovação da fase

---

## FASE 1 — Fundação & Infraestrutura

| ID | Tipo | Teste | Evidência Exigida |
|---|---|---|---|
| T1.1 | [MANUAL][GATE] | `curl http://localhost:8000/api/v1/health` retorna HTTP 200 | JSON: `{"status": "ok", "db": "connected"}` |
| T1.2 | [MANUAL][GATE] | Servidor sobe sem erros no terminal | Log do uvicorn sem `OperationalError` ou `ImportError` |
| T1.3 | [MANUAL][GATE] | Pasta `app/` não existe mais no repositório | `ls app/` retorna "não encontrado" |
| T1.4 | [MANUAL] | `GET /api/v1/docs` carrega a documentação OpenAPI | Página Swagger abre no browser |

---

## FASE 2 — Identity & Autenticação

| ID | Tipo | Teste | Evidência Exigida |
|---|---|---|---|
| T2.1 | [MANUAL][GATE] | `POST /api/v1/auth/login` com credenciais corretas | Retorna `{"token": "...", "user": {"username": ..., "role": ..., "email": ...}}` |
| T2.2 | [MANUAL][GATE] | `GET /api/v1/auth/me` com token Bearer válido | Retorna dados do usuário |
| T2.3 | [MANUAL][GATE] | `GET /api/v1/auth/me` sem token | Retorna HTTP 401 |
| T2.4 | [MANUAL][GATE] | `POST /api/v1/auth/login` com credenciais inválidas | Retorna HTTP 401 |
| T2.5 | [MANUAL] | Frontend consegue logar e redirecionar para dashboard | Sem erro de console no browser |

---

## FASE 3 — Ledger Core

| ID | Tipo | Teste | Evidência Exigida |
|---|---|---|---|
| T3.1 | [MANUAL][GATE] | `GET /api/v1/transactions?limit=20` | JSON com `{items: [...], total: N}`. Campos: `id, descricao, categoria, data_transacao, valor, valor_cents` |
| T3.2 | [MANUAL][GATE] | `GET /api/v1/transactions?search=mercado` | Filtra por `original_description` ou `normalized_desc` |
| T3.3 | [MANUAL][GATE] | `GET /api/v1/dashboard/summary-v2?month=YYYY-MM` | JSON com `{income, expenses, investments, net, savings_rate}` |
| T3.4 | [MANUAL][GATE] | `GET /api/v1/dashboard/pacing-v2?month=YYYY-MM` | JSON com `{budget, spent, projected, days_elapsed, days_total}` |
| T3.5 | [MANUAL][GATE] | `GET /api/v1/dashboard/heatmap?month=YYYY-MM` | Array de `{date, total, count}` |
| T3.6 | [MANUAL][GATE] | `GET /api/v1/dashboard/categories?month=YYYY-MM` | Array de `{category, total}` |
| T3.7 | [MANUAL][GATE] | `GET /api/v1/catalog` | JSON com `{categories: [...], merchants: [...], accounts: [...]}` |
| T3.8 | [MANUAL] | Tela `/transactions` exibe lista sem erro de console | Screenshot ou confirmação visual |

---

## FASE 4 — Credit & Installments

| ID | Tipo | Teste | Evidência Exigida |
|---|---|---|---|
| T4.1 | [MANUAL][GATE] | `GET /api/v1/dashboard/installments` | JSON com `{month, active_installments, finished_installments, global_estimated, items: [...]}` |
| T4.2 | [MANUAL][GATE] | `GET /api/v1/dashboard/subscriptions?month=YYYY-MM` | JSON com `{month, active_count, monthly_total, annual_projection, items: [...]}` |
| T4.3 | [MANUAL] | Tela `/installments` exibe planos com progresso correto | Confirmação visual |

---

## FASE 5 — Importadores & Governança

| ID | Tipo | Teste | Evidência Exigida |
|---|---|---|---|
| T5.1 | [MANUAL][GATE] | Upload de CSV Pierre via `POST /governance/import-pierre` | `import_run` criado com status `AWAITING_CONFIRMATION` |
| T5.2 | [MANUAL][GATE] | `GET /governance/imports/{run_id}/staging-items` após upload | Lista de artifacts com `validation_status` correto |
| T5.3 | [MANUAL][GATE] | `POST /governance/imports/{run_id}/confirm` | Transações inseridas em `transactions` com `run_id` correto |
| T5.4 | [MANUAL][GATE] | `POST /governance/imports/{run_id}/rollback` | Transações do `run_id` deletadas; run marcado como `ROLLED_BACK` |
| T5.5 | [MANUAL][GATE] | Reimportar mesmo CSV após confirm | Todos artifacts com status `DUPLICATE` |
| T5.6 | [MANUAL][GATE] | `GET /governance/dashboard` | JSON com `{total_runs, confirmed_runs, pending_runs, lines_inserted, last_import}` |
| T5.7 | [MANUAL] | Tela `/governance/review` exibe staging e botões funcionam | Confirmação visual |

---

## FASE 6 — Investments & Market Data

| ID | Tipo | Teste | Evidência Exigida |
|---|---|---|---|
| T6.1 | [MANUAL][GATE] | `GET /api/v1/investments/positions` | Array de `{ticker, asset_class, quantidade, preco_medio, valor_investido, valor_atual, ganho, peso_percentual}` |
| T6.2 | [MANUAL][GATE] | `GET /api/v1/investments/allocation` | Array de `{asset_class, current_total, current_total_value}` |
| T6.3 | [MANUAL][GATE] | `GET /api/v1/investments/dividends/history` | Array com campos de mês e tipos de provento |
| T6.4 | [MANUAL][GATE] | `GET /api/v1/investments/dividends/breakdown` | Array de `{ticker, total_recebido, quantidade_eventos, ...}` |
| T6.5 | [MANUAL] | Tela `/wealth/patrimonio` exibe carteira sem erros | Confirmação visual |

---

## FASE 7 — Engines Analíticas

| ID | Tipo | Teste | Evidência Exigida |
|---|---|---|---|
| T7.1 | [AUTO][GATE] | PositionEngine WAC: 10 BUY @ 10 + 5 BUY @ 20 = PM 13.33 | Resultado calculado corretamente em pytest |
| T7.2 | [AUTO][GATE] | PositionEngine SELL: venda parcial não altera PM | Resultado correto em pytest |
| T7.3 | [AUTO][GATE] | PositionEngine SPLIT: qty × ratio, PM ÷ ratio | Resultado correto em pytest |
| T7.4 | [AUTO][GATE] | CashflowEngine: sum de CREDIT e DEBIT por mês | Resultado correto em pytest |
| T7.5 | [MANUAL][GATE] | `GET /api/v1/investments/evolution/summary` | JSON com `{patrimonio_atual_value, rentabilidade_acumulada, ibov_acumulado_pct, cdi_acumulado_pct, ...}` |
| T7.6 | [MANUAL][GATE] | `GET /api/v1/investments/evolution/history` | Array com `{month, patrimonio_value, ibov_mensal_pct, cdi_mensal_pct, ...}` |
| T7.7 | [MANUAL] | Tela `/wealth/evolution` exibe gráficos sem erros | Confirmação visual |

---

## FASE 8 — AI & Learning

| ID | Tipo | Teste | Evidência Exigida |
|---|---|---|---|
| T8.1 | [MANUAL][GATE] | `GET /api/v1/governance/learning/metrics` | JSON com `{total_rules, active_rules, observing_rules, quarantined_rules}` |
| T8.2 | [MANUAL][GATE] | `GET /api/v1/governance/learning/rules` | Array com `{id, pattern, rule_type, status, hit_count, miss_count, evidence_count, confidence_score}` |
| T8.3 | [MANUAL][GATE] | `GET /api/v1/governance/reconciliations` | JSON com `{suggestions: [...], orphans: [...]}` |
| T8.4 | [MANUAL] | Tela `/governance/learning` exibe métricas e regras | Confirmação visual |

---

## FASE 9 — Validação E2E & Hardening

| ID | Tipo | Teste | Evidência Exigida |
|---|---|---|---|
| T9.1 | [MANUAL][GATE] | Todas as 18 telas do frontend carregam sem Network Error | Zero erros no console DevTools |
| T9.2 | [MANUAL][GATE] | Fluxo completo: Login → Upload → Review → Confirm → Dashboard | Dados aparecem no dashboard após confirmar importação |
| T9.3 | [MANUAL][GATE] | `GET /api/v1/investments/asset/{ticker}` com ticker válido | JSON com `{position, market_data, indicators, dividends, timeline}` |
| T9.4 | [MANUAL] | CORS configurado: frontend em porta 3000 acessa backend porta 8000 | Sem erro de CORS no console |
