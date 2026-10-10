"""Immutable executable allowlist for the five locked BCB/SGS series."""

from __future__ import annotations

from datetime import date
from types import MappingProxyType
from typing import Mapping

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
    RegistryValidationError,
    UnknownSeriesError,
)
from .models import ExternalSeriesDefinition, StaticSeriesProvenance


_ATTRIBUTION = "Banco Central do Brasil / SGS"
_LICENSE_ID = "ODbL"


def _provenance(series_id: str, source_name: str) -> StaticSeriesProvenance:
    return StaticSeriesProvenance(
        source_name=source_name,
        source_url=f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados",
        license_id=_LICENSE_ID,
        attribution=_ATTRIBUTION,
    )


_DEFINITIONS = (
    ExternalSeriesDefinition(
        registry_key=RegistryKey.BCB_SGS_SELIC_TARGET,
        provider=Provider.BCB_SGS,
        series_id="432",
        official_concept="Interest rate - Selic target",
        frequency=Frequency.DAILY,
        unit=Unit.PERCENT_PER_YEAR,
        scope=Scope.BR,
        semantic_class=SemanticClass.EXTERNAL_OBSERVATION,
        currency=None,
        provider_decimal_places=2,
        normalization_scale=2,
        historical_coverage_start=date(1999, 3, 5),
        normalized_mvp_floor=None,
        eligibility=RegistryEligibility.MVP_ELIGIBLE,
        permitted_use=SeriesUse.EXTERNAL_REFERENCE,
        provenance=_provenance("432", "Copom"),
    ),
    ExternalSeriesDefinition(
        registry_key=RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
        provider=Provider.BCB_SGS,
        series_id="11",
        official_concept="Interest rate - Selic",
        frequency=Frequency.DAILY,
        unit=Unit.PERCENT_PER_DAY,
        scope=Scope.BR,
        semantic_class=SemanticClass.EXTERNAL_OBSERVATION,
        currency=None,
        provider_decimal_places=6,
        normalization_scale=6,
        historical_coverage_start=date(1986, 6, 4),
        normalized_mvp_floor=None,
        eligibility=RegistryEligibility.MVP_ELIGIBLE,
        permitted_use=SeriesUse.EXTERNAL_REFERENCE,
        provenance=_provenance("11", "BCB-Demab"),
    ),
    ExternalSeriesDefinition(
        registry_key=RegistryKey.BCB_SGS_CDI,
        provider=Provider.BCB_SGS,
        series_id="12",
        official_concept="Interest rate - CDI",
        frequency=Frequency.DAILY,
        unit=Unit.PERCENT_PER_DAY,
        scope=Scope.BR,
        semantic_class=SemanticClass.EXTERNAL_OBSERVATION,
        currency=None,
        provider_decimal_places=6,
        normalization_scale=6,
        historical_coverage_start=date(1986, 3, 6),
        normalized_mvp_floor=None,
        eligibility=RegistryEligibility.MVP_ELIGIBLE,
        permitted_use=SeriesUse.EXTERNAL_REFERENCE,
        provenance=_provenance("12", "Cetip"),
    ),
    ExternalSeriesDefinition(
        registry_key=RegistryKey.BCB_SGS_IPCA_MONTHLY,
        provider=Provider.BCB_SGS,
        series_id="433",
        official_concept="Broad National Consumer Price Index (IPCA)",
        frequency=Frequency.MONTHLY,
        unit=Unit.PERCENT_MONTHLY_CHANGE,
        scope=Scope.BR,
        semantic_class=SemanticClass.EXTERNAL_OBSERVATION,
        currency=None,
        provider_decimal_places=2,
        normalization_scale=2,
        historical_coverage_start=date(1980, 1, 1),
        normalized_mvp_floor=None,
        eligibility=RegistryEligibility.MVP_ELIGIBLE,
        permitted_use=SeriesUse.EXTERNAL_REFERENCE,
        provenance=_provenance("433", "IBGE"),
    ),
    ExternalSeriesDefinition(
        registry_key=RegistryKey.BCB_SGS_USD_SELL,
        provider=Provider.BCB_SGS,
        series_id="1",
        official_concept="Free-market United States dollar selling exchange rate",
        frequency=Frequency.DAILY,
        unit=Unit.BRL_PER_USD,
        scope=Scope.BR,
        semantic_class=SemanticClass.EXTERNAL_OBSERVATION,
        currency="BRL/USD",
        provider_decimal_places=4,
        normalization_scale=4,
        historical_coverage_start=date(1984, 11, 28),
        normalized_mvp_floor=date(1994, 7, 1),
        eligibility=RegistryEligibility.MVP_ELIGIBLE_REFERENCE_ONLY,
        permitted_use=SeriesUse.REFERENCE_ONLY,
        provenance=_provenance("1", "Sisbacen PTAX800"),
    ),
)


SERIES_REGISTRY: Mapping[str, ExternalSeriesDefinition] = MappingProxyType(
    {definition.registry_key.value: definition for definition in _DEFINITIONS}
)

_SERIES_BY_ID: Mapping[str, ExternalSeriesDefinition] = MappingProxyType(
    {definition.series_id: definition for definition in _DEFINITIONS}
)


def all_series() -> tuple[ExternalSeriesDefinition, ...]:
    return _DEFINITIONS


def resolve_series_by_key(
    registry_key: RegistryKey | str,
) -> ExternalSeriesDefinition:
    if isinstance(registry_key, RegistryKey):
        key = registry_key.value
    elif type(registry_key) is str:
        key = registry_key
    else:
        raise UnknownSeriesError(registry_key=registry_key)
    try:
        return SERIES_REGISTRY[key]
    except KeyError as exc:
        raise UnknownSeriesError(registry_key=key) from exc


def resolve_series(
    provider: Provider | str,
    series_id: str,
) -> ExternalSeriesDefinition:
    provider_value = provider.value if isinstance(provider, Provider) else provider
    if type(series_id) is not str or series_id not in _SERIES_BY_ID:
        raise UnknownSeriesError(series_id=series_id)
    definition = _SERIES_BY_ID[series_id]
    if type(provider_value) is not str or provider_value != definition.provider.value:
        raise RegistryValidationError(
            ExternalContextErrorCode.REGISTRY_MISMATCH,
            "provider is incompatible with the allowlisted series.",
            field="provider",
            details={
                "expected": definition.provider.value,
                "received": provider_value,
                "series_id": series_id,
            },
        )
    return definition
