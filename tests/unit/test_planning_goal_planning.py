from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domains.planning import (
    GoalPlanningFact,
    GoalPlanningResult,
    GoalPlanningService,
    GoalPlanningStatus,
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
    TargetValueBasis,
)


GOAL_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_GOAL_ID = UUID("22222222-2222-2222-2222-222222222222")
USER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _goal(**overrides) -> GoalPlanningFact:
    values = {
        "goal_id": GOAL_ID,
        "user_id": USER_ID,
        "name": "Reserva",
        "description": None,
        "goal_type": GoalType.EMERGENCY_RESERVE,
        "status": GoalStatus.ACTIVE,
        "target_amount": Decimal("900.00"),
        "target_date": date(2027, 6, 15),
        "current_amount": Decimal("0.00"),
        "goal_planned_monthly_contribution": Decimal("100.00"),
        "priority": 1,
        "linked_account_id": None,
        "created_at": datetime(2026, 1, 1, 9, 0, 0),
        "updated_at": datetime(2026, 9, 16, 9, 0, 0),
    }
    values.update(overrides)
    return GoalPlanningFact(**values)


def _initial_wealth(
    amount: str = "0.00",
    source: InitialWealthSource = InitialWealthSource.USER_PROVIDED_SCENARIO,
    source_goal_id: UUID | None = None,
) -> InitialWealthFact:
    scope = {
        InitialWealthSource.GOAL_CURRENT_AMOUNT: InitialWealthScope.GOAL,
        InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT:
            InitialWealthScope.INVESTMENT_PORTFOLIO,
        InitialWealthSource.USER_PROVIDED_SCENARIO:
            InitialWealthScope.USER_PROVIDED_SCENARIO,
    }[source]
    return InitialWealthFact(
        source=source,
        amount=Decimal(amount),
        as_of=PlanningFactAsOf(observed_at=datetime(2026, 9, 16, 12, 0, 0)),
        scope=scope,
        provenance=PlanningFactProvenance(
            source_table={
                InitialWealthSource.GOAL_CURRENT_AMOUNT: "goals",
                InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT:
                    "portfolio_snapshots",
                InitialWealthSource.USER_PROVIDED_SCENARIO: "planning_request",
            }[source],
            source_type=source.value,
            goal_id=source_goal_id,
            account_id=(
                "account-a"
                if source is InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT
                else None
            ),
        ),
    )


def _assumptions(**overrides) -> ProjectionAssumptions:
    values = {
        "as_of_date": date(2026, 9, 16),
        "scenario_monthly_contribution": Decimal("100.00"),
        "expected_return_rate": Decimal("0"),
        "return_type": ReturnType.NOMINAL,
        "output_mode": OutputMode.NOMINAL,
        "horizon_months": 12,
    }
    values.update(overrides)
    return ProjectionAssumptions(**values)


class _CountingTargetSolver(TargetAchievementSolver):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def solve(self, initial_wealth_fact, assumptions, target_amount):
        self.calls += 1
        return super().solve(initial_wealth_fact, assumptions, target_amount)


class _StubTargetSolver:
    def __init__(self, result: TargetAchievementResult) -> None:
        self.result = result
        self.calls = 0

    def solve(self, initial_wealth_fact, assumptions, target_amount):
        self.calls += 1
        return self.result


def _stub_achievement(
    achievement_date: date,
    goal: GoalPlanningFact,
    initial: InitialWealthFact,
    assumptions: ProjectionAssumptions,
) -> TargetAchievementResult:
    return TargetAchievementResult(
        status=TargetAchievementStatus.ACHIEVED,
        target_amount=goal.target_amount,
        initial_wealth_fact=initial,
        assumptions=assumptions,
        achievement_period=1,
        achievement_date=achievement_date,
        months_required=1,
        achieved_wealth=goal.target_amount,
        projection_result=None,
    )


@pytest.mark.parametrize(
    "goal_type",
    [
        GoalType.EMERGENCY_RESERVE,
        GoalType.TRAVEL,
        GoalType.PURCHASE,
        GoalType.CUSTOM,
        GoalType.WEALTH_TARGET,
        GoalType.INVESTMENT_TARGET,
    ],
)
def test_all_approved_generic_goal_types_use_the_same_planning_path(goal_type):
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(goal_type=goal_type),
        _initial_wealth(),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.PROJECTED_ON_TIME
    assert solver.calls == 1


