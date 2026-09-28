# Planning UX & Simplicity Contract

**Status:** LOCKED — READY FOR IMPLEMENTATION

**Decision:** POST-10.3-UX-A / ADR-024

**Locked:** 2026-09-26

**Scope:** post-10.3 frontend experience; no financial-engine, API, persistence, FIRE, Portfolio Intelligence, or LLM implementation

---

## 1. Authority and non-negotiable boundaries

This contract changes how Planning is entered and presented, not what Planning means.

- The backend remains the only financial authority.
- API money and rates remain exact `DecimalString` values.
- Each scenario has exactly one explicit initial-wealth source.
- The ADR-020 nominal/real matrix, Goal applicability, Scenario Comparison ordering/reference semantics, and ADR-023 portfolio semantics remain unchanged.
- The browser may normalize human text into the existing request contract, but it may not calculate projections, target crossings, required contributions, scenario deltas, or certified wealth.
- MyProfit means investment portfolio wealth, not net worth, and is never read through a browser-side Investments shortcut.
- No financial return, inflation, contribution, target, or horizon is silently invented.
- No persistence is introduced by this refinement.

## 2. Official product direction — Quiet Financial OS

The official direction is **Quiet Financial OS**:

- structural minimalism in navigation and input;
- selective premium finish in typography, spacing, color, and state transitions;
- analytical density only after a result exists;
- calm, factual language;
- no landing-page hero, decorative gradient, card wall, or ornamental animation;
- a stable shell able to receive future FIRE, Portfolio Intelligence, and Copilot capabilities without multiplying technical tabs.

The interface should feel organic and responsive to user intent, but remain a working financial instrument rather than a marketing surface.

## 3. Wealth Intelligence page chrome

The Wealth Intelligence top navigation is the visible page identity. Child pages must not repeat the same location as eyebrow, breadcrumb, visible H1, description, and capability title.

### Planning

- Remove the visible `WEALTH INTELLIGENCE` eyebrow.
- Remove the visible `Planejamento Financeiro` heading and architectural description.
- Keep one semantic page heading, `Planejamento Financeiro`, as `sr-only`.
- Make the three-intention control the first visible element.
- Do not repeat the active intention as a large card title when the control already supplies that context.

### Financial Health

- Apply the same rule: remove the visible eyebrow and repeated page title.
- Keep `Saúde Financeira` as an `sr-only` H1.
- The reference-month control and page actions become the primary top row.
- This contract changes page chrome only; it does not redesign Health modules.

Breadcrumbs remain available only where hierarchy cannot be inferred from persistent navigation. Planning and Health do not need a visual breadcrumb.

## 4. Copy contract

Every visible sentence belongs to one of four classes:

| Class | Purpose | Treatment |
|---|---|---|
| A. Decision | Helps the user choose or interpret an outcome | Keep close to the control/result |
| B. Context | Prevents a likely misunderstanding | Keep short; reveal progressively when possible |
| C. Provenance | Identifies the certified origin and time context | Compress into chip/details |
| D. Implementation detail | Explains internal architecture | Remove from the product surface |

Remove primary-UI text such as `backend certificado`, `sem recálculo no navegador`, `solver`, `ordem enviada`, `resultado certificado`, and explanatory statements about no ranking. Those guarantees remain in documentation and tests.

Use factual verbs: `Simular`, `Ver quando alcança`, `Calcular aporte`, `Analisar meta`, `Comparar`. Do not use advisory language such as `melhor`, `ideal`, `recomendado`, or `vencedor`.

## 5. Information architecture — three user intentions

The five certified capabilities remain five endpoints and five result contracts, but the interface exposes three user intentions:

1. **Simular** — Forward Projection.
2. **Objetivo** — a small task switch with:
   - `Quando alcanço?` — Target Achievement;
   - `Quanto aportar?` — Required Contribution;
   - `Meta existente` — Goal Planning.
3. **Comparar** — Scenario Comparison.

