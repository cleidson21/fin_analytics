> [!IMPORTANT]
> A pasta docs/ é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela. Toda nova implementação deve ler os documentos existentes em docs/, atualizá-los quando necessário e registrar decisões arquiteturais por meio de ADRs antes de prosseguir.

# Pierre Finance - Referência Técnica

**Data da Consulta:** 18 de Julho de 2026.
**Acesso:** [VALIDADO] MCP Operacional.

## Endpoint e Ambiente
- **REST:** [CONFIRMADO] Endpoints sob proteção estrita (Erro 403 Forbidden).
- **MCP:** [VALIDADO] Handshake STDIO e proxy conectam perfeitamente através de https://pierre.finance/mcp.

## Autenticação
- **Formato:** [VALIDADO] Authorization: Bearer <API_KEY>

> **Conclusão:** A infraestrutura de conexão está validada. O próximo passo será realizar o dump de ferramentas (Tools) do MCP para revelar os contratos REST finais.
