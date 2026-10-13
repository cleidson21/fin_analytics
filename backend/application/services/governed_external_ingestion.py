"""Governed orchestration from certified external acquisition to R3-D storage.

This module deliberately owns no HTTP transport and no persistence mechanism.
It joins the R3-E2 provider port to the existing R3-E1 store service, keeps
provider I/O outside SQLite transactions, and publishes a global operational
result only through ``finalize_acquisition``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum

from backend.application.ports.external_observation_provider import (
    ExternalObservationProvider,
    ExternalObservationProviderError,
    ProviderAcquisitionResult,
    ProviderAcquisitionStatus,
    ProviderChunkResult,
    ProviderChunkStatus,
    ProviderErrorCode,
    ProviderInterval,
)
from backend.application.services.external_observation_store import (
    AcquisitionChunkEvidence,
    AcquisitionFinalizationRequest,
    AcquisitionFinalizationResult,
    AcquisitionInterval,
    ExternalObservationStoreService,
    ObservationIngestionMode,
)
from backend.domains.external_context import (
    ExternalContextPersistenceError,
    ExternalSeriesSyncState,
    Frequency,
    ObservationWriteDisposition,
    RegistryKey,
    SyncAttemptResult,
    encode_utc_timestamp,
    resolve_series_by_key,
)


class AcquisitionIntent(str, Enum):
    """The only acquisition intents executable by the R3-E3 service."""

    ORDINARY_REFRESH = "ORDINARY_REFRESH"
    HISTORICAL_RECONCILIATION = "HISTORICAL_RECONCILIATION"


class GovernedIngestionStage(str, Enum):
    PROVIDER = "PROVIDER"
    PERSISTENCE = "PERSISTENCE"
    FINALIZATION = "FINALIZATION"


class GovernedIngestionErrorCode(str, Enum):
    PROVIDER_ACQUISITION_FAILED = "PROVIDER_ACQUISITION_FAILED"
    PROVIDER_RESULT_INVALID = "PROVIDER_RESULT_INVALID"
    PERSISTENCE_FAILED = "PERSISTENCE_FAILED"
    FINALIZATION_FAILED = "FINALIZATION_FAILED"
    FINALIZATION_RESULT_INVALID = "FINALIZATION_RESULT_INVALID"


class GovernedIngestionError(Exception):
    """Safe typed error for a stage that cannot produce a finalized result."""

    def __init__(
        self,
        code: GovernedIngestionErrorCode | str,
        *,
        stage: GovernedIngestionStage,
        acquisition_id: str,
        requested_interval: ProviderInterval,
        chunk_results: tuple["GovernedChunkResult", ...] = (),
    ) -> None:
        code_value = code.value if isinstance(code, GovernedIngestionErrorCode) else code
        _validate_safe_code(code_value)
        super().__init__(f"Governed external ingestion failed during {stage.value}.")
        self.code = code_value
        self.stage = stage
        self.acquisition_id = acquisition_id
        self.requested_interval = requested_interval
        self.chunk_results = chunk_results


@dataclass(frozen=True)
class GovernedAcquisitionRequest:
    """Explicit invocation; constructing or importing the service does no work."""

    acquisition_id: str
    registry_key: RegistryKey
    intent: AcquisitionIntent
    reference_date: date | None = None
    historical_interval: ProviderInterval | None = None

    def __post_init__(self) -> None:
        _validate_acquisition_id(self.acquisition_id)
        if not isinstance(self.registry_key, RegistryKey):
            raise TypeError("registry_key must be a RegistryKey.")
        resolve_series_by_key(self.registry_key)
        if not isinstance(self.intent, AcquisitionIntent):
            raise TypeError("intent must be an AcquisitionIntent.")
        if self.reference_date is not None and type(self.reference_date) is not date:
            raise TypeError("reference_date must be a strict civil date or None.")
        if self.historical_interval is not None and not isinstance(
            self.historical_interval, ProviderInterval
        ):
            raise TypeError("historical_interval must be a ProviderInterval or None.")
        if self.intent is AcquisitionIntent.ORDINARY_REFRESH:
            if self.reference_date is None or self.historical_interval is not None:
                raise ValueError(
                    "ORDINARY_REFRESH requires reference_date and forbids a historical interval."
                )
        elif self.reference_date is not None or self.historical_interval is None:
            raise ValueError(
                "HISTORICAL_RECONCILIATION requires one explicit interval and no reference_date."
            )

    @property
    def requested_interval(self) -> ProviderInterval:
        if self.intent is AcquisitionIntent.ORDINARY_REFRESH:
            assert self.reference_date is not None
            return ordinary_revision_interval(self.registry_key, self.reference_date)
        assert self.historical_interval is not None
        _validate_interval_floor(self.registry_key, self.historical_interval)
        return self.historical_interval


@dataclass(frozen=True)
class GovernedChunkResult:
    """Auditable provider and persistence outcome for one original chunk."""

    interval: ProviderInterval
    provider_status: ProviderChunkStatus
    response_received: bool
    payload_validated: bool
    normalization_completed: bool
    observation_count: int
    persistence_attempted: int
    persistence_confirmed: int
    inserted_transitions: int
    retransmissions: int
    persistence_completed: bool
    empty_response: bool
    retrieved_at: datetime | None = None
    http_status: int | None = None
    error_stage: GovernedIngestionStage | None = None
    error_code: str | None = None
    terminal_failure: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.interval, ProviderInterval):
            raise TypeError("interval must be a ProviderInterval.")
        if not isinstance(self.provider_status, ProviderChunkStatus):
            raise TypeError("provider_status must be a ProviderChunkStatus.")
        for field_name in (
            "response_received",
            "payload_validated",
            "normalization_completed",
            "persistence_completed",
            "empty_response",
            "terminal_failure",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a strict boolean.")
        for field_name in (
            "observation_count",
            "persistence_attempted",
            "persistence_confirmed",
            "inserted_transitions",
            "retransmissions",
        ):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field_name} must be a non-negative strict integer.")
        if self.persistence_attempted > self.observation_count:
            raise ValueError("Persistence attempts cannot exceed provider observations.")
        if self.persistence_confirmed > self.persistence_attempted:
            raise ValueError("Confirmed persistence cannot exceed attempts.")
        if self.inserted_transitions + self.retransmissions != self.persistence_confirmed:
            raise ValueError("Persistence dispositions must equal confirmed operations.")
        if self.persistence_completed:
            if not (
                self.response_received
                and self.payload_validated
                and self.normalization_completed
            ):
                raise ValueError("Persistence completion requires complete provider certification.")
            if self.persistence_confirmed != self.observation_count:
                raise ValueError("Every observation must be confirmed for chunk completion.")
        if self.empty_response:
            if self.observation_count != 0 or not self.persistence_completed:
                raise ValueError("A valid empty chunk is complete and contains no observations.")
        if self.error_stage is None and self.error_code is not None:
            raise ValueError("An error code requires an error stage.")
        if self.error_stage is not None and self.error_code is None:
            raise ValueError("An error stage requires a safe error code.")
        if self.error_code is not None:
            _validate_safe_code(self.error_code)
        if self.http_status is not None and (
            type(self.http_status) is not int or not 100 <= self.http_status <= 599
        ):
            raise ValueError("http_status must be a valid HTTP status or None.")
        if self.retrieved_at is not None:
            encode_utc_timestamp(self.retrieved_at, field="retrieved_at")

    @property
    def is_complete(self) -> bool:
        return self.persistence_completed


@dataclass(frozen=True)
class GovernedIngestionResult:
    acquisition_id: str
    registry_key: RegistryKey
    intent: AcquisitionIntent
    requested_interval: ProviderInterval
    provider_status: ProviderAcquisitionStatus
    global_result: SyncAttemptResult
    chunk_results: tuple[GovernedChunkResult, ...]
    finalization: AcquisitionFinalizationResult

    def __post_init__(self) -> None:
        _validate_acquisition_id(self.acquisition_id)
        if not isinstance(self.registry_key, RegistryKey):
            raise TypeError("registry_key must be a RegistryKey.")
        if not isinstance(self.intent, AcquisitionIntent):
            raise TypeError("intent must be an AcquisitionIntent.")
        if not isinstance(self.requested_interval, ProviderInterval):
            raise TypeError("requested_interval must be a ProviderInterval.")
        if not isinstance(self.provider_status, ProviderAcquisitionStatus):
            raise TypeError("provider_status must be a ProviderAcquisitionStatus.")
        if not isinstance(self.global_result, SyncAttemptResult):
            raise TypeError("global_result must be a SyncAttemptResult.")
        if type(self.chunk_results) is not tuple or not self.chunk_results:
            raise ValueError("chunk_results must be a non-empty tuple.")
        if not isinstance(self.finalization, AcquisitionFinalizationResult):
            raise TypeError("finalization must be an AcquisitionFinalizationResult.")
        if self.finalization.acquisition_id != self.acquisition_id:
            raise ValueError("Finalization identity does not match the acquisition.")
        if self.finalization.global_result is not self.global_result:
            raise ValueError("Finalization result does not match the governed result.")

    @property
    def sync_state(self) -> ExternalSeriesSyncState:
        return self.finalization.sync_state

    @property
    def persistence_confirmed(self) -> int:
        return sum(chunk.persistence_confirmed for chunk in self.chunk_results)

    @property
    def inserted_transitions(self) -> int:
        return sum(chunk.inserted_transitions for chunk in self.chunk_results)

    @property
    def retransmissions(self) -> int:
        return sum(chunk.retransmissions for chunk in self.chunk_results)


def ordinary_revision_interval(
    registry_key: RegistryKey,
    reference_date: date,
) -> ProviderInterval:
    """Apply the locked DAILY 90-day or MONTHLY 24-calendar-month window."""

    if not isinstance(registry_key, RegistryKey):
        raise TypeError("registry_key must be a RegistryKey.")
    if type(reference_date) is not date:
        raise TypeError("reference_date must be a strict civil date.")
    definition = resolve_series_by_key(registry_key)
    floor = definition.earliest_normalized_date
    if reference_date < floor:
        raise ValueError("reference_date precedes the registry-normalized floor.")
    if definition.frequency is Frequency.DAILY:
        start = max(floor, reference_date - timedelta(days=89))
    elif definition.frequency is Frequency.MONTHLY:
        absolute_month = reference_date.year * 12 + (reference_date.month - 1) - 23
        year, zero_based_month = divmod(absolute_month, 12)
        start = max(floor, date(year, zero_based_month + 1, 1))
    else:  # The executable registry is closed; fail if corrupted.
        raise ValueError("The registry frequency has no governed revision window.")
    return ProviderInterval(start=start, end=reference_date)


class GovernedExternalIngestionService:
    """Execute one explicit provider acquisition and evidence-backed finalization."""

    def __init__(
        self,
        *,
        provider: ExternalObservationProvider,
        store: ExternalObservationStoreService,
        utc_clock: Callable[[], datetime],
    ) -> None:
        if not isinstance(provider, ExternalObservationProvider):
            raise TypeError("provider must implement ExternalObservationProvider.")
        if not isinstance(store, ExternalObservationStoreService):
            raise TypeError("store must be an ExternalObservationStoreService.")
        if not callable(utc_clock):
            raise TypeError("utc_clock must be callable.")
        self._provider = provider
        self._store = store
        self._utc_clock = utc_clock

    def ingest(self, request: GovernedAcquisitionRequest) -> GovernedIngestionResult:
        if not isinstance(request, GovernedAcquisitionRequest):
            raise TypeError("request must be a GovernedAcquisitionRequest.")
        interval = request.requested_interval

        # The provider completes all HTTP work before any SQLite write begins.
        try:
            provider_result = self._provider.acquire(
                request.registry_key,
                interval.start,
                interval.end,
                correlation_id=request.acquisition_id,
            )
        except ExternalObservationProviderError as exc:
            raise GovernedIngestionError(
                exc.code.value,
                stage=GovernedIngestionStage.PROVIDER,
                acquisition_id=request.acquisition_id,
                requested_interval=interval,
            ) from exc
        except Exception as exc:
            raise GovernedIngestionError(
                GovernedIngestionErrorCode.PROVIDER_ACQUISITION_FAILED,
                stage=GovernedIngestionStage.PROVIDER,
                acquisition_id=request.acquisition_id,
                requested_interval=interval,
            ) from exc

        try:
            self._validate_provider_result(request, interval, provider_result)
        except Exception as exc:
            raise GovernedIngestionError(
                GovernedIngestionErrorCode.PROVIDER_RESULT_INVALID,
                stage=GovernedIngestionStage.PROVIDER,
                acquisition_id=request.acquisition_id,
                requested_interval=interval,
            ) from exc

        governed_chunks = tuple(
            self._process_chunk(chunk) for chunk in provider_result.chunk_results
        )
        evidences = tuple(self._to_finalization_evidence(chunk) for chunk in governed_chunks)
        derived_result = _derive_global_result(evidences)
        try:
            operational_at = self._utc_clock()
            encode_utc_timestamp(operational_at, field="operational_at")
            finalization_request = AcquisitionFinalizationRequest(
                acquisition_id=request.acquisition_id,
                registry_key=request.registry_key,
                requested_interval=AcquisitionInterval(interval.start, interval.end),
                operational_at=operational_at,
                planned_chunks=evidences,
                declared_result=derived_result,
                error_code=_first_error_code(governed_chunks),
                http_status=_first_provider_failure_status(governed_chunks),
            )
            finalization = self._store.finalize_acquisition(finalization_request)
        except Exception as exc:
            code = (
                exc.code.value
                if isinstance(exc, ExternalContextPersistenceError)
                else GovernedIngestionErrorCode.FINALIZATION_FAILED.value
            )
            raise GovernedIngestionError(
                code,
                stage=GovernedIngestionStage.FINALIZATION,
                acquisition_id=request.acquisition_id,
                requested_interval=interval,
                chunk_results=governed_chunks,
            ) from exc

        if finalization.global_result is not derived_result:
            raise GovernedIngestionError(
                GovernedIngestionErrorCode.FINALIZATION_RESULT_INVALID,
                stage=GovernedIngestionStage.FINALIZATION,
                acquisition_id=request.acquisition_id,
                requested_interval=interval,
                chunk_results=governed_chunks,
            )
        return GovernedIngestionResult(
            acquisition_id=request.acquisition_id,
            registry_key=request.registry_key,
            intent=request.intent,
            requested_interval=interval,
            provider_status=provider_result.status,
            global_result=derived_result,
            chunk_results=governed_chunks,
            finalization=finalization,
        )

    @staticmethod
    def _validate_provider_result(
        request: GovernedAcquisitionRequest,
        interval: ProviderInterval,
        result: ProviderAcquisitionResult,
    ) -> None:
        if not isinstance(result, ProviderAcquisitionResult):
            raise TypeError("The provider returned an unsupported acquisition result.")
        if result.registry_key is not request.registry_key:
            raise ValueError("Provider result registry key differs from the request.")
        if result.requested_interval != interval:
            raise ValueError("Provider result interval differs from the request.")
        flattened = tuple(
            observation
            for chunk in result.chunk_results
            for observation in chunk.observations
        )
        if result.observations != flattened or result.status is not result.derived_status:
            raise ValueError("Provider aggregate counts or status are inconsistent.")
        if (
            result.planned_chunks[0].start != interval.start
            or result.planned_chunks[-1].end != interval.end
        ):
            raise ValueError("Provider chunks do not cover the requested boundaries.")
        previous_end: date | None = None
        for chunk in result.chunk_results:
            if previous_end is not None and chunk.interval.start != previous_end + timedelta(days=1):
                raise ValueError("Provider chunks must be ordered, gap-free, and non-overlapping.")
            previous_end = chunk.interval.end
            for observation in chunk.observations:
                if observation.registry_key is not request.registry_key:
                    raise ValueError("A provider observation uses another registry key.")
                # Monthly observations describe the whole economic month, whose
                # end may follow an explicit mid-month request end. The provider
                # record's normalized period start remains the bounded anchor.
                anchor = observation.content.reference_period.start
                if not chunk.interval.start <= anchor <= chunk.interval.end:
                    raise ValueError("A provider observation lies outside its chunk.")

    def _process_chunk(self, chunk: ProviderChunkResult) -> GovernedChunkResult:
        if chunk.status in {ProviderChunkStatus.FAILED, ProviderChunkStatus.INCOMPLETE}:
            return GovernedChunkResult(
                interval=chunk.interval,
                provider_status=chunk.status,
                response_received=chunk.response_received,
                payload_validated=chunk.payload_validated,
                normalization_completed=chunk.normalization_completed,
                observation_count=chunk.observation_count,
                persistence_attempted=0,
                persistence_confirmed=0,
                inserted_transitions=0,
                retransmissions=0,
                persistence_completed=False,
                empty_response=False,
                retrieved_at=chunk.retrieved_at,
                http_status=chunk.http_status,
                error_stage=GovernedIngestionStage.PROVIDER,
                error_code=(chunk.error_code or ProviderErrorCode.CERTIFICATION_REJECTED).value,
                terminal_failure=chunk.terminal_failure,
            )
        if chunk.status is ProviderChunkStatus.EMPTY:
            return GovernedChunkResult(
                interval=chunk.interval,
                provider_status=chunk.status,
                response_received=chunk.response_received,
                payload_validated=chunk.payload_validated,
                normalization_completed=chunk.normalization_completed,
                observation_count=0,
                persistence_attempted=0,
                persistence_confirmed=0,
                inserted_transitions=0,
                retransmissions=0,
                persistence_completed=True,
                empty_response=True,
                retrieved_at=chunk.retrieved_at,
                http_status=chunk.http_status,
            )

        attempted = confirmed = inserted = retransmissions = 0
        error_code: str | None = None
        for observation in chunk.observations:
            attempted += 1
            try:
                write = self._store.ingest(
                    observation,
                    acquisition_mode=ObservationIngestionMode.DEFERRED,
                )
            except Exception as exc:
                error_code = (
                    exc.code.value
                    if isinstance(exc, ExternalContextPersistenceError)
                    else GovernedIngestionErrorCode.PERSISTENCE_FAILED.value
                )
                break
            confirmed += 1
            if write.disposition is ObservationWriteDisposition.INSERTED:
                inserted += 1
            elif write.disposition is ObservationWriteDisposition.RETRANSMISSION:
                retransmissions += 1
            else:
                error_code = GovernedIngestionErrorCode.PERSISTENCE_FAILED.value
                break

        completed = error_code is None and confirmed == chunk.observation_count
        return GovernedChunkResult(
            interval=chunk.interval,
            provider_status=chunk.status,
            response_received=chunk.response_received,
            payload_validated=chunk.payload_validated,
            normalization_completed=chunk.normalization_completed,
            observation_count=chunk.observation_count,
            persistence_attempted=attempted,
            persistence_confirmed=confirmed,
            inserted_transitions=inserted,
            retransmissions=retransmissions,
            persistence_completed=completed,
            empty_response=False,
            retrieved_at=chunk.retrieved_at,
            http_status=chunk.http_status,
            error_stage=(GovernedIngestionStage.PERSISTENCE if error_code else None),
            error_code=error_code,
            terminal_failure=error_code is not None,
        )

    @staticmethod
    def _to_finalization_evidence(
        chunk: GovernedChunkResult,
    ) -> AcquisitionChunkEvidence:
        return AcquisitionChunkEvidence(
            interval=AcquisitionInterval(chunk.interval.start, chunk.interval.end),
            response_received=chunk.response_received,
            payload_validated=(
                chunk.payload_validated and chunk.normalization_completed
            ),
            persistence_completed=chunk.persistence_completed,
            observations_received=chunk.observation_count,
            empty_response=chunk.empty_response,
            error_code=chunk.error_code,
            http_status=(
                chunk.http_status
                if chunk.error_stage is GovernedIngestionStage.PROVIDER
                else None
            ),
        )


def _validate_interval_floor(
    registry_key: RegistryKey,
    interval: ProviderInterval,
) -> None:
    definition = resolve_series_by_key(registry_key)
    if interval.start < definition.earliest_normalized_date:
        raise ValueError("The historical interval precedes the registry-normalized floor.")


def _validate_acquisition_id(value: str) -> None:
    if type(value) is not str or not 1 <= len(value) <= 128:
        raise ValueError("acquisition_id must contain between 1 and 128 characters.")
    if any(
        not (character.isascii() and (character.isalnum() or character in "-_.:"))
        for character in value
    ):
        raise ValueError("acquisition_id contains unsafe characters.")


def _validate_safe_code(value: str) -> None:
    if type(value) is not str or not 1 <= len(value) <= 64:
        raise ValueError("error code must contain between 1 and 64 characters.")
    if any(
        not (
            character.isascii()
            and (character.isupper() or character.isdigit() or character == "_")
        )
        for character in value
    ):
        raise ValueError("error code must use uppercase ASCII letters, digits, or underscores.")


def _derive_global_result(
    chunks: tuple[AcquisitionChunkEvidence, ...],
) -> SyncAttemptResult:
    completed = tuple(chunk for chunk in chunks if chunk.is_complete)
    if len(completed) == len(chunks):
        return (
            SyncAttemptResult.EMPTY
            if all(chunk.empty_response for chunk in completed)
            else SyncAttemptResult.SUCCESS
        )
    if completed:
        return SyncAttemptResult.PARTIAL
    return SyncAttemptResult.FAILED


def _first_error_code(chunks: tuple[GovernedChunkResult, ...]) -> str | None:
    return next((chunk.error_code for chunk in chunks if chunk.error_code is not None), None)


def _first_provider_failure_status(
    chunks: tuple[GovernedChunkResult, ...],
) -> int | None:
    return next(
        (
            chunk.http_status
            for chunk in chunks
            if chunk.error_stage is GovernedIngestionStage.PROVIDER
            and chunk.http_status is not None
        ),
        None,
    )
