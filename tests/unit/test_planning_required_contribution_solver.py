from dataclasses import FrozenInstanceError, fields, replace
from datetime import date, datetime
from decimal import Decimal

import pytest

from backend.domains.planning import (
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    OutputMode,
    PlanningFactAsOf,
    PlanningFactProvenance,
    ProjectionAssumptions,
    RequiredContributionResult,
    RequiredContributionSolver,
    RequiredContributionStatus,
    ReturnType,
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
        "scenario_monthly_contribution": Decimal("777.77"),
        "expected_return_rate": Decimal("0"),
        "return_type": ReturnType.NOMINAL,
        "output_mode": OutputMode.NOMINAL,
        "horizon_months": 3,
    }
    values.update(overrides)
    return ProjectionAssumptions(**values)


def _reaches_target(result) -> bool:
    return result.status in {
        TargetAchievementStatus.ALREADY_ACHIEVED,
        TargetAchievementStatus.ACHIEVED,
    }


def _brute_force_cents(
    fact: InitialWealthFact,
    assumptions: ProjectionAssumptions,
    target: Decimal,
    maximum_cents: int,
) -> Decimal:
    target_solver = TargetAchievementSolver()
    for cents in range(maximum_cents + 1):
        contribution = Decimal((0, Decimal(cents).as_tuple().digits, -2))
        candidate = replace(
            assumptions,
            scenario_monthly_contribution=contribution,
        )
        if _reaches_target(target_solver.solve(fact, candidate, target)):
            return contribution
    raise AssertionError("brute-force test oracle did not find a solution")


class _CountingTargetSolver(TargetAchievementSolver):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def solve(self, initial_wealth_fact, assumptions, target_amount):
        self.calls += 1
        return super().solve(initial_wealth_fact, assumptions, target_amount)


@pytest.mark.parametrize("initial", ["1000.00", "1500.00"])
def test_already_achieved_requires_zero_without_binary_search(initial):
    counting_solver = _CountingTargetSolver()
    template = _assumptions(scenario_monthly_contribution=Decimal("999.99"))

    result = RequiredContributionSolver(counting_solver).solve(
        _initial_wealth(initial),
        template,
        Decimal("1000.00"),
    )

    assert result.status is RequiredContributionStatus.ALREADY_ACHIEVED
    assert result.required_monthly_contribution == Decimal("0.00")
    assert result.solved_assumptions.scenario_monthly_contribution == Decimal("0.00")
    assert result.target_achievement_result.status is TargetAchievementStatus.ALREADY_ACHIEVED
    assert result.target_achievement_result.achievement_period == 0
    assert result.target_achievement_result.projection_result is None
    assert result.assumptions_template is template
    assert counting_solver.calls == 1


def test_zero_contribution_required_is_resolved_before_binary_search():
    counting_solver = _CountingTargetSolver()
    result = RequiredContributionSolver(counting_solver).solve(
        _initial_wealth("1000.00"),
        _assumptions(
            scenario_monthly_contribution=Decimal("999.99"),
            expected_return_rate=Decimal("0.12"),
            horizon_months=12,
        ),
        Decimal("1100.00"),
    )

    assert result.status is RequiredContributionStatus.ZERO_CONTRIBUTION_REQUIRED
    assert result.required_monthly_contribution == Decimal("0.00")
    assert result.target_achievement_result.status is TargetAchievementStatus.ACHIEVED
    assert result.target_achievement_result.assumptions is result.solved_assumptions
    assert counting_solver.calls == 1


def test_zero_rate_has_simple_exact_required_contribution():
    result = RequiredContributionSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(),
        Decimal("1300.00"),
    )

    assert result.status is RequiredContributionStatus.SOLVED
    assert result.required_monthly_contribution == Decimal("100.00")
    assert result.target_achievement_result.achievement_period == 3
    assert result.target_achievement_result.achieved_wealth == Decimal("1300.00")


def test_smallest_cent_is_returned_when_fractional_average_is_required():
    result = RequiredContributionSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(horizon_months=2),
        Decimal("1000.03"),
    )

    assert result.required_monthly_contribution == Decimal("0.02")
    previous = TargetAchievementSolver().solve(
        result.initial_wealth_fact,
        replace(
            result.solved_assumptions,
            scenario_monthly_contribution=Decimal("0.01"),
        ),
        result.target_amount,
    )
    assert result.target_achievement_result.status is TargetAchievementStatus.ACHIEVED
    assert not _reaches_target(previous)


