# STATUS: LOCKED / APPROVED FOR IMPLEMENTATION

# AUTHORITY: ADR-028

# Phase 10.R2-A — Smart Financial Context Contract

**Date locked:** 2026-10-03

**Implementation state:** `10.R2-B1 — READY / NOT STARTED`

## 1. Purpose

Smart Financial Context answers one bounded question:

> What does FINANALYTICS already know that is semantically eligible for this
> financial task?

It composes existing governed facts, explicit declarations, deterministic
outputs, and user-confirmed observations without inventing convenient values.
It is a read-oriented context layer around existing authorities, not a new
financial engine.

## 2. Repository reality at lock time

The contract is based on source and read-only database inspection, not the R0
audit alone:

- `/profile` has no backend API or governed extended-profile model;
- authenticated `name` and `email` come from `users` through the auth session;
- `fin_profile_extended` stores only `display_name`, `occupation`, `company`,
  and `tax_regime` in browser `localStorage`;
- CPF, telephone, birthdate, gross monthly income, and employment start are
  transient and old persisted copies are removed;
- the active Pierre ledger uses `(provider, external_id)` transaction identity,
  contains no `user_id`, and is governed by `governance_status` plus
  `economic_classification`;
- the active database is single-tenant at this checkpoint: one application
  user, seven Pierre accounts, and one consolidated Health scope;
- 1,462 governed transactions span 18 calendar months; 349 are classified
  `ENTRADA`; recurring descriptions exist, but transfer-like categories,
  variable values, sparse payer metadata, and absent own-transfer links prevent
  automatic salary authority;
- Health owns certified monthly income, expense, realized net cashflow,
  `savings_amount`, savings rate, history, categories, anomalies, and trends;
- Planning already owns the guarded investment-wealth resolver and owned Goal
  readers; FIRE composes the same wealth authority.

These counts are audit evidence, not hardcoded implementation constants.

## 3. Non-negotiable boundaries

1. Profile owns declared user context; transactions remain observed evidence.
2. A recurring credit candidate is not automatically salary or income truth.
3. Declared gross income and observed received income coexist and never
   overwrite one another.
4. There is no universal source precedence. Each consumer requests explicit
   semantic capabilities.
5. Health, Goals, Planning, FIRE, and the Planning portfolio resolver retain
   their existing calculation and source authority.
6. R2 performs no external-provider read, LLM call, financial-record write, or
   hidden scenario mutation.
7. Smart Context reads are immutable composition. Profile declarations and
   income-source decisions use separate explicit write paths.
8. Financial values remain `Decimal` through authoritative boundaries and JSON
   strings publicly.
9. Missing or ambiguous data remains missing or ambiguous; zero is never a
   fallback.
10. Every offered value carries human-readable provenance and purpose-limited
    exposure.

## 4. Taxonomy application

| Class | R2 application | Rule |
|---|---|---|
| `DECLARED` | Profile gross monthly income and future approved preferences | Explicit user save; never inferred from transactions |
| `OBSERVED` | Governed transactions, confirmed recurring received-income evidence, portfolio snapshot | Preserve source, scope, period, and completeness |
| `DERIVED` | Health metrics and recurring-evidence summaries | Reuse the owning service; no duplicate formula |
| `EXTERNAL_OBSERVATION` | Reserved for R3 interoperability | No R2 provider implementation |
| `EXTERNAL_EXPECTATION` | Reserved for R3 interoperability | No R2 provider implementation |
| `ASSUMPTION` | Planning return/contribution/inflation and FIRE spending/withdrawal rate | Explicit analysis input; never produced as a fact by R2 |
| `USER_OVERRIDE` | Scenario-scoped replacement or explicit use of a reference | Preserve source/reference and effective scenario value separately |

## 5. Profile field classification and persistence lock

