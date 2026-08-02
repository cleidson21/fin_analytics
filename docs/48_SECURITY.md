> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Segurança — FIN Analytics

---

## JWT (JSON Web Tokens)

| Parâmetro | Valor |
|---|---|
| Algoritmo | `HS256` |
| Payload obrigatório | `sub` (user_id), `exp`, `iat`, `jti` (token ID único) |
| `ACCESS_TOKEN_EXPIRE` | 60 minutos (configurável via `JWT_EXPIRE_MINUTES`) |
| `REFRESH_TOKEN_EXPIRE` | 7 dias |
| Secret | `JWT_SECRET` via `ISecrets` — nunca hardcoded |

### Fluxo de Tokens

```
Login → access_token (60min) + refresh_token (7d)
        ↓
access_token expira → POST /auth/refresh com refresh_token
        ↓
Novo access_token emitido + refresh_token ROTACIONADO (novo jti)
        ↓
Refresh expirado ou revogado → 401 → novo login obrigatório
```

### Revogação de Tokens

- Refresh tokens são armazenados em banco (tabela `refresh_tokens`) com `jti`, `user_id`, `expires_at`, `revoked`
- Ao fazer logout: `revoked=True`
- Ao rotacionar: token antigo revogado, novo criado
- Validação: verificar se `jti` existe e não está revogado

---

## Password Hashing

| Parâmetro | Valor |
|---|---|
| Algoritmo | `bcrypt` |
| Rounds | 12 (mínimo) |
| Biblioteca | `passlib[bcrypt]` |

**Regras:**
- `hashed_password` **nunca** sai do banco — nunca serializado em DTO
- Comparação sempre via `verify_password(plain, hashed)` — nunca comparar strings diretamente
- Senhas temporárias ou reset são geradas como UUID4 e comunicadas por email

---

## Secrets — Regras de Armazenamento

| Secret | Armazenamento | Nunca |
|---|---|---|
| `JWT_SECRET` | `.env` / env var | Banco, código, log |
| `PIERRE_API_KEY` | `.env` / env var | Banco, log, resposta API |
| `GEMINI_API_KEY` | `.env` / env var | Banco, log |
| `MYPROFIT_PASSWORD` | `.env` (temporário) | Banco |
| `MYPROFIT_SESSION_COOKIES` | Banco (criptografado) ou memória | Plaintext |

> [!CAUTION]
> **Nunca commitar o arquivo `.env` com valores reais.** O `.gitignore` já exclui `.env`. Apenas `.env.example` (sem valores) é versionado.

---

## CORS

```
Origins permitidas (development):
  - http://localhost:3000
  - http://localhost:5173
  - http://127.0.0.1:*

Origins permitidas (production):
  - Configurar via ALLOWED_ORIGINS no .env

Métodos permitidos: GET, POST, PUT, PATCH, DELETE, OPTIONS
Headers permitidos: Authorization, Content-Type, X-Request-ID
Credentials: True (para cookies de sessão)
```

---

## Rate Limiting

| Endpoint | Limite | Janela |
|---|---|---|
| `POST /auth/login` | 10 req | 1 minuto por IP |
| `POST /auth/refresh` | 20 req | 1 minuto por IP |
| `POST /import/csv` | 5 req | 1 hora por usuário |
| `POST /sync/*` | 10 req | 1 hora por usuário |
| Demais endpoints | 100 req | 1 minuto por usuário |

Implementar com middleware FastAPI + contador em `ICache`.

---

## Bearer Token na API

```
Header obrigatório em todos os endpoints autenticados:
Authorization: Bearer <access_token>

Ausente → 401 Unauthorized
Expirado → 401 com code AUTH_TOKEN_EXPIRED
Inválido → 401 com code AUTH_TOKEN_INVALID
```

---

## Segurança dos Providers

### Pierre Finance
- API Key via header `Authorization: Bearer sk-...`
- Chave lida de `ISecrets.get("PIERRE_API_KEY")`
- **Nunca** exposta em logs (usar masking: `sk-****`)
- **Nunca** retornada em DTOs de resposta da API interna

### MyProfit
- Credenciais (`MYPROFIT_USERNAME`, `MYPROFIT_PASSWORD`) usadas **uma vez** para autenticar
- Sessão (cookies) armazenada de forma segura — nunca em texto plano no banco
- 2FA **nunca** é bypassado — fluxo manual via UI se necessário
- Senha **nunca** armazenada no banco — apenas no `.env` para automação inicial

---

## Headers de Segurança (API)

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

---

## Auditoria de Segurança

- Toda tentativa de login (sucesso ou falha) deve ser logada com IP, timestamp e resultado
- Tokens revogados devem ser registrados com motivo
- Acessos a endpoints administrativos devem ser logados
