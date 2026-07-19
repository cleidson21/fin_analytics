> [!IMPORTANT]
> A pasta docs/ é a única fonte oficial de documentação do projeto.

# Códigos de Erro (Pierre Finance)

Os códigos mapeados e retornados pelo servidor seguem os padrões REST [CONFIRMADO]:
- 400: Bad Request (Parâmetros inválidos)
- 401: Unauthorized (Token ausente ou revogado)
- 403: Forbidden (Escopo insuficiente para a chave)
- 429: Too Many Requests (Rate limit excedido)
- 500: Internal Server Error
