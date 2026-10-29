# AI & LLM Architecture

**Status:** `10.R4-C CLOSED / PUSHED`

**Date:** 2026-10-28 — runtime status and governed evaluation plan reconciled

**Canonical responsibility:** current AI-runtime truth, AI authority/privacy
boundaries, and high-level provider/tool direction. Phase 10.R4 owns the exact
runtime and implementation contract.

## 1. Verified current state

Status and evaluation evidence below were reconciled on 2026-10-28. Execution
order is owned only by `IMPLEMENTATION_ROADMAP.md`; this owner defines the AI
boundary and tests, not a parallel roadmap. No provider was called in this task.

No AI runtime is currently operating in the application.

- no Advisor service or route;
- no Insights generator/runtime;
- no Copilot;
- no OpenAI client/runtime;
- no Ollama integration/runtime;
- no scheduler for AI work;
- R4-A provider-neutral contracts and the internal R4-B authorization,
  read-only tool, and minimum-context boundaries now exist, but there is no
  real provider adapter, router, or retry executor;
- R4-C immutable minimized audit/telemetry contracts, replaceable sink ports,
  deterministic volatile in-memory sinks, and audit fail-closed enforcement now
  exist, but there is no durable sink or external observability;
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

## 11. R4.0 approved runtime contract

R4.0 approves the provider-neutral foundation only. By itself it does not activate a
provider, install a model or SDK, call a remote API, expose an endpoint, create
a scheduler, or persist telemetry. The runtime must be one
infrastructure that reconciles the historical Gemini scaffolding; it must not
create a second Advisor or assume that a functional Advisor already exists.

The canonical flow is:

```text
authenticated internal use case
  -> authorization, privacy, and consent policy
  -> minimum certified context and allowlisted read-only tools
  -> evidence-based provider/model router and resilience controls
  -> one eligible provider adapter
  -> structured-output validation
  -> minimized audit/telemetry envelope
```

`AIProvider` is a domain-neutral port. Its eventual implementation must expose
bounded model discovery, health probing, generation, cancellation, and resource
closure without leaking SDK types into financial services. A request carries a
request ID, authenticated user scope, task kind, execution mode, data
classification, remote-processing authorization, required capabilities,
minimum context with certified source references, output schema, allowed tools,
token/cost ceilings, deadline, and policy version. A response carries the
provider and exact model identity/version or local digest, validated structured
output, cited certified sources, executed tool calls, token and latency usage,
cost when applicable, retries, fallback reason, outcome, and UTC timestamp.

Provider and model capability registries are separate. Provider capabilities
describe transport, health, structured-output, tool, privacy, and deployment
properties; model capabilities describe context/output limits, supported task
types, exact revision or digest, license, quantization, and measured evidence.
Availability is discovered and verified at runtime or at an authorized
preflight; no model ID is an eternal constant or financial-domain dependency.

Structured output is accepted only after schema and semantic-boundary
validation. Financial numbers originating in certified tools remain exact
Decimal strings with provenance. Invalid or incomplete output fails explicitly;
it cannot become a partial financial fact. The common error taxonomy must at
least distinguish invalid request/output, unauthorized task/tool/data,
privacy-policy rejection, no eligible provider/model, local runtime unavailable,
authentication, quota, rate limit, provider overload, timeout, network failure,
model unavailable, budget exceeded, tool failure, cancellation, and internal
failure, with transient/permanent classification and retry eligibility.

## 12. Execution modes, selection, resilience, and fallback

- `LOCAL_ONLY` is the default. If Ollama or an eligible local model is absent,
  it returns explicit unavailability; it never promotes the request to cloud.
- `REMOTE_ONLY` requires an eligible remote task and explicit remote-processing
  authorization. Provider integration alone is not that authorization.
- `HYBRID` is opt-in. It may consider a compatible local or remote provider
  only after privacy, consent, capability, token, budget, and policy gates pass.

The router first applies these hard gates, then ranks eligible candidates from
current health and measured quality, latency, cost, limits, and task fit.
Historical evidence may influence selection only when its dataset, model
revision, configuration, sample, and freshness are known. Time of day is not a
fixed routing rule before benchmark evidence exists.