The inner task switch under `Objetivo` is not a second global tab bar. It appears only while that intention is active. Deep links and browser history should retain the selected intention/task without persisting a financial scenario.

## 6. Default common flow

A common projection asks for the minimum information that cannot be obtained structurally or from a certified source:

1. explicit initial-wealth source;
2. monthly contribution;
3. expected annual return, entered as a percentage;
4. horizon in months.

When the source is MyProfit, no wealth amount is requested. When the source is Goal current amount, the owned Goal is selected. When the source is manual, the amount is requested.

`as_of_date`, manual `observed_at`, return/output configuration, and fixed operational settings leave the common flow under the rules below. The source never becomes implicit.

## 7. Defaults and advanced options

### Context defaults

- `as_of_date`: today at submit time.
- manual `observed_at`: timestamp at submit time.

### Operational defaults

- `rate_basis = EFFECTIVE_ANNUAL`.
- `contribution_timing = END_OF_MONTH`.

These are the only supported values and do not require editable common-flow controls.

### Interpretation default

The default display contract is `NOMINAL → NOMINAL`. It is permitted only because the active state remains visible as a compact summary such as `Valores nominais · sem descontar inflação`, with a direct route to Advanced. It must never be an undiscoverable hidden assumption.

### Prohibited defaults

There is no default wealth, contribution, return, inflation, target, or horizon. Archetypes do not fill rates.

### Advanced disclosure

Advanced contains:

- return type and output mode;
- inflation only for `NOMINAL → REAL`;
- explicit `as_of_date` override;
- explicit manual `observed_at` override;
- optional scenario archetype metadata;
- read-only disclosure of annual-effective rate basis and end-of-month contribution timing.

It displays a compact state summary and a visible accent when any value differs from the standard state. `REAL → NOMINAL` remains disabled. Switching away from `NOMINAL → REAL` removes inflation from the request, regardless of stale UI text.

Target basis is derived from output mode for generic Target, Required, and comparison-target requests because the certified contract requires equality. Goal Planning is different: Goals do not certify whether their stored target is nominal or real, so the user must explicitly declare the Goal target basis in the main Goal task. It cannot be silently inferred.

## 8. Temporal semantics

### Data-base (`as_of_date`)

- Default mode is `AUTO_TODAY`.
- The value is captured at every submit from the browser's local civil date.
- Construct `YYYY-MM-DD` from local calendar components; do not use a UTC conversion such as `toISOString().slice(0, 10)`.
- If the user selects an Advanced override, that explicit date remains stable until cleared.
- The submitted/result date remains visible after execution.

This is a temporal context default, not a financial assumption. A visibly incorrect device date can be overridden.

### Manual-source `observed_at`

- Default mode is `AUTO_SUBMIT`.
- At submit, the interface captures a fresh absolute ISO-8601 timestamp.
- Page-load or capability-activation timestamps are prohibited because they become stale.
- The user may enter a historical observation timestamp under Advanced.
- Auto mode means the user is attesting that the entered manual amount is current at submission.

Portfolio `observed_at` remains `null`; its technical snapshot-version timestamp is never substituted.

## 9. Brazilian string-safe financial presentation

### Money display

Primary textual money formatting must never use `Number`, `parseFloat`, `Intl.NumberFormat(number)`, or another binary floating-point round trip.

The formatter validates and operates on the canonical decimal string: split sign, integer, and fractional digits; group the integer digits in threes; pad the certified cent fraction to two positions.

Examples:

| API truth | UI |
|---|---|
| `112594.46` | `R$ 112.594,46` |
| `200` | `R$ 200,00` |
| `-1454.18` | `-R$ 1.454,18` |

Money is not silently rounded. Input with more than two declared decimal places is invalid. If an unexpected response violates the certified money contract, the interface shows a safe unavailable value and records a diagnostic rather than altering the amount.

### Rate display

Rate display shifts the decimal string by two places and rounds only the presentation string, never the stored/API truth.

