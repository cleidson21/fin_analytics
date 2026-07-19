
> [!IMPORTANT]
> A pasta docs/ é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela. Toda nova implementação deve ler os documentos existentes em docs/, atualizá-los quando necessário e registrar decisões arquiteturais por meio de ADRs antes de prosseguir.

# AI Engine

O Gemini é utilizado **apenas para exceções**.
Fluxo: Regras -> Encontrou? -> SIM (Salva) / NÃO (Gemini -> Usuário -> Regra).