@pytest.mark.parametrize(
    ("annual_rate", "expected"),
    [
        ("0.12", "89.57"),
        ("-0.5", "161.96"),
        ("-0.999999", "895.60"),
    ],
)
def test_positive_negative_and_near_minus_one_rates_are_cent_minimal(
    annual_rate,
    expected,
):
    result = RequiredContributionSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(expected_return_rate=Decimal(annual_rate)),
        Decimal("1300.00"),
    )

    assert result.required_monthly_contribution == Decimal(expected)
    assert result.target_achievement_result.status is TargetAchievementStatus.ACHIEVED


def test_solver_respects_end_of_month_contribution_timing():
    result = RequiredContributionSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(
            expected_return_rate=Decimal("0.12"),
            horizon_months=1,
        ),
        Decimal("1110.00"),
    )
    period = result.target_achievement_result.projection_result.periods[0]

    assert period.projected_return == Decimal("9.49")
    assert result.required_monthly_contribution == Decimal("100.51")
    assert period.ending_wealth == Decimal("1110.00")


def test_half_even_sensitive_case_keeps_cent_minimal_result():
    annual_rate = Decimal("1.005") ** Decimal("12") - Decimal("1")
    result = RequiredContributionSolver().solve(
        _initial_wealth("1.00"),
        _assumptions(
            expected_return_rate=annual_rate,
            horizon_months=1,
        ),
        Decimal("1.01"),
    )
    period = result.target_achievement_result.projection_result.periods[0]

    assert period.projected_return == Decimal("0.00")
    assert result.required_monthly_contribution == Decimal("0.01")


def test_target_date_template_reuses_resolved_horizon():
    result = RequiredContributionSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(horizon_months=None, target_date=date(2026, 12, 1)),
        Decimal("1300.00"),
    )

    assert result.required_monthly_contribution == Decimal("100.00")
    assert result.solved_assumptions.target_date == date(2026, 12, 1)
    assert result.solved_assumptions.resolved_horizon_months == 3


@pytest.mark.parametrize(
    ("return_type", "output_mode", "expected_return", "inflation"),
    [
        (ReturnType.NOMINAL, OutputMode.REAL, "0.08", "0.03"),
        (ReturnType.REAL, OutputMode.REAL, "0.04", None),
    ],
)
def test_real_output_modes_match_small_independent_brute_force_oracle(
    return_type,
    output_mode,
    expected_return,
    inflation,
):
    fact = _initial_wealth("100.00")
    template = _assumptions(
        expected_return_rate=Decimal(expected_return),
        return_type=return_type,
        output_mode=output_mode,
        inflation_rate=None if inflation is None else Decimal(inflation),
        horizon_months=2,
    )
    target = Decimal("102.00")

    result = RequiredContributionSolver().solve(fact, template, target)
    brute = _brute_force_cents(fact, template, target, maximum_cents=200)

    assert result.required_monthly_contribution == brute
    assert result.solved_assumptions.return_type is return_type
    assert result.solved_assumptions.output_mode is output_mode


def test_template_contribution_is_ignored_and_all_other_fields_are_preserved():
    first_template = _assumptions(scenario_monthly_contribution=Decimal("0.00"))
    second_template = _assumptions(scenario_monthly_contribution=Decimal("99999.99"))
    solver = RequiredContributionSolver()

    first = solver.solve(_initial_wealth(), first_template, Decimal("1300.00"))
    second = solver.solve(_initial_wealth(), second_template, Decimal("1300.00"))

    assert first.required_monthly_contribution == second.required_monthly_contribution
    assert first.required_monthly_contribution == Decimal("100.00")
    assert first.assumptions_template is first_template
    assert second.assumptions_template is second_template
    assert replace(
        first.solved_assumptions,
        scenario_monthly_contribution=second.solved_assumptions.scenario_monthly_contribution,
    ) == second.solved_assumptions


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
def test_source_changes_provenance_but_not_required_contribution(source, scope):
    result = RequiredContributionSolver().solve(
        _initial_wealth(source=source, scope=scope),
        _assumptions(),
        Decimal("1300.00"),
    )

    assert result.required_monthly_contribution == Decimal("100.00")
    assert result.initial_wealth_fact.source is source
    assert result.target_achievement_result.initial_wealth_fact is result.initial_wealth_fact


def test_large_decimal_magnitude_is_searched_without_float_conversion():
    initial = "1" + "0" * 100 + ".00"
    target = Decimal("1" + "0" * 97 + "300.00")
    result = RequiredContributionSolver().solve(
        _initial_wealth(initial),
        _assumptions(),
        target,
    )

    assert result.required_monthly_contribution == Decimal("100.00")
    assert result.target_achievement_result.achieved_wealth == target
    assert len(str(target).split(".")[0]) > 80


