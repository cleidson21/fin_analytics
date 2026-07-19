> [!IMPORTANT]
> A pasta docs/ é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela. Toda nova implementação deve ler os documentos existentes em docs/, atualizá-los quando necessário e registrar decisões arquiteturais por meio de ADRs antes de prosseguir.

# Sprint P0: Provider Discovery

Este documento registra os resultados da Sprint P0 de Discovery das APIs e integrações (Pierre e MyProfit).

## Pierre Finance
- **Acesso REST API:** [CONFIRMADO] Conectividade estabelecida. O servidor responde, porém retornou Erro 403 (Forbidden) nos endpoints testados (/api/v1/health), indicando proteção ativa.
- **Acesso MCP:** [VALIDADO] Conexão estabelecida com sucesso. O script de inicialização exportou a chave e o proxy STDIO para o MCP foi criado sem erros.
- **Status:** O ambiente de infraestrutura foi totalmente corrigido. A documentação dos endpoints exatos ainda depende do handshake do MCP (que agora está funcionando).

## MyProfit
- **Acesso Oficial:** [CONFIRMADO] Não existe API REST pública documentada pelo fornecedor.
- **Acesso Scraping/Session:** [CONFIRMADO] A integração dependerá de scraping interativo simulando um usuário. A sessão será armazenada via cookies.
