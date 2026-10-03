# Portfolio Intelligence Contract & Source-of-Truth Audit

**Phase:** 10.5-A

**Date:** 2026-10-02

**Status:** `AUDIT COMPLETE / USER DECISIONS RESOLVED`

**Next gate:** Phase 10.5-B — `PAUSED / PENDING WEALTH OS REALIGNMENT`

**Resume policy:** preserve this audit and its resolved decisions; resume 10.5-B
only after Phase 10.R7 closes the Wealth OS realignment. Do not rerun 10.5-A
unless new evidence invalidates a finding.

---

## 1. Status

Phase 10.5-A is complete as an architecture and source-of-truth audit. The two
product decisions identified by the audit are resolved: governed persistence of
MyProfit `total_atual` is the selected position-valuation authority, and
performance/benchmark presentation is deferred from the MVP. Phase 10.5-B may
now lock the exact contract without reopening those decisions.

No production code, test, migration, package, endpoint, frontend, score,
threshold, or recommendation was created. Phase 10.5-B has not started.

## 2. Executive Summary

The repository has one certified aggregate wealth source:
`portfolio_snapshots.patrimonio`, selected through the guarded semantics of
ADR-023 and `PlanningPortfolioSourceResolver`. It is a monthly investment
portfolio fact in BRL context, not net worth, not a live valuation, and not a
position-level decomposition.

The repository also persists daily position snapshots, asset metadata, income
events, imported portfolio returns/benchmarks, and import provenance. These are
useful facts, but they do not currently form a certified, temporally aligned
Portfolio Intelligence read model. In the inspected database, 151 of 163
position snapshots have no `current_value`; at the latest date, 26 of 28
positions lack it. The importer receives a provider current total but persists
it only for records classified with sector `RDB`. Consequently, the sum of
position valuations cannot be reconciled to the monthly portfolio total.

Existing Investments endpoints and frontend screens calculate allocation,
performance-like values, diversification scores, labels, and chart series.
Those paths mix imported values, live market quotes, average-cost proxies,
floats, different dates, and frontend calculations. They are product surfaces,
not certified Portfolio Intelligence engines, and must not be adopted as the
new source of truth without reconciliation.

The approved valuation direction is to persist MyProfit `total_atual`
comprehensively with governed snapshot/observation semantics. This does not
make position-valued totals equivalent to `portfolio_snapshots.patrimonio`:
aggregate investment wealth and position valuation remain distinct facts until
a formal reconciliation invariant is proven. Live-market valuation is not the
MVP authority. Performance and benchmark metrics are outside the MVP; monthly
snapshots support wealth evolution only, never rentabilidade.

The smallest useful candidate is a read-only, deterministic view containing:

1. certified aggregate investment wealth;
2. position and classification facts at one explicit snapshot date;
3. allocation and top-N concentration only after a single valuation basis is
   complete and governed;
4. counts and explicit unclassified/missing-valuation coverage;
5. monthly wealth evolution, clearly not labelled performance;
6. compact provenance, completeness, scope, and temporal-alignment facts.

Performance, benchmarks, yield, risk models, scores, target allocation, and
rebalance advice remain outside the MVP unless separately contracted.

## 3. Scope

This audit covers the current Investments persistence and import pipeline,
market-data integration, Planning/FIRE source boundary, Investments API,
Investments frontend, relevant tests, live read-only SQLite shape, and the
governing Wealth Intelligence documentation.

It does not design or implement an endpoint, read model, engine, frontend,
migration, target allocation, score, threshold, trade recommendation, AI
interpretation, or Phase 10.5-B contract.

The six requested top-level canonical documents —
`project/01_PROJECT_MASTER_PLAN.md`, `03_PHASE_STATUS.md`,
`04_CURRENT_PHASE.md`, `06_AUDIT_LOG.md`, `07_FRONTEND_CONTRACT.md`, and
`09_IMPLEMENTATION_QUEUE.md` — are absent from the repository. The active
governance evidence is under `project/wealth-intelligence/`. This is documented
as governance drift, not silently substituted or repaired here.

## 4. Existing Architecture

The current relevant flow is:

```text
MyProfit files
  -> parser / confirmation use cases
  -> assets, position_snapshots, portfolio_snapshots, income_events

yfinance
  -> cache-only quote/history provider
  -> Investments endpoints and UI fallbacks

portfolio_snapshots
  -> PlanningPortfolioSourceResolver (ADR-023 guard)
  -> Planning and FIRE aggregate initial wealth

Investments router
  -> endpoint-local aggregation and mixed valuation fallbacks
  -> Wealth frontend hooks
  -> additional browser-side calculations and labels
```

