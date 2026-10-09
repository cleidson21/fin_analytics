# External Series Registry

**Phase:** `10.R3-B`

**Status:** `CONTRACT APPROVED / LOCKED`

**Implementation status:** `NOT STARTED / DOCUMENTAL REGISTRY LOCKED`

This registry is the locked source allowlist for the first R3 increment. It
does not authorize provider code, database writes, valuation, smart prefills,
or engine changes. Official metadata and identities were revalidated on
2026-10-09.

## 1. Registry rules

- A registry key fixes provider, native identifier, concept, semantic class,
  unit, frequency, scope, source, license, and permitted purpose.
- Provider payload text cannot redefine these semantics at runtime.
- Every numeric value is parsed directly from its lexical string to `Decimal`.
- Every series declares provider decimal places and one fixed normalization
  scale. Canonical persistence is exact fixed-scale text; no float or SQLite
  numeric affinity is financial authority.
- Daily `% p.d.` and annual `% p.y.` values remain in their original units.
  R3 does not annualize, deannualize, accumulate, or compound them.
- Monthly IPCA is monthly percentage variation, not an annual rate and not an
  index level.
- An omitted date is absence, not zero.
- A series is not callable unless its registry status is `MVP_ELIGIBLE` and the
  contract has been approved.

## 2. Locked MVP catalog

| Registry key | Provider ID | Official concept | Frequency | Unit | Scope | Semantic class | Contract status |
|---|---:|---|---|---|---|---|---|
| `BCB_SGS_SELIC_TARGET` | 432 | Interest rate - Selic target | daily | `% p.y.` | BR | `EXTERNAL_OBSERVATION` | `MVP_ELIGIBLE` |
| `BCB_SGS_SELIC_EFFECTIVE` | 11 | Interest rate - Selic | daily | `% p.d.` | BR | `EXTERNAL_OBSERVATION` | `MVP_ELIGIBLE` |
| `BCB_SGS_CDI` | 12 | Interest rate - CDI | daily | `% p.d.` | BR | `EXTERNAL_OBSERVATION` | `MVP_ELIGIBLE` |
| `BCB_SGS_IPCA_MONTHLY` | 433 | Broad National Consumer Price Index (IPCA) | monthly | monthly `%` variation | BR | `EXTERNAL_OBSERVATION` | `MVP_ELIGIBLE` |
| `BCB_SGS_USD_SELL` | 1 | Free-market United States dollar selling exchange rate | daily | current monetary unit per USD | BR FX reference | `EXTERNAL_OBSERVATION` | `MVP_ELIGIBLE_REFERENCE_ONLY` |

The English labels above reproduce the official SGS metadata presentation. API
and product labels may use governed Portuguese human labels without changing
the official concept.

## 3. Series details and official evidence

### 3.1 `BCB_SGS_SELIC_TARGET` — SGS 432

| Attribute | Contract value |
|---|---|
| Provider | Banco Central do Brasil / SGS |
| Official full name | Interest rate - Selic target |
| Short name | Selic target |
| Native identifier | `432` |
| Frequency | daily |
| Unit | `% p.y.` (`% a.a.` in Portuguese presentation) |
| Source named by SGS | Copom |
| License | Open Data Commons Open Database License (ODbL), per BCB Open Data catalog |
| Historical coverage start | 1999-03-05 |
| Decimal places declared by SGS | 2 |
| Economic meaning | Current target rate defined by Copom, repeated on daily reference dates by the series |
| Currency | not applicable |
| MVP eligibility | yes, as an external reference only |
| Forbidden interpretation | effective overnight rate, daily percentage rate, automatic expected return |

Official evidence:

- [BCB Open Data dataset for SGS 432](https://dadosabertos.bcb.gov.br/dataset/432-taxa-de-juros---meta-selic-definida-pelo-copom)
- [SGS metadata for series 432](https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.do?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=432)
- Endpoint pattern: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados`

### 3.2 `BCB_SGS_SELIC_EFFECTIVE` — SGS 11

| Attribute | Contract value |
|---|---|
| Provider | Banco Central do Brasil / SGS |
| Official full name | Interest rate - Selic |
| Short name | Selic |
| Native identifier | `11` |
| Frequency | daily |
| Unit | `% p.d.` (`% a.d.` in Portuguese presentation) |
| Source named by SGS | BCB-Demab |
| License | Open Data Commons Open Database License (ODbL), per BCB Open Data catalog |
| Historical coverage start | 1986-06-04 |
| Decimal places declared by SGS | 6 |
| Economic meaning | Effective Selic daily rate in the provider's original daily unit |
| Currency | not applicable |
| MVP eligibility | yes, as an external observation |
| Forbidden interpretation | Selic target, annual rate, accumulated return, automatic Planning/FIRE return |

Official evidence:

- [BCB Open Data dataset for SGS 11](https://dadosabertos.bcb.gov.br/pt_BR/dataset/11-taxa-de-juros---selic)
- [SGS metadata for series 11](https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.do?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=11)
- Endpoint pattern: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados`

### 3.3 `BCB_SGS_CDI` — SGS 12

| Attribute | Contract value |
|---|---|
| Provider | Banco Central do Brasil / SGS |
| Official full name | Interest rate - CDI |
| Short name | CDI |
| Native identifier | `12` |
| Frequency | daily |
| Unit | `% p.d.` (`% a.d.` in Portuguese presentation) |
| Source named by SGS | Cetip |
| License | Open Data Commons Open Database License (ODbL), per BCB Open Data catalog |
| Historical coverage start | 1986-03-06 |
| Decimal places declared by SGS | 6 |
| Economic meaning | CDI daily rate in the provider's original daily unit |
| Currency | not applicable |
| MVP eligibility | yes, as an external observation |
| Forbidden interpretation | monthly accumulated CDI, annual rate, portfolio performance, automatic expected return |

Official evidence:

- [SGS metadata for series 12](https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.do?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=12)
- Endpoint pattern: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados`

The historical research file `audits/EXTERNAL_DATA_ECOSYSTEM.md` listed SGS
4389 as “CDI”. That code is not used by this registry: the official metadata
revalidation establishes SGS 12 as the daily `% p.d.` CDI concept requested by
R3. SGS 4389 is a different accumulated monthly series and is not an alias.

### 3.4 `BCB_SGS_IPCA_MONTHLY` — SGS 433

| Attribute | Contract value |
|---|---|
| Provider | Banco Central do Brasil / SGS |
| Official full name | Broad National Consumer Price Index (IPCA) |
| Short name | Broad National Consumer Price Index (IPCA) |
| Native identifier | `433` |
| Frequency | monthly |
| Unit | monthly percentage variation |
| Source named by SGS | IBGE |
| License | Open Data Commons Open Database License (ODbL), per BCB Open Data catalog |
| Historical coverage start | 1980-01-01 |
| Decimal places declared by SGS | 2 |
| Economic meaning | IPCA percentage variation for the economic reference month |
| Currency | not applicable |
| MVP eligibility | yes, as an external observation |
| Forbidden interpretation | annual inflation, index level, Focus expectation, automatic Planning/FIRE inflation |

Official evidence:

- [SGS metadata for series 433](https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.do?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=433)
- Endpoint pattern: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados`

The provider may encode a monthly observation as the first civil day of the
month. Normalization must preserve the whole economic month rather than treat
that date as a daily observation.

### 3.5 `BCB_SGS_USD_SELL` — SGS 1

| Attribute | Contract value |
|---|---|
| Provider | Banco Central do Brasil / SGS |
| Official full name | Taxa de câmbio - Livre - Dólar americano (venda) - diário |
| Short name | Commercial exchange rate |
| Native identifier | `1` |
| Frequency | daily |
| Unit | current monetary unit per US dollar |
| Normalized currency pair | `BRL/USD` for observations in the current-real period |
| Source named by SGS | Sisbacen PTAX800 |
| License | Open Data Commons Open Database License (ODbL), per BCB Open Data catalog |
| Historical coverage start | 1984-11-28 |
| Locked normalized MVP floor | 1994-07-01; earlier monetary regimes are excluded pending a separate currency-regime contract |
| Decimal places declared by SGS | 4 |
| Economic meaning | Official SGS free-market USD selling exchange-rate series |
| MVP eligibility | yes, reference-only |
| Forbidden interpretation | certified portfolio FX, historical valuation converter, universal “PTAX” alias |

Official evidence:

- [BCB Open Data dataset for SGS 1](https://dadosabertos.bcb.gov.br/dataset/1-taxa-de-cambio---livre---dolar-americano-venda---diario)
- [SGS metadata for series 1](https://www3.bcb.gov.br/sgspub/consultarmetadados/consultarMetadadosSeries.do?method=consultarMetadadosSeriesInternet&hdOidSerieSelecionada=1)
- Endpoint pattern: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados`

The source field references `PTAX800`, but the registry does not rename SGS 1
to “PTAX”. The series keeps its official full concept until a separate contract
proves that a narrower PTAX label is semantically safe for the intended use.
The historical unit also spans prior Brazilian monetary units; R3 must not
normalize pre-real observations to `BRL/USD` without a separately approved
currency-regime treatment.

## 4. Exact value representation

The provider-declared decimal places and locked normalization scales are:

| Registry key | Provider decimal places | Normalization scale | Canonical storage example |
|---|---:|---:|---|
| `BCB_SGS_SELIC_TARGET` | 2 | 2 | `13.65` |
| `BCB_SGS_SELIC_EFFECTIVE` | 6 | 6 | `0.052788` |
| `BCB_SGS_CDI` | 6 | 6 | `0.052788` |
| `BCB_SGS_IPCA_MONTHLY` | 2 | 2 | `0.42` |
| `BCB_SGS_USD_SELL` | 4 | 4 | `5.4321` |

These scales preserve provider metadata; they do not convert units. The
adapter parses accepted provider text directly to Python `Decimal`, rejects
float/JSON-number transit and non-zero fractional digits beyond the registry
scale, and may only add trailing zeroes. It does not round. The accepted
provider lexical form is retained separately from the normalized canonical
text.

Canonical fixed-scale text is exact but is not numerically sortable by ordinary
SQLite text collation. Repositories must not use SQL lexical order, range
predicates, casts, aggregates, or arithmetic on the value field. Numeric
comparison and ordering happen only after exact `Decimal` conversion. A future
need for numeric database filtering requires a separately approved storage
contract.

## 5. SGS API and interval policy

### 5.1 Official constraints

For daily series, the BCB Open Data portal states that, beginning 2025-03-26:

- JSON and CSV historical queries require filters;
- a date interval is limited to ten years;
- a request outside that limit returns an error.

The JSON resource accepts `dataInicial` and `dataFinal` in `dd/MM/yyyy` and
returns observation objects with date and value text. R3 treats both bounds as
inclusive and locks that behavior with fixtures before live activation.

### 5.2 Deterministic partitioning

Requests longer than ten years are partitioned into closed, non-overlapping
civil-date intervals. The next interval starts one day after the prior interval
ends. Each interval must independently satisfy the provider maximum.

The adapter must:

- preserve the original requested boundary;
- merge chunks in ascending economic-date order;
- reject duplicates with conflicting values as a typed provider inconsistency;
- accept weekends, holidays, and other missing dates as absence;
- return `PARTIAL` with explicit missing intervals when only some chunks
  succeed;
- never retry the entire historical range when only one chunk failed.

The endpoint exposes no pagination token in this contract. Temporal
partitioning is the safe pagination mechanism.

## 6. Locked per-series operating policy

These operational values are `APPROVED BY USER / LOCKED`; they govern call
suppression, not economic meaning.

| Registry key | Refresh interval | Evidence sufficient for `CURRENT` | Absence that does not prove `STALE` |
|---|---:|---|---|
| `BCB_SGS_SELIC_TARGET` | 6 hours | successful complete query through `as_of` identifies the provider-returned head | unchanged target or non-observation date |
| `BCB_SGS_SELIC_EFFECTIVE` | 6 hours | successful complete query through `as_of` identifies the provider-returned latest daily observation | weekend/holiday gap |
| `BCB_SGS_CDI` | 6 hours | successful complete query through `as_of` identifies the provider-returned latest daily observation | weekend/holiday gap |
| `BCB_SGS_IPCA_MONTHLY` | 24 hours | successful complete query through `as_of` identifies the provider-returned latest published economic month | no observation for the current calendar month |
| `BCB_SGS_USD_SELL` | 6 hours | successful complete query through `as_of` identifies the provider-returned latest daily observation | weekend/holiday gap |

The refresh intervals only decide when acquisition is due. They do not prove
economic freshness. A failed refresh changes acquisition health, not
automatically freshness. An eligible last-known-good remains an available
historical reference; its freshness is `CURRENT`, `STALE`, or `UNKNOWN` only
under the evidence rules above. With insufficient evidence the result is
`UNKNOWN`. No policy asserts an undocumented publication calendar.

## 7. License and attribution

The BCB Open Data catalog declares its SGS datasets under the Open Data Commons
Open Database License (ODbL). Future implementation must:

- preserve Banco Central do Brasil/SGS attribution and the source URL;
- retain the registry license identifier with stored observations;
- revalidate terms before production release;
- avoid presenting FINANALYTICS as the producer of BCB/IBGE/Cetip observations;
- keep provider-specific restrictions out of generic financial authority.

No conclusion in this registry grants rights beyond the provider's published
terms.

## 8. Deferred registry candidates

| Candidate | Semantic class | Status | Reason |
|---|---|---|---|
| BCB Focus expectations | `EXTERNAL_EXPECTATION` | `CONTRACT_READY / IMPLEMENTATION_DEFERRED / NOT IMPLEMENTED` | Different temporal/horizon/statistical model; not needed for first observation increment |
| IBGE/SIDRA details | `EXTERNAL_OBSERVATION` | `DEFERRED` | SGS 433 covers MVP headline IPCA; component detail needs a separate source contract |
| CVM/brFinance fundamentals | `EXTERNAL_OBSERVATION` or derived facts, pending contract | `DEFERRED` | Portfolio Intelligence authority and provider-maintenance questions unresolved |
| News/RSS | external untrusted content, not a numeric observation | `DEFERRED` | Belongs to a separate content and injection-safety contract |
| yfinance market observations | pending certification | `DEFERRED TO R3-G` | Existing boundary must be remediated under ADR-006; not automatically authoritative |
| SGS 4389 | monthly accumulated CDI series | `EXCLUDED FROM MVP` | Different concept/unit from daily CDI SGS 12 |

## 9. Focus contract envelope

The following fields are reserved conceptually for a later Focus adapter:

- provider and indicator;
- collection/publication date;
- reference date or horizon;
- expectation statistic, such as median, only when selected explicitly;
- exact Decimal value and unit;
- respondent/base metadata when officially supplied and needed;
- retrieved/known-from timestamps;
- availability and revision metadata.

Focus implementation must use `EXTERNAL_EXPECTATION`, never
`EXTERNAL_OBSERVATION`. It is not part of the R3 MVP implementation sequence
until a separate approval activates the deferred task.

Official discovery references:

- [BCB Open Data — Market Expectations](https://dadosabertos.bcb.gov.br/dataset/expectativas-mercado)
- [BCB Olinda Expectations service documentation](https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/documentacao)

## 10. Lock record

The user approved the following on 2026-10-09 after independent review:

1. the five-series allowlist;
2. SGS 1 reference-only treatment;
3. SGS 1 real-era ingestion floor and exclusion of earlier monetary regimes;
4. exclusion of SGS 4389 from the daily-CDI concept;
5. operational refresh intervals;
6. fixed normalization scales and canonical SQLite text storage;
7. independent refresh, economic freshness, and acquisition-health states;
8. Focus deferral;
9. ODbL attribution approach.

This registry is locked, but implementation is not started. It authorizes the
separately scoped R3-C executable-registry task; it does not itself authorize a
provider call, database write, valuation, frontend change, or engine input.
