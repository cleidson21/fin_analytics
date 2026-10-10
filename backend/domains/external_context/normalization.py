"""Strict, context-independent Decimal and civil-period normalization."""

from __future__ import annotations

import calendar
import re
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal

from .enums import Frequency, Provider, Scope, SemanticClass, Unit
from .errors import (
    DecimalNormalizationError,
    ExternalContextErrorCode,
    FingerprintPayloadError,
    ReferencePeriodError,
    RegistryValidationError,
)
from .models import (
    ExternalObservation,
    ExternalObservationProvenance,
    ExternalSeriesDefinition,
    NormalizedDecimal,
    NormalizedExternalContent,
    ReferencePeriod,
)
from .registry import resolve_series


MAX_INTEGRAL_DIGITS = 40
MAX_FRACTIONAL_DIGITS = 18
MAX_CANONICAL_CHARACTERS = 64
MAX_ORIGINAL_UTF8_BYTES = 128
ALLOWED_NORMALIZATION_SCALES = frozenset({2, 4, 6})

CONTENT_PAYLOAD_V1_KEYS = frozenset(
    {
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
)

_DECIMAL_INPUT_PATTERN = re.compile(
    r"(?P<sign>-)?(?P<integer>0|[1-9][0-9]*)(?:\.(?P<fraction>[0-9]+))?",
    flags=re.ASCII,
)
_ISO_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", flags=re.ASCII)


def _invalid_field_type(field: str, expected: str, received: object) -> FingerprintPayloadError:
    return FingerprintPayloadError(
        ExternalContextErrorCode.INVALID_FIELD_TYPE,
        f"{field} must be {expected}.",
        field=field,
        details={"received_type": type(received).__name__},
    )


def normalize_decimal_text(value_text: object, *, scale: object) -> NormalizedDecimal:
    """Normalize lexical decimal text without arithmetic or ambient-context rounding."""

    if type(scale) is not int or scale not in ALLOWED_NORMALIZATION_SCALES:
        raise DecimalNormalizationError(
            ExternalContextErrorCode.INVALID_SCALE,
            "scale must be one of the executable registry scales.",
            field="value_scale",
            details={"allowed": tuple(sorted(ALLOWED_NORMALIZATION_SCALES)), "received": scale},
        )
    if type(value_text) is not str:
        raise DecimalNormalizationError(
            ExternalContextErrorCode.INVALID_FIELD_TYPE,
            "value_text must be lexical text; floats and JSON numbers are forbidden.",
            field="value_text",
            details={"received_type": type(value_text).__name__},
        )
    try:
        original_size = len(value_text.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise DecimalNormalizationError(
            ExternalContextErrorCode.DECIMAL_LEXICAL_INVALID,
            "value_text must be valid UTF-8-compatible ASCII decimal text.",
            field="value_text",
        ) from exc
    if original_size > MAX_ORIGINAL_UTF8_BYTES:
        raise DecimalNormalizationError(
            ExternalContextErrorCode.DECIMAL_ORIGINAL_TOO_LARGE,
            "value_text exceeds 128 UTF-8 bytes.",
            field="value_text",
            details={"maximum_bytes": MAX_ORIGINAL_UTF8_BYTES, "received_bytes": original_size},
        )

    match = _DECIMAL_INPUT_PATTERN.fullmatch(value_text)
    if match is None:
        raise DecimalNormalizationError(
            ExternalContextErrorCode.DECIMAL_LEXICAL_INVALID,
            "value_text does not use the approved plain ASCII decimal grammar.",
            field="value_text",
        )

    integral = match.group("integer")
    fraction = match.group("fraction") or ""
    if len(integral) > MAX_INTEGRAL_DIGITS:
        raise DecimalNormalizationError(
            ExternalContextErrorCode.DECIMAL_INTEGRAL_DIGITS_EXCEEDED,
            "value_text exceeds 40 integral digits.",
            field="value_text",
            details={"maximum_digits": MAX_INTEGRAL_DIGITS, "received_digits": len(integral)},
        )
    if len(fraction) > MAX_FRACTIONAL_DIGITS:
        raise DecimalNormalizationError(
            ExternalContextErrorCode.DECIMAL_FRACTIONAL_DIGITS_EXCEEDED,
            "value_text exceeds 18 fractional digits.",
            field="value_text",
            details={
                "maximum_digits": MAX_FRACTIONAL_DIGITS,
                "received_digits": len(fraction),
            },
        )

    excess_fraction = fraction[scale:]
    if any(character != "0" for character in excess_fraction):
        raise DecimalNormalizationError(
            ExternalContextErrorCode.DECIMAL_SCALE_EXCEEDED,
            "value_text contains non-zero digits beyond the registry scale.",
            field="value_text",
            details={"scale": scale},
        )

    canonical_fraction = fraction[:scale].ljust(scale, "0")
    is_zero = integral == "0" and not any(character != "0" for character in fraction)
    sign = "" if is_zero else (match.group("sign") or "")
    canonical_text = f"{sign}{integral}.{canonical_fraction}"
    if len(canonical_text) > MAX_CANONICAL_CHARACTERS:
        raise DecimalNormalizationError(
            ExternalContextErrorCode.DECIMAL_CANONICAL_TOO_LARGE,
            "Canonical decimal text exceeds 64 ASCII characters.",
            field="value_text",
            details={
                "maximum_characters": MAX_CANONICAL_CHARACTERS,
                "received_characters": len(canonical_text),
            },
        )

    return NormalizedDecimal(
        value=Decimal(canonical_text),
        canonical_text=canonical_text,
        scale=scale,
        original_text=value_text,
    )


def parse_civil_date(value: object, *, field_name: str) -> date:
    if type(value) is not str or _ISO_DATE_PATTERN.fullmatch(value) is None:
        raise ReferencePeriodError(
            ExternalContextErrorCode.INVALID_DATE,
            f"{field_name} must use strict YYYY-MM-DD civil-date text.",
            field=field_name,
        )
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ReferencePeriodError(
            ExternalContextErrorCode.INVALID_DATE,
            f"{field_name} is not an existing civil date.",
            field=field_name,
        ) from exc
    if parsed.isoformat() != value:
        raise ReferencePeriodError(
            ExternalContextErrorCode.INVALID_DATE,
            f"{field_name} must use canonical YYYY-MM-DD text.",
            field=field_name,
        )
    return parsed


def normalize_reference_period(
    *,
    definition: ExternalSeriesDefinition,
    reference_period_start: object,
    reference_period_end: object,
) -> ReferencePeriod:
    start = parse_civil_date(
        reference_period_start,
        field_name="reference_period_start",
    )
    end = parse_civil_date(
        reference_period_end,
        field_name="reference_period_end",
    )
    if end < start:
        raise ReferencePeriodError(
            ExternalContextErrorCode.PERIOD_INVERTED,
            "reference_period_end cannot precede reference_period_start.",
            field="reference_period_end",
        )

    if definition.frequency is Frequency.DAILY:
        if start != end:
            raise ReferencePeriodError(
                ExternalContextErrorCode.PERIOD_FREQUENCY_MISMATCH,
                "A DAILY series requires equal period start and end dates.",
                field="reference_period_end",
            )
    elif definition.frequency is Frequency.MONTHLY:
        expected_end = date(
            start.year,
            start.month,
            calendar.monthrange(start.year, start.month)[1],
        )
        if start.day != 1 or end != expected_end:
            raise ReferencePeriodError(
                ExternalContextErrorCode.PERIOD_FREQUENCY_MISMATCH,
                "A MONTHLY series requires the first and last civil day of one month.",
                field="reference_period_end",
                details={
                    "expected_start": date(start.year, start.month, 1).isoformat(),
                    "expected_end": expected_end.isoformat(),
                },
            )
    else:  # The executable registry is closed; fail if a definition is corrupted.
        raise ReferencePeriodError(
            ExternalContextErrorCode.PERIOD_FREQUENCY_MISMATCH,
            "The series frequency is not executable in R3-C.",
            field="frequency",
        )

    if start < definition.earliest_normalized_date:
        raise ReferencePeriodError(
            ExternalContextErrorCode.HISTORICAL_LIMIT_VIOLATION,
            "The reference period precedes the series normalized-history floor.",
            field="reference_period_start",
            details={
                "earliest_allowed": definition.earliest_normalized_date.isoformat(),
                "received": start.isoformat(),
                "series_id": definition.series_id,
            },
        )
    return ReferencePeriod(start=start, end=end)


def _validate_payload_shape(payload: object) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise FingerprintPayloadError(
            ExternalContextErrorCode.PAYLOAD_SHAPE_INVALID,
            "Content payload must be a mapping with exactly eleven fields.",
        )
    payload_keys = set(payload.keys())
    missing = CONTENT_PAYLOAD_V1_KEYS - payload_keys
    extra = payload_keys - CONTENT_PAYLOAD_V1_KEYS
    if missing or extra:
        raise FingerprintPayloadError(
            ExternalContextErrorCode.PAYLOAD_SHAPE_INVALID,
            "Content payload must contain exactly the eleven V1 fields.",
            details={
                "missing": tuple(sorted(str(key) for key in missing)),
                "extra": tuple(sorted(str(key) for key in extra)),
            },
        )
    return payload


def _require_string_field(payload: Mapping[str, object], field_name: str) -> str:
    value = payload[field_name]
    if type(value) is not str:
        raise _invalid_field_type(field_name, "a string", value)
    return value


def _require_registry_value(
    *,
    field_name: str,
    received: object,
    expected: object,
) -> None:
    if received != expected:
        raise RegistryValidationError(
            ExternalContextErrorCode.REGISTRY_MISMATCH,
            f"{field_name} is incompatible with the allowlisted series.",
            field=field_name,
            details={"expected": expected, "received": received},
        )


def validate_and_normalize_content(
    payload: object,
) -> NormalizedExternalContent:
    """Validate the closed V1 shape and normalize it against the registry."""

    values = _validate_payload_shape(payload)
    provider_text = _require_string_field(values, "provider")
    series_id = _require_string_field(values, "series_id")
    definition = resolve_series(provider_text, series_id)

    semantic_class = _require_string_field(values, "semantic_class")
    frequency = _require_string_field(values, "frequency")
    unit = _require_string_field(values, "unit")
    scope = _require_string_field(values, "scope")
    currency = values["currency"]
    if currency is not None and type(currency) is not str:
        raise _invalid_field_type("currency", "a string or null", currency)
    value_scale = values["value_scale"]
    if type(value_scale) is not int:
        raise _invalid_field_type("value_scale", "a strict integer", value_scale)

    _require_registry_value(
        field_name="semantic_class",
        received=semantic_class,
        expected=definition.semantic_class.value,
    )
    _require_registry_value(
        field_name="frequency",
        received=frequency,
        expected=definition.frequency.value,
    )
    _require_registry_value(
        field_name="unit",
        received=unit,
        expected=definition.unit.value,
    )
    _require_registry_value(
        field_name="currency",
        received=currency,
        expected=definition.currency,
    )
    _require_registry_value(
        field_name="scope",
        received=scope,
        expected=definition.scope.value,
    )
    _require_registry_value(
        field_name="value_scale",
        received=value_scale,
        expected=definition.normalization_scale,
    )

    period = normalize_reference_period(
        definition=definition,
        reference_period_start=_require_string_field(values, "reference_period_start"),
        reference_period_end=_require_string_field(values, "reference_period_end"),
    )
    normalized_decimal = normalize_decimal_text(
        values["value_text"],
        scale=definition.normalization_scale,
    )
    return NormalizedExternalContent(
        provider=Provider(provider_text),
        series_id=series_id,
        reference_period=period,
        semantic_class=SemanticClass(semantic_class),
        frequency=Frequency(frequency),
        value=normalized_decimal.value,
        value_text=normalized_decimal.canonical_text,
        value_scale=definition.normalization_scale,
        unit=Unit(unit),
        currency=currency,
        scope=Scope(scope),
    )


def normalize_external_observation(
    payload: object,
    *,
    retrieved_at: datetime,
    observed_at: datetime | None = None,
    published_at: datetime | None = None,
    provider_revision_id: str | None = None,
    revised_at: datetime | None = None,
) -> ExternalObservation:
    """Build an immutable observation without clocks, network, or persistence fields."""

    content = validate_and_normalize_content(payload)
    definition = resolve_series(content.provider, content.series_id)
    values = _validate_payload_shape(payload)
    provenance = ExternalObservationProvenance(
        provider_value_text=values["value_text"],
        provider_decimal_places=definition.provider_decimal_places,
        source_url=definition.provenance.source_url,
        license_id=definition.provenance.license_id,
        retrieved_at=retrieved_at,
        observed_at=observed_at,
        published_at=published_at,
        provider_revision_id=provider_revision_id,
        revised_at=revised_at,
    )
    return ExternalObservation(
        registry_key=definition.registry_key,
        series_concept=definition.official_concept,
        content=content,
        provenance=provenance,
    )
