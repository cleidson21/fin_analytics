> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Eventos do Domínio — FIN Analytics

Eventos representam fatos que aconteceram. São imutáveis e publicados após persistência confirmada.

---

## Estrutura Base de Todo Evento
```
event_id: UUID
event_type: str         # nome do evento
occurred_at: datetime   # gerado pelo Clock
user_id: UUID
correlation_id: UUID    # para rastrear cadeia de operações
```

---



## TransactionImported
**Quando:** Uma ou mais transações importadas de qualquer Provider.
```
provider: ProviderType
account_id: UUID
transactions_count: int
date_range: DateRangeDTO
```

---

## CategoryClassified
**Quando:** Categoria atribuída a uma transação (manual ou IA).
```
transaction_id: UUID
category_id: UUID
method: str    # "manual" | "ai" | "provider"
```

---

## PortfolioUpdated
**Quando:** Posições do portfólio atualizadas (sync MyProfit ou atualização de cotações).
```
portfolio_id: UUID
positions_count: int
total_value_before: Decimal | None
total_value_after: Decimal | None
provider: ProviderType
```

---

## DividendReceived
**Quando:** Dividendo(s) importado(s) e persistido(s).
```
portfolio_id: UUID
asset_id: UUID
dividends_count: int
total_gross: Decimal
```

---

## SyncStarted
**Quando:** Sincronização de um Provider iniciada.
```
provider: ProviderType
resources: list[str]
```

---

## SyncFinished
**Quando:** Sincronização concluída com sucesso total ou parcial.
```
provider: ProviderType
resources: list[str]
created: int
updated: int
skipped: int
errors_count: int
duration_ms: int
```

---

## SyncFailed
**Quando:** Sincronização falhou completamente.
```
provider: ProviderType
error_message: str
error_code: str | None
```

---

## ProviderDisconnected
**Quando:** Provider desconectado pelo usuário.
```
provider_id: UUID
provider_type: ProviderType
data_deleted: bool
```

---

## InsightGenerated
**Quando:** IA gerou novo insight para o usuário.
```
insight_id: UUID
type: str
period: DateRangeDTO | None
```

---

## BackupCreated
**Quando:** Backup do banco de dados criado com sucesso.
```
path: str
size_bytes: int
```

---

## Regras de Eventos

1. Eventos são publicados **após** o commit da transação de banco — nunca antes.
2. Eventos são imutáveis — nunca mutados após criação.
3. O `IEventBus` distribui os eventos assincronamente.
4. Handlers de evento são idempotentes — podem ser executados mais de uma vez sem efeitos colaterais.
5. Falhas em handlers de evento **não** fazem rollback da operação principal.
