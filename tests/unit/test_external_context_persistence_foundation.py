from datetime import date, datetime, timedelta, timezone

import pytest

from backend.domains.external_context import (
    EXTERNAL_SERIES_REGISTRY_VERSION,
    AcquisitionHealth,
    Availability,
    EconomicFreshness,
    ExternalContextReasonCode,
    ExternalSeriesSyncState,
    FreshnessEvidence,
    Frequency,
    SyncAttemptResult,
    UTCCodecError,
    decode_utc_timestamp,
    encode_utc_timestamp,
    evaluate_external_series_state,
    is_refresh_due,
    operational_refresh_interval,
)


def test_registry_contract_version_is_strict_positive_v1_and_independent() -> None:
    from backend.domains.external_context import CONTENT_FINGERPRINT_VERSION

    assert EXTERNAL_SERIES_REGISTRY_VERSION == 1
    assert type(EXTERNAL_SERIES_REGISTRY_VERSION) is int
    assert EXTERNAL_SERIES_REGISTRY_VERSION > 0
    assert CONTENT_FINGERPRINT_VERSION == 1
    assert "registry_contract_version" not in {
        "provider",
        "series_id",
        "reference_period_start",
        "reference_period_end",
        "semantic_class",
        "frequency",
        "value_text",
        "value_scale",
        "unit",
        "currency",
        "scope",
    }


@pytest.mark.parametrize(
    "value",
    [
        datetime(1, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 10, 10, 14, 5, 7, 123, tzinfo=timezone.utc),
        datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc),
    ],
)
def test_utc_codec_exact_roundtrip(value: datetime) -> None:
    encoded = encode_utc_timestamp(value)
    assert len(encoded) == 27
    assert encoded.isascii()
    assert encoded.endswith("Z")
    assert decode_utc_timestamp(encoded) == value
    assert encode_utc_timestamp(decode_utc_timestamp(encoded)) == encoded


@pytest.mark.parametrize(
    "value",
    [
        datetime(2026, 1, 1),
        datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=-3))),
        "2026-01-01T00:00:00.000000Z",
        1,
        True,
    ],
)
def test_utc_encoder_rejects_non_canonical_inputs(value: object) -> None:
    with pytest.raises(UTCCodecError):
        encode_utc_timestamp(value)


@pytest.mark.parametrize(
    "value",
    [
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:00:00.00000Z",
        "2026-01-01T00:00:00.000000+00:00",
        "2026-02-30T00:00:00.000000Z",
        "2026-01-01t00:00:00.000000Z",
        1,
    ],
)
def test_utc_decoder_rejects_invalid_or_noncanonical_text(value: object) -> None:
    with pytest.raises(UTCCodecError):
        decode_utc_timestamp(value)


def _never_acquired_state(*, version: int = 1) -> ExternalSeriesSyncState:
    return ExternalSeriesSyncState(
        registry_key="BCB_SGS_SELIC_TARGET",
        provider="BCB_SGS",
        series_id="432",
        registry_contract_version=version,
    )


def test_never_acquired_state_has_no_manufactured_success_or_freshness() -> None:
    state = _never_acquired_state()
    result = evaluate_external_series_state(
        state=state,
        has_eligible_observation=False,
        requested_start=date(2026, 1, 1),
        requested_end=date(2026, 1, 1),
        current_registry_version=1,
    )
    assert state.last_attempt_at is None
    assert state.last_success_at is None
    assert state.coverage_start is None
    assert result.availability is Availability.UNAVAILABLE
    assert result.economic_freshness is EconomicFreshness.UNKNOWN
    assert result.acquisition_health is AcquisitionHealth.UNKNOWN
    assert result.reason_code is ExternalContextReasonCode.NEVER_ACQUIRED


def test_registry_mismatch_does_not_override_lkg_availability() -> None:
    instant = datetime(2026, 10, 10, tzinfo=timezone.utc)
    state = ExternalSeriesSyncState(
        registry_key="BCB_SGS_SELIC_TARGET",
        provider="BCB_SGS",
        series_id="432",
        registry_contract_version=2,
        last_attempt_at=instant,
        last_success_at=instant,
        coverage_start=date(2026, 1, 1),
        coverage_end=date(2026, 12, 31),
        last_attempt_result=SyncAttemptResult.SUCCESS,
        last_valid_observation_event_id="event",
    )
    result = evaluate_external_series_state(
        state=state,
        has_eligible_observation=True,
        requested_start=date(2026, 2, 1),
        requested_end=date(2026, 2, 1),
        freshness_evidence=FreshnessEvidence.CURRENT,
        current_registry_version=1,
    )
    assert result.availability is Availability.AVAILABLE
    assert result.economic_freshness is EconomicFreshness.UNKNOWN
    assert result.acquisition_health is AcquisitionHealth.UNKNOWN
    assert result.reason_code is ExternalContextReasonCode.REGISTRY_VERSION_MISMATCH


