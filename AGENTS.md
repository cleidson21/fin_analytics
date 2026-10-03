# FinAnalytics Agent Guide

## Read before writing

1. Read `project/wealth-intelligence/README.md`, then the canonical owner for the concern.
2. Check `CURRENT_STATE.md`, `MASTER_PLAN.md`, `IMPLEMENTATION_ROADMAP.md`, applicable accepted ADRs, and any `LOCKED` phase contract.
3. Inspect code, tests, database evidence, documentation, and Git state. Status text never overrides repository reality.
4. In `frontend/`, also follow `frontend/AGENTS.md`. Nested instructions add local rules; they cannot weaken this file.

## Document authority and conflict resolution

Use this order when two documents conflict:

1. accepted ADR or `LOCKED` contract for its explicit scope;
2. the canonical concern owner listed below;
3. `CURRENT_STATE.md` for verified present reality;
4. `MASTER_PLAN.md` for product direction;
5. `IMPLEMENTATION_ROADMAP.md` for the active queue;
6. phase audits and research as evidence;
7. documents marked `SUPERSEDED / HISTORICAL`.

Canonical owners under `project/wealth-intelligence/`:

- product vision and long-term direction: `MASTER_PLAN.md`;
- current repository reality: `CURRENT_STATE.md`;
- active phase order and dependencies: `IMPLEMENTATION_ROADMAP.md`;
- cross-cutting architecture and product information architecture: `ARCHITECTURE.md`;
- data semantics, provenance, and source authority: `DATA_AND_SOURCE_OF_TRUTH.md`;
- frontend and UX principles: `UI_UX_PLAN.md`;
- AI architecture and runtime boundary: `AI_AND_LLM.md`;
- security and privacy: `SECURITY_AND_GOVERNANCE.md`;
- external product inspiration: `PRODUCT_REFERENCES.md`;
- validation philosophy: `TESTING_STRATEGY.md`;
- accepted decisions: `DECISION_LOG.md`;
- phase-specific truth: the applicable locked contract or audit.

Before creating a document, prove that no existing owner can carry the concern. Audits preserve evidence; they do not become permanent duplicate specifications. Link to an owner instead of copying it.

## Architecture boundaries

- Do not change a `LOCKED` contract without an explicit reconciliation task.
- Engines calculate. Governed data/read models expose facts. Frontend presents. AI interprets and orchestrates approved capabilities.
- Preserve `Decimal` through financial authority and string contracts. Floats and JavaScript `Number` are presentation-only where explicitly approved.
- Reuse deterministic engines and existing provider/read boundaries. Never create a second engine for an existing capability.
- Before adding an input, check whether the system already knows the semantically correct fact, can derive it deterministically, or has an appropriate external reference.
- An empty form is a fallback, not the default product experience.

## Context, external data, and AI

- Distinguish `DECLARED`, `OBSERVED`, `DERIVED`, `EXTERNAL_OBSERVATION`, `EXTERNAL_EXPECTATION`, `ASSUMPTION`, and `USER_OVERRIDE`. There is no universal precedence between them.
- Every smart value exposes source, meaning, scope, and freshness. Assumptions remain explicit and editable where appropriate.
- External data never silently replaces governed internal facts.
- AI receives minimum-necessary context and uses approved tools/services. It does not query arbitrary tables, calculate financial truth, or write financial records autonomously.
- Secrets remain server-side. Never persist API keys, credentials, tokens, CPF, phone, or unnecessary financial/personal data in frontend storage or prompts.

## Git, scope, and validation

- Preserve authorized dirty-worktree baselines. Never stash, reset, clean, restore, or rewrite unrelated work.
- Work only inside the explicit phase. Do not stage, commit, push, tag, migrate, or install dependencies without authorization.
- Validate in proportion to risk and independently of status claims. Backend tests run from repository root with `python -m pytest`.
- Stop on unexpected worktree changes, source-of-truth ambiguity, contract gaps, material user decisions, or scope requiring new authorization.

## Development-model guidance

- Architecture and financial contracts: GPT-5.6 Sol High.
- Hard reconciliation: GPT-5.6 Sol Extra High when justified.
- Frontend implementation: Sonnet 4.6.
- Independent product/UX critique: Opus 4.6 in a separate review context.
- Mechanical documentation and Git work: a lower-effort model when the task is deterministic and safe.

Model names are workflow guidance, not architectural dependencies.
