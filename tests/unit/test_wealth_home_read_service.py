from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from backend.api.wealth_home_mapping import map_wealth_home
from backend.application.dtos.cashflow_summary_dto import MonthlyFinancialMetricsDTO
from backend.application.exceptions.smart_context_ownership_error import (
    SmartContextOwnershipUnavailableError,
)
from backend.application.exceptions.planning_portfolio_source_error import (
    PlanningPortfolioSourceAmbiguousError,
    PlanningPortfolioSourceUnavailableError,
)
from backend.application.services.wealth_home_read_service import (
    WealthHomeAvailability,
    WealthHomeCompleteness,
    WealthHomeFreshness,
    WealthHomeReadService,
)
from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domains.planning.facts import (
    GoalPlanningFact,
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    PlanningFactAsOf,
    PlanningFactProvenance,
)


OWNER_ID = UUID("00000000-0000-0000-0000-000000000701")
OTHER_ID = UUID("00000000-0000-0000-0000-000000000702")
READ_AT = datetime(2026, 10, 22, 14, 30, tzinfo=timezone.utc)


class GuardFake:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[object, UUID]] = []

    def resolve(self, db, current_user_id):
        self.calls.append((db, current_user_id))
        if self.error is not None:
            raise self.error


class HealthSourceFake:
    def __init__(self, fact: MonthlyFinancialMetricsDTO | None) -> None:
        self.fact = fact
        self.calls: list[date] = []

    def read_month(self, db, *, as_of_date):
        self.calls.append(as_of_date)
        return self.fact


class GoalSourceFake:
    def __init__(self, goals: tuple[GoalPlanningFact, ...]) -> None:
        self.goals = goals
        self.calls: list[UUID] = []

    def read_owned(self, db, current_user_id):
        self.calls.append(current_user_id)
        return self.goals


class PortfolioResolverFake:
    def __init__(self, fact: InitialWealthFact | None = None, error: Exception | None = None):
        self.fact = fact
        self.error = error
        self.calls: list[tuple[object, UUID, date]] = []

    def resolve(self, db, current_user_id, as_of_date):
        self.calls.append((db, current_user_id, as_of_date))
        if self.error is not None:
            raise self.error
        return self.fact


def _health(reference_month: str = "2026-10") -> MonthlyFinancialMetricsDTO:
    return MonthlyFinancialMetricsDTO(
        reference_month=reference_month,
        total_income=Decimal("7500.00"),
        total_expense=Decimal("4123.45"),
        net_cashflow=Decimal("3376.55"),
        savings_amount=Decimal("3376.55"),
        savings_rate=Decimal("0.450206"),
    )


def _goal(status: GoalStatus, *, owner_id: UUID = OWNER_ID, day: int = 10):
    return GoalPlanningFact(
        goal_id=UUID(f"00000000-0000-0000-0000-0000000007{day:02d}"),
        user_id=owner_id,
        name=f"Goal {status.value}",
        description=None,
        goal_type=GoalType.CUSTOM,
        status=status,
        target_amount=Decimal("10000.00"),
        target_date=None,
        current_amount=None,
        goal_planned_monthly_contribution=None,
        priority=None,
        linked_account_id=None,
        created_at=datetime(2026, 1, day),
        updated_at=datetime(2026, 10, day),
    )


def _portfolio_fact(
    *,
    reference_month: str = "2026-10",
    amount: Decimal = Decimal("842450.00"),
    source_type: str = "MYPROFIT_EVOLUCAO",
) -> InitialWealthFact:
    return InitialWealthFact(
        source=InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT,
        amount=amount,
        as_of=PlanningFactAsOf(reference_month=reference_month),
        scope=InitialWealthScope.INVESTMENT_PORTFOLIO,
        provenance=PlanningFactProvenance(
            source_table="portfolio_snapshots",
            source_type=source_type,
            account_id="portfolio-synthetic-01",
            reference_month=reference_month,
            run_id="run-synthetic-01",
            created_at=datetime(2026, 10, 20, 9, 0),
            updated_at=datetime(2026, 10, 20, 10, 0),
        ),
    )


