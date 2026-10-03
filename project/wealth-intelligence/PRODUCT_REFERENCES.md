# Product References — Wealth OS

**Status:** `CANONICAL REFERENCE CATALOG / NON-NORMATIVE`

**Reviewed:** 2026-10-02

These references are product inspiration, not financial-methodology or visual
specifications. FinAnalytics must not copy branding, proprietary text, assets,
or layouts. A useful interaction pattern becomes eligible only after its data,
authority, precision, temporal, privacy, and ownership contracts are approved.

This file owns external product inspiration. It is not a roadmap, feature
approval, methodology contract, or proof that a referenced interaction has been
fully observed. `MASTER_PLAN.md` and `ARCHITECTURE.md` may link here but must not
duplicate the catalog.

## Reference matrix

| Reference | URL | Pattern learned | Possible FinAnalytics application | What not to copy | Related future phase |
|---|---|---|---|---|---|
| Mais Retorno — Asset Comparator | https://maisretorno.com/app/comparador-ativos | Search-first entry, explicit selected assets, side-by-side analysis | One reusable comparator under **Tools**, with certified facts, comparable dates, and saved criteria only after persistence is contracted | Proprietary indicators, ranking logic, copy, ads, or visual layout | 10.R3 / post-10.5 |
| Mais Retorno — Fund Comparison | https://maisretorno.com/comparacao-fundos | Discovery followed by comparable dimensions and progressive detail | Fund/asset comparison through one normalized external-context boundary | Treating heterogeneous products or unavailable fields as directly comparable | 10.R3 / post-10.5 |
| Mais Retorno — Portfolio Simulator | https://maisretorno.com/app/simulador-carteiras/novo | Build a hypothetical allocation, compare scenarios, keep simulation distinct from holdings | Portfolio laboratory under **Tools**, separate from the governed real portfolio | Its financial methodology, benchmark assumptions, or simulated portfolio as reality | Post-10.5 / 10.R6 |
| Mais Retorno — Saved Comparisons | https://maisretorno.com/app/comparacao-favorito | Resume and organize prior comparisons | Saved comparison criteria after ownership/lifecycle/versioning are approved | Browser-only persistence or silent stale results | Post-10.5 |
| Mais Retorno — API Profile | https://maisretorno.com/app/meu-perfil/api | Provider/integration configuration as account-level capability | Settings > Integrations showing status, freshness, scopes, and masked identifiers | Client-side plaintext credentials or provider-specific settings pages | 10.R3 / 10.R4 |
| Investidor10 | https://investidor10.com.br/ | Search/discovery hub; portfolio, rankings, target price, tracker, dividend agenda/radar, comparator, results calendar, material facts, lists, IPO calendar, news | Separate personal portfolio context from discovery tools; prioritize Watchlist, asset search, agenda, relevant events, and comparator after data contracts | Commercial upsells, opaque rankings/scores, recommendations, or feature-for-feature duplication | 10.R3 / 10.5+ |
| Valor Investe — Fixed-Income Calculator | https://infograficos.valor.globo.com/calculadoras/calculadora-de-renda-fixa.html | Reference rates visible before calculation; editable assumptions; inputs separated from deterministic results | Smart Defaults card showing reference, source/date, explicit use/override, then backend-calculated output | Using the page's formulas/rates as FinAnalytics authority or equating current rates with future returns | 10.R3 / Tools |
| ETFs Brasil — Portfolio Simulator | https://www.etfsbrasil.com.br/simulador-de-portfolios | Up to three portfolios side by side, inline allocation controls, clear 100% totals, shared parameters, scenario comparison | Compact multi-scenario allocation laboratory with user-visible composition and deterministic comparison | Imported backtest/risk methodology, asset universe, rankings, or performance claims | Post-10.5 / Tools |

## Pattern decisions

- **Adopt conceptually:** search-first discovery, progressive disclosure,
  side-by-side comparison, inline scenario controls, visible composition,
  shared parameters, saved criteria with lifecycle, and source/freshness labels.
- **Defer pending contracts:** rankings, screeners, target prices, recommended
  portfolios, backtests, risk metrics, news relevance, and alerts.
- **Reject as authority:** opaque scores, commercial recommendations, hidden
  assumptions, frontend financial calculation, and historical performance used
  as an automatic expected return.
- **Navigation implication:** calculators/comparators belong to a coherent
  `Tools` area but their engines remain reusable from contextual flows.

## Observation limitations

The public Investidor10 and ETFs Brasil surfaces were directly observable.
Several Mais Retorno application routes required JavaScript or authentication;
their public/indexed descriptions confirmed the high-level comparator,
simulation, saved-comparison, and portfolio-management patterns but not every
logged-in interaction. The Valor interactive page blocked automated access, so
R0 records only the user-designated visible-reference/editable-assumption
pattern and does not claim formula or implementation findings.
