"""Structured, provider-neutral errors for the External Context domain."""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Mapping

from backend.domain.exceptions.base import FINAnalyticsError


class ExternalContextErrorCode(str, Enum):
    UNKNOWN_SERIES = "UNKNOWN_SERIES"
    REGISTRY_MISMATCH = "REGISTRY_MISMATCH"
    INVALID_FIELD_TYPE = "INVALID_FIELD_TYPE"
    PAYLOAD_SHAPE_INVALID = "PAYLOAD_SHAPE_INVALID"
    DECIMAL_LEXICAL_INVALID = "DECIMAL_LEXICAL_INVALID"
    DECIMAL_ORIGINAL_TOO_LARGE = "DECIMAL_ORIGINAL_TOO_LARGE"
    DECIMAL_INTEGRAL_DIGITS_EXCEEDED = "DECIMAL_INTEGRAL_DIGITS_EXCEEDED"
    DECIMAL_FRACTIONAL_DIGITS_EXCEEDED = "DECIMAL_FRACTIONAL_DIGITS_EXCEEDED"
    DECIMAL_SCALE_EXCEEDED = "DECIMAL_SCALE_EXCEEDED"
    DECIMAL_CANONICAL_TOO_LARGE = "DECIMAL_CANONICAL_TOO_LARGE"
    INVALID_SCALE = "INVALID_SCALE"
    INVALID_DATE = "INVALID_DATE"
    PERIOD_INVERTED = "PERIOD_INVERTED"
    PERIOD_FREQUENCY_MISMATCH = "PERIOD_FREQUENCY_MISMATCH"
    HISTORICAL_LIMIT_VIOLATION = "HISTORICAL_LIMIT_VIOLATION"
    INVALID_PROVENANCE = "INVALID_PROVENANCE"


class ExternalContextDomainError(FINAnalyticsError):
    """Base error carrying a stable code and safe structured details."""

    def __init__(
        self,
        code: ExternalContextErrorCode,
        message: str,
        *,
        field: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.details = MappingProxyType(dict(details or {}))


class UnknownSeriesError(ExternalContextDomainError):
    def __init__(
        self,
        *,
        registry_key: object | None = None,
        series_id: object | None = None,
    ) -> None:
        details = {}
        if registry_key is not None:
            details["registry_key"] = registry_key
        if series_id is not None:
            details["series_id"] = series_id
        super().__init__(
            ExternalContextErrorCode.UNKNOWN_SERIES,
            "The external series is not present in the executable allowlist.",
            field="series_id" if series_id is not None else "registry_key",
            details=details,
        )


class RegistryValidationError(ExternalContextDomainError):
    pass


class DecimalNormalizationError(ExternalContextDomainError):
    pass


class ReferencePeriodError(ExternalContextDomainError):
    pass


class FingerprintPayloadError(ExternalContextDomainError):
    pass


class ProvenanceValidationError(ExternalContextDomainError):
    pass
