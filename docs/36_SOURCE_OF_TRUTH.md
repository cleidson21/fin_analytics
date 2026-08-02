> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto. Este documento foi atualizado pela Revisão Arquitetural V3.1 (`60_ARCHITECTURE_REVISION_V31.md`).

# Source of Truth por Domínio

**[ATUALIZADO em 2026-07-30 — Revisão V3.1]**

---

## Definição

**Source of Truth (SoT)** é o Provider cuja versão dos dados é canônica e prevalece em caso de conflito. O sistema **nunca recalcula nem reclassifica** dados provenientes do SoT.

---

## Fonte Única da Verdade — Regra Oficial

```
Pierre Finance (movimentações)
        │
        ▼
   Pipeline de Sync
        │
        ▼
   SQLite (banco local)
        │
        ▼
   REST API
        │
        ▼
   Frontend

MyProfit (investimentos)
        │
        ▼
   Pipeline de Sync
        │
        ▼
   SQLite (banco local)
```

**É terminantemente proibido:**
- Consumir Pierre ou MyProfit diretamente pelo frontend;
- Realizar consultas em tempo real aos providers para renderizar páginas;
- Depender da disponibilidade dos providers para funcionamento da interface.

---

## Dados Canônicos

> Os dados persistidos no banco local representam uma cópia canônica dos Providers. O banco local é a **única** fonte utilizada pelo Frontend. Após sincronizados, nenhuma tela consultará a API da Pierre ou do MyProfit diretamente.

---

## Matriz de Source of Truth (V3.1)

| Dado | Source of Truth | Observações |
|---|---|---|
| **Contas bancárias** | Pierre | Via `GET /tools/api/get-transactions` (`account_*` fields) |
| **Cartões de crédito** | Pierre | `account_type: CREDIT` |
| **Transações** | Pierre | Dado canônico, imutável após sync |
| **Categorias** | Pierre | String original (`category`, `original_category`). Catálogo local apenas para consulta. |
| **Faturas / Parcelas** | Pierre | `bill_id`, `installment_number`, `total_installments` fornecidos pelo provider |
| **Ativos** | MyProfit | B3 via scraping MyProfit |
| **Posições** | MyProfit | Custódia atual |
| **Dividendos** | MyProfit | Proventos recebidos |
| **Rentabilidade** | MyProfit | Calculada pelo MyProfit |
| **Patrimônio** | MyProfit | Consolidado pelo MyProfit |

---

## O que a Pierre já realiza (não repetir)

A Pierre entrega dados **já processados** pelo Open Finance:
- Normalização do dado bancário
- Categorização das transações
- Identificação de contas e tipos
- Identificação de parcelas (`installmentNumber`, `totalInstallments`)
- Identificação de faturas (`billId`)

**O FINANALYTICS não deverá repetir nenhum desses processamentos.**

---

## Responsabilidades do Sistema

| Camada | Responsabilidade |
|---|---|
| **Pierre / MyProfit** | Processar, normalizar, categorizar e entregar |
| **Pipeline** | Sincronizar e persistir |
| **Backend** | Consultar, relacionar e apresentar |
| **Frontend** | Exibir — never compute |
| **Gemini** | Analisar (Read Only) |

---

## Estratégia de Sincronização

### Idempotência
Todo UPSERT usa `ON CONFLICT (provider, external_id) DO UPDATE`. A mesma sincronização executada N vezes produz o mesmo estado final no banco.

### Governança
Toda sincronização registra automaticamente em:
- `sync_state` — estado atual do provider (cursor, última sync bem-sucedida)
- `sync_history` — histórico de execuções (received, inserted, updated, ignored, status)

### Modos
| Modo | Fluxo | Uso |
|---|---|---|
| Produção | API → memória → banco | Operação normal |
| Desenvolvimento | API → JSON → banco | Debug e auditoria |
| Replay | JSON → banco | Reprodução de bugs, testes |

## Referência Completa

Ver `60_ARCHITECTURE_REVISION_V31.md` para todos os detalhes arquiteturais vigentes.
