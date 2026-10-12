"""Application-owned R3-D transaction, history, and sync-state orchestration."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from backend.domains.external_context import (
    EXTERNAL_SERIES_REGISTRY_VERSION,
    EconomicIdentity,
    ExternalContextPersistenceError,
    ExternalContextPersistenceErrorCode,
    ExternalObservation,
    ExternalObservationProvenance,
    ExternalSeriesSyncState,
    ObservationWriteDisposition,
    ObservationWriteResult,
    PersistedObservationEvent,
    Provider,
    RegistryKey,
    SyncAttemptResult,
    build_content_fingerprint_v1,
    encode_utc_timestamp,
    normalize_external_observation,
    operational_refresh_interval,
    resolve_series_by_key,
)
from backend.infrastructure.persistence.repositories.external_context import (
    ExternalObservationRepository,
    ExternalSeriesSyncStateRepository,
)


class SQLiteImmediateUnitOfWork:
    """One explicit SQLite writer reservation over the caller-provided Session."""

    def __init__(self, db: Session, *, busy_timeout_ms: int) -> None:
        if type(busy_timeout_ms) is not int or busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms must be a non-negative strict integer.")
        self.db = db
        self.busy_timeout_ms = busy_timeout_ms

    def begin_immediate(self) -> None:
        if self.db.in_transaction():
            raise ExternalContextPersistenceError(
                ExternalContextPersistenceErrorCode.TRANSACTION_CONFLICT,
                "R3-D requires an idle Session before BEGIN IMMEDIATE.",
            )
        connection = self.db.connection()
        connection.exec_driver_sql(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
        connection.exec_driver_sql("BEGIN IMMEDIATE")

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()


class ObservationIngestionMode(str, Enum):
    """Compatibility mode for one certified observation write."""

    IMMEDIATE = "immediate"
    DEFERRED = "deferred"


@dataclass(frozen=True)
class AcquisitionInterval:
    start: date
    end: date

    def __post_init__(self) -> None:
        if type(self.start) is not date or type(self.end) is not date:
            raise TypeError("Acquisition interval boundaries must be civil dates.")
        if self.end < self.start:
            raise ValueError("Acquisition interval end cannot precede its start.")


@dataclass(frozen=True)
class AcquisitionChunkEvidence:
    """Ephemeral evidence for one planned acquisition chunk.

    ``persistence_completed`` means every accepted observation in the chunk was
    either committed as a transition or handled as a certified retransmission.
    It is also true for a fully received, validated empty chunk.
    """

    interval: AcquisitionInterval
    response_received: bool
    payload_validated: bool
    persistence_completed: bool
    observations_received: int
    empty_response: bool = False
    error_code: str | None = None
    http_status: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.interval, AcquisitionInterval):
            raise TypeError("interval must be an AcquisitionInterval.")
        for field_name in (
            "response_received",
            "payload_validated",
            "persistence_completed",
            "empty_response",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a strict boolean.")
        if type(self.observations_received) is not int or self.observations_received < 0:
            raise ValueError("observations_received must be a non-negative strict integer.")
        if self.payload_validated and not self.response_received:
            raise ValueError("A payload cannot be validated before its response is received.")
        if self.persistence_completed and not self.payload_validated:
            raise ValueError("Persistence cannot complete before full payload validation.")
        if self.empty_response and not self.is_complete:
            raise ValueError("An empty response is evidence only after complete processing.")
        if self.empty_response and self.observations_received != 0:
            raise ValueError("An empty chunk cannot report economic observations.")
        if self.is_complete and self.observations_received == 0 and not self.empty_response:
            raise ValueError("A completed zero-observation chunk must be marked empty.")
        _validate_safe_error(self.error_code)
        _validate_http_status(self.http_status)

    @property
    def is_complete(self) -> bool:
        return (
            self.response_received
            and self.payload_validated
            and self.persistence_completed
        )


@dataclass(frozen=True)
class AcquisitionFinalizationRequest:
    """Typed, non-persistent proof supplied to global acquisition finalization."""

    acquisition_id: str
    registry_key: RegistryKey
    requested_interval: AcquisitionInterval
    operational_at: datetime
    planned_chunks: tuple[AcquisitionChunkEvidence, ...]
    declared_result: SyncAttemptResult
    error_code: str | None = None
    http_status: int | None = None

    def __post_init__(self) -> None:
        if type(self.acquisition_id) is not str or not 1 <= len(self.acquisition_id) <= 128:
            raise ValueError("acquisition_id must contain between 1 and 128 characters.")
        if any(
            not (
                character.isascii()
                and (character.isalnum() or character in "-_.:")
            )
            for character in self.acquisition_id
        ):
            raise ValueError("acquisition_id contains unsafe characters.")
        if not isinstance(self.registry_key, RegistryKey):
            raise TypeError("registry_key must be a RegistryKey.")
        resolve_series_by_key(self.registry_key)
        if not isinstance(self.requested_interval, AcquisitionInterval):
            raise TypeError("requested_interval must be an AcquisitionInterval.")
        encode_utc_timestamp(self.operational_at, field="operational_at")
        if type(self.planned_chunks) is not tuple or not self.planned_chunks:
            raise ValueError("planned_chunks must be a non-empty tuple.")
        if any(not isinstance(chunk, AcquisitionChunkEvidence) for chunk in self.planned_chunks):
            raise TypeError("planned_chunks must contain AcquisitionChunkEvidence values.")
        if not isinstance(self.declared_result, SyncAttemptResult):
            raise TypeError("declared_result must be a SyncAttemptResult.")
        _validate_safe_error(self.error_code)
        _validate_http_status(self.http_status)
        self._validate_plan_partition()
        if self.declared_result is not self.derived_result:
            raise ExternalContextPersistenceError(
                ExternalContextPersistenceErrorCode.ACQUISITION_EVIDENCE_INVALID,
                "The declared global result is inconsistent with chunk evidence.",
                field="declared_result",
                details={
                    "declared": self.declared_result.value,
                    "derived": self.derived_result.value,
                },
            )
        if self.derived_result in {SyncAttemptResult.SUCCESS, SyncAttemptResult.EMPTY}:
            if self.error_code is not None:
                raise ValueError("A complete acquisition cannot carry a global error code.")

    @property
    def derived_result(self) -> SyncAttemptResult:
        complete_chunks = tuple(chunk for chunk in self.planned_chunks if chunk.is_complete)
        if len(complete_chunks) == len(self.planned_chunks):
            if all(chunk.empty_response for chunk in complete_chunks):
                return SyncAttemptResult.EMPTY
            return SyncAttemptResult.SUCCESS
        if complete_chunks:
            return SyncAttemptResult.PARTIAL
        return SyncAttemptResult.FAILED

    @property
    def queried_intervals(self) -> tuple[AcquisitionInterval, ...]:
        return tuple(chunk.interval for chunk in self.planned_chunks if chunk.is_complete)

    @property
    def uncompleted_intervals(self) -> tuple[AcquisitionInterval, ...]:
        return tuple(chunk.interval for chunk in self.planned_chunks if not chunk.is_complete)

    def _validate_plan_partition(self) -> None:
        first = self.planned_chunks[0].interval
        last = self.planned_chunks[-1].interval
        if first.start != self.requested_interval.start or last.end != self.requested_interval.end:
            raise ExternalContextPersistenceError(
                ExternalContextPersistenceErrorCode.ACQUISITION_EVIDENCE_INVALID,
                "Planned chunks must cover the requested interval boundaries exactly.",
                field="planned_chunks",
            )
        previous_end: date | None = None
        for chunk in self.planned_chunks:
            interval = chunk.interval
            if (
                interval.start < self.requested_interval.start
                or interval.end > self.requested_interval.end
            ):
                raise ExternalContextPersistenceError(
                    ExternalContextPersistenceErrorCode.ACQUISITION_EVIDENCE_INVALID,
                    "A planned chunk lies outside the requested interval.",
                    field="planned_chunks",
                )
            if previous_end is not None and interval.start != previous_end + timedelta(days=1):
                raise ExternalContextPersistenceError(
                    ExternalContextPersistenceErrorCode.ACQUISITION_EVIDENCE_INVALID,
                    "Planned chunks must be ordered, gap-free, and non-overlapping.",
                    field="planned_chunks",
                )
            previous_end = interval.end


@dataclass(frozen=True)
class AcquisitionFinalizationResult:
    acquisition_id: str
    global_result: SyncAttemptResult
    requested_interval: AcquisitionInterval
    queried_intervals: tuple[AcquisitionInterval, ...]
    uncompleted_intervals: tuple[AcquisitionInterval, ...]
    sync_state: ExternalSeriesSyncState
    repeated_finalization: bool


def _validate_safe_error(value: str | None) -> None:
    if value is None:
        return
    if type(value) is not str or not 1 <= len(value) <= 64:
        raise ValueError("error_code must contain between 1 and 64 characters.")
    if any(
        not (
            character.isascii()
            and (character.isupper() or character.isdigit() or character == "_")
        )
        for character in value
    ):
        raise ValueError("error_code must use only uppercase ASCII letters, digits, and underscores.")


def _validate_http_status(value: int | None) -> None:
    if value is not None and (type(value) is not int or not 100 <= value <= 599):
        raise ValueError("http_status must be an HTTP status or None.")


class ExternalObservationStoreService:
    def __init__(
        self,
        db: Session,
        *,
        utc_clock: Callable[[], datetime],
        max_attempts: int = 3,
        busy_timeout_ms: int = 250,
        retry_delay_seconds: float = 0.01,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if type(max_attempts) is not int or max_attempts < 1:
            raise ValueError("max_attempts must be a positive strict integer.")
        self._db = db
        self._clock = utc_clock
        self._max_attempts = max_attempts
        self._busy_timeout_ms = busy_timeout_ms
        self._retry_delay_seconds = retry_delay_seconds
        self._sleeper = sleeper

    def ingest(
        self,
        observation: ExternalObservation,
        *,
        expected_content_fingerprint: str | None = None,
        acquisition_mode: ObservationIngestionMode = ObservationIngestionMode.IMMEDIATE,
    ) -> ObservationWriteResult:
        if not isinstance(acquisition_mode, ObservationIngestionMode):
            raise TypeError("acquisition_mode must be an ObservationIngestionMode.")
        certified = self._recertify(observation)
        fingerprint = build_content_fingerprint_v1(certified.content.as_payload_v1())
        if (
            expected_content_fingerprint is not None
            and expected_content_fingerprint != fingerprint.content_fingerprint
        ):
            raise ExternalContextPersistenceError(
                ExternalContextPersistenceErrorCode.FINGERPRINT_MISMATCH,
                "The supplied fingerprint does not match certified R3-C content.",
                field="content_fingerprint",
            )

        last_busy_error: OperationalError | None = None
        for attempt in range(self._max_attempts):
            uow = SQLiteImmediateUnitOfWork(
                self._db,
                busy_timeout_ms=self._busy_timeout_ms,
            )
            try:
                uow.begin_immediate()
                observation_repo = ExternalObservationRepository(self._db)
                sync_repo = ExternalSeriesSyncStateRepository(self._db)
                head = observation_repo.get_head(certified.economic_identity)
                transaction_time = self._clock()
                encode_utc_timestamp(transaction_time, field="transaction_time_utc")
                if transaction_time < certified.provenance.retrieved_at:
                    raise ExternalContextPersistenceError(
                        ExternalContextPersistenceErrorCode.CLOCK_REGRESSION,
                        "transaction_time_utc precedes retrieved_at.",
                        field="transaction_time_utc",
                    )
                if head is not None and transaction_time < head.known_from:
                    raise ExternalContextPersistenceError(
                        ExternalContextPersistenceErrorCode.CLOCK_REGRESSION,
                        "transaction_time_utc precedes the current head known_from.",
                        field="transaction_time_utc",
                    )

                if head is not None and (
                    head.content_fingerprint_version,
                    head.content_fingerprint,
                ) == fingerprint.as_pair():
                    result = ObservationWriteResult(
                        disposition=ObservationWriteDisposition.RETRANSMISSION,
                        event=head,
                    )
                    if acquisition_mode is ObservationIngestionMode.IMMEDIATE:
                        self._record_success(
                            sync_repo,
                            certified,
                            event=head,
                            retransmission=True,
                        )
                    else:
                        self._record_deferred_event(
                            sync_repo,
                            certified,
                            event=head,
                            retransmission=True,
                        )
                else:
                    event = PersistedObservationEvent(
                        observation_event_id=str(uuid4()),
                        observation=certified,
                        registry_contract_version=EXTERNAL_SERIES_REGISTRY_VERSION,
                        content_fingerprint_version=fingerprint.content_fingerprint_version,
                        content_fingerprint=fingerprint.content_fingerprint,
                        ingested_at=transaction_time,
                        known_from=transaction_time,
                        knowledge_sequence=(head.knowledge_sequence + 1 if head else 1),
                        supersedes_event_id=(head.observation_event_id if head else None),
                    )
                    observation_repo.insert(event)
                    if acquisition_mode is ObservationIngestionMode.IMMEDIATE:
                        self._record_success(
                            sync_repo,
                            certified,
                            event=event,
                            retransmission=False,
                        )
                    else:
                        self._record_deferred_event(
                            sync_repo,
                            certified,
                            event=event,
                            retransmission=False,
                        )
                    result = ObservationWriteResult(
                        disposition=ObservationWriteDisposition.INSERTED,
                        event=event,
                    )
                try:
                    uow.commit()
                except Exception as exc:
                    uow.rollback()
                    raise ExternalContextPersistenceError(
                        ExternalContextPersistenceErrorCode.COMMIT_OUTCOME_UNKNOWN,
                        "The SQLite commit outcome could not be established; no automatic retry was performed.",
                    ) from exc
                return result
            except OperationalError as exc:
                uow.rollback()
                if not self._is_busy(exc) or attempt + 1 >= self._max_attempts:
                    if self._is_busy(exc):
                        raise ExternalContextPersistenceError(
                            ExternalContextPersistenceErrorCode.TRANSACTION_CONFLICT,
                            "SQLite writer reservation remained busy after bounded retries.",
                        ) from exc
                    raise
                last_busy_error = exc
                self._sleeper(self._retry_delay_seconds)
            except IntegrityError as exc:
                uow.rollback()
                raise ExternalContextPersistenceError(
                    ExternalContextPersistenceErrorCode.INTEGRITY_VIOLATION,
                    "SQLite rejected the governed External Context transaction.",
                ) from exc
            except Exception:
                uow.rollback()
                raise
        raise AssertionError(last_busy_error)

    def get_sync_state(
        self,
        registry_key: RegistryKey | str,
    ) -> ExternalSeriesSyncState | None:
        """Return persisted operational state without initializing or mutating it."""

        definition = resolve_series_by_key(registry_key)
        return ExternalSeriesSyncStateRepository(self._db).get(definition.registry_key)

    def finalize_acquisition(
        self,
        request: AcquisitionFinalizationRequest,
    ) -> AcquisitionFinalizationResult:
        """Publish one evidence-backed global result under ``BEGIN IMMEDIATE``.

        V1 deliberately replaces scalar durable coverage with the newly proved
        integral requested interval after complete SUCCESS/EMPTY finalization.
        It never unions that interval with legacy or disconnected coverage.
        """

        if not isinstance(request, AcquisitionFinalizationRequest):
            raise TypeError("request must be an AcquisitionFinalizationRequest.")
        last_busy_error: OperationalError | None = None
        for attempt in range(self._max_attempts):
            uow = SQLiteImmediateUnitOfWork(
                self._db,
                busy_timeout_ms=self._busy_timeout_ms,
            )
            try:
                uow.begin_immediate()
                repo = ExternalSeriesSyncStateRepository(self._db)
                current = repo.get(request.registry_key) or repo.initialize(request.registry_key)
                self._reject_stale_finalization(request, current)
                desired = self._build_finalized_state(request, current)
                if request.operational_at == current.last_attempt_at:
                    if desired != current:
                        raise ExternalContextPersistenceError(
                            ExternalContextPersistenceErrorCode.STALE_ACQUISITION_FINALIZATION,
                            "An equal-time finalization conflicts with the persisted conclusion.",
                            field="operational_at",
                        )
                    uow.commit()
                    return self._finalization_result(
                        request,
                        current,
                        repeated=True,
                    )
                repo.save(desired)
                try:
                    uow.commit()
                except Exception as exc:
                    uow.rollback()
                    raise ExternalContextPersistenceError(
                        ExternalContextPersistenceErrorCode.COMMIT_OUTCOME_UNKNOWN,
                        "The SQLite finalization commit outcome could not be established; no automatic retry was performed.",
                    ) from exc
                return self._finalization_result(request, desired, repeated=False)
            except OperationalError as exc:
                uow.rollback()
                if not self._is_busy(exc) or attempt + 1 >= self._max_attempts:
                    if self._is_busy(exc):
                        raise ExternalContextPersistenceError(
                            ExternalContextPersistenceErrorCode.TRANSACTION_CONFLICT,
                            "SQLite writer reservation remained busy after bounded retries.",
                        ) from exc
                    raise
                last_busy_error = exc
                self._sleeper(self._retry_delay_seconds)
            except IntegrityError as exc:
                uow.rollback()
                raise ExternalContextPersistenceError(
                    ExternalContextPersistenceErrorCode.INTEGRITY_VIOLATION,
                    "SQLite rejected the governed acquisition finalization.",
                ) from exc
            except Exception:
                uow.rollback()
                raise
        raise AssertionError(last_busy_error)

    def record_failed_attempt(
        self,
        *,
        registry_key: RegistryKey,
        attempted_at: datetime,
        error_code: str,
        http_status: int | None = None,
        partial: bool = False,
        next_retry_at: datetime | None = None,
        coverage_start: date | None = None,
        coverage_end: date | None = None,
    ) -> ExternalSeriesSyncState:
        encode_utc_timestamp(attempted_at, field="attempted_at")
        if next_retry_at is not None:
            encode_utc_timestamp(next_retry_at, field="next_retry_at")
        uow = SQLiteImmediateUnitOfWork(self._db, busy_timeout_ms=self._busy_timeout_ms)
        try:
            uow.begin_immediate()
            repo = ExternalSeriesSyncStateRepository(self._db)
            current = repo.get(registry_key) or repo.initialize(registry_key)
            updated = ExternalSeriesSyncState(
                registry_key=current.registry_key,
                provider=current.provider,
                series_id=current.series_id,
                registry_contract_version=current.registry_contract_version,
                last_attempt_at=attempted_at,
                last_success_at=current.last_success_at,
                next_refresh_eligible_at=next_retry_at,
                coverage_start=coverage_start if coverage_start is not None else current.coverage_start,
                coverage_end=coverage_end if coverage_end is not None else current.coverage_end,
                last_attempt_result=(SyncAttemptResult.PARTIAL if partial else SyncAttemptResult.FAILED),
                partial_coverage=partial,
                last_error_code=error_code,
                last_http_status=http_status,
                last_valid_observation_event_id=current.last_valid_observation_event_id,
                consecutive_retransmissions=current.consecutive_retransmissions,
                accepted_transitions=current.accepted_transitions,
                observations_received=current.observations_received,
            )
            repo.save(updated)
            uow.commit()
            return updated
        except Exception:
            uow.rollback()
            raise

    def record_empty_success(
        self,
        *,
        registry_key: RegistryKey,
        attempted_at: datetime,
    ) -> ExternalSeriesSyncState:
        encode_utc_timestamp(attempted_at, field="attempted_at")
        definition = resolve_series_by_key(registry_key)
        uow = SQLiteImmediateUnitOfWork(self._db, busy_timeout_ms=self._busy_timeout_ms)
        try:
            uow.begin_immediate()
            repo = ExternalSeriesSyncStateRepository(self._db)
            current = repo.get(registry_key) or repo.initialize(registry_key)
            updated = ExternalSeriesSyncState(
                registry_key=current.registry_key,
                provider=current.provider,
                series_id=current.series_id,
                registry_contract_version=EXTERNAL_SERIES_REGISTRY_VERSION,
                last_attempt_at=attempted_at,
                last_success_at=attempted_at,
                next_refresh_eligible_at=attempted_at + operational_refresh_interval(definition.frequency),
                coverage_start=current.coverage_start,
                coverage_end=current.coverage_end,
                last_attempt_result=SyncAttemptResult.EMPTY,
                partial_coverage=False,
                last_error_code=None,
                last_http_status=None,
                last_valid_observation_event_id=current.last_valid_observation_event_id,
                consecutive_retransmissions=current.consecutive_retransmissions,
                accepted_transitions=current.accepted_transitions,
                observations_received=current.observations_received,
            )
            repo.save(updated)
            uow.commit()
            return updated
        except Exception:
            uow.rollback()
            raise

    def get_identity_as_of(
        self,
        identity: EconomicIdentity,
        *,
        consumer_as_of_date: date,
        consumer_as_of_timestamp: datetime,
    ) -> PersistedObservationEvent | None:
        return ExternalObservationRepository(self._db).get_identity_as_of(
            identity,
            consumer_as_of_date=consumer_as_of_date,
            consumer_as_of_timestamp=consumer_as_of_timestamp,
        )

    def get_latest_series_as_of(
        self,
        *,
        provider: Provider,
        series_id: str,
        consumer_as_of_date: date,
        consumer_as_of_timestamp: datetime,
    ) -> PersistedObservationEvent | None:
        return ExternalObservationRepository(self._db).get_latest_series_as_of(
            provider=provider,
            series_id=series_id,
            consumer_as_of_date=consumer_as_of_date,
            consumer_as_of_timestamp=consumer_as_of_timestamp,
        )

    @staticmethod
    def _recertify(observation: ExternalObservation) -> ExternalObservation:
        if not isinstance(observation, ExternalObservation):
            raise TypeError("observation must be an ExternalObservation.")
        provenance = observation.provenance
        payload = observation.content.as_payload_v1()
        payload["value_text"] = provenance.provider_value_text
        rebuilt = normalize_external_observation(
            payload,
            retrieved_at=provenance.retrieved_at,
            observed_at=provenance.observed_at,
            published_at=provenance.published_at,
            provider_revision_id=provenance.provider_revision_id,
            revised_at=provenance.revised_at,
        )
        if rebuilt.registry_key is not observation.registry_key:
            raise ValueError("Observation registry identity failed recertification.")
        return rebuilt

    @staticmethod
    def _record_success(
        repo: ExternalSeriesSyncStateRepository,
        observation: ExternalObservation,
        *,
        event: PersistedObservationEvent,
        retransmission: bool,
    ) -> None:
        definition = resolve_series_by_key(observation.registry_key)
        current = repo.get(observation.registry_key) or repo.initialize(observation.registry_key)
        start = observation.content.reference_period.start
        end = observation.content.reference_period.end
        coverage_start = min(current.coverage_start, start) if current.coverage_start else start
        coverage_end = max(current.coverage_end, end) if current.coverage_end else end
        retrieved_at = observation.provenance.retrieved_at
        repo.save(
            ExternalSeriesSyncState(
                registry_key=definition.registry_key.value,
                provider=definition.provider.value,
                series_id=definition.series_id,
                registry_contract_version=EXTERNAL_SERIES_REGISTRY_VERSION,
                last_attempt_at=retrieved_at,
                last_success_at=retrieved_at,
                next_refresh_eligible_at=retrieved_at + operational_refresh_interval(definition.frequency),
                coverage_start=coverage_start,
                coverage_end=coverage_end,
                last_attempt_result=SyncAttemptResult.SUCCESS,
                partial_coverage=False,
                last_error_code=None,
                last_http_status=None,
                last_valid_observation_event_id=event.observation_event_id,
                consecutive_retransmissions=(current.consecutive_retransmissions + 1 if retransmission else 0),
                accepted_transitions=current.accepted_transitions + (0 if retransmission else 1),
                observations_received=current.observations_received + 1,
            )
        )

    @staticmethod
    def _record_deferred_event(
        repo: ExternalSeriesSyncStateRepository,
        observation: ExternalObservation,
        *,
        event: PersistedObservationEvent,
        retransmission: bool,
    ) -> None:
        current = repo.get(observation.registry_key) or repo.initialize(observation.registry_key)
        repo.save(
            ExternalSeriesSyncState(
                registry_key=current.registry_key,
                provider=current.provider,
                series_id=current.series_id,
                registry_contract_version=current.registry_contract_version,
                last_attempt_at=current.last_attempt_at,
                last_success_at=current.last_success_at,
                next_refresh_eligible_at=current.next_refresh_eligible_at,
                coverage_start=current.coverage_start,
                coverage_end=current.coverage_end,
                last_attempt_result=current.last_attempt_result,
                partial_coverage=current.partial_coverage,
                last_error_code=current.last_error_code,
                last_http_status=current.last_http_status,
                last_valid_observation_event_id=event.observation_event_id,
                consecutive_retransmissions=(
                    current.consecutive_retransmissions + 1 if retransmission else 0
                ),
                accepted_transitions=current.accepted_transitions + (0 if retransmission else 1),
                observations_received=current.observations_received + 1,
            )
        )

    def _reject_stale_finalization(
        self,
        request: AcquisitionFinalizationRequest,
        current: ExternalSeriesSyncState,
    ) -> None:
        persisted_times = tuple(
            instant
            for instant in (current.last_attempt_at, current.last_success_at)
            if instant is not None
        )
        if persisted_times and request.operational_at < max(persisted_times):
            raise ExternalContextPersistenceError(
                ExternalContextPersistenceErrorCode.STALE_ACQUISITION_FINALIZATION,
                "The acquisition finalization is older than persisted operational state.",
                field="operational_at",
            )
        if current.last_valid_observation_event_id is not None:
            event = ExternalObservationRepository(self._db).get_by_id(
                current.last_valid_observation_event_id
            )
            if event is None:
                raise ExternalContextPersistenceError(
                    ExternalContextPersistenceErrorCode.INTEGRITY_VIOLATION,
                    "The sync-state last-known-good pointer does not resolve.",
                    field="last_valid_observation_event_id",
                )
            if request.operational_at < event.known_from:
                raise ExternalContextPersistenceError(
                    ExternalContextPersistenceErrorCode.STALE_ACQUISITION_FINALIZATION,
                    "The acquisition finalization predates its last-known-good event.",
                    field="operational_at",
                )

    @staticmethod
    def _build_finalized_state(
        request: AcquisitionFinalizationRequest,
        current: ExternalSeriesSyncState,
    ) -> ExternalSeriesSyncState:
        result = request.derived_result
        complete = result in {SyncAttemptResult.SUCCESS, SyncAttemptResult.EMPTY}
        definition = resolve_series_by_key(request.registry_key)
        if complete:
            coverage_start = request.requested_interval.start
            coverage_end = request.requested_interval.end
            last_success_at = request.operational_at
            next_refresh = request.operational_at + operational_refresh_interval(
                definition.frequency
            )
            error_code = None
            http_status = None
        else:
            coverage_start = current.coverage_start
            coverage_end = current.coverage_end
            last_success_at = current.last_success_at
            next_refresh = current.next_refresh_eligible_at
            error_code = request.error_code or next(
                (
                    chunk.error_code
                    for chunk in request.planned_chunks
                    if not chunk.is_complete and chunk.error_code is not None
                ),
                "ACQUISITION_PARTIAL"
                if result is SyncAttemptResult.PARTIAL
                else "ACQUISITION_FAILED",
            )
            http_status = request.http_status or next(
                (
                    chunk.http_status
                    for chunk in request.planned_chunks
                    if not chunk.is_complete and chunk.http_status is not None
                ),
                None,
            )
        return ExternalSeriesSyncState(
            registry_key=current.registry_key,
            provider=current.provider,
            series_id=current.series_id,
            registry_contract_version=(
                EXTERNAL_SERIES_REGISTRY_VERSION
                if result is not SyncAttemptResult.FAILED
                else current.registry_contract_version
            ),
            last_attempt_at=request.operational_at,
            last_success_at=last_success_at,
            next_refresh_eligible_at=next_refresh,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
            last_attempt_result=result,
            partial_coverage=result is SyncAttemptResult.PARTIAL,
            last_error_code=error_code,
            last_http_status=http_status,
            last_valid_observation_event_id=current.last_valid_observation_event_id,
            consecutive_retransmissions=current.consecutive_retransmissions,
            accepted_transitions=current.accepted_transitions,
            observations_received=current.observations_received,
        )

    @staticmethod
    def _finalization_result(
        request: AcquisitionFinalizationRequest,
        state: ExternalSeriesSyncState,
        *,
        repeated: bool,
    ) -> AcquisitionFinalizationResult:
        return AcquisitionFinalizationResult(
            acquisition_id=request.acquisition_id,
            global_result=request.derived_result,
            requested_interval=request.requested_interval,
            queried_intervals=request.queried_intervals,
            uncompleted_intervals=request.uncompleted_intervals,
            sync_state=state,
            repeated_finalization=repeated,
        )

    @staticmethod
    def _is_busy(exc: OperationalError) -> bool:
        original = exc.orig
        return isinstance(original, sqlite3.OperationalError) and (
            "locked" in str(original).lower() or "busy" in str(original).lower()
        )