There is no `backend/domains/portfolio_intelligence/`, certified allocation or
performance engine, dedicated Portfolio Intelligence read model, persisted
price/FX history, or Portfolio Intelligence API/frontend route.

## 5. Certified Data Inventory

| Data | Source | Grain | Certified? | Temporal Basis | Limitations |
|---|---|---|---|---|---|
| Investment portfolio wealth | `portfolio_snapshots.patrimonio` | account + reference month | Yes, only through ADR-023 guarded resolution | Monthly bucket | Mutable UPSERT; not exact time travel; not net worth; no position reconciliation invariant |
| Imported portfolio return | `portfolio_snapshots.pct_mensal`, `pct_acumulada` | account + reference month | Persisted provider fact, not a FINANALYTICS performance engine | Monthly/import snapshot | Float parsing before Decimal; provider semantics/cashflow method not certified |
| Imported benchmarks | `cdi`, `ibov`, `sp500` fields in portfolio snapshots | account + reference month | Reference fact only | Monthly/import snapshot | Coverage/method/currency comparability not governed |
| Position quantity and average price | `position_snapshots` | account + asset + reference date | Persisted imported fact with run/source provenance | Daily snapshot date | Logical account only; no authenticated ownership relation; average cost is not market value |
| Position current value | `position_snapshots.current_value` | account + asset + reference date | Persisted when present | Daily snapshot date | 151/163 missing in inspected DB; importer discards provider total for most assets |
| Asset identity/class | `assets` | ticker | Governed reference row | Latest mutable metadata | Heuristic classification; taxonomy/comment mismatch; stale values possible |
| Sector | `assets.sector` | ticker | Imported reference data | Latest mutable metadata | Not issuer taxonomy; may be missing/stale; classification input, not a certified exposure model |
| Currency | `assets.currency` | ticker | Persisted reference field | Latest mutable metadata | All inspected assets are BRL, including global/crypto categories; original currency is not preserved |
| Income event | `income_events` | account + asset + event dates/type/amount | Persisted event with run provenance | Payment/ex/import dates | Future payment rows exist; received income requires an explicit payment-date cutoff |
| Live quote/history | yfinance provider/cache | ticker + provider observation | Reference data only | Current quote or provider history | Not persisted/certified; partial asset coverage; float normalization; FX limitations |
| Accounts | live `accounts` table | provider + external id | External integration record | Mutable | Schema does not match legacy ORM ownership model; no `user_id` on live table |
| Import run | sync/import logs | user + source + dataset + run | Provenance fact | Import time | Supports lineage, not economic valuation semantics |

Read-only database evidence on 2026-10-01:

- 39 assets, 163 position snapshots, 49 portfolio snapshots, and 610 income
  events;
- one investment account across the relevant snapshot/event tables;
- 28 assets in the latest position snapshot dated 2026-09-27;
- portfolio history from 2022-09 through 2026-09 without missing monthly rows;
- all relevant snapshot/event run IDs resolve to successful runs;
- five income-event rows have payment dates after the audit date and therefore
  cannot be called received income as of the audit date.

These counts describe the inspected local database, not a permanent contract.

## 6. Source Classification

| Candidate | Classification | Current owner | Safe use now |
|---|---|---|---|
| Guarded monthly investment wealth | CERTIFIED FACT | Planning source resolver / Investments persistence | Direct display with month, BRL context, scope, and provenance |
| Position quantity/average cost/current value when present | CERTIFIED FACT (row-level, with limitations) | Investments persistence/import | Display as imported facts; not silently synthesize missing valuation |
| Asset metadata/classification | REFERENCE DATA | Investments persistence/import | Classification context with unclassified coverage |
| Income events | CERTIFIED FACT (event-level) | Investments/Dividends | Date-filtered event facts; keep analytics in Dividends boundary |
| Imported returns and benchmarks | REFERENCE / EXTERNAL REPORTED FACT | MyProfit snapshot | Only as explicitly provider-reported context if approved |
| Planning aggregate-wealth resolution | DERIVED FACT — EXISTING ENGINE/RESOLVER | Planning | Resolve one eligible wealth fact; not position analytics |
| Allocation weights and top-N | DERIVED FACT — NEW DETERMINISTIC ENGINE REQUIRED | Future Portfolio Intelligence | Only from one aligned and sufficiently complete valuation set |
| Counts and completeness ratios | DERIVED FACT — NEW DETERMINISTIC ENGINE REQUIRED | Future Portfolio Intelligence | Deterministic from one selected snapshot |
| Existing Investments allocation/performance outputs | NOT CERTIFIED FOR 10.5 | Investments API/UI | Audit evidence only; do not adopt as authority |
| TWR, MWR/XIRR, robust P&L, risk metrics, rebalance deltas | UNSUPPORTED | None | Defer pending sources/contracts/engines |

