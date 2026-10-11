"""add_external_context_store

Revision ID: 4f9c2d7e1a6b
Revises: 2d6b4f8a9c1e
Create Date: 2026-10-10 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f9c2d7e1a6b"
down_revision: Union[str, Sequence[str], None] = "2d6b4f8a9c1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "external_observation_versions",
        sa.Column("observation_event_id", sa.String(length=36), nullable=False),
        sa.Column("registry_key", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("series_id", sa.String(length=32), nullable=False),
        sa.Column("series_concept", sa.String(length=255), nullable=False),
        sa.Column("semantic_class", sa.String(length=64), nullable=False),
        sa.Column("reference_period_start", sa.String(length=10), nullable=False),
        sa.Column("reference_period_end", sa.String(length=10), nullable=False),
        sa.Column("value_text", sa.String(length=64), nullable=False),
        sa.Column("value_scale", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=True),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("registry_contract_version", sa.Integer(), nullable=False),
        sa.Column("content_fingerprint_version", sa.Integer(), nullable=False),
        sa.Column("content_fingerprint", sa.String(length=71), nullable=False),
        sa.Column("provider_value_text", sa.String(length=128), nullable=False),
        sa.Column("provider_decimal_places", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=False),
        sa.Column("license_id", sa.String(length=64), nullable=False),
        sa.Column("attribution", sa.String(length=255), nullable=False),
        sa.Column("retrieved_at", sa.String(length=27), nullable=False),
        sa.Column("observed_at", sa.String(length=27), nullable=True),
        sa.Column("published_at", sa.String(length=27), nullable=True),
        sa.Column("provider_revision_id", sa.String(length=255), nullable=True),
        sa.Column("revised_at", sa.String(length=27), nullable=True),
        sa.Column("ingested_at", sa.String(length=27), nullable=False),
        sa.Column("known_from", sa.String(length=27), nullable=False),
        sa.Column("knowledge_sequence", sa.Integer(), nullable=False),
        sa.Column("supersedes_event_id", sa.String(length=36), nullable=True),
        sa.CheckConstraint("registry_contract_version > 0", name="ck_external_observation_registry_version"),
        sa.CheckConstraint("content_fingerprint_version > 0", name="ck_external_observation_fingerprint_version"),
        sa.CheckConstraint("knowledge_sequence > 0", name="ck_external_observation_knowledge_sequence"),
        sa.CheckConstraint("value_scale >= 0 AND value_scale <= 18", name="ck_external_observation_value_scale"),
        sa.CheckConstraint("typeof(value_text) = 'text'", name="ck_external_observation_value_text_storage"),
        sa.CheckConstraint("LENGTH(reference_period_start) = 10", name="ck_external_observation_period_start_length"),
        sa.CheckConstraint("LENGTH(reference_period_end) = 10", name="ck_external_observation_period_end_length"),
        sa.CheckConstraint("LENGTH(retrieved_at) = 27", name="ck_external_observation_retrieved_at_length"),
        sa.CheckConstraint("LENGTH(ingested_at) = 27", name="ck_external_observation_ingested_at_length"),
        sa.CheckConstraint("LENGTH(known_from) = 27", name="ck_external_observation_known_from_length"),
        sa.CheckConstraint("ingested_at = known_from", name="ck_external_observation_logical_time_equal"),
        sa.CheckConstraint("LENGTH(content_fingerprint) = 71", name="ck_external_observation_fingerprint_length"),
        sa.CheckConstraint(
            "supersedes_event_id IS NULL OR supersedes_event_id <> observation_event_id",
            name="ck_external_observation_no_self_supersession",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_event_id"],
            ["external_observation_versions.observation_event_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("observation_event_id"),
        sa.UniqueConstraint(
            "provider", "series_id", "reference_period_start",
            "reference_period_end", "semantic_class", "knowledge_sequence",
            name="uq_external_observation_identity_sequence",
        ),
    )
    op.create_index(
        "ix_external_observation_identity_head",
        "external_observation_versions",
        ["provider", "series_id", "reference_period_start", "reference_period_end", "semantic_class", "knowledge_sequence"],
        unique=False,
    )
    op.create_index(
        "ix_external_observation_series_as_of",
        "external_observation_versions",
        ["provider", "series_id", "reference_period_end", "known_from", "knowledge_sequence"],
        unique=False,
    )

    op.create_table(
        "external_series_sync_state",
        sa.Column("registry_key", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("series_id", sa.String(length=32), nullable=False),
        sa.Column("registry_contract_version", sa.Integer(), nullable=False),
        sa.Column("last_attempt_at", sa.String(length=27), nullable=True),
        sa.Column("last_success_at", sa.String(length=27), nullable=True),
        sa.Column("next_refresh_eligible_at", sa.String(length=27), nullable=True),
        sa.Column("coverage_start", sa.String(length=10), nullable=True),
        sa.Column("coverage_end", sa.String(length=10), nullable=True),
        sa.Column("last_attempt_result", sa.String(length=16), nullable=True),
        sa.Column("partial_coverage", sa.Boolean(), nullable=False),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_http_status", sa.Integer(), nullable=True),
        sa.Column("last_valid_observation_event_id", sa.String(length=36), nullable=True),
        sa.Column("consecutive_retransmissions", sa.Integer(), nullable=False),
        sa.Column("accepted_transitions", sa.Integer(), nullable=False),
        sa.Column("observations_received", sa.Integer(), nullable=False),
        sa.CheckConstraint("registry_contract_version > 0", name="ck_external_sync_registry_version"),
        sa.CheckConstraint(
            "(coverage_start IS NULL AND coverage_end IS NULL) OR "
            "(coverage_start IS NOT NULL AND coverage_end IS NOT NULL AND coverage_end >= coverage_start)",
            name="ck_external_sync_coverage",
        ),
        sa.CheckConstraint(
            "last_attempt_result IS NULL OR last_attempt_result IN ('SUCCESS', 'EMPTY', 'PARTIAL', 'FAILED')",
            name="ck_external_sync_attempt_result",
        ),
        sa.CheckConstraint("partial_coverage IN (0, 1)", name="ck_external_sync_partial_coverage"),
        sa.CheckConstraint(
            "last_http_status IS NULL OR (last_http_status >= 100 AND last_http_status <= 599)",
            name="ck_external_sync_http_status",
        ),
        sa.CheckConstraint("consecutive_retransmissions >= 0", name="ck_external_sync_retransmissions"),
        sa.CheckConstraint("accepted_transitions >= 0", name="ck_external_sync_transitions"),
        sa.CheckConstraint("observations_received >= 0", name="ck_external_sync_observations_received"),
        sa.ForeignKeyConstraint(
            ["last_valid_observation_event_id"],
            ["external_observation_versions.observation_event_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("registry_key"),
        sa.UniqueConstraint("provider", "series_id", name="uq_external_sync_provider_series"),
    )
    op.create_index(
        "ix_external_sync_refresh",
        "external_series_sync_state",
        ["next_refresh_eligible_at"],
        unique=False,
    )

    op.execute(
        "CREATE TRIGGER trg_external_observation_versions_no_update "
        "BEFORE UPDATE ON external_observation_versions "
        "BEGIN SELECT RAISE(ABORT, 'external observation versions are append-only'); END"
    )
    op.execute(
        "CREATE TRIGGER trg_external_observation_versions_no_delete "
        "BEFORE DELETE ON external_observation_versions "
        "BEGIN SELECT RAISE(ABORT, 'external observation versions are append-only'); END"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_external_observation_versions_no_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_external_observation_versions_no_update")
    op.drop_index("ix_external_sync_refresh", table_name="external_series_sync_state")
    op.drop_table("external_series_sync_state")
    op.drop_index("ix_external_observation_series_as_of", table_name="external_observation_versions")
    op.drop_index("ix_external_observation_identity_head", table_name="external_observation_versions")
    op.drop_table("external_observation_versions")
