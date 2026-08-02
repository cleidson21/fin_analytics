> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Commands — FIN Analytics

Commands representam intenções de mutação. Sempre imutáveis após criação. Nunca contêm lógica — apenas dados validados.

---



## AuthenticateUserCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `email` | string | ✅ | Email válido |
| `password` | string | ✅ | Não vazio |

---

## RefreshTokenCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `refresh_token` | string | ✅ | JWT válido, não expirado |

---

## SyncPierreCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `user_id` | UUID | ✅ | Usuário existente |
| `start_date` | date | ❌ | Formato ISO 8601. Máx 365 dias atrás |
| `end_date` | date | ❌ | >= start_date |
| `force` | boolean | ❌ | Default false. True ignora cache |
| `resources` | list[str] | ❌ | ["accounts", "transactions", "bills"] — default all |

---

## SyncMyProfitCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `user_id` | UUID | ✅ | |
| `resources` | list[str] | ❌ | ["positions", "dividends"] — default all |
| `force` | boolean | ❌ | Default false |

---

## RefreshQuotesCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `user_id` | UUID | ✅ | |
| `tickers` | list[Ticker] | ❌ | Se vazio, atualiza todos os ativos ativos |

---

## ImportCsvCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `user_id` | UUID | ✅ | |
| `file_bytes` | bytes | ✅ | Max 10MB |
| `csv_type` | string | ✅ | "transactions" ou "dividends" |
| `account_id` | UUID | ❌ | Se transactions, qual conta associar |
| `encoding` | string | ❌ | Default: auto-detect |
| `delimiter` | string | ❌ | Default: auto-detect |
| `date_format` | string | ❌ | Default: auto-detect |
| `confirm` | boolean | ✅ | False = preview, True = persistir |

---

## ClassifyTransactionCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `user_id` | UUID | ✅ | |
| `transaction_ids` | list[UUID] | ❌ | Se vazio, classifica todas sem categoria |
| `override` | boolean | ❌ | Default false. True reclassifica mesmo já classificadas |

---

## UpdateCategoryCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `user_id` | UUID | ✅ | |
| `transaction_id` | UUID | ✅ | |
| `category_id` | UUID | ✅ | |

---

## ConnectProviderCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `user_id` | UUID | ✅ | |
| `provider_type` | ProviderType | ✅ | Enum válido |
| `config` | JSON | ❌ | Não deve conter secrets |

---

## DisconnectProviderCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `user_id` | UUID | ✅ | |
| `provider_id` | UUID | ✅ | |
| `delete_data` | boolean | ❌ | Default false |

---

## GenerateInsightsCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `user_id` | UUID | ✅ | |
| `period` | DateRange | ❌ | Default: últimos 30 dias |
| `context` | string | ❌ | Pergunta livre para a IA |

---

## BackupDatabaseCommand
| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `user_id` | UUID | ✅ | |
| `destination` | string | ❌ | Default: local storage |

---

## Regra Geral de Commands

1. Commands são **objetos de dados imutáveis** — sem métodos, sem lógica.
2. Toda validação de Command ocorre na **camada Application**, antes de entrar no Use Case.
3. Commands nunca referenciam entidades do Provider diretamente.
4. Commands nunca retornam resultado — retornam o Use Case que os processa.
