# External Context Implementation Plan

**Phase:** `10.R3`

**Status:** `CONTRACT APPROVED / LOCKED / VERSIONED`

**Implementation:** R3-C `IMPLEMENTED / VALIDATED / INDEPENDENTLY APPROVED /
CLOSED`; R3-D.1 `CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED /
VERSIONED`; R3-D `CLOSED / PUSHED`; R3-E.0 `CONTRACT APPROVED / INDEPENDENTLY
VERIFIED / LOCKED / VERSIONED / PUSHED`; R3-E1/E2/E3 `CLOSED / PUSHED`;
R3-E4 `IMPLEMENTED / TESTED / INDEPENDENTLY APPROVED / IMPLEMENTATION
CHECKPOINT`; R3-F.0 `CONTRACT APPROVED / DOCUMENTED`; R3-F1 `IMPLEMENTED /
TESTED / AWAITING INDEPENDENT REVIEW`

This plan decomposes the locked External Context contract into independently
reviewable increments. The contract, registry, and ADR-029 were explicitly
approved and locked on 2026-10-09. The approved R3-B.2 amendment was
independently verified on 2026-10-10. R3-C is implemented, validated,
independently approved, and closed. The user explicitly approved the R3-D.1
registry-version and UTC logical knowledge-time decisions on 2026-10-10; Gemini
3.8 Flash High independently approved the eight-document contract delta with 0
blocking, 0 material, 0 minor, and 2 informational findings. R3-D is closed and
pushed at baseline `d62012413f7ec956b070c0fe21420be1f29403ff`. The user
explicitly approved the R3-E.0 decisions on 2026-10-11 and the Deferred
Ingestion & Acquisition Finalization V1 remediation on 2026-10-12. The
R3-E sequence through R3-E4 is checkpointed. On 2026-10-14, the user approved
R3-F.0 decisions D1-D6 and the three mandatory temporal/status refinements
documented below. R3-F1 was implemented and focused-tested on 2026-10-15; it
remains open pending independent review.

## 1. Dependency order

The R3-A sequence is refined to put durable temporal authority before live
provider ingestion:

```text
R3-B contract and registry approval
  -> R3-C domain, normalization, and executable registry
  -> R3-D.1 registry-version and UTC knowledge-time contract delta review
  -> R3-D observation store, cache state, and freshness
  -> R3-E BCB/SGS provider and ingestion
  -> R3-F external reference context boundary
  -> R3-I independent stabilization of the activated BCB-only scope

Separate activation gates:
  R3-G existing market boundary remediation
  R3-H Focus expectations (deferred)
```

Why persistence moves ahead of live provider integration: the contract requires
knowledge-time replay, immutable revisions, deduplication, and last-known-good.
Implementing network ingestion first would either lose those guarantees or
create a temporary process-cache authority that must later be replaced.

R3-C, R3-D, R3-E, R3-F, and R3-I are mandatory for closure of the
BCB/SGS-only R3 MVP. R3-G is mandatory before any yfinance value may enter
External Context, but its legacy behavior changes require a separate impact
approval and are not required to close a BCB-only MVP. R3-H remains in the plan
for semantic completeness and is not part of the first MVP unless separately
activated. A deferred task is never reported as implemented.

## 2. Cross-cutting gates

Every microphase must preserve:

- exact `Decimal` authority and string-based provider parsing;
- canonical fixed-scale SQLite text persistence with no SQL numeric operations;
- explicit economic and knowledge time;
- purpose limitation and provenance;
- absence distinct from zero;
- no hidden default or engine-input substitution;
- no direct consumer-to-provider access;
- no frontend financial calculations;
- no AI, R4, or R6 product integration;
- ADR-006, ADR-023, and ADR-028 boundaries;
- deterministic tests with mocked provider I/O and no internet dependency;
- no change to public OpenAPI unless a later contract explicitly authorizes an
  additive external-context API.

## 3. R3-B — Contract and series registry lock

### Objective

Approve and lock the External Context semantics, official series catalog,
temporal model, persistence direction, failure model, and implementation order.

### Scope

