# OpenAPI & REST Guidelines

## 1. Padrão REST e Versionamento
- Todas as rotas baseadas em recursos devem usar substantivos no plural (ex: `/api/v1/investments/positions`).
- O versionamento é feito na URL: `/api/v1/...`
- Ações imutáveis que fogem do CRUD padrão devem ser verbos, ou sub-recursos (ex: `/import/cei` via `POST`).

## 2. Padrão de Requisição
- **GET**: Consulta de dados. Sem side-effects. Deve usar Query Params para paginação e filtros.
- **POST**: Criação de recursos ou engatilhamento de processos pesados (como imports).
- **PUT**: Atualização completa de recurso (substituição).
- **PATCH**: Atualização parcial de recurso.
- **DELETE**: Exclusão de recurso.

## 3. Paginação, Filtros e Ordenação
- Parâmetros padrão: `page` (default: 1), `size` (default: 50).
- Ordenação: `sort_by=campo` e `sort_order=asc|desc`.
- Retorno de coleções paginadas deve usar um envelopamento (Envelope) contendo `items` e `meta` (com paginação).

## 4. Nomenclatura e Convenções
- Todas as chaves JSON (campos DTO) devem seguir `snake_case`.
- Datas devem usar `ISO 8601` (`YYYY-MM-DD` ou `YYYY-MM-DDTHH:MM:SSZ`).
- Valores monetários ou decimais devem ser expostos como string ou number mas tipados internamente como `Decimal`.

## 5. Swagger e OpenAPI
- Todos os endpoints devem possuir `response_model`, `summary` (curto), e `description` (longo).
- Erros esperados (ex: 404, 400, 422) devem estar documentados no dict `responses` do decorator do FastAPI.
- Incluir `tags` agrupadoras por domínio.
