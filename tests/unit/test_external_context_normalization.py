from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal, localcontext

import pytest

from backend.domains.external_context import (
    DecimalNormalizationError,
    ExternalContextErrorCode,
    FingerprintPayloadError,
    Frequency,
    ReferencePeriodError,
    RegistryKey,
    RegistryValidationError,
    normalize_decimal_text,
    normalize_reference_period,
    resolve_series_by_key,
    validate_and_normalize_content,
)


def _payload(**overrides: object) -> dict[str, object]:
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


@pytest.mark.parametrize(
    ("lexical", "scale", "expected_text", "expected_value"),
    [
        ("10.5", 2, "10.50", Decimal("10.50")),
        ("10.50", 2, "10.50", Decimal("10.50")),
        ("10", 2, "10.00", Decimal("10.00")),
        ("-0.00", 2, "0.00", Decimal("0.00")),
        ("-0", 4, "0.0000", Decimal("0.0000")),
        ("0.052788", 6, "0.052788", Decimal("0.052788")),
        ("-0.40", 2, "-0.40", Decimal("-0.40")),
        ("1.230000", 2, "1.23", Decimal("1.23")),
    ],
)
def test_decimal_normalization_is_exact_and_never_rounds(
    lexical: str,
    scale: int,
    expected_text: str,
    expected_value: Decimal,
) -> None:
    normalized = normalize_decimal_text(lexical, scale=scale)
    assert normalized.canonical_text == expected_text
    assert normalized.value == expected_value
    assert normalized.original_text == lexical
    assert normalized.scale == scale


@pytest.mark.parametrize(
    "lexical",
    [
        "",
        " 10.50",
        "10.50 ",
        "+10.50",
        "01.00",
        ".50",
        "1.",
        "1e2",
        "1E2",
        "NaN",
        "Infinity",
        "-Infinity",
        "1,23",
        "1_000.00",
        "１２.３４",
        "١٢.٣٤",
    ],
)
def test_decimal_normalization_rejects_non_contract_lexical_forms(lexical: str) -> None:
    with pytest.raises(DecimalNormalizationError) as failure:
        normalize_decimal_text(lexical, scale=2)
    assert failure.value.code is ExternalContextErrorCode.DECIMAL_LEXICAL_INVALID


@pytest.mark.parametrize("value", [10.5, 10, True, False, Decimal("10.5"), None])
def test_decimal_normalization_rejects_non_text_inputs(value: object) -> None:
    with pytest.raises(DecimalNormalizationError) as failure:
        normalize_decimal_text(value, scale=2)
    assert failure.value.code is ExternalContextErrorCode.INVALID_FIELD_TYPE


def test_non_zero_digits_beyond_series_scale_are_rejected_without_rounding() -> None:
    with pytest.raises(DecimalNormalizationError) as failure:
        normalize_decimal_text("10.501", scale=2)
    assert failure.value.code is ExternalContextErrorCode.DECIMAL_SCALE_EXCEEDED


@pytest.mark.parametrize("scale", [True, False, 0, 1, 3, 5, 18, "2", None])
def test_only_executable_registry_scales_are_accepted(scale: object) -> None:
    with pytest.raises(DecimalNormalizationError) as failure:
        normalize_decimal_text("1.00", scale=scale)
    assert failure.value.code is ExternalContextErrorCode.INVALID_SCALE


def test_integral_digit_limit_accepts_40_and_rejects_41() -> None:
    accepted = "9" * 40 + ".00"
    assert normalize_decimal_text(accepted, scale=2).canonical_text == accepted

    with pytest.raises(DecimalNormalizationError) as failure:
        normalize_decimal_text("9" * 41 + ".00", scale=2)
    assert failure.value.code is ExternalContextErrorCode.DECIMAL_INTEGRAL_DIGITS_EXCEEDED


def test_fractional_digit_limit_accepts_18_and_rejects_19() -> None:
    accepted = "1.12" + "0" * 16
    assert normalize_decimal_text(accepted, scale=2).canonical_text == "1.12"

    with pytest.raises(DecimalNormalizationError) as failure:
        normalize_decimal_text("1." + "0" * 19, scale=2)
    assert failure.value.code is ExternalContextErrorCode.DECIMAL_FRACTIONAL_DIGITS_EXCEEDED


def test_original_lexical_byte_limit_is_checked_before_numeric_digit_limits() -> None:
    with pytest.raises(DecimalNormalizationError) as at_limit:
        normalize_decimal_text("9" * 128, scale=2)
    assert at_limit.value.code is ExternalContextErrorCode.DECIMAL_INTEGRAL_DIGITS_EXCEEDED

    with pytest.raises(DecimalNormalizationError) as above_limit:
        normalize_decimal_text("9" * 129, scale=2)
    assert above_limit.value.code is ExternalContextErrorCode.DECIMAL_ORIGINAL_TOO_LARGE


def test_largest_contract_number_stays_inside_canonical_64_character_envelope() -> None:
    lexical = "-" + "9" * 40 + "." + "9" * 6
    normalized = normalize_decimal_text(lexical, scale=6)
    assert normalized.canonical_text == lexical
    assert len(normalized.canonical_text) == 48
    assert len(normalized.canonical_text) <= 64


def test_first_lexical_shape_above_canonical_envelope_is_already_rejected() -> None:
    # With the largest executable scale (6), 57 integral digits would produce
    # 65 canonical characters. The stricter 40-digit bound rejects it first.
    with pytest.raises(DecimalNormalizationError) as failure:
        normalize_decimal_text("9" * 57 + "." + "0" * 6, scale=6)
    assert failure.value.code is ExternalContextErrorCode.DECIMAL_INTEGRAL_DIGITS_EXCEEDED


