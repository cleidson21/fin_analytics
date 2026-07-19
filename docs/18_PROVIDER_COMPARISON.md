> [!IMPORTANT]
> A pasta docs/ é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela. Toda nova implementação deve ler os documentos existentes em docs/, atualizá-los quando necessário e registrar decisões arquiteturais por meio de ADRs antes de prosseguir.

# Matriz de Integrações e Comparação

| Recurso | Pierre | MyProfit | Observações |
|---------|--------|----------|-------------|
| **Transações** | [PENDENTE] | [INFERIDO] | Pierre é o core bank |
| **REST** | [CONFIRMADO] | ✗ | Pierre REST responde 403 Forbidden com chave atual |
| **MCP** | [VALIDADO] | ✗ | Pierre MCP validado com sucesso via script local |
| **Bearer** | [VALIDADO] | ✗ | Pierre exige header Authorization |
| **Cookies** | ✗ | [CONFIRMADO] | Requisito do web scraper MyProfit |

*(Algumas seções foram omitidas por brevidade, veja referências completas em 16 e 17).*
