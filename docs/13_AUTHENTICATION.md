# Authentication Architecture

## Visão Geral
A autenticação do sistema (Fase 2) cobrirá usuários internos (FIN Analytics).
As autenticações de Integrações cobrem os provedores.

## Integrações
- **Pierre**: Baseada em Bearer Token e API Keys.
- **MyProfit**: Baseada em Sessão de Cookies com 2FA interativo. O sistema armazena apenas a sessão ativa (MyProfitAuth), solicitando o 2FA via frontend quando a sessão expirar.
