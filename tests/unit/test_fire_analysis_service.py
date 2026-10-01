from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from backend.application.services.fire_analysis_service import (
    FireAnalysisService,
    FireAnalysisType,
    FireProjectedDateCommand,
    FireRequiredContributionCommand,
    FireSummaryCommand,
    PortfolioInitialWealthSelection,
    UserProvidedInitialWealthSelection,
)
from backend.domains.fire import FireSummaryCalculator
from backend.domains.planning.assumptions import OutputMode, ProjectionAssumptions, ReturnType
from backend.domains.planning.facts import (
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    PlanningFactAsOf,
    PlanningFactProvenance,
)
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionResult,
    RequiredContributionStatus,
)
from backend.domains.planning.target_basis import TargetValueBasis
from backend.domains.planning.target_solver import (
    TargetAchievementResult,
    TargetAchievementStatus,
)


USER_ID = UUID("00000000-0000-0000-0000-000000000001")
AS_OF_DATE = date(2026, 9, 30)
OBSERVED_AT = datetime(2026, 9, 30, 10, 30, tzinfo=timezone.utc)


def _portfolio_fact(amount: str = "250000.00") -> InitialWealthFact:
    return InitialWealthFact(
        source=InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT,
        amount=Decimal(amount),
        as_of=PlanningFactAsOf(reference_month="2026-09"),
        scope=InitialWealthScope.INVESTMENT_PORTFOLIO,
        provenance=PlanningFactProvenance(
            source_table="portfolio_snapshots",
            source_type="MYPROFIT_EVOLUCAO",
            account_id="portfolio-account",
            reference_month="2026-09",
            run_id="portfolio-run",
        ),
    )


class RecordingPortfolioResolver:
    def __init__(self, fact: InitialWealthFact) -> None:
        self.fact = fact
        self.calls: list[tuple[object, UUID, date]] = []

    def resolve(
        self,
        db: object,
        current_user_id: UUID,
        as_of_date: date,
    ) -> InitialWealthFact:
        self.calls.append((db, current_user_id, as_of_date))
        return self.fact


class RecordingFireSummaryCalculator:
    def __init__(self) -> None:
        self.inputs = []
        self._calculator = FireSummaryCalculator()

    def calculate(self, input):
        self.inputs.append(input)
        return self._calculator.calculate(input)


class RecordingTargetSolver:
    def __init__(
        self,
        status: TargetAchievementStatus = TargetAchievementStatus.NOT_REACHED_WITHIN_HORIZON,
    ) -> None:
        self.status = status
        self.calls = []

    def solve(
        self,
        initial_wealth_fact: InitialWealthFact,
        assumptions: ProjectionAssumptions,
        target_amount: Decimal,
    ) -> TargetAchievementResult:
        self.calls.append((initial_wealth_fact, assumptions, target_amount))
        if self.status is TargetAchievementStatus.ALREADY_ACHIEVED:
            return TargetAchievementResult(
                status=self.status,
                target_amount=target_amount,
                initial_wealth_fact=initial_wealth_fact,
                assumptions=assumptions,
                achievement_period=0,
                achievement_date=assumptions.as_of_date,
                months_required=0,
                achieved_wealth=initial_wealth_fact.amount,
                projection_result=None,
            )
        return TargetAchievementResult(
            status=self.status,
            target_amount=target_amount,
            initial_wealth_fact=initial_wealth_fact,
            assumptions=assumptions,
            achievement_period=None,
            achievement_date=None,
            months_required=None,
            achieved_wealth=None,
            projection_result=None,
        )


class RecordingRequiredContributionSolver:
    def __init__(
        self,
        status: RequiredContributionStatus = RequiredContributionStatus.SOLVED,
    ) -> None:
        self.status = status
        self.calls = []

    def solve(
        self,
        initial_wealth_fact: InitialWealthFact,
        assumptions: ProjectionAssumptions,
        target_amount: Decimal,
    ) -> RequiredContributionResult:
        self.calls.append((initial_wealth_fact, assumptions, target_amount))
        target_result = TargetAchievementResult(
            status=TargetAchievementStatus.NOT_REACHED_WITHIN_HORIZON,
            target_amount=target_amount,
            initial_wealth_fact=initial_wealth_fact,
            assumptions=assumptions,
            achievement_period=None,
            achievement_date=None,
            months_required=None,
            achieved_wealth=None,
            projection_result=None,
        )
        return RequiredContributionResult(
            status=self.status,
            target_amount=target_amount,
            initial_wealth_fact=initial_wealth_fact,
            assumptions_template=assumptions,
            required_monthly_contribution=Decimal("123.45"),
            solved_assumptions=assumptions,
            target_achievement_result=target_result,
        )