- `EXTERNAL_CONTEXT_CONTRACT.md`;
- `EXTERNAL_SERIES_REGISTRY.md`;
- this implementation plan;
- accepted ADR-029;
- minimal canonical status/testing pointers.

### Exclusions

Code, migration, database mutation, dependency installation, provider calls,
frontend, public API, engine changes, R4, R6.

### Acceptance

- Official metadata supports every MVP registry entry.
- Locked decisions and still-conditional implementation gates are visibly
  distinct.
- All ten material decisions have explicit user approval dated 2026-10-09.
- Markdown, internal links, and documentation scope pass.
- Independent architectural review finds no blocking/material contract gap.

### Recommended execution

GPT-5.6 Sol High; medium-to-high architectural reasoning. Independent review in
a fresh context before lock.

## 4. R3-C — Domain, normalization, and executable registry

### Objective

Implement provider-neutral immutable domain types, strict normalization, typed
errors, the executable allowlisted registry, and the complete
`content_fingerprint_v1` calculation boundary without network or persistence.

R3-C implements a typed V1 payload with exactly the eleven contracted fields,
registry validation, Decimal and civil-period normalization, canonical JSON,
the V1 domain prefix, SHA-256 output, and the separately exposed fingerprint
version. It does not persist either fingerprint field.

### Candidate files

- `backend/domains/external_context/models.py`;
- `backend/domains/external_context/enums.py`;
- `backend/domains/external_context/registry.py`;
- `backend/domains/external_context/normalization.py`;
- `backend/domains/external_context/errors.py`;
- `tests/unit/test_external_context_domain.py`;
- `tests/unit/test_external_series_registry.py`;
- `tests/unit/test_external_context_normalization.py`.

Paths are conceptual until repository conventions are reconfirmed at task
preflight.

### Tests owned

- registry allowlist and unknown-series rejection;
- exact units/frequencies/semantic classes for all five series;
- Decimal lexical parsing without float transit;
- exact fixed-scale canonicalization per registry entry, including zero-padding
  without rounding, negative-zero normalization, over-scale rejection, and
  extreme values within the approved lexical bounds;
- separation of stored value, original unit, provider precision,
  normalization scale, and internal `Decimal` precision;
- civil daily versus monthly reference-period normalization;
- immutable models and required/optional provenance;
- observation versus expectation separation;
- malformed, NaN, Infinity, exponent, locale separator, and excessive-size
  rejection according to the locked parser contract;
- no defaults for missing values;
- all three complete normative V1 payload/hash vectors through the production
  fingerprint implementation, not a copy of that implementation in tests;
- deterministic key ordering independent of dictionary construction order;
- normalized fingerprint equivalence for `10.5` and `10.50`, plus negative
  zero normalization;
- different valid values and periods producing different fingerprints;
- another allowlisted series using only its own coherent registry metadata;
- exclusion of `retrieved_at` and every other operational/provenance field from
  the closed eleven-field payload;
- rejection with structured validation errors for unknown/incompatible series
  metadata, missing or extra fields, floats, booleans-as-integers, and invalid
  scale, with no valid domain fingerprint;
- exact prefix bytes, UTF-8 compact JSON without BOM/newline/salt, lowercase
  hexadecimal output, and `content_fingerprint_version = 1`.

### Acceptance

No HTTP, SQL, migration, cache, public API, or engine behavior. R2 taxonomy is
reused without modification.

### Independent gate

Fresh-context domain/precision/temporal review.

### Recommended execution

GPT-5.6 Sol High; high reasoning.

## 5. R3-D — Observation store, cache state, and freshness

### Objective

Implement immutable bitemporal persistence, revision/deduplication semantics,
series sync state, repository boundaries, last-known-good, and deterministic
availability/freshness evaluation. Implement the locked
`EXTERNAL_SERIES_REGISTRY_VERSION = 1`, persist
`registry_contract_version` in both R3-D structures, and apply the UTC codec,
logical transaction-time, serialized unit-of-work, and mismatch rules from the
R3-D.1 amendment.

### Candidate files

