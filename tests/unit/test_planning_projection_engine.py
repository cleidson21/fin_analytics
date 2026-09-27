from dataclasses import FrozenInstanceError, fields
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_EVEN, getcontext, localcontext

import pytest

from backend.domains.planning import (
    ForwardProjectionEngine,
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    OutputMode,
    PlanningFactAsOf,
    PlanningFactProvenance,
    ProjectionAssumptions,
    ProjectionPeriod,
    ReturnType,
)
from backend.domains.planning.projection import (
    DECIMAL_CALCULATION_PRECISION,
    _estimate_working_precision,
    _quantize_money,
)


POSITIVE_MONTHLY_RATE = Decimal(
    "0.009488792934582974126355069193493956394460700845789475687468293980379846757233312842368003607676341"
)
NEGATIVE_MONTHLY_RATE = Decimal(
    "-0.0105962410353190023974723009887689776419662722370494608135865563792507969906615282541175481527227743"
)
FISHER_ANNUAL_RATE = Decimal(
    "0.047619047619047619047619047619047619047619047619047619047619047619047619047619047619047619047619048"
)
FISHER_MONTHLY_RATE = Decimal(
    "0.003884191966384934932782121128384017958938745779680488321197849685417107035646570477627972058007929"
)
RATE_TOLERANCE = Decimal("1e-75")


def _initial_wealth(
    amount="1000.00",
    source=InitialWealthSource.USER_PROVIDED_SCENARIO,
    scope=InitialWealthScope.USER_PROVIDED_SCENARIO,
):
    if source is InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT:
        as_of = PlanningFactAsOf(reference_month="2026-09")
        provenance = PlanningFactProvenance(
            source_table="portfolio_snapshots",
            source_type="MYPROFIT_EVOLUCAO",
            account_id="account-a",
            reference_month="2026-09",
            run_id="run-2026-09",
        )
    elif source is InitialWealthSource.GOAL_CURRENT_AMOUNT:
        as_of = PlanningFactAsOf(observed_at=datetime(2026, 9, 10, 12, 0, 0))
        provenance = PlanningFactProvenance(
            source_table="goals",
            source_type="USER_GOVERNED_GOAL",
        )
    else:
        as_of = PlanningFactAsOf(observed_at=datetime(2026, 9, 16, 12, 0, 0))
        provenance = PlanningFactProvenance(
            source_table="planning_request",
            source_type="USER_PROVIDED_SCENARIO",
        )

    value = amount if isinstance(amount, Decimal) else Decimal(amount)
    return InitialWealthFact(
        source=source,
        amount=value,
        as_of=as_of,
        scope=scope,
        provenance=provenance,
    )


def _assumptions(**overrides):
    values = {
        "as_of_date": date(2026, 9, 16),
        "scenario_monthly_contribution": Decimal("0.00"),
        "expected_return_rate": Decimal("0"),
        "return_type": ReturnType.NOMINAL,
        "output_mode": OutputMode.NOMINAL,
        "horizon_months": 12,
    }
    values.update(overrides)
    return ProjectionAssumptions(**values)


def _independent_oracle(
    initial,
    contribution,
    monthly_rate,
    horizon,
    precision=100,
):
    """Transparent test-only recurrence using a precomputed monthly rate."""

    periods = []
    opening = initial
    cumulative_contributions = Decimal("0.00")
    cumulative_growth = Decimal("0.00")
    with localcontext() as context:
        context.prec = precision
        for _ in range(horizon):
            projected_return = (opening * monthly_rate).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_EVEN,
            )
            ending = opening + projected_return + contribution
            cumulative_contributions += contribution
            cumulative_growth += projected_return
            periods.append(
                (
                    opening,
                    projected_return,
                    ending,
                    cumulative_contributions,
                    cumulative_growth,
                )
            )
            opening = ending
    return periods


