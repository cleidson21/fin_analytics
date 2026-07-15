# API Error Catalog

Catálogo de erros HTTP e exceções mapeadas no contrato da API.

## 400 Bad Request
- **Código Interno**: `ERR_BAD_REQUEST`
- **Descrição**: Requisição malformada. Faltam parâmetros, quebras de validação de payload ou regras de negócio síncronas.
- **Origem**: FastAPI Dependency Injection, Pydantic, ou Validações de Domínio.
- **Como reproduzir**: Enviar um payload JSON inválido, ou omitir parâmetros requeridos.
- **Como corrigir**: Checar schema via OpenAPI Swagger e seguir regras de campos opcionais/obrigatórios.

## 401 Unauthorized
- **Código Interno**: `ERR_UNAUTHORIZED`
- **Descrição**: Autenticação ausente, token inválido ou expirado.
- **Origem**: Security Layer (Bearer Tokens).
- **Como reproduzir**: Não enviar cabeçalho `Authorization: Bearer <token>`.
- **Como corrigir**: Realizar login e adquirir novo JWT token.

## 403 Forbidden
- **Código Interno**: `ERR_FORBIDDEN`
- **Descrição**: O usuário está autenticado, mas não tem permissão de acessar o recurso ou tenant.
- **Origem**: Authorization / RBAC.
- **Como reproduzir**: Acessar log de importação de outro `user_id`.
- **Como corrigir**: Checar os papéis ou acesso do usuário logado.

## 404 Not Found
- **Código Interno**: `ERR_NOT_FOUND`
- **Descrição**: O recurso solicitado não existe na base de dados (Ex: Log_id não encontrado).
- **Origem**: Repositories e Services ao buscar IDs específicos.
- **Como reproduzir**: Consultar um ImportLog que não existe na base, ex: `/api/v1/investments/import/uuid-inexistente`.
- **Como corrigir**: Garantir que o recurso foi listado previamente em coleções.

## 409 Conflict
- **Código Interno**: `ERR_CONFLICT`
- **Descrição**: Conflito de regras de negócio ou de estado (ex: duplicidade de importação já processada).
- **Origem**: Application Services.
- **Como reproduzir**: Tentar deletar um recurso travado ou importar duas vezes o mesmo Idempotency Hash forçado.
- **Como corrigir**: Resolver a restrição do estado.

## 422 Unprocessable Entity
- **Código Interno**: `ERR_VALIDATION`
- **Descrição**: Validação Pydantic falhou nos tipos de dados.
- **Origem**: FastAPI.
- **Como reproduzir**: Mandar "A" num campo do tipo `Decimal`.
- **Como corrigir**: Adequar os tipos do frontend ao DTO da rota.

## 500 Internal Server Error
- **Código Interno**: `ERR_INTERNAL_SERVER`
- **Descrição**: Falha sistêmica, crash de Engine, ou erro de BD não tratado.
- **Origem**: Qualquer camada não mapeada.
- **Como reproduzir**: Bug.
- **Como corrigir**: Reportar no log do Sentry/Backend e consertar a exception stacktrace.