- `backend/infrastructure/persistence/models/external_context.py`;
- `backend/infrastructure/persistence/repositories/external_context.py`;
- `backend/application/services/external_context_freshness.py`;
- a governed UTC timestamp codec at the domain/persistence boundary;
- an application-owned R3-D transactional unit of work;
- one Alembic migration from the then-current sole head;
- `tests/unit/test_external_context_persistence.py`;
- `tests/unit/test_external_context_freshness.py`;
- `tests/unit/test_external_context_migration.py`.

### Tests owned

- upgrade/downgrade/re-upgrade on disposable DB;
- migration/metadata parity;
- executable registry version exactly `1`, positive strict-integer validation,
  Python-bool rejection, and no implicit V2 support;
- `registry_contract_version INTEGER NOT NULL` in observation versions and sync
  state, with immutable event history and sync version changing only after
  certified acquisition or governed reconciliation;
- first sync-state initialization setting
  `registry_contract_version = EXTERNAL_SERIES_REGISTRY_VERSION` without
  manufacturing acquisition success, attempt, observation, coverage, health,
  or current evidence for a never-acquired series;
- registry/fingerprint version independence, unchanged eleven-field V1 payload,
  last-known-good preservation, and `REGISTRY_VERSION_MISMATCH` producing
  `UNKNOWN` freshness/health without changing availability or manufacturing an
  event, zero, `STALE`, or `UNAVAILABLE`;
- canonical fixed-scale `TEXT` roundtrip through the real SQLite/SQLAlchemy
  dialect after close/reopen, including `typeof(value) = 'text'`, small
  percentage values, scale extremes, and no float;
- proof that SQL lexical ordering/range/arithmetic is not used as numeric
  authority;
- economic, content, and knowledge-event identity with immutable history;
- separate persistence of `content_fingerprint_version` and
  `content_fingerprint`, with deduplication comparing their pair only against
  the current head of the same economic identity and no global fingerprint
  uniqueness;
- concurrent ingestion atomicity for the same economic identity;
- simultaneous identical ingestion deduplicating to one committed event;
- simultaneous conflicting transitions producing a deterministic serialized
  order or a typed retry/conflict, never lost history;
- atomic allocation of `knowledge_sequence` and deterministic tie-breaking;
- rollback leaving no event, head change, partial sync-state success, or
  eligible `known_from`;
- `A -> B -> A` producing three events while consecutive identical
  retransmission creates no new event;
- version-aware replay and compatibility with the immutable V1 formula; no
  cross-version deduplication without a separately approved transition policy;
- late ingestion and no look-ahead;
- exact `consumer_as_of` selection before A, at A, at B, and at reverted A;
- canonical 27-character ASCII UTC `TEXT` codec
  (`YYYY-MM-DDTHH:MM:SS.ffffffZ`) with exact byte roundtrip, close/reopen,
  real-date validation, fixed microseconds, UTC-only aware datetimes, extreme
  dates, and rejection of naive/non-zero-offset/non-canonical inputs;
- lexicographic/chronological equivalence only for codec-certified timestamps;
- injected `transaction_time_utc` captured once per attempt after the
  `BEGIN IMMEDIATE` reservation, with `ingested_at = known_from`, comparison to
  `retrieved_at` and the current head, and typed failure without clamping;
- `BEGIN IMMEDIATE` as the first relevant transaction operation, two independent
  connections, bounded timeout/retry, new time and head reread after retry,
  event/sync atomicity, rollback, equal-microsecond sequence ordering, and no
  repository-owned clock or commit;
- direct SQL/transaction evidence that `BEGIN IMMEDIATE`, rather than an
  assumption about `Session.begin()`, precedes the head read and prevents a
  `knowledge_sequence` allocation race;
- an adversarial proof of the logical retroactivity window between assigned
  `known_from` and physical commit, with no claim that either timestamp is the
  physical commit or first-visibility instant;
- compatibility using APIs available in declared `SQLAlchemy==2.0.21`, plus
  verification in the locally observed `2.0.51`, without dependency changes;
- repeated identical retrieval preserving the original event `known_from` and
  updating only bounded sync telemetry;