def _service(
    *,
    health=None,
    goals=(),
    guard=None,
    portfolio=None,
    today=date(2026, 10, 22),
):
    return WealthHomeReadService(
        ownership_guard=guard or GuardFake(),
        health_source=HealthSourceFake(health),
        goal_source=GoalSourceFake(goals),
        portfolio_source_resolver=portfolio or PortfolioResolverFake(_portfolio_fact()),
        today=lambda: today,
        clock=lambda: READ_AT,
    )


def test_composes_decimal_health_and_owned_goal_lifecycle_counts():
    goals = (
        _goal(GoalStatus.ACTIVE, day=10),
        _goal(GoalStatus.ACTIVE, day=11),
        _goal(GoalStatus.PAUSED, day=12),
        _goal(GoalStatus.ACHIEVED, day=13),
    )
    service = _service(health=_health(), goals=goals)

    result = service.read(object(), OWNER_ID, reference_month="2026-10")

    assert result.status is WealthHomeAvailability.AVAILABLE
    assert result.contract_version == "wealth-home-v2"
    assert result.scope == "AUTHENTICATED_SINGLE_USER"
    assert result.health.net_cashflow == Decimal("3376.55")
    assert type(result.health.net_cashflow) is Decimal
    assert result.health.source.freshness is WealthHomeFreshness.PARTIAL_PERIOD
    assert result.health.source.completeness is WealthHomeCompleteness.UNKNOWN
    assert result.goals.total_count == 4
    assert {item.status: item.count for item in result.goals.by_status} == {
        GoalStatus.ACTIVE: 2,
        GoalStatus.ACHIEVED: 1,
        GoalStatus.PAUSED: 1,
        GoalStatus.CANCELLED: 0,
    }
    assert result.goals.source.updated_at == datetime(2026, 10, 13)
    assert result.investments.status is WealthHomeAvailability.AVAILABLE
    assert result.investments.investment_wealth == Decimal("842450.00")
    assert result.investments.requested_reference_month == "2026-10"
    assert result.investments.snapshot_reference_month == "2026-10"
    assert result.investments.currency == "BRL"
    assert result.investments.source_type == "MYPROFIT_EVOLUCAO"
    assert result.investments.source.completeness is WealthHomeCompleteness.UNKNOWN


def test_public_mapping_serializes_money_as_an_exact_json_string():
    result = _service(health=_health(), goals=()).read(
        object(), OWNER_ID, reference_month="2026-10"
    )

    response = map_wealth_home(result)
    body = response.model_dump(mode="json")

    assert body["health"]["net_cashflow"] == "3376.55"
    assert type(body["health"]["net_cashflow"]) is str
    assert body["investments"]["investment_wealth"] == "842450.00"
    assert type(body["investments"]["investment_wealth"]) is str
    assert body["investments"]["source_type"] == "MYPROFIT_EVOLUCAO"
    assert body["goals"]["total_count"] == 0
    assert body["goals"]["source"]["completeness"] == "COMPLETE"


def test_missing_health_fact_is_insufficient_data_without_fabricated_zero():
    result = _service(health=None, goals=()).read(
        object(), OWNER_ID, reference_month="2026-09"
    )

    assert result.status is WealthHomeAvailability.INSUFFICIENT_DATA
    assert result.health.status is WealthHomeAvailability.INSUFFICIENT_DATA
    assert result.health.net_cashflow is None
    assert result.health.reason == "NO_CERTIFIED_HEALTH_FACT"
    assert result.health.source.freshness is WealthHomeFreshness.CLOSED_PERIOD
    assert result.goals.status is WealthHomeAvailability.AVAILABLE
    assert result.goals.total_count == 0


def test_ownership_failure_stops_before_any_source_read():
    guard = GuardFake(SmartContextOwnershipUnavailableError("not owned"))
    health = HealthSourceFake(_health())
    goals = GoalSourceFake(())
    portfolio = PortfolioResolverFake(_portfolio_fact())
    service = WealthHomeReadService(
        ownership_guard=guard,
        health_source=health,
        goal_source=goals,
        portfolio_source_resolver=portfolio,
        today=lambda: date(2026, 10, 22),
        clock=lambda: READ_AT,
    )

    with pytest.raises(SmartContextOwnershipUnavailableError):
        service.read(object(), OTHER_ID, reference_month="2026-10")

    assert health.calls == []
    assert goals.calls == []
    assert portfolio.calls == []


