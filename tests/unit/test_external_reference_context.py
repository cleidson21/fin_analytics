from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.application.services.external_reference_context import (
    ExternalReferenceContextError,
    ExternalReferenceContextErrorCode,
    ExternalReferenceContextRequest,
    ExternalReferenceContextService,
)
from backend.application.services.external_observation_store import (
    ExternalObservationStoreService,
)
from backend.domains.external_context import (
    EXTERNAL_SERIES_REGISTRY_VERSION,
    AcquisitionHealth,
    Availability,
    EconomicFreshness,
    ExternalContextReasonCode,
    ExternalSeriesSyncState,
    PersistedObservationEvent,
    RegistryKey,
    SyncAttemptResult,
    UTCCodecError,
    build_content_fingerprint_v1,
    normalize_external_observation,
    resolve_series_by_key,
)
from backend.domains.external_context.purposes import (
    EXTERNAL_REFERENCE_PURPOSE_ALLOWLIST,
    ExternalReferencePurpose,
)
from backend.infrastructure.persistence.models.external_context import (
    ExternalObservationVersionModel,
    ExternalSeriesSyncStateModel,
)


UTC = timezone.utc
AS_OF_TIMESTAMP = datetime(2026, 10, 15, 12, tzinfo=UTC)


class _ReadOnlyStore:
    def __init__(
        self,
        *,
        event: PersistedObservationEvent | None = None,
        state: ExternalSeriesSyncState | None = None,
    ) -> None:
        self.event = event
        self.state = state
        self.latest_calls: list[dict[str, object]] = []
        self.sync_calls: list[RegistryKey] = []

    def get_latest_series_as_of(self, **kwargs):
        self.latest_calls.append(kwargs)
        return self.event

    def get_sync_state(self, registry_key):
        self.sync_calls.append(registry_key)
        return self.state


class _ForbiddenStore:
    def get_latest_series_as_of(self, **_kwargs):
        raise AssertionError("Store must not be called for forbidden access.")

    def get_sync_state(self, _registry_key):
        raise AssertionError("Store must not be called for forbidden access.")


def _request(
    *,
    purpose: ExternalReferencePurpose = ExternalReferencePurpose.MARKET_FX_REFERENCE,
    reference_key: RegistryKey = RegistryKey.BCB_SGS_USD_SELL,
    as_of_date: date = date(2026, 10, 11),
    as_of_timestamp: datetime = AS_OF_TIMESTAMP,
) -> ExternalReferenceContextRequest:
    return ExternalReferenceContextRequest(
        purpose=purpose,
        reference_key=reference_key,
        consumer_as_of_date=as_of_date,
        consumer_as_of_timestamp=as_of_timestamp,
    )


def _event(
    *,
    registry_key: RegistryKey = RegistryKey.BCB_SGS_USD_SELL,
    value_text: str = "5.4321",
    period_start: date = date(2026, 10, 9),
    period_end: date = date(2026, 10, 9),
    known_from: datetime = datetime(2026, 10, 10, 12, tzinfo=UTC),
    knowledge_sequence: int = 1,
    event_number: int = 1,
    supersedes_event_id: str | None = None,
) -> PersistedObservationEvent:
    definition = resolve_series_by_key(registry_key)
    observation = normalize_external_observation(
        {
            "provider": definition.provider.value,
            "series_id": definition.series_id,
            "reference_period_start": period_start.isoformat(),
            "reference_period_end": period_end.isoformat(),
            "semantic_class": definition.semantic_class.value,
            "frequency": definition.frequency.value,
            "value_text": value_text,
            "value_scale": definition.normalization_scale,
            "unit": definition.unit.value,
            "currency": definition.currency,
            "scope": definition.scope.value,
        },
        retrieved_at=known_from - timedelta(seconds=1),
    )
    fingerprint = build_content_fingerprint_v1(observation.content.as_payload_v1())
    return PersistedObservationEvent(
        observation_event_id=str(UUID(int=event_number)),
        observation=observation,
        registry_contract_version=EXTERNAL_SERIES_REGISTRY_VERSION,
        content_fingerprint_version=fingerprint.content_fingerprint_version,
        content_fingerprint=fingerprint.content_fingerprint,
        ingested_at=known_from,
        known_from=known_from,
        knowledge_sequence=knowledge_sequence,
        supersedes_event_id=supersedes_event_id,
    )