- Annual user assumption and applied annual rate: two percentage decimals, e.g. `0.08` → `8,00% a.a.`.
- Derived monthly rate: four percentage decimals, e.g. `0.006434030110003...` → `0,6434% a.m.`.
- Presentation rounding is deterministic decimal `ROUND_HALF_UP` implemented on digit strings.
- The full canonical rate remains available in an accessible detail/title for audit, but not as the primary value.

### Dates

- Day-level display and input: `DD/MM/AAAA`; API: `YYYY-MM-DD`.
- Accept only complete, valid Gregorian dates.
- Month bucket: `MM/AAAA`; `reference_month` never receives a fabricated day.
- Technical date-times use pt-BR date and time with an explicit timezone representation where available.

## 10. Brazilian input adapters

Adapters keep an editable display string separate from the canonical request string. They perform exact lexical transformation, not financial calculation.

### Money input

Accepted examples:

- `1000`
- `1.000`
- `1.000,50`
- `R$ 1.000,50`

Rules:

- optional `R$`, spaces, and one leading sign are normalized;
- comma is the only decimal separator;
- dots are grouping separators and every group after the first must contain exactly three digits;
- `1000.50` is rejected as ambiguous, with `Use vírgula para centavos`;
- exponent notation, duplicated signs/separators, invalid grouping, and more than two decimal digits are rejected;
- no silent rounding or truncation;
- `1.000,50` produces canonical `1000.50`.

The mask may group on blur, but must not fight cursor movement while editing.

### Percentage input

The label is `Retorno esperado ao ano` or `Inflação esperada ao ano`, never `fração decimal`.

Accepted examples: `8`, `8,5`, `8%`, and a single-dot decimal variant such as `8.5` for tolerant paste. A comma and dot in the same percentage is invalid; grouping has no meaning in this field; exponent notation is invalid.

The exact textual decimal is shifted two places left:

| User text | Meaning | API fraction |
|---|---|---|
| `8` | 8% | `0.08` |
| `8,5` | 8.5% | `0.085` |
| `0,08` | 0.08% | `0.0008` |

No float and no rounding are used. Domain limits remain backend-owned. Extreme but structurally valid rates may receive a non-blocking warning, never an automatic correction.

## 11. Errors and form preservation

- Lexical/required errors appear beside the field and connect through accessible error semantics.
- A safe API `422` location is mapped to the corresponding field when its path is recognized.
- An unmapped `422` uses `Revise os dados informados` at form level.
- `401` uses the existing authentication handling; missing/wrong-owner Goal uses the established unavailable state; `500` remains generic.
- Valid domain statuses are results, not errors.
- Submission errors preserve all entered values and any prior result, while clearly marking that the prior result belongs to the previous successful input.
- MyProfit unavailability never becomes zero, a changed date, or an automatic manual-source fallback.

## 12. Source-selection experience

Source selection is explicit and uses human labels:

- `Carteira de investimentos MyProfit`
- `Informar patrimônio inicial`
- `Valor atual de uma meta`

The helper for MyProfit is `O valor será obtido ao simular.` A secondary disclosure clarifies `Carteira de investimentos; não representa seu patrimônio total.`

There is no preview request in this implementation contract. After a response, the certified initial wealth is shown normally. Switching source builds a discriminated selector so stale amount, observation time, Goal ID, account ID, and provenance cannot cross variants.

## 13. Goal experience

Goal selection shows server-owned name, type, lifecycle status, target, and deadline as context. The Planning request continues to send the Goal path identity, source selector, assumptions, and explicit target basis only; the client does not certify Goal money.

- Goal current amount and MyProfit remain distinct one-source choices.
- Goal target and current amount are not re-entered.
- Goal applicability and final status remain backend-owned.
- The Goal deadline is displayed but is not silently reused as projection horizon: doing so would prevent analysis beyond the deadline and could erase `PROJECTED_LATE` semantics.
- The user still chooses an analysis horizon under the current contract.
- Goal planned contribution is displayed as a Goal fact but is not silently copied into the scenario contribution.