- optional publication/revision fields remaining null when absent;
- independent operational refresh, economic freshness, and acquisition health;
- acquisition failure preserving eligible last-known-good without forcing
  `STALE`, and `UNKNOWN` when economic freshness cannot be proven;
- per-series freshness, partial/unavailable reasons, and negative cache;
- no user/account data, raw payload, secret, or legacy `REAL` reuse;
- repositories do not commit and service is read-only outside sync metadata.

### Acceptance

One focused migration, no data backfill, no provider network, and no financial
engine/API/frontend change.

### Independent gate

Schema/Decimal/bitemporal/migration review on disposable database copies.

### Recommended execution

GPT-5.6 Sol High; high reasoning. Extra-high only if SQLite/Alembic temporal
constraints require reconciliation.

## 6. R3-E — BCB/SGS observations

**Status:** `READY / NOT STARTED`

R3-E is divided into four bounded implementation increments. This amendment
implements none of them.

### R3-E — Store Compatibility Adapter

Adapt only the existing `ExternalObservationStoreService` with an explicit
typed `immediate`/`deferred` ingestion mode, defaulting to `immediate` so all
legacy R3-D behavior and 45 tests remain unchanged. Deferred mode must preserve
R3-C recertification, Registry Version V1, Content Fingerprint V1, event
history, head-only deduplication, sequence/supersession, LKG, event counters,
and application-owned `BEGIN IMMEDIATE` transactions while withholding global
success, successful refresh advancement, partial-state clearing, and coverage
expansion.

Add only the same-service `get_sync_state(registry_key)` and
`finalize_acquisition(...)` responsibilities. The query returns `None` for no
row and never initializes or mutates state. The finalizer consumes typed chunk
evidence, publishes the global result, rejects stale/regressive conclusions,
updates only finalization-owned fields, preserves counters already changed by
deferred ingestion, and is counter-idempotent on retry. No third table,
migration, persistent attempt journal, or exactly-once claim is authorized.

Candidate files:

- the existing `backend/application/services/external_observation_store.py`;
- existing R3-D domain types only where the approved typed interface requires
  a minimal additive type;
- focused store-compatibility tests extending the existing R3-D suite.

### R3-E — BCB Provider

Implement the first official BCB/SGS client and adapter, safe HTTP transport,
response parsing, typed security/failure handling, deterministic interval
partitioning, and R3-C certification. The adapter assigns `retrieved_at` only
after the complete provider response is received and passes that acquisition
provenance through the governed boundary; it does not assign `ingested_at` or
`known_from`.

This increment has no active-database access. It performs no R3-D persistence,
migration, public API, frontend, scheduler, deployment, or financial-engine
work.

Candidate files remain:

- `backend/infrastructure/external/bcb_sgs_client.py`;
- `backend/infrastructure/external/bcb_sgs_adapter.py`;
- `backend/core/config.py` only if approved provider settings are not already
  representable;
- provider fixtures under `tests/fixtures/external_context/`;
- `tests/unit/test_bcb_sgs_client.py`;
- `tests/unit/test_bcb_sgs_adapter.py`.

### R3-E — Governed Ingestion

Apply the approved ordinary windows using one explicit stable civil date `D`:

- DAILY: inclusive `max(registry_normalized_floor, D - 89 days)` through `D`;
- MONTHLY: inclusive maximum of the normalized floor and the first day of the
  month 23 civil calendar months before `D`, through `D`.

Implement explicit bounded historical deep reconciliation, with no automatic
full backfill for a first acquisition. Certify each complete chunk through
R3-C before first persistence, persist through R3-D, and finalize EMPTY,
PARTIAL, FAILED, or successful acquisition outcomes conservatively. Requested
interval, proven queried interval, and observed economic coverage remain
distinct; discontinuous completed chunks cannot become one durable continuous
coverage range.

Every observation uses the explicit deferred store mode. Global finalization
alone records `SUCCESS`, `EMPTY`, `PARTIAL`, or `FAILED`. It preserves immutable
history, Content Fingerprint V1, Registry Version V1, UTC V1, `A -> B -> A`,
coherent counters, last-known-good, and per-transaction atomicity. It does not
promise global atomicity across chunks or reconstruct interrupted in-flight
attempts without a journal.