def _state(
    event: PersistedObservationEvent,
    *,
    registry_version: int = EXTERNAL_SERIES_REGISTRY_VERSION,
    result: SyncAttemptResult = SyncAttemptResult.SUCCESS,
    coverage_start: date | None = date(2026, 10, 1),
    coverage_end: date | None = date(2026, 10, 15),
    partial_coverage: bool = False,
) -> ExternalSeriesSyncState:
    definition = resolve_series_by_key(event.observation.registry_key)
    return ExternalSeriesSyncState(
        registry_key=definition.registry_key.value,
        provider=definition.provider.value,
        series_id=definition.series_id,
        registry_contract_version=registry_version,
        last_attempt_at=AS_OF_TIMESTAMP + timedelta(hours=1),
        last_success_at=AS_OF_TIMESTAMP + timedelta(hours=1),
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        last_attempt_result=result,
        partial_coverage=partial_coverage,
        last_valid_observation_event_id=event.observation_event_id,
    )


def test_purpose_enum_and_allowlist_are_exact_closed_and_immutable() -> None:
    assert {purpose.value for purpose in ExternalReferencePurpose} == {
        "MARKET_INTEREST_RATE_REFERENCE",
        "MARKET_INFLATION_REFERENCE",
        "MARKET_FX_REFERENCE",
    }
    assert EXTERNAL_REFERENCE_PURPOSE_ALLOWLIST == {
        ExternalReferencePurpose.MARKET_INTEREST_RATE_REFERENCE: frozenset(
            {
                RegistryKey.BCB_SGS_SELIC_TARGET,
                RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
                RegistryKey.BCB_SGS_CDI,
            }
        ),
        ExternalReferencePurpose.MARKET_INFLATION_REFERENCE: frozenset(
            {RegistryKey.BCB_SGS_IPCA_MONTHLY}
        ),
        ExternalReferencePurpose.MARKET_FX_REFERENCE: frozenset(
            {RegistryKey.BCB_SGS_USD_SELL}
        ),
    }
    with pytest.raises(TypeError):
        EXTERNAL_REFERENCE_PURPOSE_ALLOWLIST[
            ExternalReferencePurpose.MARKET_FX_REFERENCE
        ] = frozenset()
    with pytest.raises(AttributeError):
        EXTERNAL_REFERENCE_PURPOSE_ALLOWLIST[
            ExternalReferencePurpose.MARKET_FX_REFERENCE
        ].add(RegistryKey.BCB_SGS_CDI)


@pytest.mark.parametrize(
    ("purpose", "reference_key"),
    [
        (
            ExternalReferencePurpose.MARKET_INTEREST_RATE_REFERENCE,
            RegistryKey.BCB_SGS_SELIC_TARGET,
        ),
        (
            ExternalReferencePurpose.MARKET_INTEREST_RATE_REFERENCE,
            RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
        ),
        (
            ExternalReferencePurpose.MARKET_INTEREST_RATE_REFERENCE,
            RegistryKey.BCB_SGS_CDI,
        ),
        (
            ExternalReferencePurpose.MARKET_INFLATION_REFERENCE,
            RegistryKey.BCB_SGS_IPCA_MONTHLY,
        ),
        (
            ExternalReferencePurpose.MARKET_FX_REFERENCE,
            RegistryKey.BCB_SGS_USD_SELL,
        ),
    ],
)
def test_each_approved_pair_delegates_exact_two_cut_read(
    purpose: ExternalReferencePurpose,
    reference_key: RegistryKey,
) -> None:
    store = _ReadOnlyStore()
    request = _request(purpose=purpose, reference_key=reference_key)

    result = ExternalReferenceContextService(store).read_reference(request)

    definition = resolve_series_by_key(reference_key)
    assert store.latest_calls == [
        {
            "provider": definition.provider,
            "series_id": definition.series_id,
            "consumer_as_of_date": request.consumer_as_of_date,
            "consumer_as_of_timestamp": request.consumer_as_of_timestamp,
        }
    ]
    assert store.sync_calls == [reference_key]
    assert result.purpose is purpose
    assert result.reference_key is reference_key


def test_cross_purpose_access_fails_typed_before_any_store_call() -> None:
    request = _request(
        purpose=ExternalReferencePurpose.MARKET_INFLATION_REFERENCE,
        reference_key=RegistryKey.BCB_SGS_USD_SELL,
    )

    with pytest.raises(ExternalReferenceContextError) as failure:
        ExternalReferenceContextService(_ForbiddenStore()).read_reference(request)

    assert failure.value.code is ExternalReferenceContextErrorCode.PURPOSE_NOT_ALLOWED
    assert failure.value.details == {
        "purpose": "MARKET_INFLATION_REFERENCE",
        "reference_key": "BCB_SGS_USD_SELL",
    }