## 7. Temporal Semantics

- `portfolio_snapshots` is monthly (`YYYY-MM`) and mutable by UPSERT.
- `position_snapshots` is dated daily and may have several imported dates per
  month.
- `current_value` has no independent persisted price/valuation timestamp.
- yfinance quotes use provider time and a short-lived cache; quote history uses
  provider dates but is not persisted as governed portfolio valuation.
- income events distinguish payment date, ex-date, and import time.
- import runs establish lineage and success, not economic observation time.

Position composition and aggregate wealth cannot be silently joined merely
because their dates fall in the same month. A future response must expose the
selected position snapshot date and aggregate reference month separately, plus
an alignment status. Historical income must be cut by the relevant payment-date
semantics. Alignment is unresolved until the valuation authority is locked.

## 8. Portfolio Scope Semantics

In the current architecture:

- **investment portfolio** means eligible imported investment wealth, not net
  worth;
- **portfolio snapshot** is one account/month aggregate provider record;
- **position snapshot** is one account/asset/date imported holding;
- **account** is an external logical identifier in Investments persistence;
- **asset** is a ticker-centric catalog record;
- **asset class** is a normalized/import-inferred label on the asset row.

ADR-023 permits the aggregate portfolio source only under a guarded
single-user/single-tenant invariant and prevents an arbitrary external account
selector. The live Investments endpoints still accept an optional account ID
and do not enforce the same semantic ownership guard. A future Portfolio
Intelligence API must use server-owned scope resolution and must not expose an
arbitrary client account selector.

## 9. Portfolio Value Authority

`portfolio_snapshots.patrimonio` is the only current canonical aggregate value.
It is Decimal-backed, monthly, imported, and guarded when used by Planning/FIRE.
It may be displayed as investment portfolio wealth with its reference month.

It does not establish:

- real-time value;
- net worth;
- cash content;
- position-level valuation components;
- exact historical time travel;
- a reconciliation to position snapshots.

The current Investments API also calculates values from position rows, quotes,
or average cost. That mixed value is not the portfolio-value authority.

## 10. Position / Valuation Authority

The position row authoritatively stores imported quantity, average price, and
current value only when current value is present. The MyProfit parser receives
`total_atual`, but the confirmation use case persists it only when the imported
sector is exactly `RDB`; other assets lose that valuation fact.

At the latest position date, only 2 of 28 positions have `current_value`. The
current allocation endpoint fills gaps with yfinance for selected classes and
then with `quantity × average_price`, combining market value and cost basis.
Fixed income lacks a general quote path. Quote dates, fallback basis, and
completeness are not exposed as a coherent contract.

Therefore there is no certified authority for value by asset or value by class.
Missing values must remain missing/partial; average cost must not be presented
as current value. Decision 1 selects comprehensive, governed persistence of
MyProfit `total_atual` as the authority to be contracted and implemented; it
does not retroactively certify the incomplete current rows or reconcile their
sum with aggregate investment wealth.

## 11. Asset Classification Authority

The persisted taxonomy observed in code/data includes `STOCK`, `FII`, `BDR`,
`ETF_GLOBAL`, `FIXED_INCOME`, `CRYPTO`, and `OTHER`. The model comment instead
mentions `ETF` and `STOCK_US`, demonstrating taxonomy drift.

Classification is derived heuristically from imported sector text. Existing
asset classes are generally preserved, while missing sector may be enriched.
New imported assets default to BRL currency. The inspected current snapshot has
no `OTHER` classification, but that does not make unknown impossible.

Class counts are supportable as reference facts. Value-weighted class exposure
inherits the unresolved valuation problem. Sector, issuer, geography, and
currency exposure are not certified by this classification model.

## 12. Allocation Feasibility

Allocation by asset and class is deterministic in principle:

```text
weight = aligned_position_value / sum(aligned_position_values)
```

It is safe only when all included values share scope, snapshot date, valuation
basis, currency, and a declared missing-value policy. The current data does not
meet those preconditions. The existing endpoint calculation is not reusable as
authority because it mixes stored values, current quotes, and cost proxies using
float arithmetic.

Status: **PARTIALLY SUPPORTED / CONTRACT BLOCKED BY VALUATION AUTHORITY**.

## 13. Concentration Feasibility

Largest position and top-3/top-5/top-10 shares are deterministic sums of
certified allocation weights and need no opinionated threshold. They must be
computed server-side using Decimal and a stable tie-breaker.

Zero total, missing values, and partial coverage must not produce misleading
percentages. Until position valuation is governed, these metrics are not
reliable. Once governed, the facts are presentation-safe; labels such as “high
concentration” remain interpretations requiring a separate rule/user limit.

## 14. Diversification Feasibility

