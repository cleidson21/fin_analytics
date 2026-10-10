import json
import re
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from backend.domains.external_context import (
    CONTENT_FINGERPRINT_VERSION,
    CONTENT_PAYLOAD_V1_KEYS,
    DOMAIN_PREFIX_V1,
    DecimalNormalizationError,
    ExternalContextErrorCode,
    FingerprintPayloadError,
    RegistryKey,
    UnknownSeriesError,
    build_content_fingerprint_v1,
    canonical_json_v1,
    normalize_external_observation,
)


SELIC_CANONICAL_JSON = (
    '{"currency":null,"frequency":"DAILY","provider":"BCB_SGS",'
    '"reference_period_end":"2026-10-09",'
    '"reference_period_start":"2026-10-09","scope":"BR",'
    '"semantic_class":"EXTERNAL_OBSERVATION","series_id":"432",'
    '"unit":"PERCENT_PER_YEAR","value_scale":2,"value_text":"10.50"}'
)
IPCA_CANONICAL_JSON = (
    '{"currency":null,"frequency":"MONTHLY","provider":"BCB_SGS",'
    '"reference_period_end":"2026-09-30",'
    '"reference_period_start":"2026-09-01","scope":"BR",'
    '"semantic_class":"EXTERNAL_OBSERVATION","series_id":"433",'
    '"unit":"PERCENT_MONTHLY_CHANGE","value_scale":2,"value_text":"-0.40"}'
)
USD_CANONICAL_JSON = (
    '{"currency":"BRL/USD","frequency":"DAILY","provider":"BCB_SGS",'
    '"reference_period_end":"2026-10-09",'
    '"reference_period_start":"2026-10-09","scope":"BR",'
    '"semantic_class":"EXTERNAL_OBSERVATION","series_id":"1",'
    '"unit":"BRL_PER_USD","value_scale":4,"value_text":"5.4321"}'
)


def _selic_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "provider": "BCB_SGS",
        "series_id": "432",
        "reference_period_start": "2026-10-09",
        "reference_period_end": "2026-10-09",
        "semantic_class": "EXTERNAL_OBSERVATION",
        "frequency": "DAILY",
        "value_text": "10.50",
        "value_scale": 2,
        "unit": "PERCENT_PER_YEAR",
        "currency": None,
        "scope": "BR",
    }
    payload.update(overrides)
    return payload


NORMATIVE_VECTORS = (
    (
        _selic_payload(),
        SELIC_CANONICAL_JSON,
        "sha256:c6b9708c32eb552fa60322d16b793adc48d8b03b7757e975952a526d536e9022",
    ),
    (
        {
            "provider": "BCB_SGS",
            "series_id": "433",
            "reference_period_start": "2026-09-01",
            "reference_period_end": "2026-09-30",
            "semantic_class": "EXTERNAL_OBSERVATION",
            "frequency": "MONTHLY",
            "value_text": "-0.40",
            "value_scale": 2,
            "unit": "PERCENT_MONTHLY_CHANGE",
            "currency": None,
            "scope": "BR",
        },
        IPCA_CANONICAL_JSON,
        "sha256:4105c9c3f1139a0676688d53b21973a1905345e328347a5abed43a77a333a351",
    ),
    (
        {
            "provider": "BCB_SGS",
            "series_id": "1",
            "reference_period_start": "2026-10-09",
            "reference_period_end": "2026-10-09",
            "semantic_class": "EXTERNAL_OBSERVATION",
            "frequency": "DAILY",
            "value_text": "5.4321",
            "value_scale": 4,
            "unit": "BRL_PER_USD",
            "currency": "BRL/USD",
            "scope": "BR",
        },
        USD_CANONICAL_JSON,
        "sha256:71f700aeb716ea7396a2ab595ff12470858095115595fd146975852dd5f0c83d",
    ),
)


@pytest.mark.parametrize(("payload", "expected_json", "expected_hash"), NORMATIVE_VECTORS)
def test_normative_vectors_use_production_domain_code(
    payload: dict[str, object],
    expected_json: str,
    expected_hash: str,
) -> None:
    result = build_content_fingerprint_v1(payload)
    assert result.content_fingerprint_version == 1
    assert result.canonical_json == expected_json
    assert result.content_fingerprint == expected_hash


