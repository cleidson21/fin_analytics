from dataclasses import FrozenInstanceError, fields
from datetime import date, datetime
from decimal import Decimal

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
    ReturnType,
    TargetAchievementResult,
    TargetAchievementSolver,
    TargetAchievementStatus,
)


def _initial_wealth(
    amount: str = "1000.00",
    source: InitialWealthSource = InitialWealthSource.USER_PROVIDED_SCENARIO,
    scope: InitialWealthScope = InitialWealthScope.USER_PROVIDED_SCENARIO,
) -> InitialWealthFact:
    return InitialWealthFact(
        source=source,
        amount=Decimal(amount),
        as_of=PlanningFactAsOf(observed_at=datetime(2026, 9, 16, 12, 0, 0)),
        scope=scope,
        provenance=PlanningFactProvenance(
            source_table="planning_request",
            source_type=source.value,
        ),
    )


def _assumptions(**overrides) -> ProjectionAssumptions:
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


class _CountingProjectionEngine(ForwardProjectionEngine):
    def __init__(self) -> None:
        self.calls = 0

    def project(self, initial_wealth_fact, assumptions):
        self.calls += 1
        return super().project(initial_wealth_fact, assumptions)


@pytest.mark.parametrize("initial", ["1000.00", "1500.00"])
def test_already_achieved_uses_period_zero_without_projection(initial):
    engine = _CountingProjectionEngine()
    fact = _initial_wealth(initial)
    assumptions = _assumptions()

    result = TargetAchievementSolver(engine).solve(
        fact,
        assumptions,
        Decimal("1000.00"),
    )

    assert result.status is TargetAchievementStatus.ALREADY_ACHIEVED
    assert result.achievement_period == 0
    assert result.achievement_date == assumptions.as_of_date
    assert result.months_required == 0
    assert result.achieved_wealth == fact.amount
    assert result.projection_result is None
    assert engine.calls == 0


def test_exact_target_is_achieved_in_first_month_with_end_of_month_contribution():
    result = TargetAchievementSolver().solve(
        _initial_wealth("900.00"),
        _assumptions(
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=3,
        ),
        Decimal("1000.00"),
    )

    assert result.status is TargetAchievementStatus.ACHIEVED
    assert result.achievement_period == 1
    assert result.months_required == 1
    assert result.achievement_date == date(2026, 10, 31)
    assert result.achieved_wealth == Decimal("1000.00")


def test_first_overshoot_is_returned_instead_of_later_crossings():
    result = TargetAchievementSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=6,
        ),
        Decimal("1250.00"),
    )

    assert result.status is TargetAchievementStatus.ACHIEVED
    assert result.achievement_period == 3
    assert result.months_required == 3
    assert result.achievement_date == date(2026, 12, 31)
    assert result.achieved_wealth == Decimal("1300.00")
    assert result.projection_result.periods[-1].ending_wealth == Decimal("1600.00")


def test_positive_return_first_crossing_matches_independent_known_values():
    result = TargetAchievementSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(expected_return_rate=Decimal("0.12"), horizon_months=3),
        Decimal("1019.00"),
    )

    assert [period.ending_wealth for period in result.projection_result.periods[:2]] == [
        Decimal("1009.49"),
        Decimal("1019.07"),
    ]
    assert result.status is TargetAchievementStatus.ACHIEVED
    assert result.achievement_period == 2
    assert result.achieved_wealth == Decimal("1019.07")


def test_negative_return_does_not_imply_unreachable_when_contributions_cross_target():
    result = TargetAchievementSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(
            expected_return_rate=Decimal("-0.12"),
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=2,
        ),
        Decimal("1089.40"),
    )

    assert result.status is TargetAchievementStatus.ACHIEVED
    assert result.achievement_period == 1
    assert result.achieved_wealth == Decimal("1089.40")


def test_zero_contribution_positive_return_can_reach_target():
    result = TargetAchievementSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(expected_return_rate=Decimal("0.12"), horizon_months=3),
        Decimal("1019.00"),
    )

    assert result.status is TargetAchievementStatus.ACHIEVED
    assert result.achievement_period == 2


@pytest.mark.parametrize("annual_rate", [Decimal("0"), Decimal("-0.12")])
def test_zero_contribution_non_positive_return_is_proven_unreachable(annual_rate):
    result = TargetAchievementSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(expected_return_rate=annual_rate, horizon_months=3),
        Decimal("1000.01"),
    )

    assert result.status is TargetAchievementStatus.UNREACHABLE
    assert result.achievement_period is None
    assert result.achievement_date is None
    assert result.months_required is None
    assert result.achieved_wealth is None


def test_zero_initial_and_contribution_are_unreachable_even_with_positive_return():
    result = TargetAchievementSolver().solve(
        _initial_wealth("0.00"),
        _assumptions(expected_return_rate=Decimal("2.5"), horizon_months=3),
        Decimal("0.01"),
    )

    assert result.status is TargetAchievementStatus.UNREACHABLE
    assert result.projection_result.final_wealth == Decimal("0.00")