def test_refresh_policy_is_operational_and_explicit() -> None:
    now = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)
    state = ExternalSeriesSyncState(
        registry_key="BCB_SGS_CDI",
        provider="BCB_SGS",
        series_id="12",
        registry_contract_version=1,
        next_refresh_eligible_at=now + timedelta(hours=6),
    )
    assert operational_refresh_interval(Frequency.DAILY) == timedelta(hours=6)
    assert operational_refresh_interval(Frequency.MONTHLY) == timedelta(hours=24)
    assert not is_refresh_due(state=state, at=now)
    assert is_refresh_due(state=state, at=now + timedelta(hours=6))


@pytest.mark.parametrize(
    ("attempt", "expected_health"),
    [
        (SyncAttemptResult.SUCCESS, AcquisitionHealth.HEALTHY),
        (SyncAttemptResult.EMPTY, AcquisitionHealth.HEALTHY),
        (SyncAttemptResult.PARTIAL, AcquisitionHealth.DEGRADED),
        (SyncAttemptResult.FAILED, AcquisitionHealth.FAILED),
    ],
)
def test_acquisition_health_is_independent_from_lkg_availability(attempt, expected_health) -> None:
    instant = datetime(2026, 10, 10, tzinfo=timezone.utc)
    state = ExternalSeriesSyncState(
        registry_key="BCB_SGS_SELIC_TARGET",
        provider="BCB_SGS",
        series_id="432",
        registry_contract_version=1,
        last_attempt_at=instant,
        last_success_at=instant if attempt in {SyncAttemptResult.SUCCESS, SyncAttemptResult.EMPTY} else None,
        coverage_start=date(2026, 1, 1),
        coverage_end=date(2026, 12, 31),
        last_attempt_result=attempt,
        partial_coverage=attempt is SyncAttemptResult.PARTIAL,
        last_valid_observation_event_id="event",
    )
    result = evaluate_external_series_state(
        state=state,
        has_eligible_observation=True,
        requested_start=date(2026, 2, 1),
        requested_end=date(2026, 2, 1),
        freshness_evidence=FreshnessEvidence.INSUFFICIENT,
        current_registry_version=1,
    )
    assert result.availability is Availability.AVAILABLE
    assert result.acquisition_health is expected_health
    assert result.economic_freshness is EconomicFreshness.UNKNOWN


def test_freshness_requires_explicit_evidence_and_is_not_refresh_age() -> None:
    instant = datetime(2026, 10, 10, tzinfo=timezone.utc)
    state = ExternalSeriesSyncState(
        registry_key="BCB_SGS_IPCA_MONTHLY",
        provider="BCB_SGS",
        series_id="433",
        registry_contract_version=1,
        last_attempt_at=instant,
        last_success_at=instant,
        next_refresh_eligible_at=instant - timedelta(days=30),
        coverage_start=date(2026, 1, 1),
        coverage_end=date(2026, 9, 30),
        last_attempt_result=SyncAttemptResult.SUCCESS,
        last_valid_observation_event_id="event",
    )
    unknown = evaluate_external_series_state(
        state=state,
        has_eligible_observation=True,
        requested_start=date(2026, 9, 1),
        requested_end=date(2026, 9, 30),
        current_registry_version=1,
    )
    current = evaluate_external_series_state(
        state=state,
        has_eligible_observation=True,
        requested_start=date(2026, 9, 1),
        requested_end=date(2026, 9, 30),
        freshness_evidence=FreshnessEvidence.CURRENT,
        current_registry_version=1,
    )
    stale = evaluate_external_series_state(
        state=state,
        has_eligible_observation=True,
        requested_start=date(2026, 9, 1),
        requested_end=date(2026, 9, 30),
        freshness_evidence=FreshnessEvidence.STALE,
        current_registry_version=1,
    )
    assert is_refresh_due(state=state, at=instant)
    assert unknown.economic_freshness is EconomicFreshness.UNKNOWN
    assert current.economic_freshness is EconomicFreshness.CURRENT
    assert stale.economic_freshness is EconomicFreshness.STALE


def test_requested_interval_outside_certified_coverage_is_partial() -> None:
    instant = datetime(2026, 10, 10, tzinfo=timezone.utc)
    state = ExternalSeriesSyncState(
        registry_key="BCB_SGS_SELIC_TARGET",
        provider="BCB_SGS",
        series_id="432",
        registry_contract_version=1,
        last_attempt_at=instant,
        last_success_at=instant,
        coverage_start=date(2026, 6, 1),
        coverage_end=date(2026, 6, 30),
        last_attempt_result=SyncAttemptResult.SUCCESS,
        last_valid_observation_event_id="event",
    )
    result = evaluate_external_series_state(
        state=state,
        has_eligible_observation=True,
        requested_start=date(2026, 5, 1),
        requested_end=date(2026, 6, 30),
        current_registry_version=1,
    )
    assert result.availability is Availability.PARTIAL
    assert result.reason_code is ExternalContextReasonCode.PARTIAL_COVERAGE
