# External Context Contract

**Phase:** `10.R3-B`

**Status:** `CONTRACT APPROVED / LOCKED / VERSIONED`

**Implementation status:** `R3-B.2 APPROVED / INDEPENDENTLY VERIFIED / LOCKED`;
R3-C `READY / NOT STARTED`; R3 runtime `NOT STARTED`

**Authority:** this contract derives from the approved R3-A audit, the accepted
Wealth OS architecture, the independently approved R3-B.1 remediation, and
accepted ADR-029. The user explicitly approved all ten material decisions on
2026-10-09. The user also explicitly approved the normative
`content_fingerprint_v1` amendment on 2026-10-09; independent delta review
approved it on 2026-10-10. Contract lock does not mean implementation
completion.

## 1. Purpose

R3 establishes governed, purpose-limited external economic references. It does
not create effective financial assumptions, certified portfolio values,
recommendations, AI behavior, or user-experience recomposition.

The canonical flow is:

```text
Provider
  -> Adapter
  -> Normalization and semantic classification
  -> Governed observation store
  -> Availability and freshness evaluation
  -> External reference context
  -> Purpose-limited consumer
```

No consumer may bypass this flow to call a provider, interpret provider units,
or query the observation store directly.

## 2. Decision vocabulary

This contract uses the following labels deliberately:

- `SUPPORTED BY OFFICIAL SOURCE`: verified against the provider's official
  metadata or documentation;
- `CONSISTENT WITH EXISTING CONTRACT`: follows an already accepted ADR or
  canonical owner;
- `APPROVED BY USER`: explicitly accepted on 2026-10-09;
- `PROPOSED`: a future design outside the ten decisions locked here;
- `REQUIRES USER APPROVAL`: a future material proposal not covered by this
  lock;
- `LOCKED`: already fixed by an accepted ADR or locked phase contract.

The ten decisions in section 18 are `APPROVED BY USER / LOCKED`. Future items
that still say `PROPOSED` or require a separate activation remain unlocked.

## 3. Scope

### 3.1 Locked MVP

The first operational increment is limited to official BCB/SGS observations in
the allowlisted registry:

- Selic target, SGS 432;
- effective Selic, SGS 11;
- CDI, SGS 12;
- IPCA monthly variation, SGS 433;
- USD/BRL selling exchange reference, SGS 1.

SGS 1 is a macro/reference observation only. R3 must not use it for portfolio
valuation, historical conversion, net-worth reconstruction, or replacement of
ADR-023 authority.

### 3.2 Contract-ready but deferred

BCB Focus expectations are modeled as `EXTERNAL_EXPECTATION`, but provider,
normalizer, persistence, and consumer implementation are deferred until a
separate approval. The contract must be able to represent collection date,
indicator, forecast horizon, statistic, unit, provider, availability, and
revision metadata without treating an expectation as an observation.

### 3.3 Out of scope

R3 does not implement:

- AI providers, prompts, tools, or orchestration (R4);
- Home, Goals, Planning, FIRE, Profile, or Settings recomposition (R6);
- smart prefills or automatic assumptions;
- recommendations or financial advice;
- user-specific data export to macro providers;
- live portfolio valuation or replacement of `portfolio_snapshots.patrimonio`;
- news, CVM fundamentals, IBGE/SIDRA detail, or a second yfinance integration
  in the initial MVP;
- public API or frontend behavior unless a later approved R3 task explicitly
  contracts one.

## 4. Semantic classes

The locked Smart Context taxonomy is reused, not rewritten:

- `EXTERNAL_OBSERVATION`: an observed external fact for an economic reference
  period, as delivered by an allowlisted provider;
- `EXTERNAL_EXPECTATION`: a forecast, survey result, or market expectation for
  an explicit future or target horizon.

An expectation is never normalized into an observation. Neither class is an
`ASSUMPTION`, `USER_OVERRIDE`, or governed internal fact.

## 5. Immutable observation model

The locked domain model is typed and immutable. The domain value is always a
Python `Decimal` constructed from validated lexical text. The persistence
representation is specified separately in section 8; a SQL type declaration
does not define the domain authority.

### 5.1 Required

| Field | Meaning |
|---|---|
| `provider` | Allowlisted provider identifier, initially `BCB_SGS` |
| `series_id` | Provider-native identifier, such as `432` |
| `series_concept` | Stable registry concept, never inferred from payload text |
| `semantic_class` | `EXTERNAL_OBSERVATION` or `EXTERNAL_EXPECTATION` |
| `value` | Exact Python `Decimal`; parsed from text with no float transit |
| `normalization_scale` | Fixed registry scale used by canonical value text |
| `unit` | Registry-owned semantic unit |
| `frequency` | Registry-owned economic frequency |
| `scope` | Geographic/market scope, initially `BR` |
| `reference_period_start` | Start of the economic period |
| `reference_period_end` | End of the economic period |
| `retrieved_at` | UTC timestamp of the provider response |
| `known_from` | UTC knowledge boundary of this committed event |
| `ingested_at` | UTC timestamp when persistence completed |
| `content_fingerprint_version` | Version of the immutable content-fingerprint formula, initially `1` |
| `content_fingerprint` | Deterministic digest of canonical semantic content; non-unique across non-consecutive historical events |
| `knowledge_sequence` | Monotonic event order inside one economic identity |
| `source_url` | Governed provider endpoint or metadata URL |
| `license_id` | Registry-owned license identifier |

