> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Configuração de Ambiente — FIN Analytics

Fonte complementar: [19_ENVIRONMENT.md](19_ENVIRONMENT.md)

---

## Variáveis de Ambiente (Completo)

### Banco de Dados

| Variável | Obrigatória | Formato | Exemplo | Consumidor |
|---|---|---|---|---|
| `DATABASE_URL` | ✅ | URL SQLAlchemy | `sqlite+aiosqlite:///./database/fin_analytics.db` | Python (SQLAlchemy) |

---

### Autenticação

| Variável | Obrigatória | Formato | Exemplo | Consumidor |
|---|---|---|---|---|
| `JWT_SECRET` | ✅ | string ≥ 32 chars | `my-super-secret-key-32chars-min` | Python (core/security.py) |
| `JWT_EXPIRE_MINUTES` | ❌ | integer | `60` | Python (core/security.py) |
| `JWT_REFRESH_EXPIRE_DAYS` | ❌ | integer | `7` | Python (core/security.py) |

---

### Pierre Finance

| Variável | Obrigatória | Formato | Exemplo | Consumidor |
|---|---|---|---|---|
| `PIERRE_API_KEY` | ✅* | string `sk-...` | `sk-XwXm...` | Python, Node (MCP via scripts/start_mcp.ps1) |

*Obrigatória apenas se o Provider Pierre estiver habilitado.

---

### MyProfit

| Variável | Obrigatória | Formato | Exemplo | Consumidor |
|---|---|---|---|---|
| `MYPROFIT_USERNAME` | ✅* | email | `user@email.com` | Python (integrations/myprofit/) |
| `MYPROFIT_PASSWORD` | ✅* | string | `senha123` | Python |

*Obrigatória apenas se o Provider MyProfit estiver habilitado.

---

### Inteligência Artificial

| Variável | Obrigatória | Formato | Exemplo | Consumidor |
|---|---|---|---|---|
| `GEMINI_API_KEY` | ❌ | string | `AIzaSy...` | Python (integrations/gemini/) |
| `OPENAI_API_KEY` | ❌ | string | `sk-...` | Python (reservado) |

---

### Aplicação

| Variável | Obrigatória | Formato | Exemplo | Consumidor |
|---|---|---|---|---|
| `ENVIRONMENT` | ✅ | `development` / `production` | `development` | Python (core/config.py) |
| `YFINANCE_ENABLED` | ❌ | boolean | `true` | Python |
| `ALLOWED_ORIGINS` | ❌ | CSV de URLs | `http://localhost:3000` | Python (CORS middleware) |
| `LOG_LEVEL` | ❌ | `DEBUG`/`INFO`/`WARNING`/`ERROR` | `INFO` | Python (core/logging.py) |
| `CACHE_TTL_SECONDS` | ❌ | integer | `300` | Python (ICache) |
| `SYNC_INTERVAL_HOURS` | ❌ | integer | `6` | Python (IScheduler) |

---

## Regras de Configuração

1. **Nunca commitar `.env`** — apenas `.env.example` (valores em branco)
2. `.env` é carregado pelo `pydantic-settings` em `core/config.py`
3. Para o MCP (Node), usar obrigatoriamente `scripts/start_mcp.ps1` que exporta as variáveis
4. Em produção, usar variáveis de ambiente do sistema (não arquivo `.env`)
5. `ISecrets.get(key)` é o único ponto de acesso a secrets em Use Cases

---

## Exemplo de .env.example (Atualizado)

```env
# Banco de Dados
DATABASE_URL=sqlite+aiosqlite:///./database/fin_analytics.db

# Autenticação
JWT_SECRET=
JWT_EXPIRE_MINUTES=60
JWT_REFRESH_EXPIRE_DAYS=7

# Pierre Finance
PIERRE_API_KEY=

# MyProfit
MYPROFIT_USERNAME=
MYPROFIT_PASSWORD=

# IA
GEMINI_API_KEY=
OPENAI_API_KEY=

# Aplicação
ENVIRONMENT=development
YFINANCE_ENABLED=true
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```