| Fact | Feasibility | Evidence / limitation |
|---|---|---|
| Number of positions/assets | SUPPORTED | Deterministic at one selected position snapshot |
| Number of asset classes | SUPPORTED | Deterministic, but taxonomy provenance and `OTHER` must be disclosed |
| Weight by class | PARTIALLY SUPPORTED | Requires resolved position valuation |
| Unclassified count | SUPPORTED | `OTHER`/missing classification can be counted |
| Unclassified exposure | PARTIALLY SUPPORTED | Requires resolved valuation |
| Issuer concentration | UNSUPPORTED | No governed issuer identity model |
| Sector concentration | PARTIALLY SUPPORTED | Sector metadata exists but is not a stable governed taxonomy; valuation unresolved |
| Geographic exposure | UNSUPPORTED | No certified geography fact |
| Currency exposure | UNSUPPORTED | Original currency/FX provenance is not preserved |
| Broker/account concentration | UNSUPPORTED FOR MVP | Ownership and multi-account semantics are not contracted |

No diversification score is justified by these facts.

## 15. Historical Evolution Feasibility

The 49 inspected monthly portfolio snapshots form a continuous series from
2022-09 through 2026-09. `patrimonio` can safely support a chart called
**investment wealth evolution**, with reference month and source disclosed.

Changes between snapshots include contributions, withdrawals, income, price
movement, and possibly provider-specific scope changes. Without cashflow-aware
attribution they are not portfolio return. The current frontend language and
rebasing must not convert this wealth series into “performance”.

## 16. Performance / Return Audit

There is no certified FINANALYTICS portfolio-performance engine.

- Provider fields `pct_mensal` and `pct_acumulada` are imported facts whose
  calculation method is not governed locally.
- Evolution endpoints expose provider values and browser code rebases them by
  subtraction.
- The performance hook derives “unrealized gain” from current wealth minus net
  contributions, labels accumulated return as CAGR/total return, and supplies
  zero placeholders for several metrics.
- Asset detail derives gain from a mixed current-price basis and average cost;
  dividends are handled separately.
- No certified TWR, MWR/XIRR, cashflow-adjusted return, robust realized P&L,
  total return, or annualization engine exists.

Calling snapshot growth “rentabilidade” is closure-critical semantic risk.
Decision 2 confirms that performance and benchmark comparison are **outside
the MVP**.

## 17. Benchmark Audit

Monthly snapshots contain imported CDI, Ibovespa, and S&P 500 fields. There is
no separate governed benchmark-history store, no certified cumulative
comparison engine, and no proof that provider return methodology, dates,
currency, and cashflow treatment match the portfolio series.

Frontend alpha/rebasing calculations are not a certified engine. Benchmark
comparison is unsupported for the MVP. If imported fields are ever shown, they
must be labelled provider-reported context, not locally verified alpha.

## 18. Dividend Analytics Boundary

Income events support monthly/annual and by-asset dividend facts, subject to
payment-date cutoff and account scope. Existing Dividends endpoints and UI
already own that analytical surface.

Portfolio Intelligence should not duplicate dividend engines. The MVP may link
to the existing Dividends experience or later consume a separately certified
income fact, but dividend concentration and income charts remain outside the
10.5 MVP boundary.

## 19. Yield Audit

Yield on cost, current yield, portfolio yield, and dividend yield have
ambiguous denominators and timing in the current implementation. Average cost,
mixed valuation fallbacks, future income rows, and absent valuation dates make
the result non-comparable. Existing YOC-like calculations are not a suitable
Portfolio Intelligence authority.

Status: **UNSUPPORTED FOR MVP**.

## 20. Risk Metrics Audit

| Metric | Required evidence | Finding |
|---|---|---|
| Volatility | aligned periodic total returns | Unsupported; no certified return series |
| Drawdown / max drawdown | consistent total-return or value series with cashflow policy | Unsupported; wealth snapshots include flows |
| Beta | aligned portfolio and benchmark returns | Unsupported |
| Sharpe / Sortino | returns, frequency, risk-free/downside contract | Unsupported |
| VaR | return distribution, horizon/confidence/model contract | Unsupported |
| Correlation/covariance | aligned asset return history and currency policy | Unsupported |

yfinance history is cache-only, incomplete by asset class, and uses unsuitable
FX handling for historical global assets. All advanced risk metrics are
deferred.

## 21. Target Allocation / Rebalancing Audit

No certified target allocation, user desired weights, tolerance, or strategy
policy exists. Current allocation facts do not imply an ideal allocation.
Rebalance delta, under/over-allocation labels, and trade suggestions are outside
10.5 and remain in the later Rebalancing phase after an explicit contract.

## 22. Portfolio Score Audit

