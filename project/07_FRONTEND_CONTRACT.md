# FINANALYTICS V3 — FRONTEND CONTRACT
> Documento crítico. Define a interface exata que o Backend V3 deve respeitar.
> **O Frontend é intocável.** A API deve se adaptar a este contrato, não o contrário.

---

## 1. DTOs e Tipos (Baseado em `types/entities.ts` e `types/dto.ts`)

### `Transaction`
```typescript
{
  id: string;
  descricao?: string;
  categoria?: string;
  macro_categoria: string;
  parcelamento: string;
  observacao?: string;
  data_transacao?: string;
  valor?: number;
  valor_cents?: number;
}
```

### `Position`
```typescript
{
  ticker: string;
  classe_ativo?: string;
  observacao?: string;
  data_snapshot?: string;
  quantidade: number;
  valor_investido: number;
  valor_atual: number;
  ganho: number;
  peso: number;
}
```

### `Dividend`
```typescript
{
  id_economico: string;
  ticker: string;
  tipo_evento?: string;
  observacao?: string;
  valor?: number;
  data_pagamento?: string;
}
```

### `PortfolioEvolutionPoint`
```typescript
{
  month: string;
  patrimonio_value: number;
  compras_value: number;
  proventos_value: number;
  rentabilidade_mensal_pct: number;
}
```

---

## 2. Endpoints Esperados e Hooks Correspondentes

### Auth
| Endpoint | Hook/Local | Payload (Request) | Payload (Response) |
|---|---|---|---|
| `POST /auth/token` (ou `/auth/login`) | `LoginPage` | N/A | `{ token: string, user: User }` |
| `GET /auth/me` | `AuthContext` | N/A | `User` |

*(O `User` do frontend espera `username` e `role`. O Backend mapeará `username = email` para manter compatibilidade)*

### Dashboard & Banking
| Endpoint | Hook/Local | Query Params | Retorno Esperado |
|---|---|---|---|
| `GET /dashboard/summary-v2` | `DashboardPage` | `?month=` | `{ income, expenses, investments, net, savings_rate }` |
| `GET /dashboard/pacing-v2` | `DashboardPage` | `?month=` | `{ budget, spent, projected, days_elapsed, days_total }` |
| `GET /dashboard/heatmap` | `DashboardPage` | `?month=` | `Array<{ date, total, count }>` |
| `GET /dashboard/categories` | `DashboardPage` | `?month=` | `Array<{ category, total }>` |
| `GET /transactions` | `useTransactions` | `limit, offset, search, startDate, endDate, category, sortBy, sortOrder` | `PaginatedResponse<Transaction>` |
| `GET /catalog` | `TransactionsPage` | N/A | Lista de categorias, merchants e contas |

### Credit
| Endpoint | Hook/Local | Query Params | Retorno Esperado |
|---|---|---|---|
| `GET /dashboard/installments` | `InstallmentsPage` | N/A | `{ month, active_installments, finished_installments, global_estimated, items: InstallmentItem[] }` |
| `GET /dashboard/subscriptions` | `SubscriptionsPage`| `?month=` | `{ month, active_count, monthly_total, annual_projection, items: SubscriptionItem[] }` |

### Investments & Wealth
| Endpoint | Hook/Local | Query Params | Retorno Esperado |
|---|---|---|---|
| `GET /investments/allocation` | `useAllocationData`| N/A | `Array<{ asset_class, current_total, current_total_value }>` |
| `GET /investments/positions` | `useAllocationData`| N/A | `Array<PositionDetail>` |
| `GET /investments/evolution/summary` | `useGrowthData` | N/A | `PortfolioEvolutionSummary` |
| `GET /investments/evolution/history` | `useGrowthData` | N/A | `Array<PortfolioEvolutionPoint>` |
| `GET /investments/dividends/history` | `useDividendsData` | N/A | `Array<DividendHistory>` |
| `GET /investments/dividends/breakdown` | `useDividendsData` | N/A | `Array<DividendBreakdown>` |
| `GET /investments/asset/{ticker}` | `AssetDetailPage` | N/A | `{ position, market_data, indicators, dividends, timeline }` |

