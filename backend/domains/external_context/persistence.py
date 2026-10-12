"""Immutable R3-D persistence and operational-state value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from backend.domain.exceptions.base import FINAnalyticsError

from .enums import AcquisitionHealth, Availability, EconomicFreshness, Frequency
from .models import ExternalObservation
from .utc_codec import encode_utc_timestamp


class ExternalContextPersistenceErrorCode(str, Enum):
    INVALID_STORAGE_VALUE = "INVALID_STORAGE_VALUE"
    UNSUPPORTED_REGISTRY_VERSION = "UNSUPPORTED_REGISTRY_VERSION"
    FINGERPRINT_MISMATCH = "FINGERPRINT_MISMATCH"
    CLOCK_REGRESSION = "CLOCK_REGRESSION"
    TRANSACTION_CONFLICT = "TRANSACTION_CONFLICT"
    COMMIT_OUTCOME_UNKNOWN = "COMMIT_OUTCOME_UNKNOWN"
    INTEGRITY_VIOLATION = "INTEGRITY_VIOLATION"
    ACQUISITION_EVIDENCE_INVALID = "ACQUISITION_EVIDENCE_INVALID"
    STALE_ACQUISITION_FINALIZATION = "STALE_ACQUISITION_FINALIZATION"


class ExternalContextPersistenceError(FINAnalyticsError):
    def __init__(
        self,
        code: ExternalContextPersistenceErrorCode,
        message: str,
        *,
        field: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.details = MappingProxyType(dict(details or {}))


class ObservationWriteDisposition(str, Enum):
    INSERTED = "INSERTED"
    RETRANSMISSION = "RETRANSMISSION"


class SyncAttemptResult(str, Enum):
    SUCCESS = "SUCCESS"
    EMPTY = "EMPTY"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class FreshnessEvidence(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    INSUFFICIENT = "INSUFFICIENT"


class ExternalContextReasonCode(str, Enum):
    REGISTRY_VERSION_MISMATCH = "REGISTRY_VERSION_MISMATCH"
    NEVER_ACQUIRED = "NEVER_ACQUIRED"
    NO_ELIGIBLE_OBSERVATION = "NO_ELIGIBLE_OBSERVATION"
    PARTIAL_COVERAGE = "PARTIAL_COVERAGE"
    ACQUISITION_FAILED = "ACQUISITION_FAILED"
    ACQUISITION_PARTIAL = "ACQUISITION_PARTIAL"
    INSUFFICIENT_FRESHNESS_EVIDENCE = "INSUFFICIENT_FRESHNESS_EVIDENCE"


@dataclass(frozen=True)
class PersistedObservationEvent:
    observation_event_id: str
    observation: ExternalObservation
    registry_contract_version: int
    content_fingerprint_version: int
    content_fingerprint: str
    ingested_at: datetime
    known_from: datetime
    knowledge_sequence: int
    supersedes_event_id: str | None

    def __post_init__(self) -> None:
        if type(self.observation_event_id) is not str or not self.observation_event_id:
            raise ValueError("observation_event_id is required.")
        if not isinstance(self.observation, ExternalObservation):
            raise TypeError("observation must be ExternalObservation.")
        for field_name, value in (
            ("registry_contract_version", self.registry_contract_version),
            ("content_fingerprint_version", self.content_fingerprint_version),
            ("knowledge_sequence", self.knowledge_sequence),
        ):
            if type(value) is not int or value < 1:
                raise ValueError(f"{field_name} must be a positive strict integer.")
        encode_utc_timestamp(self.ingested_at, field="ingested_at")
        encode_utc_timestamp(self.known_from, field="known_from")
        if self.ingested_at != self.known_from:
            raise ValueError("ingested_at and known_from must be identical in V1.")
        if self.knowledge_sequence == 1 and self.supersedes_event_id is not None:
            raise ValueError("The first knowledge event cannot supersede another event.")
        if self.knowledge_sequence > 1 and not self.supersedes_event_id:
            raise ValueError("A later knowledge event must supersede its immediate head.")


@dataclass(frozen=True)
class ObservationWriteResult:
    disposition: ObservationWriteDisposition
    event: PersistedObservationEvent


@dataclass(frozen=True)
class ExternalSeriesSyncState:
    registry_key: str
    provider: str
    series_id: str
    registry_contract_version: int
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    next_refresh_eligible_at: datetime | None = None
    coverage_start: date | None = None
    coverage_end: date | None = None
    last_attempt_result: SyncAttemptResult | None = None
    partial_coverage: bool = False
    last_error_code: str | None = None
    last_http_status: int | None = None
    last_valid_observation_event_id: str | None = None
    consecutive_retransmissions: int = 0
    accepted_transitions: int = 0
    observations_received: int = 0

    def __post_init__(self) -> None:
        if type(self.registry_contract_version) is not int or self.registry_contract_version < 1:
            raise ValueError("registry_contract_version must be a positive strict integer.")
        for field_name in (
            "last_attempt_at",
            "last_success_at",
            "next_refresh_eligible_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                encode_utc_timestamp(value, field=field_name)
        if (self.coverage_start is None) != (self.coverage_end is None):
            raise ValueError("Coverage boundaries must both be null or both be present.")
        if self.coverage_start is not None and self.coverage_end < self.coverage_start:
            raise ValueError("coverage_end cannot precede coverage_start.")
        for field_name in (
            "consecutive_retransmissions",
            "accepted_transitions",
            "observations_received",
        ):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field_name} must be a non-negative strict integer.")
        if self.last_http_status is not None and (
            type(self.last_http_status) is not int
            or not 100 <= self.last_http_status <= 599
        ):
            raise ValueError("last_http_status must be an HTTP status or None.")


@dataclass(frozen=True)
class ExternalSeriesState:
    availability: Availability
    economic_freshness: EconomicFreshness
    acquisition_health: AcquisitionHealth
    reason_code: ExternalContextReasonCode | None


def operational_refresh_interval(frequency: Frequency) -> timedelta:
    if frequency is Frequency.DAILY:
        return timedelta(hours=6)
    if frequency is Frequency.MONTHLY:
        return timedelta(hours=24)
    raise TypeError("frequency must be an executable Frequency.")


def is_refresh_due(*, state: ExternalSeriesSyncState, at: datetime) -> bool:
    encode_utc_timestamp(at, field="at")
    return state.next_refresh_eligible_at is None or at >= state.next_refresh_eligible_at


def evaluate_external_series_state(
    *,
    state: ExternalSeriesSyncState | None,
    has_eligible_observation: bool,
    requested_start: date,
    requested_end: date,
    freshness_evidence: FreshnessEvidence = FreshnessEvidence.INSUFFICIENT,
    current_registry_version: int,
) -> ExternalSeriesState:
    if type(current_registry_version) is not int or current_registry_version < 1:
        raise ValueError("current_registry_version must be a positive strict integer.")
    if type(requested_start) is not date or type(requested_end) is not date:
        raise TypeError("Requested coverage requires civil dates.")
    if requested_end < requested_start:
        raise ValueError("requested_end cannot precede requested_start.")

    if not has_eligible_observation:
        availability = Availability.UNAVAILABLE
        availability_reason = ExternalContextReasonCode.NO_ELIGIBLE_OBSERVATION
    elif (
        state is not None
        and state.coverage_start is not None
        and state.coverage_start <= requested_start
        and state.coverage_end >= requested_end
    ):
        availability = Availability.AVAILABLE
        availability_reason = None
    else:
        availability = Availability.PARTIAL
        availability_reason = ExternalContextReasonCode.PARTIAL_COVERAGE

    if state is None or state.last_attempt_result is None:
        return ExternalSeriesState(
            availability=availability,
            economic_freshness=EconomicFreshness.UNKNOWN,
            acquisition_health=AcquisitionHealth.UNKNOWN,
            reason_code=(
                ExternalContextReasonCode.NEVER_ACQUIRED
                if state is not None
                else availability_reason
            ),
        )
    if state.registry_contract_version != current_registry_version:
        return ExternalSeriesState(
            availability=availability,
            economic_freshness=EconomicFreshness.UNKNOWN,
            acquisition_health=AcquisitionHealth.UNKNOWN,
            reason_code=ExternalContextReasonCode.REGISTRY_VERSION_MISMATCH,
        )

    health = {
        SyncAttemptResult.SUCCESS: AcquisitionHealth.HEALTHY,
        SyncAttemptResult.EMPTY: AcquisitionHealth.HEALTHY,
        SyncAttemptResult.PARTIAL: AcquisitionHealth.DEGRADED,
        SyncAttemptResult.FAILED: AcquisitionHealth.FAILED,
    }[state.last_attempt_result]
    freshness = {
        FreshnessEvidence.CURRENT: EconomicFreshness.CURRENT,
        FreshnessEvidence.STALE: EconomicFreshness.STALE,
        FreshnessEvidence.INSUFFICIENT: EconomicFreshness.UNKNOWN,
    }[freshness_evidence]
    reason = availability_reason
    if state.last_attempt_result is SyncAttemptResult.PARTIAL:
        reason = ExternalContextReasonCode.ACQUISITION_PARTIAL
    elif state.last_attempt_result is SyncAttemptResult.FAILED:
        reason = ExternalContextReasonCode.ACQUISITION_FAILED
    elif freshness is EconomicFreshness.UNKNOWN and reason is None:
        reason = ExternalContextReasonCode.INSUFFICIENT_FRESHNESS_EVIDENCE
    return ExternalSeriesState(
        availability=availability,
        economic_freshness=freshness,
        acquisition_health=health,
        reason_code=reason,
    )
