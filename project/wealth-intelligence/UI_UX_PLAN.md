# Frontend & UX Direction — Wealth OS

**Status:** `10.R1 PRINCIPLES LOCKED / R5 IMPLEMENTATION NOT STARTED`

**Date:** 2026-10-02

**Canonical responsibility:** cross-product frontend and UX principles. Product
area ownership lives in `ARCHITECTURE.md`; exact Planning behavior remains in
ADR-024 and `PLANNING_UX_CONTRACT.md`; financial semantics remain in their
domain contracts.

## 1. Direction

The existing **Quiet Financial OS** direction remains useful and evolves toward
richer analytical experiences. The interface should preserve:

- clarity and strong information hierarchy;
- controlled density;
- progressive disclosure;
- accessibility and keyboard usability;
- answer-first result presentation;
- restrained motion;
- deterministic backend authority.

It should add, where the task benefits:

- contextual prefill and explicit `Use` actions;
- visible source, date, scope, freshness, and completeness;
- search-first discovery;
- contextual quick actions;
- inline scenario controls;
- side-by-side comparison;
- responsive analytical layouts;
- System/Light/Dark support through semantic tokens.

## 2. Smart input principles

### Known data before repeated input

If FINANALYTICS has an eligible, semantically correct value, the interface
should prefill it or offer it directly. Empty form entry is a fallback, not the
default experience, especially for Planning, FIRE, Goals, and future tools.

The UI must distinguish:

| Presentation | Meaning | Override behavior |
|---|---|---|
| Auto-filled fact | Governed internal or declared fact selected for the task | Source selection or edit through its owner; never hidden mutation |
| Reference suggestion | External observation/expectation or derived context offered for review | Explicit `Use` or dismiss action |
| Default assumption | Scenario premise, never a fact | Visible and editable before execution |

Every smart value should answer: where did it come from, when was it observed
or published, what does it represent, and can it be overridden?

### R2 declared and observed income states

The R2 UI must never merge declared salary with recurring transaction evidence.
Declared monthly gross income is an editable Profile fact. A recurring-income
candidate shows its signature meaning, evidence months, occurrence counts,
typical/minimum/maximum amounts, latest observation, freshness, and risk flags;
it offers explicit confirm, reject, and reset actions. Confirmation changes the
decision state, not the source transaction and not Profile. A stale confirmed
source remains visibly stale rather than disappearing or reverting silently.

### Form behavior

- Preserve the complete API/domain contract even when Advanced options are
  collapsed.
- Keep assumptions explicit and visually different from facts/references.
- Never carry stale hidden values across source or mode changes.
- User-facing financial text remains string-safe; browser numeric conversion is
  limited to explicitly approved rendering boundaries.
- Results remain visible during recalculation when their stale premise is
  clearly signaled.

## 3. Home and contextual actions

Future Home is a personal command center, not a directory of cards or a setup
form. It should primarily answer:

- Where am I?
- What changed?
- Am I progressing?
- What needs attention?
- What can I explore next?

Exact widgets are deferred. Valid conceptual actions include simulating a Goal
contribution, adjusting a FIRE assumption, inspecting portfolio concentration,
viewing upcoming income events, opening relevant market context, or asking the
Copilot about the current context. Actions must change context, scenario,
comparison, monitoring, analysis, or navigation; animation is not a substitute
for interaction.

## 4. Navigation migration

R1 locks the conceptual areas Home, Plan, Portfolio, Explore, Income, Monitor,
Market, Copilot, Tools, Profile, Settings, and Data & Governance. It does not
lock URLs.

- Existing routes and deep links remain operational.
- R5 owns shell/navigation implementation and must define migration/redirect
  behavior explicitly.
- Data & Governance remains accessible even if it becomes secondary to normal
  consumer journeys.
- Profile and Settings are reused; no `Profile V2`, `Settings V2`, Preferences,
  or standalone AI Settings route is planned.
- A reusable engine may appear in a contextual journey and in Tools without
  duplicating its calculation authority.