def test_invalid_purpose_and_registry_key_are_rejected() -> None:
    with pytest.raises(TypeError, match="ExternalReferencePurpose"):
        ExternalReferenceContextRequest(
            purpose="PLANNING",
            reference_key=RegistryKey.BCB_SGS_IPCA_MONTHLY,
            consumer_as_of_date=date(2026, 10, 15),
            consumer_as_of_timestamp=AS_OF_TIMESTAMP,
        )
    with pytest.raises(TypeError, match="RegistryKey"):
        ExternalReferenceContextRequest(
            purpose=ExternalReferencePurpose.MARKET_FX_REFERENCE,
            reference_key="1",
            consumer_as_of_date=date(2026, 10, 15),
            consumer_as_of_timestamp=AS_OF_TIMESTAMP,
        )


def test_request_requires_explicit_zero_offset_utc_and_normalizes_timezone() -> None:
    with pytest.raises(UTCCodecError):
        _request(as_of_timestamp=datetime(2026, 10, 15, 12))
    with pytest.raises(UTCCodecError):
        _request(
            as_of_timestamp=datetime(
                2026,
                10,
                15,
                9,
                tzinfo=timezone(timedelta(hours=-3)),
            )
        )

    zero_offset = timezone(timedelta(0), name="ZERO")
    request = _request(as_of_timestamp=datetime(2026, 10, 15, 12, tzinfo=zero_offset))
    assert request.consumer_as_of_timestamp.tzinfo is UTC


def test_history_and_provider_parameters_are_rejected_not_ignored() -> None:
    with pytest.raises(TypeError, match="history_window"):
        ExternalReferenceContextRequest(
            purpose=ExternalReferencePurpose.MARKET_FX_REFERENCE,
            reference_key=RegistryKey.BCB_SGS_USD_SELL,
            consumer_as_of_date=date(2026, 10, 15),
            consumer_as_of_timestamp=AS_OF_TIMESTAMP,
            history_window=30,
        )
    with pytest.raises(TypeError, match="provider_url"):
        ExternalReferenceContextRequest(
            purpose=ExternalReferencePurpose.MARKET_FX_REFERENCE,
            reference_key=RegistryKey.BCB_SGS_USD_SELL,
            consumer_as_of_date=date(2026, 10, 15),
            consumer_as_of_timestamp=AS_OF_TIMESTAMP,
            provider_url="https://example.invalid",
        )


def test_request_result_and_nested_envelopes_are_immutable() -> None:
    service = ExternalReferenceContextService(_ReadOnlyStore())
    request = _request()
    result = service.read_reference(request)

    with pytest.raises(FrozenInstanceError):
        request.reference_key = RegistryKey.BCB_SGS_CDI
    with pytest.raises(FrozenInstanceError):
        result.reference_key = RegistryKey.BCB_SGS_CDI
    with pytest.raises(FrozenInstanceError):
        result.reference_replay.reference = None
    with pytest.raises(FrozenInstanceError):
        result.operational_state_snapshot.state_observed_at = AS_OF_TIMESTAMP


def test_absence_is_explicit_and_never_numeric_zero() -> None:
    result = ExternalReferenceContextService(_ReadOnlyStore()).read_reference(_request())

    assert result.reference_replay.reference is None
    assert result.reference_replay.availability is Availability.UNAVAILABLE
    assert (
        result.reference_replay.reason_code
        is ExternalContextReasonCode.NO_ELIGIBLE_OBSERVATION
    )
    assert (
        result.operational_state_snapshot.economic_freshness
        is EconomicFreshness.UNKNOWN
    )
    assert (
        result.operational_state_snapshot.acquisition_health
        is AcquisitionHealth.UNKNOWN
    )
    assert (
        result.operational_state_snapshot.reason_code
        is ExternalContextReasonCode.NEVER_ACQUIRED
    )


def test_decimal_zero_and_full_provenance_are_preserved_without_float() -> None:
    event = _event(value_text="0.0000")
    result = ExternalReferenceContextService(_ReadOnlyStore(event=event)).read_reference(
        _request()
    )

    replayed = result.reference_replay.reference
    assert replayed is event
    assert replayed.observation.content.value == Decimal("0.0000")
    assert type(replayed.observation.content.value) is Decimal
    assert replayed.observation.content.value_text == "0.0000"
    assert replayed.observation.provenance == event.observation.provenance
    assert result.reference_replay.availability is Availability.AVAILABLE


