from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from backend.domains.external_context import (
    AcquisitionHealth,
    Availability,
    EconomicFreshness,
    Frequency,
    Provider,
    RegistryEligibility,
    RegistryKey,
    SERIES_REGISTRY,
    Scope,
    SemanticClass,
    SeriesUse,
    Unit,
    UnknownSeriesError,
    all_series,
    resolve_series,
    resolve_series_by_key,
)


EXPECTED_SERIES = {
    "BCB_SGS_SELIC_TARGET": {
        "series_id": "432",
        "concept": "Interest rate - Selic target",
        "frequency": Frequency.DAILY,
        "unit": Unit.PERCENT_PER_YEAR,
        "scale": 2,
        "currency": None,
        "start": date(1999, 3, 5),
        "source": "Copom",
    },
    "BCB_SGS_SELIC_EFFECTIVE": {
        "series_id": "11",
        "concept": "Interest rate - Selic",
        "frequency": Frequency.DAILY,
        "unit": Unit.PERCENT_PER_DAY,
        "scale": 6,
        "currency": None,
        "start": date(1986, 6, 4),
        "source": "BCB-Demab",
    },
    "BCB_SGS_CDI": {
        "series_id": "12",
        "concept": "Interest rate - CDI",
        "frequency": Frequency.DAILY,
        "unit": Unit.PERCENT_PER_DAY,
        "scale": 6,
        "currency": None,
        "start": date(1986, 3, 6),
        "source": "Cetip",
    },
    "BCB_SGS_IPCA_MONTHLY": {
        "series_id": "433",
        "concept": "Broad National Consumer Price Index (IPCA)",
        "frequency": Frequency.MONTHLY,
        "unit": Unit.PERCENT_MONTHLY_CHANGE,
        "scale": 2,
        "currency": None,
        "start": date(1980, 1, 1),
        "source": "IBGE",
    },
    "BCB_SGS_USD_SELL": {
        "series_id": "1",
        "concept": "Free-market United States dollar selling exchange rate",
        "frequency": Frequency.DAILY,
        "unit": Unit.BRL_PER_USD,
        "scale": 4,
        "currency": "BRL/USD",
        "start": date(1984, 11, 28),
        "source": "Sisbacen PTAX800",
    },
}


def test_registry_contains_exactly_the_five_locked_series() -> None:
    assert set(SERIES_REGISTRY) == set(EXPECTED_SERIES)
    assert len(SERIES_REGISTRY) == 5
    assert len(all_series()) == 5
    assert {definition.series_id for definition in all_series()} == {
        "432",
        "11",
        "12",
        "433",
        "1",
    }


@pytest.mark.parametrize(("registry_key", "expected"), EXPECTED_SERIES.items())
def test_registry_metadata_matches_the_locked_catalog(
    registry_key: str,
    expected: dict[str, object],
) -> None:
    definition = resolve_series_by_key(registry_key)

    assert definition.registry_key.value == registry_key
    assert definition.provider is Provider.BCB_SGS
    assert definition.series_id == expected["series_id"]
    assert definition.official_concept == expected["concept"]
    assert definition.frequency is expected["frequency"]
    assert definition.unit is expected["unit"]
    assert definition.scope is Scope.BR
    assert definition.semantic_class is SemanticClass.EXTERNAL_OBSERVATION
    assert definition.currency == expected["currency"]
    assert definition.provider_decimal_places == expected["scale"]
    assert definition.normalization_scale == expected["scale"]
    assert definition.historical_coverage_start == expected["start"]
    assert definition.provenance.source_name == expected["source"]
    assert definition.provenance.license_id == "ODbL"
    assert definition.provenance.attribution == "Banco Central do Brasil / SGS"
    assert definition.provenance.source_url.endswith(
        f"bcdata.sgs.{definition.series_id}/dados"
    )


def test_sgs_1_is_reference_only_and_uses_the_real_era_floor() -> None:
    definition = resolve_series_by_key(RegistryKey.BCB_SGS_USD_SELL)

    assert definition.eligibility is RegistryEligibility.MVP_ELIGIBLE_REFERENCE_ONLY
    assert definition.permitted_use is SeriesUse.REFERENCE_ONLY
    assert definition.normalized_mvp_floor == date(1994, 7, 1)
    assert definition.earliest_normalized_date == date(1994, 7, 1)
    assert "PTAX" not in definition.official_concept.upper()


@pytest.mark.parametrize(
    "registry_key",
    [
        RegistryKey.BCB_SGS_SELIC_TARGET,
        RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
        RegistryKey.BCB_SGS_CDI,
        RegistryKey.BCB_SGS_IPCA_MONTHLY,
    ],
)
def test_non_fx_series_have_no_currency_and_are_regular_mvp_references(
    registry_key: RegistryKey,
) -> None:
    definition = resolve_series_by_key(registry_key)
    assert definition.currency is None
    assert definition.eligibility is RegistryEligibility.MVP_ELIGIBLE
    assert definition.permitted_use is SeriesUse.EXTERNAL_REFERENCE


def test_focus_and_unapproved_series_are_not_executable() -> None:
    assert all("FOCUS" not in key for key in SERIES_REGISTRY)
    assert all(definition.series_id != "4389" for definition in all_series())
    with pytest.raises(UnknownSeriesError) as failure:
        resolve_series_by_key("BCB_FOCUS_IPCA_MEDIAN")
    assert failure.value.code.value == "UNKNOWN_SERIES"


def test_registry_resolves_by_official_identity() -> None:
    assert resolve_series("BCB_SGS", "432") is SERIES_REGISTRY[
        "BCB_SGS_SELIC_TARGET"
    ]
    assert resolve_series(Provider.BCB_SGS, "1") is SERIES_REGISTRY[
        "BCB_SGS_USD_SELL"
    ]


def test_unknown_series_identity_raises_typed_error() -> None:
    with pytest.raises(UnknownSeriesError) as failure:
        resolve_series("BCB_SGS", "999999")
    assert failure.value.field == "series_id"
    assert failure.value.details["series_id"] == "999999"


def test_registry_and_definitions_are_immutable() -> None:
    with pytest.raises(TypeError):
        SERIES_REGISTRY["ARBITRARY"] = SERIES_REGISTRY["BCB_SGS_SELIC_TARGET"]

    definition = resolve_series_by_key("BCB_SGS_SELIC_TARGET")
    with pytest.raises(FrozenInstanceError):
        definition.normalization_scale = 6
    with pytest.raises(FrozenInstanceError):
        definition.provenance.license_id = "changed"


def test_state_dimensions_are_independent_closed_enums() -> None:
    assert {state.value for state in Availability} == {
        "AVAILABLE",
        "PARTIAL",
        "UNAVAILABLE",
    }
    assert {state.value for state in EconomicFreshness} == {
        "CURRENT",
        "STALE",
        "UNKNOWN",
    }
    assert {state.value for state in AcquisitionHealth} == {
        "HEALTHY",
        "DEGRADED",
        "FAILED",
        "UNKNOWN",
    }
    assert Availability is not EconomicFreshness
    assert EconomicFreshness is not AcquisitionHealth