def test_prefix_is_the_exact_normative_nul_terminated_byte_sequence() -> None:
    assert CONTENT_FINGERPRINT_VERSION == 1
    assert len(DOMAIN_PREFIX_V1) == 53
    assert DOMAIN_PREFIX_V1.endswith(b"\x00")
    assert DOMAIN_PREFIX_V1.hex() == (
        "46494e414e414c59544943532f45585445524e414c5f434f4e544558542f"
        "434f4e54454e545f46494e4745525052494e542f563100"
    )


def test_dictionary_insertion_order_does_not_change_json_or_fingerprint() -> None:
    payload = _selic_payload()
    reversed_payload = dict(reversed(tuple(payload.items())))

    regular = build_content_fingerprint_v1(payload)
    reversed_result = build_content_fingerprint_v1(reversed_payload)

    assert regular.canonical_json == reversed_result.canonical_json == SELIC_CANONICAL_JSON
    assert regular.content_fingerprint == reversed_result.content_fingerprint


def test_lexically_equivalent_decimals_share_the_same_fingerprint() -> None:
    short = build_content_fingerprint_v1(_selic_payload(value_text="10.5"))
    fixed = build_content_fingerprint_v1(_selic_payload(value_text="10.50"))
    assert short.content_fingerprint == fixed.content_fingerprint
    assert short.normalized_content.value_text == "10.50"
    assert short.normalized_content.value == Decimal("10.50")


def test_negative_and_positive_zero_share_the_same_fingerprint() -> None:
    negative = build_content_fingerprint_v1(_selic_payload(value_text="-0.00"))
    positive = build_content_fingerprint_v1(_selic_payload(value_text="0.00"))
    assert negative.content_fingerprint == positive.content_fingerprint
    assert negative.normalized_content.value_text == "0.00"


def test_valid_value_and_period_changes_produce_different_fingerprints() -> None:
    baseline = build_content_fingerprint_v1(_selic_payload())
    changed_value = build_content_fingerprint_v1(_selic_payload(value_text="10.51"))
    changed_period = build_content_fingerprint_v1(
        _selic_payload(
            reference_period_start="2026-10-08",
            reference_period_end="2026-10-08",
        )
    )
    assert baseline.content_fingerprint != changed_value.content_fingerprint
    assert baseline.content_fingerprint != changed_period.content_fingerprint


def test_sgs_11_complementary_vector_uses_coherent_registry_metadata() -> None:
    payload = {
        "provider": "BCB_SGS",
        "series_id": "11",
        "reference_period_start": "2026-10-09",
        "reference_period_end": "2026-10-09",
        "semantic_class": "EXTERNAL_OBSERVATION",
        "frequency": "DAILY",
        "value_text": "0.052788",
        "value_scale": 6,
        "unit": "PERCENT_PER_DAY",
        "currency": None,
        "scope": "BR",
    }
    result = build_content_fingerprint_v1(payload)
    assert result.normalized_content.value == Decimal("0.052788")
    assert result.normalized_content.value_text == "0.052788"
    assert result.content_fingerprint not in {
        expected_hash for _, _, expected_hash in NORMATIVE_VECTORS
    }


def test_same_content_is_reproducible_and_uses_lowercase_sha256_form() -> None:
    first = build_content_fingerprint_v1(_selic_payload())
    second = build_content_fingerprint_v1(_selic_payload())
    assert first.content_fingerprint == second.content_fingerprint
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", first.content_fingerprint)
    assert first.as_pair() == (1, first.content_fingerprint)
    with pytest.raises(FrozenInstanceError):
        first.content_fingerprint_version = 2


def test_canonical_json_has_exact_closed_representation() -> None:
    canonical = canonical_json_v1(_selic_payload())
    decoded = json.loads(canonical)

    assert canonical == SELIC_CANONICAL_JSON
    assert set(decoded) == CONTENT_PAYLOAD_V1_KEYS
    assert decoded["currency"] is None
    assert type(decoded["value_scale"]) is int
    assert type(decoded["value_text"]) is str
    assert canonical.encode("utf-8").startswith(b"{")
    assert not canonical.startswith("\ufeff")
    assert not canonical.endswith("\n")
    assert ": " not in canonical
    assert ", " not in canonical