## 5. Discovery and tools

- Search-first is preferred for asset discovery, comparator, screener, and
  tracker workflows, not for every page.
- Tools should be discoverable from navigation, search, and contextual actions,
  rather than hidden only in deep menus.
- Side-by-side scenarios should share genuinely common parameters and keep
  scenario-specific assumptions explicit.
- Saved comparisons, watchlists, and scenarios need ownership, lifecycle,
  versioning, and freshness contracts. Browser-only state must not masquerade as
  durable truth.
- A portfolio simulator stays visibly separate from the governed real
  portfolio.

## 6. Theme target

The target is **System / Light / Dark**.

Migration is incremental and token-based:

1. define/verify semantic color, typography, spacing, elevation, and status
   tokens;
2. make the shell honor system/user preference;
3. migrate shared primitives and charts;
4. migrate product areas without rewriting their financial logic;
5. validate contrast, meaning, printing/export where relevant, and reduced
   motion in both themes.

The current presence of light/dark CSS variables does not mean theme support is
implemented; the live shell and many components still use hard-coded dark
utilities. R5 owns the exact design contract and implementation.

## 7. Analytical layout principles

- Lead with the answer or state, followed by supporting facts and then detailed
  provenance.
- Use tables for exact comparisons and charts for relationships/trends; do not
  hide exact values when precision matters.
- Keep source/freshness close to the value it qualifies.
- Show partial/unavailable data explicitly instead of fabricating zero.
- Keep comparison reference neutral; do not imply a winner unless a governed
  method owns that interpretation.
- Use color as supporting meaning, never as the only carrier of status.
- Prefer responsive reflow over horizontal compression of critical facts.
- Loading, error, empty, partial, stale, and insufficient-data states are part
  of the product contract.

## 8. Product-area UX boundaries

- **Plan:** Goals owns objective lifecycle, Planning owns deterministic
  scenarios/solvers, and FIRE owns the specialized independence journey. The UI
  composes them without merging engines.
- **Portfolio:** display only certified facts and completeness. Existing
  Investments browser heuristics, performance labels, and scores do not become
  authority through redesign.
- **Income:** reuse Dividends/event facts; do not duplicate yield calculations.
- **Market/Explore:** always label source, time, external-observation versus
  expectation, and comparability limits.
- **Profile:** show declared context and purpose-limited persistence; never
  imply that transient fields are saved.
- **Settings:** future categories are Security, Notifications, Appearance, Data
  & Privacy, Integrations, AI & Providers, and Market Data. Unimplemented
  controls must not simulate success.

## 9. AI interaction

Valid future access points are a global Copilot, contextual Ask AI, concise
briefing/explanation, and form assistance. AI content must be labeled and must
show the relevant source/freshness context. The user reviews explicit scenario
assumptions before execution.

Do not duplicate a full chat on every page. AI cannot calculate figures, hide
assumption changes, persist decisions autonomously, or expose secrets/personal
identifiers.

## 10. Product-reference boundary

`PRODUCT_REFERENCES.md` is the only canonical catalog of external product
inspiration. Reusable patterns include search-first entry, progressive detail,
saved comparisons with lifecycle, visible reference assumptions, inline
allocation controls, and side-by-side scenarios. External formulas, rankings,
scores, target prices, commercial placements, branding, or layouts are not
adopted automatically.

## 11. Validation expectations

R5 and R6 must validate:

- both themes plus system preference and persistence;
- keyboard, focus, semantics, contrast, and reduced motion;
- narrow and wide analytical layouts;
- all living states;
- exact frontend/API field parity;
- visible source/freshness/provenance;
- absence of browser-side financial authority;
- preservation of accepted Goals, Health, Planning, and FIRE behavior;
- route/deep-link migration behavior.

Exact component, token, breakpoint, widget, and route contracts are deferred to
R5/R6. This document intentionally does not promise a page or metric merely
because it appeared in an older mockup.