Durable coverage is promoted only for a globally complete, fully received,
validated, gap-free requested interval, including valid empty chunks. PARTIAL
and FAILED do not enlarge it; no prior coverage plus PARTIAL keeps both fields
null. Legacy coverage is not retroactively treated as proof of queried
continuity, and disconnected successful chunks are reported in the typed
operation result without a fictitious union.

Before multichunk persistence is implemented, tests must prove that an
intermediate committed chunk cannot be reported as global acquisition success.
If the current service, two tables, and approved minimal extension cannot
provide that conservative crash state, implementation stops for a material
decision before any alternative method, interface, table, or schema is added.

Candidate files remain:

- `backend/application/services/external_observation_ingestion.py`;
- the existing R3-D application service only through the Store Compatibility
  Adapter above;
- `tests/unit/test_external_observation_ingestion.py`.

### R3-E — Manual Refresh

Expose only explicit internal invocation. Apply the existing six-hour DAILY
and twenty-four-hour MONTHLY call-suppression policy independently from the
revision windows. Provide no scheduler, startup backfill, silent full-history
fallback, public endpoint, screen, or operational deployment.

Historical deep reconciliation requires registry series, inclusive start/end
dates, and explicit reconciliation intent. It is never scheduled or inferred
from missing history.

### Tests owned

- five allowlisted series and arbitrary-series rejection;
- DAILY 90-day and MONTHLY 24-calendar-month inclusive window boundaries,
  explicit `D`, leap day, year/month transitions, and normalized floors;
- daily date filters and ten-year maximum chunking;
- inclusive, non-overlapping boundaries and empty dates;
- monthly reference-period normalization;
- response byte/count caps and malformed payloads;
- timeout, DNS, 429, transient 5xx, permanent 4xx, bounded retry/backoff;
- explicit manual reconciliation and no startup/scheduler/full-history
  fallback;
- side-effect-free `get_sync_state(...)` and conservative never-acquired state;
- successful, EMPTY, PARTIAL, FAILED, discontinuous, and interrupted-before-
  finalization acquisitions;
- no false continuous coverage, `AVAILABLE`, `CURRENT`, or global `SUCCESS`;
- LKG, idempotent counters where applicable, and observation deduplication;
- Decimal precision, unit mismatch, and conflicting duplicates;
- no additional migration and active database untouched;
- no personal data in requests/logs;
- deterministic mocked HTTP and disposable SQLite only; no live internet is an
  automated pass condition.

### Acceptance

No consumer calls the provider directly; no projection/default/valuation; no
public API or frontend. Provider base URL is governed and not user-controlled.
No provider implementation begins until the R3-E.0 targeted independent
remediation review passes and the contract is approved.

### Independent gate

Provider contract, failure, SSRF, privacy, windows, coverage/finalization,
crash safety, no-network-test, and no-active-database review.

### Recommended execution

GPT-5.6 Sol High; high reasoning.

## 7. R3-F — External reference context

### R3-F.0 approved purpose contract

`CONTRACT APPROVED / DOCUMENTED` on 2026-10-14. R3-F.0 authorizes no runtime
consumer and implements no service. The closed purpose enum for R3-F1 is:

- `MARKET_INTEREST_RATE_REFERENCE`;
- `MARKET_INFLATION_REFERENCE`;
- `MARKET_FX_REFERENCE`.

The immutable purpose-to-series matrix is an additional service restriction:

| Purpose | Only eligible series | Certified source | Permitted consumer in this phase |
|---|---|---|---|
| `MARKET_INTEREST_RATE_REFERENCE` | `BCB_SGS_SELIC_TARGET`, `BCB_SGS_SELIC_EFFECTIVE`, `BCB_SGS_CDI` | certified BCB/SGS Registry and Store | future internal Market context composer |
| `MARKET_INFLATION_REFERENCE` | `BCB_SGS_IPCA_MONTHLY` | certified BCB/SGS Registry and Store | future internal Market context composer |
| `MARKET_FX_REFERENCE` | `BCB_SGS_USD_SELL` | certified BCB/SGS Registry and Store | future internal Market context composer |

