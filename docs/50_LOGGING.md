> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Estratégia de Logging — FIN Analytics

---

## Stack de Logging

| Componente | Tecnologia |
|---|---|
| Logger base | `structlog` (structured logging) |
| Formato (dev) | Pretty print com cores |
| Formato (prod) | JSON (uma linha por evento) |
| Handler | `stdout` (capturado por orquestrador) |
| Level padrão | `INFO` (configurável via `LOG_LEVEL`) |

---

## Campos Obrigatórios em Todo Log

```json
{
  "timestamp": "2024-07-19T17:00:00Z",
  "level": "INFO",
  "logger": "application.use_cases.sync_pierre",
  "message": "Sync Pierre started",
  "request_id": "uuid-v4",
  "correlation_id": "uuid-v4",
  "user_id": "uuid-or-null",
  "environment": "development"
}
```

---

## Request ID e Correlation ID

| ID | Gerado por | Propagado via | Finalidade |
|---|---|---|---|
| `request_id` | Middleware da API (por requisição HTTP) | Header `X-Request-ID` | Rastrear uma requisição HTTP individual |
| `correlation_id` | Use Case (por operação) | Context var / log | Rastrear uma cadeia de operações (ex: sync completo) |

**Regra:** O `correlation_id` de um `SyncPierreAccounts` é o mesmo do `SyncPierreTransactions` disparado na sequência.

---

## O Que Logar por Camada

### API Router
- `INFO` Request recebida (método, path, user_id)
- `INFO` Response enviada (status code, duration_ms)
- `WARNING` Rate limit atingido
- `ERROR` Exceção não tratada

### Use Case
- `INFO` Use Case iniciado (nome, user_id, parâmetros não-sensíveis)
- `INFO` Use Case concluído (resultado resumido)
- `WARNING` Dados não encontrados / operação parcial
- `ERROR` Falha com stack trace

### Repository
- `DEBUG` Query executada (sem dados sensíveis)
- `DEBUG` Registros encontrados (count)
- `WARNING` Conflito de upsert

### Provider Adapters
- `INFO` Chamada ao Provider iniciada (endpoint, não a API key)
- `INFO` Resposta recebida (status code, items count)
- `WARNING` Rate limit do Provider (429)
- `ERROR` Falha de autenticação (401/403) — **sem logar a chave**

### Sync/Import
- `INFO` Sync iniciado (provider, resources, user_id)
- `INFO` Sync concluído (created, updated, skipped, errors_count, duration_ms)
- `ERROR` Sync falhou (motivo, sem dados sensíveis)

---

## O Que NUNCA Logar

| Item | Motivo |
|---|---|
| API Keys (`PIERRE_API_KEY`, `GEMINI_API_KEY`) | Exposição de credenciais |
| Senha do usuário (plaintext) | Dados sensíveis |
| `hashed_password` | Dados sensíveis |
| Session cookies do MyProfit | Dados sensíveis |
| Tokens JWT completos | Dados sensíveis |
| CPF/CNPJ | Dados pessoais (LGPD) |
| Números de conta completos | Dados pessoais |

---

## Auditoria (Audit Trail)

Operações críticas geram entradas de auditoria separadas (tabela `audit_log`):

| Evento | Registra |
|---|---|
| Login bem-sucedido | user_id, IP, timestamp |
| Tentativa de login falha | email, IP, timestamp, motivo |
| Token revogado | user_id, jti, motivo |
| Provider conectado/desconectado | user_id, provider_type |
| CSV importado | user_id, tipo, total rows |
| Sync executado | user_id, provider, resultado |
| Categoria alterada manualmente | user_id, transaction_id, old/new category |

---

## Níveis de Log por Ambiente

| Level | Development | Production |
|---|---|---|
| DEBUG | ✅ | ❌ |
| INFO | ✅ | ✅ |
| WARNING | ✅ | ✅ |
| ERROR | ✅ | ✅ |
| CRITICAL | ✅ | ✅ (+ alertas) |
