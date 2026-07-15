# Response Patterns

A consolidação da camada de API do FINANALYTICS define que todas as requisições, sem exceção, obedecem aos seguintes padrões estritos.

## 1. Single Resource Pattern
Rotas que buscam um elemento único (GET por ID) retornam diretamente o DTO que as representa. Se der erro, joga o 404 catalogado.
Exemplo:
```json
{
  "id": "123",
  "nome": "Dado único",
  "valor": 12.5
}
```

## 2. Collections Pattern (Arrays)
Rotas que devolvem listas retornam o array list de DTOs, ou envelopados se houver paginação.
Para simplificar (MVP da Sprint), nós retornamos arrays de JSON diretos em listas não-paginadas, com ResponseModel `List[DTO]`.
Exemplo:
```json
[
  { "id": "1", "nome": "Item 1" },
  { "id": "2", "nome": "Item 2" }
]
```

## 3. Success / Error Responses Simples
Para deleções ou mutações, em vez de dicionários soltos como `{"message": "Deletado"}`, usamos um DTO `MessageResponse` padrão:
```python
class MessageResponse(BaseModel):
    message: str
```
Exemplo:
```json
{
  "message": "Operação realizada com sucesso"
}
```

## 4. Tipos e Contratos Universais (DTOs)
- Valores Financeiros: Sempre tipo `Decimal` convertido para numérico exato e enviado como `number` ou `string` para não perder precisão no JavaScript.
- Identificadores: Strings de Hashes Hexadecimais ou UUIDs padrão.
- Data e Tempo: Sempre serializados em formato ISO 8601 (`YYYY-MM-DD` ou `YYYY-MM-DDTHH:MM:SSZ`).
- Campos vazios: Retornam `null` no JSON (`Optional` no Pydantic, devidamente preenchido se não definido default factory).
