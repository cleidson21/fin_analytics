> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Source of Truth por Domínio

---

## Definição

**Source of Truth (SoT)** é o Provider cuja versão dos dados prevalece em caso de conflito. Outros Providers podem **complementar** mas não **sobrescrever** o SoT.

---

## Matriz de Source of Truth

| Dado | Source of Truth | Complementar | Observações |
|---|---|---|---|
| **Saldo bancário** | Pierre | — | Via `/tools/api/get-balance` |
| **Transações bancárias** | Pierre | CSV (manual) | Pierre é autoridade para dados Open Finance |
| **Faturas de cartão** | Pierre | — | Via `/tools/api/get-bills` |
| **Parcelamentos** | Pierre | — | Via `/tools/api/get-installments` |
| **Carteiras de investimentos** | MyProfit | — | B3 via scraping |
| **Posições atuais** | MyProfit | YFinance (preços) | MyProfit é posição, YFinance é preço atual |
| **Dividendos** | MyProfit | CSV | CSV para dividendos não cobertos |
| **Preços de ativos** | YFinance | — | Cotações em tempo real |
| **Categorias** | Sistema (padrão) + IA | Usuário | Usuário pode sobrescrever |
| **Usuários** | Sistema | — | Autenticação interna |
| **Credenciais** | `.env` / Secrets | — | Nunca no banco |

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
