"""Read-only FIRE application orchestration over the locked Planning contracts."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TypeAlias
from uuid import UUID

from backend.application.services.planning_initial_wealth_fact_builder import (
    build_user_initial_wealth_fact,
)
from backend.application.services.planning_portfolio_source_resolver import (
    PlanningPortfolioSourceResolver,
)
from backend.domains.fire.summary import (
    FireSummary,
    FireSummaryCalculator,
    FireSummaryInput,
)
from backend.domains.planning.assumptions import (
    ContributionTiming,
    OutputMode,
    ProjectionAssumptions,
    RateBasis,
    ReturnType,
)
from backend.domains.planning.facts import InitialWealthFact
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionResult,
    RequiredContributionSolver,
)
from backend.domains.planning.target_basis import TargetValueBasis
from backend.domains.planning.target_solver import (
    TargetAchievementResult,
    TargetAchievementSolver,
)


_NEUTRAL_MONTHLY_CONTRIBUTION = Decimal("0.00")


class FireAnalysisType(str, Enum):
    """The three locked FIRE application modes."""

    SUMMARY = "SUMMARY"
    PROJECTED_DATE = "PROJECTED_DATE"
    REQUIRED_CONTRIBUTION = "REQUIRED_CONTRIBUTION"


@dataclass(frozen=True)
class PortfolioInitialWealthSelection:
    """Source-only selection delegated to Planning's ADR-023 resolver."""


@dataclass(frozen=True)
class UserProvidedInitialWealthSelection:
    """Explicit manual wealth and provenance already validated at the API boundary."""

    amount: Decimal
    observed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("amount must be Decimal")
        if not self.amount.is_finite():
            raise ValueError("amount must be finite")
        if not isinstance(self.observed_at, datetime):
            raise TypeError("observed_at must be datetime")


FireInitialWealthSelection: TypeAlias = (
    PortfolioInitialWealthSelection | UserProvidedInitialWealthSelection
)


def _validate_common_command(
    initial_wealth: FireInitialWealthSelection,
    as_of_date: date,
    monthly_retirement_spending: Decimal,
    assumed_annual_withdrawal_rate: Decimal,
) -> None:
    if not isinstance(
        initial_wealth,
        (PortfolioInitialWealthSelection, UserProvidedInitialWealthSelection),
    ):
        raise TypeError("initial_wealth must be a supported FIRE wealth selection")
    if type(as_of_date) is not date:
        raise ValueError("as_of_date must be a date")
    FireSummaryInput(
        eligible_investment_wealth=Decimal("0.00"),
        monthly_retirement_spending=monthly_retirement_spending,
        assumed_annual_withdrawal_rate=assumed_annual_withdrawal_rate,
    )


def _build_projected_assumptions(
    *,
    as_of_date: date,
    scenario_monthly_contribution: Decimal,
    expected_return_rate: Decimal,
    return_type: ReturnType,
    inflation_rate: Decimal | None,
    horizon_months: int,
) -> ProjectionAssumptions:
    return ProjectionAssumptions(
        as_of_date=as_of_date,
        scenario_monthly_contribution=scenario_monthly_contribution,
        expected_return_rate=expected_return_rate,
        return_type=return_type,
        output_mode=OutputMode.REAL,
        inflation_rate=inflation_rate,
        horizon_months=horizon_months,
        target_date=None,
        rate_basis=RateBasis.EFFECTIVE_ANNUAL,
        contribution_timing=ContributionTiming.END_OF_MONTH,
    )


def _build_required_assumptions(
    *,
    as_of_date: date,
    expected_return_rate: Decimal,
    return_type: ReturnType,
    inflation_rate: Decimal | None,
    desired_fire_date: date,
) -> ProjectionAssumptions:
    return ProjectionAssumptions(
        as_of_date=as_of_date,
        scenario_monthly_contribution=_NEUTRAL_MONTHLY_CONTRIBUTION,
        expected_return_rate=expected_return_rate,
        return_type=return_type,
        output_mode=OutputMode.REAL,
        inflation_rate=inflation_rate,
        horizon_months=None,
        target_date=desired_fire_date,
        rate_basis=RateBasis.EFFECTIVE_ANNUAL,
        contribution_timing=ContributionTiming.END_OF_MONTH,
    )


@dataclass(frozen=True)
class FireSummaryCommand:
    """Application command for a summary-only FIRE analysis."""

    initial_wealth: FireInitialWealthSelection
    as_of_date: date
    monthly_retirement_spending: Decimal
    assumed_annual_withdrawal_rate: Decimal
    analysis_type: FireAnalysisType = FireAnalysisType.SUMMARY

    def __post_init__(self) -> None:
        if self.analysis_type is not FireAnalysisType.SUMMARY:
            raise ValueError("FireSummaryCommand must use SUMMARY")
        _validate_common_command(
            self.initial_wealth,
            self.as_of_date,
            self.monthly_retirement_spending,
            self.assumed_annual_withdrawal_rate,
        )


