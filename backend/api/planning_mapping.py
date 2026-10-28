"""Pure Planning API/domain builders and serializers; no database or financial math."""

from decimal import Decimal

from backend.application.services.planning_initial_wealth_fact_builder import (
    build_user_initial_wealth_fact as _build_user_initial_wealth_fact,
)
from backend.application.dtos.planning_dto import (
    ForwardProjectionResponseDTO,
    GoalProgressResponseDTO,
    GoalPlanningFactResponseDTO,
    GoalPlanningResponseDTO,
    InitialWealthFactResponseDTO,
    PlanningFactAsOfResponseDTO,
    PlanningFactProvenanceResponseDTO,
    ProjectionPeriodResponseDTO,
    ProjectionAssumptionsRequestDTO,
    ProjectionAssumptionsResponseDTO,
    PlanningGoalContextResponseDTO,
    RequiredContributionResponseDTO,
    ScenarioComparisonEntryResponseDTO,
    ScenarioComparisonResponseDTO,
    TargetAchievementResponseDTO,
    TargetAchievementResultResponseDTO,
    UserProvidedInitialWealthRequestDTO,
)
from backend.domains.planning.assumptions import ProjectionAssumptions
from backend.domains.planning.facts import (
    GoalPlanningFact,
    InitialWealthFact,
)
from backend.domains.planning.projection import (
    ForwardProjectionResult,
    ProjectionPeriod,
)
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionResult,
)
from backend.domains.planning.goal_planning import GoalPlanningResult
from backend.domains.planning.goal_progress import GoalProgressResult
from backend.domains.planning.scenario_comparison import (
    ScenarioComparisonEntry,
    ScenarioComparisonResult,
)
from backend.domains.planning.target_basis import TargetValueBasis
from backend.domains.planning.target_solver import TargetAchievementResult


def serialize_decimal(value: Decimal) -> str:
    """Return Decimal's exact declared representation without financial formatting."""

    if not isinstance(value, Decimal):
        raise TypeError("financial response values must be Decimal")
    if not value.is_finite():
        raise ValueError("financial response values must be finite")
    return str(value)


def build_projection_assumptions(
    request: ProjectionAssumptionsRequestDTO,
) -> ProjectionAssumptions:
    """Map a structurally valid request to the domain, retaining domain validation."""

    return ProjectionAssumptions(
        as_of_date=request.as_of_date,
        scenario_monthly_contribution=request.scenario_monthly_contribution,
        expected_return_rate=request.expected_return_rate,
        return_type=request.return_type,
        output_mode=request.output_mode,
        inflation_rate=request.inflation_rate,
        horizon_months=request.horizon_months,
        target_date=request.target_date,
        rate_basis=request.rate_basis,
        contribution_timing=request.contribution_timing,
    )


def build_user_initial_wealth_fact(
    request: UserProvidedInitialWealthRequestDTO,
) -> InitialWealthFact:
    """Create the single allowed caller-provided fact without certified provenance."""

    return _build_user_initial_wealth_fact(
        amount=request.amount,
        observed_at=request.observed_at,
    )


def map_initial_wealth_fact(
    fact: InitialWealthFact,
) -> InitialWealthFactResponseDTO:
    """Expose approved source provenance without internal source_table metadata."""

    return InitialWealthFactResponseDTO(
        source=fact.source,
        amount=serialize_decimal(fact.amount),
        scope=fact.scope,
        as_of=PlanningFactAsOfResponseDTO(
            reference_month=fact.as_of.reference_month,
            observed_at=fact.as_of.observed_at,
        ),
        provenance=PlanningFactProvenanceResponseDTO(
            source_type=fact.provenance.source_type,
            goal_id=fact.provenance.goal_id,
            account_id=fact.provenance.account_id,
            reference_month=fact.provenance.reference_month,
            run_id=fact.provenance.run_id,
            created_at=fact.provenance.created_at,
            updated_at=fact.provenance.updated_at,
        ),
    )


def map_projection_assumptions(
    assumptions: ProjectionAssumptions,
) -> ProjectionAssumptionsResponseDTO:
    """Return the exact assumptions used by a certified domain result."""

    return ProjectionAssumptionsResponseDTO(
        as_of_date=assumptions.as_of_date,
        scenario_monthly_contribution=serialize_decimal(
            assumptions.scenario_monthly_contribution
        ),
        expected_return_rate=serialize_decimal(assumptions.expected_return_rate),
        return_type=assumptions.return_type,
        output_mode=assumptions.output_mode,
        inflation_rate=(
            None
            if assumptions.inflation_rate is None
            else serialize_decimal(assumptions.inflation_rate)
        ),
        horizon_months=assumptions.horizon_months,
        target_date=assumptions.target_date,
        rate_basis=assumptions.rate_basis,
        contribution_timing=assumptions.contribution_timing,
    )