| Field | Classification | R2 disposition | Purpose and restrictions |
|---|---|---|---|
| Authenticated name | `IDENTITY` | Keep in `users`; editable only through an explicit identity path | Product identity/display; not financial context by default |
| Email | `IDENTITY / SENSITIVE` | Keep existing server persistence; Profile display-only | Authentication/contact identity; never sent to financial context or AI by default |
| `display_name` | `DISPLAY_ONLY` | Do not create a second authoritative name field | Existing browser alias may remain during transition; later UI should prefer authenticated name |
| Telephone | `SENSITIVE / PURPOSE_LIMITED` | `DO NOT STORE` in R2 | No approved financial consumer or communication workflow |
| Birthdate | `SENSITIVE / PURPOSE_LIMITED` | `DO NOT STORE` in R2 | FIRE v1 explicitly does not consume age/birthdate |
| CPF | `SENSITIVE / PURPOSE_LIMITED` | `DO NOT STORE` in R2 | No approved tax/KYC feature; prohibited from context and AI |
| Occupation | `DECLARED_WORK_CONTEXT` | `DEFER`; existing local value is non-authoritative | No current deterministic consumer |
| Employer/company | `DECLARED_WORK_CONTEXT / SENSITIVE` | `DEFER`; existing local value is non-authoritative | Useful only after a purpose-specific reconciliation workflow exists |
| Declared monthly income | `DECLARED_FINANCIAL_CONTEXT` | `PERSIST NOW` through explicit authenticated save | Gross monthly BRL declaration; never automatic Planning/Health input |
| Tax/employment regime | `DECLARED_WORK_CONTEXT` | `DEFER`; existing local value is non-authoritative | No current calculation or eligibility contract |
| Employment start | `DECLARED_WORK_CONTEXT / SENSITIVE` | `DO NOT STORE` in R2 | No current feature needs it; recurrence evidence comes from transactions |

No transient browser value is silently uploaded. Fields marked `DEFER` remain
outside governed Smart Context until a feature proves purpose, validation,
retention, and deletion semantics.

## 6. Declared monthly income contract

The current Profile label is locked semantically as:

`declared_monthly_gross_income`

- amount: positive cent-scale `Decimal`, nullable and editable;
- basis: `GROSS`;
- period: `MONTHLY`;
- currency: `BRL` in R2;
- source: `USER_PROFILE`;
- semantic type: `DECLARED`;
- provenance: authenticated user, explicit save, `as_of_date`, `declared_at`,
  and `updated_at`;
- confirmation: the explicit save is the declaration; no second confirmation
  flag is required;
- clearing: an explicit authenticated null/remove action, never an empty-string
  coercion;
- use: display or reference only unless a consuming feature explicitly selects
  gross declared income.

It is not automatically a Planning contribution, Health income, sustainable
capacity, FIRE spending, or bank-received salary.

## 7. Recurring-income evidence contract

### 7.1 Eligible observations

An observation is eligible for recurring received-income detection only when:

- `governance_status = CLASSIFIED`;
- `economic_classification = ENTRADA`;
- the raw transaction type is exactly `CREDIT` for detector version 1;
- provider, external transaction identity, account scope, description, amount,
  currency, and date are present and structurally valid;
- currency is consistent inside one candidate signature;
- it is not governed as `IGNORAR` or `SAIDA`;
- explicit investment-income or same-titularity-transfer evidence does not make
  it ineligible under the versioned detector rules.

Generic transfer wording is a risk flag, not proof of income or proof of an
own-account transfer. It may produce a candidate only with visible ambiguity
and mandatory confirmation.

### 7.2 Conservative signature

The detector groups observations by a server-owned, versioned signature made
from:

- provider;
- account scope;
- currency;
- normalized description;
- compatible incoming direction.

Normalization is deliberately conservative: Unicode normalization, case
folding, trim, and whitespace collapse. It does not remove all digits, merge
counterparties, apply fuzzy matching, or expose the raw description in public
IDs. Payer/receiver metadata may be supporting evidence when present but cannot
be required because the live ledger is sparse.

The public `candidate_id` is opaque and versioned. Clients cannot submit an
account, signature, transaction list, or claimed evidence as authority.

### 7.3 Observation window and candidate threshold

For the initial detector, the evidence window is the six most recent calendar
months intersecting the authenticated request's `as_of_date`. An incomplete
current month may contribute observed occurrences but must be labeled partial.

A signature becomes `DETECTED_CANDIDATE` only when it has eligible occurrences
in at least three distinct calendar months inside that window. Multiple
occurrences in one month count as one observed month, remain visible as
evidence, and do not inflate recurrence.

