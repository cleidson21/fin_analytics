# Canonical Model

O Modelo Canônico é o contrato absoluto entre os Connectors (Providers) e o Domínio.

## Entidades
Todo Provider obrigatoriamente converte seus dados proprietários nas seguintes estruturas imutáveis antes de enviar ao Domínio:
- **Transaction**
- **Asset**
- **Position**
- **Dividend**
- **Institution**
- **Portfolio**
- **Category**
- **Currency**
- **Provider**

Nenhuma tela ou regra de negócio consome objetos originais da Pierre ou MyProfit. O Domínio conhece apenas o Modelo Canônico.
