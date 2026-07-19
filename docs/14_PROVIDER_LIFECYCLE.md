# Provider Lifecycle

## Ciclo de Vida do Connector
1. **Connector**: Interface de entrada.
2. **Authentication**: Resolve credenciais ou sessões (API Key, JWT, Cookies).
3. **Session/Client**: Mantém a conexão (httpx, requests).
4. **Mapper**: Transforma o payload original em Canonical Model.
5. **Canonical Model**: Representação pura da entidade (Asset, Transaction).
6. **Application**: Recebe o Canonical Model e orquestra.
7. **API / Frontend**: Consomem apenas o resultado do Domínio.
