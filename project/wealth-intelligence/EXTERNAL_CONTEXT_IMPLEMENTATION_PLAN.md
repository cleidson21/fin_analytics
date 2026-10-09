# External Context Implementation Plan

**Phase:** `10.R3`

**Status:** `CONTRACT APPROVED / LOCKED`

**Implementation:** `NOT STARTED`

This plan decomposes the locked External Context contract into independently
reviewable increments. The contract, registry, and ADR-029 were explicitly
approved and locked on 2026-10-09. Only R3-C is now `READY / NOT STARTED`;
every implementation microphase still requires its own task and gate.

## 1. Dependency order

The R3-A sequence is refined to put durable temporal authority before live
provider ingestion:

```text
R3-B contract and registry approval
  -> R3-C domain, normalization, and executable registry
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
errors, and the executable allowlisted registry without network or persistence.

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
- no defaults for missing values.

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
availability/freshness evaluation.

### Candidate files

- `backend/infrastructure/persistence/models/external_context.py`;
- `backend/infrastructure/persistence/repositories/external_context.py`;
- `backend/application/services/external_context_freshness.py`;
- one Alembic migration from the then-current sole head;
- `tests/unit/test_external_context_persistence.py`;
- `tests/unit/test_external_context_freshness.py`;
- `tests/unit/test_external_context_migration.py`.

### Tests owned

- upgrade/downgrade/re-upgrade on disposable DB;
- migration/metadata parity;
- canonical fixed-scale `TEXT` roundtrip through the real SQLite/SQLAlchemy
  dialect after close/reopen, including `typeof(value) = 'text'`, small
  percentage values, scale extremes, and no float;
- proof that SQL lexical ordering/range/arithmetic is not used as numeric
  authority;
- economic, content, and knowledge-event identity with immutable history;
- concurrent ingestion atomicity for the same economic identity;
- simultaneous identical ingestion deduplicating to one committed event;
- simultaneous conflicting transitions producing a deterministic serialized
  order or a typed retry/conflict, never lost history;
- atomic allocation of `knowledge_sequence` and deterministic tie-breaking;
- rollback leaving no event, head change, partial sync-state success, or
  eligible `known_from`;
- `A -> B -> A` producing three events while consecutive identical
  retransmission creates no new event;
- late ingestion and no look-ahead;
- exact `consumer_as_of` selection before A, at A, at B, and at reverted A;
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

### Objective

Implement the first official provider adapter, safe HTTP transport, deterministic
interval partitioning, normalization, and ingestion into the R3-D store.

### Candidate files

- `backend/infrastructure/external/bcb_sgs_client.py`;
- `backend/infrastructure/external/bcb_sgs_adapter.py`;
- `backend/application/services/external_observation_ingestion.py`;
- `backend/core/config.py` only if governed provider timeout/base settings are
  not already representable;
- provider fixtures under `tests/fixtures/external_context/`;
- `tests/unit/test_bcb_sgs_client.py`;
- `tests/unit/test_bcb_sgs_adapter.py`;
- `tests/unit/test_external_observation_ingestion.py`.

### Tests owned

- five allowlisted series and arbitrary-series rejection;
- daily date filters and ten-year maximum chunking;
- inclusive, non-overlapping boundaries and empty dates;
- monthly reference-period normalization;
- response byte/count caps and malformed payloads;
- timeout, DNS, 429, transient 5xx, permanent 4xx, bounded retry/backoff;
- partial chunk results and safe retry hints;
- Decimal precision, unit mismatch, and conflicting duplicates;
- no personal data in requests/logs;
- deterministic mocks only; live internet is an optional manual smoke, never a
  required automated test.

### Acceptance

No consumer calls provider directly; no projection/default/valuation; no public
API or frontend. Provider base URL is governed and not user-controlled.

### Independent gate

Provider-contract, failure, SSRF, privacy, and no-network-test review.

### Recommended execution

GPT-5.6 Sol High; high reasoning.

## 7. R3-F — External reference context

### Objective

Implement the internal purpose-limited `ExternalReferenceContextService` over
R3-C/D/E boundaries, with explicit `as_of`, provenance, availability,
freshness, and absence.

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
- `CURRENT`, `STALE`, `UNKNOWN`, `AVAILABLE`, `PARTIAL`, `UNAVAILABLE`, and
  independent acquisition-health states;
- last-known-good and source failure behavior;
- cross-purpose leakage prevention;
- no SQL in composer, no internal HTTP, no user-financial writes;
- no mutation of Planning/FIRE/Goal/Health inputs;
- OpenAPI compatibility unchanged.

### Acceptance

Internal reference boundary only. Availability of a reference does not make it
an effective assumption or Smart Context default.

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
- authority and purpose limits.

The following are operational policy:

- timeout duration;
- retry count/backoff;
- response byte/row caps;
- process/negative-cache intervals;
- provider refresh intervals.

Operational values must be centrally configured, bounded, tested, and recorded
by registry/provider version. Changing them does not change economic meaning,
but still requires regression evidence and must not silently weaken safety.

## 12. Test ownership matrix

| Requirement | Owning microphase |
|---|---|
| Registry, units, semantic classes | R3-C |
| Decimal and civil-date normalization | R3-C |
| Canonical scales, no rounding, unit/precision separation | R3-C |
| Bitemporal identity/no look-ahead | R3-D |
| Revision/deduplication/history including `A -> B -> A` | R3-D |
| Exact SQLite text roundtrip and lexical-order prohibition | R3-D |
| Migration/schema parity | R3-D |
| Refresh/freshness/acquisition separation, negative cache, last-known-good | R3-D |
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
locked on 2026-10-09 after independent review. Therefore:

`10.R3-C — Domain, Normalization & Executable Registry`

`READY / NOT STARTED`.

R3-C requires a separate implementation prompt. Do not start it in this
documentation checkpoint.