@pytest.mark.parametrize("annual_rate", ["0.12", "0", "-0.1", "-0.75", "-0.999999"])
def test_target_predicate_is_monotonic_over_fixed_contribution_grid(annual_rate):
    fact = _initial_wealth("100.00")
    template = _assumptions(
        expected_return_rate=Decimal(annual_rate),
        horizon_months=3,
    )
    target = Decimal("130.00")
    target_solver = TargetAchievementSolver()
    outcomes = []

    for whole_units in range(0, 151, 15):
        candidate = replace(
            template,
            scenario_monthly_contribution=Decimal(whole_units).quantize(Decimal("0.00")),
        )
        outcomes.append(_reaches_target(target_solver.solve(fact, candidate, target)))

    assert outcomes == sorted(outcomes)
    assert outcomes[0] is False
    assert outcomes[-1] is True


@pytest.mark.parametrize(
    ("annual_rate", "initial", "target", "horizon", "maximum_cents"),
    [
        ("0", "10.00", "10.07", 3, 10),
        ("0.12", "10.00", "10.50", 2, 50),
        ("-0.5", "10.00", "11.00", 2, 200),
    ],
)
def test_binary_search_matches_small_brute_force_cent_oracle(
    annual_rate,
    initial,
    target,
    horizon,
    maximum_cents,
):
    fact = _initial_wealth(initial)
    template = _assumptions(
        expected_return_rate=Decimal(annual_rate),
        horizon_months=horizon,
    )
    target_amount = Decimal(target)

    result = RequiredContributionSolver().solve(fact, template, target_amount)
    brute = _brute_force_cents(
        fact,
        template,
        target_amount,
        maximum_cents=maximum_cents,
    )

    assert result.required_monthly_contribution == brute


def test_binary_search_uses_logarithmic_number_of_target_solves():
    counting_solver = _CountingTargetSolver()
    result = RequiredContributionSolver(counting_solver).solve(
        _initial_wealth("0.00"),
        _assumptions(horizon_months=12),
        Decimal("1000000.00"),
    )

    assert result.status is RequiredContributionStatus.SOLVED
    assert counting_solver.calls <= 32


def test_final_result_explicitly_satisfies_c_and_rejects_previous_cent():
    result = RequiredContributionSolver().solve(
        _initial_wealth("1000.00"),
        _assumptions(expected_return_rate=Decimal("-0.5"), horizon_months=12),
        Decimal("1500.00"),
    )
    previous_assumptions = replace(
        result.solved_assumptions,
        scenario_monthly_contribution=(
            result.required_monthly_contribution - Decimal("0.01")
        ),
    )
    previous = TargetAchievementSolver().solve(
        result.initial_wealth_fact,
        previous_assumptions,
        result.target_amount,
    )

    assert _reaches_target(result.target_achievement_result)
    assert not _reaches_target(previous)


@pytest.mark.parametrize(
    ("target", "exception"),
    [
        (Decimal("0"), ValueError),
        (Decimal("-0.01"), ValueError),
        (Decimal("1.000"), ValueError),
        (Decimal("NaN"), ValueError),
        (Decimal("Infinity"), ValueError),
        (1, TypeError),
        (1.0, TypeError),
        (True, TypeError),
        ("1.00", TypeError),
        (None, TypeError),
    ],
)
def test_target_contract_is_reused_without_silent_coercion(target, exception):
    with pytest.raises(exception):
        RequiredContributionSolver().solve(
            _initial_wealth(),
            _assumptions(),
            target,
        )


def test_result_is_immutable_deterministic_and_preserves_nested_audit_trail():
    fact = _initial_wealth()
    template = _assumptions(expected_return_rate=Decimal("0.12"))
    solver = RequiredContributionSolver()

    first = solver.solve(fact, template, Decimal("1300.00"))
    second = solver.solve(fact, template, Decimal("1300.00"))

    assert first == second
    assert first.initial_wealth_fact is fact
    assert first.assumptions_template is template
    assert first.target_achievement_result.assumptions is first.solved_assumptions
    with pytest.raises(FrozenInstanceError):
        first.required_monthly_contribution = Decimal("0.00")


def test_result_contract_and_status_enum_are_complete_without_extra_outputs():
    assert {field.name for field in fields(RequiredContributionResult)} == {
        "status",
        "target_amount",
        "initial_wealth_fact",
        "assumptions_template",
        "required_monthly_contribution",
        "solved_assumptions",
        "target_achievement_result",
    }
    assert set(RequiredContributionStatus) == {
        RequiredContributionStatus.ALREADY_ACHIEVED,
        RequiredContributionStatus.ZERO_CONTRIBUTION_REQUIRED,
        RequiredContributionStatus.SOLVED,
        RequiredContributionStatus.IMPOSSIBLE_HORIZON,
        RequiredContributionStatus.OUT_OF_SUPPORTED_RANGE,
    }