### 5.2 Optional only when supplied or evidenced

| Field | Rule |
|---|---|
| `currency` | Required only when the registry proves the applicable currency; `BRL/USD` for SGS 1 only inside the approved real-era scope |
| `observed_at` | Provider event timestamp only when the source actually supplies one; it is not synthesized from a civil reference date |
| `published_at` | Present only when the provider supplies a reliable publication time |
| `provider_revision_id` | Present only when the provider supplies an official revision identifier |
| `revised_at` | Present only when the provider supplies a reliable revision time |
| `provider_decimal_places` | Present when official provider metadata declares decimal places; it is not inferred from one payload |
| `provider_value_text` | Bounded original lexical value for audit, never a raw payload dump |
| `supersedes_event_id` | Local link to the immediately prior knowledge event for the same economic identity |

The system must not invent `published_at`, `revised_at`, a revision identifier,
or a numeric quality/confidence score.

### 5.3 Status is evaluated, not financial value

Availability, economic freshness, and acquisition health are independent
dimensions:

- availability: `AVAILABLE`, `PARTIAL`, or `UNAVAILABLE`;
- freshness: `CURRENT`, `STALE`, or `UNKNOWN`.
- acquisition health: `HEALTHY`, `DEGRADED`, `FAILED`, or `UNKNOWN`.

Structured reason codes explain non-current or unavailable results. Absence is
never converted to numeric zero.

## 6. Temporal and bitemporal contract

R3 separates economic time from knowledge time.

### 6.1 Economic time

- `reference_period_start` and `reference_period_end` identify what period the
  value describes;
- a daily SGS observation uses the same civil date for start and end;
- a monthly SGS observation represents the civil month, even if the provider
  encodes its date as the first day of that month;
- provider dates are civil dates, not UTC timestamps.

### 6.2 Knowledge time

- `observed_at`, when supplied, records the provider event timestamp and does
  not replace the economic reference period;
- `retrieved_at` records, in UTC, when the complete provider response was
  received by the adapter;
- `ingested_at` is the UTC transaction timestamp assigned when a validated
  knowledge event is written to the observation store;
- `known_from` is the knowledge boundary of that committed event. It is set in
  the same transaction as `ingested_at`, is never earlier than `retrieved_at`,
  and becomes eligible only after that transaction commits;
- `published_at` and `revised_at` remain null when not supplied by the source.

For the initial SGS API, `known_from` is the successful local persistence time
of each accepted content transition. A rollback creates no knowledge event.
An older economic reference date does not backdate local knowledge. An
identical consecutive retransmission updates sync telemetry but does not create
another observation event or alter the existing event's `known_from`.

### 6.3 Consumer `as_of`

A version is eligible for a consumer query only when:

```text
reference_period_end <= consumer_as_of_date
AND known_from <= consumer_as_of_timestamp
```

If a value for August is first ingested in October, a replay as of September
must not see it. If a revised value is learned later, earlier `as_of` queries
must continue to resolve the version known at the requested time.

Resolution selects the event with the greatest `(known_from,
knowledge_sequence)` that is not later than `consumer_as_of`. The sequence is
the deterministic tie-breaker when transaction timestamps are equal.

`as_of` must be explicit at service boundaries. No provider, adapter,
repository, freshness policy, or context composer may call `date.today()` or
`datetime.now()` to manufacture a consumer boundary.

## 7. Identity, deduplication, and revisions

The economic identity is:

```text
(provider, series_id, reference_period_start, reference_period_end,
 semantic_class)
```

Three identities are distinct:

1. **Economic identity:** the tuple above; it answers which economic fact is
   being described.
2. **Content identity:** a deterministic SHA-256 `content_fingerprint` over
   canonical value text, normalization scale, unit, currency, scope, and other
   semantic content. It answers whether two payloads express the same value.
3. **Knowledge-event identity:** an opaque `observation_event_id` plus a
   monotonic `knowledge_sequence` and `known_from`. It records that the system
   learned a content transition at a specific time.

An official provider revision identifier is provenance; when present it is
stored, but it does not replace local knowledge-event identity.

Rules:

1. A consecutive retrieval whose content fingerprint equals the current head
   is an identical retransmission. It creates no knowledge event and may update
   only bounded series sync-state telemetry.
2. A changed content fingerprint creates a new immutable knowledge event; the
   prior event is not overwritten.
3. A reversion `A -> B -> A` creates three events. The third event may reuse
   A's content fingerprint, but has its own event ID, sequence, `known_from`,
   and supersedes link to B. Therefore content fingerprint is not unique over
   the full history.
4. Duplicates inside one provider response are coalesced only when their
   canonical content is identical. Conflicting duplicates are a typed provider
   inconsistency.
