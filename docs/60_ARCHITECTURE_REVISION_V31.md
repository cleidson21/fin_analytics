> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Revisão Arquitetural V3.1 — FINANALYTICS

**Data:** 2026-07-30
**Status:** VIGENTE — Substitui premissas anteriores com base na análise do payload real de `GET /tools/api/get-transactions`.

---

## 1. Objetivo da versão 1.0

> Entregar um sistema onde o usuário sincroniza sua conta da Pierre e sua carteira do MyProfit, armazena todas as informações em um banco local, consulta esses dados em dashboards e possui uma base consolidada para análises futuras pelo Gemini. Nesta versão, o sistema não recalcula informações dos provedores nem implementa novos conectores de importação.

### Não Objetivos da V1.0

O FINANALYTICS V1.0 **não tem como objetivo competir com agregadores financeiros nem substituir os Providers.**

Seu objetivo exclusivo é:
- Centralizar os dados locais;
- Oferecer dashboards rápidos;
- Permitir análises inteligentes;
- Manter um histórico consolidado.

---

## 2. Filosofia de Arquitetura

O backend deixa de ser um motor de interpretação de dados. Passa a ser um motor de passagem direta e eficiente:

```
Pierre / MyProfit
        │
        ▼
  Sistema sincroniza
        │
        ▼
  Sistema persiste
        │
        ▼
  Sistema consulta
        │
        ▼
  Sistema relaciona
        │
        ▼
  Sistema apresenta
        │
        ▼
  Gemini analisa (futuro)
```

**Antes:**
Pierre → Sistema interpreta → Banco

**Agora:**
Pierre → Sistema persiste → Sistema consulta → Sistema relaciona → Sistema apresenta

---

## 3. Princípios Arquiteturais (Regras de Ouro)

1. **Nunca recalcular dados fornecidos pelos Providers.**
2. **Persistir exatamente o que foi recebido.**
3. **Imutabilidade dos Dados de Origem:** O sistema nunca editará registros sincronizados. Correções e enriquecimentos serão armazenados em estruturas próprias (ex: `transaction_notes`), preservando intacto o dado original recebido.
4. **Idempotência Absoluta:** Toda sincronização deverá ser idempotente. Executar a mesma sincronização duas vezes nunca poderá gerar duplicação de dados.
5. **O Gemini é estritamente Read Only.** Não escreve no banco.
6. **Banco Local como Fonte Oficial:** Após sincronizados, os dados persistidos tornam-se a única fonte consultada pelo sistema. Nenhuma tela poderá consumir diretamente APIs da Pierre ou do MyProfit.
7. **Vertical Slice Inegociável:** Toda funcionalidade deverá ser implementada verticalmente. Cada Sprint só será considerada concluída quando Backend, Banco, API, Frontend, testes e documentação estiverem funcionando em conjunto.
8. **Schema First:** O banco de dados é definido antes da implementação do backend, e o backend antes do frontend. Nenhuma camada poderá criar estruturas não documentadas.

---

## 4. Source of Truth Contratual

Os domínios são isolados e definitivos. **Nenhum domínio será recalculado pelo FINANALYTICS.**

### Dados Canônicos

> Os dados persistidos no banco local representam uma cópia canônica dos Providers. O banco local é a **única** fonte utilizada pelo Frontend. Após sincronizados, nenhuma tela do sistema consultará a API da Pierre ou do MyProfit diretamente para renderizar dados.

### Pierre — Movimentações Financeiras

Fonte oficial de:
- Contas bancárias (`account_type: BANK`)
- Cartões de crédito (`account_type: CREDIT`)
- Transações (extrato corrente + fatura cartão)
- Categorias originárias (string fornecida pelo provider)
- Faturas (`bill_id`, `installment_number`, `total_installments`)

A Pierre **já realiza**:
- Normalização do dado bancário (Open Finance)
- Categorização das transações
- Identificação de contas e cartões
- Identificação de parcelas e suas faturas

**O FINANALYTICS NÃO repetirá nenhum desses processamentos.**

### MyProfit — Investimentos

Fonte oficial de:
- Ativos (ações, FIIs, etc.)
- Posições (custódia B3)
- Dividendos
- Rentabilidade
- Patrimônio

MyProfit **NÃO insere transações no domínio financeiro**. É um domínio paralelo e independente.

---

## 5. Providers Oficiais (Congelado para V1.0)

```
✓ Pierre      → Movimentações financeiras (Open Finance)
✓ MyProfit    → Patrimônio, carteira, dividendos, investimentos
```

**Não são providers desta versão:**
- CSV
- OFX
- Open Finance direto (Banco Central)
- Pluggy direto
- Qualquer outro aggregator

---

## 6. Modelagem do Banco de Dados

### Política de Evolução

A estrutura das tabelas será alterada **apenas** quando:
- Houver mudança oficial na API da Pierre;
- Houver mudança oficial na API do MyProfit;
- For necessário suportar uma funcionalidade aprovada no Roadmap.