This matrix narrows access without changing Registry V1 `SeriesUse`, units,
definitions, eligibility, identifiers, versions, or any locked contract.
Unauthorized purpose/series/consumer access returns typed
`PURPOSE_NOT_ALLOWED`; it is never silently broadened.

### R3-F1 — Point-in-time External Reference Read Boundary

`IMPLEMENTED / TESTED / AWAITING INDEPENDENT REVIEW`. R3-F1 implements only an
internal, read-only `ExternalReferenceContextService` over certified Registry
and Store boundaries, with immutable request/result contracts, the closed enum
and matrix above, exact `Decimal`, complete provenance, explicit absence, and
orthogonal status dimensions. It has no runtime consumer. Consumers may not use
direct SQL or providers.

Every request must provide both `consumer_as_of_date` and an explicit UTC
`consumer_as_of_timestamp`; there is no hidden current clock. Selection must
satisfy:

```text
reference_period_end <= consumer_as_of_date
known_from <= consumer_as_of_timestamp
```

Within those cuts, deterministic selection preserves `knowledge_sequence`,
including revision/reversion `A -> B -> A`. R3-F1 permits point-in-time lookup
only. `history_window` and any other unapproved history request must be
rejected, never ignored.

The result separates two non-interchangeable views:

- `reference_replay`: value, original economic period, selected knowledge
  event, and provenance determined by the two temporal cuts;
- `operational_state_snapshot`: current operational state observed when the
  read occurs, with no claim that it represents historical health, coverage,
  or freshness.

Mutable sync state must not be used to reconstruct historical operational
state. `state_observed_at` requires trustworthy temporal evidence; otherwise
its absence is explicit. The last eligible observation keeps its original
economic period: a Friday FX quote read on Sunday remains Friday's quote, and
the last published IPCA month does not become the current month. No
interpolation, economic carry-forward, annualization, projection, conversion,
or automatic assumption is authorized.

Economic freshness is derived only from a certified, conservative service
policy. `CURRENT` requires sufficient positive evidence; `STALE` requires an
objective criterion approved in advance; insufficient evidence yields
`UNKNOWN`. HTTP success alone cannot establish `CURRENT`. Missing data returns
`reference=None`, an explicit reason code, and the appropriate availability;
exact Decimal zero remains a valid observation. Registry mismatch preserves
eligible last-known-good and does not by itself imply `STALE` or `UNAVAILABLE`.

### Candidate files

- `backend/application/services/external_reference_context.py`;
- `backend/domains/external_context/purposes.py` when the existing domain model
  cannot own the closed purpose enum;
- `tests/unit/test_external_reference_context.py`.

### Tests owned

- explicit consumer purpose and allowlist;
- explicit date/timestamp `as_of` and no hidden current clock;
- bitemporal replay/no look-ahead;
- exact Decimal and full provenance preservation;
- separation of replay from current operational-state snapshot;
- conservative `CURRENT`, `STALE`, `UNKNOWN`, `AVAILABLE`, `PARTIAL`,
  `UNAVAILABLE`, and independent acquisition-health states;
- explicit absence, valid Decimal zero, and preserved original economic period;
- rejection of `history_window` and typed `PURPOSE_NOT_ALLOWED`;
- last-known-good and source failure behavior;
- cross-purpose leakage prevention;
- no SQL in composer, no internal HTTP, no user-financial writes;
- no mutation of Planning/FIRE/Goal/Health inputs;
- OpenAPI compatibility unchanged.

### Acceptance

Internal point-in-time reference boundary only. Availability of a reference
does not make it an effective assumption or Smart Context default. No writes,
refresh, scheduler, endpoint, frontend, migration, engine, or canonical wealth
source change is in scope.

### Independent gate

Purpose-limitation, provenance, historical replay, and hidden-default review.

### Recommended execution

GPT-5.6 Sol High; high reasoning.

## 8. R3-G — Existing market boundary remediation

### Status

`SEPARATELY GATED / NOT STARTED`. Required before yfinance is admitted to
External Context; not a prerequisite for closure of the BCB/SGS-only MVP.

### Objective

