
> [!IMPORTANT]
> A pasta docs/ é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela. Toda nova implementação deve ler os documentos existentes em docs/, atualizá-los quando necessário e registrar decisões arquiteturais por meio de ADRs antes de prosseguir.

# Architecture

A aplicação utiliza uma arquitetura Domain-Driven (Domain-Driven Design). O núcleo (Domínio) não depende de fontes de dados externas; ele define o contrato.
