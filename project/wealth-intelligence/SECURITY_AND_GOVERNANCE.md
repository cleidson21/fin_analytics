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

### TSK-SEC-JWT-01 — published remediation (2026-10-29)

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
passed; remediation **IMPLEMENTED / VALIDATED / COMMITTED / PUSHED**.
Functional commit `79c7280ce6eb6a8ab362759ac4d884264b4be8ff` and documentary
commit `1684ecc57dd66ff0280a31bb6d5688645b26c503` were published to `develop`
and confirmed by the prior controlled push's real `git ls-remote` response.
Publication does not imply deployment; legacy compatibility remains pending.
No active database, internet, new migration/dependency, frontend, financial
Engine, secret rotation, refresh endpoint/rotation, revocation or AI change.
The existing security follow-up queue remains in `IMPLEMENTATION_ROADMAP.md`;
global system security is not approved by this remediation.

### SEC-DEP-C - 2026-10-30: VALIDATED / CHECKPOINT PENDING

The owner explicitly retained ordinary CPython 3.14 on Windows and authorized
the bounded pandas 2.x / SQLAlchemy 2.0.x / test-dependency reconciliation.
Preflight: develop, HEAD `1684ecc57dd66ff0280a31bb6d5688645b26c503`, five modified
files, two untracked tests, empty index. All seven paths were snapshotted before
C; the A/B evidence and both prior parser test modules are preserved. Main venv
still has the same 117 distribution name/version pairs, including pandas 3.0.3,
SQLAlchemy 2.0.51, Starlette 1.1.0 and multipart 0.0.32. It was not upgraded.

#### Selected manifest and rationale

- FastAPI 0.103.2 -> **0.139.2**, Pydantic 2.4.2 -> **2.13.4**, new explicit
  **Starlette 1.3.1**; settings **2.14.2** retained. This adopts B's investigated
  framework basis, resolves settings' Pydantic >=2.7 requirement and FastAPI's
  old Starlette <0.28 constraint. Current metadata and the real resolver accept
  the combination; it is not an arbitrary override with --no-deps.
