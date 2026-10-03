# Security, Privacy & AI Governance

**Status:** `ACTIVE OWNER — CURRENT RISKS + LOCKED DIRECTION`

**Date:** 2026-10-02

## 1. Current verified state

- Authentication uses JWT and server environment configuration.
- The current frontend stores the access token and user JSON in
  `localStorage`; this is known browser-exposure debt.
- CORS is broad for local development and is not production hardening.
- Profile intentionally persists only display name, occupation, company, and
  tax regime in a browser record; CPF, phone, birthdate, income, and employment
  start are transient.
- Existing ownership models vary by domain. Planning's MyProfit source relies on
  the explicit ADR-023 guarded single-user/single-tenant invariant; it is not a
  general account-ownership relation.
- There is no production AI runtime, provider tool registry, or AI scheduler.

Do not infer universal endpoint protection or multi-tenant isolation from the
local deployment model. Every new contract must verify its own authentication,
ownership, and scope behavior.

## 2. Financial authority

- Financial records and certified facts are never written by AI.
- New read/write endpoints use the existing authentication mechanism and must
  fail closed on ownership ambiguity.
- Client-supplied account, portfolio, Goal, provider, or provenance identifiers
  are never authorization by themselves.
- Simulations are read-only and cannot mutate real state implicitly.
- External data and AI interpretations remain labeled and cannot overwrite
  internal facts.

## 3. Data minimization

Collect, persist, export, and disclose only what an approved feature needs.
Purpose, owner, retention, source, and deletion behavior must be explicit before
new Profile or Settings persistence is added.

AI context excludes by default:

- CPF, phone, birthdate, and unrelated work identifiers;
- credentials, tokens, hashes, and API keys;
- full account identifiers when an opaque scope is sufficient;
- raw transactions when certified aggregates answer the question;
- unrelated financial domains.

Profile is declared user context, not a ledger or AI memory. Observed income
candidates never mutate it automatically.

## 4. Secret policy

`JWT_SECRET`, Pierre/MyProfit credentials, and any Gemini/OpenAI/Ollama or other
provider credentials are secrets.

- Store them server-side in environment or approved secret storage.
- Never commit or log them.
- Never persist plaintext credentials in browser storage.
- Never expose them through `NEXT_PUBLIC_*`, public bundles, API responses,
  prompts, tool results, exports, or telemetry.
- Rotate a credential if exposure is suspected.

Future Settings may expose configured/unavailable status, provider name,
scopes, last success, and a masked identifier. Editable configuration requires
a backend secret workflow; a browser form alone is not acceptable.

## 5. External-content and prompt-injection boundary

Retrieved news, filings, analyst text, pages, and documents are untrusted data.
They require source/provenance, structural separation from instructions,
bounded content, safe rendering, and authorization-independent tool controls.

Pattern removal and HTML stripping may reduce risk but are not a complete
security boundary. The AI runtime must never gain arbitrary database, network,
filesystem, or record-write authority through retrieved content.

## 6. AI governance

If R4 implements an AI runtime, every call must be attributable to the user,
provider/model, approved tool set, context version/sources, timestamp, outcome,
latency, and validation result without logging secrets or unnecessary raw
financial context.

AI output:

- is labeled as interpretation;
- cites or identifies the context it used;
- preserves uncertainty and insufficient-data outcomes;
- cannot create financial facts or unsupported numbers;
- cannot perform autonomous trades, transfers, classifications, Goal changes,
  or provider configuration.

Any future recommendation capability requires a separate advice, methodology,
and liability contract.

## 7. Frontend safety

- Render AI/external text as untrusted content; avoid unsafe HTML injection.
- Sensitive values must not be placed in URLs, analytics, console logs, or
  persistent browser state.
- Placeholder Settings actions must not report durable success unless the
  server confirms it.
- Theme, notification, integration, and provider preferences need explicit
  persistence and privacy contracts.

## 8. Required validation

For each new external-context, Settings, Profile, or AI capability validate:

- authentication and wrong-user/non-enumeration behavior;
- server-owned scope resolution;
- minimum data exposure and logging;
- secret absence from bundles, storage, payloads, prompts, and errors;
- timeout, provider failure, malformed/untrusted content, and unavailable-data
  behavior;
- read-only/no-write boundaries where promised;
- retention, deletion, audit, and export semantics where persistence exists.

Production CORS, browser-token hardening, and a general multi-user account model
remain separate explicit work; R1 does not implement them.