@pytest.mark.parametrize("missing", sorted(CONTENT_PAYLOAD_V1_KEYS))
def test_every_missing_required_field_is_rejected(missing: str) -> None:
    payload = _selic_payload()
    del payload[missing]
    with pytest.raises(FingerprintPayloadError) as failure:
        build_content_fingerprint_v1(payload)
    assert failure.value.code is ExternalContextErrorCode.PAYLOAD_SHAPE_INVALID
    assert missing in failure.value.details["missing"]


def test_additional_field_is_rejected_before_hashing() -> None:
    with pytest.raises(FingerprintPayloadError) as failure:
        build_content_fingerprint_v1(_selic_payload(retrieved_at="2026-10-09T12:00:00Z"))
    assert failure.value.code is ExternalContextErrorCode.PAYLOAD_SHAPE_INVALID
    assert failure.value.details["extra"] == ("retrieved_at",)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider", ["BCB_SGS"]),
        ("series_id", {"value": "432"}),
        ("reference_period_start", ["2026-10-09"]),
        ("semantic_class", {"value": "EXTERNAL_OBSERVATION"}),
        ("frequency", ["DAILY"]),
        ("unit", ["PERCENT_PER_YEAR"]),
        ("currency", [None]),
        ("scope", {"value": "BR"}),
    ],
)
def test_arrays_and_nested_objects_are_rejected(field: str, value: object) -> None:
    with pytest.raises(FingerprintPayloadError) as failure:
        build_content_fingerprint_v1(_selic_payload(**{field: value}))
    assert failure.value.code is ExternalContextErrorCode.INVALID_FIELD_TYPE
    assert failure.value.field == field


@pytest.mark.parametrize("value_scale", [True, False])
def test_boolean_is_never_accepted_as_value_scale(value_scale: bool) -> None:
    with pytest.raises(FingerprintPayloadError) as failure:
        build_content_fingerprint_v1(_selic_payload(value_scale=value_scale))
    assert failure.value.code is ExternalContextErrorCode.INVALID_FIELD_TYPE


@pytest.mark.parametrize("value", [10.5, 10, True, False])
def test_numeric_or_boolean_financial_values_are_rejected(value: object) -> None:
    with pytest.raises(DecimalNormalizationError) as failure:
        build_content_fingerprint_v1(_selic_payload(value_text=value))
    assert failure.value.code is ExternalContextErrorCode.INVALID_FIELD_TYPE


def test_unknown_series_has_no_valid_domain_fingerprint() -> None:
    with pytest.raises(UnknownSeriesError):
        build_content_fingerprint_v1(_selic_payload(series_id="999"))


def test_a_to_b_to_a_reuses_content_identity_without_creating_events() -> None:
    a1 = build_content_fingerprint_v1(_selic_payload(value_text="10.50"))
    b2 = build_content_fingerprint_v1(_selic_payload(value_text="10.75"))
    a3 = build_content_fingerprint_v1(_selic_payload(value_text="10.50"))
    assert a1.content_fingerprint == a3.content_fingerprint
    assert a1.content_fingerprint != b2.content_fingerprint


def test_economic_identity_is_stable_and_contains_only_the_five_adr_fields() -> None:
    result = build_content_fingerprint_v1(_selic_payload())
    identity = result.normalized_content.economic_identity
    assert identity.as_tuple() == (
        "BCB_SGS",
        "432",
        "2026-10-09",
        "2026-10-09",
        "EXTERNAL_OBSERVATION",
    )


def test_operational_timestamps_do_not_influence_content_fingerprint() -> None:
    payload = _selic_payload(value_text="10.5")
    early = normalize_external_observation(
        payload,
        retrieved_at=datetime(2026, 10, 9, 10, tzinfo=timezone.utc),
    )
    later = normalize_external_observation(
        payload,
        retrieved_at=datetime(2026, 10, 10, 18, tzinfo=timezone.utc),
        published_at=datetime(2026, 10, 9, 9, tzinfo=timezone.utc),
        provider_revision_id="synthetic-revision",
    )

    early_fingerprint = build_content_fingerprint_v1(early.content.as_payload_v1())
    later_fingerprint = build_content_fingerprint_v1(later.content.as_payload_v1())

    assert early.registry_key is RegistryKey.BCB_SGS_SELIC_TARGET
    assert early.economic_identity == later.economic_identity
    assert early_fingerprint.content_fingerprint == later_fingerprint.content_fingerprint
    assert not hasattr(early, "knowledge_sequence")
    assert not hasattr(early, "known_from")
    assert not hasattr(early, "supersedes_event_id")