Não serão criadas colunas preventivas. **Toda alteração estrutural ocorre exclusivamente por Migration versionada. É proibida alteração manual do banco.**

### Regra do `extra_json`

Armazena apenas campos desconhecidos ou não utilizados na versão atual. **Nenhuma funcionalidade do sistema poderá depender exclusivamente de `extra_json`.** Sempre que um campo armazenado nele passar a ser utilizado ativamente, deverá ser promovido para coluna própria via Migration.

---

### Tabela: `accounts`

```sql
PRIMARY KEY (provider, external_id)

provider            TEXT NOT NULL   -- 'pierre' | 'myprofit'
external_id         TEXT NOT NULL   -- ID da conta no provider
name                TEXT NOT NULL   -- "Nubank"
type                TEXT NOT NULL   -- BANK | CREDIT
subtype             TEXT            -- CHECKING_ACCOUNT | CREDIT_CARD
bank                TEXT            -- "Nu Pagamentos S.A."
connector           TEXT            -- "Nubank"
credit_metadata_json TEXT           -- JSON com limites, fatura, etc. (estado volátil da conta)
last_sync           DATETIME
```

---

### Tabela: `transactions`

```sql
PRIMARY KEY (provider, external_id)

-- Integração
provider              TEXT NOT NULL   -- 'pierre'
external_id           TEXT NOT NULL   -- ID da transação na Pierre (UUID)
account_provider      TEXT NOT NULL   -- FK → accounts.provider
account_external_id   TEXT NOT NULL   -- FK → accounts.external_id

-- Dados canônicos
description           TEXT NOT NULL
original_description  TEXT
category              TEXT            -- String como recebida da Pierre (ex: "Compras online")
original_category     TEXT
amount                NUMERIC(12,2) NOT NULL
currency              TEXT NOT NULL   -- 'BRL'
date                  DATETIME NOT NULL
status                TEXT NOT NULL   -- POSTED | PENDING
type                  TEXT NOT NULL   -- DEBIT | CREDIT

-- Dados desnormalizados pesquisáveis
merchant_name         TEXT
bill_id               TEXT            -- ID da fatura (credit_card_data.billId)
installment_number    INTEGER         -- credit_card_data.installmentNumber
total_installments    INTEGER         -- credit_card_data.totalInstallments
purchase_date         DATETIME        -- credit_card_data.purchaseDate
receiver_name         TEXT            -- payment_data.receiver.name
payer_name            TEXT            -- payment_data.payer.name

-- Flags
manual_transaction    BOOLEAN NOT NULL DEFAULT FALSE

-- Escape
extra_json            TEXT            -- JSON para campos não mapeados ou não utilizados
```

**Campos eliminados em relação à versão anterior:**
- `hash` (artificial, Pierre já tem `id` único)
- `purchase_id` (artificial, Pierre entrega `bill_id` + `installment_number`)
- `direction` (redundante, deduzido de `type` e sinal de `amount`)
- `is_recurring` (não fornecido pela Pierre neste formato)
- `category_id` (FK para tabela de categorias — desnecessária, categoria é string)
- `user_id` (sistema single-user, auth via JWT)

---

### Tabela: `categories` (Catálogo — Sem FK)

```sql
PRIMARY KEY (provider, name)

provider          TEXT NOT NULL
name              TEXT NOT NULL   -- "Compras online", "Transferências"
normalized_name   TEXT            -- versão normalizada para buscas
```

> A tabela de categorias é um **catálogo estatístico** construído automaticamente durante o UPSERT de transações. Não existe relacionamento de FK entre `transactions` e `categories`. A Pierre pode criar novas categorias a qualquer momento e o banco continuará funcionando normalmente.

---

### Tabela: `sync_state` (Controle Incremental)

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

### Tabela: `sync_history` (Auditoria)

```sql
id            INTEGER PRIMARY KEY AUTOINCREMENT
provider      TEXT NOT NULL
started_at    DATETIME NOT NULL
finished_at   DATETIME
received      INTEGER DEFAULT 0
inserted      INTEGER DEFAULT 0
updated       INTEGER DEFAULT 0
ignored       INTEGER DEFAULT 0
status        TEXT    -- SUCCESS | FAILED | PARTIAL
error         TEXT
```

---

## 7. Pipeline de Sincronização

O pipeline é **único**. Não existem dois fluxos de código — apenas dois modos de entrada de dados:

```
[PROD]  Pierre API → JSON em memória ─┐
[DEV]   Pierre API → transactions.json ─┤
[REPLAY] transactions.json existente ──┘
                                       │
                                       ▼
                               Validação simples
                                       │
                                       ▼
                            Accounts UPSERT (provider, external_id)
                                       │
                                       ▼
                          Transactions UPSERT (provider, external_id)
                                       │
                                       ▼
                            Catálogo Categories (ON CONFLICT IGNORE)
                                       │
                                       ▼
                           sync_state UPDATE + sync_history INSERT
```

