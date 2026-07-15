# Frontend Integration Guide

Este manual estabelece as diretrizes e boas práticas de engenharia de UI para consumir a API FINANALYTICS V3.

## Padrão de Fetch e Caching
- **Recomendação Principal**: Utilize bibliotecas de Server State, como `SWR`, `React Query (TanStack)` ou `Apollo Client`.
- **Cache Local**: Como o cálculo do portfólio pode ser intensivo na Engine in-memory, configure um `staleTime` conservador (Ex: 1 minuto para Dashboard).
- **SSR / SSG**: Como os dados são estritamente dinâmicos do investidor, Next.js deve focar em SSR (Server Side Rendering) protegendo as chaves de API, ou CSR (Client-Side Rendering) com Skeleton Loaders.

## Ordem das Chamadas
Para maximizar a Perceived Performance (Performance Percebida):
1. **Initial Load**: O Frontend dispara `GET /api/v1/investments/dashboard`. Com uma requisição, todas as 4 áreas (Resumo, Alocação, Performance e Risco) são carregadas.
2. **Lazy Loading**: Caso o usuário abra a aba de Posições Detalhadas, efetuar a chamada separada para `GET /api/v1/investments/positions`. Esta rota é paginada!
3. **Página de Importação**: Dispara o Upload via POST e assim que concluído, invalida o cache do Dashboard para provocar um `Re-fetch` reativo, atualizando os números na tela automaticamente.

## Tratamento de Loading (UX)
- Use **Skeleton Loaders** nas caixas de Resumo Financeiro, enquanto `SWR` ou `React Query` carregam o endpoint do Dashboard.
- Não utilize travamento de tela bloqueante.

## Tratamento de Erro e Retry
- Intercepte respostas Globais via Axios Interceptors (ou Fetch customizado).
- **Código 401/403**: Force um logout imediato ou refresh do JWT.
- **Código 400/422**: Formate a mensagem de erro do array do FastAPI e injete no form do usuário (Toast Error).
- **Código 500**: Ative política de **Retry com Backoff Exponencial** (ex: React Query retry = 3).
- Sempre emita Toast Notifications ao usuário. Nunca deixe um erro silencioso no console.

## Manipulação de Valores Monetários
- Todos os campos financeiros (`current_wealth`, `twr`) trafegam como Float genérico (`Decimal` nativo serializado) no JSON. No JavaScript, eles perdem precisão intrínseca na vírgula flutuante. Utilize uma biblioteca formatadora local (`Intl.NumberFormat('pt-BR')`) estritamente apenas no momento de exibição. Nunca modifique o estado bruto do React com strings formatadas.