def test_last_known_daily_observation_keeps_friday_period_on_sunday() -> None:
    friday = date(2026, 10, 9)
    event = _event(period_start=friday, period_end=friday)
    request = _request(as_of_date=date(2026, 10, 11))

    result = ExternalReferenceContextService(_ReadOnlyStore(event=event)).read_reference(
        request
    )

    period = result.reference_replay.reference.observation.content.reference_period
    assert period.start == friday
    assert period.end == friday
    assert result.consumer_as_of_date == date(2026, 10, 11)


def test_last_known_ipca_observation_keeps_original_month() -> None:
    event = _event(
        registry_key=RegistryKey.BCB_SGS_IPCA_MONTHLY,
        value_text="0.42",
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
    )
    request = _request(
        purpose=ExternalReferencePurpose.MARKET_INFLATION_REFERENCE,
        reference_key=RegistryKey.BCB_SGS_IPCA_MONTHLY,
        as_of_date=date(2026, 10, 15),
    )

    result = ExternalReferenceContextService(_ReadOnlyStore(event=event)).read_reference(
        request
    )

    period = result.reference_replay.reference.observation.content.reference_period
    assert period.start == date(2026, 9, 1)
    assert period.end == date(2026, 9, 30)


def test_store_selected_a_b_a_replay_and_sequence_are_preserved_verbatim() -> None:
    t1 = datetime(2026, 10, 10, 12, 0, 1, tzinfo=UTC)
    a1 = _event(known_from=t1, knowledge_sequence=1, event_number=1)
    b2 = _event(
        value_text="5.5000",
        known_from=t1 + timedelta(seconds=1),
        knowledge_sequence=2,
        event_number=2,
        supersedes_event_id=a1.observation_event_id,
    )
    a3 = _event(
        known_from=t1 + timedelta(seconds=2),
        knowledge_sequence=3,
        event_number=3,
        supersedes_event_id=b2.observation_event_id,
    )

    for selected in (a1, b2, a3):
        result = ExternalReferenceContextService(
            _ReadOnlyStore(event=selected)
        ).read_reference(_request(as_of_timestamp=selected.known_from))
        assert result.reference_replay.reference is selected
        assert result.reference_replay.reference.knowledge_sequence == (
            selected.knowledge_sequence
        )
    assert a1.content_fingerprint == a3.content_fingerprint
    assert a1.observation_event_id != a3.observation_event_id


def test_knowledge_cut_is_forwarded_and_future_revision_is_not_synthesized() -> None:
    cut = datetime(2026, 10, 10, 12, 0, 1, tzinfo=UTC)
    earlier = _event(known_from=cut, event_number=1)
    store = _ReadOnlyStore(event=earlier)

    result = ExternalReferenceContextService(store).read_reference(
        _request(as_of_timestamp=cut)
    )

    assert store.latest_calls[0]["consumer_as_of_timestamp"] == cut
    assert result.reference_replay.reference is earlier


def test_equal_timestamp_sequence_selected_by_store_is_preserved() -> None:
    instant = datetime(2026, 10, 10, 12, 0, 1, tzinfo=UTC)
    first = _event(known_from=instant, knowledge_sequence=1, event_number=1)
    selected = _event(
        value_text="5.5000",
        known_from=instant,
        knowledge_sequence=2,
        event_number=2,
        supersedes_event_id=first.observation_event_id,
    )

    result = ExternalReferenceContextService(
        _ReadOnlyStore(event=selected)
    ).read_reference(_request(as_of_timestamp=instant))

    assert result.reference_replay.reference is selected
    assert result.reference_replay.reference.knowledge_sequence == 2