**Modo Desenvolvimento:** Salva o JSON bruto da API em `exports/pierre/raw/` para reprodução de bugs, testes e replay offline.
**Modo Replay:** Reprocessa um JSON salvo sem chamar a API. Mesmo pipeline, mesma validação, mesmo resultado esperado.
**Modo Produção:** JSON fica em memória. Sem arquivo em disco.

---

## 8. Estrutura Arquitetural (Organização Física)

O projeto adota **Vertical Slices por Domínio**, abandonando o modelo de camadas horizontais.

```
backend/
    domains/
        pierre/
            models.py       ← SQLAlchemy
            schemas.py      ← Pydantic (DTOs)
            repository.py   ← Acesso ao banco
            service.py      ← Orquestração e regras
            router.py       ← Endpoints FastAPI
            pipeline.py     ← Lógica de importação/sync
            tests/
        myprofit/
            models.py
            schemas.py
            repository.py
            service.py
            router.py
            tests/
        dashboard/
            schemas.py
            service.py
            router.py
            tests/
        ai/
            service.py      ← Read Only
            router.py
            tests/
        auth/
            models.py
            schemas.py
            repository.py
            service.py
            router.py
            tests/
        shared/
            db.py           ← Engine, Session
            config.py       ← Settings
            security.py     ← JWT helpers
```

**Regras de Comunicação entre Domínios:**
Nenhum domínio poderá depender diretamente da implementação interna de outro domínio. A comunicação entre domínios deverá ocorrer preferencialmente por `Services` públicos e contratos (Schemas/DTOs). Exceções somente quando explicitamente aprovadas na arquitetura.

É proibido criar um módulo genérico gigante (ex: `utils.py` com regras de negócio de múltiplos domínios).

---

## 9. Roadmap V3.1

### Sprint 4.4 — Pierre Completo
| Sub-entrega | Conteúdo |
|---|---|
| 4.4.1 | Banco e Pipeline base (models, migrations, pipeline skeleton) |
| 4.4.2 | Sincronização Pierre (carga real, UPSERT, modos Dev/Prod/Replay) |
| 4.4.3 | Governança (`sync_state`, `sync_history`, tela de status) |
| 4.4.4 | Dashboard com dados reais (zero mocks) |
| 4.4.5 | Teste de Replay (idempotência comprovada) |

### Sprint 4.5 — MyProfit
Sincronização de Carteira, Ativos, Dividendos. Dashboard de patrimônio.

### Sprint 4.6 — Relacionamento
Cruzamento analítico Pierre × MyProfit. Visão consolidada.

### Sprint 4.7 — Gemini
Análises e insights. Estritamente Read Only. Sem escrita no banco.

---

## 10. Definition of Done — Sprint 4.4

A Sprint 4.4 é considerada concluída **somente quando:**
1. O usuário consegue sincronizar dados reais da Pierre;
2. As tabelas `accounts`, `transactions`, `categories`, `sync_state` e `sync_history` estão corretamente populadas;
3. Sincronizações sucessivas **não geram duplicações** (Replay Test aprovado);
4. O Dashboard consome **exclusivamente** dados do banco local;
5. A tela de Governança exibe histórico e status das sincronizações;
6. Backend, Banco, API, Frontend, testes e documentação funcionam em conjunto (**Vertical Slice**);
7. **Nenhum dado mockado existe no fluxo Pierre.**

---

## 11. Fora do Escopo da Versão 1.0

Não fazem parte desta implementação:
- Importação via CSV ou OFX
- Open Finance genérico ou Banco Central
- Novos Providers (além de Pierre e MyProfit)
- Reclassificação automática por IA
- Alteração automática de categorias
- Escrita de dados de volta nos Providers
- Colunas preventivas para funcionalidades futuras

---

## 12. Impacto sobre Documentação Anterior

| Documento | Status |
|---|---|
| `01_ARCHITECTURE.md` | Precisa atualização |
| `02_DOMAIN_MODEL.md` | Precisa atualização |
| `03_DATABASE.md` | Precisa atualização |
| `05_IMPORT_PIPELINE.md` | Precisa atualização |
| `09_ROADMAP.md` | Precisa atualização |
| `16_PIERRE_REFERENCE.md` | Precisa atualização (schema real) |
| `21_PROVIDER_MODELS.md` | Precisa atualização (campos reais) |
| `36_SOURCE_OF_TRUTH.md` | Precisa atualização (nova filosofia) |
| `54_IMPLEMENTATION_ORDER.md` | Será substituído pelas Sprints 4.4–4.7 |
| `29_DOMAIN_ENTITIES.md` | Obsoleto (entidades redefinidas aqui) |
| `32_PROVIDER_MAPPING.md` | Obsoleto (mapeamento eliminado) |
| `40_DTOS.md` | Obsoleto (DTOs agora em `schemas.py` por domínio) |

> Este documento (`60_ARCHITECTURE_REVISION_V31.md`) é a nova referência arquitetural oficial. Em caso de conflito com documentos anteriores, este prevalece.