5. A missing period creates no numeric observation.
6. Historical resolution selects the latest eligible knowledge event, not the
   latest distinct content hash.

### 7.1 Normative `content_fingerprint_v1` amendment

`APPROVED BY USER / LOCKED`: content fingerprint version 1 closes the content
serialization gap identified at the start of R3-C without reopening any of the
ten material R3-B decisions. The hashing algorithm is:

```text
content_fingerprint_version = 1

validated = validate_against_registry(input)
normalized = normalize_decimal_and_period(validated)
canonical_json = canonical_json_v1(normalized)
hash_input = DOMAIN_PREFIX_V1 || UTF8(canonical_json)
digest = SHA256(hash_input)
content_fingerprint = "sha256:" || lowercase_hex(digest)
```

Validation against the executable series registry and normalization both occur
before hashing. Bytes from an invalid payload may have a mathematical SHA-256
digest, but that digest is never a valid domain content fingerprint.

The persisted and compared identity is the pair
`(content_fingerprint_version, content_fingerprint)`. A digest from another
version must not be compared as if it used the V1 formula.

### 7.2 Closed V1 payload

The canonical payload has exactly these eleven keys:

| Field | JSON type | Nullable |
|---|---|---|
| `provider` | string | no |
| `series_id` | string | no |
| `reference_period_start` | string | no |
| `reference_period_end` | string | no |
| `semantic_class` | string | no |
| `frequency` | string | no |
| `value_text` | string | no |
| `value_scale` | integer | no |
| `unit` | string | no |
| `currency` | string or null | yes |
| `scope` | string | no |

No required key may be omitted and no additional key is accepted. `currency`
is always present, including when its JSON value is `null`. Booleans are not
accepted as integers. Arrays, nested objects, and floats are prohibited.

The stable V1 identifiers are:

- provider: `BCB_SGS`;
- frequency: `DAILY` or `MONTHLY`;
- unit: `PERCENT_PER_YEAR`, `PERCENT_PER_DAY`,
  `PERCENT_MONTHLY_CHANGE`, or `BRL_PER_USD` as fixed by the registry series;
- scope: `BR`;
- currency: `BRL/USD` for SGS 1 in the approved real-era scope and JSON `null`
  for the other four MVP series;
- semantic class: `EXTERNAL_OBSERVATION` for all five SGS MVP series.

These values are stable identifiers, not editable labels. Unknown or
series-incompatible codes are rejected rather than silently normalized. Focus
is not part of the executable registry authorized by this amendment.

### 7.3 Decimal and period normalization

V1 uses the registry scales already locked by this contract:

| SGS series | `value_scale` |
|---:|---:|
| 432 | 2 |
| 11 | 6 |
| 12 | 6 |
| 433 | 2 |
| 1 | 4 |

Input is strict lexical text parsed directly to Python `Decimal`, never through
float. It permits no external whitespace, exponent, locale-dependent
separator, `NaN`, or infinity. Normalization adds trailing zeroes to the fixed
registry scale, converts negative zero to positive zero, and performs no
rounding. Non-zero digits beyond the registry scale are rejected. Therefore
`10.5` and `10.50` both normalize to `10.50`, while `-0.00` normalizes to
`0.00`. `value_text` in the hash is this canonical result, never the original
provider lexical representation.

Economic dates are ISO civil dates in `YYYY-MM-DD` form. A daily observation
has equal period start and end. A monthly observation has the first and last
civil day of its economic month. These dates are not converted to timestamps;
no execution clock, timezone, or timestamp enters the payload.

### 7.4 Canonical JSON and hash bytes

The normative serialization reference is:

```python
json.dumps(
    payload,
    sort_keys=True,
    ensure_ascii=False,
    separators=(",", ":"),
    allow_nan=False,
)
```

The resulting JSON has exactly the eleven keys, alphabetically ordered, with
no extra spaces, newline, or BOM. It is encoded directly as UTF-8. Financial
values remain strings, `value_scale` is a JSON integer, and non-applicable
currency is the literal JSON `null`.

`DOMAIN_PREFIX_V1` is the following byte sequence, including one final NUL
byte:

```text
FINANALYTICS/EXTERNAL_CONTEXT/CONTENT_FINGERPRINT/V1\x00
```