The months need not be consecutive. This accommodates a missing month and
end-of-month/beginning-of-next-month shifts without requiring exact day-of-month
equality or inventing a payroll period. Actual dates are never relabeled.

The 3-of-6 lock is evidence-led: the live ledger contains twelve description
groups with at least three distinct months and substantially more two-month
noise. It is an implementation constant covered by tests, not a configurable
user preference. Changing it requires contract reconciliation.

### 7.4 Amount evidence

Exact amount equality and arbitrary percentage bands are prohibited candidate
gates. Amount variability is explainable evidence only:

- occurrence count and distinct observed months;
- latest amount;
- cent-scale median received amount (`typical_received_amount`);
- minimum and maximum observed amount;
- median absolute deviation when at least three values exist;
- first and latest occurrence dates;
- per-month occurrence counts;
- description/signature match and transfer/investment risk flags.

The live data shows large within-signature variability, so no 5%, 10%, or other
similarity threshold is approved. Numeric confidence and opaque weighted scores
are also prohibited.

## 8. Candidate, confirmation, rejection, and staleness

The lifecycle is:

- `DETECTED_CANDIDATE` — deterministic evidence only;
- `CONFIRMED_AS_INCOME` — explicit durable user decision that this signature
  represents a recurring received-income source;
- `REJECTED` — explicit durable user decision suppressing the same signature
  version until the user reverses it or a materially different signature is
  detected.

`STALE` is an observation/freshness state, not a fourth classification. A
confirmed source is stale when it has no qualifying occurrence in the current
six-month evidence window. It remains confirmed historically, is not deleted,
and must not be offered as current received income until evidence resumes or
the user reviews it.

Confirmation never mutates Profile, transaction governance, transaction
categories, or Health. Rejection never deletes transactions. Both actions are
auditable and reversible through an explicit decision update.

## 9. Declared, observed, and derived income

The product uses precise names:

- **Declared gross monthly income** — `DECLARED`, Profile, gross BRL/month;
- **Observed recurring received income** — `OBSERVED`, confirmed transaction
  signature, bank-received cash evidence;
- **Recent total cash income** — Health-owned observed monthly `ENTRADA` total;
- **Typical received amount** — `DERIVED` median for one confirmed signature.

These may legitimately differ because of taxes, benefits, deductions, partial
payments, multiple payers, timing, refunds, or transfers. R2 never labels an
observed bank credit as gross salary and never silently chooses between the
values.

Multiple confirmed sources are supported as a tuple. Smart Context does not
sum their medians into a new canonical income. Aggregate monthly cash income
remains owned by Financial Health.

## 10. Health and expense boundary

Smart Context references Health outputs without recalculation:

- `total_income` and `total_expense` are observed monthly facts;
- `net_cashflow` and `savings_amount` are realized historical surplus/deficit;
- `savings_rate` is a historical derived ratio;
- averages exist only under the certified Health request/period semantics;
- there is no certified fixed-expense, essential-expense, investable-capacity,
  or sustainable-contribution fact.

R2 may expose a Health fact or reference with its period and scope. It must not
rename realized savings as capacity to invest or prefill FIRE retirement
spending from historical expense.

## 11. Existing domain reuse

- **Investment wealth:** delegate to `PlanningPortfolioSourceResolver`; do not
  query Investments HTTP or create another resolver.
- **Goals:** use the owned Decimal Goal read boundary for target, target date,
  current amount, planned contribution, priority, and status. No new Goal math.
- **Planning:** initial wealth may be an eligible fact/source selection;
  contribution, return, and inflation remain explicit assumptions unless the
  user explicitly copies a labeled reference permitted by a later consumer
  contract.
- **FIRE:** eligible investment wealth may reuse the certified selector.
  Retirement spending and withdrawal rate remain explicit required assumptions
  under ADR-025. R2 does not prefill either.

## 12. Smart value model

A smart value is an immutable conceptual record with the minimum applicable
fields:

| Field | Contract |
|---|---|
| `key` | Stable semantic capability key, not a UI field name |
| `value` | Exact typed value or null only when the state permits it |
| `value_type` | `MONEY`, `RATIO`, `DATE`, `PERIOD`, `TEXT`, `ENUM`, `BOOLEAN`, or structured fact |
| `semantic_type` | One canonical R1 taxonomy value |
| `owner` | Canonical capability that owns the value |
| `source` / `source_label` | Stable machine source plus safe human label |
| `scope` | User-safe feature/account/Goal/portfolio scope; no raw internal IDs unless required |
| `observed_at` / `declared_at` | Applicable source time |
| `reference_period` | Applicable month/date range/horizon |
| `freshness` | Optional and source-specific; never fabricated |
| `evidence` | Bounded structured evidence when the value is a candidate/reference |
| `confirmation_status` | Applicable to user-confirmed observations only |
| `override_policy` | `NOT_ALLOWED`, `SELECT_SOURCE`, `USE_AS_REFERENCE`, or `SCENARIO_OVERRIDE` |
| `reason` | Human-readable eligibility/unavailability explanation |

Fields that do not apply are omitted or null by contract; callers do not infer
missing semantics from defaults.

## 13. Feature-specific resolution

The application boundary is conceptually:

`SmartFinancialContextService.get_context_for(feature, current_user, as_of)`

It returns an immutable feature-specific context DTO. A global dump of Profile,
transactions, Goals, portfolio, and Health data is prohibited.

The service may:

- call approved internal readers/services;
- apply feature-specific eligibility;
- compose provenance without changing it;
- return facts, suggestions, required assumptions, and unavailable states.

It may not calculate portfolio/Health/Planning/FIRE truth, call providers or
LLMs, write data, invoke internal HTTP, or accept client-authored certification.

Initial feature identifiers are `PROFILE`, `HOME`, `PLANNING`, `GOAL`, and
`FIRE`. Public exposure is implemented only where R2 or a later consumer phase
has a real need; enumeration does not authorize R6 UI recomposition.

## 14. Source priority matrix

| Feature/input | Preferred semantic source | Fallback/reference | Auto-fill? | Override? |
|---|---|---|---|---|
| Planning initial wealth | Certified investment portfolio selector when explicitly chosen | User-provided scenario or owned Goal current amount | Offer/select, not hidden | Source selection or scenario value; source fact unchanged |
| Planning contribution | Explicit `ASSUMPTION` | Goal planned contribution or observed reference only through explicit `Use` | No | Yes, scenario-scoped |
| Planning return | Explicit `ASSUMPTION` | None in R2 | No | Yes |
| Planning inflation | Explicit `ASSUMPTION` | R3 may later offer an external reference | No | Yes |
| Goal current value | Owned stored Goal fact | None | Yes when Goal selected | Edit through Goals, not Smart Context |
| Goal planned contribution | Owned stored Goal fact | None | Offer within Goal context | Edit through Goals; scenario copy does not mutate Goal |
| FIRE wealth | Certified investment portfolio selector or explicit user scenario | No aggregation/fallback | Explicit source selection | Source choice/manual scenario only |
| FIRE retirement spending | Explicit `ASSUMPTION` | Historical expense display only, not a prefill | No | Yes, required |
| FIRE withdrawal rate | Explicit `ASSUMPTION` | None | No | Yes, required |
| Health income | Certified governed monthly `ENTRADA` total | None | Display fact | No mutation; change governance at owner |
| Profile income | Declared gross monthly income | Observed confirmed sources shown separately | Profile display only | Explicit Profile edit |
| Home income summary | Health recent monthly cash income | Confirmed sources may be supporting detail | Yes after R6 presentation contract | No hidden source substitution |
| Home wealth | Certified eligible investment wealth | Unavailable if resolver fails | Yes after R6 presentation contract | No fact overwrite |
| Home savings capacity | None — not certified | Health realized savings may be labeled historical only | No | Scenario input remains explicit |

## 15. Smart Context matrix