The frontend already computes a “diversification score” from top-five share and
asset count, clamps it to 0–100, and attaches hard-coded labels. Other screens
use thresholds such as 50, 66, and 70 without a governed owner or versioned
formula.

That score is not a certified fact and must not enter the 10.5 MVP. A future
score would require explicit dimensions, normalization, thresholds, versioning,
explainability, and golden vectors. No opaque Portfolio/Risk/Quality score is
recommended.

## 23. Facts vs Interpretations

| Item | Type | Deterministic? | Needs Threshold? | Needs User Assumption? | Proposed Owner |
|---|---|---:|---:|---:|---|
| Investment wealth = BRL amount at reference month | FACT | No calculation beyond source resolution | No | No | Portfolio Intelligence read model using ADR-023 guard |
| Asset weight = 18.4% | DERIVED FACT | Yes | No | No | Portfolio Intelligence Decimal engine |
| Top five = 61.8% | DERIVED FACT | Yes | No | No | Portfolio Intelligence Decimal engine |
| Target FII allocation = 30% | USER ASSUMPTION | N/A | No | Yes | Future Rebalancing contract |
| Above configured concentration limit | RULE-BASED INTERPRETATION | Yes | Yes | Usually | Future governed rules/Insights |
| “Portfolio is well diversified” | RULE-BASED INTERPRETATION | Only after a rule contract | Yes | Possibly | Not MVP |
| Narrative explanation of certified facts | AI INTERPRETATION | No financial math in AI | Depends | No | Future 10.8/10.9 layer |

The MVP should expose facts and derived facts, not opinions.

## 24. Insights Overlap

The documented Insights boundary already mentions concentration, cash,
diversification, and class-mix rules. The active Investments frontend also
contains similar rule-like labels. No independent canonical Insights engine was
found that Portfolio Intelligence can safely reuse as metric authority.

The future architecture should make Portfolio Intelligence own deterministic
facts and allow a rule engine to consume those facts. It should not duplicate
thresholds in API and frontend, nor convert existing UI heuristics into a
contract by accident.

## 25. Investments UI Overlap

Current Wealth screens already display allocation, positions, dividends,
evolution, performance-like metrics, alpha, and a diversification score. The
audit found these risks:

- allocation mixes stored market value, live quote, and average-cost fallback;
- hooks coerce financial responses to JavaScript `Number`;
- score/labels and top-five calculations live in the browser;
- growth milestones and benchmark rebasing are browser calculations;
- performance maps unsupported/zero placeholder metrics into authoritative
  labels;
- positions and portfolio hooks target routes not present in the audited
  Investments router;
- dividend aggregates/yield are duplicated in frontend calculations.

Portfolio Intelligence must replace or consume certified server facts; it must
not be a renamed duplicate of these pages.

## 26. Candidate Metric Matrix

| Metric | Source | Existing Owner | New Math? | Reliable? | MVP Recommendation | Notes |
|---|---|---|---:|---:|---|---|
| Portfolio value | guarded `portfolio_snapshots.patrimonio` | Planning resolver/source | No | Yes, at monthly grain | INCLUDE | Label investment wealth; expose reference month |
| Asset weights | aligned position valuations | None certified | Yes | No today | CONDITIONAL | Lock valuation authority first |
| Asset-class weights | positions + asset class | None certified | Yes | No today | CONDITIONAL | Inherits valuation and taxonomy limitations |
| Largest position | certified weights | None | Yes | No today | CONDITIONAL | Fact only; stable tie-breaker |
| Top-3 concentration | certified weights | None | Yes | No today | CONDITIONAL | No “high” threshold |
| Top-5 concentration | certified weights | Frontend heuristic only | Yes | No today | CONDITIONAL | Do not reuse browser score |
| Asset/position count | one position snapshot | None | Yes | Yes | INCLUDE | Define zero/negative position policy |
| Class count | positions + asset class | None | Yes | Yes with disclosure | INCLUDE | Include `OTHER` explicitly |
| Unclassified exposure | positions + valuation + class | None | Yes | No today | CONDITIONAL | Count can be included now; value share waits |
| Cash exposure | absent/ambiguous | None | Yes | No | DEFER | No certified cash component |
| Domestic/international exposure | absent geography/original domicile | None | Yes | No | DEFER | `ETF_GLOBAL` is not sufficient geography |
| Currency exposure | original currency + aligned FX | None | Yes | No | DEFER | Current rows all BRL; original currency lost |
| Portfolio evolution | monthly `patrimonio` | Investments history | Minimal | Yes as wealth evolution | INCLUDE | Never call it return |
| Portfolio performance | cashflows + certified valuation/return engine | None | Yes | No | DEFER | No TWR/MWR authority |
| Benchmark comparison | comparable portfolio/benchmark returns | Frontend only | Yes | No | DEFER | Imported benchmark context is not enough |
| Dividend concentration | income events | Dividends | Yes | Partially | KEEP SEPARATE | Avoid duplicating Dividends |
| Yield | income + governed denominator/date | Investments/UI | Yes | No | DEFER | Denominator/timing ambiguous |
| Drawdown | certified return/value-with-flow policy | None | Yes | No | DEFER | Wealth series contains cashflows |
| Volatility | certified periodic returns | None | Yes | No | DEFER | No return series authority |
| Rebalance delta | current + user target allocation | None | Yes | No | DEFER TO 10.6 | No target allocation contract |
| Risk score | multiple governed metrics/rules | None | Yes | No | EXCLUDE | Opaque score prohibited |
| Diversification score | allocation + versioned rules | Frontend heuristic | Yes | No | EXCLUDE | Existing formula is ungoverned |