def _service(
    fact: InitialWealthFact | None = None,
    *,
    target_status: TargetAchievementStatus = TargetAchievementStatus.NOT_REACHED_WITHIN_HORIZON,
    required_status: RequiredContributionStatus = RequiredContributionStatus.SOLVED,
):
    resolver = RecordingPortfolioResolver(fact or _portfolio_fact())
    summary_calculator = RecordingFireSummaryCalculator()
    target_solver = RecordingTargetSolver(target_status)
    required_solver = RecordingRequiredContributionSolver(required_status)
    return (
        FireAnalysisService(
            summary_calculator=summary_calculator,
            portfolio_source_resolver=resolver,
            target_achievement_solver=target_solver,
            required_contribution_solver=required_solver,
        ),
        resolver,
        summary_calculator,
        target_solver,
        required_solver,
    )


def _projected_command(**overrides) -> FireProjectedDateCommand:
    values = {
        "initial_wealth": PortfolioInitialWealthSelection(),
        "as_of_date": AS_OF_DATE,
        "monthly_retirement_spending": Decimal("5000.00"),
        "assumed_annual_withdrawal_rate": Decimal("0.04"),
        "scenario_monthly_contribution": Decimal("1000.00"),
        "expected_return_rate": Decimal("0.06"),
        "return_type": ReturnType.REAL,
        "horizon_months": 120,
    }
    values.update(overrides)
    return FireProjectedDateCommand(**values)


def _required_command(**overrides) -> FireRequiredContributionCommand:
    values = {
        "initial_wealth": PortfolioInitialWealthSelection(),
        "as_of_date": AS_OF_DATE,
        "monthly_retirement_spending": Decimal("5000.00"),
        "assumed_annual_withdrawal_rate": Decimal("0.04"),
        "expected_return_rate": Decimal("0.06"),
        "return_type": ReturnType.REAL,
        "desired_fire_date": date(2036, 9, 30),
    }
    values.update(overrides)
    return FireRequiredContributionCommand(**values)


def test_summary_mode_builds_one_manual_fact_and_invokes_no_planning_solver():
    service, resolver, _, target_solver, required_solver = _service()
    command = FireSummaryCommand(
        initial_wealth=UserProvidedInitialWealthSelection(
            amount=Decimal("250000.00"),
            observed_at=OBSERVED_AT,
        ),
        as_of_date=AS_OF_DATE,
        monthly_retirement_spending=Decimal("5000.00"),
        assumed_annual_withdrawal_rate=Decimal("0.04"),
    )

    result = service.analyze(command, db=object(), current_user_id=USER_ID)

    assert result.analysis_type is FireAnalysisType.SUMMARY
    assert result.projection is None
    assert result.required_contribution is None
    assert resolver.calls == []
    assert target_solver.calls == []
    assert required_solver.calls == []
    assert result.initial_wealth_fact.source is InitialWealthSource.USER_PROVIDED_SCENARIO
    assert result.initial_wealth_fact.scope is InitialWealthScope.USER_PROVIDED_SCENARIO
    assert result.initial_wealth_fact.as_of.observed_at == OBSERVED_AT
    assert result.initial_wealth_fact.provenance.source_table == "planning_request"


def test_projected_real_resolves_one_fact_once_and_preserves_it_across_composition():
    fact = _portfolio_fact()
    service, resolver, summary_calculator, target_solver, required_solver = _service(fact)

    result = service.analyze(
        _projected_command(),
        db="read-session",
        current_user_id=USER_ID,
    )

    assert resolver.calls == [("read-session", USER_ID, AS_OF_DATE)]
    assert len(summary_calculator.inputs) == 1
    assert summary_calculator.inputs[0].eligible_investment_wealth is fact.amount
    assert len(target_solver.calls) == 1
    solved_fact, assumptions, target_amount = target_solver.calls[0]
    assert solved_fact is fact
    assert target_amount == result.summary.fire_target
    assert required_solver.calls == []
    assert result.initial_wealth_fact is fact
    assert result.projection is not None
    assert result.projection.status is TargetAchievementStatus.NOT_REACHED_WITHIN_HORIZON
    assert result.required_contribution is None
    assert assumptions.output_mode is OutputMode.REAL
    assert assumptions.return_type is ReturnType.REAL
    assert assumptions.inflation_rate is None
    assert result.output_mode is OutputMode.REAL
    assert result.target_value_basis is TargetValueBasis.REAL


