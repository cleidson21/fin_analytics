"""Deterministic Goal orchestration over the certified Planning solvers."""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domains.planning.assumptions import OutputMode, ProjectionAssumptions
from backend.domains.planning.facts import (
    GoalPlanningFact,
    InitialWealthFact,
    InitialWealthSource,
)
from backend.domains.planning.target_solver import (
    TargetAchievementResult,
    TargetAchievementSolver,
    TargetAchievementStatus,
)
from backend.domains.planning.target_basis import TargetValueBasis


class GoalPlanningStatus(str, Enum):
    """Approved orchestration states for generic Goal planning."""

    PROJECTED_EARLY = "PROJECTED_EARLY"
    PROJECTED_ON_TIME = "PROJECTED_ON_TIME"
    PROJECTED_LATE = "PROJECTED_LATE"
    ALREADY_ACHIEVED = "ALREADY_ACHIEVED"
    NOT_REACHED_WITHIN_HORIZON = "NOT_REACHED_WITHIN_HORIZON"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"


_ELIGIBLE_GOAL_TYPES = frozenset(
    {
        GoalType.EMERGENCY_RESERVE,
        GoalType.TRAVEL,
        GoalType.PURCHASE,
        GoalType.CUSTOM,
        GoalType.WEALTH_TARGET,
        GoalType.INVESTMENT_TARGET,
    }
)
# Forward Planning 10.3 eligibility contract (TSK-10.3.5-R, 2026-09-17):
# GoalStatus.ACTIVE is the ONLY lifecycle status eligible for forward planning.
# GoalStatus.ACHIEVED is a persisted/manual lifecycle fact that does NOT prove
# current_amount >= target_amount and must NOT be re-projected or automatically
# converted to GoalPlanningStatus.ALREADY_ACHIEVED.
# GoalPlanningStatus.ALREADY_ACHIEVED is a strictly mathematical result produced
# by TargetAchievementSolver when initial_wealth >= target for a ACTIVE Goal.
# These two concepts are NOT equivalent and must NOT be synchronized automatically.
_PROJECTABLE_GOAL_STATUS = GoalStatus.ACTIVE


@dataclass(frozen=True)
class GoalPlanningResult:
    """Immutable Goal assessment preserving all source and solver provenance."""

    status: GoalPlanningStatus
    goal_fact: GoalPlanningFact
    initial_wealth_fact: Optional[InitialWealthFact]
    assumptions: ProjectionAssumptions
    target_value_basis: Optional[TargetValueBasis]
    target_achievement_result: Optional[TargetAchievementResult]


def _require_valid_inputs(
    goal_fact: GoalPlanningFact,
    initial_wealth_fact: InitialWealthFact,
    assumptions: ProjectionAssumptions,
) -> None:
    if not isinstance(goal_fact, GoalPlanningFact):
        raise TypeError("goal_fact must be GoalPlanningFact")
    if not isinstance(initial_wealth_fact, InitialWealthFact):
        raise TypeError("initial_wealth_fact must be InitialWealthFact")
    if not isinstance(assumptions, ProjectionAssumptions):
        raise TypeError("assumptions must be ProjectionAssumptions")
    if not isinstance(goal_fact.goal_type, GoalType):
        raise TypeError("goal_fact.goal_type must be GoalType")
    if not isinstance(goal_fact.status, GoalStatus):
        raise TypeError("goal_fact.status must be GoalStatus")


def _require_target_value_basis(
    target_value_basis: Optional[TargetValueBasis],
) -> None:
    if target_value_basis is not None and not isinstance(
        target_value_basis,
        TargetValueBasis,
    ):
        raise TypeError("target_value_basis must be TargetValueBasis or None")


def _require_matching_goal_provenance(
    goal_fact: GoalPlanningFact,
    initial_wealth_fact: InitialWealthFact,
) -> None:
    if initial_wealth_fact.source is not InitialWealthSource.GOAL_CURRENT_AMOUNT:
        return

    source_goal_id = initial_wealth_fact.provenance.goal_id
    if source_goal_id is None:
        raise ValueError(
            "GOAL_CURRENT_AMOUNT provenance must identify its source goal"
        )
    if source_goal_id != goal_fact.goal_id:
        raise ValueError(
            "GOAL_CURRENT_AMOUNT provenance must match goal_fact.goal_id"
        )


def _require_matching_target_basis(
    target_value_basis: TargetValueBasis,
    output_mode: OutputMode,
) -> None:
    expected_output_mode = {
        TargetValueBasis.NOMINAL: OutputMode.NOMINAL,
        TargetValueBasis.REAL: OutputMode.REAL,
    }[target_value_basis]
    if output_mode is not expected_output_mode:
        raise ValueError("target value basis must match projection output mode")


