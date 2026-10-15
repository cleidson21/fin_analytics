# Structural Foreign Key Remediation — `position_snapshots`

**Document Version:** 1.2.0\\
**Status:** `IMPLEMENTED / FINDINGS REMEDIATED / TESTED IN ISOLATED SQLITE / AWAITING INDEPENDENT DELTA REVIEW / NO DEPLOYMENT`\\
**Related ADRs:** ADR-014, ADR-029\\
**Related Finding:** `INF-R3D-01`\\
**Alembic Revision:** `b7e2d1a4c9f3` (successor of `4f9c2d7e1a6b`)\\
**Git Baseline:** `c4a8bba534049f5671367cab10b431fc9b49b0ce`

## 1. Evidence boundary

The earlier authorized read-only inspection of MyProfit run
`6c90ea3c-d6f4-4d2e-9023-6218ee92f893` established only that the run remained
`RUNNING`, with `finished_at = null`; the returned `account_id`,
`reference_date`, and `report` fields were present with `null`. This is
compatible with a failure before the primary confirmation commit, but does not
prove that no financial row was written and does not locate the original
exception on its own. Subsequent backend traceback evidence confirmed the
invalid physical foreign key as the import failure, and the user confirmed that
MyProfit import resumed after the targeted operational SQLite hotfix removed
only that invalid constraint. This reconciliation does not reinvestigate the
HTTP failure.

Separately, an isolated SQLite fixture reproduces the deterministic error
`foreign key mismatch - "position_snapshots" referencing "accounts"` when all
of the following are true:

- `position_snapshots.account_id` physically references `accounts.id`;
- `accounts` instead has the composite key `(provider, external_id)` and no
  `id` column; and
- `PRAGMA foreign_keys=ON` is active.

This proves the structural mechanism independently of the operational incident.

## 2. Provenance correction

The canonical Alembic migration `a1b2c3d4e5f6_wealth_phase1.py` does **not**
declare the invalid account foreign key; it declares only
`asset_id -> assets.id`. Revision `08aabd3f3f30` later adds `current_value`.
The legacy SQL file `database/migrations/005_open_finance.sql` does declare
`account_id REFERENCES accounts(id)`, so it is a possible source of historical
drift, but the exact path that produced the reported operational schema remains
unestablished.

The ORM contract already treats `account_id` as a mandatory indexed logical
identifier with no physical foreign key. The corrective revision therefore
removes only the reported invalid physical constraint and preserves the valid
asset relationship.

## 3. Corrective revision

Revision `b7e2d1a4c9f3` is a conditional, fail-closed SQLite repair:

1. If the invalid `account_id -> accounts.id` foreign key is absent, the
   revision performs no table rewrite and only advances Alembic bookkeeping.
2. If the invalid foreign key is present, the revision requires the exact
   supported 12-column shape, exactly the invalid account FK plus the valid
   `asset_id -> assets.id` FK, no dependent triggers or views, and no inbound
   foreign key from any real SQLite table, including composite relationships.
3. The four secondary indexes are validated by name, ordered columns,
   uniqueness, ASC/DESC, collation, partial status, expression status, full
   `index_xinfo` key shape, and their `sqlite_master` DDL presence.
4. Only after those checks does Alembic batch-recreate the table using an
   explicit `copy_from` definition. This avoids SQLAlchemy reflection failure
   against the nonexistent `accounts.id` target.
5. The revision preserves all rows, column types/nullability/defaults, the
   business-key UNIQUE constraint, and the four secondary indexes, then runs
   `PRAGMA foreign_key_check('position_snapshots')`.
6. Unknown columns, unexpected foreign keys, inbound foreign keys, malformed
   indexes, triggers, or views abort before batch DDL instead of risking loss.
7. Downgrade is explicitly blocked. Reintroducing an invalid constraint is
   unsafe, while a silent no-op downgrade would falsely stamp an unreverted
   physical schema.