@pytest.mark.parametrize("horizon", [1, 3, 1200])
def test_growing_path_beyond_horizon_is_not_called_unreachable(horizon):
    result = TargetAchievementSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(
            scenario_monthly_contribution=Decimal("0.01"),
            horizon_months=horizon,
        ),
        Decimal("999999.00"),
    )

    assert result.status is TargetAchievementStatus.NOT_REACHED_WITHIN_HORIZON
    assert result.projection_result.horizon_months == horizon


def test_target_date_horizon_uses_projection_period_end_as_authority():
    result = TargetAchievementSolver().solve(
        _initial_wealth("900.00"),
        _assumptions(
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=None,
            target_date=date(2026, 12, 1),
        ),
        Decimal("1200.00"),
    )

    assert result.status is TargetAchievementStatus.ACHIEVED
    assert result.achievement_period == 3
    assert result.achievement_date == date(2026, 12, 31)
    assert result.achievement_date == result.projection_result.periods[2].period_end


def test_nominal_to_real_target_is_compared_in_projection_output_basis_only():
    result = TargetAchievementSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(
            expected_return_rate=Decimal("0.10"),
            return_type=ReturnType.NOMINAL,
            output_mode=OutputMode.REAL,
            inflation_rate=Decimal("0.05"),
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=1,
        ),
        Decimal("1103.00"),
    )

    assert result.status is TargetAchievementStatus.ACHIEVED
    assert result.achieved_wealth == Decimal("1103.88")
    assert result.target_amount == Decimal("1103.00")


def test_large_magnitude_target_remains_exact_decimal():
    initial = Decimal("9" * 220 + ".00")
    target = initial + Decimal("1.00")
    result = TargetAchievementSolver().solve(
        _initial_wealth(str(initial)),
        _assumptions(
            scenario_monthly_contribution=Decimal("1.00"),
            horizon_months=1,
        ),
        target,
    )

    assert result.status is TargetAchievementStatus.ACHIEVED
    assert result.achieved_wealth == target
    assert isinstance(result.achieved_wealth, Decimal)
    assert result.achieved_wealth.adjusted() + 1 == 221


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
def test_source_changes_provenance_but_not_target_math(source, scope):
    result = TargetAchievementSolver().solve(
        _initial_wealth("900.00", source, scope),
        _assumptions(
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=2,
        ),
        Decimal("1000.00"),
    )

    assert result.status is TargetAchievementStatus.ACHIEVED
    assert result.achievement_period == 1
    assert result.achieved_wealth == Decimal("1000.00")
    assert result.initial_wealth_fact.source is source
    assert result.initial_wealth_fact.scope is scope


def test_solver_executes_one_complete_projection_for_non_initial_target():
    engine = _CountingProjectionEngine()
    result = TargetAchievementSolver(engine).solve(
        _initial_wealth("900.00"),
        _assumptions(
            scenario_monthly_contribution=Decimal("100.00"),
            horizon_months=12,
        ),
        Decimal("1000.00"),
    )

    assert result.status is TargetAchievementStatus.ACHIEVED
    assert len(result.projection_result.periods) == 12
    assert engine.calls == 1


@pytest.mark.parametrize(
    ("target", "exception", "message"),
    [
        (1000, TypeError, "must be Decimal"),
        (1000.0, TypeError, "must be Decimal"),
        (True, TypeError, "must be Decimal"),
        ("1000.00", TypeError, "must be Decimal"),
        (Decimal("NaN"), ValueError, "must be finite"),
        (Decimal("Infinity"), ValueError, "must be finite"),
        (Decimal("-Infinity"), ValueError, "must be finite"),
        (Decimal("0.00"), ValueError, "greater than zero"),
        (Decimal("-0.01"), ValueError, "greater than zero"),
        (Decimal("1000.001"), ValueError, "at most two decimal places"),
    ],
)
def test_invalid_target_is_rejected_without_silent_coercion(target, exception, message):
    with pytest.raises(exception, match=message):
        TargetAchievementSolver().solve(
            _initial_wealth(),
            _assumptions(),
            target,
        )


def test_result_is_immutable_deterministic_and_preserves_input_references():
    fact = _initial_wealth("900.00")
    assumptions = _assumptions(
        scenario_monthly_contribution=Decimal("100.00"),
        horizon_months=2,
    )
    solver = TargetAchievementSolver()

    first = solver.solve(fact, assumptions, Decimal("1000.00"))
    second = solver.solve(fact, assumptions, Decimal("1000.00"))

    assert first == second
    assert first.initial_wealth_fact is fact
    assert first.assumptions is assumptions
    assert first.projection_result.initial_wealth_fact is fact
    assert first.projection_result.assumptions is assumptions
    with pytest.raises(FrozenInstanceError):
        first.status = TargetAchievementStatus.UNREACHABLE


def test_result_type_contains_only_target_solver_fields():
    assert [field.name for field in fields(TargetAchievementResult)] == [
        "status",
        "target_amount",
        "initial_wealth_fact",
        "assumptions",
        "achievement_period",
        "achievement_date",
        "months_required",
        "achieved_wealth",
        "projection_result",
    ]
