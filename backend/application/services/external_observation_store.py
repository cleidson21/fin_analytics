"""Application-owned R3-D transaction, history, and sync-state orchestration."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from datetime import date, datetime
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
    ) -> ObservationWriteResult:
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
                    self._record_success(
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
                    self._record_success(
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
    def _is_busy(exc: OperationalError) -> bool:
        original = exc.orig
        return isinstance(original, sqlite3.OperationalError) and (
            "locked" in str(original).lower() or "busy" in str(original).lower()
        )