| Context fact | Owner | Semantic type | Certified? | Autofill | Suggest | Override | Notes |
|---|---|---|---|---|---|---|---|
| Investment wealth | Planning portfolio resolver | `OBSERVED` | Yes under ADR-023 guard | Eligible source only | Yes | Source/manual choice | Investment wealth, not net worth |
| Declared gross income | Profile | `DECLARED` | User-governed after save | Profile only | Yes | Edit Profile | BRL/month, gross |
| Confirmed recurring received income | Income decision + governed ledger | `OBSERVED` | Confirmed observation | No hidden use | Yes | Feature-scoped use | Not gross salary |
| Unconfirmed recurring candidate | Recurring evidence engine | `OBSERVED` candidate | No | No | Confirmation only | Confirm/reject | Explainable evidence |
| Monthly expenses | Health | `OBSERVED`/`DERIVED` | Yes | Display only | Historical reference | Scenario override only where allowed | Not retirement spending |
| Savings capacity | None | — | No | No | No | Explicit scenario contribution | Health savings is realized, not capacity |
| Goal target | Goals | `DECLARED` | User-governed | When Goal selected | Yes | Edit Goal | Target basis remains explicit in Planning |
| Goal planned contribution | Goals | `DECLARED` | User-governed | Goal context only | Yes | Explicit copy/edit | Not Planning contribution automatically |
| Retirement spending | FIRE request | `ASSUMPTION` | Explicit input | No | No R2 suggestion | Yes | ADR-025 preserved |
| Withdrawal rate | FIRE request | `ASSUMPTION` | Explicit input | No | No | Yes | No default |
| Expected return | Planning/FIRE request | `ASSUMPTION` | Explicit input | No | No R2 reference | Yes | Historical performance never substituted |
| Inflation | Planning/FIRE request | `ASSUMPTION` | Explicit input | No | R3 future only | Yes | No BCB/Focus in R2 |
| Portfolio positions | Investments / future Portfolio Intelligence | `OBSERVED` | Partial for R2 purpose | No | No | No | 10.5-B remains paused |

## 16. Provenance and freshness

Human-readable provenance examples are part of the contract:

- `Perfil · informado por você · válido em 03/10/2026`;
- `Transações governadas · observado em 5 de 6 meses`;
- `Carteira MyProfit · referência 09/2026`.

Internal primary keys, raw descriptions, account numbers, SQL/table names, and
run IDs are not default display provenance.

Freshness is source-specific:

- Profile declarations expose `as_of_date` and `updated_at`; they do not receive
  an arbitrary stale deadline;
- observed candidates expose first/latest occurrence and the six-month evidence
  window;
- confirmed sources with no qualifying occurrence in the current window are
  `STALE`;
- Health exposes requested/reference periods and closed/partial semantics;
- portfolio freshness remains ADR-023 monthly reference plus technical update
  provenance;
- R3 owns external freshness enums/policies.

## 17. User override model

`USER_OVERRIDE` is feature/scenario scoped unless a separate explicit settings
or Profile save persists it. A resolution result keeps:

- offered source/reference value and provenance;
- selected/effective value;
- override reason or selection action when applicable;
- analysis/feature scope.

An override never rewrites a transaction, Profile declaration, Goal, Health
fact, portfolio snapshot, or external reference.

## 18. UX semantic states

R2 locks meaning and copy principles, not styling:

| State | Meaning | Safe copy pattern |
|---|---|---|
| `KNOWN_FACT` | Eligible governed or declared fact | `Informado por você` / source label |
| `SUGGESTED_REFERENCE` | Evidence/reference offered for explicit use | `Usar como referência` |
| `ASSUMPTION_REQUIRED` | No fact is semantically allowed | `Defina a premissa desta análise` |
| `USER_OVERRIDE_ACTIVE` | Effective scenario value differs from offered reference | `Valor usado nesta análise` |
| `INCOMPLETE_OR_UNAVAILABLE` | Missing, ambiguous, stale, or insufficient evidence | Explain reason; never show zero fallback |

Before confirmation, avoid `Seu salário é X`. Use `Possível renda recorrente`,
`Observado nas suas transações`, `Confirmar renda recorrente`, and `Não é meu
rendimento`.

## 19. Authentication, ownership, and scope

Every public R2 operation requires the existing authenticated current user. No
public request accepts arbitrary `user_id`.

Profile declarations and income decisions are keyed server-side by the current
user. The current transaction ledger cannot prove per-user account ownership.
Until an explicit ownership migration exists, observed-income reads must reuse
an ADR-023-style guard:

1. exactly one application user exists;
2. that stored UUID equals `current_user.id` semantically;
3. the detector derives ledger account scopes internally;
4. zero/ambiguous/inconsistent tenant scope fails closed;
5. the client cannot select account/provider scope as authorization.