def _month_key(value: date) -> tuple[int, int]:
    return value.year, value.month


class GoalPlanningService:
    """Classify one governed Goal using one explicit scenario and wealth fact."""

    def __init__(
        self,
        target_solver: Optional[TargetAchievementSolver] = None,
    ) -> None:
        self._target_solver = target_solver or TargetAchievementSolver()

    def preflight_applicability(
        self,
        goal_fact: GoalPlanningFact,
        assumptions: ProjectionAssumptions,
        target_value_basis: Optional[TargetValueBasis],
        initial_wealth_fact: Optional[InitialWealthFact] = None,
    ) -> Optional[GoalPlanningResult]:
        """Return NOT_APPLICABLE before projection-specific facts are consumed."""

        if not isinstance(goal_fact, GoalPlanningFact):
            raise TypeError("goal_fact must be GoalPlanningFact")
        if not isinstance(assumptions, ProjectionAssumptions):
            raise TypeError("assumptions must be ProjectionAssumptions")
        if not isinstance(goal_fact.goal_type, GoalType):
            raise TypeError("goal_fact.goal_type must be GoalType")
        if not isinstance(goal_fact.status, GoalStatus):
            raise TypeError("goal_fact.status must be GoalStatus")

        if (
            goal_fact.status is _PROJECTABLE_GOAL_STATUS
            and goal_fact.goal_type in _ELIGIBLE_GOAL_TYPES
        ):
            return None

        return self._result(
            GoalPlanningStatus.NOT_APPLICABLE,
            goal_fact,
            initial_wealth_fact,
            assumptions,
            target_value_basis,
        )

    def evaluate(
        self,
        goal_fact: GoalPlanningFact,
        initial_wealth_fact: InitialWealthFact,
        assumptions: ProjectionAssumptions,
        target_value_basis: Optional[TargetValueBasis],
    ) -> GoalPlanningResult:
        _require_valid_inputs(
            goal_fact,
            initial_wealth_fact,
            assumptions,
        )

        applicability_result = self.preflight_applicability(
            goal_fact,
            assumptions,
            target_value_basis,
            initial_wealth_fact,
        )
        if applicability_result is not None:
            return applicability_result

        _require_matching_goal_provenance(goal_fact, initial_wealth_fact)
        _require_target_value_basis(target_value_basis)

        if target_value_basis is None:
            return self._result(
                GoalPlanningStatus.INSUFFICIENT_DATA,
                goal_fact,
                initial_wealth_fact,
                assumptions,
                target_value_basis,
            )

        _require_matching_target_basis(
            target_value_basis,
            assumptions.output_mode,
        )

        if (
            goal_fact.target_date is None
            and initial_wealth_fact.amount < goal_fact.target_amount
        ):
            return self._result(
                GoalPlanningStatus.INSUFFICIENT_DATA,
                goal_fact,
                initial_wealth_fact,
                assumptions,
                target_value_basis,
            )

        achievement = self._target_solver.solve(
            initial_wealth_fact,
            assumptions,
            goal_fact.target_amount,
        )

        if achievement.status is TargetAchievementStatus.ALREADY_ACHIEVED:
            status = GoalPlanningStatus.ALREADY_ACHIEVED
        elif achievement.status is TargetAchievementStatus.ACHIEVED:
            if goal_fact.target_date is None:  # Defensive: preflight forbids this path.
                raise RuntimeError("target date is required to classify achievement timing")
            if achievement.achievement_date is None:
                raise RuntimeError("ACHIEVED target result must contain achievement_date")
            achievement_month = _month_key(achievement.achievement_date)
            target_month = _month_key(goal_fact.target_date)
            if achievement_month < target_month:
                status = GoalPlanningStatus.PROJECTED_EARLY
            elif achievement_month == target_month:
                status = GoalPlanningStatus.PROJECTED_ON_TIME
            else:
                status = GoalPlanningStatus.PROJECTED_LATE
        else:
            status = GoalPlanningStatus.NOT_REACHED_WITHIN_HORIZON

        return self._result(
            status,
            goal_fact,
            initial_wealth_fact,
            assumptions,
            target_value_basis,
            achievement,
        )

    @staticmethod
    def _result(
        status: GoalPlanningStatus,
        goal_fact: GoalPlanningFact,
        initial_wealth_fact: Optional[InitialWealthFact],
        assumptions: ProjectionAssumptions,
        target_value_basis: Optional[TargetValueBasis],
        target_achievement_result: Optional[TargetAchievementResult] = None,
    ) -> GoalPlanningResult:
        return GoalPlanningResult(
            status=status,
            goal_fact=goal_fact,
            initial_wealth_fact=initial_wealth_fact,
            assumptions=assumptions,
            target_value_basis=target_value_basis,
            target_achievement_result=target_achievement_result,
        )
