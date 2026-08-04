> [!IMPORTANT]
<<<<<<< HEAD
> A pasta `docs/` é a única fonte oficial de documentação do projeto. Este documento foi atualizado pela Revisão Arquitetural V3.1 (`60_ARCHITECTURE_REVISION_V31.md`).

# Pierre Finance — Referência Técnica

**[ATUALIZADO em 2026-07-30 — Revisão V3.1 com payload real analisado]**

## Status da Integração

| Item | Status |
|---|---|
| REST API | ✅ Validado |
| Autenticação Bearer | ✅ Validado |
| MCP STDIO | ✅ Validado |
| Payload RAW analisado | ✅ `transactions_raw_12m.json` (3.1MB, 82.354 linhas) |

## Endpoint Principal

```
GET https://www.pierre.finance/tools/api/get-transactions
Authorization: Bearer <PIERRE_API_KEY>

Params:
  startDate: YYYY-MM-DD
  endDate:   YYYY-MM-DD
  format:    raw | structured
```

## Schema do Payload RAW (confirmado em produção)

### Envelope
```json
{
  "success": true,
  "data": [ ...transactions ]
}
```

### Campos da Transação
```
id                   UUID    – Identificador único da Pierre (usado como external_id)
account_id           UUID    – ID da conta na Pierre (usado como account_external_id)
description          string  – Descrição processada
original_description string  – Descrição original do banco
category             string  – Categoria (ex: "Compras online", "Transferências")
original_category    string  – Categoria original
tr_confidence        null    – Confiança da categorização (não utilizado ainda)
tr_reasoning         null    – Raciocínio (não utilizado ainda)
currency_code        string  – "BRL"
amount               number  – Valor (positivo = débito para cartão, negativo = saída para conta)
amount_in_account_currency null
date                 ISO8601 – Data da transação
installment_due_date ISO8601 – Data de vencimento da parcela
type                 string  – "DEBIT" | "CREDIT"
status               string  – "POSTED" | "PENDING"
payment_data         object  – { payer: {name, document}, receiver: {name, document}, sameOwnership }
credit_card_data     object  – { purchaseDate, installmentNumber, totalInstallments, totalAmount,
                                 billId, isFullInstallmentTransaction, isIndividualInstallment }
merchant             null    – Dados do estabelecimento (quando disponível)
account_name         string  – "Nubank"
account_type         string  – "BANK" | "CREDIT"
account_subtype      string  – "CHECKING_ACCOUNT" | "CREDIT_CARD"
account_item_id      UUID    – ID do item (conexão Open Finance)
connector_name       string  – "Nubank"
connector_image_url  string  – URL do ícone da instituição
account_credit_data  object  – Dados do cartão de crédito (limites, fatura, etc.) — pertence à conta
item_bank_name       string  – Nome oficial da instituição
bill_id              UUID    – ID da fatura (presente em transações de cartão)
bill_due_date        date    – Data de vencimento da fatura
official_bill_amount number  – Valor total da fatura
bill_period_start    date    – Início do período da fatura
bill_period_end      date    – Fim do período da fatura
manual_transaction   bool    – Se é uma transação manual
```

## O que a Pierre já processa (não repetir no backend)

| Processamento | Status |
|---|---|
| Normalização dos dados Open Finance | ✅ Pierre faz |
| Categorização das transações | ✅ Pierre faz |
| Identificação do tipo de conta (BANK/CREDIT) | ✅ Pierre faz |
| Identificação de parcelas | ✅ Pierre faz (`installmentNumber`, `totalInstallments`) |
| Agrupamento por fatura | ✅ Pierre faz (`billId`, `bill_period_start/end`) |

## Mapeamento para o Banco Local

| Campo Pierre | Coluna no Banco | Observação |
|---|---|---|
| `id` | `external_id` | PK composta com `provider='pierre'` |
| `account_id` | `account_external_id` | FK composta |
| `description` | `description` | |
| `original_description` | `original_description` | |
| `category` | `category` | String, sem FK |
| `original_category` | `original_category` | |
| `amount` | `amount` | |
| `currency_code` | `currency` | |
| `date` | `date` | |
| `status` | `status` | |
| `type` | `type` | |
| `merchant.name` | `merchant_name` | |
| `credit_card_data.billId` | `bill_id` | |
| `credit_card_data.installmentNumber` | `installment_number` | |
| `credit_card_data.totalInstallments` | `total_installments` | |
| `credit_card_data.purchaseDate` | `purchase_date` | |
| `payment_data.receiver.name` | `receiver_name` | |
| `payment_data.payer.name` | `payer_name` | |
| `manual_transaction` | `manual_transaction` | |
| `account_credit_data` | `accounts.credit_metadata_json` | Pertence à conta, não à transação |
| Demais campos | `extra_json` | Escape para campos não mapeados |
=======
> A pasta docs/ é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela. Toda nova implementação deve ler os documentos existentes em docs/, atualizá-los quando necessário e registrar decisões arquiteturais por meio de ADRs antes de prosseguir.

# Pierre Finance - Referência Técnica

**Data da Consulta:** 18 de Julho de 2026.
**Acesso:** [VALIDADO] MCP Operacional.

## Endpoint e Ambiente
- **REST:** [CONFIRMADO] Endpoints sob proteção estrita (Erro 403 Forbidden).
- **MCP:** [VALIDADO] Handshake STDIO e proxy conectam perfeitamente através de https://pierre.finance/mcp.

## Autenticação
- **Formato:** [VALIDADO] Authorization: Bearer <API_KEY>

> **Conclusão:** A infraestrutura de conexão está validada. O próximo passo será realizar o dump de ferramentas (Tools) do MCP para revelar os contratos REST finais.
>>>>>>> 021d439dcbb06040c0005dbd27456a26c9f1d7e9
