> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# Value Objects do Domínio (FIN Analytics)

Value Objects são imutáveis e sem identidade própria. Validam-se na criação.

---

## Money

**Finalidade:** Representar um valor monetário com sua moeda.

| Campo | Tipo | Descrição |
|---|---|---|
| `amount` | Decimal(12,4) | Valor numérico |
| `currency` | CurrencyCode | ISO 4217 (BRL, USD) |

**Regras:**
- Não pode ser negativo em contextos de `Position.current_value`.
- Em `Transaction.amount`, sempre positivo — a direção é `MovementType`.
- Operações entre moedas diferentes exigem conversão explícita.
- Nunca utilizar `float` — sempre `Decimal` com precisão configurada.

**Exemplos:**
```
Money(amount=150.00, currency="BRL")
Money(amount=0.01, currency="USD")
```

---

## Percentage

**Finalidade:** Representar um percentual com precisão.

| Campo | Tipo | Descrição |
|---|---|---|
| `value` | Decimal(8,4) | Valor em percentual (ex: 12.63 = 12,63%) |

**Regras:**
- Intervalo: -100.0000 a qualquer positivo (ganhos ilimitados).
- Armazenar como percentual puro, NÃO como decimal (0.1263) — usar `12.63`.

---

## Quantity

**Finalidade:** Quantidade de cotas, ações ou unidades de ativo.

| Campo | Tipo | Descrição |
|---|---|---|
| `value` | Decimal(14,6) | Quantidade com 6 casas decimais |

**Regras:**
- Nunca negativo.
- Para BTC e cripto, 8 casas decimais podem ser necessárias — ampliar se necessário.

---

## Ticker

**Finalidade:** Código único de um ativo financeiro em bolsa.

| Campo | Tipo | Descrição |
|---|---|---|
| `symbol` | string | Código do ativo |
| `exchange` | string | Bolsa (B3, NYSE, NASDAQ) |

**Regras:**
- B3: uppercase, 4-6 caracteres alfanuméricos (ex: `PETR4`, `HGLG11`).
- US: uppercase, 1-5 letras (ex: `AAPL`, `MSFT`).
- Crypto: uppercase, 2-10 chars (ex: `BTC`, `ETH`).
- Normalizar sempre para uppercase antes de armazenar.

**Exemplos:**
```
Ticker(symbol="PETR4", exchange="B3")
Ticker(symbol="AAPL", exchange="NASDAQ")
```

---

## CurrencyCode

**Finalidade:** Código ISO 4217 de moeda.

**Regras:**
- Sempre 3 letras uppercase.
- Validar contra lista de moedas suportadas na tabela `Currency`.
- Aceitos: BRL, USD, EUR, GBP, BTC, ETH, USDT.

---

## AccountNumber

**Finalidade:** Número de conta bancária.

| Campo | Tipo | Descrição |
|---|---|---|
| `number` | string | Número da conta (normalizado) |
| `agency` | string | Agência bancária |
| `bank_code` | string | Código ISPB/COMPE |

**Regras:**
- Normalizar: remover hífen, zeros à esquerda conforme banco.
- Nunca expor em logs.

---

## DateRange

**Finalidade:** Intervalo de datas para filtros e consultas.

| Campo | Tipo | Descrição |
|---|---|---|
| `start` | date | Data início (inclusive) |
| `end` | date | Data fim (inclusive) |

**Regras:**
- `start` deve ser anterior ou igual a `end`.
- Máximo de 365 dias por consulta (limitação de rate limit dos Providers).

---

## CPF / CNPJ

**Finalidade:** Documento fiscal brasileiro.

**Regras CPF:**
- 11 dígitos numéricos.
- Validar dígitos verificadores.
- Armazenar somente dígitos (sem máscara).

**Regras CNPJ:**
- 14 dígitos numéricos.
- Validar dígitos verificadores.
- Armazenar somente dígitos.
