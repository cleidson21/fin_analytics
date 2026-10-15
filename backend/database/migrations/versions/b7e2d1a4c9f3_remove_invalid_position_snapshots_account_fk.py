"""remove_invalid_position_snapshots_account_fk

Revision ID: b7e2d1a4c9f3
Revises: 4f9c2d7e1a6b
Create Date: 2026-10-13 22:00:00.000000

Repairs a reported physical-schema drift where position_snapshots.account_id references
accounts(id), while the operational accounts table uses the composite primary key
(provider, external_id). The canonical Alembic position_snapshots migration does not
declare this foreign key; its exact historical introduction is therefore not established.

The upgrade is intentionally conditional. A canonical schema without the invalid foreign
key is left untouched. A drifted schema is rebuilt only after its relevant column shape
and foreign keys match the explicitly supported repair input.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e2d1a4c9f3"
down_revision: Union[str, Sequence[str], None] = "4f9c2d7e1a6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_EXPECTED_COLUMN_SHAPE = {
    "id": ("VARCHAR(36)", 1, None, 1, 0),
    "account_id": ("VARCHAR(36)", 1, None, 0, 0),
    "asset_id": ("VARCHAR(36)", 1, None, 0, 0),
    "reference_date": ("VARCHAR(10)", 1, None, 0, 0),
    "quantity": ("NUMERIC(18, 8)", 1, None, 0, 0),
    "avg_price": ("NUMERIC(18, 6)", 0, None, 0, 0),
    "source_type": ("VARCHAR", 1, None, 0, 0),
    "run_id": ("VARCHAR(36)", 0, None, 0, 0),
    "is_manual": ("INTEGER", 1, None, 0, 0),
    "created_at": ("DATETIME", 1, None, 0, 0),
    "updated_at": ("DATETIME", 1, None, 0, 0),
    "current_value": ("NUMERIC(18, 2)", 0, None, 0, 0),
}

_EXPECTED_SECONDARY_INDEXES = {
    "ix_position_snapshots_account_id": "account_id",
    "ix_position_snapshots_asset_id": "asset_id",
    "ix_position_snapshots_reference_date": "reference_date",
    "ix_position_snapshots_run_id": "run_id",
}


def _foreign_keys(bind) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in bind.exec_driver_sql(
            "PRAGMA foreign_key_list('position_snapshots')"
        ).mappings()
    ]


def _pragma_identifier(identifier: str) -> str:
    """Quote a schema-owned identifier for SQLite's PRAGMA argument syntax."""
    return "'" + identifier.replace("'", "''") + "'"


def _validate_secondary_indexes(bind, index_rows: list[dict[str, object]]) -> None:
    secondary_index_rows = {
        row["name"]: row for row in index_rows if row["origin"] == "c"
    }
    if set(secondary_index_rows) != set(_EXPECTED_SECONDARY_INDEXES):
        raise RuntimeError(
            "Unsupported position_snapshots secondary-index names; refusing a "
            "lossy batch rebuild."
        )

    for index_name, expected_column in _EXPECTED_SECONDARY_INDEXES.items():
        index_row = secondary_index_rows[index_name]
        pragma_name = _pragma_identifier(index_name)
        index_info = bind.exec_driver_sql(
            f"PRAGMA index_info({pragma_name})"
        ).mappings().all()
        index_xinfo = bind.exec_driver_sql(
            f"PRAGMA index_xinfo({pragma_name})"
        ).mappings().all()
        index_sql = bind.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type = 'index' AND name = ?",
            (index_name,),
        ).scalar_one_or_none()

        key_rows = [row for row in index_xinfo if row["key"] == 1]
        auxiliary_rows = [row for row in index_xinfo if row["key"] == 0]
        valid_index_info = (
            len(index_info) == 1
            and index_info[0]["seqno"] == 0
            and index_info[0]["cid"] >= 0
            and index_info[0]["name"] == expected_column
        )
        valid_key_xinfo = (
            len(key_rows) == 1
            and key_rows[0]["seqno"] == 0
            and key_rows[0]["cid"] >= 0
            and key_rows[0]["name"] == expected_column
            and key_rows[0]["desc"] == 0
            and key_rows[0]["coll"] == "BINARY"
        )
        valid_auxiliary_xinfo = (
            len(auxiliary_rows) == 1
            and auxiliary_rows[0]["seqno"] == 1
            and auxiliary_rows[0]["cid"] == -1
            and auxiliary_rows[0]["name"] is None
            and auxiliary_rows[0]["desc"] == 0
            and auxiliary_rows[0]["coll"] == "BINARY"
        )
        if (
            index_row["unique"] != 0
            or index_row["partial"] != 0
            or not valid_index_info
            or not valid_key_xinfo
            or not valid_auxiliary_xinfo
            or index_sql is None
            or not index_sql.lstrip().upper().startswith("CREATE INDEX ")
        ):
            raise RuntimeError(
                "Unsupported position_snapshots secondary-index definition; "
                f"refusing a lossy batch rebuild: {index_name}."
            )


