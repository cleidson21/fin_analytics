"""Transient Goal budget accounting over the certified scenario comparison."""

from dataclasses import dataclass, field, replace
from decimal import Decimal, localcontext
from typing import Optional, Sequence
from uuid import UUID

from backend.domains.planning.assumptions import (
    OutputMode,
    ProjectionAssumptions,
    ReturnType,
)
from backend.domains.planning.facts import InitialWealthSource
from backend.domains.planning.goal_batch_contribution import (
    GOAL_BATCH_CONTRIBUTION_MAX_GOALS,
    GoalBatchContributionAvailability,
    GoalBatchContributionImpediment,
    GoalBatchContributionSelection,
)
from backend.domains.planning.scenario_comparison import (
    ScenarioComparisonEngine,
    ScenarioComparisonResult,
    ScenarioDefinition,
)
from backend.domains.planning.target_basis import TargetValueBasis


def require_budget_money(value: Decimal) -> Decimal:
    """Validate explicit money without coercion, quantization or ambient math."""

    if not isinstance(value, Decimal):
        raise TypeError("budget amounts must be Decimal")
    if not value.is_finite() or value < 0 or value.as_tuple().exponent < -2:
        raise ValueError("budget amounts must be finite nonnegative cent-scale values")
    return value


@dataclass(frozen=True)
class GoalBudgetAllocation:
    goal_id: UUID
    scenario_monthly_contribution: Decimal

    def __post_init__(self) -> None:
        require_budget_money(self.scenario_monthly_contribution)


@dataclass(frozen=True)
class GoalBudgetScenario:
    scenario_id: str
    allocations: tuple[GoalBudgetAllocation, ...]


@dataclass(frozen=True)
class GoalBudgetScenarioSummary:
    scenario_id: str
    allocations: tuple[GoalBudgetAllocation, ...]
    allocated_total: Decimal
    unallocated_amount: Decimal
    exceeded_amount: Decimal


@dataclass(frozen=True)
class GoalBudgetRequest:
    """Validated ordered A/B distributions with exact, pre-read accounting."""

    goal_ids: tuple[UUID, ...]
    monthly_budget: Decimal
    scenarios: tuple[GoalBudgetScenario, ...]
    summaries: tuple[GoalBudgetScenarioSummary, ...] = field(init=False)

    def __post_init__(self) -> None:
        require_budget_money(self.monthly_budget)
        if not 1 <= len(self.goal_ids) <= GOAL_BATCH_CONTRIBUTION_MAX_GOALS:
            raise ValueError("goal_ids must contain between 1 and 20 items")
        if len(set(self.goal_ids)) != len(self.goal_ids):
            raise ValueError("goal_ids must not contain duplicates")
        if tuple(s.scenario_id for s in self.scenarios) != ("A", "B"):
            raise ValueError("scenarios must be ordered A then B")

        normalized = []
        for scenario in self.scenarios:
            by_id = {a.goal_id: a for a in scenario.allocations}
            if (
                len(by_id) != len(scenario.allocations)
                or set(by_id) != set(self.goal_ids)
            ):
                raise ValueError("each scenario must allocate to every selected Goal once")
            normalized.append(tuple(by_id[goal_id] for goal_id in self.goal_ids))

        amounts = (self.monthly_budget,) + tuple(
            a.scenario_monthly_contribution
            for allocations in normalized
            for a in allocations
        )
        # Align every supplied coefficient to cents, plus room for a batch carry.
        precision = max(
            len(value.as_tuple().digits) + value.as_tuple().exponent + 2
            for value in amounts
        ) + len(str(len(self.goal_ids))) + 1
        with localcontext() as context:
            context.prec = max(precision, 3)
            totals = tuple(
                sum((a.scenario_monthly_contribution for a in allocations), Decimal("0"))
                for allocations in normalized
            )
            if totals[0] != totals[1]:
                raise ValueError("Scenario allocated totals must be exactly equal.")
            summaries = tuple(
                GoalBudgetScenarioSummary(
                    scenario_id=scenario.scenario_id,
                    allocations=allocations,
                    allocated_total=total,
                    unallocated_amount=max(self.monthly_budget - total, Decimal("0")),
                    exceeded_amount=max(total - self.monthly_budget, Decimal("0")),
                )
                for scenario, allocations, total in zip(self.scenarios, normalized, totals)
            )
        object.__setattr__(self, "summaries", summaries)