@dataclass(frozen=True)
class FireProjectedDateCommand:
    """Application command that delegates one target solve to Planning."""

    initial_wealth: FireInitialWealthSelection
    as_of_date: date
    monthly_retirement_spending: Decimal
    assumed_annual_withdrawal_rate: Decimal
    scenario_monthly_contribution: Decimal
    expected_return_rate: Decimal
    return_type: ReturnType
    horizon_months: int
    inflation_rate: Decimal | None = None
    analysis_type: FireAnalysisType = FireAnalysisType.PROJECTED_DATE

    def __post_init__(self) -> None:
        if self.analysis_type is not FireAnalysisType.PROJECTED_DATE:
            raise ValueError("FireProjectedDateCommand must use PROJECTED_DATE")
        _validate_common_command(
            self.initial_wealth,
            self.as_of_date,
            self.monthly_retirement_spending,
            self.assumed_annual_withdrawal_rate,
        )
        self.projection_assumptions()

    def projection_assumptions(self) -> ProjectionAssumptions:
        """Construct Planning-owned projection inputs with FIRE's fixed REAL basis."""

        return _build_projected_assumptions(
            as_of_date=self.as_of_date,
            scenario_monthly_contribution=self.scenario_monthly_contribution,
            expected_return_rate=self.expected_return_rate,
            return_type=self.return_type,
            inflation_rate=self.inflation_rate,
            horizon_months=self.horizon_months,
        )


@dataclass(frozen=True)
class FireRequiredContributionCommand:
    """Application command that delegates one inverse solve to Planning."""

    initial_wealth: FireInitialWealthSelection
    as_of_date: date
    monthly_retirement_spending: Decimal
    assumed_annual_withdrawal_rate: Decimal
    expected_return_rate: Decimal
    return_type: ReturnType
    desired_fire_date: date
    inflation_rate: Decimal | None = None
    analysis_type: FireAnalysisType = FireAnalysisType.REQUIRED_CONTRIBUTION

    def __post_init__(self) -> None:
        if self.analysis_type is not FireAnalysisType.REQUIRED_CONTRIBUTION:
            raise ValueError(
                "FireRequiredContributionCommand must use REQUIRED_CONTRIBUTION"
            )
        _validate_common_command(
            self.initial_wealth,
            self.as_of_date,
            self.monthly_retirement_spending,
            self.assumed_annual_withdrawal_rate,
        )
        self.projection_assumptions()

    def projection_assumptions(self) -> ProjectionAssumptions:
        """Construct the neutral Planning template for the inverse solver."""

        return _build_required_assumptions(
            as_of_date=self.as_of_date,
            expected_return_rate=self.expected_return_rate,
            return_type=self.return_type,
            inflation_rate=self.inflation_rate,
            desired_fire_date=self.desired_fire_date,
        )


FireAnalysisCommand: TypeAlias = (
    FireSummaryCommand | FireProjectedDateCommand | FireRequiredContributionCommand
)


@dataclass(frozen=True)
class FireAnalysisAssumptions:
    """Exact FIRE inputs used by an analysis, without HTTP serialization."""

    monthly_retirement_spending: Decimal
    assumed_annual_withdrawal_rate: Decimal
    expected_return_rate: Decimal | None
    return_type: ReturnType | None
    inflation_rate: Decimal | None
    scenario_monthly_contribution: Decimal | None
    horizon_months: int | None
    desired_fire_date: date | None


@dataclass(frozen=True)
class FireAnalysisResult:
    """Read-only composition of a FIRE summary and at most one Planning result."""

    analysis_type: FireAnalysisType
    as_of_date: date
    output_mode: OutputMode
    target_value_basis: TargetValueBasis
    summary: FireSummary
    initial_wealth_fact: InitialWealthFact
    assumptions: FireAnalysisAssumptions
    projection: TargetAchievementResult | None
    required_contribution: RequiredContributionResult | None


