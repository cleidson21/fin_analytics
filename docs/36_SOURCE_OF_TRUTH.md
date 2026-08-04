> [!IMPORTANT]
<<<<<<< HEAD
> A pasta `docs/` é a única fonte oficial de documentação do projeto. Este documento foi atualizado pela Revisão Arquitetural V3.1 (`60_ARCHITECTURE_REVISION_V31.md`).

# Source of Truth por Domínio

**[ATUALIZADO em 2026-07-30 — Revisão V3.1]**

=======
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Source of Truth por Domínio

>>>>>>> 021d439dcbb06040c0005dbd27456a26c9f1d7e9
---

## Definição

<<<<<<< HEAD
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
=======
**Source of Truth (SoT)** é o Provider cuja versão dos dados prevalece em caso de conflito. Outros Providers podem **complementar** mas não **sobrescrever** o SoT.

---

## Fonte Única da Verdade (Regra Oficial da Arquitetura)

A integração com a Pierre (e outros providers) obedecerá obrigatoriamente ao fluxo:
```
Pierre Finance
        │
        ▼
Sync Service
        │
        ▼
SQLite
        │
        ▼
Read Models
        │
        ▼
REST API
        │
        ▼
Frontend
```

**É terminantemente proibido:**
- consumir Pierre diretamente pelo frontend;
- realizar consultas em tempo real para renderização das páginas;
- depender da disponibilidade da Pierre para funcionamento da interface.

Toda consulta da interface deve passar pela nossa REST API e consumir prioritariamente o banco SQLite.

---

## Matriz de Source of Truth

| Dado | Source of Truth | Complementar | Observações |
|---|---|---|---|
| **Saldos bancários** | Pierre | — | Via `/tools/api/get-balance` |
| **Transações bancárias** | Pierre | CSV (manual) | Pierre é autoridade para dados Open Finance |
| **Faturas de cartão** | Pierre | — | Via `/tools/api/get-bills` |
| **Assinaturas (Subscriptions)** | Backend (Inferência) | Pierre | Pierre fornece as transações originais; o Backend infere a periodicidade baseada na repetição mensal e flag `is_recurring`. |
| **Parcelamentos (Installments)**| Backend (Inferência) | Pierre | Pierre envia parcelas isoladas; Backend agrupa via `purchase_id` e calcula dívida restante. Frontend APENAS exibe. |
| **Carteiras de investimentos** | MyProfit | — | B3 via scraping |
| **Posições atuais** | MyProfit | YFinance (preços) | MyProfit é posição, YFinance é preço atual |
| **Dividendos** | MyProfit | CSV | CSV para dividendos não cobertos |
| **Preços de ativos** | YFinance | — | Cotações em tempo real |
| **Categorias** | Sistema (padrão) + IA | Usuário | Usuário pode sobrescrever |
| **Usuários** | Sistema | — | Autenticação interna |
| **Credenciais** | `.env` / Secrets | — | Nunca no banco |

---

## Responsabilidades de Cálculo (Inferência vs Exibição)

Para fins de governança de arquitetura, aplicam-se as seguintes regras sobre inteligência de dados (particularmente em **Assinaturas e Parcelamentos**):

1. **Responsabilidade do Backend:** O backend é o ÚNICO autorizado a realizar matemática de datas, projeções anuais de gastos (Assinaturas), agrupamento de histórico fantasma e inferência de parcelas passadas/restantes (Installments).
2. **Responsabilidade do Frontend:** O frontend é passivo. Ele APENAS renderiza os DTOs pré-calculados. É **terminantemente proibido** realizar loops no frontend para somar parcelas ou projetar encerramento de dívidas.
3. **Origem dos Dados Físicos:** O provedor externo (ex: Pierre) é a origem do dado físico (uma transação isolada de cartão de crédito no extrato). O backend os transforma no modelo canônico (InstallmentItemDTO).

---

## Regra de Conflito

Quando dois Providers retornam dados conflitantes para a mesma entidade:

1. Aplicar a hierarquia da tabela acima (SoT prevalece).
2. Se `external_id` coincidir mas `amount` diferir → log de conflito + manter SoT.
3. Sempre registrar a origem (`provider`) em cada registro para rastreabilidade.

---

# Estratégia de Sincronização

---

## Ciclo de Sync

```
1. Trigger (manual / agendado / webhook futuro)
2. Provider.authenticate()
3. Provider.fetch(resource, params)
4. Mapper.to_canonical(raw_data)
5. Deduplicate (hash check)
6. Persist (create / update metadados)
7. Update Provider.last_sync_at + sync_status
8. Emit domain events (opcional)
```

## Modos de Sincronização

O sistema utilizará **sincronização híbrida**, que deverá alimentar exclusivamente o banco SQLite.

### 1. Manual
- **Botão:** "Atualizar Dados" na interface.
- **Ação:** Executará o `manualUpdate` da Pierre e forçará a atualização do banco SQLite.

### 2. Automática
- **Mecanismo:** Scheduler configurável.
- **Exemplos de gatilhos:** na inicialização do sistema, diariamente em horários predefinidos, ou sob demanda do sistema (heurísticas).

---

## Frequência Sugerida

| Recurso | Frequência | Justificativa |
|---|---|---|
| Transações Pierre | A cada 6 horas | Rate limit Pierre |
| Saldos Pierre | A cada 1 hora | Dados críticos |
| Posições MyProfit | 1x por dia (fim de dia) | B3 fecha às 17h |
| Dividendos MyProfit | 1x por semana | Baixa frequência |
| Preços YFinance | A cada 30 min (mercado aberto) | Cotações |

---

## Estratégia de Fallback

| Cenário | Ação |
|---|---|
| Pierre offline | Exibir dados do cache + aviso na UI |
| MyProfit sessão expirada | Notificar usuário para reautenticar |
| YFinance rate limit | Retornar último preço conhecido + timestamp |
| Erro 5XX do Provider | Retry com backoff exponencial (3 tentativas) |
>>>>>>> 021d439dcbb06040c0005dbd27456a26c9f1d7e9