The four visible characters `\`, `x`, `0`, `0` do not replace the final NUL.
The normative hexadecimal bytes are:

```text
46494e414e414c59544943532f45585445524e414c5f434f4e544558542f434f4e54454e545f46494e4745525052494e542f563100
```

The prefix bytes are concatenated directly with the canonical UTF-8 JSON
bytes. There is no additional separator, newline, salt, or secret. Output is
exactly `sha256:` followed by 64 lowercase hexadecimal digits.

### 7.5 Explicitly excluded fields

The V1 hash excludes `registry_key`, `series_concept`, `provider_value_text`,
`provider_decimal_places`, `retrieved_at`, `ingested_at`, `known_from`,
`published_at`, `revised_at`, `observed_at`, `observation_event_id`,
`knowledge_sequence`, `supersedes_event_id`, `provider_revision_id`, URLs,
license, availability, economic freshness, acquisition health, execution
clock, and random identifiers. These governed facts may exist elsewhere in the
observation and provenance model; this exclusion does not remove them from the
future model.

The economic identity remains `(provider, series_id, reference_period_start,
reference_period_end, semantic_class)`, and all five fields participate in the
V1 payload. Consequently different series, periods, or normalized content have
different content fingerprints, while equivalent normalized content has the
same fingerprint inside V1. A content fingerprint is not a knowledge-event ID.

### 7.6 Normative test vectors

These are synthetic contract vectors, not claims about historical BCB values.
Each payload shown is the complete canonical JSON submitted after the V1 domain
prefix.

**Vector 1 — Selic target**

```json
{"currency":null,"frequency":"DAILY","provider":"BCB_SGS","reference_period_end":"2026-10-09","reference_period_start":"2026-10-09","scope":"BR","semantic_class":"EXTERNAL_OBSERVATION","series_id":"432","unit":"PERCENT_PER_YEAR","value_scale":2,"value_text":"10.50"}
```

```text
sha256:c6b9708c32eb552fa60322d16b793adc48d8b03b7757e975952a526d536e9022
```

**Vector 2 — negative IPCA**

```json
{"currency":null,"frequency":"MONTHLY","provider":"BCB_SGS","reference_period_end":"2026-09-30","reference_period_start":"2026-09-01","scope":"BR","semantic_class":"EXTERNAL_OBSERVATION","series_id":"433","unit":"PERCENT_MONTHLY_CHANGE","value_scale":2,"value_text":"-0.40"}
```

```text
sha256:4105c9c3f1139a0676688d53b21973a1905345e328347a5abed43a77a333a351
```

**Vector 3 — USD selling exchange reference**

```json
{"currency":"BRL/USD","frequency":"DAILY","provider":"BCB_SGS","reference_period_end":"2026-10-09","reference_period_start":"2026-10-09","scope":"BR","semantic_class":"EXTERNAL_OBSERVATION","series_id":"1","unit":"BRL_PER_USD","value_scale":4,"value_text":"5.4321"}
```

```text
sha256:71f700aeb716ea7396a2ab595ff12470858095115595fd146975852dd5f0c83d
```

The expected hashes are normative and must not be silently changed to match a
different payload. An implementation mismatch blocks R3-C as
`BLOCKED — FINGERPRINT TEST VECTOR MISMATCH` pending investigation.

### 7.7 Complementary valid and rejection vectors

Every valid complementary vector must show the complete final payload or an
unambiguous delta from a fully stated payload. Valid cases use only coherent
registry combinations. The following deltas refer unambiguously to the complete
Selic payload in normative vector 1 unless a complete payload is shown:

| Valid case | Exact input/final payload rule | Expected relation |
|---|---|---|
| construction order | construct the same eleven key/value pairs from vector 1 in reverse insertion order; the final canonical payload is exactly vector 1 | same V1 fingerprint as vector 1 |
| lexical equivalence | provider lexical input `10.5`; final normalized payload is exactly vector 1 with `value_text = "10.50"` | same V1 fingerprint as vector 1 and as lexical input `10.50` |
| different value | vector 1 with the sole delta `value_text = "10.51"` after valid normalization | valid V1 fingerprint different from vector 1 |
| different period | vector 1 with exactly `reference_period_start = "2026-10-08"` and `reference_period_end = "2026-10-08"` | valid V1 fingerprint different from vector 1 |
| negative zero | provider lexical input `-0.00`; final payload is vector 1 with the sole delta `value_text = "0.00"` | same V1 fingerprint as provider lexical input `0.00` normalized into that final payload |

The coherent different-series case uses this complete normalized payload:

```json
{"currency":null,"frequency":"DAILY","provider":"BCB_SGS","reference_period_end":"2026-10-09","reference_period_start":"2026-10-09","scope":"BR","semantic_class":"EXTERNAL_OBSERVATION","series_id":"11","unit":"PERCENT_PER_DAY","value_scale":6,"value_text":"0.052788"}
```

It is accepted as a valid V1 payload and is distinct from all three normative
payloads. No complementary hash literal becomes normative merely by being used
in implementation tests.

Rejection cases include SGS 432 with `PERCENT_PER_DAY`, SGS 432 classified as
`EXTERNAL_EXPECTATION`, SGS 11 with scale 2, incompatible currency, unknown
series, missing or extra fields, float values, and invalid scale. They expect a
structured validation exception and have no valid domain fingerprint.

### 7.8 Revision history, deduplication, and versioning

The existing historical rule remains:

```text
Event 1: A -> fingerprint A
Event 2: B -> fingerprint B
Event 3: A -> fingerprint A
```

Events 1 and 3 may share `(version, fingerprint)` but remain distinct by event
ID, knowledge sequence, `known_from`, and predecessor. Deduplication compares
only the current head of the same economic identity and uses the version plus
fingerprint pair. There is no global unique constraint on the fingerprint.
Persistence and concurrency remain R3-D responsibilities.

V1 is immutable after publication. A future V2 requires its own specification
and distinct domain prefix, persists alongside rather than overwriting V1, and
cannot participate in cross-version deduplication without an approved
transition policy. No V2 behavior is authorized here.

## 8. Persistence proposal

`APPROVED BY USER / LOCKED`: use a persistent SQLite observation store rather
than process-only cache or legacy `REAL` tables.

### 8.1 `external_observation_versions`

Conceptual minimum:

- opaque primary key;
- provider and series identifier;
- stable series concept and semantic class;
- economic-period start/end;
- exact canonical fixed-scale decimal `TEXT` plus explicit normalization scale;
- bounded original value text;
- unit and nullable currency;
- frequency and scope;
- optional publication/revision metadata;
- optional provider-observed timestamp plus required retrieved, known-from, and
  ingested UTC timestamps;
- content-fingerprint version, non-unique content fingerprint, monotonic
  knowledge sequence, and optional immediate supersedes reference;
- source URL and license identifier.

Required database guarantees:

- unique `(provider, series, economic identity, knowledge_sequence)` and
  opaque event ID;
- `(content_fingerprint_version, content_fingerprint)` indexed but deliberately
  not unique, so `A -> B -> A` remains reproducible;
- checks for valid period ordering and non-empty provider/series/unit;
- checks that stored value has SQLite `TEXT` storage class, has no surrounding
  whitespace, stays within the approved lexical length, and declares the
  registry normalization scale;
- self-FK for supersession when used;
- indexes for series plus reference period and series plus `known_from`;
- no float/`REAL`, raw response payload, user/account identifier, secret, or
  provider credential.

#### 8.1.1 Decimal storage decision

`APPROVED BY USER / LOCKED`: SQLite stores the normalized value as canonical
fixed-scale `TEXT`, not `NUMERIC(38,18)`.

SQLite's `NUMERIC` is an affinity, not a fixed precision/scale guarantee. A
numeric-looking text value may be converted to `INTEGER` or approximate
binary `REAL`, and the precision/scale arguments in a type name are not
enforced by SQLite. SQLAlchemy `Numeric(asdecimal=True)` can return `Decimal`,
but when the DBAPI supplies a floating-point value the conversion cannot
recover precision that was already lost. Therefore the R3 SQLite contract must
not infer exactness from either declaration.

The approved registry owns one fixed normalization scale per series. The
adapter parses the provider string directly to `Decimal`, rejects float/JSON
number transit, non-finite/exponent/locale forms, and rejects non-zero digits
beyond the registry scale. Canonicalization may add trailing zeroes to the
fixed scale and normalizes negative zero to positive zero; it never rounds a
provider value. `provider_value_text` preserves the bounded accepted lexical
source separately.

The locked common safety envelope is at most 40 integral digits, at most 18
fractional digits, 64 ASCII characters for canonical text, and 128 bytes for
accepted provider value text. Current registry scales are narrower. Canonical
grammar is `-?(0|[1-9][0-9]{0,39})\.[0-9]{S}`, where `S` is the registry scale;
leading plus, exponent, leading zeroes, whitespace, locale separators,
non-finite values, and negative zero are rejected or canonicalized as stated.
These are security/representation bounds, not claimed economic ranges.

Database checks provide coarse defense in depth; the strict grammar, digit
bounds, series scale, and exact `Decimal` reconstruction are enforced at the
domain/repository boundary and revalidated on read. SQL lexical order is not
numeric order. R3 therefore prohibits SQL arithmetic, range predicates,
`ORDER BY value_text`, and `CAST(value_text AS NUMERIC)` as financial
authority. Numeric comparison or sorting occurs only after exact conversion to
Python `Decimal`. A future need for database-side numeric range search requires
a separate approved storage design.

Alternatives evaluated:

- **Scaled 64-bit integer:** exact only while the series-specific scaled value
  remains within SQLite's signed 64-bit range. With scale 6, for example, the
  maximum absolute unscaled magnitude is about `9.22e12`. Official metadata
  does not establish sufficient absolute bounds for every present and future
  series. It is portable only while every reader preserves the companion scale,
  so this is not the common MVP representation.
- **SQLite NUMERIC:** rejected for the MVP because affinity conversion and the
  real DBAPI/dialect path do not prove exact roundtrip across the permitted
  domain. Native fixed-decimal types may be appropriate in a future database,
  but their guarantees cannot be projected backward onto SQLite.
- **Canonical TEXT:** recommended because it preserves every accepted digit
  across close/reopen and makes conversion to `Decimal` explicit. Its lexical
  ordering limitation is an explicit query prohibition, not hidden behavior.

A future move to a database with a proven native fixed-decimal type must parse
and validate the canonical text, migrate without float transit, compare every
value exactly, and preserve unit/scale metadata. The repository boundary keeps
that portability path explicit rather than depending on SQLite coercion.

Official technical basis:

- [SQLite Datatypes](https://www.sqlite.org/datatype3.html) documents dynamic
  typing, affinity conversion, ignored type-name precision, and text collation;
- [SQLite Floating Point](https://www.sqlite.org/floatingpoint.html) documents
  binary64 approximation and the signed 64-bit integer range;
- [SQLite STRICT Tables](https://www.sqlite.org/stricttables.html) confirms that
  strict tables accept only the core storage-class names, not a fixed-precision
  `NUMERIC(p,s)` type;
- [SQLAlchemy Numeric](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Numeric)
  documents that Decimal conversion behavior and accuracy depend on the
  DBAPI/dialect value path.

The representation separates: stored canonical value, provider unit,
provider-declared decimal places, registry normalization scale, and Python
`Decimal` precision. Daily rates are not annualized, percentage values do not
use a currency-cent scale, and no implicit rounding is permitted.

### 8.2 `external_series_sync_state`

One operational row per registry series records only:

- last attempt and last successful retrieval timestamps;
- last covered reference interval;
- bounded typed error code and HTTP status when safe;
- retry eligibility time;
- partial-coverage marker;
- current registry contract version.
- consecutive-retransmission and accepted-transition counters when useful for
  bounded operations evidence.

It stores no financial-user data and is not observation authority. A successful
empty response may update sync state without creating a numeric observation.
The two approved conceptual tables are sufficient for immutable content-transition
history, historical replay, deduplication, last-known-good, and current sync
health. They intentionally do not retain every identical fetch attempt. If
full acquisition-event audit becomes a product or regulatory requirement, a
third append-only fetch-event structure requires separate approval rather than
overloading observation history.

### 8.3 Retention and migration

- Observation versions are retained for reproducibility; no automatic pruning
  is authorized in the MVP.
- Operational attempt detail may be bounded later, but last-success and
  coverage state must remain auditable.
- A future R3-D migration must be singular and deterministic, create empty
  structures, perform no speculative backfill, and be tested by upgrade,
  downgrade, and re-upgrade on a disposable database copy.
- Existing legacy `asset_prices`, benchmark, or `macro_indicators` SQL is not
  reused merely by name; the repository audit found no active Alembic-owned
  table that satisfies this contract.

## 9. Refresh, economic freshness, acquisition health, and availability

No universal TTL exists. Each registry entry owns three separate evaluations:

1. **operational refresh age**, controlling when another provider call is due;
2. **economic freshness**, deciding whether evidence is sufficient to call an
   eligible observation `CURRENT`, `STALE`, or `UNKNOWN`;
3. **acquisition health**, describing whether the latest acquisition was
   `HEALTHY`, `DEGRADED`, `FAILED`, or `UNKNOWN`.

For SGS, only a successful, complete bounded query ending at the explicit
`as_of` can establish the latest provider-returned observation for that
boundary. This does not prove an undocumented publication schedule. Calendar
age, refresh due state, or a network failure alone must not label an economic
observation stale.

Evaluation rules:

- `AVAILABLE + CURRENT`: a successful complete head query proves that the
  selected eligible observation is the latest provider-returned value through
  the requested boundary;
- `AVAILABLE + STALE`: a later eligible observation is known, or a separately
  approved series-specific economic recency rule proves the selected
  observation obsolete;
- `AVAILABLE + UNKNOWN`: an eligible historical/last-known-good observation
  exists, but current evidence is insufficient to prove `CURRENT` or `STALE`;
- `PARTIAL + UNKNOWN`: only part of the requested interval was obtained, so the
  response must expose missing coverage;
- `UNAVAILABLE + UNKNOWN`: no eligible observation exists or validation failed;
- `CURRENT` never means guaranteed economic recency, publication timeliness,
  or suitability as an effective product assumption.

For target Selic, a complete query may confirm that an unchanged repeated target
is still the provider-returned head. For SGS 11, 12, and 1, weekends or holidays
without observations do not imply staleness. For monthly IPCA, absence of a
current-calendar-month observation does not imply staleness. In every case,
insufficient evidence preserves `UNKNOWN` rather than inventing a calendar.

The locked initial operational refresh intervals are six hours for daily
series and twenty-four hours for monthly series. They are call-suppression
policy, not economic truth and not a universal TTL. Later adjustment must
preserve the contract governance and corresponding tests.

## 10. Cache layers

- **Process cache:** optional short-lived request coalescing keyed by provider,
  series, interval, and registry version. Loss is harmless.
- **Observation store:** durable immutable versions and knowledge time. It is
  the governed source for replay and reference context.
- **Last-known-good:** the latest eligible stored event. Acquisition failure is
  exposed independently and does not automatically change economic freshness
  to `STALE`; freshness remains supported by prior evidence or becomes
  `UNKNOWN` when that evidence is insufficient for the requested boundary.
- **Negative cache:** short-lived typed absence/failure keyed by request
  identity. It suppresses repeated failing calls but never stores a financial
  zero and never becomes an observation.

Provider success, observation availability, and cache validity are distinct.

## 11. Provider and adapter contracts

### 11.1 Request

A typed provider request contains only:

- registry series key;
- provider-native series identifier resolved by the registry;
- inclusive civil start/end dates;
- explicit request timestamp and consumer `as_of`;
- correlation identifier safe for logs.

Callers cannot supply arbitrary URLs, units, provider names, or series IDs.

### 11.2 Response

A typed provider response contains:

- validated raw observation records as bounded date/value strings;
- response retrieval timestamp;
- covered interval and completeness marker;
- safe provider response metadata needed for rate-limit handling;
- no unbounded raw body.

### 11.3 Adapter responsibilities

The adapter:

- constructs only governed base URLs;
- enforces allowed series and provider-specific interval limits;
- validates response size, shape, dates, units, and Decimal lexical values;
- normalizes to the immutable domain type;
- classifies typed errors;
- performs bounded retry only for transient failures.

The adapter does not calculate projections, returns, inflation assumptions,
portfolio values, recommendations, or product defaults.

## 12. BCB/SGS request contract

For JSON/CSV daily-series requests from 26 March 2025 onward, official BCB
documentation requires date filters and limits each requested period to ten
years. The R3 adapter must therefore:

- always send `dataInicial` and `dataFinal` for daily series;
- treat both provider parameters as inclusive civil dates;
- split longer ranges into deterministic non-overlapping chunks of at most ten
  years, with each next chunk beginning on the civil day after the prior end;
- merge, validate, deduplicate, and sort by civil reference date;
- accept dates without observations without manufacturing values;
- expose a partial result if one or more chunks fail after bounded retry;
- cap response bytes and observation count before parsing;
- never send a request without a registry-approved series.

The exact ten-year boundary algorithm and inclusive semantics must be frozen by
fixtures and contract tests before live provider implementation.

## 13. Failure taxonomy

| Failure | Retry | Result when eligible last-known-good exists | Result without it |
|---|---:|---|---|
| timeout / DNS / connection | bounded | `AVAILABLE`; acquisition `FAILED`; freshness evaluated independently | `UNAVAILABLE + UNKNOWN`; acquisition `FAILED` |
| HTTP 429 | bounded, honor safe retry hint | `AVAILABLE`; acquisition `DEGRADED` or `FAILED`; freshness independent | `UNAVAILABLE + UNKNOWN`; acquisition `FAILED` |
| HTTP 5xx | bounded | `AVAILABLE`; acquisition `FAILED`; freshness independent | `UNAVAILABLE + UNKNOWN`; acquisition `FAILED` |
| permanent HTTP 4xx | no, except 408/429 | `AVAILABLE`; acquisition `FAILED` with permanent reason; freshness independent | `UNAVAILABLE + UNKNOWN`; acquisition `FAILED` |
| invalid/malformed payload | no automatic semantic retry | `AVAILABLE`; acquisition `FAILED`; freshness independent | `UNAVAILABLE + UNKNOWN`; acquisition `FAILED` |
| incompatible unit/series | no | do not ingest invalid content; prior eligible event may remain `AVAILABLE` with independent freshness | `UNAVAILABLE + UNKNOWN`; acquisition `FAILED` |
| missing period / empty response | no numeric observation | prior event remains historical reference; `STALE` only with positive evidence, otherwise `UNKNOWN` | `UNAVAILABLE + UNKNOWN` |
| partial chunk failure | bounded for failed chunk | `PARTIAL + UNKNOWN`; acquisition `DEGRADED` | `PARTIAL + UNKNOWN`; acquisition `DEGRADED` |
| expired process/negative cache | perform governed refresh | depends on refresh | depends on refresh |

Error objects contain a stable code, transient flag, safe HTTP status, provider,
series key, and retry time when known. Logs must not include full response
bodies, credentials, arbitrary URLs, or personal/financial payloads.

## 14. External reference context contract

`ExternalReferenceContextService` is an internal, read-only boundary. Its
conceptual request contains:

- purpose/consumer identity from a closed enum;
- allowlisted reference key;
- explicit consumer `as_of` date and timestamp;
- optional bounded history window when approved for that purpose.

Its result preserves:

- semantic class;
- exact Decimal value or explicit absence;
- concept, unit, currency, frequency, and scope;
- provider-declared precision and normalization scale;
- economic period and knowledge time;
- provider/source/license metadata;
- availability, freshness, completeness, and reason code.

The service delegates to domain/repository/provider boundaries. It contains no
SQL, provider-specific parsing, effective-input selection, financial formula,
user-financial write, or internal HTTP call to FINANALYTICS APIs.

Consumers receive only purpose-allowlisted references. A reference result never
mutates an engine request and never implies “use this value.”

## 15. Financial authority boundaries

### Portfolio

ADR-023 remains locked. `portfolio_snapshots.patrimonio` remains the aggregate
investment-wealth authority. External quotes or FX must not recalculate it.

### Planning and FIRE

Macro observations may become labeled references in a future approved R6
experience. They are not effective inflation, return, contribution, spending,
or withdrawal-rate inputs. Current request schemas and engines remain unchanged.

### Goals and Health

R3 does not modify Goal amount/contribution/deadline or Health income, expense,
cashflow, savings amount, or savings rate.

### Smart Financial Context

ADR-028 and the locked R2 feature allowlists remain unchanged. R2/R3 composition
requires a separately approved boundary; R3 must not edit B5/B7 allowlists.

## 16. Existing market-data boundary

ADR-006 prohibits a second yfinance system. Future R3-G work must assess and
remediate the existing `MarketDataProvider`, `YFinanceProvider`, and
`MarketDataService` boundary in place.

Known debt remains explicit:

- float-based history/provider transit;
- insufficient provenance and temporal semantics;
- process-local cache only;
- weak timeout/retry/error taxonomy;
- hard-coded USD/BRL fallback `5.0`;
- current FX applied to historical observations;
- provider licensing/personal-use limitations.

The hard-coded FX fallback is priority remediation debt, not an authorized
change in R3-B. No yfinance value becomes certified External Context authority
until its own contract, impact analysis, and regression gate are approved.

## 17. Security, privacy, and licensing

- Providers and series are allowlisted in code from the approved registry.
- Base URLs are static configuration; users cannot submit a URL or provider
  selector, preventing SSRF-style arbitrary fetches.
- Timeouts, response byte caps, observation-count caps, and bounded retries are
  mandatory.
- External payloads are untrusted and validated before normalization or logs.
- Macro requests carry no user ID, account, portfolio, transactions, Profile
  facts, token, or other personal/financial data.
- Credentials, if a future provider needs them, remain server-side settings.
- Every result carries provider and license metadata suitable for attribution.
- BCB/SGS registry entries use the portal's ODbL declaration; R3 must preserve
  attribution and recheck terms before deployment.
- Provider raw bodies and secrets are never logged or persisted.

## 18. Accepted and locked material decisions

The user explicitly accepted the following decisions on 2026-10-09 after an
independent review reported zero blocking, material, or minor findings:

1. Five-series SGS MVP, including SGS 1 as reference-only.
   The locked real-era ingestion floor for SGS 1 is 1994-07-01;
   pre-real observations remain outside normalized MVP scope.
2. Focus as contract-ready but implementation-deferred.
3. Persistent bitemporal observation store with immutable versions and separate
   sync state.
4. Canonical fixed-scale decimal `TEXT` for SQLite, with registry scale,
   locked lexical/digit bounds, explicit `Decimal` conversion, and no
   database-side numeric ordering.
5. Economic/content/knowledge-event identity supporting `A -> B -> A`.
6. Separate availability, economic freshness, and acquisition-health enums.
7. Six-hour daily and twenty-four-hour monthly operational refresh
   intervals.
8. Reordered implementation plan that places persistence/freshness before live
   provider integration.
9. R3-C/D/E/F/I as the mandatory BCB-only closure path; Focus remains
   deferred and R3-G is required before any yfinance admission but needs a
   separate legacy-impact activation decision.
10. ADR-029 as the accepted canonical lock vehicle.

## 19. Mandatory future contract tests

Before implementation can be accepted, deterministic tests with no live
internet dependency must prove:

- all three complete normative V1 vectors through production code; deterministic
  construction order; `10.5`/`10.50` and negative-zero equivalence; valid
  value/period/series differences; exclusion of operational fields; strict
  missing/extra/float/registry-mismatch rejection; exact prefix/UTF-8/null/output
  representation; and `content_fingerprint_version = 1`;
- exact canonical decimal text roundtrip through SQLite 3.50.4 and SQLAlchemy
  2.0.51 (or the then-pinned real runtime), including close/reopen;
- registry-scale extremes, very small daily percentage values, sign and zero,
  trailing-zero canonicalization, over-scale rejection, and no rounding;
- `typeof(value) = 'text'`, no float transit, and no SQL numeric authority;
- `A -> B -> A` produces three events; consecutive A retransmission creates no
  event; provider-response duplicate conflict fails explicitly;
- `consumer_as_of` selects the correct event before A, at A, at B, and at the
  reverted A, including equal-timestamp sequence tie-breaking;
- late ingestion is not visible earlier, and absent `published_at` stays null;
- operational refresh due state does not itself change economic freshness;
- network/acquisition failure preserves an eligible last-known-good without
  automatically forcing `STALE` and preserves structured reasons;
- migration upgrade, downgrade, and re-upgrade on a disposable database copy,
  plus metadata parity and exact data reconstruction;
- provider tests use fixtures/mocks only, while OpenAPI and Planning, FIRE,
  Goals, Health, Portfolio, and R2 engines/contracts remain unchanged.

## 20. Lock status

This document, the series registry, the implementation plan, and ADR-029 are
approved and locked as of 2026-10-09. The R3-B.2 amendment fixes
`content_fingerprint_v1` normatively and was independently verified on
2026-10-10 with 0 blocking, 0 material, 0 minor, and 2 informational findings;
the three normative vectors and V1 binary prefix were reproduced. It does not
implement any R3 runtime capability. Therefore:

- R3 implementation is `NOT STARTED`;
- no schema, provider, dependency, API, frontend, or engine change is
  present in this checkpoint;
- R3-B is `CONTRACT APPROVED / LOCKED / VERSIONED` and ADR-029 remains
  `ACCEPTED / LOCKED`;
- R3-B.2 is `APPROVED / INDEPENDENTLY VERIFIED / LOCKED`;
- R3-C is `READY / NOT STARTED` and requires its own implementation prompt,
  tests, independent implementation review, and checkpoint.