Fallback is an explicit routing decision, not an exception shortcut. Gemini to
Ollama is allowed only in `HYBRID`, when the local model satisfies the original
task and output contract, and when the caller is informed of material quality
or capability differences. Ollama to Gemini is prohibited whenever the request
requires offline operation. If no compatible provider exists, the result is a
typed error or explicitly declared degraded outcome; limitations are never
hidden.

There is one retry controller across application and SDK. The initial baseline
is at most three total attempts, configurable downward, always inside one total
deadline, token ceiling, and cost budget. Only classified transient failures
may retry, using bounded exponential backoff with jitter and `Retry-After` when
valid. Authentication, policy, invalid request/output, exhausted daily quota,
hard budget, and incompatible/unavailable model errors do not retry blindly.
SDK retries must be disabled or incorporated into the same attempt accounting.

Circuit breakers are scoped by provider/model. Their initial thresholds,
observation windows, recovery periods, and half-open probes are experimental
values that require mocked validation and later calibration; they are not
operational settings authorized by this contract. Rate limits and concurrency
are bounded per provider/model/user scope. Cache is allowed only for an
idempotent, semantically equivalent request whose source freshness and access
scope remain valid.

Gemini handling must distinguish `429 RESOURCE_EXHAUSTED` caused by a
recoverable rate window from exhausted daily/project quota, and distinguish
both from `503 UNAVAILABLE` overload. Network failures and timeouts may be
transient; authentication, policy, unsupported model, and hard quota/cost
failures are permanent for the current operation unless verified evidence says
otherwise. No retry loop may consume tokens indefinitely.

## 13. Local provider contract and assisted Ollama gate

Ollama `0.40.5` is installed on the current Windows computer through the exact
`Ollama.Ollama` WinGet package. The package is registered and the executable
responds with the expected version. User-observed R4-D.1 evidence records the
user-scoped `LOCAL_ONLY` configuration. Qwen 3.5 4B `Q4_K_M`, Ollama model ID
`d8b0f5e9760c`, is installed with context `4096` and concurrency `1` for local
validation; no provider is activated in FinAnalytics. Any
artifact admitted for operational use must still be pinned by the required
exact digest and record its license, quantization, configuration, storage, and
verified effective limits.

Llama 3.2 3B and Llama 3.1 8B quantized candidates may seed that evaluation;
they are candidates only, not approved operational models. Their real
availability, license, digest, RAM/VRAM, CPU/GPU behavior, context, throughput,
latency, concurrency, storage, and energy implications must be reverified when
the gate runs.

**User-approved R4-D candidate priority (2026-10-16):** the first operational
evaluation candidate is Qwen 3.5 4B `Q4_K_M`; Qwen 3.5 9B `Q4_K_M` is the
second priority, subject to evidence for full-GPU execution or CPU/GPU offload.
This ordering authorizes neither download nor execution and elects no winner.
The confirmed host has a Xeon E5-2667 v4, 32 GB across four declared DDR4-2400
8 GB modules in declared quad-channel configuration, and an NVIDIA RTX 5060
with 8 GB VRAM. The theoretical main-memory bandwidth is at most 76.8 GB/s and
remains contingent on verifying the effective quad-channel configuration.
R4-D.3 must measure RAM, VRAM, GPU/CPU layer placement, latency, tokens/s,
context consumption, and quality under equivalent synthetic financial tasks.
Ollama remains the initial runtime; direct llama.cpp is only a future comparison.

