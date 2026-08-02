# Integrations Architecture

## Visão Geral
Toda integração externa atua apenas como um adaptador (Provider) que consome dados de uma fonte e os converte no Canonical Model do sistema. Nenhuma integração dita o formato do Domínio.

## Pierre Finance
A Pierre atua via REST API (e opcionalmente MCP). Base URL: `https://www.pierre.finance`.
- **Recursos Confirmados [VALIDADO — OpenAPI real]**:
  - Autenticação via API Key/Bearer (`Authorization: Bearer sk-...`).
  - Contas, Cartões de crédito, Transações, Saldos, Parcelamentos.
  - Spending Limits, Payment Reminders, Analytics de categorias.
  - Open Finance connection flow (fluxo de consentimento).
  - Paginação e Rate Limits estritos (429 Too Many Requests).
  - Erros padronizados (400, 401, 403, 404, 429, 500).
- **Recursos NÃO existentes [CONFIRMADO — ADR-009]**:
  - ❌ Webhooks (não existem)
  - ❌ Investimentos, Posições, Dividendos (não cobertos pela Pierre)
  - ❌ Refresh Token automatizado (token fixo via API Key)

## MyProfit
O MyProfit atua via automação de Sessão, pois não provê API REST pública.
- **Fluxo de Autenticação**: Login + Senha -> Solicita 2FA -> Obtém Cookies -> Salva Sessão.
- **Regras**:
  - O código 2FA NUNCA é armazenado.
  - Não há bypass automatizado do 2FA.
  - A sessão é persistida (cookies) e renovada quando necessário.