### Governança & Importadores
| Endpoint | Hook/Local | HTTP Method | Payload/Retorno |
|---|---|---|---|
| `/governance/dashboard` | `GovernanceDashboardPage`| `GET` | `DashboardMetrics` |
| `/governance/imports` | `GovernanceDashboardPage`| `GET` | Lista de `ImportRun` |
| `/governance/import-pierre`| `GovernanceUploadPage` | `POST` | Body: `{ raw_text }` |
| `/governance/import-myprofit`| `GovernanceUploadPage` | `POST` | Body: `{ raw_text, file_name }` |
| `/governance/imports/{id}` | `ReviewContent` | `GET` | Detalhes do `ImportRun` |
| `/governance/imports/{id}/staging-items` | `ReviewContent` | `GET` | Items no staging com `validation_status` |
| `/governance/imports/{id}/confirm` | `ReviewContent` | `POST` | Confirma o `ImportRun` |
| `/governance/imports/{id}/rollback` | `ReviewContent` | `POST` | Reverte o `ImportRun` |
| `/governance/audit` | `useAuditRuns` | `GET` | Lista de auditoria |
| `/governance/database/summary` | `useDatabaseAdmin` | `GET` | Métricas do BD |
| `/governance/database/integrity` | `useDatabaseAdmin` | `GET` | Resultado de checagem de FK e integridade |

### Governança de Dados (Admin CRUD)
| Endpoint | Hook/Local | HTTP Method | Payload/Retorno |
|---|---|---|---|
| `/governance/transactions/{id}` | `TransactionEditDialog` | `PUT` | Atualiza categoria, observação, parcelamento |
| `/governance/positions/{ticker}/{date}` | `PositionEditDialog` | `PUT` | Atualiza classe, observação |
| `/governance/dividends/{id}` | `DividendEditDialog` | `PUT` | Atualiza tipo_evento, observacao |
| `/governance/categories/merge` | `CategoryMergeDialog` | `POST` | Junta 2 categorias |

### Reconciliação
| Endpoint | Hook/Local | HTTP Method | Payload/Retorno |
|---|---|---|---|
| `/governance/reconciliations` | `ReconciliationPage` | `GET` | `{ suggestions: [...], orphans: [...] }` |
| `/governance/links/{id}/confirm` | `ReconciliationPage` | `POST` | N/A |
| `/governance/links/{id}/reject` | `ReconciliationPage` | `POST` | N/A |

### AI & Learning
| Endpoint | Hook/Local | HTTP Method | Payload/Retorno |
|---|---|---|---|
| `/governance/learning/metrics` | `LearningDashboard` | `GET` | `{ total_rules, active_rules, observing_rules, quarantined_rules, memory_health_score }` |
| `/governance/learning/rules` | `LearningDashboard` | `GET` | Lista de `ClassificationRule` |
| `/governance/learning/rules/top` | `LearningDashboard` | `GET` | Top rules |
| `/governance/learning/rules/problematic` | `LearningDashboard`| `GET` | Rules com `miss_count` alto |

---

## 3. Páginas (Rotas Frontend) Protegidas

O Backend não pode exigir nenhuma mudança nos caminhos (`routes`) ou estrutura das páginas seguintes:

### Main
- `/` (Dashboard)
- `/login`

### Banking
- `/transactions`
- `/installments`
- `/subscriptions`
- `/categories`
- `/goals`

### Wealth
- `/wealth/patrimonio`
- `/wealth/evolution`
- `/wealth/dividends`
- `/wealth/allocation`
- `/wealth/asset/[ticker]`

### Governança
- `/governance`
- `/governance/imports`
- `/governance/review`
- `/governance/audit`
- `/governance/learning`
- `/governance/database`
- `/governance/data`
- `/governance/reconciliation`

---

## 4. Regras de Interface

1. **Campos Adicionais:** O Backend PODE retornar campos a mais nos JSONs (ex: `valor_cents`), desde que mantenha os campos que o Frontend já espera.
2. **Nomenclatura Legada:** Se o Frontend espera `valor`, o Backend deve mapear seu campo interno (ex: `amount`) para `valor` no JSON de resposta (DTO).
3. **Erros:** Todos os endpoints protegidos devem retornar `401` se o token for inválido, para que o `AuthContext` deslogue o usuário automaticamente.
