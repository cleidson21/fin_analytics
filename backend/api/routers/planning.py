"""Authenticated transient endpoints over the certified Planning engines."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies.planning import CurrentPlanningUser, PlanningReadSession
from backend.api.planning_errors import raise_planning_error
from backend.api.planning_mapping import (
    build_projection_assumptions,
    build_user_initial_wealth_fact,
    map_forward_projection_result,
    map_goal_planning_result,
    map_required_contribution_result,
    map_scenario_comparison_result,
    map_target_achievement_response,
)
from backend.application.dtos.planning_dto import (
    ForwardProjectionResponseDTO,
    GoalPathCurrentAmountInitialWealthRequestDTO,
    GoalPlanningRequestDTO,
    GoalPlanningResponseDTO,
    GoalCurrentAmountInitialWealthRequestDTO,
    InvestmentPortfolioSnapshotInitialWealthRequestDTO,
    InitialWealthSelectorRequestDTO,
    ProjectionRequestDTO,
    RequiredContributionRequestDTO,
    RequiredContributionResponseDTO,
    ScenarioComparisonRequestDTO,
    ScenarioComparisonResponseDTO,
    ScenarioDefinitionRequestDTO,
    TargetAchievementRequestDTO,
    TargetAchievementResponseDTO,
    UserProvidedInitialWealthRequestDTO,
)
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.services.planning_portfolio_source_resolver import (
    PlanningPortfolioSourceResolver,
)
from backend.domains.planning.assumptions import OutputMode, ProjectionAssumptions
from backend.domains.planning.facts import InitialWealthFact
from backend.domains.planning.goal_planning import GoalPlanningService
from backend.domains.planning.projection import ForwardProjectionEngine
from backend.domains.planning.readers import PlanningGoalReadQuery
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionSolver,
)
from backend.domains.planning.scenario_comparison import (
    ScenarioComparisonEngine,
    ScenarioDefinition,
)
from backend.domains.planning.target_basis import TargetValueBasis
from backend.domains.planning.target_solver import TargetAchievementSolver


router = APIRouter(prefix="/planning", tags=["Planning"])


def get_forward_projection_engine() -> ForwardProjectionEngine:
    """Provide one stateless certified engine per HTTP calculation request."""

    return ForwardProjectionEngine()


def get_target_achievement_solver() -> TargetAchievementSolver:
    """Provide the certified target solver without API-side projection logic."""

    return TargetAchievementSolver()


def get_required_contribution_solver() -> RequiredContributionSolver:
    """Provide the certified inverse solver without API-side searching."""

    return RequiredContributionSolver()


def get_goal_planning_service() -> GoalPlanningService:
    """Provide the certified Goal Planning orchestrator without API-side rules."""

    return GoalPlanningService()


def get_scenario_comparison_engine() -> ScenarioComparisonEngine:
    """Provide the certified transient comparison engine without HTTP-side math."""

    return ScenarioComparisonEngine()


def get_planning_goal_read_query() -> PlanningGoalReadQuery:
    """Provide the Decimal-safe direct Goal reader for the selected source."""

    return PlanningGoalReadQuery()


def get_planning_portfolio_source_resolver() -> PlanningPortfolioSourceResolver:
    """Provide the ADR-023 resolver, which owns portfolio scope selection."""

    return PlanningPortfolioSourceResolver()


ForwardProjectionEngineDependency = Annotated[
    ForwardProjectionEngine,
    Depends(get_forward_projection_engine),
]
TargetAchievementSolverDependency = Annotated[
    TargetAchievementSolver,
    Depends(get_target_achievement_solver),
]
RequiredContributionSolverDependency = Annotated[
    RequiredContributionSolver,
    Depends(get_required_contribution_solver),
]
GoalPlanningServiceDependency = Annotated[
    GoalPlanningService,
    Depends(get_goal_planning_service),
]
ScenarioComparisonEngineDependency = Annotated[
    ScenarioComparisonEngine,
    Depends(get_scenario_comparison_engine),
]
PlanningGoalReadQueryDependency = Annotated[
    PlanningGoalReadQuery,
    Depends(get_planning_goal_read_query),
]
PlanningPortfolioSourceResolverDependency = Annotated[
    PlanningPortfolioSourceResolver,
    Depends(get_planning_portfolio_source_resolver),
]


def _require_matching_target_basis(
    target_value_basis: TargetValueBasis,
    assumptions: ProjectionAssumptions,
) -> None:
    """Enforce the ADR-020 value-unit match; never convert the target."""

    expected_output_mode = {
        TargetValueBasis.NOMINAL: OutputMode.NOMINAL,
        TargetValueBasis.REAL: OutputMode.REAL,
    }[target_value_basis]
    if assumptions.output_mode is not expected_output_mode:
        raise ValueError("target value basis must match projection output mode")


def _resolve_initial_wealth_fact(
    selector: InitialWealthSelectorRequestDTO,
    current_user: UserResponseDTO,
    db: PlanningReadSession,
    goal_reader: PlanningGoalReadQuery,
    portfolio_resolver: PlanningPortfolioSourceResolver,
    as_of_date: date,
) -> InitialWealthFact:
    """Resolve one explicit origin; certified Goal values always come server-side."""

    if isinstance(selector, UserProvidedInitialWealthRequestDTO):
        return build_user_initial_wealth_fact(selector)

    if isinstance(selector, GoalCurrentAmountInitialWealthRequestDTO):
        goal = goal_reader.get_goal(db, selector.goal_id, current_user.id)
        if goal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found.",
            )
        fact = goal_reader.current_amount_as_initial_wealth(goal)
        if fact is None:
            raise ValueError("selected Goal current amount is unavailable")
        return fact

    if isinstance(selector, InvestmentPortfolioSnapshotInitialWealthRequestDTO):
        return portfolio_resolver.resolve(db, current_user.id, as_of_date)

    raise TypeError("unsupported initial wealth source")


def _resolve_goal_planning_initial_wealth_fact(
    selector: UserProvidedInitialWealthRequestDTO
    | GoalPathCurrentAmountInitialWealthRequestDTO,
    goal_fact,
    current_user: UserResponseDTO,
    db: PlanningReadSession,
    goal_reader: PlanningGoalReadQuery,
    portfolio_resolver: PlanningPortfolioSourceResolver,
    as_of_date: date,
) -> InitialWealthFact:
    """Resolve one Goal endpoint source; path Goal is the only Goal identity."""

    if isinstance(selector, UserProvidedInitialWealthRequestDTO):
        return build_user_initial_wealth_fact(selector)

    if isinstance(selector, GoalPathCurrentAmountInitialWealthRequestDTO):
        fact = goal_reader.current_amount_as_initial_wealth(goal_fact)
        if fact is None:
            raise ValueError("selected Goal current amount is unavailable")
        return fact

    if isinstance(selector, InvestmentPortfolioSnapshotInitialWealthRequestDTO):
        return portfolio_resolver.resolve(db, current_user.id, as_of_date)

    raise TypeError("unsupported initial wealth source")


def _build_scenario_definitions(
    requests: tuple[ScenarioDefinitionRequestDTO, ...],
    current_user: UserResponseDTO,
    db: PlanningReadSession,
    goal_reader: PlanningGoalReadQuery,
    portfolio_resolver: PlanningPortfolioSourceResolver,
) -> tuple[ScenarioDefinition, ...]:
    """Resolve every selected source before one atomic domain comparison call."""

    return tuple(
        _build_scenario_definition(
            request,
            current_user,
            db,
            goal_reader,
            portfolio_resolver,
        )
        for request in requests
    )


def _build_scenario_definition(
    request: ScenarioDefinitionRequestDTO,
    current_user: UserResponseDTO,
    db: PlanningReadSession,
    goal_reader: PlanningGoalReadQuery,
    portfolio_resolver: PlanningPortfolioSourceResolver,
) -> ScenarioDefinition:
    """Build one scenario after its own assumptions establish the portfolio as-of."""

    assumptions = build_projection_assumptions(request.assumptions)
    return ScenarioDefinition(
        scenario_id=request.scenario_id,
        initial_wealth_fact=_resolve_initial_wealth_fact(
            request.initial_wealth,
            current_user,
            db,
            goal_reader,
            portfolio_resolver,
            assumptions.as_of_date,
        ),
        assumptions=assumptions,
        label=request.label,
        archetype=request.archetype,
    )


@router.post("/projection", response_model=ForwardProjectionResponseDTO)
async def project(
    request: ProjectionRequestDTO,
    current_user: CurrentPlanningUser,
    db: PlanningReadSession,
    goal_reader: PlanningGoalReadQueryDependency,
    portfolio_resolver: PlanningPortfolioSourceResolverDependency,
    engine: ForwardProjectionEngineDependency,
) -> ForwardProjectionResponseDTO:
    """Delegate one generic projection to the certified forward engine."""

    try:
        assumptions = build_projection_assumptions(request.assumptions)
        initial_wealth_fact = _resolve_initial_wealth_fact(
            request.initial_wealth,
            current_user,
            db,
            goal_reader,
            portfolio_resolver,
            assumptions.as_of_date,
        )
        return map_forward_projection_result(
            engine.project(initial_wealth_fact, assumptions)
        )
    except HTTPException:
        raise
    except Exception as error:
        raise_planning_error(error)


@router.post(
    "/target-achievement",
    response_model=TargetAchievementResponseDTO,
)
async def target_achievement(
    request: TargetAchievementRequestDTO,
    current_user: CurrentPlanningUser,
    db: PlanningReadSession,
    goal_reader: PlanningGoalReadQueryDependency,
    portfolio_resolver: PlanningPortfolioSourceResolverDependency,
    solver: TargetAchievementSolverDependency,
) -> TargetAchievementResponseDTO:
    """Delegate one target solve without a second API-side projection."""

    try:
        assumptions = build_projection_assumptions(request.assumptions)
        initial_wealth_fact = _resolve_initial_wealth_fact(
            request.initial_wealth,
            current_user,
            db,
            goal_reader,
            portfolio_resolver,
            assumptions.as_of_date,
        )
        _require_matching_target_basis(request.target_value_basis, assumptions)
        result = solver.solve(
            initial_wealth_fact,
            assumptions,
            request.target_amount,
        )
        return map_target_achievement_response(result, request.target_value_basis)
    except HTTPException:
        raise
    except Exception as error:
        raise_planning_error(error)


@router.post(
    "/required-contribution",
    response_model=RequiredContributionResponseDTO,
)
async def required_contribution(
    request: RequiredContributionRequestDTO,
    current_user: CurrentPlanningUser,
    db: PlanningReadSession,
    goal_reader: PlanningGoalReadQueryDependency,
    portfolio_resolver: PlanningPortfolioSourceResolverDependency,
    solver: RequiredContributionSolverDependency,
) -> RequiredContributionResponseDTO:
    """Delegate one inverse solve without API-side cent search or rounding."""

    try:
        assumptions = build_projection_assumptions(request.assumptions)
        initial_wealth_fact = _resolve_initial_wealth_fact(
            request.initial_wealth,
            current_user,
            db,
            goal_reader,
            portfolio_resolver,
            assumptions.as_of_date,
        )
        _require_matching_target_basis(request.target_value_basis, assumptions)
        result = solver.solve(
            initial_wealth_fact,
            assumptions,
            request.target_amount,
        )
        return map_required_contribution_result(
            result,
            request.target_value_basis,
        )
    except HTTPException:
        raise
    except Exception as error:
        raise_planning_error(error)


@router.post(
    "/goals/{goal_id}/projection",
    response_model=GoalPlanningResponseDTO,
)
async def goal_projection(
    goal_id: UUID,
    request: GoalPlanningRequestDTO,
    current_user: CurrentPlanningUser,
    db: PlanningReadSession,
    goal_reader: PlanningGoalReadQueryDependency,
    portfolio_resolver: PlanningPortfolioSourceResolverDependency,
    service: GoalPlanningServiceDependency,
) -> GoalPlanningResponseDTO:
    """Evaluate one owned Goal through the certified Goal Planning service."""

    try:
        goal_fact = goal_reader.get_goal(db, goal_id, current_user.id)
        if goal_fact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found.",
            )
        assumptions = build_projection_assumptions(request.assumptions)
        applicability_result = service.preflight_applicability(
            goal_fact,
            assumptions,
            request.target_value_basis,
        )
        if applicability_result is not None:
            return map_goal_planning_result(applicability_result)
        initial_wealth_fact = _resolve_goal_planning_initial_wealth_fact(
            request.initial_wealth,
            goal_fact,
            current_user,
            db,
            goal_reader,
            portfolio_resolver,
            assumptions.as_of_date,
        )
        return map_goal_planning_result(
            service.evaluate(
                goal_fact,
                initial_wealth_fact,
                assumptions,
                request.target_value_basis,
            )
        )
    except HTTPException:
        raise
    except Exception as error:
        raise_planning_error(error)


@router.post(
    "/scenarios/compare",
    response_model=ScenarioComparisonResponseDTO,
)
async def compare_scenarios(
    request: ScenarioComparisonRequestDTO,
    current_user: CurrentPlanningUser,
    db: PlanningReadSession,
    goal_reader: PlanningGoalReadQueryDependency,
    portfolio_resolver: PlanningPortfolioSourceResolverDependency,
    engine: ScenarioComparisonEngineDependency,
) -> ScenarioComparisonResponseDTO:
    """Resolve explicit sources then delegate one ordered transient comparison."""

    try:
        scenarios = _build_scenario_definitions(
            request.scenarios,
            current_user,
            db,
            goal_reader,
            portfolio_resolver,
        )
        return map_scenario_comparison_result(
            engine.compare(
                scenarios,
                request.reference_scenario_id,
                request.target_amount,
                request.target_value_basis,
            )
        )
    except HTTPException:
        raise
    except Exception as error:
        raise_planning_error(error)