def _independent_extreme_oracle(initial, contribution, annual_rate, horizon):
    """High-precision Newton oracle independent of production rate helpers."""

    with localcontext() as context:
        context.prec = 500
        annual_growth_factor = Decimal("1") + annual_rate
        monthly_growth_factor = Decimal("2")
        for _ in range(2000):
            next_factor = (
                Decimal("11") * monthly_growth_factor
                + annual_growth_factor / (monthly_growth_factor ** 11)
            ) / Decimal("12")
            if next_factor == monthly_growth_factor:
                break
            monthly_growth_factor = next_factor
        else:
            raise AssertionError("independent monthly-rate oracle did not converge")

        monthly_rate = monthly_growth_factor - Decimal("1")
        periods = _independent_oracle(
            initial,
            contribution,
            monthly_rate,
            horizon,
            precision=500,
        )
        return monthly_rate, periods


def test_zero_rate_and_zero_contribution_keeps_wealth_exact_for_twelve_months():
    result = ForwardProjectionEngine().project(_initial_wealth(), _assumptions())

    assert len(result.periods) == 12
    assert all(period.opening_wealth == Decimal("1000.00") for period in result.periods)
    assert all(period.projected_return == Decimal("0.00") for period in result.periods)
    assert all(period.ending_wealth == Decimal("1000.00") for period in result.periods)
    assert result.monthly_equivalent_rate == Decimal("0")
    assert result.final_wealth == Decimal("1000.00")
    assert result.total_contributions == Decimal("0.00")
    assert result.total_projected_growth == Decimal("0.00")


def test_zero_rate_with_contribution_has_exact_end_of_month_recurrence():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=3,
        ),
    )

    assert [period.opening_wealth for period in result.periods] == [
        Decimal("1000.00"),
        Decimal("1100.00"),
        Decimal("1200.00"),
    ]
    assert [period.ending_wealth for period in result.periods] == [
        Decimal("1100.00"),
        Decimal("1200.00"),
        Decimal("1300.00"),
    ]
    assert result.total_contributions == Decimal("300.00")
    assert result.total_projected_growth == Decimal("0.00")


def test_positive_rate_uses_compound_monthly_equivalent_and_independent_oracle():
    assumptions = _assumptions(
        expected_return_rate=Decimal("0.12"),
        scenario_monthly_contribution=Decimal("100.00"),
    )
    result = ForwardProjectionEngine().project(_initial_wealth(), assumptions)
    oracle = _independent_oracle(
        Decimal("1000.00"),
        Decimal("100.00"),
        POSITIVE_MONTHLY_RATE,
        12,
    )

    assert abs(result.monthly_equivalent_rate - POSITIVE_MONTHLY_RATE) < RATE_TOLERANCE
    assert result.effective_projection_annual_rate == Decimal("0.12")
    for period, expected in zip(result.periods, oracle):
        assert (
            period.opening_wealth,
            period.projected_return,
            period.ending_wealth,
            period.cumulative_contributions,
            period.cumulative_projected_growth,
        ) == expected


def test_contribution_does_not_earn_return_in_same_month():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(
            expected_return_rate=Decimal("0.12"),
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=1,
        ),
    )

    first = result.periods[0]
    assert first.projected_return == Decimal("9.49")
    assert first.projected_return == (
        Decimal("1000.00") * POSITIVE_MONTHLY_RATE
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    assert first.projected_return != (
        Decimal("1100.00") * POSITIVE_MONTHLY_RATE
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def test_negative_rate_and_contribution_keep_end_of_month_order():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(
            expected_return_rate=Decimal("-0.12"),
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=2,
        ),
    )

    assert abs(result.monthly_equivalent_rate - NEGATIVE_MONTHLY_RATE) < RATE_TOLERANCE
    assert result.monthly_equivalent_rate < Decimal("0")
    assert result.periods[0].projected_return == Decimal("-10.60")
    assert result.periods[0].ending_wealth == Decimal("1089.40")
    assert result.periods[1].opening_wealth == Decimal("1089.40")
    assert result.total_projected_growth < Decimal("0")


def test_negative_return_without_contribution_reduces_wealth():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(expected_return_rate=Decimal("-0.12"), horizon_months=3),
    )

    assert all(period.projected_return < Decimal("0") for period in result.periods)
    assert result.final_wealth < result.initial_wealth
    assert result.total_projected_growth < Decimal("0")


