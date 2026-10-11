"""SQLAlchemy metadata for the two governed R3-D SQLite structures."""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class ExternalObservationVersionModel(Base):
    __tablename__ = "external_observation_versions"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "series_id",
            "reference_period_start",
            "reference_period_end",
            "semantic_class",
            "knowledge_sequence",
            name="uq_external_observation_identity_sequence",
        ),
        CheckConstraint("registry_contract_version > 0", name="ck_external_observation_registry_version"),
        CheckConstraint("content_fingerprint_version > 0", name="ck_external_observation_fingerprint_version"),
        CheckConstraint("knowledge_sequence > 0", name="ck_external_observation_knowledge_sequence"),
        CheckConstraint("value_scale >= 0 AND value_scale <= 18", name="ck_external_observation_value_scale"),
        CheckConstraint("typeof(value_text) = 'text'", name="ck_external_observation_value_text_storage"),
        CheckConstraint("LENGTH(reference_period_start) = 10", name="ck_external_observation_period_start_length"),
        CheckConstraint("LENGTH(reference_period_end) = 10", name="ck_external_observation_period_end_length"),
        CheckConstraint("LENGTH(retrieved_at) = 27", name="ck_external_observation_retrieved_at_length"),
        CheckConstraint("LENGTH(ingested_at) = 27", name="ck_external_observation_ingested_at_length"),
        CheckConstraint("LENGTH(known_from) = 27", name="ck_external_observation_known_from_length"),
        CheckConstraint("ingested_at = known_from", name="ck_external_observation_logical_time_equal"),
        CheckConstraint("LENGTH(content_fingerprint) = 71", name="ck_external_observation_fingerprint_length"),
        CheckConstraint(
            "supersedes_event_id IS NULL OR supersedes_event_id <> observation_event_id",
            name="ck_external_observation_no_self_supersession",
        ),
        Index(
            "ix_external_observation_identity_head",
            "provider",
            "series_id",
            "reference_period_start",
            "reference_period_end",
            "semantic_class",
            "knowledge_sequence",
        ),
        Index(
            "ix_external_observation_series_as_of",
            "provider",
            "series_id",
            "reference_period_end",
            "known_from",
            "knowledge_sequence",
        ),
    )

    observation_event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    registry_key: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    series_id: Mapped[str] = mapped_column(String(32), nullable=False)
    series_concept: Mapped[str] = mapped_column(String(255), nullable=False)
    semantic_class: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_period_start: Mapped[str] = mapped_column(String(10), nullable=False)
    reference_period_end: Mapped[str] = mapped_column(String(10), nullable=False)
    value_text: Mapped[str] = mapped_column(String(64), nullable=False)
    value_scale: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    registry_contract_version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_fingerprint_version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_fingerprint: Mapped[str] = mapped_column(String(71), nullable=False)
    provider_value_text: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_decimal_places: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)
    license_id: Mapped[str] = mapped_column(String(64), nullable=False)
    attribution: Mapped[str] = mapped_column(String(255), nullable=False)
    retrieved_at: Mapped[str] = mapped_column(String(27), nullable=False)
    observed_at: Mapped[str | None] = mapped_column(String(27), nullable=True)
    published_at: Mapped[str | None] = mapped_column(String(27), nullable=True)
    provider_revision_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    revised_at: Mapped[str | None] = mapped_column(String(27), nullable=True)
    ingested_at: Mapped[str] = mapped_column(String(27), nullable=False)
    known_from: Mapped[str] = mapped_column(String(27), nullable=False)
    knowledge_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    supersedes_event_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("external_observation_versions.observation_event_id", ondelete="RESTRICT"),
        nullable=True,
    )


class ExternalSeriesSyncStateModel(Base):
    __tablename__ = "external_series_sync_state"
    __table_args__ = (
        UniqueConstraint("provider", "series_id", name="uq_external_sync_provider_series"),
        CheckConstraint("registry_contract_version > 0", name="ck_external_sync_registry_version"),
        CheckConstraint(
            "(coverage_start IS NULL AND coverage_end IS NULL) OR "
            "(coverage_start IS NOT NULL AND coverage_end IS NOT NULL AND coverage_end >= coverage_start)",
            name="ck_external_sync_coverage",
        ),
        CheckConstraint(
            "last_attempt_result IS NULL OR last_attempt_result IN ('SUCCESS', 'EMPTY', 'PARTIAL', 'FAILED')",
            name="ck_external_sync_attempt_result",
        ),
        CheckConstraint("partial_coverage IN (0, 1)", name="ck_external_sync_partial_coverage"),
        CheckConstraint(
            "last_http_status IS NULL OR (last_http_status >= 100 AND last_http_status <= 599)",
            name="ck_external_sync_http_status",
        ),
        CheckConstraint("consecutive_retransmissions >= 0", name="ck_external_sync_retransmissions"),
        CheckConstraint("accepted_transitions >= 0", name="ck_external_sync_transitions"),
        CheckConstraint("observations_received >= 0", name="ck_external_sync_observations_received"),
        Index("ix_external_sync_refresh", "next_refresh_eligible_at"),
    )

    registry_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    series_id: Mapped[str] = mapped_column(String(32), nullable=False)
    registry_contract_version: Mapped[int] = mapped_column(Integer, nullable=False)
    last_attempt_at: Mapped[str | None] = mapped_column(String(27), nullable=True)
    last_success_at: Mapped[str | None] = mapped_column(String(27), nullable=True)
    next_refresh_eligible_at: Mapped[str | None] = mapped_column(String(27), nullable=True)
    coverage_start: Mapped[str | None] = mapped_column(String(10), nullable=True)
    coverage_end: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_attempt_result: Mapped[str | None] = mapped_column(String(16), nullable=True)
    partial_coverage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_valid_observation_event_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("external_observation_versions.observation_event_id", ondelete="RESTRICT"),
        nullable=True,
    )
    consecutive_retransmissions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepted_transitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    observations_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
