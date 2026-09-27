from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal

import pytest

from backend.domains.planning import (
    ContributionTiming,
    OutputMode,
    ProjectionAssumptions,
    RateBasis,
    ReturnType,
)


def _assumptions(**overrides):
    values = {
        "as_of_date": date(2026, 9, 16),
        "scenario_monthly_contribution": Decimal("1000.00"),
        "expected_return_rate": Decimal("0.085"),
        "return_type": ReturnType.NOMINAL,
        "output_mode": OutputMode.NOMINAL,
        "horizon_months": 12,
    }
    values.update(overrides)
    return ProjectionAssumptions(**values)


@pytest.mark.parametrize(
    ("return_type", "output_mode", "inflation_rate"),
    [
        (ReturnType.NOMINAL, OutputMode.NOMINAL, None),
        (ReturnType.NOMINAL, OutputMode.REAL, Decimal("0.045")),
        (ReturnType.REAL, OutputMode.REAL, None),
    ],
)
def test_approved_nominal_real_matrix_is_valid(
    return_type,
    output_mode,
    inflation_rate,
):
    assumptions = _assumptions(
        return_type=return_type,
        output_mode=output_mode,
        inflation_rate=inflation_rate,
    )

    assert assumptions.return_type is return_type
    assert assumptions.output_mode is output_mode
    assert assumptions.inflation_rate == inflation_rate


@pytest.mark.parametrize(
    "contribution",
    [Decimal("0.00"), Decimal("1000"), Decimal("1000.1"), Decimal("1000.00")],
)
def test_non_negative_cent_scale_contribution_is_valid(contribution):
    assert _assumptions(
        scenario_monthly_contribution=contribution,
    ).scenario_monthly_contribution is contribution


@pytest.mark.parametrize(
    "annual_rate",
    [Decimal("-0.999"), Decimal("0"), Decimal("0.085"), Decimal("1"), Decimal("2.5")],
)
def test_finite_annual_rate_greater_than_minus_one_is_valid(annual_rate):
    assumptions = _assumptions(expected_return_rate=annual_rate)

    assert assumptions.expected_return_rate is annual_rate
    assert assumptions.rate_basis is RateBasis.EFFECTIVE_ANNUAL


@pytest.mark.parametrize("horizon", [1, 1200])
def test_supported_horizon_boundaries_are_valid(horizon):
    assert _assumptions(horizon_months=horizon).resolved_horizon_months == horizon


def test_target_date_resolves_by_calendar_month_and_ignores_day():
    first_day = _assumptions(horizon_months=None, target_date=date(2026, 10, 1))
    last_day = _assumptions(horizon_months=None, target_date=date(2026, 10, 31))

    assert first_day.resolved_horizon_months == 1
    assert last_day.resolved_horizon_months == 1


def test_target_date_resolves_cross_year_without_day_approximation():
    assumptions = _assumptions(
        as_of_date=date(2026, 12, 20),
        horizon_months=None,
        target_date=date(2027, 1, 1),
    )

    assert assumptions.resolved_horizon_months == 1


def test_target_date_resolves_twelve_months():
    assumptions = _assumptions(
        horizon_months=None,
        target_date=date(2027, 9, 30),
    )

    assert assumptions.resolved_horizon_months == 12


def test_decimal_rate_identity_is_preserved():
    rate = Decimal("0.085")
    assumptions = _assumptions(expected_return_rate=rate)

    assert assumptions.expected_return_rate is rate
    assert type(assumptions.expected_return_rate) is Decimal


def test_assumptions_are_immutable():
    assumptions = _assumptions()

    with pytest.raises(FrozenInstanceError):
        assumptions.expected_return_rate = Decimal("0.10")


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"scenario_monthly_contribution": Decimal("-0.01")}, "cannot be negative"),
        ({"scenario_monthly_contribution": Decimal("1000.001")}, "at most two"),
        ({"scenario_monthly_contribution": 0.1}, "must be Decimal"),
        ({"scenario_monthly_contribution": True}, "must be Decimal"),
        ({"expected_return_rate": Decimal("-1")}, "greater than -1"),
        ({"expected_return_rate": Decimal("-1.01")}, "greater than -1"),
        ({"expected_return_rate": Decimal("NaN")}, "must be finite"),
        ({"expected_return_rate": Decimal("Infinity")}, "must be finite"),
        ({"expected_return_rate": Decimal("-Infinity")}, "must be finite"),
        ({"expected_return_rate": 0.085}, "must be Decimal"),
        ({"expected_return_rate": True}, "must be Decimal"),
        ({"as_of_date": datetime(2026, 9, 16)}, "must be a date"),
    ],
)
def test_invalid_scalar_inputs_fail_without_coercion(overrides, message):
    with pytest.raises(ValueError, match=message):
        _assumptions(**overrides)