@pytest.mark.parametrize(
    ("return_type", "output_mode", "rate"),
    [
        (ReturnType.NOMINAL, OutputMode.NOMINAL, Decimal("0.12")),
        (ReturnType.REAL, OutputMode.REAL, Decimal("0.04")),
    ],
)
def test_direct_nominal_and_real_modes_preserve_supplied_annual_rate(
    return_type,
    output_mode,
    rate,
):
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(
            expected_return_rate=rate,
            return_type=return_type,
            output_mode=output_mode,
            horizon_months=1,
        ),
    )

    assert result.effective_projection_annual_rate == rate


def test_direct_annual_rate_disclosure_preserves_input_precision():
    precise_rate = Decimal(
        "0.123456789012345678901234567890123456789012345678901234567890"
        "123456789012345678901234567890"
    )
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(expected_return_rate=precise_rate, horizon_months=1),
    )

    assert result.effective_projection_annual_rate == precise_rate
    assert result.assumptions.expected_return_rate is precise_rate


def test_nominal_to_real_applies_fisher_once_and_uses_real_monthly_rate():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(
            expected_return_rate=Decimal("0.10"),
            return_type=ReturnType.NOMINAL,
            output_mode=OutputMode.REAL,
            inflation_rate=Decimal("0.05"),
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=12,
        ),
    )
    oracle = _independent_oracle(
        Decimal("1000.00"),
        Decimal("100.00"),
        FISHER_MONTHLY_RATE,
        12,
    )

    assert (
        abs(result.effective_projection_annual_rate - FISHER_ANNUAL_RATE)
        < RATE_TOLERANCE
    )
    assert abs(result.monthly_equivalent_rate - FISHER_MONTHLY_RATE) < RATE_TOLERANCE
    assert result.final_wealth == oracle[-1][2]
    assert result.total_projected_growth == oracle[-1][4]


def test_zero_nominal_return_with_positive_inflation_becomes_negative_real_growth():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(
            expected_return_rate=Decimal("0"),
            return_type=ReturnType.NOMINAL,
            output_mode=OutputMode.REAL,
            inflation_rate=Decimal("0.06"),
            horizon_months=2,
        ),
    )

    assert result.effective_projection_annual_rate < Decimal("0")
    assert result.monthly_equivalent_rate < Decimal("0")
    assert result.final_wealth < result.initial_wealth


def test_equal_nominal_return_and_inflation_resolve_to_exact_zero_real_rate():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(
            expected_return_rate=Decimal("0.10"),
            return_type=ReturnType.NOMINAL,
            output_mode=OutputMode.REAL,
            inflation_rate=Decimal("0.10"),
            horizon_months=1,
        ),
    )

    assert result.effective_projection_annual_rate == Decimal("0")
    assert result.monthly_equivalent_rate == Decimal("0")
    assert result.periods[0].projected_return == Decimal("0.00")


def test_deflation_increases_real_rate_without_second_adjustment():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(
            expected_return_rate=Decimal("0.03"),
            return_type=ReturnType.NOMINAL,
            output_mode=OutputMode.REAL,
            inflation_rate=Decimal("-0.02"),
            horizon_months=1,
        ),
    )

    assert result.effective_projection_annual_rate > Decimal("0.03")
    assert result.periods[0].projected_return == Decimal("4.16")


@pytest.mark.parametrize(
    "annual_rate",
    [Decimal("2.5"), Decimal("-0.999999999999999999")],
)
def test_extreme_valid_rates_project_without_float_or_complex_values(annual_rate):
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(expected_return_rate=annual_rate, horizon_months=2),
    )

    assert isinstance(result.monthly_equivalent_rate, Decimal)
    assert result.monthly_equivalent_rate > Decimal("-1")
    assert len(result.periods) == 2


def test_money_quantization_uses_round_half_even_at_ties():
    assert _quantize_money(Decimal("0.005")) == Decimal("0.00")
    assert _quantize_money(Decimal("0.015")) == Decimal("0.02")
    assert _quantize_money(Decimal("-0.015")) == Decimal("-0.02")


def test_every_period_reuses_cent_scale_closing_balance_and_satisfies_invariant():
    result = ForwardProjectionEngine().project(
        _initial_wealth("1234.56"),
        _assumptions(
            expected_return_rate=Decimal("0.12"),
            scenario_monthly_contribution=Decimal("78.90"),
        ),
    )

    for index, period in enumerate(result.periods):
        assert period.ending_wealth == (
            result.initial_wealth
            + period.cumulative_contributions
            + period.cumulative_projected_growth
        )
        assert period.ending_wealth.as_tuple().exponent >= -2
        if index:
            assert period.opening_wealth == result.periods[index - 1].ending_wealth


