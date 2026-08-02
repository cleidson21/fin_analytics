> [!IMPORTANT]
> A pasta docs/ é a única fonte oficial de documentação do projeto.

# Rate Limits (Pierre Finance)

- **Existe Rate Limit?** [CONFIRMADO]
A API retorna 429 Too Many Requests quando excedida a capacidade por IP ou Token, exigindo *backoff* no consumo de transações de longo alcance.
