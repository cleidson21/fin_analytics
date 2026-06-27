# 5.5 Canonical Normalization

## Objetivo
## Objetivo
A maior e mais importante Engine do projeto. Ela consome a abstração `RawDocument` (gerada pelos Readers) e consolida os arrays brutos de qualquer origem (Nubank, Pierre, B3, MyProfit) numa estrutura universal padronizada. O Normalizer é puro processamento semântico de negócio.

## Estrutura (Canonical Financial Event)
Qualquer parser deve culminar neste modelo antes de tentar escrever no banco:
```json
{
  "source": "...",
  "type": "...",
  "date": "...",
  "description": "...",
  "amount": 0.0,
  "currency": "...",
  "asset": "...",
  "quantity": 0.0,
  "fees": 0.0,
  "account": "...",
  "credit_card": "...",
  "broker": "...",
  "external_hash": "...",
  "raw_data": {}
}
```

## Regras
Independentemente da origem (CSV, API, OCR), depois da etapa de Normalização, **todo o restante do sistema (Reconciliação, Governança e Banco) trabalha EXCLUSIVAMENTE com Canonical Events**. Nenhuma fonte externa escreve diretamente nas tabelas finais.
