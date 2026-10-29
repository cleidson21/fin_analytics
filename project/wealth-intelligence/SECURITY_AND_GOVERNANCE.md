# Security, Privacy & AI Governance

**Status:** `ACTIVE OWNER — CURRENT RISKS + LOCKED DIRECTION`

**Date:** 2026-10-29

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

### TSK-SEC-JWT-01 — local remediation, not published (2026-10-29)

At published baseline `0ac08c11ba4a05342641c0c9365977c9d2c727e6`, a
synthetic, correctly signed refresh token returned HTTP 200 from the real
Profile context router using the real `get_current_user`. A valid access token
also returned 200; a signed `sub="not-a-uuid"` returned 500. The pre-fix run was
`1 passed, 2 failed, 2 warnings`. Root cause: shared HS256 validation checked
signature/expiry but not token purpose, and UUID parsing errors escaped the
credential boundary. No personal user/token or live service was used.

The local correction adds `type="access"` to newly issued access tokens;
refresh tokens retain `type="refresh"`. Existing claims, lifetimes, HS256, configured
secret, `IJWTService`, login response and `AuthTokenDTO` remain unchanged.
The HTTP dependency alone owns the access-purpose policy after verified decode:
explicit `access` is allowed; refresh, unknown, null and other invalid types
return the existing uniform credential HTTP 401 with `WWW-Authenticate: Bearer`.
Expiration is required and verified. Invalid/missing/non-UUID subjects return
401, and UUID parsing cannot escape as 500. Missing tokens keep OAuth2's
existing 401; nonexistent users keep 401 and inactive users keep the existing
400 denial. No financial response or JWT payload is included in these errors.
The generic JWT verifier still verifies both token kinds; it is not access
authorization. No unverified claims grant access.

`SEC-JWT-LEGACY — REMOVAL PENDING`: transitional compatibility accepts an absent
`type` only through the same signature, required expiration, UUID and active-user
checks. An explicit null or refresh type cannot enter this branch. No compatibility configuration was
added. This branch does not switch off automatically: remove it in a bounded
follow-up after publication/deployment and the maximum configured lifetime of
the last pre-change access token (default 60 minutes), once all old issuers
have stopped. Existing legitimate sessions need no mass invalidation. This is
not a permanent promise to support untyped tokens.

Checkpoint regression on 2026-10-29 reran the same 43-file selection in a
single process: **1161 passed, 121 warnings, 0 failed, 0 errors, 0 skipped**
in 28.29 seconds. It used the repository virtualenv, a new dedicated parent
under the OS temporary directory, a new `pytest` child as `--basetemp`, and a
dedicated disposable SQLite `TEST_DATABASE_URL`. The warnings were the same
Pydantic, `datetime.utcnow()` and Goals AsyncMock categories described below.
No production database, network, or model was used. Reproducible PowerShell:

```powershell
$jwtTempParent = Join-Path $env:TEMP ('finanalytics-sec-jwt-checkpoint-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $jwtTempParent -ErrorAction Stop | Out-Null
$jwtTempBase = Join-Path $jwtTempParent 'pytest'
$jwtTestDbPath = (Join-Path $jwtTempParent 'isolated-test.db').Replace('\','/')
$env:TEST_DATABASE_URL = 'sqlite+aiosqlite:///' + $jwtTestDbPath
$jwtRegressionFiles = @(rg --files tests/unit | Where-Object { $_ -match 'test_(jwt_|planning_|goal|profile_context_api|income_candidate_api|fire_|wealth_home_|smart_context_|smart_financial_context_|recurring_income_|database_bootstrap_safety)' } | Sort-Object)
.\.venv\Scripts\python.exe -m pytest @jwtRegressionFiles -q -p no:cacheprovider "--basetemp=$jwtTempBase"
```

Two focused files (`tests/unit/test_jwt_service.py` and
`tests/unit/test_jwt_auth_boundary.py`) cover issuance/expiry/jti/signatures,
purpose and malformed claims, expired/absent/invalid/tampered/wrong-algorithm
tokens, legacy access, absent/inactive users, login and DTO parity. Production
Planning, Profile and Financial Context routes run through real authentication
with mocked infrastructure; the Planning projection uses its certified engine.
Captured DEBUG logs and error canaries contain no tested secret/token/password
or private financial/identity payload. This is bounded test evidence, not a
global logging or authentication security certification.