def test_rejects_goal_fact_outside_authenticated_scope():
    service = _service(
        health=_health(),
        goals=(_goal(GoalStatus.ACTIVE, owner_id=OTHER_ID),),
    )

    with pytest.raises(RuntimeError, match="outside the authenticated scope"):
        service.read(object(), OWNER_ID, reference_month="2026-10")


def test_portfolio_resolver_receives_requested_month_as_of_and_can_return_earlier_snapshot():
    db = object()
    portfolio = PortfolioResolverFake(_portfolio_fact(reference_month="2026-08"))
    result = _service(
        health=_health("2026-09"),
        portfolio=portfolio,
        today=date(2026, 10, 22),
    ).read(db, OWNER_ID, reference_month="2026-09")

    assert portfolio.calls == [(db, OWNER_ID, date(2026, 9, 30))]
    assert result.investments.requested_reference_month == "2026-09"
    assert result.investments.snapshot_reference_month == "2026-08"
    assert result.investments.source.freshness is WealthHomeFreshness.CLOSED_PERIOD


def test_missing_portfolio_snapshot_does_not_fabricate_zero_or_invalidate_other_sources():
    portfolio = PortfolioResolverFake(
        error=PlanningPortfolioSourceUnavailableError("no eligible snapshot")
    )
    result = _service(health=_health(), goals=(), portfolio=portfolio).read(
        object(), OWNER_ID, reference_month="2026-10"
    )

    assert result.status is WealthHomeAvailability.INSUFFICIENT_DATA
    assert result.health.status is WealthHomeAvailability.AVAILABLE
    assert result.goals.status is WealthHomeAvailability.AVAILABLE
    assert result.investments.status is WealthHomeAvailability.INSUFFICIENT_DATA
    assert result.investments.investment_wealth is None
    assert result.investments.snapshot_reference_month is None
    assert result.investments.reason == "NO_ELIGIBLE_INVESTMENT_SNAPSHOT"


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (
            PlanningPortfolioSourceAmbiguousError("two scopes"),
            "INVESTMENT_SOURCE_NOT_ELIGIBLE",
        ),
        (RuntimeError("resolver failure"), "INVESTMENT_SOURCE_FAILURE"),
    ],
)
def test_portfolio_failure_isolated_from_valid_health_and_goals(error, reason):
    result = _service(
        health=_health(),
        goals=(_goal(GoalStatus.ACTIVE),),
        portfolio=PortfolioResolverFake(error=error),
    ).read(object(), OWNER_ID, reference_month="2026-10")

    assert result.health.net_cashflow == Decimal("3376.55")
    assert result.goals.total_count == 1
    assert result.investments.status is WealthHomeAvailability.UNAVAILABLE
    assert result.investments.investment_wealth is None
    assert result.investments.reason == reason


@pytest.mark.parametrize(
    "fact",
    [
        _portfolio_fact(reference_month="2026-11"),
        _portfolio_fact(source_type="MYPROFIT_ATIVOS"),
    ],
)
def test_rejects_non_eligible_portfolio_fact_without_exposing_a_value(fact):
    result = _service(
        health=_health(),
        portfolio=PortfolioResolverFake(fact),
    ).read(object(), OWNER_ID, reference_month="2026-10")

    assert result.health.status is WealthHomeAvailability.AVAILABLE
    assert result.investments.status is WealthHomeAvailability.UNAVAILABLE
    assert result.investments.investment_wealth is None
    assert result.investments.reason == "INVESTMENT_SOURCE_NOT_ELIGIBLE"


@pytest.mark.parametrize("reference_month", ["2026-00", "2026-13", "2026/10", "2026-11"])
def test_rejects_invalid_or_future_reference_month(reference_month):
    with pytest.raises(ValueError):
        _service(health=_health()).read(
            object(), OWNER_ID, reference_month=reference_month
        )