## 27. Recommended MVP Boundary

Proposed, not locked:

1. aggregate investment wealth from the guarded monthly snapshot;
2. one server-selected position snapshot with asset/class facts;
3. asset and class allocation only after MyProfit `total_atual` is persisted
   comprehensively under governed snapshot/observation semantics;
4. largest position and fixed top-3/top-5 facts from the same weights;
5. position count, class count, missing-valuation count, and unclassified count;
6. unclassified exposure only when value coverage permits it;
7. monthly investment wealth evolution, not performance;
8. scope, dates, currency context, source, run/provenance, completeness, and
   temporal-alignment indicators.

If no valuation reconciliation is authorized, the safe initial subset is
limited to aggregate wealth, counts, metadata coverage, and wealth evolution.
That subset is technically safe but materially less useful.

## 28. Deferred Metrics / Features

- TWR, MWR/XIRR, CAGR, robust P&L, attribution, and total return;
- benchmark alpha/comparison;
- dividend concentration and income analytics duplication;
- all yield metrics;
- volatility, drawdown, beta, Sharpe, Sortino, VaR, correlation, covariance;
- issuer, geography, currency, and reliable sector exposure;
- cash exposure until a certified cash component exists;
- target allocation, rebalance deltas, tolerances, and trade suggestions;
- risk, quality, portfolio, and diversification scores;
- prediction, recommendations, LLM calculations, and AI narratives;
- persistence/materialized Portfolio Intelligence tables unless query evidence
  later justifies them.

## 29. Precision Policy Findings

Persistence uses SQL numeric columns and Planning/FIRE preserve Decimal and
strict string serialization. The Investments import path first parses through
`float` and some API/frontend paths convert values to float/Number. That is not
suitable for new financial authority.

The 10.5-B contract should specify Decimal-only financial math, server-side
rounding, money at the source-supported scale, a dedicated weight/ratio quantum,
and financial JSON values as strings. It should reuse a documented project
rounding convention where applicable rather than inventing one in the UI.

## 30. Currency / FX Findings

The aggregate portfolio source is currently governed in BRL context. Asset
rows do not preserve reliable original currency: all inspected assets are BRL,
including global/crypto classifications. yfinance converts some quotes using a
current USD/BRL rate, uses a hard-coded `5.0` fallback when FX lookup fails, and
converts historical prices with one current FX rate rather than date-aligned FX.

Currency exposure and foreign-asset historical performance are unsupported.
The MVP may disclose BRL presentation context, but must not infer economic
currency exposure from the current field.

## 31. Data Quality / Missing Data

| Condition | Audit classification | Required semantic treatment |
|---|---|---|
| Missing position current value | Partial result | Keep missing; expose coverage; never silently call cost basis market value |
| Zero current value | Potentially valid | Distinguish explicit zero from missing |
| Unknown/`OTHER` class | Valid but unclassified | Preserve and expose count/share when computable |
| Stale/mixed snapshot dates | Invalid for silent aggregation | Select one date or mark unresolved/alignment status |
| Duplicate asset at same account/date | Invalid | Reject/invariant failure; unique key should protect it |
| Negative position | Contract unresolved | Do not silently discard; decide unsupported vs explicit short semantics |
| Currency mismatch | Unsupported | Do not aggregate without governed conversion/provenance |
| Missing benchmark history | Unsupported comparison | Omit benchmark result |
| Missing income data | Partial/unknown | Do not treat absence as zero without certified completeness |
| Future payment event | Valid scheduled/imported fact | Exclude from “received as of” until payment date |

Observed reconciliation evidence:

- latest position cost proxy: BRL 114,866.68;
- latest mixed stored-value/cost proxy: BRL 116,660.47;
- September 2026 portfolio wealth: BRL 112,929.97.

The difference is not merely rounding and has no certified decomposition.

## 32. Empty / Edge States

