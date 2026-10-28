"""Deterministic batch orchestration over the certified contribution solver."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence

from backend.domains.planning.assumptions import ProjectionAssumptions
from backend.domains.planning.facts import GoalPlanningFact, InitialWealthFact
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionResult,
    RequiredContributionSolver,
)


GOAL_BATCH_CONTRIBUTION_MAX_GOALS = 20


class GoalBatchContributionAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class GoalBatchContributionImpediment(str, Enum):
    TARGET_MISSING = "TARGET_MISSING"
    TARGET_NONPOSITIVE = "TARGET_NONPOSITIVE"
    CURRENT_AMOUNT_MISSING = "CURRENT_AMOUNT_MISSING"
    CURRENT_AMOUNT_NEGATIVE = "CURRENT_AMOUNT_NEGATIVE"


@dataclass(frozen=True)
class GoalBatchContributionSelection:
    """One owned Goal paired with its governed initial-wealth fact, if available."""

    goal: GoalPlanningFact
    initial_wealth_fact: Optional[InitialWealthFact]


@dataclass(frozen=True)
class GoalBatchContributionItem:
    goal: GoalPlanningFact
    availability: GoalBatchContributionAvailability
    impediment: Optional[GoalBatchContributionImpediment]
    calculation: Optional[RequiredContributionResult]


@dataclass(frozen=True)
class GoalBatchContributionPreview:
    assumptions: ProjectionAssumptions
    items: tuple[GoalBatchContributionItem, ...]


class GoalBatchContributionPreviewService:
    """Apply one certified solver independently to each ordered Goal selection."""

    def __init__(self, solver: RequiredContributionSolver) -> None:
        if not isinstance(solver, RequiredContributionSolver):
            raise TypeError("solver must be RequiredContributionSolver")
        self._solver = solver

    def preview(
        self,
        selections: Sequence[GoalBatchContributionSelection],
        assumptions: ProjectionAssumptions,
    ) -> GoalBatchContributionPreview:
        if not isinstance(assumptions, ProjectionAssumptions):
            raise TypeError("assumptions must be ProjectionAssumptions")

        ordered = tuple(selections)
        if not 1 <= len(ordered) <= GOAL_BATCH_CONTRIBUTION_MAX_GOALS:
            raise ValueError(
                "goal selections must contain between 1 and "
                f"{GOAL_BATCH_CONTRIBUTION_MAX_GOALS} items"
            )
        goal_ids = tuple(selection.goal.goal_id for selection in ordered)
        if len(set(goal_ids)) != len(goal_ids):
            raise ValueError("goal selections must not contain duplicate IDs")

        return GoalBatchContributionPreview(
            assumptions=assumptions,
            items=tuple(
                self._preview_one(selection, assumptions)
                for selection in ordered
            ),
        )

    def _preview_one(
        self,
        selection: GoalBatchContributionSelection,
        assumptions: ProjectionAssumptions,
    ) -> GoalBatchContributionItem:
        goal = selection.goal
        target = goal.target_amount
        current = goal.current_amount

        if target is None:
            return self._unavailable(
                goal,
                GoalBatchContributionImpediment.TARGET_MISSING,
            )
        if target <= 0:
            return self._unavailable(
                goal,
                GoalBatchContributionImpediment.TARGET_NONPOSITIVE,
            )
        if current is None:
            return self._unavailable(
                goal,
                GoalBatchContributionImpediment.CURRENT_AMOUNT_MISSING,
            )
        if current < 0:
            return self._unavailable(
                goal,
                GoalBatchContributionImpediment.CURRENT_AMOUNT_NEGATIVE,
            )

        initial_wealth_fact = selection.initial_wealth_fact
        if initial_wealth_fact is None:
            raise ValueError("available Goal must have an initial wealth fact")
        if initial_wealth_fact.provenance.goal_id != goal.goal_id:
            raise ValueError("initial wealth provenance must match selected Goal")
        if initial_wealth_fact.amount != current:
            raise ValueError("initial wealth amount must match selected Goal")

        return GoalBatchContributionItem(
            goal=goal,
            availability=GoalBatchContributionAvailability.AVAILABLE,
            impediment=None,
            calculation=self._solver.solve(
                initial_wealth_fact,
                assumptions,
                target,
            ),
        )

    @staticmethod
    def _unavailable(
        goal: GoalPlanningFact,
        impediment: GoalBatchContributionImpediment,
    ) -> GoalBatchContributionItem:
        return GoalBatchContributionItem(
            goal=goal,
            availability=GoalBatchContributionAvailability.UNAVAILABLE,
            impediment=impediment,
            calculation=None,
        )
