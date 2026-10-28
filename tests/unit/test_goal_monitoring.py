"""Pure domain tests for the R6.3 Goal monitoring overview."""

from datetime import date, datetime
from decimal import Decimal, getcontext
from uuid import UUID

import pytest

from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domains.planning import goal_monitoring
from backend.domains.planning.facts import GoalPlanningFact
from backend.domains.planning.goal_monitoring import (
    GoalDataFlag,
    GoalProgressState,
    build_goal_monitoring_overview,
)


USER_ID = UUID("00000000-0000-0000-0000-000000000801")


def _goal(sequence: int = 1, **overrides) -> GoalPlanningFact:
    values = {
        "goal_id": UUID(f"00000000-0000-0000-0000-{sequence:012d}"),
        "user_id": USER_ID,
        "name": f"Goal {sequence}",
        "description": None,
        "goal_type": GoalType.CUSTOM,
        "status": GoalStatus.ACTIVE,
        "target_amount": Decimal("100.00"),
        "target_date": date(2028, 12, 31),
        "current_amount": Decimal("25.00"),
        "goal_planned_monthly_contribution": Decimal("10.00"),
        "priority": sequence,
        "linked_account_id": None,
        "created_at": datetime(2026, 1, sequence, 10, 0),
        "updated_at": datetime(2026, 10, 27, 9, 30),
    }
    values.update(overrides)
    return GoalPlanningFact(**values)


@pytest.mark.parametrize(
    ("target", "current", "expected_state"),
    [
        (None, Decimal("10.00"), GoalProgressState.UNAVAILABLE),
        (Decimal("0.00"), Decimal("0.00"), GoalProgressState.UNAVAILABLE),
        (Decimal("-1.00"), Decimal("0.00"), GoalProgressState.UNAVAILABLE),
        (Decimal("100.00"), None, GoalProgressState.UNAVAILABLE),
        (Decimal("100.00"), Decimal("-0.01"), GoalProgressState.NEGATIVE_CURRENT),
        (Decimal("100.00"), Decimal("0.00"), GoalProgressState.NOT_STARTED),
        (Decimal("100.00"), Decimal("99.99"), GoalProgressState.IN_PROGRESS),
        (Decimal("100.00"), Decimal("100.00"), GoalProgressState.ACHIEVED),
        (Decimal("100.00"), Decimal("100.01"), GoalProgressState.EXCEEDED),
    ],
)
def test_each_goal_belongs_to_exactly_one_progress_state(
    target,
    current,
    expected_state,
):
    item = build_goal_monitoring_overview(
        (_goal(target_amount=target, current_amount=current),)
    ).goals[0]

    assert item.progress_state is expected_state


def test_summary_counts_match_the_complete_collection_without_monetary_totals():
    overview = build_goal_monitoring_overview(
        (
            _goal(1, current_amount=Decimal("0.00")),
            _goal(2, current_amount=Decimal("25.00")),
            _goal(3, current_amount=Decimal("100.00")),
            _goal(4, current_amount=Decimal("101.00")),
            _goal(5, current_amount=Decimal("-1.00")),
            _goal(6, current_amount=None),
        )
    )

    assert overview.summary.total_goals == 6
    assert overview.summary.not_started == 1
    assert overview.summary.in_progress == 1
    assert overview.summary.achieved == 1
    assert overview.summary.exceeded == 1
    assert overview.summary.negative_current == 1
    assert overview.summary.unavailable == 1
    assert sum(
        (
            overview.summary.not_started,
            overview.summary.in_progress,
            overview.summary.achieved,
            overview.summary.exceeded,
            overview.summary.negative_current,
            overview.summary.unavailable,
        )
    ) == overview.summary.total_goals
    assert not hasattr(overview.summary, "total_current_amount")
    assert not hasattr(overview.summary, "overall_completion_percent")


def test_flags_preserve_null_zero_negative_and_deterministic_field_order():
    goals = (
        _goal(
            1,
            target_amount=None,
            current_amount=None,
            goal_planned_monthly_contribution=None,
        ),
        _goal(
            2,
            target_amount=Decimal("0.00"),
            current_amount=Decimal("-1.00"),
            goal_planned_monthly_contribution=Decimal("0.00"),
        ),
    )

    first, second = build_goal_monitoring_overview(goals).goals

    assert first.data_flags == (
        GoalDataFlag.TARGET_MISSING,
        GoalDataFlag.CURRENT_MISSING,
        GoalDataFlag.MONTHLY_CONTRIBUTION_MISSING,
    )
    assert second.data_flags == (
        GoalDataFlag.TARGET_NONPOSITIVE,
        GoalDataFlag.CURRENT_NEGATIVE,
        GoalDataFlag.MONTHLY_CONTRIBUTION_ZERO,
    )


def test_overview_reuses_r62_calculation_once_per_goal(monkeypatch):
    original = goal_monitoring.calculate_goal_progress
    calls = []

    def spy(target_amount, current_amount):
        calls.append((target_amount, current_amount))
        return original(target_amount, current_amount)

    monkeypatch.setattr(goal_monitoring, "calculate_goal_progress", spy)

    overview = build_goal_monitoring_overview((_goal(1), _goal(2)))

    assert calls == [
        (Decimal("100.00"), Decimal("25.00")),
        (Decimal("100.00"), Decimal("25.00")),
    ]
    assert [item.progress.completion_percent for item in overview.goals] == [
        Decimal("25.00"),
        Decimal("25.00"),
    ]


def test_input_order_and_lifecycle_status_are_preserved_without_reclassification():
    goals = (
        _goal(2, status=GoalStatus.CANCELLED),
        _goal(1, status=GoalStatus.ACHIEVED),
    )

    overview = build_goal_monitoring_overview(goals)

    assert [item.goal.goal_id for item in overview.goals] == [
        goals[0].goal_id,
        goals[1].goal_id,
    ]
    assert all(
        item.progress_state is GoalProgressState.IN_PROGRESS
        for item in overview.goals
    )


def test_empty_collection_is_zeroed_and_duplicate_ids_are_rejected():
    empty = build_goal_monitoring_overview(())

    assert empty.goals == ()
    assert empty.summary.total_goals == 0
    assert sum(
        (
            empty.summary.not_started,
            empty.summary.in_progress,
            empty.summary.achieved,
            empty.summary.exceeded,
            empty.summary.negative_current,
            empty.summary.unavailable,
        )
    ) == 0

    duplicated = _goal()
    with pytest.raises(ValueError, match="duplicate goal_id"):
        build_goal_monitoring_overview((duplicated, duplicated))


def test_overview_keeps_decimal_precision_and_global_context_unchanged():
    before = getcontext().copy()

    item = build_goal_monitoring_overview(
        (
            _goal(
                target_amount=Decimal("10.01"),
                current_amount=Decimal("3.34"),
            ),
        )
    ).goals[0]

    assert item.progress.gap_amount == Decimal("6.67")
    assert item.progress.completion_percent == Decimal("33.37")
    after = getcontext()
    assert (after.prec, after.rounding, after.Emax, after.Emin, after.clamp) == (
        before.prec,
        before.rounding,
        before.Emax,
        before.Emin,
        before.clamp,
    )
