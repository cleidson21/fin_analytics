"""Purpose-limited point-in-time reads over the certified External Context store."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from backend.application.services.external_observation_store import (
    ExternalObservationStoreService,
)
from backend.domain.exceptions.base import FINAnalyticsError
from backend.domains.external_context import (
    EXTERNAL_SERIES_REGISTRY_VERSION,
    AcquisitionHealth,
    Availability,
    EconomicFreshness,
    ExternalContextReasonCode,
    ExternalSeriesSyncState,
    FreshnessEvidence,
    PersistedObservationEvent,
    RegistryKey,
    SyncAttemptResult,
    encode_utc_timestamp,
    evaluate_external_series_state,
    resolve_series_by_key,
)
from backend.domains.external_context.purposes import (
    EXTERNAL_REFERENCE_PURPOSE_ALLOWLIST,
    ExternalReferencePurpose,
)


class ExternalReferenceContextErrorCode(str, Enum):
    PURPOSE_NOT_ALLOWED = "PURPOSE_NOT_ALLOWED"


class ExternalReferenceContextError(FINAnalyticsError):
    """Stable, safe failure for the R3-F1 read boundary."""

    def __init__(
        self,
        code: ExternalReferenceContextErrorCode,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = MappingProxyType(dict(details or {}))


@dataclass(frozen=True)
class ExternalReferenceContextRequest:
    purpose: ExternalReferencePurpose
    reference_key: RegistryKey
    consumer_as_of_date: date
    consumer_as_of_timestamp: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.purpose, ExternalReferencePurpose):
            raise TypeError("purpose must be an ExternalReferencePurpose.")
        if not isinstance(self.reference_key, RegistryKey):
            raise TypeError("reference_key must be a RegistryKey.")
        if type(self.consumer_as_of_date) is not date:
            raise TypeError("consumer_as_of_date must be a civil date.")
        encode_utc_timestamp(
            self.consumer_as_of_timestamp,
            field="consumer_as_of_timestamp",
        )
        object.__setattr__(
            self,
            "consumer_as_of_timestamp",
            self.consumer_as_of_timestamp.astimezone(timezone.utc),
        )


@dataclass(frozen=True)
class ExternalReferenceReplay:
    """Deterministic result of the economic-date and knowledge-time cuts."""

    reference: PersistedObservationEvent | None
    availability: Availability
    reason_code: ExternalContextReasonCode | None

    def __post_init__(self) -> None:
        if self.reference is None:
            if self.availability is not Availability.UNAVAILABLE:
                raise ValueError("Absent reference must be UNAVAILABLE.")
            if self.reason_code is not ExternalContextReasonCode.NO_ELIGIBLE_OBSERVATION:
                raise ValueError("Absent reference requires NO_ELIGIBLE_OBSERVATION.")
            return
        if not isinstance(self.reference, PersistedObservationEvent):
            raise TypeError("reference must be a PersistedObservationEvent or None.")
        if self.availability is not Availability.AVAILABLE:
            raise ValueError("An eligible point reference must be AVAILABLE.")
        if self.reason_code is not None:
            raise ValueError("An available point reference has no availability reason.")


@dataclass(frozen=True)
class ExternalOperationalStateSnapshot:
    """Current mutable operational evidence; never a historical replay claim."""

    sync_state: ExternalSeriesSyncState | None
    state_observed_at: datetime | None
    economic_freshness: EconomicFreshness
    acquisition_health: AcquisitionHealth
    reason_code: ExternalContextReasonCode | None

    def __post_init__(self) -> None:
        if self.sync_state is not None and not isinstance(
            self.sync_state, ExternalSeriesSyncState
        ):
            raise TypeError("sync_state must be ExternalSeriesSyncState or None.")
        if self.state_observed_at is not None:
            encode_utc_timestamp(self.state_observed_at, field="state_observed_at")
        if not isinstance(self.economic_freshness, EconomicFreshness):
            raise TypeError("economic_freshness must be EconomicFreshness.")
        if not isinstance(self.acquisition_health, AcquisitionHealth):
            raise TypeError("acquisition_health must be AcquisitionHealth.")
        if self.reason_code is not None and not isinstance(
            self.reason_code, ExternalContextReasonCode
        ):
            raise TypeError("reason_code must be ExternalContextReasonCode or None.")


@dataclass(frozen=True)
class ExternalReferenceContextResult:
    purpose: ExternalReferencePurpose
    reference_key: RegistryKey
    consumer_as_of_date: date
    consumer_as_of_timestamp: datetime
    reference_replay: ExternalReferenceReplay
    operational_state_snapshot: ExternalOperationalStateSnapshot

    def __post_init__(self) -> None:
        validated = ExternalReferenceContextRequest(
            purpose=self.purpose,
            reference_key=self.reference_key,
            consumer_as_of_date=self.consumer_as_of_date,
            consumer_as_of_timestamp=self.consumer_as_of_timestamp,
        )
        object.__setattr__(
            self,
            "consumer_as_of_timestamp",
            validated.consumer_as_of_timestamp,
        )
        if not isinstance(self.reference_replay, ExternalReferenceReplay):
            raise TypeError("reference_replay must be ExternalReferenceReplay.")
        if not isinstance(
            self.operational_state_snapshot,
            ExternalOperationalStateSnapshot,
        ):
            raise TypeError(
                "operational_state_snapshot must be ExternalOperationalStateSnapshot."
            )


class ExternalReferenceContextService:
    """Read-only R3-F1 boundary over certified Registry and Store services."""

    def __init__(self, store: ExternalObservationStoreService) -> None:
        self._store = store

    def read_reference(
        self,
        request: ExternalReferenceContextRequest,
    ) -> ExternalReferenceContextResult:
        if not isinstance(request, ExternalReferenceContextRequest):
            raise TypeError("request must be an ExternalReferenceContextRequest.")

        allowed_keys = EXTERNAL_REFERENCE_PURPOSE_ALLOWLIST[request.purpose]
        if request.reference_key not in allowed_keys:
            raise ExternalReferenceContextError(
                ExternalReferenceContextErrorCode.PURPOSE_NOT_ALLOWED,
                "The external reference key is not allowed for this purpose.",
                details={
                    "purpose": request.purpose.value,
                    "reference_key": request.reference_key.value,
                },
            )

        definition = resolve_series_by_key(request.reference_key)
        event = self._store.get_latest_series_as_of(
            provider=definition.provider,
            series_id=definition.series_id,
            consumer_as_of_date=request.consumer_as_of_date,
            consumer_as_of_timestamp=request.consumer_as_of_timestamp,
        )
        state = self._store.get_sync_state(request.reference_key)

        replay = ExternalReferenceReplay(
            reference=event,
            availability=(
                Availability.AVAILABLE
                if event is not None
                else Availability.UNAVAILABLE
            ),
            reason_code=(
                None
                if event is not None
                else ExternalContextReasonCode.NO_ELIGIBLE_OBSERVATION
            ),
        )
        operational = self._build_operational_snapshot(
            event=event,
            state=state,
            consumer_as_of_date=request.consumer_as_of_date,
        )
        return ExternalReferenceContextResult(
            purpose=request.purpose,
            reference_key=request.reference_key,
            consumer_as_of_date=request.consumer_as_of_date,
            consumer_as_of_timestamp=request.consumer_as_of_timestamp,
            reference_replay=replay,
            operational_state_snapshot=operational,
        )

    @staticmethod
    def _build_operational_snapshot(
        *,
        event: PersistedObservationEvent | None,
        state: ExternalSeriesSyncState | None,
        consumer_as_of_date: date,
    ) -> ExternalOperationalStateSnapshot:
        if (
            state is not None
            and state.registry_contract_version != EXTERNAL_SERIES_REGISTRY_VERSION
        ):
            return ExternalOperationalStateSnapshot(
                sync_state=state,
                state_observed_at=None,
                economic_freshness=EconomicFreshness.UNKNOWN,
                acquisition_health=AcquisitionHealth.UNKNOWN,
                reason_code=ExternalContextReasonCode.REGISTRY_VERSION_MISMATCH,
            )

        freshness_evidence = FreshnessEvidence.INSUFFICIENT
        if (
            state is not None
            and ExternalReferenceContextService._has_current_freshness_evidence(
                event=event,
                state=state,
                consumer_as_of_date=consumer_as_of_date,
            )
        ):
            freshness_evidence = FreshnessEvidence.CURRENT
        evaluated = evaluate_external_series_state(
            state=state,
            has_eligible_observation=event is not None,
            requested_start=consumer_as_of_date,
            requested_end=consumer_as_of_date,
            freshness_evidence=freshness_evidence,
            current_registry_version=EXTERNAL_SERIES_REGISTRY_VERSION,
        )

        if state is None or state.last_attempt_result is None:
            reason = ExternalContextReasonCode.NEVER_ACQUIRED
        elif state.last_attempt_result is SyncAttemptResult.PARTIAL:
            reason = ExternalContextReasonCode.ACQUISITION_PARTIAL
        elif state.last_attempt_result is SyncAttemptResult.FAILED:
            reason = ExternalContextReasonCode.ACQUISITION_FAILED
        elif evaluated.economic_freshness is EconomicFreshness.UNKNOWN:
            reason = ExternalContextReasonCode.INSUFFICIENT_FRESHNESS_EVIDENCE
        else:
            reason = None

        return ExternalOperationalStateSnapshot(
            sync_state=state,
            state_observed_at=None,
            economic_freshness=evaluated.economic_freshness,
            acquisition_health=evaluated.acquisition_health,
            reason_code=reason,
        )

    @staticmethod
    def _has_current_freshness_evidence(
        *,
        event: PersistedObservationEvent | None,
        state: ExternalSeriesSyncState,
        consumer_as_of_date: date,
    ) -> bool:
        if event is None:
            return False
        if state.last_attempt_result not in (
            SyncAttemptResult.SUCCESS,
            SyncAttemptResult.EMPTY,
        ):
            return False
        if state.partial_coverage:
            return False
        if (
            state.last_attempt_at is None
            or state.last_success_at is None
            or state.last_attempt_at != state.last_success_at
        ):
            return False
        if state.coverage_start is None or state.coverage_end is None:
            return False
        if not state.coverage_start <= consumer_as_of_date <= state.coverage_end:
            return False
        return state.last_valid_observation_event_id == event.observation_event_id


__all__ = [
    "ExternalOperationalStateSnapshot",
    "ExternalReferenceContextError",
    "ExternalReferenceContextErrorCode",
    "ExternalReferenceContextRequest",
    "ExternalReferenceContextResult",
    "ExternalReferenceContextService",
    "ExternalReferenceReplay",
]