Remediate the existing yfinance boundary under ADR-006 without creating a
second integration or promoting uncertified market data to portfolio authority.

### Required pre-implementation decision

A focused impact audit must decide whether each legacy caller can tolerate:

- removal of hard-coded USD/BRL fallback `5.0`;
- explicit unavailable/stale errors;
- Decimal-safe boundary values;
- corrected historical FX alignment;
- richer provenance and timestamps.

No calculation or fallback behavior may change merely because this task is
listed in the R3 plan. The focused audit and explicit activation decision must
approve the exact compatibility strategy first.

### Candidate files

Only the existing `MarketDataProvider`, `YFinanceProvider`,
`MarketDataService`, their direct callers, and focused tests after real paths
are reconfirmed. No parallel yfinance adapter is allowed.

### Tests owned

- hard-coded fallback removal behavior and affected legacy callers;
- timeouts/retries/error taxonomy;
- Decimal-safe normalization;
- historical date-aligned FX rather than current FX on old prices;
- process-cache semantics and explicit freshness;
- license/attribution presentation contract;
- Investments regression and ADR-023 authority protection.

### Acceptance

No portfolio wealth recalculation, no hidden fallback, no second provider
system, and no automatic certification of yfinance observations.

### Independent gate

Mandatory financial-authority and Investments regression review before any
behavior change is accepted.

### Recommended execution

GPT-5.6 Sol Extra High due to legacy financial-impact reconciliation.

## 9. R3-H — Focus expectations

### Status

`CONTRACT_READY / IMPLEMENTATION DEFERRED / NOT IMPLEMENTED`.

### Activation gate

Requires a separate user decision confirming product need, official Focus
dataset/statistic/horizon selections, publication/collection semantics,
freshness policy, and whether the existing observation schema represents the
expectation dimensions without lossy overloading.

### Eventual candidate scope

- Focus provider and adapter;
- explicit expectation statistic and forecast horizon;
- `EXTERNAL_EXPECTATION` only;
- immutable bitemporal persistence and revisions;
- no automatic Planning/FIRE assumption.

### Eventual tests

Indicator/horizon/statistic identity, collection/publication dates, missing
periods, revisions, no observation conflation, and no hidden defaults.

### Recommended execution

GPT-5.6 Sol High; high reasoning, only after activation.

## 10. R3-I — Independent stabilization

### Objective

Challenge the complete approved R3 implementation from a fresh context.

### Scope

- contract-to-code and registry-to-adapter parity;
- provider failure and security review;
- persistence/migration/bitemporal audit;
- Decimal/no-float audit;
- cache/freshness/last-known-good behavior;
- `A -> B -> A`, retransmission, late ingestion, and no look-ahead behavior;
- exact SQLite text persistence and no SQL numeric-authority operations;
- purpose limitation and no hidden defaults;
- ADR-006/023/028 compatibility;
- no engine/frontend/AI/R6 drift;
- full relevant backend regressions and OpenAPI comparison;
- live-provider smoke only if explicitly authorized and nonessential to pass.

### Acceptance

Zero blocking/material findings, or remediation plus independent delta review.
Only then may the activated R3 scope be closed. The closure report must list
R3-G and R3-H as deferred/not implemented when they were not activated; it may
not relabel deferral as delivery.

### Recommended execution

Independent high-capability reviewer in a fresh context; high reasoning.

## 11. Contract and operational separation

The following are contract artifacts:

- domain types and registry semantics;
- identity, Decimal, provenance, time, revision, freshness, and error rules;
- authority and purpose limits;
- R3-E ordinary revision windows, manual-reconciliation gate, acquisition
  finalization, and conservative coverage semantics.

The following are operational policy:

- timeout duration;
- retry count/backoff;
- response byte/row caps;
- process/negative-cache intervals;
- call rate, worker count, and any future automatic-execution policy.

Operational values must be centrally configured, bounded, tested, and recorded
by registry/provider version. Changing them does not change economic meaning,
but still requires regression evidence and must not silently weaken safety.

## 12. Test ownership matrix

