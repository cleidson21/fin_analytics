# AI & LLM Architecture

**Status:** `10.R1 HIGH-LEVEL DIRECTION LOCKED / RUNTIME NOT IMPLEMENTED`

**Date:** 2026-10-02

**Canonical responsibility:** current AI-runtime truth, AI authority/privacy
boundaries, and high-level provider/tool direction. Phase 10.R4 owns the exact
runtime and implementation contract.

## 1. Verified current state

No AI runtime is currently operating in the application.

- no Advisor service or route;
- no Insights generator/runtime;
- no Copilot;
- no OpenAI client/runtime;
- no Ollama integration/runtime;
- no scheduler for AI work;
- no provider abstraction or tool registry;
- `backend/integrations/gemini/classifier.py`, `models.py`, and `prompts.py` are
  empty files;
- AI-related tables, environment settings, and installed SDKs are scaffolding,
  not implemented capability.

Historical documents that describe providers, scheduled briefings, insight
storage, or advisor experiences are proposals unless a later R4 contract and
code explicitly implement them. The current frontend Wealth Intelligence hub
also contains future-facing AI copy; it does not prove runtime availability.

## 2. Locked role of AI

AI is a **consumer and orchestrator of deterministic capabilities and governed
context**. It may:

- interpret and explain certified facts;
- structure user intent;
- help the user configure a reviewable scenario;
- call approved read-only context and calculation tools;
- summarize sourced external context;
- surface relevant facts with uncertainty and provenance.

AI must not:

- calculate financial truth itself;
- query arbitrary database tables;
- create a parallel financial engine;
- write financial records autonomously;
- change Goals, transactions, positions, classifications, or assumptions
  without the explicit governed user workflow;
- convert external observations or expectations into internal facts;
- invent prices, news, consensus, reasons, or recommendations;
- receive or expose credentials.

## 3. Capability-oriented architecture

```text
User question or contextual action
  -> AI runtime
  -> approved tool registry
  -> deterministic service or governed context reader
  -> typed result with provenance
  -> AI interpretation
  -> labeled response with source/freshness context
```

Candidate capabilities include reading financial context or an owned Goal and
running the certified Planning or FIRE services. Reading Portfolio Intelligence
or normalized market context is unavailable until those capabilities exist.
The AI never reproduces tool calculations in prompt logic.

R4 will decide exact tool schemas, authorization, timeouts, error handling,
audit records, cost/token telemetry, context limits, and output validation.

## 4. Provider-aware direction

The future runtime may support **OpenAI, Gemini, and Ollama** behind an
abstraction. R1 intentionally does not lock:

- the protocol/interface;
- a required provider;
- provider parity;
- primary/fallback order;
- a model name;
- local versus cloud deployment;
- environment-variable names beyond existing reality.

Provider selection must not leak into financial-domain services or page-level
business logic. Model/provider availability is configuration state, not a
product truth.

## 5. Context and privacy

Use the minimum context necessary for the specific tool call or question.
Exclude by default:

- CPF, telephone, birthdate, and unrelated employment identifiers;
- passwords, hashes, JWTs, API keys, access tokens, and provider secrets;
- complete account identifiers when an opaque/user-safe scope is sufficient;
- raw transaction detail when aggregates answer the question;
- unrelated personal or financial domains.

Financial facts may be supplied only through approved context builders/tools
with source, scope, time, and completeness appropriate to the task. Profile is
not AI memory. Conversation or tool state must not silently become declared
context or financial truth.

## 6. Secret policy

Provider credentials are server-side only, using environment or approved secret
storage. They must never be:

- persisted in browser storage;
- embedded in a public Next.js bundle;
- returned in API payloads or logs;
- inserted into prompts or tool results.

Settings may eventually show provider name, configured/unavailable status,
scopes, last success, and a masked identifier. A backend configuration workflow
is required before any editable provider setup exists.

## 7. External-content safety

News, documents, analyst text, and other retrieved content are untrusted data,
not instructions. R4/R3 contracts must provide structural isolation,
provenance, bounded content, injection resistance, safe rendering, and
traceable failures. Sanitization alone is not an authorization boundary.

## 8. Output and advice boundary

AI output is interpretation and must be visibly labeled as such. Deterministic
services provide figures, statuses, dates, comparisons, and scenario results.
AI may explain those results but cannot silently change inputs or create
unsupported numerical claims.

Consultative interpretation is allowed within the supplied evidence. Any future
investment recommendation, target-price methodology, prescriptive portfolio,
or autonomous action requires a separate explicit contract; it is not included
in R4 or R6 by implication.

## 9. Access points

The conceptual channels are:

- a global Copilot;
- contextual `Ask AI` actions;
- briefing/explanation surfaces;
- smart-form assistance that leaves assumptions explicit for review.

The target is not a full duplicated chat on every page. No access point exists
in production today.

## 10. R4 boundary

Phase 10.R4 is an infrastructure foundation, not the complete Copilot product.
Its architectural scope is:

- provider abstraction and configuration strategy;
- approved read-only tool registry;
- authorization and minimum-context construction;
- structured outputs and auditability;
- privacy, secret handling, timeouts, errors, and cost/token telemetry;
- a minimal integration surface proving the boundary.

R4 must consume the R2 Smart Context and R3 External Context semantics. It does
not implement financial engines, Portfolio Intelligence, recommendation logic,
or the full R6 experience recomposition.

Historical provider/model/cost research remains available in repository audits
and infrastructure notes. It is non-normative and must be revalidated when R4
starts.
