"""Strict public Planning API DTO primitives and request boundaries."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Literal, Optional, Union
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    StrictInt,
    WithJsonSchema,
)

from backend.domains.planning.assumptions import (
    ContributionTiming,
    OutputMode,
    RateBasis,
    ReturnType,
)
from backend.domains.planning.facts import InitialWealthScope, InitialWealthSource
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionStatus,
)
from backend.domains.planning.goal_planning import GoalPlanningStatus
from backend.domains.planning.goal_monitoring import GoalDataFlag, GoalProgressState
from backend.domains.planning.target_basis import TargetValueBasis
from backend.domains.planning.target_solver import TargetAchievementStatus
from backend.domains.planning.scenario_comparison import ScenarioArchetype
from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType


_DECIMAL_STRING_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?$")
_ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISO_DATETIME_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}T")


def _parse_decimal_string(value: Any) -> Decimal:
    """Accept only finite non-exponent JSON decimal strings without coercion."""

    if type(value) is not str:
        raise ValueError("financial values must be decimal strings")
    if not _DECIMAL_STRING_PATTERN.fullmatch(value):
        raise ValueError("financial values must be plain decimal strings")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as error:  # Defensive for Decimal variants.
        raise ValueError("financial values must be valid decimal strings") from error
    if not decimal_value.is_finite():
        raise ValueError("financial values must be finite")
    return decimal_value


def _serialize_decimal(value: Decimal) -> str:
    """Serialize certified Decimal truth without float conversion or rounding."""

    if not isinstance(value, Decimal):
        raise TypeError("financial response values must be Decimal")
    if not value.is_finite():
        raise ValueError("financial response values must be finite")
    return str(value)


def _parse_iso_date(value: Any) -> date:
    if type(value) is not str or not _ISO_DATE_PATTERN.fullmatch(value):
        raise ValueError("dates must use ISO YYYY-MM-DD strings")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("dates must use valid ISO YYYY-MM-DD strings") from error


def _parse_iso_datetime(value: Any) -> datetime:
    if type(value) is not str or not _ISO_DATETIME_PREFIX.match(value):
        raise ValueError("timestamps must use ISO-8601 datetime strings")
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("timestamps must use valid ISO-8601 datetime strings") from error


StrictDecimalString = Annotated[
    Decimal,
    BeforeValidator(_parse_decimal_string, json_schema_input_type=str),
    PlainSerializer(_serialize_decimal, return_type=str, when_used="json"),
    WithJsonSchema(
        {
            "type": "string",
            "pattern": r"^-?\d+(?:\.\d+)?$",
            "description": "Finite plain decimal string; JSON numbers are not accepted.",
        }
    ),
]
"""Decimal-only JSON string primitive that preserves the declared scale."""

StrictISODate = Annotated[
    date,
    BeforeValidator(_parse_iso_date, json_schema_input_type=str),
    WithJsonSchema({"type": "string", "format": "date"}),
]
"""Date-only request primitive; datetimes are not accepted for monthly semantics."""

StrictISODatetime = Annotated[
    datetime,
    BeforeValidator(_parse_iso_datetime, json_schema_input_type=str),
    WithJsonSchema({"type": "string", "format": "date-time"}),
]
"""Explicit provenance timestamp primitive; no timestamp is manufactured."""


class _PlanningRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserProvidedInitialWealthRequestDTO(_PlanningRequestDTO):
    """Caller-provided wealth, intentionally never labeled as a certified fact."""

    source: Literal[InitialWealthSource.USER_PROVIDED_SCENARIO]
    amount: StrictDecimalString
    observed_at: StrictISODatetime


class GoalCurrentAmountInitialWealthRequestDTO(_PlanningRequestDTO):
    """A selector only; future endpoints resolve its owned Goal on the server."""

    source: Literal[InitialWealthSource.GOAL_CURRENT_AMOUNT]
    goal_id: UUID


class InvestmentPortfolioSnapshotInitialWealthRequestDTO(_PlanningRequestDTO):
    """Server-resolved ADR-023 selector with no client-certified portfolio facts."""

    source: Literal[InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT]


InitialWealthSelectorRequestDTO = Annotated[
    Union[
        UserProvidedInitialWealthRequestDTO,
        GoalCurrentAmountInitialWealthRequestDTO,
        InvestmentPortfolioSnapshotInitialWealthRequestDTO,
    ],
    Field(discriminator="source"),
]


class GoalPathCurrentAmountInitialWealthRequestDTO(_PlanningRequestDTO):
    """Path Goal selector; the client cannot select a second certified Goal."""

    source: Literal[InitialWealthSource.GOAL_CURRENT_AMOUNT]


GoalPlanningInitialWealthSelectorRequestDTO = Annotated[
    Union[
        UserProvidedInitialWealthRequestDTO,
        GoalPathCurrentAmountInitialWealthRequestDTO,
        InvestmentPortfolioSnapshotInitialWealthRequestDTO,
    ],
    Field(discriminator="source"),
]


class ProjectionAssumptionsRequestDTO(_PlanningRequestDTO):
    """Complete API echo of the immutable ProjectionAssumptions input contract."""

    as_of_date: StrictISODate
    scenario_monthly_contribution: StrictDecimalString
    expected_return_rate: StrictDecimalString
    return_type: ReturnType
    output_mode: OutputMode
    inflation_rate: Optional[StrictDecimalString] = None
    horizon_months: Optional[StrictInt] = None
    target_date: Optional[StrictISODate] = None
    rate_basis: RateBasis
    contribution_timing: ContributionTiming


class ProjectionRequestDTO(_PlanningRequestDTO):
    """Request for one transient certified forward projection."""

    initial_wealth: InitialWealthSelectorRequestDTO
    assumptions: ProjectionAssumptionsRequestDTO


class TargetAchievementRequestDTO(ProjectionRequestDTO):
    """Request for one target solve in the explicit output-value basis."""

    target_amount: StrictDecimalString
    target_value_basis: TargetValueBasis


class RequiredContributionRequestDTO(ProjectionRequestDTO):
    """Request for one certified required-contribution solve."""

    target_amount: StrictDecimalString
    target_value_basis: TargetValueBasis


class GoalPlanningRequestDTO(_PlanningRequestDTO):
    """Owned-Goal Planning request; Goal facts stay exclusively server-side."""

    initial_wealth: GoalPlanningInitialWealthSelectorRequestDTO
    assumptions: ProjectionAssumptionsRequestDTO
    target_value_basis: Optional[TargetValueBasis] = None


class ScenarioDefinitionRequestDTO(_PlanningRequestDTO):
    """One explicit ordered scenario; financial comparability stays in the domain."""

    scenario_id: str
    initial_wealth: InitialWealthSelectorRequestDTO
    assumptions: ProjectionAssumptionsRequestDTO
    label: Optional[str] = None
    archetype: Optional[ScenarioArchetype] = None


class ScenarioComparisonRequestDTO(_PlanningRequestDTO):
    """Transient request with an explicit reference and optional shared target pair."""

    scenarios: tuple[ScenarioDefinitionRequestDTO, ...]
    reference_scenario_id: str
    target_amount: Optional[StrictDecimalString] = None
    target_value_basis: Optional[TargetValueBasis] = None


class PlanningFactAsOfResponseDTO(BaseModel):
    """Public temporal anchor for a source fact."""

    reference_month: Optional[str]
    observed_at: Optional[datetime]


class PlanningFactProvenanceResponseDTO(BaseModel):
    """Public provenance excluding internal table names and SQL implementation detail."""

    source_type: Optional[str]
    goal_id: Optional[UUID]
    account_id: Optional[str]
    reference_month: Optional[str]
    run_id: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class InitialWealthFactResponseDTO(BaseModel):
    """Public, source-preserving response representation of one wealth origin."""

    source: InitialWealthSource
    amount: str
    scope: InitialWealthScope
    as_of: PlanningFactAsOfResponseDTO
    provenance: PlanningFactProvenanceResponseDTO


class ProjectionAssumptionsResponseDTO(BaseModel):
    """String-safe response echo without changing domain Decimal values."""

    as_of_date: date
    scenario_monthly_contribution: str
    expected_return_rate: str
    return_type: ReturnType
    output_mode: OutputMode
    inflation_rate: Optional[str]
    horizon_months: Optional[int]
    target_date: Optional[date]
    rate_basis: RateBasis
    contribution_timing: ContributionTiming


class ProjectionPeriodResponseDTO(BaseModel):
    """One already-calculated monthly period; all financial values are strings."""

    period: int
    period_end: date
    opening_wealth: str
    contribution: str
    projected_return: str
    ending_wealth: str
    cumulative_contributions: str
    cumulative_projected_growth: str


class ForwardProjectionResponseDTO(BaseModel):
    """Public representation of the certified ForwardProjectionResult."""

    initial_wealth_fact: InitialWealthFactResponseDTO
    assumptions: ProjectionAssumptionsResponseDTO
    effective_projection_annual_rate: str
    monthly_equivalent_rate: str
    periods: tuple[ProjectionPeriodResponseDTO, ...]
    initial_wealth: str
    final_wealth: str
    total_contributions: str
    total_projected_growth: str
    as_of_date: date
    horizon_months: int


class TargetAchievementResultResponseDTO(BaseModel):
    """Certified target result without introducing new target-crossing logic."""

    status: TargetAchievementStatus
    target_amount: str
    initial_wealth_fact: InitialWealthFactResponseDTO
    assumptions: ProjectionAssumptionsResponseDTO
    achievement_period: Optional[int]
    achievement_date: Optional[date]
    months_required: Optional[int]
    achieved_wealth: Optional[str]
    projection_result: Optional[ForwardProjectionResponseDTO]


class TargetAchievementResponseDTO(TargetAchievementResultResponseDTO):
    """Target endpoint result plus the explicitly requested target-value basis."""

    target_value_basis: TargetValueBasis


class RequiredContributionResponseDTO(BaseModel):
    """Public representation of the certified RequiredContributionResult."""

    status: RequiredContributionStatus
    target_amount: str
    target_value_basis: TargetValueBasis
    initial_wealth_fact: InitialWealthFactResponseDTO
    assumptions_template: ProjectionAssumptionsResponseDTO
    required_monthly_contribution: str
    solved_assumptions: ProjectionAssumptionsResponseDTO
    target_achievement_result: TargetAchievementResultResponseDTO


class GoalPlanningFactResponseDTO(BaseModel):
    """Public owned-Goal context, preserving Decimal values as strings."""

    goal_id: UUID
    name: str
    description: Optional[str]
    goal_type: GoalType
    status: GoalStatus
    target_amount: str
    target_date: Optional[date]
    current_amount: Optional[str]
    goal_planned_monthly_contribution: Optional[str]
    priority: Optional[int]
    linked_account_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class PlanningGoalContextResponseDTO(BaseModel):
    """Minimum owned-Goal context used only to seed transient Planning inputs."""

    goal_id: UUID
    name: str
    goal_type: GoalType
    status: GoalStatus
    target_amount: str
    current_amount: Optional[str]
    planned_monthly_contribution: Optional[str]
    target_date: Optional[date]


class GoalProgressResponseDTO(BaseModel):
    """Decimal-safe nominal cadastral progress for one owned Goal."""

    goal_id: UUID
    name: str
    target_amount: Optional[str]
    current_amount: Optional[str]
    gap_amount: Optional[str]
    completion_percent: Optional[str]


class GoalMonitoringSummaryResponseDTO(BaseModel):
    """Count-only summary over the complete owned Goal collection."""

    total_goals: int
    not_started: int
    in_progress: int
    achieved: int
    exceeded: int
    negative_current: int
    unavailable: int


class GoalMonitoringItemResponseDTO(BaseModel):
    """Goal context plus the certified R6.2 progress and factual indicators."""

    goal_id: UUID
    name: str
    goal_type: GoalType
    status: GoalStatus
    target_amount: Optional[str]
    current_amount: Optional[str]
    planned_monthly_contribution: Optional[str]
    target_date: Optional[date]
    gap_amount: Optional[str]
    completion_percent: Optional[str]
    progress_state: GoalProgressState
    data_flags: tuple[GoalDataFlag, ...]


class GoalMonitoringOverviewResponseDTO(BaseModel):
    """Complete unpaginated monitoring read model for one authenticated user."""

    summary: GoalMonitoringSummaryResponseDTO
    goals: tuple[GoalMonitoringItemResponseDTO, ...]


class GoalPlanningResponseDTO(BaseModel):
    """Certified GoalPlanningResult without HTTP-side timing or solver logic."""

    status: GoalPlanningStatus
    goal_fact: GoalPlanningFactResponseDTO
    initial_wealth_fact: Optional[InitialWealthFactResponseDTO]
    assumptions: ProjectionAssumptionsResponseDTO
    target_value_basis: Optional[TargetValueBasis]
    target_achievement_result: Optional[TargetAchievementResultResponseDTO]


class ScenarioComparisonEntryResponseDTO(BaseModel):
    """One ordered, source-preserving comparison entry from the certified engine."""

    scenario_id: str
    label: Optional[str]
    archetype: Optional[ScenarioArchetype]
    initial_wealth_fact: InitialWealthFactResponseDTO
    assumptions: ProjectionAssumptionsResponseDTO
    projection_result: ForwardProjectionResponseDTO
    target_achievement_result: Optional[TargetAchievementResultResponseDTO]
    final_wealth_delta: str
    total_contributions_delta: str
    total_projected_growth_delta: str
    months_saved_or_lost: Optional[int]


class ScenarioComparisonResponseDTO(BaseModel):
    """Complete transient comparison without ranking or persistence semantics."""

    reference_scenario_id: str
    entries: tuple[ScenarioComparisonEntryResponseDTO, ...]
    as_of_date: date
    horizon_months: int
    output_mode: OutputMode
    contribution_timing: ContributionTiming
    target_amount: Optional[str]
    target_value_basis: Optional[TargetValueBasis]
