from dataclasses import FrozenInstanceError
from decimal import Decimal, getcontext, localcontext

import pytest

from backend.domains.fire import (
    FireSummaryCalculator,
    FireSummaryInput,
    FireSummaryStatus,
)


def _calculate(
    wealth: str = "250000.00",
    spending: str = "5000.00",
    rate: str = "0.04",
):
    return FireSummaryCalculator().calculate(
        FireSummaryInput(
            eligible_investment_wealth=Decimal(wealth),
            monthly_retirement_spending=Decimal(spending),
            assumed_annual_withdrawal_rate=Decimal(rate),
        )
    )


def test_exact_target_uses_exact_annual_spending_and_money_scale():
    result = _calculate()

    assert result.monthly_retirement_spending == Decimal("5000.00")
    assert result.annual_required_spending == Decimal("60000.00")
    assert result.fire_target == Decimal("1500000.00")


def test_target_rounds_up_with_ceiling_not_half_even():
    result = _calculate(spending="1000.00", rate="0.07")

    assert result.annual_required_spending == Decimal("12000.00")
    assert result.fire_target == Decimal("171428.58")


def test_progress_above_one_is_preserved_with_zero_gap_and_achieved_status():
    result = _calculate(wealth="1800000.00")

    assert result.progress_ratio == Decimal("1.20000000")
    assert result.gap_to_fire == Decimal("0.00")
    assert result.status is FireSummaryStatus.ALREADY_FINANCIALLY_INDEPENDENT


def test_monthly_withdrawal_is_derived_from_raw_annual_withdrawal():
    result = _calculate(wealth="100.51", spending="1000.00", rate="0.12")

    assert result.supported_annual_withdrawal == Decimal("12.06")
    assert result.supported_monthly_withdrawal == Decimal("1.01")


def test_exact_target_equality_counts_as_financial_independence():
    result = _calculate(wealth="1500000.00")

    assert result.gap_to_fire == Decimal("0.00")
    assert result.progress_ratio == Decimal("1.00000000")
    assert result.status is FireSummaryStatus.ALREADY_FINANCIALLY_INDEPENDENT


def test_zero_wealth_is_valid_and_returns_zero_capacity():
    result = _calculate(wealth="0.00")

    assert result.gap_to_fire == result.fire_target
    assert result.progress_ratio == Decimal("0.00000000")
    assert result.supported_annual_withdrawal == Decimal("0.00")
    assert result.supported_monthly_withdrawal == Decimal("0.00")
    assert result.status is FireSummaryStatus.BELOW_FIRE_TARGET


@pytest.mark.parametrize(
    "spending",
    [
        Decimal("0"),
        Decimal("-0.01"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("5000.001"),
    ],
)
def test_invalid_monthly_retirement_spending_is_rejected(spending):
    with pytest.raises(ValueError):
        FireSummaryInput(
            eligible_investment_wealth=Decimal("1.00"),
            monthly_retirement_spending=spending,
            assumed_annual_withdrawal_rate=Decimal("0.04"),
        )


@pytest.mark.parametrize(
    "rate",
    [
        Decimal("0"),
        Decimal("-0.01"),
        Decimal("1"),
        Decimal("1.01"),
        Decimal("NaN"),
        Decimal("Infinity"),
    ],
)
def test_invalid_withdrawal_rate_is_rejected(rate):
    with pytest.raises(ValueError):
        FireSummaryInput(
            eligible_investment_wealth=Decimal("1.00"),
            monthly_retirement_spending=Decimal("1.00"),
            assumed_annual_withdrawal_rate=rate,
        )


@pytest.mark.parametrize(
    "wealth",
    [
        Decimal("-0.01"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("1.001"),
    ],
)
def test_invalid_eligible_investment_wealth_is_rejected(wealth):
    with pytest.raises(ValueError):
        FireSummaryInput(
            eligible_investment_wealth=wealth,
            monthly_retirement_spending=Decimal("1.00"),
            assumed_annual_withdrawal_rate=Decimal("0.04"),
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "eligible_investment_wealth",
        "monthly_retirement_spending",
        "assumed_annual_withdrawal_rate",
    ],
)
def test_inputs_reject_non_decimal_authority(field_name):
    values = {
        "eligible_investment_wealth": Decimal("1.00"),
        "monthly_retirement_spending": Decimal("1.00"),
        "assumed_annual_withdrawal_rate": Decimal("0.04"),
    }
    values[field_name] = 1.0

    with pytest.raises(TypeError, match="must be Decimal"):
        FireSummaryInput(**values)


def test_input_and_result_are_immutable_and_keep_decimal_outputs():
    input = FireSummaryInput(
        eligible_investment_wealth=Decimal("1.00"),
        monthly_retirement_spending=Decimal("1.00"),
        assumed_annual_withdrawal_rate=Decimal("0.04"),
    )
    result = FireSummaryCalculator().calculate(input)

    with pytest.raises(FrozenInstanceError):
        input.eligible_investment_wealth = Decimal("2.00")
    with pytest.raises(FrozenInstanceError):
        result.fire_target = Decimal("2.00")

    for value in (
        result.monthly_retirement_spending,
        result.annual_required_spending,
        result.assumed_annual_withdrawal_rate,
        result.fire_target,
        result.eligible_investment_wealth,
        result.gap_to_fire,
        result.progress_ratio,
        result.supported_annual_withdrawal,
        result.supported_monthly_withdrawal,
    ):
        assert type(value) is Decimal


def test_large_valid_values_use_local_adaptive_precision_without_mutating_global_context():
    large_spending = Decimal("9" * 80 + ".99")
    original_precision = getcontext().prec

    with localcontext() as context:
        context.prec = 7
        result = FireSummaryCalculator().calculate(
            FireSummaryInput(
                eligible_investment_wealth=Decimal("9" * 80 + ".99"),
                monthly_retirement_spending=large_spending,
                assumed_annual_withdrawal_rate=Decimal("0.000001"),
            )
        )

        assert result.fire_target.is_finite()
        assert result.fire_target.as_tuple().exponent == -2
        assert result.fire_target > result.eligible_investment_wealth
        assert getcontext().prec == 7

    assert getcontext().prec == original_precision


def test_calculator_requires_the_explicit_input_model():
    with pytest.raises(TypeError, match="FireSummaryInput"):
        FireSummaryCalculator().calculate(object())
