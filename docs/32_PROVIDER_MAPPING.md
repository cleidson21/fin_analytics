> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

> [!CAUTION]
> **DOCUMENTO OBSOLETO — V3.1**
> O mapeamento de providers para um domínio canônico central foi eliminado na V3.1.
> Cada domínio agora é responsável pelo seu próprio mapeamento em `repository.py`.
> O mapeamento oficial Pierre → banco está em `16_PIERRE_REFERENCE.md`.
> Este arquivo é mantido apenas como referência histórica. Não implementar.

# Mapeamento de Providers — FIN Analytics (OBSOLETO)

**Regra Fundamental:** Nenhum campo do domínio canônico pode referenciar campos do Provider diretamente. O Connector converte. O Domínio recebe apenas o Canônico.

---

## Pierre Finance → Canônico

**Escopo confirmado pelo OpenAPI real (24 endpoints):** Banking — Contas, Cartões, Transações, Saldos, Parcelamentos.
**Escopo NÃO coberto pela Pierre:** Investimentos, Posições, Dividendos, Ativos (ver ADR-009).

### Account
| Pierre (`/tools/api/get-accounts`) | Canônico | Notas |
|---|---|---|
| `accountId` | `external_id` | |
| `providerCode` | `provider_code` | Ex: NUBANK |
| `accountName` | `name` | |
| `accountType` | `type` | Mapear: BANK→BANK, CREDIT→CREDIT_CARD, INVESTMENT→INVESTMENT |
| `accountSubtype` | `subtype` | |
| `accountBalance` | `balance` | |
| `accountCurrencyCode` | `currency_code` | |
| `accountMarketingName` | `provider_metadata.marketing_name` | |
| — | `id` | Gerado internamente (UUID) |
| — | `provider` | `PIERRE` (constante) |
| — | `institution_id` | Derivado de `providerCode` via Institution lookup |

### Transaction
| Pierre (`/tools/api/get-transactions`) | Canônico | Notas |
|---|---|---|
| `id` da transação | `external_id` | |
| `amount` | `amount` | Pierre retorna positivo — `direction` = DEBIT se saída |
| `description` | `description` | |
| `date` | `transaction_date` | |
| `category` | `category_id` | Lookup ou criação de categoria |
| `accountId` | `account_id` (via external_id lookup) | |
| `status` (se existir) | `status` | |
| — | `id` | UUID gerado |
| — | `provider` | `PIERRE` |
| — | `hash` | SHA256 calculado |
| — | `currency_code` | Herdado da Account |

### NÃO mapeável via Pierre
- `Asset` → [NÃO EXISTE]
- `Position` → [NÃO EXISTE]
- `Dividend` → [NÃO EXISTE]

---

## MyProfit → Canônico

**Escopo:** Investimentos B3 — Ações, FIIs, ETFs, Dividendos, Posições.
**Método de acesso:** Web scraping via sessão autenticada (CSV export ou DOM scraping).

### Asset
| MyProfit (CSV/Scraping) | Canônico | Notas |
|---|---|---|
| Ticker | `ticker` (Ticker VO) | Normalizar uppercase |
| Nome | `name` | |
| Tipo (Ação, FII, ETF) | `type` | Mapear strings para AssetType enum |
| — | `exchange` | `B3` (constante) |
| — | `currency_code` | `BRL` (constante para B3) |
| — | `id` | UUID gerado |

### Position
| MyProfit (CSV/Scraping) | Canônico | Notas |
|---|---|---|
| Ticker | `asset_id` (via Asset lookup) | |
| Quantidade | `quantity` | |
| Preço médio | `avg_cost` | |
| Valor atual | `current_value` | |
| Rentabilidade | `gain_loss_pct` | |
| — | `provider` | `MYPROFIT` |
| — | `snapshot_date` | Data da extração |

### Dividend
| MyProfit (CSV "Proventos") | Canônico | Notas |
|---|---|---|
| Ticker | `asset_id` | |
| Tipo (DIV, JCP) | `type` | |
| Valor/cota | `amount_per_unit` | |
| Qtd posição | `quantity` | |
| Total bruto | `gross_amount` | |
| Data-com | `ex_date` | |
| Data pagto | `payment_date` | |

---

## CSV → Canônico

| Padrão CSV | Canônico | Notas |
|---|---|---|
| Coluna "data" | `transaction_date` | Tentar múltiplos formatos de data |
| Coluna "valor" | `amount` + `direction` | Negativo = DEBIT, Positivo = CREDIT |
| Coluna "descrição" | `description` | |
| Coluna "categoria" | `category_id` | Criar categoria se não existir |
| — | `provider` | `CSV` |
| — | `hash` | SHA256 da linha inteira |

---

## YFinance → Canônico

| YFinance | Canônico | Notas |
|---|---|---|
| `symbol` | `ticker` | |
| `longName` | `name` | |
| `currency` | `currency_code` | |
| `exchange` | `exchange` | |
| `sector` | `sector` | |
| `currentPrice` | `current_price` (em Position) | Snapshot |

---

## Manual → Canônico

| Manual (formulário UI) | Canônico | Notas |
|---|---|---|
| Todos os campos digitados pelo usuário | Diretamente no canônico | Sem transformação |
| — | `provider` | `MANUAL` |

---

## Matriz de Cobertura

| Entidade | Pierre | MyProfit | CSV | YFinance | Manual |
|---|---|---|---|---|---|
| Transaction | ✅ Completo | ❌ | ✅ Parcial | ❌ | ✅ |
| Account | ✅ Completo | ❌ | ❌ | ❌ | ✅ |
| Asset | ❌ | ✅ Completo | ❌ | ✅ Cotações | ✅ |
| Position | ❌ | ✅ Completo | ❌ | ✅ Preços | ✅ |
| Dividend | ❌ | ✅ Completo | ✅ CSV | ❌ | ✅ |
| Institution | ✅ Parcial | ✅ Parcial | ❌ | ❌ | ✅ |
| Category | ✅ Auto | ❌ | ✅ Parcial | ❌ | ✅ |
| Portfolio | ❌ | ✅ | ❌ | ❌ | ✅ |
| User | ❌ | ❌ | ❌ | ❌ | Sistema |
| Currency | ❌ | ❌ | ❌ | ✅ | Sistema |