- No eligible portfolio snapshot: unavailable, not zero.
- Explicit certified zero `patrimonio`: valid observed zero.
- No selected position snapshot: composition unavailable/empty with reason.
- Empty snapshot: zero positions; do not infer zero aggregate wealth.
- Single asset/class: valid fact; do not automatically label concentrated.
- Only unclassified assets: preserve count; value exposure depends on valuation
  completeness.
- Zero total aligned valuation: weights unavailable, not division by zero or
  fabricated zeros.
- Negative/short quantity: explicit unsupported/contract error until short
  semantics are approved.
- Missing prices/current values: partial result with coverage, never invisible
  substitution.

## 33. Provenance Requirements

A future response should expose the smallest useful set of:

- aggregate wealth reference month;
- position snapshot date;
- valuation basis and, when applicable, valuation/price date;
- server-resolved portfolio/account scope description;
- presentation currency/context;
- data source and observation/import provenance suitable for users;
- position count and valued-position count;
- classification coverage/unclassified count;
- completeness and temporal-alignment status.

Internal run IDs may remain server/audit details unless needed for diagnostics;
user responses should not leak technical identifiers without product value.

## 34. Read Model / Engine Options

| Option | Assessment |
|---|---|
| A. Consume existing Investments outputs directly | Rejected: mixed valuation bases, float/browser math, optional account scope, and ungoverned labels |
| B. New read model only | Insufficient if it merely relocates ambiguous calculations |
| C. New deterministic engine + read model | Viable once certified position facts/valuation are supplied |
| D. Combination of guarded query/resolver, pure engine, and response read model | Recommended |

Recommended architecture:

```text
authenticated request
  -> guarded Portfolio Intelligence source query
  -> one position snapshot + one separately identified aggregate wealth fact
  -> immutable Decimal inputs
  -> pure composition/concentration engine
  -> read model with facts + provenance + completeness
  -> string-safe API response
```

Reuse ADR-023 ownership/provenance patterns and the existing aggregate wealth
source. Do not force the aggregate Planning resolver to become a position
repository, and do not duplicate Planning/FIRE projection math.

## 35. API Design Considerations

No endpoint shape is locked. Plausible options are:

- one read-only summary endpoint containing composition and compact provenance,
  plus a separate evolution endpoint for ranged monthly history; or
- one summary response with an optional bounded history collection.

Separate endpoints keep grains and payloads clearer; one endpoint simplifies
the first screen but couples monthly history to position composition. Both must
be authenticated, server-scoped, read-only, Decimal-string based, and explicit
about dates/completeness. An arbitrary client `account_id` selector should not
be accepted under the current ownership model.

## 36. Frontend Authority Boundary

The frontend may format and present server facts. It must not:

- sum position values or allocation shares;
- calculate weights, top-N, performance, alpha, yield, or score;
- derive status/labels from hard-coded thresholds;
- coerce financial response strings to `Number` as authority;
- fill missing values or mix snapshot dates;
- use chart logic as a financial engine.

Any future chart library is presentation-only. AI/LLM may later explain
certified facts but never calculate them.

## 37. Security / Ownership

The future API must require existing authentication and reuse/extend the
single-user guard established by ADR-023. It needs a server-side resolution from
authenticated user to the one eligible investment scope, including ambiguity
and cross-user fail-closed behavior.

The current Investments optional account filter is insufficient. No client
selector, broker picker, or account ID should bypass ownership semantics. The
current live `accounts` schema mismatch reinforces the need for a guarded
source reader rather than an ORM assumption.

## 38. Performance Considerations

The inspected scale is small: 28 positions in the latest snapshot and 49
monthly portfolio rows. A bounded query plus group-by/top-N calculation can run
deterministically on demand without materialization. Avoid N+1 asset/quote
lookups; join asset metadata in one query and do not call yfinance per row in a
certified request.

Materialized read models or new tables are not justified by current evidence.
Query plans and payload bounds should be tested when the contract is locked.

## 39. Existing Test Coverage

Existing coverage includes:

- Planning portfolio source ownership, latest-as-of selection, provenance,
  source consistency, and read-only behavior;
- basic Investments allocation/evolution/dividend/asset-detail mappings;
- market quote normalization and caching;
- MyProfit parsing and import paths;
- Planning/FIRE API use of aggregate portfolio wealth.

Important 10.5 gaps:

- no certified position-scope/ownership resolver tests;
- no same-date/same-basis valuation completeness invariant;
- no reconciliation behavior between aggregate and positions;
- no Decimal allocation/top-N engine tests;
- no taxonomy/unknown/currency policy tests;
- no empty/zero/negative/missing-value contract vectors;
- no cashflow-aware performance engine tests;
- no frontend tests protecting existing Wealth metric authority;
- current allocation mocks do not exercise mixed valuation or completeness.

