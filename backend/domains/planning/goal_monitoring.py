"""Deterministic R6.3 monitoring over Decimal-safe Goal facts."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Sequence

from backend.domains.planning.facts import GoalPlanningFact
from backend.domains.planning.goal_progress import (
    GoalProgressResult,
    calculate_goal_progress,
)


_ZERO = Decimal("0")


class GoalProgressState(str, Enum):
    """Mutually exclusive financial progress classification for one Goal."""

    UNAVAILABLE = "UNAVAILABLE"
    NEGATIVE_CURRENT = "NEGATIVE_CURRENT"
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    ACHIEVED = "ACHIEVED"
    EXCEEDED = "EXCEEDED"


class GoalDataFlag(str, Enum):
    """Factual data conditions without severity or recommendation semantics."""

    TARGET_MISSING = "TARGET_MISSING"
    TARGET_NONPOSITIVE = "TARGET_NONPOSITIVE"
    CURRENT_MISSING = "CURRENT_MISSING"
    CURRENT_NEGATIVE = "CURRENT_NEGATIVE"
    MONTHLY_CONTRIBUTION_MISSING = "MONTHLY_CONTRIBUTION_MISSING"
    MONTHLY_CONTRIBUTION_ZERO = "MONTHLY_CONTRIBUTION_ZERO"


@dataclass(frozen=True)
class GoalMonitoringItem:
    """One Goal fact paired with its certified R6.2 progress result."""

    goal: GoalPlanningFact
    progress: GoalProgressResult
    progress_state: GoalProgressState
    data_flags: tuple[GoalDataFlag, ...]


@dataclass(frozen=True)
class GoalMonitoringSummary:
    """Count-only summary over the exact emitted Goal collection."""

    total_goals: int
    not_started: int
    in_progress: int
    achieved: int
    exceeded: int
    negative_current: int
    unavailable: int


@dataclass(frozen=True)
class GoalMonitoringOverview:
    """Complete ordered monitoring read model for one authenticated user."""

    summary: GoalMonitoringSummary
    goals: tuple[GoalMonitoringItem, ...]


def _classify_progress(
    target_amount: Decimal | None,
    current_amount: Decimal | None,
) -> GoalProgressState:
    if target_amount is None or target_amount <= _ZERO or current_amount is None:
        return GoalProgressState.UNAVAILABLE
    if current_amount < _ZERO:
        return GoalProgressState.NEGATIVE_CURRENT
    if current_amount == _ZERO:
        return GoalProgressState.NOT_STARTED
    if current_amount < target_amount:
        return GoalProgressState.IN_PROGRESS
    if current_amount == target_amount:
        return GoalProgressState.ACHIEVED
    return GoalProgressState.EXCEEDED


def _data_flags(goal: GoalPlanningFact) -> tuple[GoalDataFlag, ...]:
    flags: list[GoalDataFlag] = []
    target_amount: Decimal | None = goal.target_amount

    if target_amount is None:
        flags.append(GoalDataFlag.TARGET_MISSING)
    elif target_amount <= _ZERO:
        flags.append(GoalDataFlag.TARGET_NONPOSITIVE)

    if goal.current_amount is None:
        flags.append(GoalDataFlag.CURRENT_MISSING)
    elif goal.current_amount < _ZERO:
        flags.append(GoalDataFlag.CURRENT_NEGATIVE)

    contribution = goal.goal_planned_monthly_contribution
    if contribution is None:
        flags.append(GoalDataFlag.MONTHLY_CONTRIBUTION_MISSING)
    elif contribution == _ZERO:
        flags.append(GoalDataFlag.MONTHLY_CONTRIBUTION_ZERO)

    return tuple(flags)


def build_goal_monitoring_overview(
    goals: Sequence[GoalPlanningFact],
) -> GoalMonitoringOverview:
    """Build an ordered count-only overview and reuse the certified R6.2 math."""

    seen_goal_ids = set()
    items: list[GoalMonitoringItem] = []
    counts = {state: 0 for state in GoalProgressState}

    for goal in goals:
        if goal.goal_id in seen_goal_ids:
            raise ValueError("goal collection contains duplicate goal_id")
        seen_goal_ids.add(goal.goal_id)

        target_amount: Decimal | None = goal.target_amount
        progress = calculate_goal_progress(target_amount, goal.current_amount)
        progress_state = _classify_progress(target_amount, goal.current_amount)
        counts[progress_state] += 1
        items.append(
            GoalMonitoringItem(
                goal=goal,
                progress=progress,
                progress_state=progress_state,
                data_flags=_data_flags(goal),
            )
        )

    summary = GoalMonitoringSummary(
        total_goals=len(items),
        not_started=counts[GoalProgressState.NOT_STARTED],
        in_progress=counts[GoalProgressState.IN_PROGRESS],
        achieved=counts[GoalProgressState.ACHIEVED],
        exceeded=counts[GoalProgressState.EXCEEDED],
        negative_current=counts[GoalProgressState.NEGATIVE_CURRENT],
        unavailable=counts[GoalProgressState.UNAVAILABLE],
    )
    return GoalMonitoringOverview(summary=summary, goals=tuple(items))
