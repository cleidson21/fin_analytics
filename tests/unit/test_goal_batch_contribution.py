"""Pure orchestration tests for the R6.4 Goal contribution batch."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domains.planning.assumptions import (
    ContributionTiming,
    OutputMode,
    ProjectionAssumptions,
    RateBasis,
    ReturnType,
)
from backend.domains.planning.facts import (
    GoalPlanningFact,
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    PlanningFactAsOf,
    PlanningFactProvenance,
)
from backend.domains.planning.goal_batch_contribution import (
    GoalBatchContributionAvailability,
    GoalBatchContributionImpediment,
    GoalBatchContributionPreviewService,
    GoalBatchContributionSelection,
)
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionSolver,
    RequiredContributionStatus,
)


USER_ID = UUID("00000000-0000-0000-0000-000000000941")


def _goal(sequence: int, **overrides) -> GoalPlanningFact:
    values = {
        "goal_id": UUID(f"00000000-0000-0000-0000-{sequence:012d}"),
        "user_id": USER_ID,
        "name": f"Goal {sequence}",
        "description": None,
        "goal_type": GoalType.WEALTH_TARGET,
        "status": GoalStatus.ACTIVE,
        "target_amount": Decimal("1200.00"),
        "target_date": None,
        "current_amount": Decimal("0.00"),
        "goal_planned_monthly_contribution": None,
        "priority": sequence,
        "linked_account_id": None,
        "created_at": datetime(2026, 1, 1),
        "updated_at": datetime(2026, 10, 27),
    }
    values.update(overrides)
    return GoalPlanningFact(**values)


def _wealth(goal: GoalPlanningFact) -> InitialWealthFact | None:
    if goal.current_amount is None or goal.current_amount < 0:
        return None
    return InitialWealthFact(
        source=InitialWealthSource.GOAL_CURRENT_AMOUNT,
        amount=goal.current_amount,
        as_of=PlanningFactAsOf(observed_at=goal.updated_at),
        scope=InitialWealthScope.GOAL,
        provenance=PlanningFactProvenance(
            source_table="goals",
            source_type="USER_GOVERNED_GOAL",
            goal_id=goal.goal_id,
        ),
    )


def _assumptions(**overrides) -> ProjectionAssumptions:
    values = {
        "as_of_date": date(2026, 10, 27),
        "scenario_monthly_contribution": Decimal("0.00"),
        "expected_return_rate": Decimal("0"),
        "return_type": ReturnType.NOMINAL,
        "output_mode": OutputMode.NOMINAL,
        "inflation_rate": None,
        "horizon_months": 12,
        "rate_basis": RateBasis.EFFECTIVE_ANNUAL,
        "contribution_timing": ContributionTiming.END_OF_MONTH,
    }
    values.update(overrides)
    return ProjectionAssumptions(**values)


class _CountingSolver(RequiredContributionSolver):
    def __init__(self):
        super().__init__()
        self.goal_ids = []

    def solve(self, initial_wealth_fact, assumptions_template, target_amount):
        self.goal_ids.append(initial_wealth_fact.provenance.goal_id)
        return super().solve(
            initial_wealth_fact,
            assumptions_template,
            target_amount,
        )


def test_batch_preserves_order_and_reuses_certified_solver_per_available_goal():
    first = _goal(2, target_amount=Decimal("1200.00"))
    second = _goal(1, target_amount=Decimal("600.00"))
    solver = _CountingSolver()
    service = GoalBatchContributionPreviewService(solver)

    result = service.preview(
        (
            GoalBatchContributionSelection(first, _wealth(first)),
            GoalBatchContributionSelection(second, _wealth(second)),
        ),
        _assumptions(),
    )

    assert [item.goal.goal_id for item in result.items] == [
        first.goal_id,
        second.goal_id,
    ]
    assert solver.goal_ids == [first.goal_id, second.goal_id]
    assert [item.calculation.required_monthly_contribution for item in result.items] == [
        Decimal("100.00"),
        Decimal("50.00"),
    ]
    assert all(
        item.calculation.status is RequiredContributionStatus.SOLVED
        for item in result.items
    )


def test_zero_is_valid_and_already_achieved_returns_certified_zero():
    goal = _goal(
        1,
        target_amount=Decimal("100.00"),
        current_amount=Decimal("100.00"),
    )

    item = GoalBatchContributionPreviewService(
        RequiredContributionSolver()
    ).preview(
        (GoalBatchContributionSelection(goal, _wealth(goal)),),
        _assumptions(expected_return_rate=Decimal("0.00")),
    ).items[0]

    assert item.availability is GoalBatchContributionAvailability.AVAILABLE
    assert item.impediment is None
    assert item.calculation.status is RequiredContributionStatus.ALREADY_ACHIEVED
    assert item.calculation.required_monthly_contribution == Decimal("0.00")


def test_unavailable_facts_are_distinct_and_do_not_call_solver():
    goals = (
        _goal(1, target_amount=None),
        _goal(2, target_amount=Decimal("0.00")),
        _goal(3, current_amount=None),
        _goal(4, current_amount=Decimal("-0.01")),
    )
    solver = _CountingSolver()

    result = GoalBatchContributionPreviewService(solver).preview(
        tuple(GoalBatchContributionSelection(goal, _wealth(goal)) for goal in goals),
        _assumptions(),
    )

    assert solver.goal_ids == []
    assert [item.availability for item in result.items] == [
        GoalBatchContributionAvailability.UNAVAILABLE,
    ] * 4
    assert [item.impediment for item in result.items] == [
        GoalBatchContributionImpediment.TARGET_MISSING,
        GoalBatchContributionImpediment.TARGET_NONPOSITIVE,
        GoalBatchContributionImpediment.CURRENT_AMOUNT_MISSING,
        GoalBatchContributionImpediment.CURRENT_AMOUNT_NEGATIVE,
    ]
    assert all(item.calculation is None for item in result.items)


def test_cent_values_and_large_decimal_remain_exact():
    goal = _goal(
        1,
        target_amount=Decimal("9999999999.99"),
        current_amount=Decimal("9999999999.98"),
    )

    item = GoalBatchContributionPreviewService(
        RequiredContributionSolver()
    ).preview(
        (GoalBatchContributionSelection(goal, _wealth(goal)),),
        _assumptions(horizon_months=1),
    ).items[0]

    assert item.calculation.required_monthly_contribution == Decimal("0.01")
    assert isinstance(item.calculation.required_monthly_contribution, Decimal)
