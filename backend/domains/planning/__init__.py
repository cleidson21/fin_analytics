"""Typed Planning facts and validated projection assumptions."""

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
from backend.domains.planning.goal_planning import (
    GoalPlanningResult,
    GoalPlanningService,
    GoalPlanningStatus,
)
from backend.domains.planning.goal_batch_contribution import (
    GOAL_BATCH_CONTRIBUTION_MAX_GOALS,
    GoalBatchContributionAvailability,
    GoalBatchContributionImpediment,
    GoalBatchContributionItem,
    GoalBatchContributionPreview,
    GoalBatchContributionPreviewService,
    GoalBatchContributionSelection,
)
from backend.domains.planning.readers import (
    PlanningGoalReadQuery,
    PlanningHealthReadAdapter,
    PlanningPortfolioReadQuery,
)
from backend.domains.planning.projection import (
    ForwardProjectionEngine,
    ForwardProjectionResult,
    ProjectionPeriod,
)
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionResult,
    RequiredContributionSolver,
    RequiredContributionStatus,
)
from backend.domains.planning.scenario_comparison import (
    ScenarioArchetype,
    ScenarioComparisonEngine,
    ScenarioComparisonEntry,
    ScenarioComparisonResult,
    ScenarioDefinition,
)
from backend.domains.planning.target_solver import (
    TargetAchievementResult,
    TargetAchievementSolver,
    TargetAchievementStatus,
)
from backend.domains.planning.target_basis import TargetValueBasis

__all__ = [
    "ContributionTiming",
    "ForwardProjectionEngine",
    "ForwardProjectionResult",
    "GOAL_BATCH_CONTRIBUTION_MAX_GOALS",
    "GoalBatchContributionAvailability",
    "GoalBatchContributionImpediment",
    "GoalBatchContributionItem",
    "GoalBatchContributionPreview",
    "GoalBatchContributionPreviewService",
    "GoalBatchContributionSelection",
    "GoalPlanningFact",
    "GoalPlanningResult",
    "GoalPlanningService",
    "GoalPlanningStatus",
    "InitialWealthFact",
    "InitialWealthScope",
    "InitialWealthSource",
    "OutputMode",
    "PlanningFactAsOf",
    "PlanningFactProvenance",
    "PlanningGoalReadQuery",
    "PlanningHealthReadAdapter",
    "PlanningPortfolioReadQuery",
    "ProjectionAssumptions",
    "ProjectionPeriod",
    "RateBasis",
    "RequiredContributionResult",
    "RequiredContributionSolver",
    "RequiredContributionStatus",
    "ReturnType",
    "ScenarioArchetype",
    "ScenarioComparisonEngine",
    "ScenarioComparisonEntry",
    "ScenarioComparisonResult",
    "ScenarioDefinition",
    "TargetAchievementResult",
    "TargetAchievementSolver",
    "TargetAchievementStatus",
    "TargetValueBasis",
]