def map_projection_period(period: ProjectionPeriod) -> ProjectionPeriodResponseDTO:
    """Copy one certified projection period without recalculating it."""

    return ProjectionPeriodResponseDTO(
        period=period.period,
        period_end=period.period_end,
        opening_wealth=serialize_decimal(period.opening_wealth),
        contribution=serialize_decimal(period.contribution),
        projected_return=serialize_decimal(period.projected_return),
        ending_wealth=serialize_decimal(period.ending_wealth),
        cumulative_contributions=serialize_decimal(period.cumulative_contributions),
        cumulative_projected_growth=serialize_decimal(
            period.cumulative_projected_growth
        ),
    )


def map_forward_projection_result(
    result: ForwardProjectionResult,
) -> ForwardProjectionResponseDTO:
    """Map the complete already-certified projection result to its API boundary."""

    return ForwardProjectionResponseDTO(
        initial_wealth_fact=map_initial_wealth_fact(result.initial_wealth_fact),
        assumptions=map_projection_assumptions(result.assumptions),
        effective_projection_annual_rate=serialize_decimal(
            result.effective_projection_annual_rate
        ),
        monthly_equivalent_rate=serialize_decimal(result.monthly_equivalent_rate),
        periods=tuple(map_projection_period(period) for period in result.periods),
        initial_wealth=serialize_decimal(result.initial_wealth),
        final_wealth=serialize_decimal(result.final_wealth),
        total_contributions=serialize_decimal(result.total_contributions),
        total_projected_growth=serialize_decimal(result.total_projected_growth),
        as_of_date=result.as_of_date,
        horizon_months=result.horizon_months,
    )


def map_target_achievement_result(
    result: TargetAchievementResult,
) -> TargetAchievementResultResponseDTO:
    """Copy certified target status and optional nested projection exactly once."""

    return TargetAchievementResultResponseDTO(
        status=result.status,
        target_amount=serialize_decimal(result.target_amount),
        initial_wealth_fact=map_initial_wealth_fact(result.initial_wealth_fact),
        assumptions=map_projection_assumptions(result.assumptions),
        achievement_period=result.achievement_period,
        achievement_date=result.achievement_date,
        months_required=result.months_required,
        achieved_wealth=(
            None
            if result.achieved_wealth is None
            else serialize_decimal(result.achieved_wealth)
        ),
        projection_result=(
            None
            if result.projection_result is None
            else map_forward_projection_result(result.projection_result)
        ),
    )


def map_target_achievement_response(
    result: TargetAchievementResult,
    target_value_basis: TargetValueBasis,
) -> TargetAchievementResponseDTO:
    """Return the target result with the explicit basis supplied by the caller."""

    return TargetAchievementResponseDTO(
        **map_target_achievement_result(result).model_dump(),
        target_value_basis=target_value_basis,
    )


def map_required_contribution_result(
    result: RequiredContributionResult,
    target_value_basis: TargetValueBasis,
) -> RequiredContributionResponseDTO:
    """Copy certified inverse-solver output without searching or rounding again."""

    return RequiredContributionResponseDTO(
        status=result.status,
        target_amount=serialize_decimal(result.target_amount),
        target_value_basis=target_value_basis,
        initial_wealth_fact=map_initial_wealth_fact(result.initial_wealth_fact),
        assumptions_template=map_projection_assumptions(result.assumptions_template),
        required_monthly_contribution=serialize_decimal(
            result.required_monthly_contribution
        ),
        solved_assumptions=map_projection_assumptions(result.solved_assumptions),
        target_achievement_result=map_target_achievement_result(
            result.target_achievement_result
        ),
    )


def map_goal_planning_fact(goal_fact: GoalPlanningFact) -> GoalPlanningFactResponseDTO:
    """Copy the owned Goal Planning read fact without exposing user/ORM internals."""

    return GoalPlanningFactResponseDTO(
        goal_id=goal_fact.goal_id,
        name=goal_fact.name,
        description=goal_fact.description,
        goal_type=goal_fact.goal_type,
        status=goal_fact.status,
        target_amount=serialize_decimal(goal_fact.target_amount),
        target_date=goal_fact.target_date,
        current_amount=(
            None
            if goal_fact.current_amount is None
            else serialize_decimal(goal_fact.current_amount)
        ),
        goal_planned_monthly_contribution=(
            None
            if goal_fact.goal_planned_monthly_contribution is None
            else serialize_decimal(goal_fact.goal_planned_monthly_contribution)
        ),
        priority=goal_fact.priority,
        linked_account_id=goal_fact.linked_account_id,
        created_at=goal_fact.created_at,
        updated_at=goal_fact.updated_at,
    )