class FireAnalysisService:
    """Compose the D1 summary with exactly one authorized Planning solver."""

    def __init__(
        self,
        summary_calculator: FireSummaryCalculator | None = None,
        portfolio_source_resolver: PlanningPortfolioSourceResolver | None = None,
        target_achievement_solver: TargetAchievementSolver | None = None,
        required_contribution_solver: RequiredContributionSolver | None = None,
    ) -> None:
        self._summary_calculator = summary_calculator or FireSummaryCalculator()
        self._portfolio_source_resolver = (
            portfolio_source_resolver or PlanningPortfolioSourceResolver()
        )
        self._target_achievement_solver = (
            target_achievement_solver or TargetAchievementSolver()
        )
        self._required_contribution_solver = (
            required_contribution_solver or RequiredContributionSolver()
        )

    def analyze(
        self,
        command: FireAnalysisCommand,
        db: object,
        current_user_id: UUID,
    ) -> FireAnalysisResult:
        """Resolve one fact, calculate one summary, then select zero or one solver."""

        if not isinstance(
            command,
            (
                FireSummaryCommand,
                FireProjectedDateCommand,
                FireRequiredContributionCommand,
            ),
        ):
            raise TypeError("command must be a supported FIRE analysis command")

        initial_wealth_fact = self._resolve_initial_wealth_fact(
            command.initial_wealth,
            db,
            current_user_id,
            command.as_of_date,
        )
        summary = self._summary_calculator.calculate(
            FireSummaryInput(
                eligible_investment_wealth=initial_wealth_fact.amount,
                monthly_retirement_spending=command.monthly_retirement_spending,
                assumed_annual_withdrawal_rate=(
                    command.assumed_annual_withdrawal_rate
                ),
            )
        )

        if isinstance(command, FireSummaryCommand):
            return self._result(
                command=command,
                summary=summary,
                initial_wealth_fact=initial_wealth_fact,
                assumptions=FireAnalysisAssumptions(
                    monthly_retirement_spending=command.monthly_retirement_spending,
                    assumed_annual_withdrawal_rate=(
                        command.assumed_annual_withdrawal_rate
                    ),
                    expected_return_rate=None,
                    return_type=None,
                    inflation_rate=None,
                    scenario_monthly_contribution=None,
                    horizon_months=None,
                    desired_fire_date=None,
                ),
                projection=None,
                required_contribution=None,
            )

        if isinstance(command, FireProjectedDateCommand):
            assumptions = command.projection_assumptions()
            projection = self._target_achievement_solver.solve(
                initial_wealth_fact,
                assumptions,
                summary.fire_target,
            )
            return self._result(
                command=command,
                summary=summary,
                initial_wealth_fact=initial_wealth_fact,
                assumptions=FireAnalysisAssumptions(
                    monthly_retirement_spending=command.monthly_retirement_spending,
                    assumed_annual_withdrawal_rate=(
                        command.assumed_annual_withdrawal_rate
                    ),
                    expected_return_rate=command.expected_return_rate,
                    return_type=command.return_type,
                    inflation_rate=command.inflation_rate,
                    scenario_monthly_contribution=(
                        command.scenario_monthly_contribution
                    ),
                    horizon_months=command.horizon_months,
                    desired_fire_date=None,
                ),
                projection=projection,
                required_contribution=None,
            )

        assumptions = command.projection_assumptions()
        required_contribution = self._required_contribution_solver.solve(
            initial_wealth_fact,
            assumptions,
            summary.fire_target,
        )
        return self._result(
            command=command,
            summary=summary,
            initial_wealth_fact=initial_wealth_fact,
            assumptions=FireAnalysisAssumptions(
                monthly_retirement_spending=command.monthly_retirement_spending,
                assumed_annual_withdrawal_rate=command.assumed_annual_withdrawal_rate,
                expected_return_rate=command.expected_return_rate,
                return_type=command.return_type,
                inflation_rate=command.inflation_rate,
                scenario_monthly_contribution=None,
                horizon_months=None,
                desired_fire_date=command.desired_fire_date,
            ),
            projection=None,
            required_contribution=required_contribution,
        )

    def _resolve_initial_wealth_fact(
        self,
        selection: FireInitialWealthSelection,
        db: object,
        current_user_id: UUID,
        as_of_date: date,
    ) -> InitialWealthFact:
        if isinstance(selection, PortfolioInitialWealthSelection):
            return self._portfolio_source_resolver.resolve(
                db,
                current_user_id,
                as_of_date,
            )
        if isinstance(selection, UserProvidedInitialWealthSelection):
            return build_user_initial_wealth_fact(
                amount=selection.amount,
                observed_at=selection.observed_at,
            )
        raise TypeError("unsupported FIRE wealth selection")

    @staticmethod
    def _result(
        *,
        command: FireAnalysisCommand,
        summary: FireSummary,
        initial_wealth_fact: InitialWealthFact,
        assumptions: FireAnalysisAssumptions,
        projection: TargetAchievementResult | None,
        required_contribution: RequiredContributionResult | None,
    ) -> FireAnalysisResult:
        return FireAnalysisResult(
            analysis_type=command.analysis_type,
            as_of_date=command.as_of_date,
            output_mode=OutputMode.REAL,
            target_value_basis=TargetValueBasis.REAL,
            summary=summary,
            initial_wealth_fact=initial_wealth_fact,
            assumptions=assumptions,
            projection=projection,
            required_contribution=required_contribution,
        )