def test_horizon_one_has_one_based_period_and_matching_final_wealth():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(horizon_months=1),
    )

    assert len(result.periods) == 1
    assert result.periods[0].period == 1
    assert result.final_wealth == result.periods[0].ending_wealth


def test_supported_1200_month_horizon_is_iterative_and_complete():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(horizon_months=1200),
    )

    assert len(result.periods) == 1200
    assert result.periods[-1].period == 1200
    assert result.horizon_months == 1200


def test_precision_budget_grows_with_projection_magnitude():
    short_assumptions = _assumptions(
        expected_return_rate=Decimal("0.12"),
        horizon_months=12,
    )
    extreme_assumptions = _assumptions(
        expected_return_rate=Decimal("100"),
        horizon_months=1200,
    )

    short_precision = _estimate_working_precision(
        Decimal("1000.00"),
        short_assumptions,
    )
    extreme_precision = _estimate_working_precision(
        Decimal("1000.00"),
        extreme_assumptions,
    )

    assert short_precision == DECIMAL_CALCULATION_PRECISION
    assert extreme_precision > DECIMAL_CALCULATION_PRECISION
    assert extreme_precision > short_precision


def test_extreme_projection_matches_high_precision_oracle_through_1200_months():
    initial = _initial_wealth("1000.00")
    assumptions = _assumptions(
        expected_return_rate=Decimal("100"),
        horizon_months=1200,
    )
    engine = ForwardProjectionEngine()

    result = engine.project(initial, assumptions)
    repeated = engine.project(initial, assumptions)
    oracle_rate, oracle_periods = _independent_extreme_oracle(
        Decimal("1000.00"),
        Decimal("0.00"),
        Decimal("100"),
        1200,
    )

    assert result == repeated
    assert len(result.periods) == 1200
    assert result.final_wealth.is_finite()
    assert result.final_wealth.adjusted() + 1 > 200
    assert (
        abs(result.monthly_equivalent_rate - oracle_rate)
        < Decimal("1e-330")
    )

    for period_number in (1, 12, 120, 451, 452, 600, 1200):
        actual = result.periods[period_number - 1]
        expected = oracle_periods[period_number - 1]
        assert (
            actual.opening_wealth,
            actual.projected_return,
            actual.ending_wealth,
            actual.cumulative_contributions,
            actual.cumulative_projected_growth,
        ) == expected

    assert all(
        money.as_tuple().exponent == -2
        for period in result.periods
        for money in (
            period.opening_wealth,
            period.contribution,
            period.projected_return,
            period.ending_wealth,
            period.cumulative_contributions,
            period.cumulative_projected_growth,
        )
    )
    with localcontext() as invariant_context:
        invariant_context.prec = 500
        assert all(
            period.ending_wealth
            == (
                result.initial_wealth
                + period.cumulative_contributions
                + period.cumulative_projected_growth
            )
            for period in result.periods
        )
    assert result.final_wealth == oracle_periods[-1][2]
    assert result.total_projected_growth == oracle_periods[-1][4]


def test_extreme_projection_preserves_global_decimal_context():
    context_before = getcontext().copy()

    ForwardProjectionEngine().project(
        _initial_wealth("1000.00"),
        _assumptions(
            expected_return_rate=Decimal("100"),
            horizon_months=1200,
        ),
    )

    context_after = getcontext()
    assert context_after.prec == context_before.prec
    assert context_after.rounding == context_before.rounding
    assert context_after.Emax == context_before.Emax
    assert context_after.Emin == context_before.Emin
    assert context_after.clamp == context_before.clamp


def test_period_calendar_uses_real_month_ends_across_year_boundary():
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(horizon_months=4),
    )

    assert [period.period_end for period in result.periods] == [
        date(2026, 10, 31),
        date(2026, 11, 30),
        date(2026, 12, 31),
        date(2027, 1, 31),
    ]


