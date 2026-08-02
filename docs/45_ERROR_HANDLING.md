> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Tratamento de Erros — FIN Analytics

---

## Hierarquia de Exceções

```
FINAnalyticsError (base)
├── DomainError
│   ├── ValidationError
│   ├── DuplicateEntityError
│   └── BusinessRuleViolationError
├── ApplicationError
│   ├── UseCaseError
│   ├── CommandValidationError
│   └── UnauthorizedError
├── InfrastructureError
│   ├── DatabaseError
│   ├── ConnectionError
│   └── StorageError
└── ProviderError
    ├── PierreProviderError
    │   ├── PierreAuthError         # 401
    │   ├── PierreRateLimitError    # 429
    │   └── PierreServerError      # 5xx
    ├── MyProfitProviderError
    │   ├── MyProfitSessionExpired
    │   └── MyProfitScrapingError
    └── YFinanceProviderError
```

---

## Códigos de Erro Internos (API)

| Código | HTTP | Descrição |
|---|---|---|
| `AUTH_INVALID_CREDENTIALS` | 401 | Email ou senha inválidos |
| `AUTH_TOKEN_EXPIRED` | 401 | Token JWT expirado |
| `AUTH_TOKEN_INVALID` | 401 | Token JWT malformado |
| `AUTH_INSUFFICIENT_ROLE` | 403 | Usuário sem permissão |
| `USER_NOT_FOUND` | 404 | Usuário não encontrado |
| `USER_ALREADY_EXISTS` | 409 | Email já cadastrado |
| `PROVIDER_NOT_ACTIVE` | 422 | Provider desconectado |
| `PROVIDER_AUTH_ERROR` | 502 | Pierre/MyProfit rejeitou autenticação |
| `PROVIDER_RATE_LIMIT` | 429 | Rate limit do Provider atingido |
| `PROVIDER_UNAVAILABLE` | 503 | Provider indisponível |
| `CSV_INVALID_FORMAT` | 422 | Headers inválidos no CSV |
| `CSV_ENCODING_ERROR` | 422 | Encoding não detectável |
| `ENTITY_NOT_FOUND` | 404 | Entidade genérica não encontrada |
| `DUPLICATE_ENTITY` | 409 | Entidade já existe |
| `VALIDATION_ERROR` | 422 | Dados de entrada inválidos |
| `INTERNAL_ERROR` | 500 | Erro interno inesperado |

---

## Resposta de Erro Padrão (API)

```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Email ou senha inválidos.",
    "details": null,
    "request_id": "uuid-here"
  }
}
```

---

## Estratégia de Retry

| Cenário | Retry | Backoff | Máx Tentativas |
|---|---|---|---|
| Pierre 5xx | ✅ | Exponencial (1s, 2s, 4s) | 3 |
| Pierre 429 | ✅ | Respeitar `Retry-After` header | 3 |
| Pierre 401 | ❌ | — | 0 (notificar usuário) |
| MyProfit sessão | ❌ | — | 0 (notificar usuário) |
| YFinance 5xx | ✅ | Linear (2s) | 3 |
| Database timeout | ✅ | Linear (500ms) | 2 |

---

# Fronteiras Transacionais — FIN Analytics

---

## Regras de Transação de Banco

| Operação | Transação? | Isolamento | Observações |
|---|---|---|---|
| `create(transaction)` | ✅ | Read Committed | Única operação, commit imediato |
| `bulk_create(transactions)` | ✅ | Read Committed | Commit único para todo o lote. Erro em 1 → rollback total |
| `upsert(account)` | ✅ | Serializable | Evita race condition em sync paralelo |
| `update_category` | ✅ | Read Committed | |
| `soft_delete` | ✅ | Read Committed | |
| `SyncPierre` (full) | ❌ | — | **NÃO** é uma única transação — cada recurso é independente |
| `ImportCSV (confirm)` | ✅ por lote | Read Committed | Lotes de 100 linhas. Erro no lote não cancela os anteriores |
| `ClassifyTransaction` | ✅ por item | Read Committed | Um commit por transação classificada |

> [!IMPORTANT]
> A sincronização completa de um Provider **NÃO** é uma única transação do banco. Cada recurso (accounts, transactions, bills) é sincronizado em sua própria janela transacional. Isso garante que uma falha ao buscar bills não cancele as contas já salvas.

---

## Commit Points (Pontos de Commit)

```
SyncPierreAccounts:
  BEGIN TX
    upsert(account_1)
    upsert(account_2)
    ...
  COMMIT                    <- commit do bloco de accounts

SyncPierreTransactions:
  BEGIN TX (lote 1)
    create(tx_1..100)
  COMMIT

  BEGIN TX (lote 2)
    create(tx_101..200)
  COMMIT
```

---

## Rollback Esperado

| Cenário | Rollback |
|---|---|
| Falha de validação de Command | ❌ Nada foi escrito |
| Exceção no meio de `bulk_create` | ✅ Rollback do lote atual |
| Provider retorna 5xx | ❌ Nada foi escrito (leitura falhou) |
| Gemini retorna erro de classificação | ❌ Transação fica sem categoria (sem rollback) |
| Erro de storage no BackupDatabase | ❌ Banco não é afetado |