| Requirement | Owning microphase |
|---|---|
| Registry, units, semantic classes | R3-C |
| Decimal and civil-date normalization | R3-C |
| Canonical scales, no rounding, unit/precision separation | R3-C |
| V1 typed payload, canonical JSON, domain prefix, SHA-256, normative vectors, invalid-input rejection | R3-C |
| Fingerprint version/fingerprint persistence and head-only version-aware deduplication | R3-D |
| Registry V1 constant, dual-structure persistence, mismatch and history preservation | R3-D |
| Canonical UTC codec, logical transaction/knowledge time, and physical-commit limitation | R3-D |
| `BEGIN IMMEDIATE`, per-attempt clock, sequence, atomicity, retry, and concurrency proof | R3-D |
| Bitemporal identity/no look-ahead | R3-D |
| Revision/deduplication/history including `A -> B -> A` | R3-D |
| Exact SQLite text roundtrip and lexical-order prohibition | R3-D |
| Migration/schema parity | R3-D |
| Refresh/freshness/acquisition separation, negative cache, last-known-good | R3-D |
| DAILY 90-day and MONTHLY 24-calendar-month windows, floors, explicit `D` | R3-E |
| Manual deep reconciliation and no automatic full backfill | R3-E |
| Acquisition finalization, EMPTY/PARTIAL/FAILED, discontinuous coverage, crash safety | R3-E over the approved minimal R3-D service extension |
| SGS limits, chunking, provider failures | R3-E |
| Timeout/retry/rate-limit/response caps | R3-E |
| Privacy and SSRF prevention | R3-E, rechecked R3-I |
| Purpose limitation and no defaults | R3-F |
| OpenAPI/engine/R2 immutability | R3-F, R3-I |
| Existing market/yfinance behavior | R3-G only if separately activated; mandatory before yfinance admission |
| Focus expectation semantics | R3-H only if activated; otherwise deferred, not implemented |
| Full independent stabilization | R3-I |

## 13. Lock record and next task

R3-B, its three contract documents, and ADR-029 were explicitly approved and
locked on 2026-10-09 after independent review. The user explicitly approved
the R3-B.2 `content_fingerprint_v1` amendment on 2026-10-09; independent delta
review on 2026-10-10 reported 0 blocking, 0 material, 0 minor, and 2
informational findings while reproducing the three normative vectors and V1
prefix. R3-C subsequently closed after independent implementation approval.
The user explicitly approved the R3-D.1 decisions on 2026-10-10; Gemini 3.8
Flash High independently approved its eight-document contract delta (0
blocking, 0 material, 0 minor, 2 informational). R3-D was subsequently
implemented, validated, independently approved, closed, and pushed at baseline
`d62012413f7ec956b070c0fe21420be1f29403ff`.

The user explicitly approved the R3-E.0 decisions on 2026-10-11 and the
Deferred Ingestion & Acquisition Finalization V1 remediation on 2026-10-12.
R3-E.0 is `CONTRACT APPROVED / INDEPENDENTLY VERIFIED / LOCKED / VERSIONED /
PUSHED`; R3-E1/E2/E3 are `CLOSED / PUSHED`; and R3-E4 is `IMPLEMENTED / TESTED
/ INDEPENDENTLY APPROVED / IMPLEMENTATION CHECKPOINT`. Those checkpoints remain
preserved.

On 2026-10-14, the user approved R3-F.0 decisions D1-D6 with explicit
separation between deterministic bitemporal `reference_replay` and current
`operational_state_snapshot`, conservative certified `economic_freshness`, and
preservation of the selected observation's original economic period. R3-F.0 is
`CONTRACT APPROVED / DOCUMENTED`. The next separately gated task is:

`10.R3-F1 — Point-in-time External Reference Read Boundary`

`IMPLEMENTED / TESTED / AWAITING INDEPENDENT REVIEW`. The implementation adds
only the closed purpose module, read-only service/models, and focused unit tests.
The R3-F1 suite reports `28 passed`; the combined R3-F1 plus Registry/Store
regression gate reports `100 passed`. No runtime consumer, write, refresh,
scheduler, endpoint, frontend, migration, engine, or wealth-source change was
introduced. Do not declare R3-F1 closed before independent review.