This is a local single-tenant bridge, not a general multi-user contract. A
multi-user deployment requires transaction/account ownership reconciliation
before observed-income detection may remain enabled.

## 20. Storage model

R2 implementation requires two normalized persistence owners:

1. `user_declared_financial_context` — one row per authenticated user for the
   minimal declared financial fields approved now;
2. `recurring_income_decisions` — one row per user and versioned source
   signature for `CONFIRMED_AS_INCOME` or `REJECTED`, audit timestamps, and
   reversible status.

Exact SQL names may follow repository naming conventions during R2-B1, but the
separation is locked. Do not add declared financial fields to `users`, overload
Settings, store raw transaction descriptions in the decision row, or persist
computed candidate evidence.

Candidate evidence is computed on read at current scale. A cache may be added
only after measurement and cannot become authority. Durable decisions reference
the versioned signature, source/account scope, and normalizer version rather
than one transaction ID.

## 21. Migration and browser transition

One future versioned migration is required for the two persistence owners,
unique user/signature constraints, timestamps, and foreign-key/user indexes.
No migration is created by this contract task.

Backfill rules:

- never invent historical Profile declarations;
- never scrape or upload `fin_profile_extended` automatically;
- existing browser values remain local and non-authoritative;
- the future Profile may display the local legacy value and offer an explicit
  reviewed save;
- only approved fields are sent; deferred/sensitive fields are excluded;
- after server confirmation, the client may remove the corresponding legacy
  key through a separately tested transition;
- rollback disables new reads/writes without deleting the legacy browser record
  or source transactions.

## 22. Conceptual API surface

Route names follow the existing `/api/v1` and resource-router convention:

| Method and path | Purpose |
|---|---|
| `GET /api/v1/profile/context` | Read minimal declared Profile context for current user |
| `PATCH /api/v1/profile/context` | Explicitly set/clear approved declared fields |
| `GET /api/v1/financial-context/income-candidates` | Read computed candidates plus durable decisions for current user and server-resolved scope |
| `POST /api/v1/financial-context/income-candidates/{candidate_id}/confirm` | Recompute candidate, validate opaque ID, and persist confirmation |
| `POST /api/v1/financial-context/income-candidates/{candidate_id}/reject` | Recompute candidate, validate opaque ID, and persist rejection |
| `DELETE /api/v1/financial-context/income-candidates/{candidate_id}/decision` | Explicitly clear a prior decision so current evidence may resurface |

Feature-specific Smart Context remains an internal application service in R2.
No generic public `GET /financial-context` dump and no arbitrary context
mutation endpoint are approved. A later consumer may add a small purpose-bound
read endpoint after its response fields are proven necessary.

## 23. Public serialization

- money and Decimal ratios: plain JSON strings;
- dates: ISO `YYYY-MM-DD`;
- timestamps: ISO-8601 date-time;
- reference months: `YYYY-MM`;
- counts: integers;
- booleans: booleans;
- enums: stable uppercase strings;
- evidence: bounded arrays/counts without raw transaction descriptions;
- no binary float authority.

## 24. Error and empty-state model

| Condition | Contract outcome |
|---|---|
| No declared income | `200` with nullable/absent value |
| No candidate | `200` with empty list |
| Less than three observed months | Valid `INSUFFICIENT_HISTORY`/non-candidate evidence summary where requested, not `500` |
| Confirmed source stale | `200`, decision preserved, freshness `STALE` |
| Malformed Decimal/date/enum | `422` |
| Candidate ID absent, forged, or not current-user visible | Non-enumerating `404` |
| Candidate evidence changed during decision | `409` and require refresh |
| Single-tenant/ownership invariant fails | Safe `422` unavailable/ambiguous response; no first-scope fallback |
| Authentication absent/invalid | Existing `401` behavior |
| Unexpected invariant/database failure | Generic `500`, no raw data or trace |

## 25. Edge-state locks

- No history and one/two observed months never produce a candidate.
- A missing month does not insert zero and does not prevent 3-of-6 evidence.
- Multiple occurrences in a month remain evidence but count once for coverage.
- End/start-of-month shifts are accepted through distinct-month coverage; no
  exact-day rule exists.