- pandas 2.1.1 -> **2.3.3**. Its [official release notes](https://pandas.pydata.org/docs/whatsnew/v2.3.3.html)
  explicitly support Python 3.14 and [PyPI](https://pypi.org/pypi/pandas/2.3.3/json)
  supplies a cp314 Windows AMD64 wheel. Series 2.x is retained; no pandas 3.x
  migration. Direct backend imports of pandas were not found: the actual
  DataFrame consumer is YFinanceProvider through yfinance. MyProfit CSV parsing
  uses stdlib csv and existing legacy numeric conversions; Pierre uses its own
  normalization/Decimal path. Neither parser nor any financial calculation changed.
- SQLAlchemy 2.0.21 -> **2.0.44**. This is the authorized initial compatible
  2.0-series floor; [upstream's changelog](https://docs.sqlalchemy.org/en/20/changelog/changelog_20.html#change-2.0.44)
  records Python 3.14/greenlet installation support. The resolver uses a pure
  Python wheel plus greenlet 3.5.6's native wheel; a native SQLAlchemy cp314
  Windows wheel is not required for this selected distribution. Imports and
  real sync/async SQLite transactions now work; no ORM/Core conversion or DDL
  change to application models was needed.
- pytest 7.4.2 -> **9.0.3**, explicitly separately authorized in the user's
  reply, plus new **pytest-asyncio 1.4.0**. [Plugin metadata](https://pypi.org/pypi/pytest-asyncio/1.4.0/json)
  supports Python 3.14 and requires pytest >=8.4,<10. 9.0.3 is the first fixed
  version for [GHSA-6w46-j5rx-g56g / CVE-2025-71176](https://github.com/advisories/GHSA-6w46-j5rx-g56g),
  rather than adopting main's 9.1.1 just for alignment. The advisory describes
  UNIX temporary-directory handling; Windows exploitation was not reproduced.
  The existing single requirements.txt already contains pytest, so the plugin
  stays there; no new packaging/development-requirements system was created.
- **python-multipart 0.0.31** is preserved unchanged from A. Every other direct
  pin is retained, including HTTPX 0.28.1, aiosqlite 0.22.1, yfinance 0.2.31,
  bcrypt 4.0.1, python-jose 3.5.0 and the existing Google SDK. No provider/model
  was executed. Settings itself did not need another update.

The two alternatives in B remain historical evidence. C's single selected
combination resolves the specific blockers without promoting pandas 3.x,
SQLAlchemy 2.1, every installed package, or other direct dependency families.

#### Clean installation and actual resolution

Runtime: **CPython 3.14.0, MSC v.1944 64 bit (AMD64), Py_GIL_DISABLED=0**;
SQLite **3.50.4**. A new `clean-final` venv was created with stdlib
`venv.EnvBuilder(with_pip=True).create(root / 'clean-final')`, using the main
interpreter only to create it. No installed packages were copied. The complete
candidate manifest was its first dependency installation, not a framework-only
probe. Installation exited **0**, all **77 resolved distributions used wheels**,
and `pip check` returned **No broken requirements found**. Including bootstrap
pip 25.2, the fresh environment has **78 distributions**. No compiler or global
configuration was installed. The final repository requirements match the
installed candidate's entries and comments (ignoring blank lines/line endings).

Resolved transitives (direct pins are in requirements.txt; pip is venv bootstrap):

```text
Mako==1.4.3 MarkupSafe==3.0.4 Pygments==2.21.0 annotated-doc==0.0.5
annotated-types==0.8.0 anyio==4.15.1 appdirs==1.4.4 beautifulsoup4==4.15.0
certifi==2026.10.23 cffi==2.1.1 charset-normalizer==3.5.2 click==8.5.0
colorama==0.4.6 cryptography==50.0.2 ecdsa==0.19.2 frozendict==2.5.0
google-ai-generativelanguage==0.6.15 google-api-core==2.25.2
google-api-python-client==2.201.0 google-auth==2.62.0 google-auth-httplib2==0.4.4
googleapis-common-protos==1.75.0 greenlet==3.5.6 grpcio==1.85.0
grpcio-status==1.71.2 h11==0.16.0 html5lib==1.1 httpcore==1.0.9 httplib2==0.32.1
idna==3.20 iniconfig==2.3.1 lxml==6.1.3 multitasking==0.0.13 numpy==2.5.4
packaging==26.3 peewee==4.5.3 pluggy==1.7.0 proto-plus==1.28.2 protobuf==5.29.6
pyasn1==0.6.5 pyasn1-modules==0.4.2 pycparser==3.12 pydantic-core==2.46.4
pyparsing==3.3.3 python-dotenv==1.2.4 pytz==2026.6 rsa==4.9.1 six==1.17.0
soupsieve==3.0.4 tqdm==4.70.1 typing-inspection==0.4.4 typing-extensions==4.16.0
tzdata==2026.6 tzlocal==5.4.5 uritemplate==4.2.0 urllib3==2.8.0 webencodings==0.6.1
```

Compared with main's 117-distribution snapshot, 73 names overlap, five are newly
resolved (appdirs, frozendict, html5lib, lxml, webencodings), and 44 main-only
distributions are absent. Of the shared names, 45 versions differ. Important
differences include main/candidate: pandas 3.0.3/2.3.3, SQLAlchemy 2.0.51/2.0.44,
Starlette 1.1.0/1.3.1, multipart 0.0.32/0.0.31, pytest 9.1.1/9.0.3, yfinance
1.5.1/0.2.31, uvicorn 0.51.0/0.23.2, bcrypt 3.2.0/4.0.1, dateutil
2.9.0.post0/2.8.2, NumPy 2.4.6/2.5.4, greenlet 3.5.1/3.5.6, AnyIO
4.13.0/4.15.1, cryptography 49.0.0/50.0.2, Mako 1.3.12/1.4.3 and urllib3
2.7.0/2.8.0. Direct pins outside the approved families were retained even when
main differs; the transitive inventory above records the actual resolver result.
No claim of identical environments or a complete transitive lock follows:
this proves a clean install with the recorded public index state, not immutable
future resolution. Later installations must recheck transitives/advisories.

#### Compatibility, contracts and current test evidence

All commands ran from the repository root, using `clean-final`'s Python,
synthetic fixtures, separate temporary SQLite URLs and new basetemp children.
Application lifespan, FastAPI TestClient, pandas, yfinance, bcrypt, SQLAlchemy,
pytest and asyncio plugin imports passed. No public application was contacted.

- **Focused:** nine named files, **133 passed, 26 warnings**, 0 failed/errors/
  skipped. Includes the unchanged **9 Starlette limit tests**, **14 multipart
  tests**, **66 JWT tests**, market-data, MyProfit, Pierre client/import tests
  and four new Python-runtime compatibility canaries. These verify exact
  Decimal storage/compiled binding plus commit/rollback through sync and async
  SQLite sessions, and real pandas DataFrame date/order/numeric/empty-history
  consumption by the existing provider with Yahoo mocked. No financial expected
  result or validation assertion was relaxed.
- **Extended:** the exact documented **51-file** A selection, in one process:
  **1243 passed, 125 warnings, 0 failed, 0 errors, 0 skipped**, 33.39 seconds.
  This is a new C execution, not the earlier A result. It exercises JWT/login,
  Planning strict Decimal strings/UUID/dates/null/errors/ownership/A-B budget,
  Goals, Profile/Financial Context, Health, FIRE, Wealth Home and bootstrap safety.
  Starlette's nine tests and the new runtime canaries ran separately in focused
  coverage; they were not substituted for any of those 51 files.
- Warnings were visible: Pydantic class Config deprecations, utcnow/old dateutil
  utcfromtimestamp, existing Goals AsyncMock warning, legacy multipart import,
  Starlette HTTPX fallback and AnyIO BlockingPortal alias deprecations. HTTPX
  remains 0.28.1; no HTTPX2 upgrade or warning suppression was used. No unknown
  asyncio marker or skipped async test concealed missing plugin support.
- **OpenAPI:** fresh main baseline and candidate both have **61 paths / 65
  operations**. Parsed complete JSON objects are equal, covering schemas,
  operation IDs, HTTP errors, nullable/enums and field constraints, not just
  counts. Same canonical sorted compact JSON SHA-256:
  `99bd6b774646a55fb84c30b36c21ac840fe79d5b5a865612bfdd43cd254d2176`.
  Candidate `/openapi.json` through real TestClient also equals the baseline.
  No DTO, endpoint, authentication/ownership, Engine or LOCKED contract changed.

#### Post-resolution security and residual risks

OSV queried all **78 public distribution/version pairs**, including bootstrap
pip. It returned **16 alias records across 3 packages**, resolving to **8 GHSA
records**: ecdsa 0.19.2 (one HIGH), python-jose 3.5.0 (one CRITICAL), pip 25.2
(five MODERATE, one LOW). These were already present in A's inventory; none is
a new critical vulnerability introduced by the changed families. All selected
FastAPI/Starlette/Pydantic/settings/pandas/SQLAlchemy/multipart/pytest/plugin
versions and the other newly resolved transitives returned no matches on this
query. Absence of database matches is not universal security approval.

- Starlette GHSA-82w8-qh3p-5jfq / CVE-2026-54283 is **FIXED AND TESTED in the
  candidate**: 1.3.1 enforces the small urlencoded fields/size limits and retains
  multipart behavior (400 on excess, 200 on exact/below boundaries). Main's
  unchanged 1.1.0 remains affected until a separately authorized environment
  rollout. The B reproduction (7 pass / 2 fail) is retained below.
- python-jose GHSA-3qf3-8w2g-rqmx / CVE-2026-85394 remains **RESIDUAL /
  APPLICABILITY CONDITIONAL**: DER asymmetric public-key/HMAC confusion requires
  a different key setup from the explicit HS256 shared-secret boundary inspected
  here. No patched release is listed; no exploit against this configured path
  is established and JWT policy was not changed.
- ecdsa GHSA-wj6h-64fc-37mp / CVE-2024-23342 remains **RESIDUAL** in the
  distribution inventory; its P-256 signing/timing predicate is not the active
  HS256 JWT signing path. Other hypothetical consumers are not certified safe.
- pip's six GHSA records are **RESIDUAL / CONDITIONAL** installer risks involving
  crafted archives, indexes, URLs or entry points. The venv bootstraps pip 25.2;
  no global/main installer upgrade or untrusted-package experiment was performed.
  Details, severities, ranges and fixes remain in A's per-package inventory.

The previous **122 installed-version GHSA matches** retain their original
versions/severities/applicability below. They are historical main-environment
triage, not 122 proven exploits or a new candidate count. SEC-DEP overall remains
**PARTIALLY REMEDIATED / LOCAL CHANGES** with follow-up security triage; C's
authorized clean-install blockers are resolved. `SEC-JWT-LEGACY = REMOVAL PENDING`,
SEC-JWT-01 remains COMMITTED/PUSHED, Journey A accepted/published, R4 separately
gated and R7 not started. Next step is a separately authorized local checkpoint
review; no stage/commit/push/deploy or main-venv rollout is implied.

Actual commands/evidence paths (temporary root is disposable, outside repo):

```powershell
$depCRoot = Join-Path $env:TEMP 'finanalytics-sec-dep-c-0910887dffc84dde831193a6be0f897e'
$depCPython = Join-Path $depCRoot 'clean-final\Scripts\python.exe'
& $depCPython -m pip --isolated install --prefer-binary --index-url https://pypi.org/simple --report "$depCRoot\final-install-report.json" -r "$depCRoot\candidate-final-requirements.txt"
& $depCPython -m pip check
# PYTHONPATH = repo root; child DATABASE_URL points to final-openapi.db under depCRoot.
& $depCPython "$depCRoot\validate_runtime.py" $depCRoot
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:JWT_SECRET = 'synthetic-sec-dep-c-tests-only'
$env:TEST_DATABASE_URL = 'sqlite+aiosqlite:///' + $depCRoot.Replace('\','/') + '/focused.db'
& $depCPython -m pytest tests/unit/test_starlette_form_limits.py tests/unit/test_multipart_security_compatibility.py tests/unit/test_python314_dependency_compatibility.py tests/unit/test_market_data.py tests/unit/test_myprofit_proventos_parser.py tests/unit/test_pierre_import_service.py tests/unit/test_pierre_client.py tests/unit/test_jwt_service.py tests/unit/test_jwt_auth_boundary.py -q -x -p no:cacheprovider "--basetemp=$depCRoot\focused-pytest"
$jwtRegressionFiles = @(rg --files tests/unit | Where-Object { $_ -match 'test_(jwt_|planning_|goal|profile_context_api|income_candidate_api|fire_|wealth_home_|smart_context_|smart_financial_context_|recurring_income_|database_bootstrap_safety)' } | Sort-Object)
$depRegressionFiles = @($jwtRegressionFiles) + @('tests/unit/test_multipart_security_compatibility.py') + @(rg --files backend/tests/domains/health | Where-Object { $_ -match '\.py$' } | Sort-Object)
# Assert Count == 51 before invoking pytest.
$env:JWT_SECRET = 'synthetic-sec-dep-c-regression-only'
$env:TEST_DATABASE_URL = 'sqlite+aiosqlite:///' + $depCRoot.Replace('\','/') + '/regression.db'
& $depCPython -m pytest @depRegressionFiles -q -x -p no:cacheprovider "--basetemp=$depCRoot\regression-pytest"
.\.venv\Scripts\python.exe "$depCRoot\audit_final.py"
```

The install report, 78-name/version inventory, OSV responses/GHSA details,
baseline/candidate OpenAPI JSON, main-env comparison, focused/regression logs
and initial seven-file snapshots remain under that temporary root, unversioned.
Audit sends only public package names/versions; no secret, private payload or
financial data was sent. Installation used public PyPI and its normal resolver.

### SEC-DEP-B - 2026-10-29: BLOCKED / REQUIRES DECISION (historical checkpoint)

SEC-DEP-A's six authorized pending paths, multipart 0.0.31 pin, test module,
inventory and 122 installed-version GHSA matches are preserved. Preflight was
`develop`, HEAD `1684ecc57dd66ff0280a31bb6d5688645b26c503`, five modified paths,
one untracked multipart test and an empty index. The six files were snapshotted
under a unique OS-temporary directory before this continuation; the principal
venv remains Python 3.14.0 with the same 117 distribution versions. No framework
or scientific pin has been promoted into repository requirements.txt in B.

#### Framework candidates and metadata

Both temporary full-manifest candidates preserve every other existing pin,
including pandas 2.1.1, SQLAlchemy 2.0.21, pytest 7.4.2, HTTPX 0.28.1 and the
prior multipart 0.0.31 correction. Candidate files and environments live outside
the repo. Only two existing framework pins differ plus one new Starlette pin:

- **A, minimum viable framework line:** FastAPI 0.133.1, Starlette 1.3.1,
  Pydantic 2.12.5, pydantic-settings 2.14.2, python-multipart 0.0.31.
  Its framework-only normal `pip install --dry-run --ignore-installed` resolves
  successfully on Python 3.14; pydantic-core resolves to 2.41.5. FastAPI's first
  minor line permitting Starlette 1.3.1 among the checked 0.120-0.139 releases
  is 0.133; A uses that line's patch release rather than 0.133.0.
- **B, validated-environment framework basis with fixed Starlette:** FastAPI
  0.139.2, Starlette 1.3.1, Pydantic 2.13.4, settings 2.14.2, multipart 0.0.31.
  Its framework-only fresh install and `pip check` pass; core is 2.46.4.
  B is the better-supported diagnostic basis because its real parser tests ran,
  but is NOT an approved full-manifest selection: its complete install fails.

Official metadata confirms [FastAPI 0.133.1](https://pypi.org/pypi/fastapi/0.133.1/json)
requires Starlette >=0.40.0 / Pydantic >=2.7.0, while
[0.139.2](https://pypi.org/pypi/fastapi/0.139.2/json) requires Starlette >=0.46.0 /
Pydantic >=2.9.0. Neither has an upper Starlette bound blocking 1.3.1. Both
support Python >=3.10. The original FastAPI 0.103.2 instead requires Starlette
>=0.27.0,<0.28.0 and cannot simply accept the patched 1.3.1 pin.
[Settings 2.14.2](https://pypi.org/pypi/pydantic-settings/2.14.2/json) requires
Pydantic >=2.7.0. The original 2.4.2/settings contradiction was reproduced as
`ResolutionImpossible` with a metadata-only dry-run targeting Python 3.12
wheels; that target avoids attempting to build old pydantic-core on Python
3.14 and is not a change to the runtime used for installation/tests.
[Pydantic 2.12](https://pydantic.dev/articles/pydantic-v2-12-release) introduced
Python 3.14 support; both candidates' core versions have cp314 Windows wheels.
No version was chosen simply because it was latest: current PyPI metadata
reported newer FastAPI/Pydantic/Starlette releases, which were not adopted.

#### Real-parser regression and TestClient semantics

Added `tests/unit/test_starlette_form_limits.py`: nine self-contained unittest
HTTP cases using real Starlette Request.form(), a tiny local ASGI test route,
max_fields=2, max_part_size=4, and bodies below 512 bytes. Both media types test
excess fields, excess size, valid exact boundaries and valid below-boundary
inputs; missing multipart boundary returns 400. No financial app, personal
input, database, public server, request flood or parser monkeypatch is involved.

- **Before, main Starlette 1.1.0:** the final module returned 7 passed,
  2 failures, 0 errors. Too many urlencoded fields and an oversized urlencoded
  field returned 200 instead of 400. Existing multipart limits already worked.
- **After, isolated Starlette 1.3.1 framework probe B:** the same final module
  returned 9 passed, 0 failures/errors/skips. Rejected inputs returned 400;
  accepted boundary inputs returned 200 with unchanged fields. This mitigates
  [GHSA-82w8-qh3p-5jfq / CVE-2026-54283](https://github.com/advisories/GHSA-82w8-qh3p-5jfq)
  in the probe only. The project's main 1.1.0 is still CONFIRMED affected.
- An initial new assertion assumed the urlencoded size limit counted only the
  value. The first 1.3.1 probe consequently had one boundary-test failure.
  Inspection of actual on_field_name/on_field_data callbacks established that
  urlencoded counts encoded name + value, while multipart counts part data.
  The new exact-boundary examples were corrected accordingly, then all nine
  passed. No existing financial or multipart assertions were relaxed.
- One StarletteDeprecationWarning was emitted: TestClient supports HTTPX 0.28.1
  as a deprecated fallback and prefers HTTPX2. The fallback preserves the tested
  status/field behavior; no HTTPX2 dependency or test monkeypatch was introduced.
  These runs were direct unittest diagnostics, not a claimed pytest application
  regression. The new test still fails twice on the intentionally unchanged main
  environment and is not marked skipped or xfailed to hide the vulnerability.

#### Gate A: complete clean installs failed

Created two additional empty Python 3.14 venvs (A/B), without copying any of the
117 main distributions. Each ran normal `pip --isolated install --index-url
https://pypi.org/simple --report <temporary-report> -r <candidate-manifest>`,
without --no-deps or a binary-only restriction. **Both returned exit 1** before
a full environment was installed. The common failure was pandas 2.1.1 source
metadata/build through Meson 1.2.1:

```text
ERROR: Could not find ... Microsoft Visual Studio/Installer/vswhere.exe
error: metadata-generation-failed
```

PyPI has no cp314 wheel for that pandas release. The package therefore entered
a native build, and this host lacks the detected Visual Studio toolchain.
This is the observed failure, not proof that source compilation could never
work on another configured host. No compiler was installed or machine config
changed. Framework-only pip check success cannot satisfy this failed gate;
pip check on a bootstrap-only failed-install venv would not be meaningful.

The remaining runtime/test decision matrix is concrete:

- **pandas 2.1.1:** both complete candidate installs fail as above. A separately
  evaluated wheel-bearing version or an explicit supported-runtime/build choice
  is needed. [Pandas 2.3.3](https://pandas.pydata.org/docs/whatsnew/v2.3.3.html)
  documents Python 3.14 compatibility and its metadata has a cp314 Windows wheel;
  it was NOT installed, audited as a replacement, or selected here.
- **SQLAlchemy 2.0.21:** installing this unchanged declared pin separately in
  the disposable diagnostic venv succeeds (greenlet 3.5.6 resolves), but merely
  `import sqlalchemy` fails on Python 3.14: SQLCoreOperations/TypingOnly raises
  AssertionError over __static_attributes__ and __firstlineno__. No database was
  opened. A compiler alone does not address this independent import failure.
  [SQLAlchemy's changelog](https://docs.sqlalchemy.org/en/20/changelog/changelog_20.html)
  records later 3.14 work, including 2.0.44's greenlet installation change;
  no newer ORM version was installed or selected as an implicit solution.
- **Test manifest:** pytest 7.4.2 is declared, while pytest-asyncio used by the
  prior environment is absent from requirements. Installed plugin 1.4.0's
  official metadata requires pytest >=8.4,<10. A clean, supported test-runner/
  plugin selection needs evaluation; no pytest failure count is invented here,
  because full application tests were not reached. No testing pin was changed.

This extends the necessary decision beyond the four framework packages into
data/runtime and test reproducibility. Under this task's multi-package scope
stop rule, no final combination is promoted. Decide whether to authorize a
bounded Python 3.14 pandas/ORM/test-dependency reconciliation with independent
financial regressions, or explicitly select another supported Python runtime
and validate the whole manifest there. Neither automatic alignment to 117
installed packages nor a system toolchain installation is authorized by this
blocked result. No SQLAlchemy or pandas upgrade was silently implemented.

#### Partial resolution/audit evidence and pending gates

Before the separate old-SQLAlchemy import diagnostic, the B framework probe
contained 17 runtime distributions plus bootstrap pip 25.2: FastAPI 0.139.2,
Starlette 1.3.1, Pydantic 2.13.4/core 2.46.4, settings 2.14.2, multipart 0.0.31,
HTTPX 0.28.1, AnyIO 4.15.1, certifi 2026.10.23, idna 3.20, HTTPcore 1.0.9,
h11 0.16.0, python-dotenv 1.2.4, typing-extensions 4.16.0,
typing-inspection 0.4.4, annotated-doc 0.0.5 and annotated-types 0.8.0.
The A framework dry-run resolved the same common dependency versions except
FastAPI 0.133.1, Pydantic 2.12.5 and core 2.41.5. These are real subset
resolutions, not final transitive versions for the failed whole-manifest runs.

OSV queried 21 public package/version pairs from these resolutions: no matches
for the 20 runtime pairs; pip 25.2 returned 12 alias records for its previously
registered findings. Target framework versions also had zero matches in the
pre-selection query. No new critical runtime match was found in these subsets.
The full manifest/transitive audit is UNRESOLVED because installation failed;
the 122 prior installed-version matches below remain RESIDUAL and unaltered.
No general NOT APPLICABLE or system-security claim follows from zero matches.

Gate B's full environment comparison, application startup/import, financial
DTO/ownership/Decimal checks, OpenAPI schema/operation comparison and the
51-file regression were **NOT RUN / UNRESOLVED** after Gate A failed. Prior
61-path/65-operation and 1,243-pass results are SEC-DEP-A evidence only, not a
new result for B. Component success is MITIGATED in the isolated probe, not
deployed or validated for the complete application. Checkpoint is not recommended.

Reproduction commands (all candidate paths are under one unique OS-temp root;
the two full venvs were empty; the resolver venv was used only for diagnostics):

```powershell
.\.venv\Scripts\python.exe tests/unit/test_starlette_form_limits.py -v
& ($depBRoot+'\resolver\Scripts\python.exe') -m pip --isolated install --index-url https://pypi.org/simple -r ($depBRoot+'\candidate-B-framework.txt')
& ($depBRoot+'\resolver\Scripts\python.exe') tests/unit/test_starlette_form_limits.py -v
& ($depBRoot+'\resolver\Scripts\python.exe') -m pip check
& ($depBRoot+'\resolver\Scripts\python.exe') -m pip --isolated install --dry-run --ignore-installed --index-url https://pypi.org/simple --report ($depBRoot+'\framework-A-resolution.json') -r ($depBRoot+'\candidate-A-framework.txt')
# Execute once for each label A and B, against its separate initially empty venv:
& ($depBRoot+'\candidate-'+$label+'\Scripts\python.exe') -m pip --isolated install --index-url https://pypi.org/simple --report ($depBRoot+'\full-'+$label+'-report.json') -r ($depBRoot+'\candidate-'+$label+'-requirements.txt')
# Additional diagnostic uses the OLD declared SQLAlchemy pin, not an upgrade:
& ($depBRoot+'\resolver\Scripts\python.exe') -m pip --isolated install --index-url https://pypi.org/simple sqlalchemy==2.0.21
& ($depBRoot+'\resolver\Scripts\python.exe') -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

No installation touched the principal venv. Existing requirements and the
previous multipart test are preserved byte-for-byte. No auth, financial Engine,
frontend, migration, personal database, staging, commit, push, deploy, provider
or model action occurred. SEC-JWT-01 stays PUSHED, SEC-JWT-LEGACY REMOVAL PENDING,
Journey A accepted/published, R4 separately gated and R7 not started.

### SEC-DEP - 2026-10-29: PARTIALLY REMEDIATED, local/uncommitted

The only production-manifest change is `python-multipart==0.0.6` ->
`python-multipart==0.0.31`. No main-virtualenv package was installed, removed or
upgraded. The existing virtualenv already has 0.0.32 and is NOT AFFECTED by the
nine multipart advisory ranges below. This change prevents a future manifest
install from selecting known-vulnerable 0.0.6; it is not a repair performed on
the running environment. Candidate 0.0.31 is FIXED AND TESTED for this scope.
SEC-DEP remains PARTIALLY REMEDIATED because manifest and other library findings
remain open. No system-wide security certification follows.

#### Inventory and resolution boundaries

- Preflight: clean `develop`, empty index, HEAD
  `1684ecc57dd66ff0280a31bb6d5688645b26c503`; no unrelated work was changed.
- Main environment: Python 3.14.0, pip 25.2, 117 distributions; `pip check`
  returned `No broken requirements found`. This checks dependency metadata,
  not security. Eighteen direct pins exist; ten differ from the installed
  versions. The distribution-only snapshots below contain no URLs, credentials,
  local installation paths or private metadata.
- Real framework stack: FastAPI 0.139.2, Starlette 1.1.0, Pydantic 2.13.4,
  pydantic-settings 2.14.2, HTTPX 0.28.1, pytest 9.1.1 and pytest-asyncio 1.4.0.
  The declared FastAPI 0.103.2 requires Starlette >=0.27.0,<0.28.0; that old
  declared stack was not substituted for the installed stack in this task.
- A fresh `venv` outside the repo received a copy of the installed
  `site-packages`, excluding bytecode caches. No system-site-packages inheritance
  was enabled. Import paths were checked to exclude the main `.venv`.
  Comparing all 117 distributions proves the sole candidate delta is multipart
  0.0.32 -> 0.0.31; `pip --isolated install --no-deps` made no transitive changes.
  Candidate `pip check` passed. This is an installed-stack replica, not evidence
  that requirements.txt resolves cleanly. The main 117 versions and multipart
  file fingerprint were rechecked unchanged after the candidate tests.
- Official [PyPI 0.0.31 metadata](https://pypi.org/pypi/python-multipart/0.0.31/json)
  declares Python >=3.10, no runtime dependencies and a non-yanked release.
  Canonical `python_multipart` and legacy `multipart.multipart` imports work.
  FastAPI/Starlette's actual form parser and the upload route work without a
  framework change. Version 0.0.31 is the lowest release outside all nine current
  advisory ranges. Installed 0.0.32 is also unaffected; its additional
  [partial-boundary scan optimization](https://github.com/Kludex/python-multipart/releases/tag/0.0.32)
  is not a tenth advisory or a required fix in these records.
- `SEC-DEP-MANIFEST`: [settings 2.14.2 metadata](https://pypi.org/pypi/pydantic-settings/2.14.2/json)
  requires Pydantic >=2.7.0. The two-pin dry-run and full-manifest dry-runs
  before and after the multipart pin edit failed with `ResolutionImpossible`
  against Pydantic 2.4.2. Commands
  used `pip --isolated install --dry-run --ignore-installed --only-binary=:all:
  --python-version 3.12 --index-url https://pypi.org/simple`, first with the two
  pins, then `-r requirements.txt`. Python 3.12 wheel targeting isolates the
  logical conflict from old binary wheels unavailable on Python 3.14; no
  Pydantic package was installed or changed. An unsatisfiable subset proves the
  original and multipart-corrected manifests cannot install as a whole.
  The isolated current-stack validation is therefore useful but does not close
  clean-install reproducibility. A separately authorized reconciliation should
  evaluate aligning declared Pydantic to the already-used 2.13.4, or selecting
  an independently verified compatible settings pin, with framework/DTO/Decimal
  regressions; neither proposal is approved or implemented here.
- Eighteen declared packages do not account for all installed packages. The
  other 99 include transitive runtime dependencies and unrelated local tools.
  GitPython and Pillow are required by installed Streamlit; Soup Sieve by
  BeautifulSoup4; Mako by Alembic; ecdsa by python-jose. PyJWT, passlib,
  Streamlit and PDF tooling are not declared here, and no matching operational
  backend imports were found for those tool surfaces. APScheduler and
  google-generativeai are declared but have no operational scheduler/provider
  consumer in the inspected backend. These are dependency-hygiene leads, not
  authorization to remove packages or activate AI.

#### Multipart advisory assessment

All nine entries come from the [maintainer advisory list](https://github.com/Kludex/python-multipart/security/advisories)
and GitHub's reviewed package API, cross-checked with OSV on 2026-10-29.
Each lists the old declared 0.0.6 as CONFIRMED VULNERABLE VERSION according to
its published range; current installed 0.0.32 is NOT AFFECTED, and candidate
0.0.31 is FIXED AND TESTED. Version matching is not a claim of exploitation on
the currently installed stack. The real entry is authenticated
`POST /api/v1/governance/imports/upload`, using FastAPI Form/File parameters.
No arbitrary-file-write configuration or direct library `parse_form` call was
found in backend code. The nine per-entry applicability conditions follow.

- [CVE-2024-24762 / GHSA-2jv5-9r88-3w3p](https://github.com/advisories/GHSA-2jv5-9r88-3w3p): HIGH / CVSS 7.5; vulnerable `<= 0.0.6`, fixed `0.0.7`. APPLICABILITY CONDITIONAL: crafted Content-Type parsed on the Form/File boundary; no costly ReDoS payload executed.
- [CVE-2024-53981 / GHSA-59g5-xgcq-4qw3](https://github.com/advisories/GHSA-59g5-xgcq-4qw3): HIGH / CVSS 7.5; vulnerable `< 0.0.18`, fixed `0.0.18`. APPLICABILITY CONDITIONAL: malformed multipart boundary/preamble processing; only small finite canaries used.
- [CVE-2026-24486 / GHSA-wp53-j4wj-2cfg](https://github.com/advisories/GHSA-wp53-j4wj-2cfg): HIGH / CVSS 8.6; vulnerable `< 0.0.22`, fixed `0.0.22`. APPLICABILITY CONDITIONAL: requires non-default UPLOAD_DIR, UPLOAD_KEEP_FILENAME=True and a disk flush. Those options are absent from the project; Starlette owns the upload tempfile.
- [CVE-2026-40347 / GHSA-mj87-hwqh-73pj](https://github.com/advisories/GHSA-mj87-hwqh-73pj): MEDIUM / CVSS 5.3; vulnerable `< 0.0.26`, fixed `0.0.26`. APPLICABILITY CONDITIONAL: attacker-controlled multipart preamble/epilogue reaches this parser; only short finite input tested.
- [CVE-2026-42561 / GHSA-pp6c-gr5w-3c5g](https://github.com/advisories/GHSA-pp6c-gr5w-3c5g): HIGH / CVSS 7.5; vulnerable `< 0.0.27`, fixed `0.0.27`. APPLICABILITY CONDITIONAL: unbounded multipart part headers on old parser versions; default count/size rejection tested with <5 KB.
- [CVE-2026-53537 / GHSA-vffw-93wf-4j4q](https://github.com/advisories/GHSA-vffw-93wf-4j4q): LOW / CVSS 3.7; vulnerable `< 0.0.30`, fixed `0.0.30`. APPLICABILITY CONDITIONAL: upstream inspectors and backend must disagree on extended disposition names/filenames; no WAF differential deployment is assumed.
- [CVE-2026-53538 / GHSA-6jv3-5f52-599m](https://github.com/advisories/GHSA-6jv3-5f52-599m): LOW / CVSS 3.7; vulnerable `< 0.0.30`, fixed `0.0.30`. APPLICABILITY CONDITIONAL: semicolon form parsing can differ from an upstream inspector; safe route canary preserves the semicolon inside a value.
- [CVE-2026-53539 / GHSA-5rvq-cxj2-64vf](https://github.com/advisories/GHSA-5rvq-cxj2-64vf): HIGH / CVSS 7.5; vulnerable `< 0.0.30`, fixed `0.0.30`. APPLICABILITY CONDITIONAL: urlencoded semicolon-separated input reaches QuerystringParser; no large or concurrent DoS request tested.
- [CVE-2026-53540 / GHSA-v9pg-7xvm-68hf](https://github.com/advisories/GHSA-v9pg-7xvm-68hf): LOW / CVSS 3.7; vulnerable `< 0.0.31`, fixed `0.0.31`. APPLICABILITY CONDITIONAL: requires direct parse_form plus negative Content-Length; no backend caller found. A tiny stream proves rejection before read.

OSV version queries returned 18 records for 0.0.6 and 14 for 0.0.18 (including
GHSA/PYSEC aliases, not 18/14 independent vulnerabilities), zero for 0.0.31 and
zero for 0.0.32. A fresh post-pin query of 0.0.31 returned zero again. This is
absence of matches in the queried current records, not absence of every
possible future or undisclosed issue. No audit tool was installed in the main
venv; direct OSV queries were the audit equivalent. Only public distribution
names/versions were sent, never source, environment variables, JWTs or data.

#### Tests and public-contract checks

Added `tests/unit/test_multipart_security_compatibility.py` with 14 bounded
cases: both import names; plain-vs-extended disposition filename; negative
Content-Length before read; default header count/size limits; real CSV upload
bytes/filename/owner; urlencoded semicolon; quoted boundary, short preamble and
epilogue with streamed chunks; missing boundary, wrong Content-Type, missing
source and missing input; startup and secured upload OpenAPI shape. The real
upload router is used with synthetic user and mocked session/use-case; no
import record is persisted. Existing JWT tests continue to exercise real auth.

- Focused multipart plus JWT: `80 passed, 12 warnings` in 21.13 seconds,
  0 failed/errors/skips.
- Expanded candidate run: same 43 files and 1,161 cases as the JWT checkpoint,
  plus 14 multipart cases and 68 Health cases in seven files: **1243 passed,
  122 warnings, 0 failed, 0 errors, 0 skipped** in 29.63 seconds / 51 files.
- Warnings: the 121 baseline Pydantic/utcnow/Goals AsyncMock categories plus
  one intentional legacy multipart import PendingDeprecationWarning; none hidden.
- Canonically serialized baseline and candidate OpenAPI are byte-identical:
  61 paths, 65 operations, SHA-256
  `99bd6b774646a55fb84c30b36c21ac840fe79d5b5a865612bfdd43cd254d2176`.
  App imports used synthetic JWT settings and disposable SQLite paths. No
  application server was exposed publicly and no provider/model was called.
- No pytest.ini, pyproject.toml, setup.cfg or tox.ini config was found in scope.
  Root `conftest.py` sets the isolated SQLite URL before app imports and refuses
  the active database; installed pytest plugins are retained in the clone.
  Commands run from repository root with cacheprovider disabled and fresh
  dedicated basetemp children, not existing user/project/data directories.

The candidate venv path is assigned to `$depRoot\candidate`, with `$depRoot`
a unique directory under `%TEMP%`. Real commands (paths generalized for privacy):

```powershell
# Only this install occurred, in the disposable clone:
& ($depRoot+'\candidate\Scripts\python.exe') -m pip --isolated install --no-deps --index-url https://pypi.org/simple python-multipart==0.0.31
& ($depRoot+'\candidate\Scripts\python.exe') -m pip check
$env:TEST_DATABASE_URL='sqlite+aiosqlite:///' + ($depRoot + '\focused-test.db').Replace('\','/')
$env:JWT_SECRET='synthetic-sec-dep-focused-secret'
& ($depRoot+'\candidate\Scripts\python.exe') -m pytest tests/unit/test_multipart_security_compatibility.py tests/unit/test_jwt_service.py tests/unit/test_jwt_auth_boundary.py -q -p no:cacheprovider "--basetemp=$depRoot\focused-pytest"
$env:TEST_DATABASE_URL='sqlite+aiosqlite:///' + ($depRoot + '\regression-test.db').Replace('\','/')
$env:JWT_SECRET='synthetic-sec-dep-regression-secret'
$jwtRegressionFiles = @(rg --files tests/unit | Where-Object { $_ -match 'test_(jwt_|planning_|goal|profile_context_api|income_candidate_api|fire_|wealth_home_|smart_context_|smart_financial_context_|recurring_income_|database_bootstrap_safety)' } | Sort-Object)
$depRegressionFiles=@($jwtRegressionFiles)+@('tests/unit/test_multipart_security_compatibility.py')+@(rg --files backend/tests/domains/health | Where-Object { $_ -match '\.py$' } | Sort-Object)
& ($depRoot+'\candidate\Scripts\python.exe') -m pytest @depRegressionFiles -q -p no:cacheprovider "--basetemp=$depRoot\regression-pytest"
```

#### Residual priority and approval boundary

`SEC-DEP-STARLETTE`: [GHSA-82w8-qh3p-5jfq / CVE-2026-54283](https://github.com/advisories/GHSA-82w8-qh3p-5jfq),
HIGH, affects >=0.4.1,<1.3.1. APPLICABILITY CONFIRMED for the current form-parser
limit bypass, not for a destructive production attack: with only 11 input bytes,
`Request.form(max_fields=1,max_part_size=1)` accepted two urlencoded fields and
a five-character second value on Starlette 1.1.0. The real upload route accepts
that media type. This is independent of multipart's semicolon fix and is NOT
resolved by this pin. No request flood or large payload was executed. Its
metadata fix floor is Starlette 1.3.1, but a framework upgrade is outside this
task and needs explicit scope plus tests. This finding and the unsatisfiable
manifest prevent declaring SEC-DEP closed.

OSV scanned 117 installed names/versions and the 18 declared pins, then fetched
all 132 unique GHSA detail records across those sets and multipart candidates;
0 detail retrieval failures and 0 withdrawn records were observed. The installed
snapshot has 122 unique GHSA matches across 13 distributions. PYSEC/CVE aliases
are not counted again. Most version matches have not had their exploit
preconditions established in this product; they remain REQUIRES INVESTIGATION
or APPLICABILITY CONDITIONAL as specified below, not silently confirmed attacks.
The declaration-only pytest issue and nine multipart records account for the
remaining ten unique records. This audit does not cover NPM, every optional
extra, binary OS dependencies, licenses, or unknown vulnerabilities. The
declaration scan checks the 18 direct pins only: an unresolved manifest cannot
provide a complete resolved transitive-version audit for a clean install.

The existing roadmap remains the sole queue. Next bounded SEC-DEP continuation
should reconcile the manifest and assess the Starlette fix under separate
Pydantic/framework authorization; no additional direct pin was changed here.
SEC-BOOT/CORS/SESSION/REPO and SEC-JWT-LEGACY stay separately scoped. R4 remains
SEPARATELY GATED, LOCAL_ONLY default and R7 NOT STARTED. The current multipart
manifest correction and canaries are local, unstaged and uncommitted.

<details>
<summary>Declared versus installed inventory (pre-fix declarations; public names/versions only)</summary>

- fastapi: declared `0.103.2`; installed `0.139.2`; DRIFT.
- uvicorn: declared `0.23.2`; installed `0.51.0`; DRIFT.
- sqlalchemy: declared `2.0.21`; installed `2.0.51`; DRIFT.
- pydantic: declared `2.4.2`; installed `2.13.4`; DRIFT.
- pydantic-settings: declared `2.14.2`; installed `2.14.2`; MATCH.
- pandas: declared `2.1.1`; installed `3.0.3`; DRIFT.
- python-dateutil: declared `2.8.2`; installed `2.9.0.post0`; DRIFT.
- python-multipart: declared `0.0.6`; installed `0.0.32`; DRIFT.
- pytest: declared `7.4.2`; installed `9.1.1`; DRIFT.
- yfinance: declared `0.2.31`; installed `1.5.1`; DRIFT.
- apscheduler: declared `3.11.3`; installed `3.11.3`; MATCH.
- requests: declared `2.34.2`; installed `2.34.2`; MATCH.
- httpx: declared `0.28.1`; installed `0.28.1`; MATCH.
- google-generativeai: declared `0.8.6`; installed `0.8.6`; MATCH.
- aiosqlite: declared `0.22.1`; installed `0.22.1`; MATCH.
- python-jose: declared `3.5.0`; installed `3.5.0`; MATCH.
- alembic: declared `1.18.5`; installed `1.18.5`; MATCH.
- bcrypt: declared `4.0.1`; installed `3.2.0`; DRIFT.

Installed snapshot (117 distributions; 99 outside the direct manifest are not all runtime dependencies):

```text
aiosqlite==0.22.1
alembic==1.18.5
altair==6.1.0
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.13.0
APScheduler==3.11.3
attrs==26.1.0
bcrypt==3.2.0
beautifulsoup4==4.15.0
blinker==1.9.0
cachetools==7.1.4
certifi==2026.5.20
cffi==2.0.0
charset-normalizer==3.4.7
click==8.4.1
colorama==0.4.6
coverage==7.14.1
cryptography==49.0.0
curl_cffi==0.15.0
ecdsa==0.19.2
et_xmlfile==2.0.0
fastapi==0.139.2
flatbuffers==25.12.19
gitdb==4.0.12
GitPython==3.1.50
google-ai-generativelanguage==0.6.15
google-api-core==2.25.2
google-api-python-client==2.198.0
google-auth==2.56.0
google-auth-httplib2==0.4.0
google-generativeai==0.8.6
googleapis-common-protos==1.75.0
greenlet==3.5.1
grpcio==1.82.1
grpcio-status==1.71.2
h11==0.16.0
httpcore==1.0.9
httplib2==0.32.0
httptools==0.8.0
httpx==0.28.1
idna==3.16
iniconfig==2.3.0
itsdangerous==2.2.0
Jinja2==3.1.6
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
Mako==1.3.12
markdown-it-py==4.2.0
MarkupSafe==3.0.3
mdurl==0.1.2
multitasking==0.0.13
narwhals==2.21.2
networkx==3.7
numpy==2.4.6
onnxruntime==1.31.0
openpyxl==3.1.5
packaging==26.2
pandas==3.0.3
passlib==1.7.4
peewee==4.2.4
pillow==12.2.0
pip==25.2
platformdirs==4.10.0
pluggy==1.6.0
proto-plus==1.28.1
protobuf==5.29.6
psutil==7.2.2
pyarrow==24.0.0
pyasn1==0.6.4
pyasn1_modules==0.4.2
pycparser==3.0
pydantic==2.13.4
pydantic-settings==2.14.2
pydantic_core==2.46.4
pydeck==0.9.2
Pygments==2.20.0
PyJWT==2.13.0
pymupdf==2.0
pymupdf4llm==2.0
pymupdf_layout==2.0
pyparsing==3.3.2
pypdf==6.21.2
pytest==9.1.1
pytest-asyncio==1.4.0
pytest-cov==7.1.0
python-dateutil==2.9.0.post0
python-dotenv==1.2.2
python-jose==3.5.0
python-multipart==0.0.32
pytz==2026.2
PyYAML==6.0.3
referencing==0.37.0
requests==2.34.2
rich==15.0.0
rpds-py==0.30.0
rsa==4.9.1
six==1.17.0
smmap==5.0.3
soupsieve==2.8.4
SQLAlchemy==2.0.51
starlette==1.1.0
streamlit==1.57.0
tabulate==0.10.0
tenacity==9.1.4
toml==0.10.2
tqdm==4.68.4
typing-inspection==0.4.2
typing_extensions==4.15.0
tzdata==2026.2
tzlocal==5.4.4
uritemplate==4.2.0
urllib3==2.7.0
uvicorn==0.51.0
watchdog==6.0.0
websockets==16.0
yfinance==1.5.1
```

</details>

<details>
<summary>Residual version matches: each advisory, severity, affected interval and published fix floor</summary>

All package groups below inherit status CONFIRMED VULNERABLE VERSION from the
OSV installed-version query, plus the separately stated applicability status.
No group is fixed by this task. A published fix floor is metadata, not an
approved/tested compatible upgrade. Individual titles identify the relevant
operation/format; source links provide its full exploit conditions. Intervals
use OSV event notation: introduced inclusive, fixed exclusive, last_affected
inclusive. The common usage/status/installed/declaration fields on each package
group apply to every record in that group.

**anyio** - installed `4.13.0`, declared `not directly declared`. Runtime ASGI/HTTP dependency. TLS IDNA issue needs an internationalized hostname and redirected connection; process-pool stderr issue needs noisy process workers. APPLICABILITY CONDITIONAL; those predicates were not demonstrated.

- [GHSA-5p39-cfhj-2xmp](https://osv.dev/vulnerability/GHSA-5p39-cfhj-2xmp); CVE-2026-64847; MODERATE; affected `introduced=0, fixed=4.14.2`; fix floor `4.14.2`. AnyIO process-pool workers can block indefinitely on undrained stderr.
- [GHSA-82r6-8w77-94w6](https://osv.dev/vulnerability/GHSA-82r6-8w77-94w6); CVE-2026-63374; CRITICAL; affected `introduced=0, fixed=4.14.2`; fix floor `4.14.2`. AnyIO: TLSStream IDNA 2003 host name encoding enables potential TLS certificate spoofing.

**certifi** - installed `2026.5.20`, declared `not directly declared`. Requests/HTTP TLS trust. Compromised CA-chain trust is a conditional outbound-network risk; no interception was attempted. APPLICABILITY CONDITIONAL.

- [GHSA-6q48-6c7w-9gw2](https://osv.dev/vulnerability/GHSA-6q48-6c7w-9gw2); no CVE assigned; CRITICAL; affected `introduced=2019.03.09, fixed=2026.10.18`; fix floor `2026.10.18`. certifi bundles emSign root CAs with compromised intermediate CA keys.

**cryptography** - installed `49.0.0`, declared `not directly declared`. Used transitively by python-jose. This finding concerns PKCS7 EnvelopedData decryption; no such backend consumer was found. APPLICABILITY CONDITIONAL, not established for current HS256 JWT.

- [GHSA-g6cj-pr64-35w5](https://osv.dev/vulnerability/GHSA-g6cj-pr64-35w5); CVE-2026-69247; HIGH; affected `introduced=44.0.0, fixed=50.0.0`; fix floor `50.0.0`. cryptography: PKCS#7 EnvelopedData decryption exposes a Bleichenbacher oracle through distinguishable errors and timing.

**ecdsa** - installed `0.19.2`, declared `not directly declared`. python-jose transitive package. Finding needs P-256 signing/timing observations; configured JWT uses explicit HS256 with a shared secret. NOT AFFECTED for that specific configured signing path; other consumers REQUIRES INVESTIGATION.

- [GHSA-wj6h-64fc-37mp](https://osv.dev/vulnerability/GHSA-wj6h-64fc-37mp); CVE-2024-23342; HIGH; affected `introduced=0`; fix floor `none published`. Minerva timing attack on P-256 in python-ecdsa.

**GitPython** - installed `3.1.50`, declared `not directly declared`. Installed through Streamlit, not declared and no operational backend GitPython import found. REQUIRES INVESTIGATION of local tooling, untrusted repositories and per-record preconditions; no removal authorized.

- [GHSA-239g-whfq-7xj9](https://osv.dev/vulnerability/GHSA-239g-whfq-7xj9); CVE-2026-87817; HIGH; affected `introduced=0, fixed=3.1.60`; fix floor `3.1.60`. GitPython: Repository content can impersonate the git directory, leading to arbitrary code execution.
- [GHSA-23mf-xhv8-69c2](https://osv.dev/vulnerability/GHSA-23mf-xhv8-69c2); CVE-2026-110859; HIGH; affected `introduced=0, fixed=3.2.0`; fix floor `3.2.0`. GitPython: arbitrary file read via attacker-controlled branch name in Head.checkout() (incomplete fix of CVE-2026-78679).
- [GHSA-284h-m62q-gf8w](https://osv.dev/vulnerability/GHSA-284h-m62q-gf8w); CVE-2026-78676; CRITICAL; affected `introduced=0, fixed=3.1.59`; fix floor `3.1.59`. GitPython: Dormant multi-line git-config values are corrupted into live injected directives (e.g. core.hooksPath) on any unrelated GitConfigParser write, enabling RCE.
- [GHSA-2f96-g7mh-g2hx](https://osv.dev/vulnerability/GHSA-2f96-g7mh-g2hx); CVE-2026-67325; HIGH; affected `introduced=0, fixed=3.1.51`; fix floor `3.1.51`. GitPython: Command Injection via git long-option prefix abbreviation bypass of CVE-2026-42215 blocklist.
- [GHSA-3f7w-8rr8-f37f](https://osv.dev/vulnerability/GHSA-3f7w-8rr8-f37f); CVE-2026-73620; HIGH; affected `introduced=0, fixed=3.1.57`; fix floor `3.1.57`. GitPython: Unguarded git option forwarding in IndexFile.checkout() and TagReference.create() enables arbitrary file overwrite and arbitrary file read.
- [GHSA-3rp5-jjmw-4wv2](https://osv.dev/vulnerability/GHSA-3rp5-jjmw-4wv2); CVE-2026-69097; HIGH; affected `introduced=0, fixed=3.1.53`; fix floor `3.1.53`. GitPython: git-config section-name injection enables arbitrary config directives (core.sshCommand RCE).
- [GHSA-3wxw-xv34-2frg](https://osv.dev/vulnerability/GHSA-3wxw-xv34-2frg); CVE-2026-78679; MODERATE; affected `introduced=0, fixed=3.1.59`; fix floor `3.1.59`. GitPython: TagReference.create positional reference bypasses kwargs-only --file guard, enabling arbitrary file read (incomplete fix of 3af0c251).
- [GHSA-4gmw-gg2m-w46p](https://osv.dev/vulnerability/GHSA-4gmw-gg2m-w46p); CVE-2026-76219; HIGH; affected `introduced=0, fixed=3.1.58`; fix floor `3.1.58`. GitPython: Unguarded git read-tree option forwarding in IndexFile.from_tree/reset/merge_tree enables arbitrary file overwrite.
- [GHSA-539m-9xh6-q6rr](https://osv.dev/vulnerability/GHSA-539m-9xh6-q6rr); CVE-2026-73619; MODERATE; affected `introduced=0, fixed=3.1.57`; fix floor `3.1.57`. GitPython: Incomplete unsafe_git_archive_options denylist omits --add-file / --add-virtual-file, enabling arbitrary file read via Repo.archive().
- [GHSA-59cr-6r3x-644w](https://osv.dev/vulnerability/GHSA-59cr-6r3x-644w); CVE-2026-100689; MODERATE; affected `introduced=0, fixed=3.1.62`; fix floor `3.1.62`. GitPython submodule update path traversal can write outside the repository.
- [GHSA-5xxx-qhh7-9287](https://osv.dev/vulnerability/GHSA-5xxx-qhh7-9287); CVE-2026-78678; MODERATE; affected `introduced=0, fixed=3.1.59`; fix floor `3.1.59`. GitPython: Incomplete unsafe_git_revision_options denylist omits --contents/-S, enabling arbitrary file read via Repo.blame().
- [GHSA-6p8h-3wgx-97gf](https://osv.dev/vulnerability/GHSA-6p8h-3wgx-97gf); CVE-2026-73623; HIGH; affected `introduced=0, fixed=3.1.54`; fix floor `3.1.54`. GitPython: Incomplete unsafe_git_clone_options denylist omits --template enabling arbitrary command execution via clone hooks.
- [GHSA-7833-fr7j-v32q](https://osv.dev/vulnerability/GHSA-7833-fr7j-v32q); CVE-2026-78675; HIGH; affected `introduced=0, fixed=3.1.59`; fix floor `3.1.59`. GitPython: Arbitrary local file content disclosure via [include] directive in untrusted .gitmodules (SubmoduleConfigParser never disables merge_includes).
- [GHSA-83vg-56qc-22m7](https://osv.dev/vulnerability/GHSA-83vg-56qc-22m7); CVE-2026-114145; HIGH; affected `introduced=0, fixed=3.2.1`; fix floor `3.2.1`. GitPython validates a submodule's ".git" path only after cloning into it (RCE).
- [GHSA-8mcc-hrx5-hvxc](https://osv.dev/vulnerability/GHSA-8mcc-hrx5-hvxc); CVE-2026-78677; HIGH; affected `introduced=0, fixed=3.1.59`; fix floor `3.1.59`. GitPython: clone_from()/clone() omit --separate-git-dir from unsafe_git_clone_options, enabling arbitrary git-directory creation outside the destination.
- [GHSA-94p4-4cq8-9g67](https://osv.dev/vulnerability/GHSA-94p4-4cq8-9g67); CVE-2026-73622; HIGH; affected `introduced=0, fixed=3.1.55`; fix floor `3.1.55`. GitPython: Environment-variable exfiltration via Repo.create_remote() / Remote.add() URL (incomplete fix of GHSA-rwj8-pgh3-r573).
- [GHSA-956x-8gvw-wg5v](https://osv.dev/vulnerability/GHSA-956x-8gvw-wg5v); CVE-2026-67323; HIGH; affected `introduced=0, fixed=3.1.51`; fix floor `3.1.51`. GitPython: command injection via unguarded Git options in Repo.archive(), git.ls_remote(), and arbitrary file overwrite via Repo.iter_commits() / Repo.blame().
- [GHSA-9rj7-rf2p-w77r](https://osv.dev/vulnerability/GHSA-9rj7-rf2p-w77r); CVE-2026-76218; HIGH; affected `introduced=0, fixed=3.1.58`; fix floor `3.1.58`. GitPython: Unguarded git option forwarding in Repo.init enables arbitrary command execution via --template clone hooks.
- [GHSA-f9j4-qggq-h239](https://osv.dev/vulnerability/GHSA-f9j4-qggq-h239); CVE-2026-110858; HIGH; affected `introduced=3.1.30, fixed=3.2.0`; fix floor `3.2.0`. GitPython Remote.pull() refspec bypasses the --upload-pack unsafe-option guard, enabling arbitrary command execution.
- [GHSA-fjr4-x663-mwxc](https://osv.dev/vulnerability/GHSA-fjr4-x663-mwxc); CVE-2026-73624; HIGH; affected `introduced=0, fixed=3.1.54`; fix floor `3.1.54`. GitPython: Arbitrary file overwrite via git diff --output argument injection in Diffable.diff (key- and value-controlled).
- [GHSA-fx3j-rwgx-fr94](https://osv.dev/vulnerability/GHSA-fx3j-rwgx-fr94); CVE-2026-110855; MODERATE; affected `introduced=0, fixed=3.2.0`; fix floor `3.2.0`. GitPython: separate_git_dir leaks env vars via crafted .gitmodules submodule name.
- [GHSA-g5vv-9gxw-82hx](https://osv.dev/vulnerability/GHSA-g5vv-9gxw-82hx); CVE-2026-87819; HIGH; affected `introduced=0, fixed=3.1.60`; fix floor `3.1.60`. GitPython: Denial of Service via catastrophic backtracking (ReDoS) in Actor.name_email_regex — commit author/committer field parsing.
- [GHSA-gq48-pqfc-9p58](https://osv.dev/vulnerability/GHSA-gq48-pqfc-9p58); CVE-2026-110860; MODERATE; affected `introduced=0, fixed=3.2.0`; fix floor `3.2.0`. GitPython: Submodule.move() follows an attacker-committed intermediate symlink outside the worktree.
- [GHSA-hh9p-6wh2-4mfc](https://osv.dev/vulnerability/GHSA-hh9p-6wh2-4mfc); CVE-2026-76217; MODERATE; affected `introduced=0, fixed=3.1.58`; fix floor `3.1.58`. GitPython: Arbitrary file read via --pathspec-from-file in IndexFile.remove() and Head.checkout().
- [GHSA-hmq2-w58f-27jc](https://osv.dev/vulnerability/GHSA-hmq2-w58f-27jc); CVE-2026-76222; HIGH; affected `introduced=0, fixed=3.1.58`; fix floor `3.1.58`. GitPython: Arbitrary Git Repository Creation Outside the Working Tree via Unvalidated .gitmodules Submodule Name in GitPython.
- [GHSA-jm78-9fvv-mhgr](https://osv.dev/vulnerability/GHSA-jm78-9fvv-mhgr); CVE-2026-76221; HIGH; affected `introduced=0, fixed=3.1.58`; fix floor `3.1.58`. GitPython: git-config OPTION-name injection via =/#/whitespace bypasses name validator, enabling forged core.sshCommand/hooksPath (RCE).
- [GHSA-m64x-33q8-m5h7](https://osv.dev/vulnerability/GHSA-m64x-33q8-m5h7); CVE-2026-110856; HIGH; affected `introduced=0, fixed=3.2.0`; fix floor `3.2.0`. GitPython parse_actor_and_date() is vulnerable to quadratic backtracking on malformed identity lines.
- [GHSA-p538-c434-8v24](https://osv.dev/vulnerability/GHSA-p538-c434-8v24); CVE-2026-73621; MODERATE; affected `introduced=0, fixed=3.1.56`; fix floor `3.1.56`. GitPython: Arbitrary file truncation via git rev-list --output argument injection in unguarded Commit.count.
- [GHSA-r9mr-m37c-5fr3](https://osv.dev/vulnerability/GHSA-r9mr-m37c-5fr3); CVE-2026-73625; HIGH; affected `introduced=0, fixed=3.1.54`; fix floor `3.1.54`. GitPython: Unsafe git option guard bypass via single-character kwarg value token smuggling enables arbitrary command execution.
- [GHSA-rwj8-pgh3-r573](https://osv.dev/vulnerability/GHSA-rwj8-pgh3-r573); CVE-2026-67322; HIGH; affected `introduced=0, fixed=3.1.52`; fix floor `3.1.52`. GitPython: Environment-variable exfiltration via os.path.expandvars() on Repo.clone_from() URL.
- [GHSA-v396-v7q4-x2qj](https://osv.dev/vulnerability/GHSA-v396-v7q4-x2qj); CVE-2026-67324; HIGH; affected `introduced=3.1.50, fixed=3.1.51`; fix floor `3.1.51`. GitPython unsafe clone option gate bypass through joined short options.
- [GHSA-w8jc-g24h-crhw](https://osv.dev/vulnerability/GHSA-w8jc-g24h-crhw); CVE-2026-110857; HIGH; affected `introduced=0, fixed=3.2.0`; fix floor `3.2.0`. GitPython command wrappers omit unsafe protocol and option checks.
- [GHSA-wvpp-8hx9-p66j](https://osv.dev/vulnerability/GHSA-wvpp-8hx9-p66j); CVE-2026-76220; HIGH; affected `introduced=0, fixed=3.1.58`; fix floor `3.1.58`. GitPython: Unsafe git option guard bypass via split_single_char_options=False short-option token smuggling enables command execution.

**Mako** - installed `1.3.12`, declared `not directly declared`. Alembic dependency; Windows TemplateLookup with attacker-controlled drive-letter URI is conditional. No public template-URI input found. APPLICABILITY CONDITIONAL.

- [GHSA-5639-2j2p-m4mx](https://osv.dev/vulnerability/GHSA-5639-2j2p-m4mx); CVE-2026-102991; MODERATE; affected `introduced=0, fixed=1.4.2`; fix floor `1.4.2`. Mako: Path traversal via drive-letter URI on Windows in TemplateLookup.

**pillow** - installed `12.2.0`, declared `not directly declared`. Installed through Streamlit; no operational backend image parser found. REQUIRES INVESTIGATION for the listed decoder/format conditions and any external tooling consumers.

- [GHSA-22hg-r758-rrw9](https://osv.dev/vulnerability/GHSA-22hg-r758-rrw9); CVE-2026-112390; HIGH; affected `introduced=7.2.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Infinite loop in MIC n_frames when the embedded TIFF.
- [GHSA-24rc-8hj2-v98c](https://osv.dev/vulnerability/GHSA-24rc-8hj2-v98c); CVE-2026-96638; MODERATE; affected `introduced=9.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: BMP RLE decoder memory-amplification DoS via unbounded delta escape / absolute mode.
- [GHSA-254f-3936-288h](https://osv.dev/vulnerability/GHSA-254f-3936-288h); CVE-2026-112391; MODERATE; affected `introduced=5.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: PdfParser can recurse without limit in get_value() and linearize_page_tree().
- [GHSA-27h8-gf7j-v5hc](https://osv.dev/vulnerability/GHSA-27h8-gf7j-v5hc); CVE-2026-112392; HIGH; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: NULL dereference in ImagingExpand via rank filters on zero-size images.
- [GHSA-332p-7hrc-92wf](https://osv.dev/vulnerability/GHSA-332p-7hrc-92wf); CVE-2026-112393; CRITICAL; affected `introduced=2.0.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Heap buffer overflow in _tiffWriteProc when saving TIFF to BytesIO.
- [GHSA-3j72-p6qg-6xp7](https://osv.dev/vulnerability/GHSA-3j72-p6qg-6xp7); CVE-2026-96642; HIGH; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: TarIO negative size field causes infinite CPU-spin loop.
- [GHSA-4558-3h8r-v8xp](https://osv.dev/vulnerability/GHSA-4558-3h8r-v8xp); CVE-2026-112394; MODERATE; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: P;2L and P;4L decoders may read 1 to 3 bytes past the passed buffer size.
- [GHSA-45hq-cxwh-f6vc](https://osv.dev/vulnerability/GHSA-45hq-cxwh-f6vc); CVE-2026-55379; HIGH; affected `introduced=0, fixed=12.3.0`; fix floor `12.3.0`. Pillow BdfFontFile: Image.new() called without _decompression_bomb_check() — bomb protection bypass via font loading.
- [GHSA-462x-pgg6-55fp](https://osv.dev/vulnerability/GHSA-462x-pgg6-55fp); CVE-2026-112395; MODERATE; affected `introduced=8.2.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow tiled-TIFF decoder reads past tile buffer in copy4 (Unpack.c:1290).
- [GHSA-4rm8-3hmm-39fg](https://osv.dev/vulnerability/GHSA-4rm8-3hmm-39fg); CVE-2026-96641; MODERATE; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Reachable undefined behavior in native integer operations, potentially leading to denial of service or logic integrity compromise.
- [GHSA-4rr5-89j8-mwwm](https://osv.dev/vulnerability/GHSA-4rr5-89j8-mwwm); CVE-2026-112396; MODERATE; affected `introduced=11.3.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Heap use-after-free when encoding TIFF to an in-memory buffer.
- [GHSA-4x4j-2g7c-83w6](https://osv.dev/vulnerability/GHSA-4x4j-2g7c-83w6); CVE-2026-55798; MODERATE; affected `introduced=0, fixed=12.3.0`; fix floor `12.3.0`. Pillow: WindowsViewer.get_command() OS command injection via unescaped shell path.
- [GHSA-58r4-6rv3-gfh8](https://osv.dev/vulnerability/GHSA-58r4-6rv3-gfh8); CVE-2026-112397; HIGH; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Out-of-bounds access in _imagingmorph on a zero-width image.
- [GHSA-5x8w-8jj5-q52h](https://osv.dev/vulnerability/GHSA-5x8w-8jj5-q52h); CVE-2026-112398; CRITICAL; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Heap buffer overflow in FlashPix (FPX) JPEG decoding leads to code execution.
- [GHSA-5x94-69rx-g8h2](https://osv.dev/vulnerability/GHSA-5x94-69rx-g8h2); CVE-2026-54060; HIGH; affected `introduced=0, fixed=12.3.0`; fix floor `12.3.0`. Pillow: FontFile.compile(): Image.new() called without _decompression_bomb_check().
- [GHSA-5xm2-6676-qcp9](https://osv.dev/vulnerability/GHSA-5xm2-6676-qcp9); CVE-2026-112399; HIGH; affected `introduced=8.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: APNG background disposal allocates full canvas before decompression bomb check.
- [GHSA-62p4-gmf7-7g93](https://osv.dev/vulnerability/GHSA-62p4-gmf7-7g93); CVE-2026-54058; HIGH; affected `introduced=0, fixed=12.3.0`; fix floor `12.3.0`. Pillow: Out-of-bounds read via attacker-controlled row stride on Pillow's mmap path (McIdas AREA files).
- [GHSA-654x-cwwv-5j9c](https://osv.dev/vulnerability/GHSA-654x-cwwv-5j9c); CVE-2026-114501; MODERATE; affected `introduced=11.2.1, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Arrow export leaks stale heap memory when PILLOW_ALIGNMENT > 1.
- [GHSA-65qm-jvmh-6pqg](https://osv.dev/vulnerability/GHSA-65qm-jvmh-6pqg); CVE-2026-112400; HIGH; affected `introduced=9.2.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: GIF seek keeps rejected size after DecompressionBombError, allowing DoS.
- [GHSA-6r8x-57c9-28j4](https://osv.dev/vulnerability/GHSA-6r8x-57c9-28j4); CVE-2026-59199; HIGH; affected `introduced=0, fixed=12.3.0`; fix floor `12.3.0`. Pillow: Heap out-of-bounds write Image.paste() / Image.crop() via signed coordinate overflow.
- [GHSA-74r2-7ff9-mjj2](https://osv.dev/vulnerability/GHSA-74r2-7ff9-mjj2); CVE-2026-112401; MODERATE; affected `introduced=5.4.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Quadratic GIF comment concatenation allows DoS in Image.open().
- [GHSA-78g4-xqwv-q3g8](https://osv.dev/vulnerability/GHSA-78g4-xqwv-q3g8); no CVE assigned; HIGH; affected `introduced=11.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Bundled libopenjp2 2.5.4 in all wheels since 11.1.0 carries OSV-2025-219 heap-buffer-overflow write reachable from Image.open().load().
- [GHSA-7mwm-ghpf-9vrm](https://osv.dev/vulnerability/GHSA-7mwm-ghpf-9vrm); CVE-2026-112402; HIGH; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Double free in ImagingScaleAffine on calloc failure via Image.transform.
- [GHSA-8g5g-8vmr-9782](https://osv.dev/vulnerability/GHSA-8g5g-8vmr-9782); CVE-2026-112403; CRITICAL; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Heap buffer overflow in ImagingJpegDecode.
- [GHSA-8v84-f9pq-wr9x](https://osv.dev/vulnerability/GHSA-8v84-f9pq-wr9x); CVE-2026-54059; HIGH; affected `introduced=0, fixed=12.3.0`; fix floor `12.3.0`. Pillow PcfFontFile._load_bitmaps(): Image.frombytes() called without _decompression_bomb_check() — bomb protection bypass via PCF font loading.
- [GHSA-9hw9-ch79-4vh6](https://osv.dev/vulnerability/GHSA-9hw9-ch79-4vh6); CVE-2026-59205; HIGH; affected `introduced=0, fixed=12.3.0`; fix floor `12.3.0`. Pillow: Controlled heap out-of-bounds write in Pillow ImageCmsTransform.apply() via output mode mismatch.
- [GHSA-9v9v-9qvf-h2hj](https://osv.dev/vulnerability/GHSA-9v9v-9qvf-h2hj); CVE-2026-96644; HIGH; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Heap over-read in WMF/EMF rendering via 16-bit dimension truncation (Windows builds).
- [GHSA-c6hw-5grf-ff96](https://osv.dev/vulnerability/GHSA-c6hw-5grf-ff96); CVE-2026-112404; HIGH; affected `introduced=8.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: OOB read in TiffDecode.c tile and RGBA paths leaks heap memory into pixels.
- [GHSA-cp9v-662q-vvx9](https://osv.dev/vulnerability/GHSA-cp9v-662q-vvx9); CVE-2026-112405; HIGH; affected `introduced=12.0.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: NULL pointer dereference in Image.merge via an unvalidated band 0.
- [GHSA-f2g6-542v-9j58](https://osv.dev/vulnerability/GHSA-f2g6-542v-9j58); CVE-2026-112406; HIGH; affected `introduced=5.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Infinite loop in PdfParser.rewrite_pages on page tree Parent cycle.
- [GHSA-fc9g-5qg7-mf45](https://osv.dev/vulnerability/GHSA-fc9g-5qg7-mf45); CVE-2026-112891; MODERATE; affected `introduced=9.2.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Quadratic GIF comment copying during save.
- [GHSA-fj7v-r99m-22gq](https://osv.dev/vulnerability/GHSA-fj7v-r99m-22gq); CVE-2026-59198; MODERATE; affected `introduced=5.2.0, fixed=12.3.0`; fix floor `12.3.0`. Pillow TGA RLE encoder can serialize up to ~57 KB of adjacent heap data into generated images.
- [GHSA-g4qv-2jxx-769h](https://osv.dev/vulnerability/GHSA-g4qv-2jxx-769h); CVE-2026-96643; HIGH; affected `introduced=11.0.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: PNG eXIf chunk makes EXIF parsing run in quadratic time.
- [GHSA-g7cr-3p24-7wf7](https://osv.dev/vulnerability/GHSA-g7cr-3p24-7wf7); CVE-2026-96778; HIGH; affected `introduced=9.4.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Heap buffer overflow writing JPEG comment after ICC profile fills buffer.
- [GHSA-g842-9rc4-69pw](https://osv.dev/vulnerability/GHSA-g842-9rc4-69pw); CVE-2026-96637; HIGH; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Decompression bomb check bypass in SpiderImagePlugin.seek() leads to unbounded allocation DoS.
- [GHSA-gg2r-wvfm-q9rx](https://osv.dev/vulnerability/GHSA-gg2r-wvfm-q9rx); CVE-2026-112892; HIGH; affected `introduced=4.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: MSP RLE decoder expands a tiny file into unbounded memory.
- [GHSA-j4m9-6w36-pw47](https://osv.dev/vulnerability/GHSA-j4m9-6w36-pw47); CVE-2026-112893; HIGH; affected `introduced=10.0.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Invalid free in FreeType glyph rendering when a stroker is active.
- [GHSA-jg86-v3jv-hrpm](https://osv.dev/vulnerability/GHSA-jg86-v3jv-hrpm); CVE-2026-112894; HIGH; affected `introduced=5.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Quadratic-time DoS in PDF save_all (PdfParser.next_object_id).
- [GHSA-jjj6-mw9f-p565](https://osv.dev/vulnerability/GHSA-jjj6-mw9f-p565); CVE-2026-59200; HIGH; affected `introduced=5.1.0, fixed=12.3.0`; fix floor `12.3.0`. Pillow: Decompression Bomb DoS via PdfParser.PdfStream.decode().
- [GHSA-mrfp-p49p-3hf2](https://osv.dev/vulnerability/GHSA-mrfp-p49p-3hf2); CVE-2026-96640; HIGH; affected `introduced=5.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow PDF append accepts malformed shared page-tree DAG causing resource exhaustion.
- [GHSA-p4wg-p73j-c528](https://osv.dev/vulnerability/GHSA-p4wg-p73j-c528); CVE-2026-112895; HIGH; affected `introduced=5.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Unbounded recursion parsing a PDF page tree or trailer chain (incomplete fix for CVE-2026-42310).
- [GHSA-p8hx-v2p6-rp84](https://osv.dev/vulnerability/GHSA-p8hx-v2p6-rp84); CVE-2026-96636; MODERATE; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Decompression-bomb protection bypass via multi-frame seek() in MPO and DCX (MpoImageFile.seek / DcxImageFile.seek).
- [GHSA-pchr-8j38-3x4p](https://osv.dev/vulnerability/GHSA-pchr-8j38-3x4p); CVE-2026-112896; HIGH; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: TIFF encoder ColorMap plane-size mismatch causes a heap out-of-bounds read.
- [GHSA-pg7v-jwj7-p798](https://osv.dev/vulnerability/GHSA-pg7v-jwj7-p798); CVE-2026-59203; MODERATE; affected `introduced=12.0.0, fixed=12.3.0`; fix floor `12.3.0`. Pillow EpsImagePlugin negative %%BeginBinary byte count causes infinite loop denial of service.
- [GHSA-phj9-mv4w-65pm](https://osv.dev/vulnerability/GHSA-phj9-mv4w-65pm); CVE-2026-55380; HIGH; affected `introduced=0, fixed=12.3.0`; fix floor `12.3.0`. Pillow GdImageFile._open(): image dimensions accepted without _decompression_bomb_check().
- [GHSA-q45j-58j2-45rg](https://osv.dev/vulnerability/GHSA-q45j-58j2-45rg); CVE-2026-112897; HIGH; affected `introduced=5.3.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: TiffDecode returns uninitialized memory as pixels for short JPEG strips.
- [GHSA-rfgq-q3w2-pmv2](https://osv.dev/vulnerability/GHSA-rfgq-q3w2-pmv2); CVE-2026-112898; MODERATE; affected `introduced=9.1.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Image.quantize() with empty palette leaks uninitialized stack memory.
- [GHSA-v9pv-5gc8-w2m6](https://osv.dev/vulnerability/GHSA-v9pv-5gc8-w2m6); CVE-2026-96639; CRITICAL; affected `introduced=11.0.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow multi-frame loaders can reuse stale native image storage after mode transitions.
- [GHSA-vjc4-5qp5-m44j](https://osv.dev/vulnerability/GHSA-vjc4-5qp5-m44j); CVE-2026-59204; HIGH; affected `introduced=8.2.0, fixed=12.3.0`; fix floor `12.3.0`. Pillow JPEG2000 tiled decode retains a growing scratch buffer and can be used for denial of service.
- [GHSA-vx6w-vv9f-6gvg](https://osv.dev/vulnerability/GHSA-vx6w-vv9f-6gvg); CVE-2026-112899; MODERATE; affected `introduced=2.3.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: EPS load(scale) lets Ghostscript render past the decompression bomb limit.
- [GHSA-w889-685w-c8fh](https://osv.dev/vulnerability/GHSA-w889-685w-c8fh); CVE-2026-112900; CRITICAL; affected `introduced=2.6.0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Argument Injection in Ghostscript call, potentially leading into RCE.
- [GHSA-xgh8-jp6q-p5x8](https://osv.dev/vulnerability/GHSA-xgh8-jp6q-p5x8); CVE-2026-112901; MODERATE; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: ReDoS in XbmImagePlugin: 512-byte file stalls Image.open() for minutes.
- [GHSA-xj96-63gp-2gmr](https://osv.dev/vulnerability/GHSA-xj96-63gp-2gmr); CVE-2026-59197; HIGH; affected `introduced=0, fixed=12.3.0`; fix floor `12.3.0`. Pillow: Heap out-of-bounds write in ImageFilter.RankFilter via integer overflow in ImagingExpand.
- [GHSA-xvh5-g6gv-559v](https://osv.dev/vulnerability/GHSA-xvh5-g6gv-559v); CVE-2026-112902; HIGH; affected `introduced=0, fixed=13.0.0`; fix floor `13.0.0`. Pillow: Memory disclosure and segfault in libtiff encoder via crafted TIFF tags.

**pip** - installed `25.2`, declared `not directly declared`. Packaging tool, not a request handler. Archive/index/link/symlink conditions vary per advisory. APPLICABILITY CONDITIONAL; only a public prebuilt wheel was installed in a disposable environment.

- [GHSA-4xh5-x5gv-qwph](https://osv.dev/vulnerability/GHSA-4xh5-x5gv-qwph); CVE-2025-8869; MODERATE; affected `introduced=0, fixed=25.3`; fix floor `25.3`. pip's fallback tar extraction doesn't check symbolic links point to extraction directory.
- [GHSA-58qw-9mgm-455v](https://osv.dev/vulnerability/GHSA-58qw-9mgm-455v); CVE-2026-3219; MODERATE; affected `introduced=0, fixed=26.1`; fix floor `26.1`. pip has an interpretation conflict due to handling both concatenated tar and ZIP files as ZIP files.
- [GHSA-6vgw-5pg2-w6jp](https://osv.dev/vulnerability/GHSA-6vgw-5pg2-w6jp); CVE-2026-1703; LOW; affected `introduced=0, fixed=26.0`; fix floor `26.0`. pip Path Traversal vulnerability.
- [GHSA-jp4c-xjxw-mgf9](https://osv.dev/vulnerability/GHSA-jp4c-xjxw-mgf9); CVE-2026-6357; MODERATE; affected `introduced=0, fixed=26.1`; fix floor `26.1`. pip Vulnerable to Inclusion of Functionality from Untrusted Control Sphere.
- [GHSA-qwm4-qh6w-59xr](https://osv.dev/vulnerability/GHSA-qwm4-qh6w-59xr); CVE-2026-13346; MODERATE; affected `introduced=0, fixed=26.2.0`; fix floor `26.2.0`. pip would incorrectly handle doubly-encoded package URLs from indexes.
- [GHSA-wf93-45jw-7689](https://osv.dev/vulnerability/GHSA-wf93-45jw-7689); CVE-2026-8643; MODERATE; affected `introduced=0, fixed=26.1.2`; fix floor `26.1.2`. pip: Path traversal in console_scripts/gui_scripts entry point names allows installing scripts outside of target directory.

**PyJWT** - installed `2.13.0`, declared `not directly declared`. Installed but not declared and no backend import found; actual JWT implementation imports jose. REQUIRES INVESTIGATION of separate JWKS/decoding consumers and each advisory prerequisite.

- [GHSA-2gx3-rcp4-g85q](https://osv.dev/vulnerability/GHSA-2gx3-rcp4-g85q); CVE-2026-101917; MODERATE; affected `introduced=0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT: PyJWKClient still amplifies unauthenticated JWKS fetches on unknown kid values (incomplete fix of CVE-2026-48524).
- [GHSA-42vr-xj54-vc7v](https://osv.dev/vulnerability/GHSA-42vr-xj54-vc7v); CVE-2026-101918; MODERATE; affected `introduced=2.0.0a1, fixed=2.15.0`; fix floor `2.15.0`. PyJWT: Unauthenticated RecursionError DoS in pre-verification payload parse (PyJWKClient.get_signing_key_from_jwt / verify_signature=False).
- [GHSA-8wjv-2p76-3863](https://osv.dev/vulnerability/GHSA-8wjv-2p76-3863); CVE-2026-102265; MODERATE; affected `introduced=2.13.0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT: Uncaught RecursionError in jwt.decode() on deeply nested token header.
- [GHSA-9j54-fg26-wv3r](https://osv.dev/vulnerability/GHSA-9j54-fg26-wv3r); CVE-2026-102266; HIGH; affected `introduced=2.13.0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT: PyJWK accepts empty HMAC keys, bypassing PyJWT's empty-key validation.
- [GHSA-9v7f-9g4p-ffgj](https://osv.dev/vulnerability/GHSA-9v7f-9g4p-ffgj); CVE-2026-102267; HIGH; affected `introduced=0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT: PyJWKClient follows redirects when fetching JWKS.
- [GHSA-ffc3-869f-jxw9](https://osv.dev/vulnerability/GHSA-ffc3-869f-jxw9); CVE-2026-102268; CRITICAL; affected `introduced=0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT: Asymmetric-PEM detection bypass: whitespace/line-ending-mutated public keys skip the HS/asymmetric confusion guard.
- [GHSA-gvp8-978c-rx2q](https://osv.dev/vulnerability/GHSA-gvp8-978c-rx2q); CVE-2026-103001; MODERATE; affected `introduced=2.11.0, last_affected=2.13.0`; fix floor `none published`. PyJWT.decode() reintroduces options-dict mutation, enabling silent claim-verification bypass on dict reuse.
- [GHSA-hxm8-2xgr-2p9m](https://osv.dev/vulnerability/GHSA-hxm8-2xgr-2p9m); CVE-2026-102269; MODERATE; affected `introduced=0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT: Non-canonical signature segments enable raw-token revocation bypass.
- [GHSA-jwrc-g2q2-pq5p](https://osv.dev/vulnerability/GHSA-jwrc-g2q2-pq5p); CVE-2026-102270; MODERATE; affected `introduced=0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT: ReDoS vulnerability when calling the is_pem_format function..
- [GHSA-p4g4-x82p-q773](https://osv.dev/vulnerability/GHSA-p4g4-x82p-q773); CVE-2026-102271; HIGH; affected `introduced=2.4.0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT: Public keys in DER form are accepted as HMAC secrets, bypassing the CVE-2022-29217 guard.
- [GHSA-pxh4-856f-4h89](https://osv.dev/vulnerability/GHSA-pxh4-856f-4h89); no CVE assigned; HIGH; affected `introduced=0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT: HS256/384/512 verify accepts empty HMAC key via oct JWK (PyJWK/PyJWKClient) enabling token forgery.
- [GHSA-r6x4-923q-g947](https://osv.dev/vulnerability/GHSA-r6x4-923q-g947); CVE-2026-102272; HIGH; affected `introduced=2.13.0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT BOM Bypass.
- [GHSA-w2cx-738m-mc7w](https://osv.dev/vulnerability/GHSA-w2cx-738m-mc7w); CVE-2026-102273; HIGH; affected `introduced=2.13.0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT accepts public JWK containers as HMAC secrets.
- [GHSA-w6j9-cwv2-h6wq](https://osv.dev/vulnerability/GHSA-w6j9-cwv2-h6wq); CVE-2026-102274; MODERATE; affected `introduced=2.9.0, fixed=2.14.0`; fix floor `2.14.0`. PyJWT: Malformed RSA JWK aborts parsing of an entire JWK Set.
- [GHSA-x33g-cr3x-6449](https://osv.dev/vulnerability/GHSA-x33g-cr3x-6449); CVE-2026-102275; MODERATE; affected `introduced=2.1.0, fixed=2.15.0`; fix floor `2.15.0`. PyJWT accepts inconsistent OKP x/d JWKs, causing public/private key identity confusion.

**python-jose** - installed `3.5.0`, declared `3.5.0`. Direct auth dependency. DER-public-key/HMAC confusion requires the asymmetric public-key and algorithm-mixing predicates. Current explicit HS256/shared-secret boundary does not establish that scenario. APPLICABILITY CONDITIONAL; no JWT policy change authorized and no patched release is listed in this record.

- [GHSA-3qf3-8w2g-rqmx](https://osv.dev/vulnerability/GHSA-3qf3-8w2g-rqmx); CVE-2024-33663, CVE-2026-85394; CRITICAL; affected `introduced=0, last_affected=3.5.0`; fix floor `none published`. python-jose algorithm confusion guard bypassed by DER-encoded public keys.

**soupsieve** - installed `2.8.4`, declared `not directly declared`. BeautifulSoup4 dependency, potentially through market-data parsing. Attacker-controlled CSS selectors and regex shapes require investigation. APPLICABILITY CONDITIONAL.

- [GHSA-gjv8-xp57-g29c](https://osv.dev/vulnerability/GHSA-gjv8-xp57-g29c); CVE-2026-86000; MODERATE; affected `introduced=0, fixed=2.9.0`; fix floor `2.9.0`. Soup Sieve: Polynomial-time ReDoS (O(n²)) in the IDENTIFIER / VALUE selector sub-patterns.
- [GHSA-j934-xhv5-fg8f](https://osv.dev/vulnerability/GHSA-j934-xhv5-fg8f); CVE-2026-85999; MODERATE; affected `introduced=0, fixed=2.9.0`; fix floor `2.9.0`. Soup Sieve: Polynomial-time ReDoS (O(n²)) in the whitespace/comment trimming regex RE_WS_END (triggers on VALID selectors).

**starlette** - installed `1.1.0`, declared `not directly declared`. Runtime FastAPI dependency. Form-limit GHSA-82w8-qh3p-5jfq APPLICABILITY CONFIRMED by the bounded probe above; path/authority GHSA-jp82-jpqv-5vv3 APPLICABILITY CONDITIONAL on malformed ASGI path and security use of request.url before routing.

- [GHSA-82w8-qh3p-5jfq](https://osv.dev/vulnerability/GHSA-82w8-qh3p-5jfq); CVE-2026-54283; HIGH; affected `introduced=0.4.1, fixed=1.3.1`; fix floor `1.3.1`. Starlette: request.form() limits silently ignored for application/x-www-form-urlencoded enable DoS.
- [GHSA-jp82-jpqv-5vv3](https://osv.dev/vulnerability/GHSA-jp82-jpqv-5vv3); CVE-2026-54282; LOW; affected `introduced=0, fixed=1.3.0`; fix floor `1.3.0`. Starlette: Unvalidated request path concatenated into authority poisons request.url.hostname.

**urllib3** - installed `2.7.0`, declared `not directly declared`. Requests/market/provider HTTP dependency. Proxy TLS, deflate and chunk-header conditions vary per record and remote response. APPLICABILITY CONDITIONAL; no provider calls or malicious streams were tested.

- [GHSA-8988-9cw3-xx77](https://osv.dev/vulnerability/GHSA-8988-9cw3-xx77); CVE-2026-97687; HIGH; affected `introduced=1.26.0, fixed=2.8.0`; fix floor `2.8.0`. urllib3: HTTPS proxy TLS configuration may be ignored or overridden.
- [GHSA-gh4c-6fx4-qh6g](https://osv.dev/vulnerability/GHSA-gh4c-6fx4-qh6g); CVE-2026-97688; MODERATE; affected `introduced=2.6.2, fixed=2.8.0`; fix floor `2.8.0`. urllib3: Chunked Deflate streaming can enter an infinite loop.
- [GHSA-vxq7-64xx-v4gw](https://osv.dev/vulnerability/GHSA-vxq7-64xx-v4gw); CVE-2026-97689; HIGH; affected `introduced=1.10.3, fixed=2.8.0`; fix floor `2.8.0`. urllib3: HTTPResponse.stream()/read_chunked() buffers an unbounded chunk-size line into memory.

**pytest declaration only** - declared `7.4.2`, installed `9.1.1`.
[GHSA-6w46-j5rx-g56g / CVE-2025-71176](https://osv.dev/vulnerability/GHSA-6w46-j5rx-g56g),
MODERATE; affected <9.0.3, fixed >=9.0.3. CONFIRMED VULNERABLE VERSION for the
manifest pin; NOT AFFECTED for the installed and candidate pytest. Exploitation
requires unsafe local temporary-directory handling/access. The isolated tests
used exclusive fresh directories. No pytest pin change was authorized here.

</details>

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