An optional `Usar prazo/aporte da meta` preset requires the separate mini-contract in section 20 because its horizon and contribution semantics must be explicit.

## 14. Scenario Comparison — shared context plus differentiators

The current repeated full form is replaced conceptually by one shared context and compact scenario cards.

### Shared comparison context

- `as_of_date`;
- horizon months or target date;
- output mode;
- fixed `END_OF_MONTH` timing;
- fixed `EFFECTIVE_ANNUAL` rate basis;
- optional shared target and its basis, with presence controlled as one pair.

The UI materializes these shared values into every existing per-scenario API assumptions object. It does not change the endpoint.

### Scenario-specific fields

- initial-wealth source and source-specific selector;
- monthly contribution;
- expected annual return;
- return type;
- inflation only when that scenario is `NOMINAL → REAL`;
- label;
- optional archetype metadata;
- manual observation timestamp mode when relevant.

Initial source and return type remain per scenario because the certified engine permits them to vary. Their removal would reduce valid analytical capability. Scenario state is keyed by stable UI ID and isolated; editing one scenario cannot mutate another.

The user selects the reference explicitly. The interface may visually mark the reference and show signed backend deltas, but never ranks, names a winner, or recommends a scenario. Request and result order remain the user's order.

## 15. Result hierarchy

Results answer the active question before exposing implementation detail.

### Projection example

- Hero value: `R$ 134.035,93`.
- Headline: `Patrimônio projetado em 24 meses`.
- Secondary facts: initial wealth, total contributions, projected growth.
- Applied rates and provenance appear below the primary answer.

### Other capabilities

- Target: status plus `Alcançado em N meses` / factual non-achievement status.
- Required: `Aporte mensal necessário` as the primary certified amount, clearly distinct from the scenario template contribution.
- Goal: the certified Goal Planning status, target and timing context.
- Comparison: one neutral summary per scenario and deltas relative to the explicitly marked reference.

`Resultado certificado` is not a headline. Certification is a system property, not the user's question.

## 16. Provenance

Provenance remains available but visually secondary:

- compact chip, e.g. `MyProfit · set/26`;
- details/popover contains approved source, monthly reference, and import/version timestamp;
- manual source may read `Informado por você · agora` or its explicit observation date;
- Goal source identifies the selected Goal without leaking technical IDs.

`updated_at`/snapshot version is labeled `Versão importada/atualizada em`, never `Observado em`, `Posição em`, or another daily-valuation claim. Null portfolio `observed_at` is omitted. Raw account/run IDs are not main-interface content.

## 17. Charts and target visualization

Recharts remains the chart library. Existing certified `periods` and comparison projections remain the only trajectory source.

- BRL axis/tooltip formatting is isolated in the approved rendering-only numeric adapter.
- Textual summaries never consume chart numbers.
- Time axes use readable month/period labels.
- Ending wealth is primary; contributions and projected growth are secondary.
- Comparison keeps request order and visually identifies the explicit reference without suggesting superiority.
- A horizontal target `ReferenceLine` is permitted only when the target is already certified in the request/response.
- An achievement marker is permitted only from backend achievement period/date.
- The frontend never calculates target crossing.

## 18. Loading, empty states, motion, and accessibility

- Use skeletons shaped like the active form/result, reusing the Health pattern.
- Disable duplicate submission and expose progress through `aria-live` without replacing truth optimistically.
- Empty states contain no fake zero and no redundant architectural explanation.
- Motion budget is 150–250 ms for intent changes, Advanced disclosure, result crossfade, and small layout transitions.
- Prefer CSS/Tailwind transitions. No number ticker is allowed because it would require numeric financial truth; use a string-safe crossfade or no counter.
- Respect reduced-motion preferences.
- Intent/task/source controls have programmatic labels, keyboard navigation, visible focus, and hidden fields are not focusable.

## 19. Library policy