@pytest.mark.parametrize(
    ("as_of_date", "expected_period_end"),
    [
        (date(2027, 1, 15), date(2027, 2, 28)),
        (date(2028, 1, 31), date(2028, 2, 29)),
    ],
)
def test_february_month_end_handles_normal_and_leap_years(
    as_of_date,
    expected_period_end,
):
    result = ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(as_of_date=as_of_date, horizon_months=1),
    )

    assert result.periods[0].period_end == expected_period_end


def test_target_date_horizon_uses_validated_resolved_month_count():
    assumptions = _assumptions(
        horizon_months=None,
        target_date=date(2027, 1, 1),
    )
    result = ForwardProjectionEngine().project(_initial_wealth(), assumptions)

    assert assumptions.resolved_horizon_months == 4
    assert len(result.periods) == 4
    assert result.horizon_months == 4


@pytest.mark.parametrize(
    ("source", "scope"),
    [
        (InitialWealthSource.GOAL_CURRENT_AMOUNT, InitialWealthScope.GOAL),
        (
            InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT,
            InitialWealthScope.INVESTMENT_PORTFOLIO,
        ),
        (
            InitialWealthSource.USER_PROVIDED_SCENARIO,
            InitialWealthScope.USER_PROVIDED_SCENARIO,
        ),
    ],
)
def test_result_preserves_each_explicit_source_scope_and_provenance(source, scope):
    initial = _initial_wealth(source=source, scope=scope)
    result = ForwardProjectionEngine().project(
        initial,
        _assumptions(horizon_months=1),
    )

    assert result.initial_wealth_fact is initial
    assert result.initial_wealth_fact.source is source
    assert result.initial_wealth_fact.scope is scope
    assert result.initial_wealth_fact.provenance is initial.provenance


def test_fact_as_of_and_projection_as_of_are_both_preserved_without_staleness_rule():
    initial = _initial_wealth(
        source=InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT,
        scope=InitialWealthScope.INVESTMENT_PORTFOLIO,
    )
    assumptions = _assumptions(as_of_date=date(2026, 10, 20), horizon_months=1)
    result = ForwardProjectionEngine().project(initial, assumptions)

    assert result.initial_wealth_fact.as_of.reference_month == "2026-09"
    assert result.as_of_date == date(2026, 10, 20)


@pytest.mark.parametrize(
    ("amount", "message"),
    [
        (Decimal("NaN"), "must be finite"),
        (Decimal("Infinity"), "must be finite"),
        (Decimal("-0.01"), "cannot be negative"),
        (Decimal("1000.001"), "at most two decimal places"),
    ],
)
def test_engine_rejects_invalid_initial_wealth_not_guarded_by_fact(amount, message):
    with pytest.raises(ValueError, match=message):
        ForwardProjectionEngine().project(
            _initial_wealth(amount),
            _assumptions(horizon_months=1),
        )


def test_engine_rejects_float_if_fact_boundary_is_bypassed():
    initial = _initial_wealth()
    object.__setattr__(initial, "amount", 1000.0)

    with pytest.raises(TypeError, match="must be Decimal"):
        ForwardProjectionEngine().project(initial, _assumptions(horizon_months=1))


def test_inputs_results_periods_and_collection_are_immutable():
    initial = _initial_wealth()
    assumptions = _assumptions(horizon_months=1)
    result = ForwardProjectionEngine().project(initial, assumptions)

    assert isinstance(result.periods, tuple)
    assert result.initial_wealth_fact is initial
    assert result.assumptions is assumptions
    with pytest.raises(FrozenInstanceError):
        result.final_wealth = Decimal("0.00")
    with pytest.raises(FrozenInstanceError):
        result.periods[0].ending_wealth = Decimal("0.00")


def test_projection_does_not_change_global_decimal_context():
    precision_before = getcontext().prec
    rounding_before = getcontext().rounding

    ForwardProjectionEngine().project(
        _initial_wealth(),
        _assumptions(expected_return_rate=Decimal("0.12"), horizon_months=1),
    )

    assert getcontext().prec == precision_before
    assert getcontext().rounding == rounding_before


def test_result_types_contain_only_approved_projection_fields():
    assert [field.name for field in fields(ProjectionPeriod)] == [
        "period",
        "period_end",
        "opening_wealth",
        "contribution",
        "projected_return",
        "ending_wealth",
        "cumulative_contributions",
        "cumulative_projected_growth",
    ]
