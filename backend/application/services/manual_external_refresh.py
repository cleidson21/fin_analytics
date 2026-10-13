"""Explicit internal trigger for governed External Context refreshes.

R3-E4 owns only request validation, read-only eligibility evaluation, and
delegation to the R3-E3 orchestrator. It owns no provider, persistence,
finalization, scheduling, startup, or HTTP surface behavior.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum

from backend.application.ports.external_observation_provider import ProviderInterval
from backend.application.services.governed_external_ingestion import (
    AcquisitionIntent,
    GovernedAcquisitionRequest,
    GovernedExternalIngestionService,
    GovernedIngestionError,
    GovernedIngestionResult,
)
from backend.domains.external_context import (
    EXTERNAL_SERIES_REGISTRY_VERSION,
    ExternalSeriesDefinition,
    ExternalSeriesSyncState,
    RegistryKey,
    SyncAttemptResult,
    encode_utc_timestamp,
    is_refresh_due,
    operational_refresh_interval,
    resolve_series_by_key,
)


logger = logging.getLogger(__name__)


class ManualRefreshEligibilityReason(str, Enum):
    """Safe, auditable reasons for an R3-E4 eligibility conclusion."""

    INITIAL_REFRESH = "INITIAL_REFRESH"
    COOLDOWN_ACTIVE = "COOLDOWN_ACTIVE"
    COOLDOWN_ELAPSED = "COOLDOWN_ELAPSED"
    RETRY_AFTER_PARTIAL = "RETRY_AFTER_PARTIAL"
    RETRY_AFTER_FAILED = "RETRY_AFTER_FAILED"
    NO_SUCCESS_EVIDENCE = "NO_SUCCESS_EVIDENCE"
    CLOCK_REGRESSION = "CLOCK_REGRESSION"
    REGISTRY_VERSION_MISMATCH = "REGISTRY_VERSION_MISMATCH"
    SYNC_STATE_IDENTITY_MISMATCH = "SYNC_STATE_IDENTITY_MISMATCH"


class ManualRefreshStatus(str, Enum):
    """Manual-trigger outcome, distinct from provider-only evidence."""

    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    SUCCESS = "SUCCESS"
    EMPTY = "EMPTY"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ManualRefreshRequest:
    """One explicit internal request; arbitrary provider inputs are impossible."""

    acquisition_id: str
    registry_key: RegistryKey
    intent: AcquisitionIntent
    reference_date: date | None = None
    historical_interval: ProviderInterval | None = None

    def __post_init__(self) -> None:
        # Reuse R3-E3's locked request validation rather than reproducing it.
        self.to_governed_request()

    def to_governed_request(self) -> GovernedAcquisitionRequest:
        request = GovernedAcquisitionRequest(
            acquisition_id=self.acquisition_id,
            registry_key=self.registry_key,
            intent=self.intent,
            reference_date=self.reference_date,
            historical_interval=self.historical_interval,
        )
        # Force R3-E3's registry-floor and interval validation at the manual
        # request boundary, before any eligibility read can occur.
        _ = request.requested_interval
        return request


@dataclass(frozen=True)
class ManualRefreshEligibility:
    eligible: bool
    reason: ManualRefreshEligibilityReason
    evaluated_at: datetime
    registry_key: RegistryKey
    intent: AcquisitionIntent
    refresh_interval: timedelta
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    last_attempt_result: SyncAttemptResult | None
    next_eligible_at: datetime | None

    def __post_init__(self) -> None:
        if type(self.eligible) is not bool:
            raise TypeError("eligible must be a strict boolean.")
        if not isinstance(self.reason, ManualRefreshEligibilityReason):
            raise TypeError("reason must be a ManualRefreshEligibilityReason.")
        encode_utc_timestamp(self.evaluated_at, field="evaluated_at")
        if not isinstance(self.registry_key, RegistryKey):
            raise TypeError("registry_key must be a RegistryKey.")
        if not isinstance(self.intent, AcquisitionIntent):
            raise TypeError("intent must be an AcquisitionIntent.")
        if (
            not isinstance(self.refresh_interval, timedelta)
            or self.refresh_interval <= timedelta(0)
        ):
            raise ValueError("refresh_interval must be a positive timedelta.")
        for field_name in ("last_attempt_at", "last_success_at", "next_eligible_at"):
            value = getattr(self, field_name)
            if value is not None:
                encode_utc_timestamp(value, field=field_name)
        if self.last_attempt_result is not None and not isinstance(
            self.last_attempt_result, SyncAttemptResult
        ):
            raise TypeError("last_attempt_result must be a SyncAttemptResult or None.")


@dataclass(frozen=True)
class ManualRefreshResult:
    acquisition_id: str
    registry_key: RegistryKey
    intent: AcquisitionIntent
    status: ManualRefreshStatus
    eligibility: ManualRefreshEligibility
    ingestion: GovernedIngestionResult | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ManualRefreshStatus):
            raise TypeError("status must be a ManualRefreshStatus.")
        if not isinstance(self.eligibility, ManualRefreshEligibility):
            raise TypeError("eligibility must be a ManualRefreshEligibility.")
        if self.eligibility.registry_key is not self.registry_key:
            raise ValueError("Eligibility registry key differs from the manual result.")
        if self.eligibility.intent is not self.intent:
            raise ValueError("Eligibility intent differs from the manual result.")
        if self.status is ManualRefreshStatus.NOT_ELIGIBLE:
            if self.eligibility.eligible or self.ingestion is not None:
                raise ValueError("An ineligible result cannot contain an ingestion result.")
            return
        if not self.eligibility.eligible or not isinstance(
            self.ingestion, GovernedIngestionResult
        ):
            raise ValueError("An executed result requires eligible governed ingestion.")
        if (
            self.ingestion.acquisition_id != self.acquisition_id
            or self.ingestion.registry_key is not self.registry_key
            or self.ingestion.intent is not self.intent
        ):
            raise ValueError("Governed ingestion identity differs from the manual request.")
        if self.status.value != self.ingestion.global_result.value:
            raise ValueError("Manual and governed global results differ.")

    @property
    def global_result(self) -> SyncAttemptResult | None:
        return self.ingestion.global_result if self.ingestion is not None else None

    @property
    def sync_state(self) -> ExternalSeriesSyncState | None:
        return self.ingestion.sync_state if self.ingestion is not None else None


def evaluate_manual_refresh_eligibility(
    *,
    definition: ExternalSeriesDefinition,
    state: ExternalSeriesSyncState | None,
    at: datetime,
    intent: AcquisitionIntent,
) -> ManualRefreshEligibility:
    """Decide eligibility without I/O, mutation, or an implicit clock read."""

    if not isinstance(definition, ExternalSeriesDefinition):
        raise TypeError("definition must be an ExternalSeriesDefinition.")
    canonical = resolve_series_by_key(definition.registry_key)
    if definition != canonical:
        raise ValueError("definition must be the canonical executable registry entry.")
    encode_utc_timestamp(at, field="at")
    if not isinstance(intent, AcquisitionIntent):
        raise TypeError("intent must be an AcquisitionIntent.")

    interval = operational_refresh_interval(definition.frequency)
    if state is None:
        return _eligibility(
            eligible=True,
            reason=ManualRefreshEligibilityReason.INITIAL_REFRESH,
            definition=definition,
            state=None,
            at=at,
            intent=intent,
            refresh_interval=interval,
        )

    if (
        state.registry_key != definition.registry_key.value
        or state.provider != definition.provider.value
        or state.series_id != definition.series_id
    ):
        return _eligibility(
            eligible=False,
            reason=ManualRefreshEligibilityReason.SYNC_STATE_IDENTITY_MISMATCH,
            definition=definition,
            state=state,
            at=at,
            intent=intent,
            refresh_interval=interval,
        )

    # ADR-029 D.1 explicitly says a version mismatch does not itself trigger a
    # refresh. A future governed reconciliation contract must resolve it.
    if state.registry_contract_version != EXTERNAL_SERIES_REGISTRY_VERSION:
        return _eligibility(
            eligible=False,
            reason=ManualRefreshEligibilityReason.REGISTRY_VERSION_MISMATCH,
            definition=definition,
            state=state,
            at=at,
            intent=intent,
            refresh_interval=interval,
        )

    persisted_instants = tuple(
        value
        for value in (state.last_attempt_at, state.last_success_at)
        if value is not None
    )
    if persisted_instants and at < max(persisted_instants):
        return _eligibility(
            eligible=False,
            reason=ManualRefreshEligibilityReason.CLOCK_REGRESSION,
            definition=definition,
            state=state,
            at=at,
            intent=intent,
            refresh_interval=interval,
        )

    if not is_refresh_due(state=state, at=at):
        return _eligibility(
            eligible=False,
            reason=ManualRefreshEligibilityReason.COOLDOWN_ACTIVE,
            definition=definition,
            state=state,
            at=at,
            intent=intent,
            refresh_interval=interval,
        )

    reason = {
        SyncAttemptResult.PARTIAL: ManualRefreshEligibilityReason.RETRY_AFTER_PARTIAL,
        SyncAttemptResult.FAILED: ManualRefreshEligibilityReason.RETRY_AFTER_FAILED,
    }.get(state.last_attempt_result)
    if reason is None:
        reason = (
            ManualRefreshEligibilityReason.COOLDOWN_ELAPSED
            if state.last_success_at is not None
            else ManualRefreshEligibilityReason.NO_SUCCESS_EVIDENCE
        )
    return _eligibility(
        eligible=True,
        reason=reason,
        definition=definition,
        state=state,
        at=at,
        intent=intent,
        refresh_interval=interval,
    )


class ManualExternalRefreshService:
    """Evaluate and synchronously invoke one explicit governed acquisition."""

    def __init__(
        self,
        *,
        ingestion: GovernedExternalIngestionService,
        sync_state_reader: Callable[[RegistryKey], ExternalSeriesSyncState | None],
        utc_clock: Callable[[], datetime],
    ) -> None:
        if not isinstance(ingestion, GovernedExternalIngestionService):
            raise TypeError("ingestion must be a GovernedExternalIngestionService.")
        if not callable(sync_state_reader):
            raise TypeError("sync_state_reader must be callable.")
        if not callable(utc_clock):
            raise TypeError("utc_clock must be callable.")
        self._ingestion = ingestion
        self._sync_state_reader = sync_state_reader
        self._utc_clock = utc_clock

    def refresh(self, request: ManualRefreshRequest) -> ManualRefreshResult:
        if not isinstance(request, ManualRefreshRequest):
            raise TypeError("request must be a ManualRefreshRequest.")
        definition = resolve_series_by_key(request.registry_key)
        evaluated_at = self._utc_clock()
        encode_utc_timestamp(evaluated_at, field="evaluated_at")

        # This is the only preflight store operation. The injected reader owns
        # a short-lived read boundary over R3-E1 get_sync_state() and must
        # return after releasing its read transaction, before provider I/O.
        state = self._sync_state_reader(request.registry_key)
        if state is not None and not isinstance(state, ExternalSeriesSyncState):
            raise TypeError("sync_state_reader returned an unsupported value.")
        eligibility = evaluate_manual_refresh_eligibility(
            definition=definition,
            state=state,
            at=evaluated_at,
            intent=request.intent,
        )
        logger.info(
            "external_context.manual_refresh.evaluated",
            extra={
                "correlation_id": request.acquisition_id,
                "registry_key": request.registry_key.value,
                "refresh_intent": request.intent.value,
                "eligibility": eligibility.reason.value,
                "eligible": eligibility.eligible,
            },
        )
        if not eligibility.eligible:
            return ManualRefreshResult(
                acquisition_id=request.acquisition_id,
                registry_key=request.registry_key,
                intent=request.intent,
                status=ManualRefreshStatus.NOT_ELIGIBLE,
                eligibility=eligibility,
            )

        governed_request = request.to_governed_request()
        try:
            ingestion = self._ingestion.ingest(governed_request)
        except GovernedIngestionError as exc:
            logger.warning(
                "external_context.manual_refresh.failed",
                extra={
                    "correlation_id": request.acquisition_id,
                    "registry_key": request.registry_key.value,
                    "refresh_intent": request.intent.value,
                    "error_stage": exc.stage.value,
                    "error_code": exc.code,
                },
            )
            raise

        result = ManualRefreshResult(
            acquisition_id=request.acquisition_id,
            registry_key=request.registry_key,
            intent=request.intent,
            status=ManualRefreshStatus(ingestion.global_result.value),
            eligibility=eligibility,
            ingestion=ingestion,
        )
        logger.info(
            "external_context.manual_refresh.completed",
            extra={
                "correlation_id": request.acquisition_id,
                "registry_key": request.registry_key.value,
                "refresh_intent": request.intent.value,
                "global_result": result.status.value,
                "chunk_count": len(ingestion.chunk_results),
            },
        )
        return result


def _eligibility(
    *,
    eligible: bool,
    reason: ManualRefreshEligibilityReason,
    definition: ExternalSeriesDefinition,
    state: ExternalSeriesSyncState | None,
    at: datetime,
    intent: AcquisitionIntent,
    refresh_interval: timedelta,
) -> ManualRefreshEligibility:
    return ManualRefreshEligibility(
        eligible=eligible,
        reason=reason,
        evaluated_at=at,
        registry_key=definition.registry_key,
        intent=intent,
        refresh_interval=refresh_interval,
        last_attempt_at=state.last_attempt_at if state is not None else None,
        last_success_at=state.last_success_at if state is not None else None,
        last_attempt_result=state.last_attempt_result if state is not None else None,
        next_eligible_at=(
            state.next_refresh_eligible_at if state is not None else None
        ),
    )