The repair is intentionally SQLite-only. The valid
`asset_id -> assets.id` constraint remains enforced, while `account_id`
remains a logical reference.

## 4. Isolated verification

`tests/unit/test_position_snapshots_fk_remediation.py` contains twelve test
functions, expanded to twenty-two pytest cases by the index parameterization:

- reproduces the mismatch under active FK enforcement;
- preserves 223 synthetic snapshots with identical canonical SHA-256 digest;
- verifies all 12 column types, nullability, defaults and PK metadata, plus
  UNIQUE, all four indexes and the valid asset FK;
- rejects an unknown `asset_id` under `foreign_keys=ON`;
- confirms the ORM logical-account contract;
- exercises `ConfirmMyProfitAtivosSyncUseCase` with 30 synthetic rows, same-day
  UPSERT, manual preservation, and next-date history;
- proves a canonical schema is not rebuilt;
- proves unknown physical shapes fail closed;
- proves orphan asset references fail before DDL;
- proves a composite inbound FK fails before DDL while preserving source and
  dependent rows and creating no Alembic temporary table;
- rejects eleven divergent index definitions covering unexpected names, all
  four column mappings, uniqueness, DESC, collation, partial predicates,
  expressions, and unexpected column composition; and
- proves unsafe downgrade is explicitly blocked.

Both the Alembic migration connection and the `aiosqlite` use-case engine are
explicitly checked for `PRAGMA foreign_keys = 1`. The use-case test does not
exercise the HTTP router and therefore makes no claim that an HTTP 500 was
directly reproduced or eliminated.

Current results from fresh executions in this worktree:

- the two new adversarial tests: **12 passed** after parameter expansion;
- complete remediation file: **22 passed**;
- remediation + pertinent External Context migration: **27 passed**.

The historical complete-unit evidence remains **1175 passed, 2 failed**, with
the two failures limited to the unchanged `test_investments_asset_detail.py`
MagicMock/timeline cases. That full suite was not rerun in this targeted task.

All tests use disposable paths and assert that their filename is not
`fin_analytics.db`. No command in this remediation applies a revision to the
operational database.

The operational hotfix is separate from this repository revision. Per the
post-incident operational report, it preserved 223 snapshots, the valid asset
FK, `PRAGMA foreign_keys=ON`, and SQLite integrity; the user validated restored
MyProfit import. Operational Alembic bookkeeping remains at `2d6b4f8a9c1e`, so
neither `4f9c2d7e1a6b` nor `b7e2d1a4c9f3` is recorded as applied there.

## 5. Deployment gate and recovery plan

Operational deployment is not authorized. Before any future application:

1. independently review the corrected revision and tests;
2. stop all processes that can access the SQLite file;
3. create and restore-test a verified backup outside the active database path;
4. verify the actual Alembic revision and review every pending intermediate
   revision, including `4f9c2d7e1a6b` if applicable;
5. capture the pre-migration schema, row count, deterministic data digest,
   indexes, triggers/views, and `PRAGMA foreign_key_check` result;
6. apply the revision during an exclusive maintenance window;
7. repeat the same schema/data/integrity checks before restarting services; and
8. on any discrepancy, keep services stopped and restore the verified backup.

SQLite reports non-transactional DDL in this Alembic environment. The batch
table recreation must not be represented as an atomic, automatically
rollback-safe operation. Backup restoration is the operational recovery path.

The previously reported operational revision and physical schema were not
re-inspected during this code-remediation pass; they remain deployment-time
facts to verify, not assumptions embedded in the migration.

An exploratory disposable-database probe also showed that the repository-wide
Alembic graph is not a fresh-install linear chain: its two historical roots
both attempt to create `categories`, and `upgrade head` from an empty database
stops there before reaching this revision. That pre-existing bootstrap debt is
outside this targeted correction. Consequently, deployment must begin only
from an inspected, supported existing revision; this document does not claim a
fresh empty-database upgrade path.