def test_real_store_equal_time_a_b_a_selects_highest_knowledge_sequence() -> None:
    engine = create_engine("sqlite:///:memory:")
    ExternalObservationVersionModel.__table__.create(engine)
    ExternalSeriesSyncStateModel.__table__.create(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    instant = datetime(2026, 10, 10, 12, 0, 1, tzinfo=UTC)
    store = ExternalObservationStoreService(session, utc_clock=lambda: instant)
    try:
        first = store.ingest(_event(known_from=instant).observation).event
        second = store.ingest(
            _event(value_text="5.5000", known_from=instant).observation
        ).event
        reverted = store.ingest(_event(known_from=instant).observation).event

        result = ExternalReferenceContextService(store).read_reference(
            _request(as_of_timestamp=instant)
        )

        selected = result.reference_replay.reference
        assert [
            first.knowledge_sequence,
            second.knowledge_sequence,
            reverted.knowledge_sequence,
        ] == [1, 2, 3]
        assert selected.observation_event_id == reverted.observation_event_id
        assert selected.knowledge_sequence == 3
        assert selected.content_fingerprint == first.content_fingerprint
    finally:
        session.close()
        engine.dispose()


def test_current_sync_state_is_separate_and_never_claimed_as_historical() -> None:
    event = _event()
    current_state = _state(event)
    historical_cut = event.known_from

    result = ExternalReferenceContextService(
        _ReadOnlyStore(event=event, state=current_state)
    ).read_reference(_request(as_of_timestamp=historical_cut))

    assert current_state.last_attempt_at > historical_cut
    assert result.reference_replay.reference.known_from == historical_cut
    assert result.operational_state_snapshot.sync_state is current_state
    assert result.operational_state_snapshot.state_observed_at is None


def test_registry_mismatch_preserves_lkg_and_forces_unknown_operational_states() -> None:
    event = _event()
    mismatch = _state(
        event,
        registry_version=EXTERNAL_SERIES_REGISTRY_VERSION + 1,
    )

    result = ExternalReferenceContextService(
        _ReadOnlyStore(event=event, state=mismatch)
    ).read_reference(_request())

    assert result.reference_replay.reference is event
    assert result.reference_replay.availability is Availability.AVAILABLE
    snapshot = result.operational_state_snapshot
    assert snapshot.economic_freshness is EconomicFreshness.UNKNOWN
    assert snapshot.acquisition_health is AcquisitionHealth.UNKNOWN
    assert snapshot.reason_code is ExternalContextReasonCode.REGISTRY_VERSION_MISMATCH


def test_registry_mismatch_is_reported_even_without_attempt_result() -> None:
    event = _event()
    definition = resolve_series_by_key(event.observation.registry_key)
    mismatch = ExternalSeriesSyncState(
        registry_key=definition.registry_key.value,
        provider=definition.provider.value,
        series_id=definition.series_id,
        registry_contract_version=EXTERNAL_SERIES_REGISTRY_VERSION + 1,
    )

    result = ExternalReferenceContextService(
        _ReadOnlyStore(event=event, state=mismatch)
    ).read_reference(_request())

    assert result.reference_replay.reference is event
    assert (
        result.operational_state_snapshot.reason_code
        is ExternalContextReasonCode.REGISTRY_VERSION_MISMATCH
    )


def test_freshness_is_current_only_with_complete_positive_head_evidence() -> None:
    event = _event()
    positive = _state(event, result=SyncAttemptResult.EMPTY)

    result = ExternalReferenceContextService(
        _ReadOnlyStore(event=event, state=positive)
    ).read_reference(_request(as_of_date=date(2026, 10, 11)))

    snapshot = result.operational_state_snapshot
    assert snapshot.economic_freshness is EconomicFreshness.CURRENT
    assert snapshot.acquisition_health is AcquisitionHealth.HEALTHY
    assert snapshot.reason_code is None


@pytest.mark.parametrize(
    "state",
    [
        None,
        _state(_event(), coverage_start=None, coverage_end=None),
        _state(_event(), partial_coverage=True),
        _state(_event(), coverage_end=date(2026, 10, 10)),
    ],
)
def test_freshness_without_sufficient_evidence_is_unknown(
    state: ExternalSeriesSyncState | None,
) -> None:
    event = _event()
    result = ExternalReferenceContextService(
        _ReadOnlyStore(event=event, state=state)
    ).read_reference(_request(as_of_date=date(2026, 10, 11)))

    assert (
        result.operational_state_snapshot.economic_freshness
        is EconomicFreshness.UNKNOWN
    )


def test_failed_acquisition_does_not_remove_lkg_or_force_stale() -> None:
    event = _event()
    failed = _state(event, result=SyncAttemptResult.FAILED)

    result = ExternalReferenceContextService(
        _ReadOnlyStore(event=event, state=failed)
    ).read_reference(_request())

    assert result.reference_replay.reference is event
    assert result.reference_replay.availability is Availability.AVAILABLE
    assert (
        result.operational_state_snapshot.economic_freshness
        is EconomicFreshness.UNKNOWN
    )
    assert (
        result.operational_state_snapshot.acquisition_health
        is AcquisitionHealth.FAILED
    )
    assert (
        result.operational_state_snapshot.reason_code
        is ExternalContextReasonCode.ACQUISITION_FAILED
    )