@pytest.mark.parametrize(
    ("inflation", "message"),
    [
        (Decimal("-1"), "greater than -1"),
        (Decimal("-1.01"), "greater than -1"),
        (Decimal("NaN"), "must be finite"),
        (Decimal("Infinity"), "must be finite"),
        (Decimal("-Infinity"), "must be finite"),
        (0.045, "must be Decimal"),
        (True, "must be Decimal"),
    ],
)
def test_invalid_inflation_inputs_fail_without_coercion(inflation, message):
    with pytest.raises(ValueError, match=message):
        _assumptions(
            return_type=ReturnType.NOMINAL,
            output_mode=OutputMode.REAL,
            inflation_rate=inflation,
        )


def test_inflation_has_no_arbitrary_positive_cap():
    assumptions = _assumptions(
        return_type=ReturnType.NOMINAL,
        output_mode=OutputMode.REAL,
        inflation_rate=Decimal("2.5"),
    )

    assert assumptions.inflation_rate == Decimal("2.5")


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"return_type": ReturnType.NOMINAL, "output_mode": OutputMode.REAL},
            "required for NOMINAL to REAL",
        ),
        (
            {"inflation_rate": Decimal("0.04")},
            "forbidden for this return/output mode",
        ),
        (
            {
                "return_type": ReturnType.REAL,
                "output_mode": OutputMode.REAL,
                "inflation_rate": Decimal("0.04"),
            },
            "forbidden for this return/output mode",
        ),
        (
            {"return_type": ReturnType.REAL, "output_mode": OutputMode.NOMINAL},
            "not supported",
        ),
        (
            {
                "return_type": ReturnType.REAL,
                "output_mode": OutputMode.NOMINAL,
                "inflation_rate": Decimal("0.04"),
            },
            "not supported",
        ),
    ],
)
def test_invalid_nominal_real_matrix_fails(overrides, message):
    with pytest.raises(ValueError, match=message):
        _assumptions(**overrides)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"horizon_months": None}, "exactly one horizon source"),
        ({"target_date": date(2027, 1, 1)}, "exactly one horizon source"),
        ({"horizon_months": 0}, "between 1 and 1200"),
        ({"horizon_months": -1}, "between 1 and 1200"),
        ({"horizon_months": 1201}, "between 1 and 1200"),
        ({"horizon_months": True}, "must be an integer"),
        ({"horizon_months": 1.0}, "must be an integer"),
    ],
)
def test_invalid_horizon_inputs_fail(overrides, message):
    with pytest.raises(ValueError, match=message):
        _assumptions(**overrides)


@pytest.mark.parametrize(
    ("target_date", "message"),
    [
        (date(2026, 9, 1), "at least one projected month"),
        (date(2026, 9, 30), "at least one projected month"),
        (date(2026, 8, 31), "at least one projected month"),
        (date(2126, 10, 1), "cannot exceed 1200"),
    ],
)
def test_invalid_target_dates_fail(target_date, message):
    with pytest.raises(ValueError, match=message):
        _assumptions(horizon_months=None, target_date=target_date)


def test_exactly_1200_target_months_is_valid():
    assumptions = _assumptions(
        horizon_months=None,
        target_date=date(2126, 9, 30),
    )

    assert assumptions.resolved_horizon_months == 1200


def test_target_date_rejects_datetime_subclass():
    with pytest.raises(ValueError, match="target_date must be a date"):
        _assumptions(
            horizon_months=None,
            target_date=datetime(2026, 10, 1),
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("return_type", "NOMINAL", "return_type must be ReturnType"),
        ("output_mode", "NOMINAL", "output_mode must be OutputMode"),
        ("rate_basis", "EFFECTIVE_ANNUAL", "rate_basis must be EFFECTIVE_ANNUAL"),
        ("contribution_timing", "END_OF_MONTH", "contribution_timing must be END_OF_MONTH"),
    ],
)
def test_enum_strings_are_not_silently_coerced(field, value, message):
    with pytest.raises(ValueError, match=message):
        _assumptions(**{field: value})


def test_contract_does_not_contain_projection_outputs_or_initial_wealth():
    assumptions = _assumptions()

    forbidden_fields = {
        "initial_wealth",
        "final_wealth",
        "projected_return",
        "ending_balance",
        "monthly_rate",
        "growth",
        "target_achievement",
    }
    assert forbidden_fields.isdisjoint(assumptions.__dataclass_fields__)


def test_contract_constants_are_explicit_and_not_configurably_extended():
    assumptions = _assumptions()

    assert assumptions.rate_basis is RateBasis.EFFECTIVE_ANNUAL
    assert assumptions.contribution_timing is ContributionTiming.END_OF_MONTH
    assert list(RateBasis) == [RateBasis.EFFECTIVE_ANNUAL]
    assert list(ContributionTiming) == [ContributionTiming.END_OF_MONTH]