@dataclass(frozen=True)
class GoalBudgetItem:
    selection: GoalBatchContributionSelection
    availability: GoalBatchContributionAvailability
    impediment: Optional[GoalBatchContributionImpediment]
    comparison: Optional[ScenarioComparisonResult]


@dataclass(frozen=True)
class GoalBudgetPreview:
    request: GoalBudgetRequest
    assumptions: ProjectionAssumptions
    items: tuple[GoalBudgetItem, ...]


class GoalBudgetPreviewService:
    """Compare chosen contributions independently for each owned Goal."""

    def __init__(self, engine: ScenarioComparisonEngine) -> None:
        if not isinstance(engine, ScenarioComparisonEngine):
            raise TypeError("engine must be ScenarioComparisonEngine")
        self._engine = engine

    def preview(
        self,
        selections: Sequence[GoalBatchContributionSelection],
        assumptions: ProjectionAssumptions,
        request: GoalBudgetRequest,
    ) -> GoalBudgetPreview:
        if (
            assumptions.return_type is not ReturnType.NOMINAL
            or assumptions.output_mode is not OutputMode.NOMINAL
            or assumptions.inflation_rate is not None
            or assumptions.horizon_months is None
            or assumptions.target_date is not None
        ):
            raise ValueError("budget preview requires explicit nominal monthly assumptions")
        ordered = tuple(selections)
        if tuple(s.goal.goal_id for s in ordered) != request.goal_ids:
            raise ValueError("selected Goals must match the ordered budget selection")
        return GoalBudgetPreview(
            request=request,
            assumptions=assumptions,
            items=tuple(
                self._preview_one(selection, assumptions, request, index)
                for index, selection in enumerate(ordered)
            ),
        )

    def _preview_one(
        self,
        selection: GoalBatchContributionSelection,
        assumptions: ProjectionAssumptions,
        request: GoalBudgetRequest,
        index: int,
    ) -> GoalBudgetItem:
        goal = selection.goal
        impediment = None
        if goal.target_amount is None:
            impediment = GoalBatchContributionImpediment.TARGET_MISSING
        elif goal.target_amount <= 0:
            impediment = GoalBatchContributionImpediment.TARGET_NONPOSITIVE
        elif goal.current_amount is None:
            impediment = GoalBatchContributionImpediment.CURRENT_AMOUNT_MISSING
        elif goal.current_amount < 0:
            impediment = GoalBatchContributionImpediment.CURRENT_AMOUNT_NEGATIVE
        if impediment is not None:
            return GoalBudgetItem(
                selection, GoalBatchContributionAvailability.UNAVAILABLE, impediment, None
            )

        fact = selection.initial_wealth_fact
        if (
            fact is None
            or fact.provenance.goal_id != goal.goal_id
            or fact.amount != goal.current_amount
            or fact.source is not InitialWealthSource.GOAL_CURRENT_AMOUNT
        ):
            raise ValueError("initial wealth fact must match the selected Goal")
        scenarios = tuple(
            ScenarioDefinition(
                scenario_id=summary.scenario_id,
                initial_wealth_fact=fact,
                assumptions=replace(
                    assumptions,
                    scenario_monthly_contribution=(
                        summary.allocations[index].scenario_monthly_contribution
                    ),
                ),
            )
            for summary in request.summaries
        )
        return GoalBudgetItem(
            selection=selection,
            availability=GoalBatchContributionAvailability.AVAILABLE,
            impediment=None,
            comparison=self._engine.compare(
                scenarios=scenarios,
                reference_scenario_id="A",
                target_amount=goal.target_amount,
                target_value_basis=TargetValueBasis.NOMINAL,
            ),
        )
