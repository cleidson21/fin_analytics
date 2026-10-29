"""R6.5 exact budget oracles and parity with certified comparison outputs."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from decimal import Decimal, getcontext, localcontext
from uuid import UUID

import pytest

from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domains.planning.assumptions import (
    OutputMode, ProjectionAssumptions, ReturnType,
)
from backend.domains.planning.facts import GoalPlanningFact
from backend.domains.planning.goal_batch_contribution import GoalBatchContributionSelection
from backend.domains.planning.goal_budget import (
    GoalBudgetAllocation, GoalBudgetPreviewService, GoalBudgetRequest, GoalBudgetScenario,
)
from backend.domains.planning.readers import PlanningGoalReadQuery
from backend.domains.planning.scenario_comparison import (
    ScenarioComparisonEngine, ScenarioDefinition,
)
from backend.domains.planning.target_basis import TargetValueBasis


def goal(index=1, **overrides):
    values = dict(
        goal_id=UUID(int=index), user_id=UUID(int=901), name=f"Goal {index}",
        description=None, goal_type=GoalType.WEALTH_TARGET, status=GoalStatus.ACTIVE,
        target_amount=Decimal("1200.00"), target_date=date(2030, 1, 1),
        current_amount=Decimal("0.00"), goal_planned_monthly_contribution=Decimal("999"),
        priority=index, linked_account_id=None,
        created_at=datetime(2026, 1, 1), updated_at=datetime(2026, 10, 28),
    )
    values.update(overrides)
    return GoalPlanningFact(**values)


def selection(value):
    fact = (
        None if value.current_amount is None or value.current_amount < 0
        else PlanningGoalReadQuery.current_amount_as_initial_wealth(value)
    )
    return GoalBatchContributionSelection(value, fact)


def assumptions(**overrides):
    values = dict(
        as_of_date=date(2026, 10, 28), scenario_monthly_contribution=Decimal("0"),
        expected_return_rate=Decimal("0"), return_type=ReturnType.NOMINAL,
        output_mode=OutputMode.NOMINAL, horizon_months=12,
    )
    values.update(overrides)
    return ProjectionAssumptions(**values)


def budget(a=("100",), b=None, monthly="1000", ids=None):
    ids = ids or tuple(UUID(int=i + 1) for i in range(len(a)))
    return GoalBudgetRequest(
        tuple(ids), Decimal(monthly),
        tuple(
            GoalBudgetScenario(scenario_id, tuple(
                GoalBudgetAllocation(identifier, Decimal(amount))
                for identifier, amount in zip(ids, amounts)
            ))
            for scenario_id, amounts in (("A", a), ("B", b if b is not None else a))
        ),
    )


class CountingEngine(ScenarioComparisonEngine):
    def __init__(self):
        super().__init__()
        self.calls = []

    def compare(self, **kwargs):
        self.calls.append(kwargs)
        return super().compare(**kwargs)


@pytest.mark.parametrize("monthly,a,total,unallocated,exceeded", [
    ("1000", ("100", "200"), "300", "700", "0"),
    ("300", ("100", "200"), "300", "0", "0"),
    ("250", ("100", "200"), "300", "0", "50"),
    ("0", ("100", "200"), "300", "0", "300"),
    ("0", ("0", "0.00"), "0", "0", "0"),
    ("10.01", ("0", "0"), "0", "10.01", "0"),
    ("0.31", ("0.10", "0.20"), "0.30", "0.01", "0"),
])
def test_budget_independent_exact_oracles(monthly, a, total, unallocated, exceeded):
    request = budget(a, monthly=monthly)
    for summary in request.summaries:
        assert summary.allocated_total == Decimal(total)
        assert summary.unallocated_amount == Decimal(unallocated)
        assert summary.exceeded_amount == Decimal(exceeded)


def test_exact_budget_math_survives_low_ambient_precision_and_carry():
    huge = "99999999999999999999999999999999999999999999999999.99"
    expected = Decimal("100000000000000000000000000000000000000000000000000.00")
    before = getcontext().copy()
    with localcontext() as context:
        context.prec = 4
        request = budget((huge, "0.01"), ("0.01", huge), monthly=str(expected))
        assert context.prec == 4
    assert request.summaries[0].allocated_total == expected
    assert request.summaries[0].unallocated_amount == 0
    assert request.summaries[0].exceeded_amount == 0
    assert getcontext() == before or str(getcontext()) == str(before)


def test_exact_equality_rejects_difference_hidden_by_default_precision():
    with localcontext() as context:
        context.prec = 4
        with pytest.raises(ValueError, match="exactly equal"):
            budget(("999999999999999999999999999999.99", "0.01"),
                   ("999999999999999999999999999999.99", "0.02"))


def test_large_budget_subtraction_keeps_cents_under_low_ambient_precision():
    with localcontext() as context:
        context.prec = 4
        request = budget(("0.01",), monthly="1000000000000000000000000000000.00")
        assert request.summaries[0].unallocated_amount == Decimal(
            "999999999999999999999999999999.99"
        )
        assert context.prec == 4


def test_numeric_equality_accepts_different_lexical_scales():
    assert budget(("100",), ("100.00",)).summaries[0].allocated_total == Decimal("100")


@pytest.mark.parametrize("amount", ["-0.01", "1.001", "1.000", "NaN", "Infinity"])
def test_domain_rejects_invalid_money(amount):
    with pytest.raises(ValueError):
        budget((amount,))
    with pytest.raises(ValueError):
        budget(monthly=amount)


def test_redistribution_calls_certified_engine_once_per_goal_with_same_fact():
    goals = (goal(2, target_amount=Decimal("600")), goal(1))
    selections = tuple(selection(g) for g in goals)
    request = budget(("50", "100"), ("100", "50"), ids=tuple(g.goal_id for g in goals))
    engine = CountingEngine()
    common = assumptions()
    result = GoalBudgetPreviewService(engine).preview(selections, common, request)
    assert len(engine.calls) == 2
    assert tuple(item.selection.goal for item in result.items) == goals
    for i, call in enumerate(engine.calls):
        a, b = call["scenarios"]
        assert a.initial_wealth_fact is b.initial_wealth_fact is selections[i].initial_wealth_fact
        assert a.scenario_id == "A" and b.scenario_id == "B"
        assert replace(a.assumptions, scenario_monthly_contribution=Decimal("0")) == common
        assert replace(b.assumptions, scenario_monthly_contribution=Decimal("0")) == common
        assert call["target_amount"] == goals[i].target_amount
        assert call["target_value_basis"] is TargetValueBasis.NOMINAL
        assert call["reference_scenario_id"] == "A"
        assert result.items[i].comparison == ScenarioComparisonEngine().compare(**call)

    first, second = (item.comparison.entries for item in result.items)
    assert first[1].final_wealth_delta == Decimal("600.00")
    assert first[1].total_contributions_delta == Decimal("600.00")
    assert first[1].total_projected_growth_delta == Decimal("0.00")
    assert first[1].months_saved_or_lost == 6
    assert second[1].final_wealth_delta == Decimal("-600.00")
    assert second[1].months_saved_or_lost is None


@pytest.mark.parametrize("rate", ["0", "-0.05", "0.05"])
@pytest.mark.parametrize("current,target", [("0", "1000"), ("1000", "1000"), ("1500", "1000")])
def test_full_nested_parity_with_direct_engine_and_identical_scenarios(rate, current, target):
    chosen = selection(goal(current_amount=Decimal(current), target_amount=Decimal(target)))
    common = assumptions(expected_return_rate=Decimal(rate))
    request = budget(("100.10",))
    result = GoalBudgetPreviewService(ScenarioComparisonEngine()).preview((chosen,), common, request)
    direct = ScenarioComparisonEngine().compare(
        tuple(ScenarioDefinition(s, chosen.initial_wealth_fact,
                                 replace(common, scenario_monthly_contribution=Decimal("100.10")))
              for s in ("A", "B")), "A", Decimal(target), TargetValueBasis.NOMINAL,
    )
    assert result.items[0].comparison == direct
    a, b = direct.entries
    assert a.final_wealth_delta == b.final_wealth_delta == 0
    assert b.total_contributions_delta == b.total_projected_growth_delta == 0
    assert len(b.projection_result.periods) == 12
    if rate == "0":
        assert b.final_wealth == Decimal(current) + Decimal("1201.20")


@pytest.mark.parametrize("contribution,target,current,status", [
    ("0", "1200", "0", "UNREACHABLE"),
    ("1", "1200", "0", "NOT_REACHED_WITHIN_HORIZON"),
    ("100", "100", "0", "ACHIEVED"),
    ("100", "100", "100", "ALREADY_ACHIEVED"),
])
def test_solver_states_keep_full_horizon_and_nullable_time_delta(contribution, target, current, status):
    chosen = selection(goal(target_amount=Decimal(target), current_amount=Decimal(current)))
    item = GoalBudgetPreviewService(ScenarioComparisonEngine()).preview(
        (chosen,), assumptions(), budget((contribution,))
    ).items[0]
    assert item.availability.value == "AVAILABLE"
    a, b = item.comparison.entries
    achievement = b.target_achievement_result
    assert achievement.status.value == status
    assert b.final_wealth == Decimal(current) + Decimal(contribution) * 12
    assert b.projection_result.horizon_months == 12
    if status in {"UNREACHABLE", "NOT_REACHED_WITHIN_HORIZON"}:
        assert achievement.achievement_date is None
        assert achievement.months_required is None
        assert b.months_saved_or_lost is None
    else:
        assert b.months_saved_or_lost == 0


@pytest.mark.parametrize("target,current,code", [
    (None, None, "TARGET_MISSING"),
    (None, "0", "TARGET_MISSING"),
    ("0", None, "TARGET_NONPOSITIVE"),
    ("-1", "-1", "TARGET_NONPOSITIVE"),
    ("100", None, "CURRENT_AMOUNT_MISSING"),
    ("100", "-0.01", "CURRENT_AMOUNT_NEGATIVE"),
])
def test_unavailable_precedence_preserves_allocations_and_skips_engine(target, current, code):
    chosen = selection(goal(
        target_amount=None if target is None else Decimal(target),
        current_amount=None if current is None else Decimal(current),
    ))
    engine = CountingEngine()
    result = GoalBudgetPreviewService(engine).preview((chosen,), assumptions(), budget(("50",)))
    item = result.items[0]
    assert item.availability.value == "UNAVAILABLE"
    assert item.impediment.value == code
    assert item.comparison is None
    assert engine.calls == []
    assert result.request.summaries[0].allocated_total == Decimal("50")


@pytest.mark.parametrize("horizon", [1, 1200])
def test_explicit_horizon_boundaries_ignore_goal_dates(horizon):
    chosen = selection(goal(target_date=date(2020, 1, 1)))
    result = GoalBudgetPreviewService(ScenarioComparisonEngine()).preview(
        (chosen,), assumptions(horizon_months=horizon), budget(("0",))
    )
    assert result.items[0].comparison.horizon_months == horizon


@pytest.mark.parametrize("status", list(GoalStatus))
@pytest.mark.parametrize("goal_type", list(GoalType))
def test_lifecycle_and_type_do_not_change_arithmetic(status, goal_type):
    chosen = selection(goal(status=status, goal_type=goal_type))
    result = GoalBudgetPreviewService(ScenarioComparisonEngine()).preview(
        (chosen,), assumptions(horizon_months=1), budget()
    )
    assert result.items[0].comparison.entries[0].final_wealth == Decimal("100.00")


def test_twenty_goal_bound_and_immutable_results():
    goals = tuple(goal(i) for i in range(1, 21))
    request = budget(("1",) * 20)
    engine = CountingEngine()
    result = GoalBudgetPreviewService(engine).preview(
        tuple(selection(g) for g in goals), assumptions(horizon_months=1), request
    )
    assert len(result.items) == len(engine.calls) == 20
    with pytest.raises(FrozenInstanceError):
        result.request.monthly_budget = Decimal("2")
    with pytest.raises(ValueError):
        budget(("1",) * 21)


def test_duplicate_selection_and_wrong_fact_fail_closed():
    request = budget()
    with pytest.raises(ValueError):
        replace(request, goal_ids=(UUID(int=1), UUID(int=1)))
    chosen = selection(goal())
    service = GoalBudgetPreviewService(ScenarioComparisonEngine())
    with pytest.raises(ValueError):
        service.preview((chosen, chosen), assumptions(), request)
    wrong_fact = replace(chosen.initial_wealth_fact, amount=Decimal("1"))
    with pytest.raises(ValueError):
        service.preview((replace(chosen, initial_wealth_fact=wrong_fact),), assumptions(), request)