The third candidate is **PrismML Bonsai 8B GGUF `Q1_0`**, explicitly
experimental and lower-priority than both Qwen 3.5 candidates. Its published
model card describes a Qwen3-8B-based architecture, not Qwen 3.5, with about
8.19B parameters, an approximately 1.16 GB GGUF file, and Apache 2.0 licensing.
The file size is not a total-runtime-memory claim: total VRAM, buffers, context
cache, and layer placement must be measured. Compatibility with Ollama `0.40.5`
is `NOT VERIFIED`; although the model card advertises an Ollama invocation, it
also documents Q1_0 kernels through a PrismML llama.cpp fork. Any compatible
llama.cpp installation or direct-runtime comparison requires a separate gate.
Primary evidence: [announcement](https://prismml.com/news/bonsai-8b),
[model card](https://huggingface.co/prism-ml/Bonsai-8B-gguf), and
[demo repository](https://github.com/PrismML-Eng/Bonsai-demo).

No published general benchmark establishes FinAnalytics suitability or
superiority. The external model-card BFCL result (`65.7`, versus `81.0` for
Qwen3-8B in the same published table) is an unfavorable tool-calling signal
that must be reproduced under the FinAnalytics contract before any operational
consideration. Equivalent, entirely offline future evaluation must cover
Portuguese and financial interpretation, validated structured JSON, exact
Decimal and provenance preservation, correct approved-tool selection,
abstention when evidence is missing, grounding and hallucination, tokens/s,
latency, total VRAM, and context consumption. No candidate wins without this
evidence.

**R4-D.2 user-observed validation (2026-10-16):** Qwen 3.5 4B `Q4_K_M`
(`d8b0f5e9760c`) ran through Ollama `0.40.5` in `LOCAL_ONLY` mode on the RTX
5060 through CUDA, with all `33/33` layers on GPU, context `4096`, and
concurrency `1`. With thinking off, the synthetic tests completed with
syntactically valid JSON; warmed generation was approximately `80-84 tokens/s`
and the tested warmed responses took approximately `3.5-4.9 seconds`. This is
technical-candidate evidence only: source fidelity still requires stricter
testing and the model is not certified for production.

With thinking on, JSON format and a `1800`-token allowance produced no final
answer and ended with `done_reason=length`; without JSON format and with a
`3000`-token allowance, the final answer was partial and again ended with
`done_reason=length`. Generation remained near `81 tokens/s`. Thinking on is
therefore `NOT APPROVED IN TESTED CONFIGURATION`; this does not authorize an
automatic token-budget increase or establish a universal model defect.
Intermittent GPU-discovery timeouts occurred during initial loads, followed by
successful initialization. Future validation must reject or explicitly handle
empty and partial responses and test sources, grounding, and financial
conclusions rigorously. No operational integration is authorized. R4-F still
requires its pre-execution guard and `DURABLE` audit before operational provider
or tool dispatch.

R4-D uses the following assisted execution checklist. D.0-D.3 are internal
steps of R4-D, not new normative phases unless the roadmap is later amended:

| Step | Authorized scope and future checks | Success criterion |
|---|---|---|
| R4-D.0 — Hardware & Environment Preflight | Read-only verification of the real OS, architecture, CPU, RAM, GPU, VRAM, driver, free disk, virtualization/runtime constraints, and local ports; compare eligible model requirements. On Windows, the assisted run may use system inventory commands such as `Get-CimInstance`, `Get-Volume`, and vendor diagnostics such as `nvidia-smi` when already present. Install and download nothing. | Evidence identifies the real environment, constraints, candidate envelope, and stop conditions without changing the machine. |
| R4-D.1 — Assisted Ollama Installation | After separate authorization, consult current official documentation, guide the OS-specific installation, verify service, PATH, exact version, local API, loopback binding, and firewall/exposure; explicitly disable cloud features and unintended remote access. | Ollama is versioned, healthy only on the approved local boundary, cloud-disabled, and not exposed beyond the authorized interface. |
| R4-D.2 — Local Model Setup | After a separate download authorization, choose model and quantization from D.0 evidence; verify official availability, license, exact digest, storage, and limits; test basic inference, validated JSON, and operation with external network unavailable. | The pinned model produces the required structured contract locally and remains usable offline within measured resource limits. |
| R4-D.3 — Performance & Adapter Validation | Measure cold/warm start, first-token and end-to-end latency, tokens/s, CPU/RAM/GPU/VRAM, effective context, initial bounded concurrency, cancellation, and adapter errors, with no unauthorized remote access. | Reproducible measurements establish a safe local operating envelope and the provider-neutral adapter passes mocked and authorized offline integration checks. |

At each assisted step the project must present the exact commands before they
run, explain expected output and side effects, and report objective pass/stop
criteria. This contract authorizes none of those installation, download, or
execution actions now.

## 14. Gemini remote-provider contract

Gemini has one adapter based on the current official `google-genai` SDK when
R4-E is separately authorized. Historical Gemini files and the installed
legacy package are scaffolding to reconcile, not permission to maintain
duplicate adapters. Exact SDK and model versions are verified and pinned at
implementation time rather than assumed here.

Authorization to integrate the adapter is separate from authorization to send
real financial data. Real financial data is ineligible for a free Gemini tier.
Any future remote use of such data requires a verified paid project, explicit
user opt-in, minimum-necessary payload, compatible provider data-use/retention
policy, server-side secret handling, cost limits, and a task-specific approval.
Without all gates, the request remains local or returns explicit
unavailability. API keys never enter code, prompts, client storage, documents,
tool results, or logs.

## 15. Read-only tools, context, and personalization

Tool access is server-side, authenticated, user-scoped, and deny-by-default.
The runtime receives an explicit per-request allowlist, validates every typed
argument and result, enforces a bounded call count and deadline, and audits the
authorization decision and outcome. Tools may expose certified read models or
deterministic engines; they cannot expose arbitrary SQL, unrestricted network
or filesystem access, provider-native built-ins, financial operations, or any
write capability in R4 Foundation. ADR-023 remains authoritative for initial
wealth, and R2/R3 source and provenance semantics remain unchanged.

Untrusted instructions from user or external content cannot alter system
policy, tool authorization, user scope, provider mode, or data classification.
Context builders structurally separate instructions from bounded sourced data,
sanitize rendered content, preserve provenance, and omit sensitive or unrelated
fields. The LLM does not recalculate wealth, returns, dividends, or any metric
owned by an Engine.

Initial personalization is limited to explicit, correctable user preferences
and retrieval of certified information. Any memory must be consented,
minimum-necessary, user-isolated, versioned, attributable, reviewable, and
deletable. Observed pattern, hypothesis, and recommendation remain distinct.
No sensitive-data learning, implicit memory, weight update, training pipeline,
or fine-tuning is authorized. Local Llama inference does not change model
weights. Any analytical model or later fine-tuning requires a separate contract
and gate.

## 16. Telemetry and benchmark contract

The minimized logical telemetry envelope precedes persistence and real
execution. It includes request ID, opaque user scope, provider/model/version or
digest, routing decision and policy version, permitted tool-call metadata,
latency, token counts, cost when known, retries, classified error, fallback
reason, outcome, UTC timestamp, and certified source references. Raw prompts,
full financial context, personal data, credentials, tokens, and API keys are
excluded or redacted before emission. Telemetry failure cannot expose payloads
or silently authorize a provider.

The persistence medium, reuse of historical `ai_runs`, schema, retention,
access controls, deletion, and definitive sampling remain a separate gate. No
database, migration, or operational retention value is implied by this
contract.

Benchmarking is a harness separate from normal runtime and is not authorized to
run. It records the exact eligible model revision/digest and configuration,
uses identical synthetic and financially verifiable reference tasks, alternates
candidate order, and samples explicit windows across days of week in
`America/Bahia`. A limited pilot precedes any multi-day observation and both
require separate approval for provider calls, model downloads, quota,
concurrency, schedule, and budget.

Quality and availability are evaluated separately. Required measures include
success rate, `429`/`503` rates, first-token and p50/p95 end-to-end latency,
input/output tokens, estimated and actual cost, factual and financial quality,
source adherence, invalid-output rate, fallback result, and—locally—CPU, RAM,
GPU/VRAM, throughput, and energy/storage observations when measurable. Sample
size or confidence interval accompanies comparisons where applicable. No model
or time window is preferred before measurements.

## 17. Approved decisions and authorization state

The user approved the following R4.0 decisions:

1. **D1:** local Llama candidates require the hardware gate and digest pinning.
2. **D2:** read-only hardware inspection precedes any model installation.
3. **D3:** real financial data is not eligible for free Gemini; paid-project
   verification, opt-in, minimization, and compatible policy are prerequisites.
4. **D4:** there is one Gemini adapter, using the official `google-genai` SDK.
5. **D5:** one retry controller uses at most three total attempts as a
   configurable baseline within deadline and budget.
6. **D6:** `LOCAL_ONLY` is default; `HYBRID` is opt-in; no silent fallback or
   offline-to-cloud promotion exists.
7. **D7:** initial circuit-breaker parameters are experimental and calibrated
   from evidence.
8. **D8:** the benchmark protocol is reproducible but authorizes no execution,
   download, call, or expense.
9. **D9:** telemetry is minimized; persistence, `ai_runs` reuse, and final
   retention require a separate gate.
10. **D10:** initial personalization is authorized preference plus certified
    retrieval only, with no silent training.
11. **D11:** R4 builds one infrastructure and reconciles historical scaffolding;
    it does not presume an existing functional Advisor.
12. **D12:** the first increment is tested through an internal application
    service and mocks, with no endpoint, frontend, or scheduler.

Four mandatory refinements also apply: Gemini integration approval and
real-financial-data transmission approval are separate; `LOCAL_ONLY` returns
explicit unavailability even when no local model exists; benchmark quality and
availability remain separate and elect no model or schedule before evidence;
and the telemetry contract precedes persistence and real execution, with no
implicit database or migration.

R4-A through R4-H were approved as planned increments, not as one automatic
implementation authorization. R4-A, R4-B and R4-C are `CLOSED / PUSHED`.
R4-D through R4-H runtime implementations remain `NOT IMPLEMENTED` and require
their own gates; local laboratory execution is a separate evidence category.

## 18. R4-A implementation record

R4-A implements only the provider-neutral contract foundation:

- an asynchronous, SDK-free `AIProvider` application port for stable identity,
  exact model discovery, health, generation, explicit cancellation, and
  idempotent resource closure;
- frozen request/response contracts for server-resolved user scope, privacy,
  consent, capabilities, minimum structured context, certified references,
  strict output schema, tool/token/cost budgets, UTC deadline, policy versions,
  provider/model evidence, usage, latency, exact Decimal cost, validation,
  retry/fallback metadata, warnings, and UTC completion time;
- instance-scoped immutable provider/model capability registries with exact
  identifiers and no default model, alias resolution, or mutable global state;
- a closed safe error taxonomy with allowlisted metadata and no raw provider
  payload or financial context;
- strict local structural validation that rejects unknown/missing fields,
  invalid types, floats/Decimal objects in canonical values, unauthorized or
  missing source references, disallowed tool metadata, and token/cost overruns.
  Certified Decimal strings, including zero and scale, are preserved. Factual
  adherence remains explicitly `NOT_PERFORMED` for R4-B;
- an internal application service that invokes only the provider and exact
  model supplied by its caller after registry, locality, privacy, consent,
  capability, lifecycle, and deadline checks. It performs no selection, retry,
  fallback, authorization lookup, tool execution, context building, or write;
- a deterministic synthetic fake adapter covering valid output, invalid schema,
  timeout, unavailability, rate limiting, cancellation, usage, cost, discovery,
  health, and closure without network, provider SDK, environment, database, or
  filesystem I/O.

**Schema scope clarification (DOC-R4A-01 / DOC-R4A-02):** R4-A implements a
canonical, strict structural AST (`CanonicalOutputSchema` / `OutputSchemaNode`),
not a generic interpreter for every JSON Schema version. It does not claim
support for JSON Schema keywords such as `pattern`, `minimum`, `maximum`, or
`$ref`. `OutputSchemaNode` also has no enum restriction in R4-A. A future
capability that depends on any of those semantics requires a contract extension
and focused tests before activation.

**Deferred independent-review finding (MIN-R4A-01):** When a structural failure
occurs in a nested node, the full nested path is not yet propagated into
`AIErrorMetadata.field`. The finding has no confirmed functional impact on
R4-A validation or rejection behavior. It remains deferred; `validation.py` is
not changed by this checkpoint.

Focused validation passed `32` R4-A tests. Minimal R2 Smart Context and R3
External Reference regressions passed `39` tests. The user-reported root/backend
`GEMINI_API_KEY` configuration was neither read nor tested; its presence grants
no adapter, remote-processing, or real-financial-data authorization. No Gemini
or Ollama code ran, Ollama remains uninstalled, and no benchmark, database,
migration, endpoint, frontend, scheduler, commit, or push was introduced.

## 19. R4-B implementation record

R4-B implements only the internal authorization, read-only tool, and minimum
context boundary:

- `TrustedServerUserScopeResolver` derives `ServerUserScope` from the active
  `UserResponseDTO` supplied by the existing authenticated server boundary. A
  tool argument cannot set or replace `user_id`, and a request scope that does
  not match the authenticated principal fails closed;
- an immutable, instance-scoped registry contains exactly
  `read_home_context`, `read_planning_context`, `read_goal_context`,
  `read_fire_context`, and `read_owned_goal`. Definitions fix version,
  purpose, exact argument/result contracts, handler, authorization rule,
  financial data class, local timeout, per-request call ceiling, provenance,
  and `READ_ONLY` side effect. There are no aliases, wildcards, reflection,
  dynamic handlers, or R3 External Reference tool;
- the first four handlers delegate only to `SmartContextConsumerFoundation`.
  `read_owned_goal` delegates to the existing Decimal-safe
  `PlanningGoalReadQuery.get_goal(...)`, passes the authenticated user ID, and
  revalidates the returned owner before exposing a minimized result;
- the executor denies unknown, non-allowlisted, wrong-purpose, wrong-privacy,
  over-budget, expired, or cross-owner calls before returning context. Exact
  server-side parsers accept only `as_of_date` or `goal_id`; extra fields such
  as `user_id`, SQL, URL, path, or write instructions are rejected without
  relying on unsupported `OutputSchemaNode` enum or generic JSON Schema
  semantics;
- `MinimalAIContextBuilder` preserves certified Decimal strings (including
  zero), civil/observed time, semantic type, source/owner, scope, freshness,
  explicit unavailable/assumption states, evidence, provenance, and
  completeness. It omits Goal `user_id` and linked-account identity, performs
  no financial calculation, and labels retrieved text structurally as
  `UNTRUSTED_DATA` rather than interpreting it as policy;
- the existing R2 exact-single-user guard remains fail-closed but is not
  represented as universal multi-tenant authorization. Ownership exceptions
  become safe `AUTHORIZATION_DENIED` errors; missing or cross-owner Goal reads
  do not return data;
- tool timeout enforcement checks the request deadline before execution and
  rejects a result that completes after the local tool ceiling. Because the
  certified R2 readers are synchronous, R4-B does not claim unsafe cross-thread
  preemption of an already-running reader; hard cancellation remains a future
  adapter/runtime concern if evidence requires it.

Focused validation passes `24` R4-B tests plus `60` directly related R4-A/R2
regressions (`84 passed` combined). Provider-output factual adherence remains
`NOT_PERFORMED`; R4-B validates certified tool construction, not an LLM claim
against tool results. No provider, network, operational database, migration,
endpoint, frontend, scheduler, persistence, R3 consumer, engine invocation,
commit, or push is introduced. Independent review reports `84 passed`, five
read-only tools, and `0 BLOCKING / 0 MATERIAL / 0 MINOR` new findings. R4-B is
independently approved and `CLOSED / PUSHED` at
`8149e3d27a75c76ed6cc7f46fab60aabebd96396`.

## 20. R4-C implementation record

R4-C implements only the logical no-persistence audit and telemetry boundary:

- immutable, typed, versioned audit events contain request/correlation IDs,
  HMAC-pseudonymous technical scope, task and schema/policy versions, execution
  mode, allowlisted/used tools, permitted technical references, UTC timestamps,
  latency, optional tokens and exact Decimal cost, attempts, typed error,
  result, fallback, validation, and degradation state;
- event construction consumes existing `AIRequest`, `AIResponse`,
  `AIErrorCode`, `ServerUserScope`, and `ToolBudget` contracts. It has no field
  for prompts, responses, financial context, transaction descriptions, tool
  arguments, credentials, headers, or raw provider messages, and accepts no
  arbitrary metadata payload;
- typed optional metrics cover total/first-token latency, partial token usage,
  exact Decimal cost including zero, provider/model identity when known, error
  class, attempts, routing/fallback, and tool outcome without assuming provider
  parity;
- replaceable audit and telemetry ports are separate. Required audit emission
  fails closed on insufficient guarantee or sink failure; optional telemetry
  failure is reported separately and cannot masquerade as audit success;
- the only concrete sinks are deterministic in-memory test sinks. Their
  guarantee is explicitly `VOLATILE`; remote, tool-enabled, or tool-executing
  events require `DURABLE` and reject those sinks.

Focused R4-C validation passes `21` tests; direct R4-A/R4-B regressions pass
`56`, for `77 passed` combined. No global suite was run. Historical `ai_runs`
was inspected but not reused or modified. Audit persistence and definitive
retention are `NOT AUTHORIZED`. Ollama is `NOT INSTALLED`; Gemini was `NOT
CALLED`; R4-D and later increments are `NOT IMPLEMENTED`. No database access,
migration, HTTP call, provider SDK, endpoint, frontend, scheduler, commit, or
push is introduced.

**Independent review adjudication (2026-10-16):** R4-C is independently
approved with `77 passed`, `0 BLOCKING`, and `0 MATERIAL` active findings. The
historical review designation `MAT-R4C-01` is retained for traceability; its
current adjudication is `INFORMATIONAL / FUTURE ACTIVATION BLOCKER`, not a
defect in isolated R4-C scope. R4-A/R4-B services do not integrate a
pre-execution guard, so the existence of `AIAuditTelemetryEmitter` does not
establish fail-closed behavior before execution. A `VOLATILE` sink remains
insufficient for `DURABLE` audit. R4-F orchestration must integrate and
validate that pre-execution guard before any operational dispatch to providers
or tools is activated. `INF-R4C-01` remains: future HMAC key configuration,
rotation, and key-ID governance require a separately authorized secret/config
contract. This adjudication changes neither ADR-030 nor any locked decision.

**Checkpoint reconciliation (2026-10-24):** the approved R4-C implementation
is present at `HEAD` and the local `origin/develop` tracking ref as checkpoint
`14cb65db1cddd5466523eefdca54c78affb3eca7`. Its focused and direct R4-A/R4-B
selection was rerun with `77 passed`. R4-C is therefore `CLOSED / PUSHED`.
The R4-F pre-execution durable-audit guard and future HMAC key operations remain
separately gated activation requirements; they are not retroactively part of
the isolated no-persistence R4-C closure.

## 21. Product realignment — evaluation and activation gates (2026-10-28)

### Evidence, not provider certification

The inspected production paths contain R4-A's fake provider and R4-C's
in-memory sink, not an Ollama/Gemini adapter. R4-A structural validation still
reports `FactualValidationStatus.NOT_PERFORMED`; strict JSON alone is not
financial fidelity. R4-B exposes exactly five read-only context/Goal tools,
not a registered Planning/FIRE solver tool. Neither successful laboratory tool
calling nor a proposed Advisor architecture extends that registry.

Historical local evidence remains immutable and ignored by Git:

- `experiments/llm-benchmarks/reports/consolidated.md`: synthetic local pilot,
  tool-calling, security and context experiments with known methodological
  limits. It explicitly does not implement official R4-G or elect a global
  winner. Its Ollama 0.40.6 evidence is later than the 0.40.5 setup snapshot.
- `experiments/llm-benchmarks/reports/stage_q1_hr_corrected_consolidation_v2.md`:
  20 completed assisted human reviews and additive corrections; not independent
  replication, not an override of objective financial/schema failures.
- `experiments/llm-benchmarks/reports/stage_q1_thinking_t0_final.md`: 5/8 calls,
  stopped after output truncation with no final answer; incomplete pairs and
  zero T1 eligibility. No off/on superiority or production readiness follows.

These are local evidence paths, not required runtime dependencies or requests
to version the laboratories. This reconciliation neither reruns nor edits them.
Qwen 3.5 4B remains the first local evaluation baseline under the owner's
direction; its exact installed digest, license, configuration and eligibility
must be checked at an authorized execution. Other previously tested candidates
may be compared only with equivalent fixtures/configuration and explicit scope.
Gemini online equivalence is not established by the inspected reports.

Track five independent gates per provider/model/task/configuration:

- `LAB TESTED`: a bounded synthetic run with reproducible evidence, including
  failed/inconclusive outcomes. Local evidence exists; equivalent Gemini evidence
  was not found in the inspected reports.
- `RUNTIME IMPLEMENTED`: the provider-neutral adapter and orchestration exist
  and pass integration tests. Neither real provider has reached this state.
- `SECURITY GATES PASSED`: pre-dispatch policy/audit, ownership, minimization,
  injection, secret handling and failure tests pass for the actual execution path.
  R4-A/B/C internal tests do not establish this end-to-end state.
- `APPROVED FOR REAL DATA`: separate task-specific human authorization after
  safety, privacy and factual-fidelity evidence. Not established for either path.
  Gemini additionally requires the paid-project/policy/opt-in gates of ADR-030.
- `PRODUCT INTEGRATED`: an authorized user-facing journey is implemented,
  tested and accepted. No AI journey currently has this status.

### Bounded local/online test plan — not an execution authorization

R4-G owns the comparison protocol; R4-D.3/E own adapter validation and R4-F
owns operational safety. The next pilot must reuse the historical cases that
answer the task, adding only missing synthetic R6.4/R6.5 result coverage.
Do not start by rebuilding the laboratory or repeating every old matrix.

1. Freeze a versioned set of synthetic certified Goal/planning outputs,
   including explicit budget allocations, under/equal/over-budget cases,
   null/zero, unavailable sources and nominal/real labels as actually contracted.
   Generate expected numbers with certified backend services and independent
   test oracles, never model answers. R6.5 fixtures wait for its accepted contract
   and tested implementation. No production database or personal record export.
2. Pin model revision/digest, runtime/SDK, prompt and schema version, seed when
   supported, temperature, context/output limits, Thinking configuration and
   tool mode. Same semantic fixtures and source references go to both providers;
   provider-specific tokenizers/controls are reported, not asserted equivalent.
3. Separate precomputed-result explanation from tool-calling trials. The first
   measures exact Decimal-string/source/premise fidelity and abstention; the
   second measures allowed selection, typed arguments, wrong-user/unknown-tool
   refusal, call budgets, and handling of unavailable tool results. Use approved
   tools or synthetic test doubles; no production registry extension by testing.
4. Exercise prompt injection through Goal names, external text and tool output;
   attempted source/value substitution; unrelated data requests; secret echo;
   malformed JSON, invalid enum/schema, invented numerical claims, missing
   provenance and output truncation. Preserve separate structure, numeric,
   provenance, abstention and security verdicts. `REVIEW`/incomplete/truncated
   output cannot become `PASS` or a successful financial explanation.
5. Mock timeout, cancellation, absent local model, offline network, Gemini
   authentication/quota/429/503, provider outage and audit-sink failure. Verify
   bounded total attempts/deadline/token/cost budget and no silent cloud fallback.
   A live outage or a good textual answer never bypasses an authorization gate.
6. Record sample count, cold/warm and first-token/end-to-end latency, p50/p95
   only where the sample supports them, tokens (or explicit unknown), local
   resource usage and remote estimated/actual Decimal cost (or unavailable).
   Keep availability separate from quality; do not invent zero cost because an
   account advertises free access. Alternate candidate order and retain hashes
   and configuration lineage; no cross-version aggregate winner.
7. Before any call, approve exact models, number of conditions/repetitions,
   maximum HTTP calls including tool rounds/retries, token and monetary ceilings,
   schedule and output location. Start with a finite pilot; stop on privacy/tool
   escape, audit failure, input/output truncation or the approved budget ceiling.
   Diagnose a failed technical gate before another separately authorized run.
8. Review usefulness and cited facts manually without overriding objective
   failures. Promote only the tested task/configuration when the required gates
   pass; record limitations. No benchmark result alone authorizes real data,
   provider activation, persistent memory, operational advice or a scheduler.

The initial online target is one Gemini adapter, not OpenAI by default. At its
implementation gate verify the current official SDK/model and data-use terms;
this document makes no current price, quota or remote-policy claim. Synthetic
online tests still need explicit network/cost authorization. Real financial
data remains prohibited on the free Gemini tier under the project policy.
`LOCAL_ONLY` remains default; `HYBRID` is explicit opt-in. Operational remote or
tool-enabled execution needs `DURABLE` audit and the validated pre-execution
guard. Isolated lab tests must never be relabeled as that operational proof.