def test_projected_nominal_delegates_explicit_inflation_to_planning_without_fisher_math():
    service, _, _, target_solver, required_solver = _service()

    result = service.analyze(
        _projected_command(
            return_type=ReturnType.NOMINAL,
            expected_return_rate=Decimal("0.10"),
            inflation_rate=Decimal("0.04"),
        ),
        db=object(),
        current_user_id=USER_ID,
    )

    _, assumptions, _ = target_solver.calls[0]
    assert assumptions.return_type is ReturnType.NOMINAL
    assert assumptions.output_mode is OutputMode.REAL
    assert assumptions.expected_return_rate == Decimal("0.10")
    assert assumptions.inflation_rate == Decimal("0.04")
    assert result.assumptions.inflation_rate == Decimal("0.04")
    assert required_solver.calls == []


def test_required_real_uses_canonical_ceiling_target_and_neutral_template_contribution():
    service, resolver, _, target_solver, required_solver = _service()

    result = service.analyze(
        _required_command(
            monthly_retirement_spending=Decimal("1000.00"),
            assumed_annual_withdrawal_rate=Decimal("0.07"),
        ),
        db=object(),
        current_user_id=USER_ID,
    )

    assert len(resolver.calls) == 1
    assert target_solver.calls == []
    assert len(required_solver.calls) == 1
    solved_fact, assumptions, target_amount = required_solver.calls[0]
    assert solved_fact is result.initial_wealth_fact
    assert target_amount == Decimal("171428.58")
    assert target_amount == result.summary.fire_target
    assert assumptions.scenario_monthly_contribution == Decimal("0.00")
    assert assumptions.output_mode is OutputMode.REAL
    assert assumptions.return_type is ReturnType.REAL
    assert assumptions.inflation_rate is None
    assert assumptions.target_date == date(2036, 9, 30)
    assert assumptions.horizon_months is None
    assert result.projection is None
    assert result.required_contribution is not None


def test_required_nominal_preserves_desired_date_and_explicit_inflation():
    service, _, _, target_solver, required_solver = _service()
    desired_date = date(2032, 3, 30)

    result = service.analyze(
        _required_command(
            desired_fire_date=desired_date,
            return_type=ReturnType.NOMINAL,
            expected_return_rate=Decimal("0.09"),
            inflation_rate=Decimal("0.04"),
        ),
        db=object(),
        current_user_id=USER_ID,
    )

    _, assumptions, _ = required_solver.calls[0]
    assert target_solver.calls == []
    assert assumptions.return_type is ReturnType.NOMINAL
    assert assumptions.output_mode is OutputMode.REAL
    assert assumptions.inflation_rate == Decimal("0.04")
    assert assumptions.target_date == desired_date
    assert result.assumptions.desired_fire_date == desired_date


@pytest.mark.parametrize(
    "command_factory,overrides",
    [
        (_projected_command, {"inflation_rate": Decimal("0.04")}),
        (
            _projected_command,
            {"return_type": ReturnType.NOMINAL, "inflation_rate": None},
        ),
        (_required_command, {"inflation_rate": Decimal("0.04")}),
        (
            _required_command,
            {"return_type": ReturnType.NOMINAL, "inflation_rate": None},
        ),
    ],
)
def test_invalid_return_inflation_matrix_is_rejected_before_analysis(
    command_factory,
    overrides,
):
    with pytest.raises(ValueError):
        command_factory(**overrides)


def test_solver_status_is_preserved_without_fire_status_translation():
    service, _, _, target_solver, _ = _service(
        target_status=TargetAchievementStatus.UNREACHABLE
    )

    result = service.analyze(
        _projected_command(),
        db=object(),
        current_user_id=USER_ID,
    )

    assert target_solver.calls[0][2] == result.summary.fire_target
    assert result.projection is not None
    assert result.projection.status is TargetAchievementStatus.UNREACHABLE


def test_already_independent_summary_does_not_skip_requested_projected_solver():
    fact = _portfolio_fact("2000000.00")
    service, resolver, _, target_solver, required_solver = _service(
        fact,
        target_status=TargetAchievementStatus.ALREADY_ACHIEVED,
    )

    result = service.analyze(
        _projected_command(),
        db=object(),
        current_user_id=USER_ID,
    )

    assert result.summary.status.value == "ALREADY_FINANCIALLY_INDEPENDENT"
    assert len(resolver.calls) == 1
    assert len(target_solver.calls) == 1
    assert target_solver.calls[0][0] is fact
    assert required_solver.calls == []
    assert result.projection is not None
    assert result.projection.status is TargetAchievementStatus.ALREADY_ACHIEVED