def _inbound_foreign_keys(bind) -> list[dict[str, object]]:
    table_names = bind.exec_driver_sql(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).scalars().all()
    inbound: list[dict[str, object]] = []
    for table_name in table_names:
        pragma_name = _pragma_identifier(table_name)
        for row in bind.exec_driver_sql(
            f"PRAGMA foreign_key_list({pragma_name})"
        ).mappings():
            if str(row["table"]).casefold() == "position_snapshots":
                inbound.append({"source_table": table_name, **dict(row)})
    return inbound


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        raise RuntimeError(
            "b7e2d1a4c9f3 supports only the governed SQLite deployment."
        )

    table_sql = bind.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = "
        "'position_snapshots'"
    ).scalar_one_or_none()
    if table_sql is None:
        raise RuntimeError(
            "Unsupported schema: position_snapshots does not exist."
        )

    column_rows = bind.exec_driver_sql(
        "PRAGMA table_xinfo('position_snapshots')"
    ).mappings()
    observed_column_shape = {
        row["name"]: (
            row["type"],
            row["notnull"],
            row["dflt_value"],
            row["pk"],
            row["hidden"],
        )
        for row in column_rows
    }
    if observed_column_shape != _EXPECTED_COLUMN_SHAPE:
        raise RuntimeError(
            "Unsupported position_snapshots column shape; refusing a lossy batch "
            f"rebuild. Expected {_EXPECTED_COLUMN_SHAPE}, observed "
            f"{observed_column_shape}."
        )

    index_rows = bind.exec_driver_sql(
        "PRAGMA index_list('position_snapshots')"
    ).mappings().all()
    _validate_secondary_indexes(bind, [dict(row) for row in index_rows])
    unique_indexes = [
        row
        for row in index_rows
        if row["origin"] == "u" and row["unique"] == 1 and row["partial"] == 0
    ]
    unique_columns = []
    if len(unique_indexes) == 1:
        unique_columns = [
            row["name"]
            for row in bind.exec_driver_sql(
                f"PRAGMA index_info('{unique_indexes[0]['name']}')"
            ).mappings()
        ]
    if (
        len(unique_indexes) != 1
        or unique_columns != ["account_id", "asset_id", "reference_date"]
        or any(row["partial"] != 0 for row in index_rows)
    ):
        raise RuntimeError(
            "Unsupported position_snapshots index/unique shape; refusing a lossy "
            "batch rebuild."
        )

    unsupported_sql_features = {
        feature
        for feature in ("CHECK", "COLLATE", "DEFERRABLE", "WITHOUT ROWID", "STRICT")
        if feature in table_sql.upper()
    }
    if unsupported_sql_features:
        raise RuntimeError(
            "Unsupported position_snapshots table features; refusing a lossy batch "
            f"rebuild: {sorted(unsupported_sql_features)}."
        )

    foreign_keys = _foreign_keys(bind)
    invalid_account_foreign_keys = [
        foreign_key
        for foreign_key in foreign_keys
        if foreign_key["table"] == "accounts"
        and foreign_key["from"] == "account_id"
        and foreign_key["to"] == "id"
        and foreign_key["on_update"] == "NO ACTION"
        and foreign_key["on_delete"] == "NO ACTION"
        and foreign_key["match"] == "NONE"
    ]

    valid_asset_foreign_keys = [
        foreign_key
        for foreign_key in foreign_keys
        if foreign_key["table"] == "assets"
        and foreign_key["from"] == "asset_id"
        and foreign_key["to"] == "id"
        and foreign_key["on_update"] == "NO ACTION"
        and foreign_key["on_delete"] == "NO ACTION"
        and foreign_key["match"] == "NONE"
    ]
    if len(valid_asset_foreign_keys) != 1:
        raise RuntimeError(
            "Unsupported position_snapshots foreign-key shape; expected exactly "
            "one asset_id -> assets.id FK."
        )

    # Clean/canonical installs never carried this physical FK. Avoid a needless table
    # rewrite, while still advancing Alembic bookkeeping for the conditional revision.
    if not invalid_account_foreign_keys:
        if len(foreign_keys) != 1:
            raise RuntimeError(
                "Unsupported position_snapshots foreign-key shape; canonical schema "
                "must contain only asset_id -> assets.id."
            )
        return

    if len(invalid_account_foreign_keys) != 1 or len(foreign_keys) != 2:
        raise RuntimeError(
            "Unsupported position_snapshots foreign-key shape; expected only the "
            "invalid accounts FK and the valid asset_id -> assets.id FK."
        )

    inbound_foreign_keys = _inbound_foreign_keys(bind)
    if inbound_foreign_keys:
        raise RuntimeError(
            "Unsupported inbound foreign keys referencing position_snapshots; "
            "refusing batch rebuild before DDL: "
            f"{inbound_foreign_keys}."
        )

    dependents = bind.exec_driver_sql(
        """
        SELECT type, name
        FROM sqlite_master
        WHERE (type = 'trigger' AND tbl_name = 'position_snapshots')
           OR (type = 'view' AND sql LIKE '%position_snapshots%')
        ORDER BY type, name
        """
    ).all()
    if dependents:
        raise RuntimeError(
            "Unsupported position_snapshots dependents; refusing to drop triggers or "
            f"views during batch rebuild: {dependents}."
        )

    orphan_asset_count = bind.exec_driver_sql(
        """
        SELECT COUNT(*)
        FROM position_snapshots AS snapshot
        LEFT JOIN assets AS asset ON asset.id = snapshot.asset_id
        WHERE asset.id IS NULL
        """
    ).scalar_one()
    if orphan_asset_count:
        raise RuntimeError(
            "position_snapshots contains asset_id values missing from assets; "
            f"refusing batch rebuild ({orphan_asset_count} orphan rows)."
        )

    # Under SQLite, table reflection cannot resolve the invalid foreign key targeting
    # 'accounts.id' because 'accounts' uses composite PK (provider, external_id) and
    # has no 'id' column. SQLite also omits constraint names in foreign_key_list reflection.
    # Providing the target schema via copy_from with recreate="always" allows Alembic
    # batch mode to cleanly recreate position_snapshots without reflection failure,
    # preserving all existing data, valid FK to assets(id), unique constraint, and indexes.
    metadata = sa.MetaData()
    corrected_table = sa.Table(
        "position_snapshots",
        metadata,
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("reference_date", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("avg_price", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("is_manual", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("current_value", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"], ["assets.id"], name="fk_position_snapshots_asset_id"
        ),
        sa.UniqueConstraint(
            "account_id",
            "asset_id",
            "reference_date",
            name="uq_position_snapshot_account_asset_date",
        ),
        sa.Index("ix_position_snapshots_account_id", "account_id"),
        sa.Index("ix_position_snapshots_asset_id", "asset_id"),
        sa.Index("ix_position_snapshots_reference_date", "reference_date"),
        sa.Index("ix_position_snapshots_run_id", "run_id"),
    )

    with op.batch_alter_table(
        "position_snapshots", copy_from=corrected_table, recreate="always"
    ) as batch_op:
        pass

    violations = bind.exec_driver_sql(
        "PRAGMA foreign_key_check('position_snapshots')"
    ).all()
    if violations:
        raise RuntimeError(
            "Foreign-key violations remain after position_snapshots remediation: "
            f"{violations}."
        )


def downgrade() -> None:
    # Never stamp the database back to 4f9c2d7e1a6b while silently retaining the
    # remediated physical schema. Reintroducing the invalid FK is unsafe, so reversal
    # requires a separately designed and explicitly authorized recovery migration.
    raise RuntimeError(
        "b7e2d1a4c9f3 is intentionally irreversible: restoring account_id -> "
        "accounts.id would recreate an invalid SQLite foreign key."
    )