## 40. Historical Debt Interaction

The two known failures
`test_get_asset_detail_success_with_governance_value` and
`test_get_asset_detail_success_with_market_data` concern MagicMock/string
sorting in the asset-detail timeline. They remain unchanged historical debt.

They do not block the recommended MVP because it should not reuse the
asset-detail timeline code path. They become a dependency risk only if 10.5-B
chooses to build on that endpoint/timeline, which this audit recommends against.

## 41. Contract Risks

1. Treating aggregate monthly wealth as the sum of current positions without a
   proven invariant.
2. Mixing monthly portfolio, daily position, live quote, and import times.
3. Calling wealth growth performance without cashflow-aware semantics.
4. Reusing mixed cost/market fallback as certified valuation.
5. Losing precision through float/JavaScript Number paths.
6. Treating heuristic asset class/currency fields as complete exposure facts.
7. Exposing arbitrary account IDs despite absent ownership relations.
8. Converting current UI scores/thresholds into accepted policy accidentally.
9. Duplicating Dividends, Insights, Planning, FIRE, or future Rebalancing
   ownership.
10. Presenting imported benchmark/return values as locally certified math.
11. Ignoring future-dated income events in as-of semantics.
12. Treating missing canonical top-level documents as if reviewed.

## 42. User Decisions Resolved

### Decision 1 — Position valuation authority for the value-weighted MVP

**Resolution:** `APPROVED — OPTION A`.

**Question:** Which source should become the canonical value per position?

**Context:** Provider `total_atual` reaches the parser but is discarded for most
assets; the current API fills gaps with quotes or average cost. Without one
authority, allocation and concentration are unsafe.

**Option A — Persist the imported provider current total for every position
with explicit snapshot/observation semantics.**

- Pros: aligns with the imported position snapshot; broad class coverage; no
  request-time market dependency; easiest completeness/reconciliation audit.
- Cons: requires an import/persistence correction and explicit provider
  semantics; may still differ from monthly aggregate wealth.

**Option B — Value positions from live market data.**

- Pros: potentially fresher listed-asset values.
- Cons: partial fixed-income coverage; stale/provider failures; missing
  historical FX; current hard-coded FX fallback is unacceptable; mixed timing;
  more operational complexity.

**Option C — Ship a count/history-only first MVP.**

- Pros: uses current safe facts without new valuation authority.
- Cons: excludes asset/class weights and concentration, reducing product value
  and overlapping the existing evolution view.

**Approved direction:** Preserve MyProfit `total_atual` comprehensively with
governed snapshot/observation semantics, expose completeness, and keep
`portfolio_snapshots.patrimonio` and the position-valued total as distinct
facts until a reconciliation invariant is formally proven. Live-market
valuation is not the MVP authority.

### Decision 2 — Imported performance and benchmark facts in the MVP

**Resolution:** `APPROVED — OPTION A / DEFER`.

**Question:** Should the MVP display provider-reported returns/benchmarks before
a certified FINANALYTICS performance engine exists?

**Context:** The data is persisted, but its cashflow, compounding, date, and
currency methodology is not governed locally. Current frontend rebasing adds
unapproved math.

**Option A — Defer all performance/benchmark presentation.**

- Pros: strongest semantic safety; prevents wealth growth from being presented
  as return; keeps MVP focused on composition.
- Cons: removes familiar performance context from the new surface.

**Option B — Display raw provider-reported fields as contextual facts only.**

- Pros: preserves useful imported context without claiming a local engine.
- Cons: still requires exact labels, provenance, nullability, and a prohibition
  on rebasing/alpha/CAGR derivation; users may still infer comparability.

**Approved direction:** Defer TWR, MWR/XIRR, CAGR, total return, alpha,
cashflow-adjusted return, derived performance, benchmark comparison, and
MyProfit-reported return as Portfolio Intelligence authority. Historical
portfolio snapshots may support wealth evolution only.

No user decisions remain for 10.5-A. Scores, target allocation, risk metrics,
dividend duplication, international exposure, and top-N configurability retain
the audit's exclude/defer defaults. Fixed top-3 and top-5 facts are sufficient
once the approved value-weighted source is implemented and validated.

## 43. Recommended Next Step

After Phase 10.R7 closes the Wealth OS realignment, Phase 10.5-B should lock:

- the single position-valuation authority and its completeness semantics;
- the exclusion of performance and benchmark metrics from the MVP;
- exact Decimal precision and rounding;
- temporal alignment, empty/partial/error semantics;
- guarded source query and response provenance;
- the final minimal metric list and API/read-model boundaries.

`PAUSED — PHASE 10.5-B PENDING WEALTH OS REALIGNMENT`
