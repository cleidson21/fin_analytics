> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.
> Em caso de conflito entre documentos, `60_ARCHITECTURE_REVISION_V31.md` prevalece.

# 03 — Banco de Dados V3

**Versão:** 3.0 | **Status:** VIGENTE — Schema Canônico | **Data:** 2026-07-30

---

## Política de Evolução

A estrutura das tabelas será alterada **apenas** quando:
- Houver mudança oficial na API da Pierre
- Houver mudança oficial na API do MyProfit
- For necessário suportar uma funcionalidade aprovada no Roadmap

**Regras inegociáveis:**
- Não serão criadas colunas preventivas para funcionalidades futuras
- Toda alteração estrutural ocorre **exclusivamente por Migration versionada**
- É proibida alteração manual do banco de dados

---

## Tabela: `accounts`

```sql
PRIMARY KEY (provider, external_id)

provider              TEXT NOT NULL   -- 'pierre' | 'myprofit'
external_id           TEXT NOT NULL   -- ID da conta no provider
name                  TEXT NOT NULL   -- "Nubank"
type                  TEXT NOT NULL   -- BANK | CREDIT
subtype               TEXT            -- CHECKING_ACCOUNT | CREDIT_CARD
bank                  TEXT            -- "Nu Pagamentos S.A."
connector             TEXT            -- "Nubank"
credit_metadata_json  TEXT            -- JSON: limites, fatura, etc. (estado volátil)
last_sync             DATETIME
```

---

## Tabela: `transactions`

```sql
PRIMARY KEY (provider, external_id)

-- Integração
provider              TEXT NOT NULL   -- 'pierre'
external_id           TEXT NOT NULL   -- UUID da transação na Pierre
account_provider      TEXT NOT NULL   -- FK → accounts.provider
account_external_id   TEXT NOT NULL   -- FK → accounts.external_id

-- Dados canônicos (persistidos exatamente como recebidos)
description           TEXT NOT NULL
original_description  TEXT
category              TEXT            -- string como recebida da Pierre
original_category     TEXT
amount                NUMERIC(12,2) NOT NULL
currency              TEXT NOT NULL   -- 'BRL'
date                  DATETIME NOT NULL
status                TEXT NOT NULL   -- POSTED | PENDING
type                  TEXT NOT NULL   -- DEBIT | CREDIT

-- Dados desnormalizados pesquisáveis
merchant_name         TEXT
bill_id               TEXT            -- credit_card_data.billId
installment_number    INTEGER         -- credit_card_data.installmentNumber
total_installments    INTEGER         -- credit_card_data.totalInstallments
purchase_date         DATETIME        -- credit_card_data.purchaseDate
receiver_name         TEXT            -- payment_data.receiver.name
payer_name            TEXT            -- payment_data.payer.name

-- Flags
manual_transaction    BOOLEAN NOT NULL DEFAULT FALSE

-- Escape hatch para campos não mapeados
extra_json            TEXT
```

> [!IMPORTANT]
> **Regra do `extra_json`:** Armazena apenas campos desconhecidos ou não utilizados na versão atual. **Nenhuma funcionalidade poderá depender exclusivamente de `extra_json`.** Se um campo tornar-se necessário, deve ser promovido para coluna própria via Migration.

---

## Tabela: `categories` (Catálogo — sem FK)

```sql
PRIMARY KEY (provider, name)

provider          TEXT NOT NULL
name              TEXT NOT NULL   -- "Compras online", "Transferências"
normalized_name   TEXT            -- versão normalizada para buscas
```

> Catálogo estatístico construído automaticamente durante UPSERT de transações. Sem FK com `transactions`. A Pierre pode criar novas categorias a qualquer momento sem impactar o banco.

---

## Tabela: `sync_state` (Controle Incremental)

```sql
PRIMARY KEY (provider)

provider            TEXT NOT NULL
last_success_sync   DATETIME
last_attempt        DATETIME
last_cursor         TEXT
last_period         TEXT
api_version         TEXT
```

---

## Tabela: `sync_history` (Auditoria)

```sql
id            INTEGER PRIMARY KEY AUTOINCREMENT
provider      TEXT NOT NULL
started_at    DATETIME NOT NULL
finished_at   DATETIME
received      INTEGER DEFAULT 0
inserted      INTEGER DEFAULT 0
updated       INTEGER DEFAULT 0
ignored       INTEGER DEFAULT 0
status        TEXT              -- SUCCESS | FAILED | PARTIAL
error         TEXT
```

---

## Referência Completa

Ver [`60_ARCHITECTURE_REVISION_V31.md`](60_ARCHITECTURE_REVISION_V31.md) — Seção 6 (Modelagem do Banco de Dados).