def map_planning_goal_context(
    goal_fact: GoalPlanningFact,
) -> PlanningGoalContextResponseDTO:
    """Copy the approved eight-field Goal context without deriving new facts."""

    return PlanningGoalContextResponseDTO(
        goal_id=goal_fact.goal_id,
        name=goal_fact.name,
        goal_type=goal_fact.goal_type,
        status=goal_fact.status,
        target_amount=serialize_decimal(goal_fact.target_amount),
        current_amount=(
            None
            if goal_fact.current_amount is None
            else serialize_decimal(goal_fact.current_amount)
        ),
        planned_monthly_contribution=(
            None
            if goal_fact.goal_planned_monthly_contribution is None
            else serialize_decimal(goal_fact.goal_planned_monthly_contribution)
        ),
        target_date=goal_fact.target_date,
    )


def map_goal_progress(
    goal_fact: GoalPlanningFact,
    progress: GoalProgressResult,
) -> GoalProgressResponseDTO:
    """Serialize the pure R6.2 result without legacy float/capping semantics."""

    return GoalProgressResponseDTO(
        goal_id=goal_fact.goal_id,
        name=goal_fact.name,
        target_amount=(
            None
            if progress.target_amount is None
            else serialize_decimal(progress.target_amount)
        ),
        current_amount=(
            None
            if progress.current_amount is None
            else serialize_decimal(progress.current_amount)
        ),
        gap_amount=(
            None
            if progress.gap_amount is None
            else serialize_decimal(progress.gap_amount)
        ),
        completion_percent=(
            None
            if progress.completion_percent is None
            else serialize_decimal(progress.completion_percent)
        ),
    )


def map_goal_planning_result(result: GoalPlanningResult) -> GoalPlanningResponseDTO:
    """Copy certified Goal Planning output without eligibility or timing logic."""

    return GoalPlanningResponseDTO(
        status=result.status,
        goal_fact=map_goal_planning_fact(result.goal_fact),
        initial_wealth_fact=(
            None
            if result.initial_wealth_fact is None
            else map_initial_wealth_fact(result.initial_wealth_fact)
        ),
        assumptions=map_projection_assumptions(result.assumptions),
        target_value_basis=result.target_value_basis,
        target_achievement_result=(
            None
            if result.target_achievement_result is None
            else map_target_achievement_result(result.target_achievement_result)
        ),
    )


def map_scenario_comparison_entry(
    entry: ScenarioComparisonEntry,
) -> ScenarioComparisonEntryResponseDTO:
    """Copy one domain-owned comparison entry without deriving deltas or ranking."""

    return ScenarioComparisonEntryResponseDTO(
        scenario_id=entry.scenario_id,
        label=entry.label,
        archetype=entry.archetype,
        initial_wealth_fact=map_initial_wealth_fact(entry.initial_wealth_fact),
        assumptions=map_projection_assumptions(entry.assumptions),
        projection_result=map_forward_projection_result(entry.projection_result),
        target_achievement_result=(
            None
            if entry.target_achievement_result is None
            else map_target_achievement_result(entry.target_achievement_result)
        ),
        final_wealth_delta=serialize_decimal(entry.final_wealth_delta),
        total_contributions_delta=serialize_decimal(entry.total_contributions_delta),
        total_projected_growth_delta=serialize_decimal(
            entry.total_projected_growth_delta
        ),
        months_saved_or_lost=entry.months_saved_or_lost,
    )


def map_scenario_comparison_result(
    result: ScenarioComparisonResult,
) -> ScenarioComparisonResponseDTO:
    """Expose the immutable comparison result in its certified input order."""

    return ScenarioComparisonResponseDTO(
        reference_scenario_id=result.reference_scenario_id,
        entries=tuple(map_scenario_comparison_entry(entry) for entry in result.entries),
        as_of_date=result.as_of_date,
        horizon_months=result.horizon_months,
        output_mode=result.output_mode,
        contribution_timing=result.contribution_timing,
        target_amount=(
            None
            if result.target_amount is None
            else serialize_decimal(result.target_amount)
        ),
        target_value_basis=result.target_value_basis,
    )