- **Core:** existing Tailwind CSS 4.
- **Components:** reuse the small existing `components/ui` layer and Radix/shadcn-compatible primitives selectively; do not scaffold a parallel design system.
- **Charts:** keep Recharts.
- **Motion:** no new Motion dependency for the initial refinement; existing CSS/Tailwind is sufficient.
- **Testing:** add Vitest as a dev-only dependency in UX-B1, subject to the implementation task's explicit dependency review, because the string-safe financial parsers/formatters require executable table-driven and property-style regression tests. No component-test framework is required initially.
- **Avoid:** daisyUI, Tremor, Magic UI collections, a second chart library, and TanStack Table where no data table exists.

## 20. Future small backend contracts

These are optional contracts, not prerequisites for the frontend-only implementation:

1. **Certified portfolio preview** — an authenticated, ownership/as-of-aware preview returning the same certified fact/provenance semantics as Planning. Until approved, the browser must not call Investments/MyProfit endpoints for a preview.
2. **Planning assumption references** — certified reference facts with `value`, `source`, `reference date`, `semantic type`, and an explicit user opt-in. Historical facts must be labeled as context, never forecasts.
3. **Goal-derived presets** — an explicit rule for applying Goal deadline/planned contribution to a scenario without destroying late-status semantics or confusing stored intent with a chosen assumption.

## 21. Assumption assistance and existing macro data

Future assistance may offer CDI, SELIC, IPCA, certified historical portfolio performance, and custom input. Selecting a reference is always an explicit user action; nothing fills expected return or inflation automatically.

The repository already contains MyProfit portfolio benchmark fields for historical CDI/IPCA/IBOV context. A `macro_indicators` schema stub and future BCB/SGS plan also exist, but no current certified/populated Planning assumption read model was found. Therefore:

- audit and certify existing governed data before adding another external source;
- do not fetch BCB directly from the browser;
- keep BCB integration in its already planned backend phase unless a smaller contract is approved;
- never promote a historical benchmark to a future assumption without user opt-in and disclosure.

Historical portfolio return requires a certified backend performance read model/engine that handles contributions and withdrawals (for example approved TWR/MWR semantics). A naive start/end CAGR in the frontend is prohibited.

## 22. Future extension points

- **FIRE (10.4):** enters through `Objetivo` and `Simular` as a new domain mode with explicit withdrawal/retirement assumptions; it does not require a new top-level technical tab in Planning.
- **Portfolio Intelligence (10.5):** supplies certified allocation, concentration, risk, and rebalance facts; it does not choose Planning returns automatically.
- **Copilot:** may construct a natural-language draft scenario and explain certified results. The user must review the explicit assumptions before submit. The LLM never calculates or silently persists truth.
- **Goal evolution:** FIRE, Portfolio Intelligence, Health, or Copilot may propose a draft Goal. Creation and persistence require an explicit user action through the Goal contract.

## 23. Persistence

`Retomar última simulação`, saved scenarios, history, favorites, and browser storage remain a future contract. No `localStorage` shortcut is approved. ADR-021 transient-first semantics remain in force.

## 24. Proposal classification

Each proposal is assigned exactly one category.

