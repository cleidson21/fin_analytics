> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Regras de Domínio (FIN Analytics)

---

## Identidade das Entidades

| Entidade | Chave Primária | Chave Externa | Regra de Deduplicação |
|---|---|---|---|
| Transaction | UUID interno | `external_id + provider` | Hash SHA256 de `external_id + provider + date + amount` |
| Account | UUID interno | `external_id + provider` | `external_id + provider` único |
| Asset | UUID interno | `ticker + exchange` | `ticker + exchange` único |
| Position | UUID interno | `asset_id + portfolio_id + snapshot_date` | Um registro por ativo por data por carteira |
| Dividend | UUID interno | `external_id + provider` ou `asset_id + ex_date + type` | Deduplicar por hash |
| Institution | UUID interno | `code` | `code` único |
| Category | UUID interno | `slug` | `slug` único |
| Currency | `code` (PK) | — | `code` ISO 4217 único |
| User | UUID interno | `email` | `email` único |
| Provider | UUID interno | `user_id + type` | Um provider por tipo por usuário |

---

## Regras de Imutabilidade

| Entidade | Imutável | Pode Atualizar | Soft Delete | Hard Delete |
|---|---|---|---|---|
| Transaction | **SIM** (dados financeiros) | `category_id`, `tags` (metadados do usuário) | ✅ | ❌ Nunca |
| Account | Não | Todos campos | ✅ | ❌ |
| Asset | Parcial (ticker/exchange) | `name`, `sector`, `price` | ❌ | ❌ |
| Position | **SIM** (snapshot imutável) | Não — criar novo snapshot | ❌ | ❌ |
| Dividend | **SIM** | Não | ❌ | ❌ |
| Institution | Não | `name`, `logo_url` | ❌ | ❌ |
| Category | Não | `name`, `color`, `icon` | ✅ | ❌ se tiver txns |
| Currency | **SIM** | Não | ❌ | ❌ |
| User | Parcial (`email`) | `name`, `password`, `role` | ✅ | ❌ |
| Provider | Não | `status`, `config`, `sync_status` | ✅ | ✅ (sem dados) |

---

## Regras de Sincronização

| Entidade | Pode Criar | Pode Alterar | Source of Truth |
|---|---|---|---|
| Transaction | Provider ou Manual | Apenas `category`, `tags` pelo usuário | Provider de origem |
| Account | Provider ou Manual | Provider atualiza saldo | Provider de origem |
| Asset | Provider ou Manual ou YFinance | YFinance atualiza preços | Pierre (Banking) / MyProfit (Investimentos) |
| Position | Provider (snapshot) | Novo snapshot por sync | MyProfit |
| Dividend | Provider ou CSV | Não editável | MyProfit |
| Institution | Sistema ou Provider | Sistema | Sistema |
| Category | Sistema ou Usuário | Usuário | Sistema (categorias padrão) |
| User | Sistema (Bootstrap) | Usuário | Sistema |
| Provider | Usuário (configuração) | Sistema (status) | Sistema |

---

## Regras de Negócio

### Deduplicação de Transações
1. Ao ingerir uma nova transação do Provider, calcular `hash = SHA256(external_id + provider + date + amount)`.
2. Se `hash` já existir no banco → ignorar (não duplicar).
3. Se `external_id + provider` já existir mas hash diferente → atualizar campos não-financeiros.

### Classificação de Categorias
1. Se Provider envia categoria nativa → criar/buscar Category por `slug` normalizado.
2. Se Provider não envia categoria → marcar como `NULL` para classificação por IA.
3. Usuário pode sobrescrever categoria sem afetar dados do Provider.

### Posições
1. Positions são **snapshots imutáveis**. Nunca atualizar um registro existente.
2. Cada sync cria um novo `Position` com `snapshot_date = hoje`.
3. Para exibir a posição atual, sempre buscar o `Position` com `snapshot_date` mais recente por `asset_id + portfolio_id`.

### Dividendos
1. `ex_date` é imutável após criação.
2. Cálculo de `net_amount` = `gross_amount - ir_withheld`. Se IR não informado → `net_amount = gross_amount`.

### Saldos de Conta
1. `balance` em `Account` é sempre um snapshot — não calculado em tempo real.
2. Atualizar somente via sync do Provider.
3. Manter `balance_updated_at` para exibir "dados de X atrás" na UI.