- Variable amounts do not block candidacy; they remain visible evidence.
- Two or more signatures remain separate possible sources.
- Explicit own-account-transfer or investment-income evidence is ineligible;
  generic transfers remain ambiguous and require confirmation.
- Refunds and one-off large credits do not become candidates without recurrence
  and confirmation.
- Zero and negative/chargeback anomalies are ineligible received-income values.
- Declared-only, observed-only, both, and neither are valid context states.

## 26. Privacy and logging

Context sensitivity is purpose-limited:

| Data | Storage | AI eligibility | Logging/API rule |
|---|---|---|---|
| Financial amounts / salary | Approved R2 tables or certified sources only | Future purpose-specific aggregate only | Never log amounts by default; expose only to eligible authenticated response |
| Employer/occupation | Deferred | No by default | Do not add to R2 API/context |
| Birthdate | Not stored in R2 | No | Never log/expose |
| CPF | Not stored in R2 | Never | Never log/expose |
| Telephone | Not stored in R2 | Never | Never log/expose |
| Raw descriptions/counterparties | Existing governed ledger only | No by default | Do not copy into decisions, context payloads, telemetry, or logs |

Operational logs may contain request/correlation ID, authenticated opaque user
ID where repository policy permits, feature/candidate opaque ID, normalizer
version, counts, status, duration, and error class. They must not contain raw
descriptions, account numbers, salary amounts, Profile payloads, tokens, CPF,
or telephone.

## 27. Current transaction/account/category endpoint inventory

The active application currently mounts the Pierre read-model routes:

| Endpoint | Parameters | Response | Limitation relevant to R2 |
|---|---|---|---|
| `GET /api/v1/accounts` | None | Provider/account identity and display fields | Active route is unfiltered and unauthenticated; R2 must not use it as ownership authority |
| `GET /api/v1/transactions` | None | Raw transaction list with descriptions and amounts | Active route is unpaginated and unauthenticated; prohibited as Smart Context source/API composition |
| `GET /api/v1/categories` | None | Provider category rows | Raw/provider category, not governed recurring-income truth |
| `GET /api/v1/governance/transactions` | Governance/category/search pagination filters | Governed transaction view | Operator surface; not a context API |
| `GET /api/v1/financial-health/*` | `reference_month` | Certified aggregates/trends/categories/anomalies | Authenticated but consolidated single-tenant scope |

Additional async routers under `backend/api/routers/` define richer accounts,
transactions, and categories contracts but are not mounted by `backend/main.py`.
R2 must use internal readers and explicit authenticated endpoints, not assume
those dormant routers are production authority.

## 28. Required implementation validation

Future implementation must cover:

- Profile authentication, ownership, Decimal input, nullable clearing,
  purpose-limited fields, and explicit browser transition;
- recurring stable/variable candidates, 3-of-6 boundary, end/start month,
  missing month, multiple sources, refunds, transfers, investment income,
  one-off credits, insufficient/no history, and currency separation;
- candidate-not-fact before confirmation, durable confirm/reject/reverse,
  changed-evidence conflict, stale confirmed source, and no Profile mutation;
- feature-specific composition, provenance preservation, no global precedence,
  source/reference versus effective override, Health reuse, and portfolio
  resolver reuse;
- string-only Decimal serialization, ISO dates, stable enums, and absence of
  sensitive/raw fields;
- regression of Goals, Health, Planning, FIRE, Investments transaction reads,
  and the known historical failure baseline separately.

## 29. Phase boundaries

R2 does not implement BCB/SELIC/IPCA/Focus/news, provider adapters, market
reference integration, AI providers/tools, navigation/theme, Wealth Home,
Goals/Planning/FIRE redesign, Portfolio Intelligence, or engine changes.

Major consumer experience recomposition and smart-prefill integration remain
R6 work. R2 may build the declared context, evidence/confirmation foundation,
feature-specific service, and minimal Profile confirmation experience needed to
make that later work safe.

## 30. Locked outcome

`10.R2-A — CONTRACT LOCKED`

`10.R2-B1 — READY / NOT STARTED`

No material user decision remains. Exact class/file names may follow repository
conventions, but implementation may not change the semantics above without a
contract reconciliation task.