| Proposal | Category | Rationale |
|---|---|---|
| Remove redundant Planning/Health chrome | A. FRONTEND-ONLY — IMPLEMENT NOW | Semantic H1 remains; no domain effect |
| Reduce implementation-detail copy | A | Presentation only |
| Three user intentions | A | Maps to existing five endpoints |
| pt-BR string-safe money/rate/date primitives | A | Exact boundary adapter; no new financial truth |
| Field-level lexical/API errors | A | Existing error contract |
| Submit-time today/manual observation defaults | A | Temporal context made explicit in the same request |
| Visible nominal/nominal standard state + Advanced | A | Existing matrix preserved and discoverable |
| Shared comparison context | A | Materializes existing required-equal fields per scenario |
| Result hero and provenance compression | A | Existing response facts only |
| Recharts formatting/target line from certified facts | A | Presentation-only |
| Skeletons and restrained CSS transitions | A | Existing frontend capability |
| Certified portfolio preview | B. SMALL BACKEND CONTRACT — IMPLEMENT BEFORE 10.4 IF APPROVED | Requires same ownership/as-of guarantee as Planning |
| Planning assumption reference read model/endpoint | B | Requires certified facts, source/date/semantic metadata |
| Goal-derived deadline/contribution presets | B | Needs explicit stored-intent vs scenario semantics |
| Cashflow-aware historical portfolio return | C. FUTURE PHASE — 10.4 / 10.5 / Copilot | Requires a governed performance engine/read model |
| FIRE planning mode | C | Phase 10.4 |
| Allocation/risk/rebalance intelligence | C | Phase 10.5 |
| Copilot scenario drafting/explanation | C | Future LLM phase with certified context |
| Goal proposals from domain/AI | C | Future explicit-draft workflow |
| Planning persistence / resume | C | Requires a separate ADR/schema/lifecycle contract |
| Direct browser Investments/MyProfit preview | D. DEFER / REJECT | Breaks Planning trust boundary |
| Automatic return/inflation/target/contribution/horizon | D | Hidden financial assumptions |
| Ranking, winner, recommendation, score | D | Contradicts Scenario Comparison contract |
| Number-based text formatter/counter | D | Risks financial precision |
| Motion dependency in the first refinement | D | No demonstrated need beyond CSS transitions |
| Landing-page hero, gradient spectacle, UI kit stacking | D | Conflicts with Financial OS direction |
| Force common initial source or return type in comparison | D | Removes certified scenario variation |
| Direct BCB fetch or automatic macro assumption | D | Ungoverned source/forecast leap |
| Silent Goal creation or Goal-value reuse | D | Violates explicit user action/source semantics |
| `localStorage` scenario persistence | D | Bypasses ADR-021 |

## 25. Implementation microtasks

1. **UX-B1 — pt-BR financial input/output foundation**

   Add pure string adapters/formatters, date helpers, field-error primitives, and exhaustive automated tests. No Planning component migration until these primitives pass.

2. **UX-B2 — page chrome, copy reduction, and three intentions**

   Apply the semantic-heading chrome to Planning and Health; remove architectural copy; map three intentions to the five existing capabilities.

3. **UX-B3 — context defaults and Advanced options**

   Add submit-time temporal modes, visible nominal/nominal state, exact nominal/real behavior, and source-specific progressive disclosure.

4. **UX-B4 — Scenario Comparison shared context**

   Move required-equal values out of scenario cards, preserve per-scenario source/return fields and reference/order semantics, and prove no hybrid payload.

5. **UX-B5 — result hierarchy, charts, and provenance**

   Add answer-first heroes, pt-BR result formatting, compact provenance, readable charts, and certified target/achievement markers.

6. **UX-B6 — loading, microinteractions, responsiveness, and accessibility**

   Add skeletons, restrained transitions, reduced-motion behavior, keyboard/focus checks, and small-screen overflow fixes.

7. **UX-B7 — independent validation and stabilization**

   Validate payload parity, string precision, source switching, all five capabilities, manual pt-BR entry cases, charts, Health chrome, typecheck, focused lint, build, and manual UX smoke. Do not start FIRE.

Optional backend work must be contracted and scheduled separately before any frontend microtask that depends on it. None of the three proposed mini-contracts blocks UX-B1 through UX-B7.

---

## Locked outcome

The post-10.3 Planning refinement is a frontend-first, contract-preserving sequence. `UX-B1–UX-B6 = VALIDATED` after accepted manual reviews, including the B6 living-state and accessibility review. `UX-B7 = VALIDATED / CLOSED` after independent code, contract, static, frontend, and focused Planning-backend regression validation. The POST-10.3 UX cycle is `VALIDATED / CLOSED`: it preserves Planning truth without adding calculation, backend behavior, or decorative motion. Phase 10.3 remains `VALIDATED / CLOSED`; Phase 10.4 remains `READY / NOT STARTED`.