Executed from repository root, using the existing Python 3.14 virtualenv:

```powershell
# Before correction, this file contained only the three reproduction cases:
.\.venv\Scripts\python.exe -m pytest tests/unit/test_jwt_auth_boundary.py -q -p no:cacheprovider --basetemp=.pytest_tmp/tsk_sec_jwt_before
# Final focused coverage: 66 passed, 11 warnings
.\.venv\Scripts\python.exe -m pytest tests/unit/test_jwt_service.py tests/unit/test_jwt_auth_boundary.py -q -p no:cacheprovider --basetemp=.pytest_tmp/tsk_sec_jwt_focused_final
# Expanded regression selection, including the 66 new cases:
$jwtRegressionFiles = @(rg --files tests/unit | Where-Object { $_ -match 'test_(jwt_|planning_|goal|profile_context_api|income_candidate_api|fire_|wealth_home_|smart_context_|smart_financial_context_|recurring_income_|database_bootstrap_safety)' } | Sort-Object)
.\.venv\Scripts\python.exe -m pytest @jwtRegressionFiles -q -p no:cacheprovider --basetemp=.pytest_tmp/tsk_sec_jwt_regression
```

The expanded run returned `1156 passed, 121 warnings, 5 errors`; all errors were
`tmp_path` setup `WinError 3` because `.pytest_tmp` did not yet exist. Created
that parent directory, then reran exactly the five affected nodes:

```powershell
New-Item -ItemType Directory -Path .pytest_tmp -Force | Out-Null
.\.venv\Scripts\python.exe -m pytest tests/unit/test_database_bootstrap_safety.py::test_engine_uses_canonical_configured_database_url tests/unit/test_database_bootstrap_safety.py::test_runtime_engines_enable_sqlite_foreign_keys tests/unit/test_database_bootstrap_safety.py::test_backend_main_import_does_not_mutate_schema tests/unit/test_database_bootstrap_safety.py::test_backend_main_import_never_calls_create_all tests/unit/test_smart_context_migration.py::test_b1_migration_upgrade_downgrade_and_metadata_sync -q -p no:cacheprovider --basetemp=.pytest_tmp/tsk_sec_jwt_retry
```

Retry: `5 passed`, no warnings; all 1,161 distinct selected cases passed across
these two runs, not a single 1,161-pass run. Observed warnings were existing
Pydantic class-config deprecations, `datetime.utcnow()` deprecations and Goals
AsyncMock unawaited-coroutine warnings. The first plain `python -m pytest`
attempt selected system Python 3.12 without pytest; no dependency was installed.
An intermediate focused run was `64 passed, 2 failed, 11 warnings` due solely
to new tests using `nominal_final_wealth` instead of the existing `final_wealth`;
the assertions were corrected before the final 66-pass run. Immediately after
the production fix, the original three cases passed (`3 passed, 2 warnings`).

Status: vulnerability reproduced, correction implemented and selected tests
passed locally; remediation **IMPLEMENTED / VALIDATED / LOCAL CHECKPOINT /
UNPUBLISHED / NOT DEPLOYED**. Functional commit:
`79c7280ce6eb6a8ab362759ac4d884264b4be8ff`.
No active database, internet, new migration/dependency, frontend, financial
Engine, secret rotation, refresh endpoint/rotation, revocation or AI change.
The existing security follow-up queue remains in `IMPLEMENTATION_ROADMAP.md`;
global system security is not approved by this remediation.

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

R2 implementation may persist only the approved declared-income fact and
recurring-source decision metadata. It must not add CPF, phone, birthdate, employment start,
employer, occupation, tax-regime authority, raw transaction copies, or AI
memory. Candidate APIs must return bounded evidence and opaque identifiers, not
unnecessary counterpart/account detail. Logs and audit events exclude raw
descriptions and financial payloads unless a separately approved diagnostic
policy requires them.

The active ledger lacks per-transaction `user_id`; therefore R2 may reuse only
the explicit exact-single-user/current-user guard. Ambiguity or a later
multi-user state fails closed until an ownership migration is separately
contracted. Authentication alone is not ownership proof.

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