@pytest.mark.parametrize(
    "goal_type",
    [GoalType.RETIREMENT, GoalType.FINANCIAL_INDEPENDENCE, GoalType.DIVIDEND_INCOME],
)
def test_reserved_goal_types_are_not_applicable_without_solver_call(goal_type):
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(goal_type=goal_type),
        _initial_wealth(),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_achievement_result is None
    assert solver.calls == 0


def test_applicability_preflight_returns_not_applicable_without_financial_fact():
    service = GoalPlanningService()

    result = service.preflight_applicability(
        _goal(status=GoalStatus.ACHIEVED, current_amount=None),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result is not None
    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.initial_wealth_fact is None
    assert result.target_achievement_result is None


def test_applicability_preflight_requires_fact_resolution_for_active_goal():
    result = GoalPlanningService().preflight_applicability(
        _goal(status=GoalStatus.ACTIVE, current_amount=None),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result is None


@pytest.mark.parametrize("goal_status", tuple(GoalStatus))
@pytest.mark.parametrize("goal_type", tuple(GoalType))
def test_preflight_and_evaluate_share_one_applicability_rule(
    goal_status,
    goal_type,
):
    """Every real enum pair has one lifecycle/type applicability decision."""

    approved_generic_types = {
        GoalType.EMERGENCY_RESERVE,
        GoalType.TRAVEL,
        GoalType.PURCHASE,
        GoalType.CUSTOM,
        GoalType.WEALTH_TARGET,
        GoalType.INVESTMENT_TARGET,
    }
    expected_projectable = (
        goal_status is GoalStatus.ACTIVE and goal_type in approved_generic_types
    )
    solver = _CountingTargetSolver()
    service = GoalPlanningService(solver)
    goal = _goal(status=goal_status, goal_type=goal_type)
    assumptions = _assumptions()
    initial = _initial_wealth()

    preflight = service.preflight_applicability(
        goal,
        assumptions,
        TargetValueBasis.NOMINAL,
    )
    result = service.evaluate(
        goal,
        initial,
        assumptions,
        TargetValueBasis.NOMINAL,
    )

    if expected_projectable:
        assert preflight is None
        assert result.status is not GoalPlanningStatus.NOT_APPLICABLE
        assert result.initial_wealth_fact is initial
        assert solver.calls == 1
    else:
        assert preflight is not None
        assert preflight.status is GoalPlanningStatus.NOT_APPLICABLE
        assert preflight.initial_wealth_fact is None
        assert result.status is GoalPlanningStatus.NOT_APPLICABLE
        assert result.target_achievement_result is None
        assert solver.calls == 0


def test_reserved_goal_with_missing_basis_is_still_not_applicable():
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(goal_type=GoalType.RETIREMENT),
        _initial_wealth(),
        _assumptions(),
        None,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert solver.calls == 0


@pytest.mark.parametrize(
    "goal_type",
    [GoalType.RETIREMENT, GoalType.FINANCIAL_INDEPENDENCE, GoalType.DIVIDEND_INCOME],
)
def test_reserved_goal_with_basis_mismatch_is_not_applicable_without_solver_call(
    goal_type,
):
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(goal_type=goal_type),
        _initial_wealth(),
        _assumptions(
            return_type=ReturnType.NOMINAL,
            output_mode=OutputMode.REAL,
            inflation_rate=Decimal("0.04"),
        ),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_achievement_result is None
    assert solver.calls == 0


@pytest.mark.parametrize("goal_status", [GoalStatus.PAUSED, GoalStatus.CANCELLED])
def test_paused_and_cancelled_goals_are_not_applicable(goal_status):
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(status=goal_status),
        _initial_wealth(),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_achievement_result is None
    assert solver.calls == 0


@pytest.mark.parametrize(
    "goal_status",
    [GoalStatus.ACHIEVED, GoalStatus.PAUSED, GoalStatus.CANCELLED],
)
def test_non_active_goal_with_basis_mismatch_is_not_applicable_without_solver_call(
    goal_status,
):
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(status=goal_status),
        _initial_wealth(),
        _assumptions(
            return_type=ReturnType.NOMINAL,
            output_mode=OutputMode.REAL,
            inflation_rate=Decimal("0.04"),
        ),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_achievement_result is None
    assert solver.calls == 0


@pytest.mark.parametrize(
    "goal_override",
    [
        {"status": GoalStatus.ACHIEVED},
        {"status": GoalStatus.PAUSED},
        {"status": GoalStatus.CANCELLED},
        {"goal_type": GoalType.RETIREMENT},
    ],
)
def test_non_projectable_goal_does_not_consume_cross_goal_provenance(goal_override):
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(**goal_override),
        _initial_wealth(
            source=InitialWealthSource.GOAL_CURRENT_AMOUNT,
            source_goal_id=OTHER_GOAL_ID,
        ),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_achievement_result is None
    assert solver.calls == 0


# ---------------------------------------------------------------------------
# TSK-10.3.5-R — GoalStatus.ACHIEVED eligibility contract
# GoalStatus.ACHIEVED is a lifecycle/manual fact.  It is NOT_APPLICABLE for
# forward Planning regardless of current_amount, target, basis, or deadline.
# GoalPlanningStatus.ALREADY_ACHIEVED is a mathematical result and may only
# arise for GoalStatus.ACTIVE goals via TargetAchievementSolver.
# ---------------------------------------------------------------------------


# Test A — ACHIEVED + initial below target → NOT_APPLICABLE, solver 0 calls
def test_achieved_goal_with_initial_below_target_is_not_applicable():
    """Persisted ACHIEVED must not be re-projected even when initial < target."""
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(status=GoalStatus.ACHIEVED, target_amount=Decimal("900.00")),
        _initial_wealth("0.00"),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_achievement_result is None
    assert solver.calls == 0


# Test B — ACHIEVED + initial equal target → NOT_APPLICABLE, solver 0 calls
def test_achieved_goal_with_initial_equal_target_is_not_applicable():
    """Persisted ACHIEVED must not be converted to ALREADY_ACHIEVED."""
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(status=GoalStatus.ACHIEVED, target_amount=Decimal("900.00")),
        _initial_wealth("900.00"),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_achievement_result is None
    assert solver.calls == 0


# Test C — ACHIEVED + initial above target → NOT_APPLICABLE, solver 0 calls
def test_achieved_goal_with_initial_above_target_is_not_applicable():
    """Persisted ACHIEVED must not be converted to ALREADY_ACHIEVED even when initial > target."""
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(status=GoalStatus.ACHIEVED, target_amount=Decimal("900.00")),
        _initial_wealth("9999.00"),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_achievement_result is None
    assert solver.calls == 0


# Test D — ACHIEVED + missing basis → NOT_APPLICABLE (not INSUFFICIENT_DATA)
def test_achieved_goal_with_missing_basis_is_not_applicable_not_insufficient():
    """ACHIEVED gate fires before basis check; basis absence must not change outcome."""
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(status=GoalStatus.ACHIEVED),
        _initial_wealth(),
        _assumptions(),
        None,  # missing basis
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_value_basis is None
    assert result.target_achievement_result is None
    assert solver.calls == 0


# Test E — ACHIEVED + missing deadline → NOT_APPLICABLE
def test_achieved_goal_with_missing_deadline_is_not_applicable():
    """ACHIEVED gate fires before deadline check; absent target_date must not change outcome."""
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(status=GoalStatus.ACHIEVED, target_date=None),
        _initial_wealth(),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_achievement_result is None
    assert solver.calls == 0


# Test F — ACHIEVED + current_amount None → NOT_APPLICABLE (not INSUFFICIENT_DATA)
def test_achieved_goal_with_current_amount_none_is_not_applicable():
    """GoalPlanningFact allows current_amount=None; ACHIEVED must still be NOT_APPLICABLE."""
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(status=GoalStatus.ACHIEVED, current_amount=None),
        _initial_wealth(),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.target_achievement_result is None
    assert solver.calls == 0


# Mutation guard — ensure ACHIEVED does NOT slip through as ALREADY_ACHIEVED
def test_achieved_status_never_produces_already_achieved():
    """If ACHIEVED were re-projected with initial >= target, result must still be NOT_APPLICABLE."""
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(
            status=GoalStatus.ACHIEVED,
            target_amount=Decimal("100.00"),
            target_date=None,
        ),
        _initial_wealth("1000.00"),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_APPLICABLE
    assert result.status is not GoalPlanningStatus.ALREADY_ACHIEVED
    assert solver.calls == 0



# Section 31 — ACTIVE + mathematical ALREADY_ACHIEVED (separation proof)
# This test guarantees the boundary: ACTIVE may produce ALREADY_ACHIEVED via solver.
# ACHIEVED (lifecycle) never does.  If ACTIVE + initial >= target were incorrectly
# blocked, this test would fail — proving the concepts are correctly separated.
def test_active_goal_with_initial_at_target_produces_mathematical_already_achieved():
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(
            status=GoalStatus.ACTIVE,
            target_amount=Decimal("1000.00"),
            target_date=None,  # deadline not required when already achieved
        ),
        _initial_wealth("1000.00"),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.ALREADY_ACHIEVED
    assert result.target_achievement_result.status is TargetAchievementStatus.ALREADY_ACHIEVED
    assert solver.calls == 1  # solver MUST be called for ACTIVE goals


def test_missing_basis_is_insufficient_data_without_default_or_solver_call():
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(),
        _initial_wealth(),
        _assumptions(),
        None,
    )

    assert result.status is GoalPlanningStatus.INSUFFICIENT_DATA
    assert result.target_value_basis is None
    assert result.target_achievement_result is None
    assert solver.calls == 0


@pytest.mark.parametrize(
    ("basis", "output_mode"),
    [
        (TargetValueBasis.NOMINAL, OutputMode.REAL),
        (TargetValueBasis.REAL, OutputMode.NOMINAL),
    ],
)
def test_basis_output_mismatch_is_a_validation_error(basis, output_mode):
    assumptions = (
        _assumptions(
            return_type=ReturnType.NOMINAL,
            output_mode=OutputMode.REAL,
            inflation_rate=Decimal("0.04"),
        )
        if output_mode is OutputMode.REAL
        else _assumptions(output_mode=OutputMode.NOMINAL)
    )

    with pytest.raises(ValueError, match="basis must match"):
        GoalPlanningService().evaluate(
            _goal(),
            _initial_wealth(),
            assumptions,
            basis,
        )


def test_real_basis_and_real_output_are_compatible_without_target_conversion():
    result = GoalPlanningService().evaluate(
        _goal(),
        _initial_wealth(),
        _assumptions(
            return_type=ReturnType.REAL,
            output_mode=OutputMode.REAL,
        ),
        TargetValueBasis.REAL,
    )

    assert result.status is GoalPlanningStatus.PROJECTED_ON_TIME
    assert result.target_achievement_result.target_amount == Decimal("900.00")


def test_missing_target_date_is_insufficient_when_target_is_not_already_achieved():
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(target_date=None),
        _initial_wealth(),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.INSUFFICIENT_DATA
    assert result.target_achievement_result is None
    assert solver.calls == 0


def test_already_achieved_does_not_require_goal_target_date():
    solver = _CountingTargetSolver()
    result = GoalPlanningService(solver).evaluate(
        _goal(target_date=None, target_amount=Decimal("1000.00")),
        _initial_wealth("1000.00"),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.ALREADY_ACHIEVED
    assert result.target_achievement_result.status is TargetAchievementStatus.ALREADY_ACHIEVED
    assert result.target_achievement_result.achievement_period == 0
    assert solver.calls == 1


@pytest.mark.parametrize(
    ("target_amount", "expected_status", "expected_date"),
    [
        ("800.00", GoalPlanningStatus.PROJECTED_EARLY, date(2027, 5, 31)),
        ("900.00", GoalPlanningStatus.PROJECTED_ON_TIME, date(2027, 6, 30)),
        ("1000.00", GoalPlanningStatus.PROJECTED_LATE, date(2027, 7, 31)),
    ],
)
def test_achievement_timing_is_classified_by_first_crossing_month(
    target_amount,
    expected_status,
    expected_date,
):
    result = GoalPlanningService().evaluate(
        _goal(target_amount=Decimal(target_amount)),
        _initial_wealth(),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is expected_status
    assert result.target_achievement_result.achievement_date == expected_date


def test_same_month_days_do_not_change_on_time_classification():
    goal = _goal(target_date=date(2027, 6, 1))
    initial = _initial_wealth()
    assumptions = _assumptions()
    solver = _StubTargetSolver(
        _stub_achievement(date(2027, 6, 30), goal, initial, assumptions)
    )

    result = GoalPlanningService(solver).evaluate(
        goal,
        initial,
        assumptions,
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.PROJECTED_ON_TIME


def test_inverse_same_month_days_are_also_on_time():
    goal = _goal(target_date=date(2027, 6, 30))
    initial = _initial_wealth()
    assumptions = _assumptions()
    solver = _StubTargetSolver(
        _stub_achievement(date(2027, 6, 1), goal, initial, assumptions)
    )

    result = GoalPlanningService(solver).evaluate(
        goal,
        initial,
        assumptions,
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.PROJECTED_ON_TIME


@pytest.mark.parametrize("target_date", [date(2026, 8, 1), date(2026, 9, 30)])
def test_past_and_current_target_months_are_late_when_crossing_is_future(target_date):
    result = GoalPlanningService().evaluate(
        _goal(target_amount=Decimal("100.00"), target_date=target_date),
        _initial_wealth(),
        _assumptions(horizon_months=1),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.PROJECTED_LATE
    assert result.target_achievement_result.achievement_date == date(2026, 10, 31)


def test_projection_horizon_can_extend_beyond_goal_deadline_to_prove_late():
    assumptions = _assumptions(horizon_months=12)
    result = GoalPlanningService().evaluate(
        _goal(target_amount=Decimal("500.00"), target_date=date(2026, 12, 1)),
        _initial_wealth(),
        assumptions,
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.PROJECTED_LATE
    assert result.target_achievement_result.achievement_date == date(2027, 2, 28)
    assert result.assumptions is assumptions
    assert result.assumptions.resolved_horizon_months == 12


def test_horizon_before_goal_deadline_is_not_reached_not_a_timing_claim():
    result = GoalPlanningService().evaluate(
        _goal(target_amount=Decimal("1000.00"), target_date=date(2027, 6, 1)),
        _initial_wealth(),
        _assumptions(horizon_months=3),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_REACHED_WITHIN_HORIZON
    assert (
        result.target_achievement_result.status
        is TargetAchievementStatus.NOT_REACHED_WITHIN_HORIZON
    )


def test_nested_unreachable_is_preserved_under_aggregate_not_reached_status():
    result = GoalPlanningService().evaluate(
        _goal(target_amount=Decimal("100.00")),
        _initial_wealth(),
        _assumptions(scenario_monthly_contribution=Decimal("0.00")),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.NOT_REACHED_WITHIN_HORIZON
    assert result.target_achievement_result.status is TargetAchievementStatus.UNREACHABLE
    assert result.target_achievement_result.projection_result is not None


def test_goal_planned_contribution_does_not_change_projection_timing():
    service = GoalPlanningService()
    inputs = (_initial_wealth(), _assumptions(), TargetValueBasis.NOMINAL)

    first = service.evaluate(
        _goal(goal_planned_monthly_contribution=Decimal("100.00")),
        *inputs,
    )
    second = service.evaluate(
        _goal(goal_planned_monthly_contribution=Decimal("5000.00")),
        *inputs,
    )

    assert first.status is second.status
    assert first.target_achievement_result.achievement_date == (
        second.target_achievement_result.achievement_date
    )
    assert first.target_achievement_result.assumptions is inputs[1]
    assert second.target_achievement_result.assumptions is inputs[1]


def test_explicit_scenario_contribution_is_the_projection_authority():
    goal = _goal(target_amount=Decimal("900.00"))
    low = GoalPlanningService().evaluate(
        goal,
        _initial_wealth(),
        _assumptions(scenario_monthly_contribution=Decimal("50.00")),
        TargetValueBasis.NOMINAL,
    )
    high = GoalPlanningService().evaluate(
        goal,
        _initial_wealth(),
        _assumptions(scenario_monthly_contribution=Decimal("100.00")),
        TargetValueBasis.NOMINAL,
    )

    assert low.status is GoalPlanningStatus.NOT_REACHED_WITHIN_HORIZON
    assert high.status is GoalPlanningStatus.PROJECTED_ON_TIME


@pytest.mark.parametrize(
    "source",
    [
        InitialWealthSource.GOAL_CURRENT_AMOUNT,
        InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT,
        InitialWealthSource.USER_PROVIDED_SCENARIO,
    ],
)
def test_explicit_initial_wealth_origins_have_source_independent_math(source):
    initial = _initial_wealth(
        source=source,
        source_goal_id=(GOAL_ID if source is InitialWealthSource.GOAL_CURRENT_AMOUNT else None),
    )
    result = GoalPlanningService().evaluate(
        _goal(),
        initial,
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.PROJECTED_ON_TIME
    assert result.initial_wealth_fact is initial
    assert result.target_achievement_result.initial_wealth_fact is initial


@pytest.mark.parametrize("source_goal_id", [OTHER_GOAL_ID, None])
def test_goal_current_amount_requires_matching_goal_provenance(source_goal_id):
    with pytest.raises(ValueError, match="provenance"):
        GoalPlanningService().evaluate(
            _goal(),
            _initial_wealth(
                source=InitialWealthSource.GOAL_CURRENT_AMOUNT,
                source_goal_id=source_goal_id,
            ),
            _assumptions(),
            TargetValueBasis.NOMINAL,
        )


def test_large_decimal_target_and_initial_remain_exact():
    initial_amount = Decimal("1" + "0" * 100 + ".00")
    target = Decimal("1" + "0" * 97 + "300.00")
    result = GoalPlanningService().evaluate(
        _goal(target_amount=target, target_date=date(2026, 12, 1)),
        _initial_wealth(str(initial_amount)),
        _assumptions(horizon_months=3),
        TargetValueBasis.NOMINAL,
    )

    assert result.status is GoalPlanningStatus.PROJECTED_ON_TIME
    assert result.target_achievement_result.achieved_wealth == target
    assert isinstance(result.target_achievement_result.achieved_wealth, Decimal)


def test_result_is_immutable_and_preserves_complete_inputs():
    goal = _goal()
    initial = _initial_wealth()
    assumptions = _assumptions()
    result = GoalPlanningService().evaluate(
        goal,
        initial,
        assumptions,
        TargetValueBasis.NOMINAL,
    )

    assert isinstance(result, GoalPlanningResult)
    assert result.goal_fact is goal
    assert result.initial_wealth_fact is initial
    assert result.assumptions is assumptions
    with pytest.raises(FrozenInstanceError):
        result.status = GoalPlanningStatus.PROJECTED_LATE


@pytest.mark.parametrize(
    "goal",
    [
        _goal(),
        _goal(target_amount=Decimal("1000.00")),
        _goal(goal_type=GoalType.RETIREMENT),
    ],
)
def test_evaluation_is_deterministic(goal):
    service = GoalPlanningService()
    initial = _initial_wealth()
    assumptions = _assumptions()

    first = service.evaluate(goal, initial, assumptions, TargetValueBasis.NOMINAL)
    second = service.evaluate(goal, initial, assumptions, TargetValueBasis.NOMINAL)

    assert first == second


def test_normal_projectable_goal_calls_target_solver_exactly_once():
    solver = _CountingTargetSolver()
    GoalPlanningService(solver).evaluate(
        _goal(),
        _initial_wealth(),
        _assumptions(),
        TargetValueBasis.NOMINAL,
    )

    assert solver.calls == 1


@pytest.mark.parametrize("invalid_basis", ["NOMINAL", 1, True])
def test_invalid_basis_type_is_not_silently_coerced(invalid_basis):
    with pytest.raises(TypeError, match="target_value_basis"):
        GoalPlanningService().evaluate(
            _goal(),
            _initial_wealth(),
            _assumptions(),
            invalid_basis,
        )


def test_service_does_not_mutate_goal_or_assumptions():
    goal = _goal()
    assumptions = _assumptions()
    original_goal = replace(goal)
    original_assumptions = replace(assumptions)

    GoalPlanningService().evaluate(
        goal,
        _initial_wealth(),
        assumptions,
        TargetValueBasis.NOMINAL,
    )

    assert goal == original_goal
    assert assumptions == original_assumptions
