"""Immutable value objects for the R3-C External Context domain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from .enums import (
    Frequency,
    Provider,
    RegistryEligibility,
    RegistryKey,
    Scope,
    SemanticClass,
    SeriesUse,
    Unit,
)
from .errors import (
    ExternalContextErrorCode,
    ProvenanceValidationError,
)


@dataclass(frozen=True)
class StaticSeriesProvenance:
    source_name: str
    source_url: str
    license_id: str
    attribution: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("source_name", self.source_name),
            ("source_url", self.source_url),
            ("license_id", self.license_id),
            ("attribution", self.attribution),
        ):
            if type(value) is not str or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string.")


@dataclass(frozen=True)
class ExternalSeriesDefinition:
    registry_key: RegistryKey
    provider: Provider
    series_id: str
    official_concept: str
    frequency: Frequency
    unit: Unit
    scope: Scope
    semantic_class: SemanticClass
    currency: str | None
    provider_decimal_places: int
    normalization_scale: int
    historical_coverage_start: date
    normalized_mvp_floor: date | None
    eligibility: RegistryEligibility
    permitted_use: SeriesUse
    provenance: StaticSeriesProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.registry_key, RegistryKey):
            raise TypeError("registry_key must be RegistryKey.")
        if self.provider is not Provider.BCB_SGS:
            raise ValueError("R3-C permits only the BCB_SGS provider.")
        if (
            type(self.series_id) is not str
            or not self.series_id.isascii()
            or not self.series_id.isdigit()
        ):
            raise ValueError("series_id must be a textual ASCII SGS identifier.")
        if type(self.official_concept) is not str or not self.official_concept.strip():
            raise ValueError("official_concept is required.")
        if not isinstance(self.frequency, Frequency):
            raise TypeError("frequency must be Frequency.")
        if not isinstance(self.unit, Unit):
            raise TypeError("unit must be Unit.")
        if self.scope is not Scope.BR:
            raise ValueError("The locked MVP scope must be BR.")
        if self.semantic_class is not SemanticClass.EXTERNAL_OBSERVATION:
            raise ValueError("The executable SGS registry contains observations only.")
        if self.currency is not None and self.currency != "BRL/USD":
            raise ValueError("The locked MVP currency is null or BRL/USD.")
        for field_name, value in (
            ("provider_decimal_places", self.provider_decimal_places),
            ("normalization_scale", self.normalization_scale),
        ):
            if type(value) is not int or value < 0 or value > 18:
                raise ValueError(f"{field_name} must be a strict integer from 0 to 18.")
        if self.provider_decimal_places != self.normalization_scale:
            raise ValueError("Provider precision and the locked normalization scale differ.")
        if type(self.historical_coverage_start) is not date:
            raise TypeError("historical_coverage_start must be a civil date.")
        if self.normalized_mvp_floor is not None:
            if type(self.normalized_mvp_floor) is not date:
                raise TypeError("normalized_mvp_floor must be a civil date or None.")
            if self.normalized_mvp_floor < self.historical_coverage_start:
                raise ValueError("normalized_mvp_floor cannot precede official coverage.")
        if not isinstance(self.eligibility, RegistryEligibility):
            raise TypeError("eligibility must be RegistryEligibility.")
        if not isinstance(self.permitted_use, SeriesUse):
            raise TypeError("permitted_use must be SeriesUse.")

    @property
    def earliest_normalized_date(self) -> date:
        return self.normalized_mvp_floor or self.historical_coverage_start


@dataclass(frozen=True)
class NormalizedDecimal:
    value: Decimal
    canonical_text: str
    scale: int
    original_text: str

    def __post_init__(self) -> None:
        if type(self.value) is not Decimal or not self.value.is_finite():
            raise TypeError("value must be a finite Decimal.")
        if type(self.canonical_text) is not str or type(self.original_text) is not str:
            raise TypeError("Decimal representations must be strings.")
        if type(self.scale) is not int or self.scale < 0:
            raise TypeError("scale must be a non-negative strict integer.")
        if Decimal(self.canonical_text) != self.value:
            raise ValueError("canonical_text and value must represent the same number.")


@dataclass(frozen=True)
class ReferencePeriod:
    start: date
    end: date

    def __post_init__(self) -> None:
        if type(self.start) is not date or type(self.end) is not date:
            raise TypeError("Reference periods require civil dates.")
        if self.end < self.start:
            raise ValueError("Reference period cannot be inverted.")

    @property
    def start_text(self) -> str:
        return self.start.isoformat()

    @property
    def end_text(self) -> str:
        return self.end.isoformat()


@dataclass(frozen=True)
class EconomicIdentity:
    provider: Provider
    series_id: str
    reference_period_start: date
    reference_period_end: date
    semantic_class: SemanticClass

    def __post_init__(self) -> None:
        if not isinstance(self.provider, Provider):
            raise TypeError("provider must be Provider.")
        if type(self.series_id) is not str or not self.series_id:
            raise ValueError("series_id is required.")
        if (
            type(self.reference_period_start) is not date
            or type(self.reference_period_end) is not date
        ):
            raise TypeError("Economic identity requires civil dates.")
        if self.reference_period_end < self.reference_period_start:
            raise ValueError("Economic identity period cannot be inverted.")
        if not isinstance(self.semantic_class, SemanticClass):
            raise TypeError("semantic_class must be SemanticClass.")

    def as_tuple(self) -> tuple[str, str, str, str, str]:
        return (
            self.provider.value,
            self.series_id,
            self.reference_period_start.isoformat(),
            self.reference_period_end.isoformat(),
            self.semantic_class.value,
        )


@dataclass(frozen=True)
class NormalizedExternalContent:
    provider: Provider
    series_id: str
    reference_period: ReferencePeriod
    semantic_class: SemanticClass
    frequency: Frequency
    value: Decimal
    value_text: str
    value_scale: int
    unit: Unit
    currency: str | None
    scope: Scope

    def __post_init__(self) -> None:
        if not isinstance(self.provider, Provider):
            raise TypeError("provider must be Provider.")
        if type(self.series_id) is not str or not self.series_id:
            raise ValueError("series_id is required.")
        if not isinstance(self.reference_period, ReferencePeriod):
            raise TypeError("reference_period must be ReferencePeriod.")
        if not isinstance(self.semantic_class, SemanticClass):
            raise TypeError("semantic_class must be SemanticClass.")
        if not isinstance(self.frequency, Frequency):
            raise TypeError("frequency must be Frequency.")
        if type(self.value) is not Decimal or not self.value.is_finite():
            raise TypeError("value must be a finite Decimal.")
        if type(self.value_text) is not str or Decimal(self.value_text) != self.value:
            raise ValueError("value_text must exactly represent value.")
        if type(self.value_scale) is not int:
            raise TypeError("value_scale must be a strict integer.")
        if not isinstance(self.unit, Unit):
            raise TypeError("unit must be Unit.")
        if self.currency is not None and type(self.currency) is not str:
            raise TypeError("currency must be a string or None.")
        if not isinstance(self.scope, Scope):
            raise TypeError("scope must be Scope.")

    @property
    def economic_identity(self) -> EconomicIdentity:
        return EconomicIdentity(
            provider=self.provider,
            series_id=self.series_id,
            reference_period_start=self.reference_period.start,
            reference_period_end=self.reference_period.end,
            semantic_class=self.semantic_class,
        )

    def as_payload_v1(self) -> dict[str, object]:
        return {
            "provider": self.provider.value,
            "series_id": self.series_id,
            "reference_period_start": self.reference_period.start_text,
            "reference_period_end": self.reference_period.end_text,
            "semantic_class": self.semantic_class.value,
            "frequency": self.frequency.value,
            "value_text": self.value_text,
            "value_scale": self.value_scale,
            "unit": self.unit.value,
            "currency": self.currency,
            "scope": self.scope.value,
        }


def _require_utc_timestamp(value: datetime, field_name: str) -> None:
    if type(value) is not datetime:
        raise ProvenanceValidationError(
            ExternalContextErrorCode.INVALID_PROVENANCE,
            f"{field_name} must be an explicit UTC datetime.",
            field=field_name,
        )
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ProvenanceValidationError(
            ExternalContextErrorCode.INVALID_PROVENANCE,
            f"{field_name} must be timezone-aware UTC.",
            field=field_name,
        )


@dataclass(frozen=True)
class ExternalObservationProvenance:
    """Provider provenance known before any R3-D persistence transaction."""

    provider_value_text: str
    provider_decimal_places: int
    source_url: str
    license_id: str
    retrieved_at: datetime
    observed_at: datetime | None = None
    published_at: datetime | None = None
    provider_revision_id: str | None = None
    revised_at: datetime | None = None

    def __post_init__(self) -> None:
        if type(self.provider_value_text) is not str:
            raise ProvenanceValidationError(
                ExternalContextErrorCode.INVALID_PROVENANCE,
                "provider_value_text must be lexical text.",
                field="provider_value_text",
            )
        if len(self.provider_value_text.encode("utf-8")) > 128:
            raise ProvenanceValidationError(
                ExternalContextErrorCode.INVALID_PROVENANCE,
                "provider_value_text exceeds 128 UTF-8 bytes.",
                field="provider_value_text",
            )
        if type(self.provider_decimal_places) is not int or self.provider_decimal_places < 0:
            raise ProvenanceValidationError(
                ExternalContextErrorCode.INVALID_PROVENANCE,
                "provider_decimal_places must be a non-negative strict integer.",
                field="provider_decimal_places",
            )
        for field_name, value in (
            ("source_url", self.source_url),
            ("license_id", self.license_id),
        ):
            if type(value) is not str or not value.strip():
                raise ProvenanceValidationError(
                    ExternalContextErrorCode.INVALID_PROVENANCE,
                    f"{field_name} must be a non-empty string.",
                    field=field_name,
                )
        _require_utc_timestamp(self.retrieved_at, "retrieved_at")
        for field_name, value in (
            ("observed_at", self.observed_at),
            ("published_at", self.published_at),
            ("revised_at", self.revised_at),
        ):
            if value is not None:
                _require_utc_timestamp(value, field_name)
        if self.provider_revision_id is not None and (
            type(self.provider_revision_id) is not str
            or not self.provider_revision_id.strip()
        ):
            raise ProvenanceValidationError(
                ExternalContextErrorCode.INVALID_PROVENANCE,
                "provider_revision_id must be non-empty when supplied.",
                field="provider_revision_id",
            )


@dataclass(frozen=True)
class ExternalObservation:
    registry_key: RegistryKey
    series_concept: str
    content: NormalizedExternalContent
    provenance: ExternalObservationProvenance

    def __post_init__(self) -> None:
        from .registry import resolve_series_by_key

        definition = resolve_series_by_key(self.registry_key)
        if self.series_concept != definition.official_concept:
            raise ValueError("series_concept must come from the executable registry.")
        if (
            self.content.provider is not definition.provider
            or self.content.series_id != definition.series_id
        ):
            raise ValueError("Observation content does not match its registry definition.")
        if self.provenance.provider_decimal_places != definition.provider_decimal_places:
            raise ValueError("Observation precision does not match the registry.")
        if self.provenance.source_url != definition.provenance.source_url:
            raise ValueError("Observation source_url does not match the registry.")
        if self.provenance.license_id != definition.provenance.license_id:
            raise ValueError("Observation license_id does not match the registry.")

    @property
    def economic_identity(self) -> EconomicIdentity:
        return self.content.economic_identity


@dataclass(frozen=True)
class ContentFingerprintV1:
    content_fingerprint_version: int
    content_fingerprint: str
    canonical_json: str
    normalized_content: NormalizedExternalContent

    def __post_init__(self) -> None:
        if self.content_fingerprint_version != 1:
            raise ValueError("R3-C supports content_fingerprint_version 1 only.")
        if type(self.content_fingerprint) is not str or re.fullmatch(
            r"sha256:[0-9a-f]{64}", self.content_fingerprint
        ) is None:
            raise ValueError("content_fingerprint must use lowercase SHA-256 form.")
        if type(self.canonical_json) is not str:
            raise TypeError("canonical_json must be text.")
        if not isinstance(self.normalized_content, NormalizedExternalContent):
            raise TypeError("normalized_content must be NormalizedExternalContent.")

    def as_pair(self) -> tuple[int, str]:
        return self.content_fingerprint_version, self.content_fingerprint
