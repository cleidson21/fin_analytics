"""Transient, deterministic comparison over certified Planning engines."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, Sequence

from backend.domains.planning.assumptions import (
    ContributionTiming,
    OutputMode,
    ProjectionAssumptions,
)
from backend.domains.planning.facts import InitialWealthFact
from backend.domains.planning.projection import (
    ForwardProjectionEngine,
    ForwardProjectionResult,
)
from backend.domains.planning.target_basis import TargetValueBasis
from backend.domains.planning.target_solver import (
    TargetAchievementResult,
    TargetAchievementSolver,
    TargetAchievementStatus,
)


_MONEY_ZERO = Decimal("0.00")
_ZERO = Decimal("0")
_ACHIEVED_STATUSES = frozenset(
    {
        TargetAchievementStatus.ALREADY_ACHIEVED,
        TargetAchievementStatus.ACHIEVED,
    }
)


class ScenarioArchetype(str, Enum):
    """Optional metadata only; it never supplies assumptions or a ranking."""

    CONSERVATIVE = "CONSERVATIVE"
    BASE = "BASE"
    OPTIMISTIC = "OPTIMISTIC"


@dataclass(frozen=True)
class ScenarioDefinition:
    """One explicit, source-preserving Planning scenario."""

    scenario_id: str
    initial_wealth_fact: InitialWealthFact
    assumptions: ProjectionAssumptions
    label: Optional[str] = None
    archetype: Optional[ScenarioArchetype] = None

    def __post_init__(self) -> None:
        if type(self.scenario_id) is not str or not self.scenario_id:
            raise ValueError("scenario_id must be a non-empty string")
        if not isinstance(self.initial_wealth_fact, InitialWealthFact):
            raise TypeError("initial_wealth_fact must be InitialWealthFact")
        if not isinstance(self.assumptions, ProjectionAssumptions):
            raise TypeError("assumptions must be ProjectionAssumptions")
        if self.label is not None and type(self.label) is not str:
            raise TypeError("label must be a string or None")
        if self.archetype is not None and not isinstance(
            self.archetype,
            ScenarioArchetype,
        ):
            raise TypeError("archetype must be ScenarioArchetype or None")


@dataclass(frozen=True)
class ScenarioComparisonEntry:
    """One ordered comparison result preserving certified nested outputs."""

    scenario: ScenarioDefinition
    projection_result: ForwardProjectionResult
    target_achievement_result: Optional[TargetAchievementResult]
    final_wealth_delta: Decimal
    total_contributions_delta: Decimal
    total_projected_growth_delta: Decimal
    months_saved_or_lost: Optional[int]

    @property
    def scenario_id(self) -> str:
        return self.scenario.scenario_id

    @property
    def label(self) -> Optional[str]:
        return self.scenario.label

    @property
    def archetype(self) -> Optional[ScenarioArchetype]:
        return self.scenario.archetype

    @property
    def initial_wealth_fact(self) -> InitialWealthFact:
        return self.scenario.initial_wealth_fact

    @property
    def assumptions(self) -> ProjectionAssumptions:
        return self.scenario.assumptions

    @property
    def final_wealth(self) -> Decimal:
        return self.projection_result.final_wealth

    @property
    def total_contributions(self) -> Decimal:
        return self.projection_result.total_contributions

    @property
    def total_projected_growth(self) -> Decimal:
        return self.projection_result.total_projected_growth


@dataclass(frozen=True)
class ScenarioComparisonResult:
    """Immutable transient comparison with explicit shared semantics."""

    reference_scenario_id: str
    entries: tuple[ScenarioComparisonEntry, ...]
    as_of_date: date
    horizon_months: int
    output_mode: OutputMode
    contribution_timing: ContributionTiming
    target_amount: Optional[Decimal]
    target_value_basis: Optional[TargetValueBasis]


def _require_reference_id(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError("reference_scenario_id must be a non-empty string")
    return value


def _require_valid_target_amount(target_amount: object) -> Decimal:
    if not isinstance(target_amount, Decimal):
        raise TypeError("target_amount must be Decimal")
    if not target_amount.is_finite():
        raise ValueError("target_amount must be finite")
    if target_amount <= _ZERO:
        raise ValueError("target_amount must be greater than zero")
    if target_amount.as_tuple().exponent < -2:
        raise ValueError("target_amount must have at most two decimal places")
    return target_amount


def _validate_target_pair(
    target_amount: Optional[Decimal],
    target_value_basis: Optional[TargetValueBasis],
    output_mode: OutputMode,
) -> None:
    if (target_amount is None) != (target_value_basis is None):
        raise ValueError("target_amount and target_value_basis must be provided together")
    if target_amount is None:
        return

    _require_valid_target_amount(target_amount)
    if not isinstance(target_value_basis, TargetValueBasis):
        raise TypeError("target_value_basis must be TargetValueBasis")

    expected_output_mode = {
        TargetValueBasis.NOMINAL: OutputMode.NOMINAL,
        TargetValueBasis.REAL: OutputMode.REAL,
    }[target_value_basis]
    if output_mode is not expected_output_mode:
        raise ValueError("target value basis must match projection output mode")


def _validate_scenarios(
    scenarios: Sequence[ScenarioDefinition],
    reference_scenario_id: object,
    target_amount: Optional[Decimal],
    target_value_basis: Optional[TargetValueBasis],
) -> tuple[ScenarioDefinition, ...]:
    if not isinstance(scenarios, Sequence) or isinstance(scenarios, (str, bytes)):
        raise TypeError("scenarios must be an ordered sequence of ScenarioDefinition")

    immutable_scenarios = tuple(scenarios)
    if len(immutable_scenarios) < 2:
        raise ValueError("scenario comparison requires at least two scenarios")
    if not all(isinstance(scenario, ScenarioDefinition) for scenario in immutable_scenarios):
        raise TypeError("scenarios must contain ScenarioDefinition values")

    reference_id = _require_reference_id(reference_scenario_id)
    scenario_ids = tuple(scenario.scenario_id for scenario in immutable_scenarios)
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("scenario_ids must be unique within a comparison")
    if reference_id not in scenario_ids:
        raise ValueError("reference_scenario_id must identify a supplied scenario")

    reference_assumptions = immutable_scenarios[0].assumptions
    for scenario in immutable_scenarios[1:]:
        assumptions = scenario.assumptions
        if assumptions.as_of_date != reference_assumptions.as_of_date:
            raise ValueError("all scenarios must share as_of_date")
        if (
            assumptions.resolved_horizon_months
            != reference_assumptions.resolved_horizon_months
        ):
            raise ValueError("all scenarios must share resolved_horizon_months")
        if assumptions.output_mode is not reference_assumptions.output_mode:
            raise ValueError("all scenarios must share output_mode")
        if assumptions.contribution_timing is not reference_assumptions.contribution_timing:
            raise ValueError("all scenarios must share contribution_timing")

    _validate_target_pair(
        target_amount,
        target_value_basis,
        reference_assumptions.output_mode,
    )
    return immutable_scenarios


def _months_saved_or_lost(
    reference: Optional[TargetAchievementResult],
    candidate: Optional[TargetAchievementResult],
) -> Optional[int]:
    if reference is None or candidate is None:
        return None
    if (
        reference.status not in _ACHIEVED_STATUSES
        or candidate.status not in _ACHIEVED_STATUSES
    ):
        return None
    if reference.months_required is None or candidate.months_required is None:
        raise RuntimeError("achieved target result must contain months_required")
    return reference.months_required - candidate.months_required


class ScenarioComparisonEngine:
    """Compare explicit Planning scenarios without creating financial math."""

    def __init__(
        self,
        projection_engine: Optional[ForwardProjectionEngine] = None,
        target_solver: Optional[TargetAchievementSolver] = None,
    ) -> None:
        self._projection_engine = projection_engine or ForwardProjectionEngine()
        self._target_solver = target_solver or TargetAchievementSolver(
            self._projection_engine
        )

    def compare(
        self,
        scenarios: Sequence[ScenarioDefinition],
        reference_scenario_id: str,
        target_amount: Optional[Decimal] = None,
        target_value_basis: Optional[TargetValueBasis] = None,
    ) -> ScenarioComparisonResult:
        validated_scenarios = _validate_scenarios(
            scenarios,
            reference_scenario_id,
            target_amount,
            target_value_basis,
        )

        projections: dict[str, ForwardProjectionResult] = {}
        achievements: dict[str, Optional[TargetAchievementResult]] = {}
        for scenario in validated_scenarios:
            if target_amount is None:
                projections[scenario.scenario_id] = self._projection_engine.project(
                    scenario.initial_wealth_fact,
                    scenario.assumptions,
                )
                achievements[scenario.scenario_id] = None
                continue

            achievement = self._target_solver.solve(
                scenario.initial_wealth_fact,
                scenario.assumptions,
                target_amount,
            )
            achievements[scenario.scenario_id] = achievement
            if achievement.projection_result is not None:
                projections[scenario.scenario_id] = achievement.projection_result
            else:
                projections[scenario.scenario_id] = self._projection_engine.project(
                    scenario.initial_wealth_fact,
                    scenario.assumptions,
                )

        reference_projection = projections[reference_scenario_id]
        reference_achievement = achievements[reference_scenario_id]
        entries = tuple(
            ScenarioComparisonEntry(
                scenario=scenario,
                projection_result=projections[scenario.scenario_id],
                target_achievement_result=achievements[scenario.scenario_id],
                final_wealth_delta=(
                    _MONEY_ZERO
                    if scenario.scenario_id == reference_scenario_id
                    else (
                        projections[scenario.scenario_id].final_wealth
                        - reference_projection.final_wealth
                    )
                ),
                total_contributions_delta=(
                    _MONEY_ZERO
                    if scenario.scenario_id == reference_scenario_id
                    else (
                        projections[scenario.scenario_id].total_contributions
                        - reference_projection.total_contributions
                    )
                ),
                total_projected_growth_delta=(
                    _MONEY_ZERO
                    if scenario.scenario_id == reference_scenario_id
                    else (
                        projections[scenario.scenario_id].total_projected_growth
                        - reference_projection.total_projected_growth
                    )
                ),
                months_saved_or_lost=_months_saved_or_lost(
                    reference_achievement,
                    achievements[scenario.scenario_id],
                ),
            )
            for scenario in validated_scenarios
        )
        shared_assumptions = validated_scenarios[0].assumptions
        return ScenarioComparisonResult(
            reference_scenario_id=reference_scenario_id,
            entries=entries,
            as_of_date=shared_assumptions.as_of_date,
            horizon_months=shared_assumptions.resolved_horizon_months,
            output_mode=shared_assumptions.output_mode,
            contribution_timing=shared_assumptions.contribution_timing,
            target_amount=target_amount,
            target_value_basis=target_value_basis,
        )