def test_decimal_global_context_does_not_change_valid_normalization() -> None:
    lexical = "1234567890123456789012345678901234567890.052788"
    with localcontext() as context:
        context.prec = 2
        normalized = normalize_decimal_text(lexical, scale=6)
    assert normalized.canonical_text == lexical
    assert normalized.value == Decimal(lexical)


def test_daily_period_requires_equal_existing_civil_dates() -> None:
    definition = resolve_series_by_key(RegistryKey.BCB_SGS_SELIC_TARGET)
    period = normalize_reference_period(
        definition=definition,
        reference_period_start="2024-02-29",
        reference_period_end="2024-02-29",
    )
    assert period.start == date(2024, 2, 29)
    assert period.end == date(2024, 2, 29)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2024-02-01", "2024-02-29"),
        ("2025-02-01", "2025-02-28"),
        ("2026-04-01", "2026-04-30"),
        ("2026-07-01", "2026-07-31"),
    ],
)
def test_monthly_period_accepts_complete_civil_months(start: str, end: str) -> None:
    definition = resolve_series_by_key(RegistryKey.BCB_SGS_IPCA_MONTHLY)
    period = normalize_reference_period(
        definition=definition,
        reference_period_start=start,
        reference_period_end=end,
    )
    assert period.start.isoformat() == start
    assert period.end.isoformat() == end


@pytest.mark.parametrize(
    ("start", "end", "expected_code"),
    [
        ("2023-02-29", "2023-02-29", ExternalContextErrorCode.INVALID_DATE),
        ("2026-13-01", "2026-13-01", ExternalContextErrorCode.INVALID_DATE),
        ("2026-2-01", "2026-02-28", ExternalContextErrorCode.INVALID_DATE),
        ("2026-10-10", "2026-10-09", ExternalContextErrorCode.PERIOD_INVERTED),
    ],
)
def test_invalid_civil_dates_and_inverted_periods_are_rejected(
    start: str,
    end: str,
    expected_code: ExternalContextErrorCode,
) -> None:
    definition = resolve_series_by_key(RegistryKey.BCB_SGS_SELIC_TARGET)
    with pytest.raises(ReferencePeriodError) as failure:
        normalize_reference_period(
            definition=definition,
            reference_period_start=start,
            reference_period_end=end,
        )
    assert failure.value.code is expected_code


def test_frequency_incompatible_periods_are_rejected() -> None:
    daily = resolve_series_by_key(RegistryKey.BCB_SGS_SELIC_TARGET)
    monthly = resolve_series_by_key(RegistryKey.BCB_SGS_IPCA_MONTHLY)

    with pytest.raises(ReferencePeriodError) as daily_failure:
        normalize_reference_period(
            definition=daily,
            reference_period_start="2026-10-01",
            reference_period_end="2026-10-31",
        )
    with pytest.raises(ReferencePeriodError) as monthly_failure:
        normalize_reference_period(
            definition=monthly,
            reference_period_start="2026-10-02",
            reference_period_end="2026-10-31",
        )

    assert daily_failure.value.code is ExternalContextErrorCode.PERIOD_FREQUENCY_MISMATCH
    assert monthly_failure.value.code is ExternalContextErrorCode.PERIOD_FREQUENCY_MISMATCH


def test_sgs_1_rejects_pre_real_reference_dates() -> None:
    definition = resolve_series_by_key(RegistryKey.BCB_SGS_USD_SELL)
    with pytest.raises(ReferencePeriodError) as failure:
        normalize_reference_period(
            definition=definition,
            reference_period_start="1994-06-30",
            reference_period_end="1994-06-30",
        )
    assert failure.value.code is ExternalContextErrorCode.HISTORICAL_LIMIT_VIOLATION

    floor = normalize_reference_period(
        definition=definition,
        reference_period_start="1994-07-01",
        reference_period_end="1994-07-01",
    )
    assert floor.start == date(1994, 7, 1)


def test_normalized_content_is_exact_and_immutable() -> None:
    content = validate_and_normalize_content(_payload(value_text="10.5"))
    assert content.value == Decimal("10.50")
    assert content.value_text == "10.50"
    assert content.frequency is Frequency.DAILY
    with pytest.raises(FrozenInstanceError):
        content.value_text = "10.51"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider", "OTHER"),
        ("unit", "PERCENT_PER_DAY"),
        ("frequency", "MONTHLY"),
        ("currency", "BRL/USD"),
        ("semantic_class", "EXTERNAL_EXPECTATION"),
        ("scope", "US"),
        ("value_scale", 6),
    ],
)
def test_registry_incompatible_metadata_is_rejected(field: str, value: object) -> None:
    with pytest.raises(RegistryValidationError) as failure:
        validate_and_normalize_content(_payload(**{field: value}))
    assert failure.value.code is ExternalContextErrorCode.REGISTRY_MISMATCH
    assert failure.value.field == field


@pytest.mark.parametrize("value_scale", [True, False, 2.0, "2", None])
def test_value_scale_requires_a_strict_integer(value_scale: object) -> None:
    with pytest.raises(FingerprintPayloadError) as failure:
        validate_and_normalize_content(_payload(value_scale=value_scale))
    assert failure.value.code is ExternalContextErrorCode.INVALID_FIELD_TYPE
    assert failure.value.field == "value_scale"
