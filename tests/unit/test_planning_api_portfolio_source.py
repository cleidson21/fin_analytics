"""HTTP integration tests for ADR-023's source-only Planning portfolio selector."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError

from backend.api.dependencies.auth import get_current_user
from backend.api.routers import planning as planning_router
from backend.application.dtos.planning_dto import (
    GoalPlanningInitialWealthSelectorRequestDTO,
    InitialWealthSelectorRequestDTO,
)
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.exceptions.planning_portfolio_source_error import (
    PlanningPortfolioSourceUnavailableError,
)
from backend.database.session import get_db
from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domain.enums.user_role import UserRole
from backend.domains.planning.facts import (
    GoalPlanningFact,
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    PlanningFactAsOf,
    PlanningFactProvenance,
)
from backend.domains.planning.goal_planning import GoalPlanningService
from backend.domains.planning.projection import ForwardProjectionEngine
from backend.domains.planning.readers import PlanningGoalReadQuery
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionSolver,
)
from backend.domains.planning.scenario_comparison import ScenarioComparisonEngine
from backend.domains.planning.target_solver import TargetAchievementSolver
from backend.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000000811")
GOAL_ID = UUID("00000000-0000-0000-0000-000000000822")


def _current_user() -> UserResponseDTO:
    return UserResponseDTO(
        id=USER_ID,
        email="portfolio-source@example.test",
        name="Portfolio Source User",
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _portfolio_fact(amount: Decimal = Decimal("123456.78")) -> InitialWealthFact:
    return InitialWealthFact(
        source=InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT,
        amount=amount,
        scope=InitialWealthScope.INVESTMENT_PORTFOLIO,
        as_of=PlanningFactAsOf(reference_month="2026-09"),
        provenance=PlanningFactProvenance(
            source_table="portfolio_snapshots",
            source_type="MYPROFIT_EVOLUCAO",
            account_id="myprofit-evolucao",
            reference_month="2026-09",
            run_id="opaque-run-id",
            created_at=datetime(2026, 9, 3, 8, 0),
            updated_at=datetime(2026, 9, 3, 8, 0),
        ),
    )


def _goal(status: GoalStatus = GoalStatus.ACTIVE) -> GoalPlanningFact:
    return GoalPlanningFact(
        goal_id=GOAL_ID,
        user_id=USER_ID,
        name="Owned Goal",
        description=None,
        goal_type=GoalType.CUSTOM,
        status=status,
        target_amount=Decimal("124000.00"),
        target_date=date(2026, 10, 1),
        current_amount=None,
        goal_planned_monthly_contribution=None,
        priority=None,
        linked_account_id=None,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 9, 1),
    )


class _PortfolioResolverSpy:
    def __init__(self, result: InitialWealthFact | Exception) -> None:
        self.result = result
        self.calls: list[tuple[object, UUID, date]] = []

    def resolve(self, db, current_user_id: UUID, as_of_date: date) -> InitialWealthFact:
        self.calls.append((db, current_user_id, as_of_date))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class _SequencePortfolioResolver:
    def __init__(self, results: list[InitialWealthFact | Exception]) -> None:
        self._results = iter(results)
        self.calls: list[tuple[object, UUID, date]] = []

    def resolve(self, db, current_user_id: UUID, as_of_date: date) -> InitialWealthFact:
        self.calls.append((db, current_user_id, as_of_date))
        result = next(self._results)
        if isinstance(result, Exception):
            raise result
        return result


class _GoalReader:
    def __init__(self, goal: GoalPlanningFact | None) -> None:
        self.goal = goal

    def get_goal(self, db, goal_id, user_id):
        return self.goal if goal_id == GOAL_ID and user_id == USER_ID else None

    current_amount_as_initial_wealth = staticmethod(
        PlanningGoalReadQuery.current_amount_as_initial_wealth
    )


class _ForwardSpy:
    def __init__(self) -> None:
        self.calls = 0
        self._engine = ForwardProjectionEngine()

    def project(self, initial_wealth_fact, assumptions):
        self.calls += 1
        return self._engine.project(initial_wealth_fact, assumptions)


class _TargetSpy:
    def __init__(self) -> None:
        self.calls = 0
        self._solver = TargetAchievementSolver()

    def solve(self, initial_wealth_fact, assumptions, target_amount):
        self.calls += 1
        return self._solver.solve(initial_wealth_fact, assumptions, target_amount)


class _RequiredSpy:
    def __init__(self) -> None:
        self.calls = 0
        self._solver = RequiredContributionSolver()

    def solve(self, initial_wealth_fact, assumptions, target_amount):
        self.calls += 1
        return self._solver.solve(initial_wealth_fact, assumptions, target_amount)


class _ComparisonSpy:
    def __init__(self) -> None:
        self.calls = 0
        self._engine = ScenarioComparisonEngine()

    def compare(self, *args):
        self.calls += 1
        return self._engine.compare(*args)


class _GoalPlanningServiceSpy:
    def __init__(self) -> None:
        self.calls = 0
        self._service = GoalPlanningService()

    def preflight_applicability(self, *args):
        return self._service.preflight_applicability(*args)

    def evaluate(self, *args):
        self.calls += 1
        return self._service.evaluate(*args)


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def _authenticated_client():
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as client:
        yield client


def _assumptions_payload(**overrides):
    payload = {
        "as_of_date": "2026-09-20",
        "scenario_monthly_contribution": "100.00",
        "expected_return_rate": "0",
        "return_type": "NOMINAL",
        "output_mode": "NOMINAL",
        "inflation_rate": None,
        "horizon_months": 2,
        "target_date": None,
        "rate_basis": "EFFECTIVE_ANNUAL",
        "contribution_timing": "END_OF_MONTH",
    }
    payload.update(overrides)
    return payload


def _portfolio_selector():
    return {"source": "INVESTMENT_PORTFOLIO_SNAPSHOT"}


def _manual_selector(amount: str = "100.00"):
    return {
        "source": "USER_PROVIDED_SCENARIO",
        "amount": amount,
        "observed_at": "2026-09-20T09:30:00-03:00",
    }


def _projection_payload(**overrides):
    payload = {
        "initial_wealth": _portfolio_selector(),
        "assumptions": _assumptions_payload(),
    }
    payload.update(overrides)
    return payload


def _target_payload(**overrides):
    payload = _projection_payload()
    payload.update({"target_amount": "124000.00", "target_value_basis": "NOMINAL"})
    payload.update(overrides)
    return payload


def _install_portfolio_resolver(resolver):
    app.dependency_overrides[planning_router.get_planning_portfolio_source_resolver] = (
        lambda: resolver
    )


def test_portfolio_selector_is_source_only_and_rejects_all_certified_fact_forgery():
    generic = TypeAdapter(InitialWealthSelectorRequestDTO)
    goal = TypeAdapter(GoalPlanningInitialWealthSelectorRequestDTO)

    assert generic.validate_python(_portfolio_selector()).source is (
        InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT
    )
    assert goal.validate_python(_portfolio_selector()).source is (
        InitialWealthSource.INVESTMENT_PORTFOLIO_SNAPSHOT
    )
    for field, value in (
        ("amount", "999999999.99"),
        ("account_id", "unowned-account"),
        ("reference_month", "2026-09"),
        ("run_id", "forged-run"),
        ("updated_at", "2026-09-20T00:00:00Z"),
        ("currency", "USD"),
        ("scope", "INVESTMENT_PORTFOLIO"),
        ("provenance", {"source_type": "MYPROFIT_EVOLUCAO"}),
    ):
        with pytest.raises(ValidationError):
            generic.validate_python({**_portfolio_selector(), field: value})


def test_projection_resolves_portfolio_with_current_user_as_of_and_decimal_provenance(
    _authenticated_client,
):
    resolver = _PortfolioResolverSpy(_portfolio_fact())
    engine = _ForwardSpy()
    _install_portfolio_resolver(resolver)
    app.dependency_overrides[planning_router.get_forward_projection_engine] = lambda: engine

    response = _authenticated_client.post(
        "/api/v1/planning/projection", json=_projection_payload()
    )

    assert response.status_code == 200
    assert engine.calls == 1
    assert resolver.calls[0][1:] == (USER_ID, date(2026, 9, 20))
    fact = response.json()["initial_wealth_fact"]
    assert fact["amount"] == "123456.78"
    assert isinstance(fact["amount"], str)
    assert fact["source"] == "INVESTMENT_PORTFOLIO_SNAPSHOT"
    assert fact["scope"] == "INVESTMENT_PORTFOLIO"
    assert fact["as_of"] == {"reference_month": "2026-09", "observed_at": None}
    assert fact["provenance"]["reference_month"] == "2026-09"
    assert fact["provenance"]["updated_at"] == "2026-09-03T08:00:00"
    assert "source_table" not in fact["provenance"]


def test_projection_unavailable_portfolio_is_safe_422_before_engine(_authenticated_client):
    resolver = _PortfolioResolverSpy(
        PlanningPortfolioSourceUnavailableError("private resolver details")
    )
    engine = _ForwardSpy()
    _install_portfolio_resolver(resolver)
    app.dependency_overrides[planning_router.get_forward_projection_engine] = lambda: engine

    response = _authenticated_client.post(
        "/api/v1/planning/projection", json=_projection_payload()
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Selected certified portfolio source is unavailable."
    }
    assert engine.calls == 0


def test_target_and_required_use_the_portfolio_fact_once_with_request_as_of(
    _authenticated_client,
):
    target_resolver = _PortfolioResolverSpy(_portfolio_fact(Decimal("123900.00")))
    target_solver = _TargetSpy()
    _install_portfolio_resolver(target_resolver)
    app.dependency_overrides[planning_router.get_target_achievement_solver] = (
        lambda: target_solver
    )
    target = _authenticated_client.post(
        "/api/v1/planning/target-achievement", json=_target_payload()
    )

    required_resolver = _PortfolioResolverSpy(_portfolio_fact(Decimal("123900.00")))
    required_solver = _RequiredSpy()
    _install_portfolio_resolver(required_resolver)
    app.dependency_overrides[planning_router.get_required_contribution_solver] = (
        lambda: required_solver
    )
    required = _authenticated_client.post(
        "/api/v1/planning/required-contribution", json=_target_payload()
    )

    assert target.status_code == 200
    assert target_solver.calls == 1
    assert target_resolver.calls[0][1:] == (USER_ID, date(2026, 9, 20))
    assert required.status_code == 200
    assert required_solver.calls == 1
    assert required_resolver.calls[0][1:] == (USER_ID, date(2026, 9, 20))


def test_goal_preflight_skips_unavailable_portfolio_for_nonprojectable_goal(
    _authenticated_client,
):
    resolver = _PortfolioResolverSpy(
        PlanningPortfolioSourceUnavailableError("must not be reached")
    )
    service = _GoalPlanningServiceSpy()
    _install_portfolio_resolver(resolver)
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: _GoalReader(_goal(GoalStatus.PAUSED))
    )
    app.dependency_overrides[planning_router.get_goal_planning_service] = lambda: service

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json={
            "initial_wealth": _portfolio_selector(),
            "assumptions": _assumptions_payload(),
            "target_value_basis": "NOMINAL",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "NOT_APPLICABLE"
    assert response.json()["initial_wealth_fact"] is None
    assert resolver.calls == []
    assert service.calls == 0


def test_active_goal_uses_portfolio_after_preflight_and_source_failure_is_422(
    _authenticated_client,
):
    success = _PortfolioResolverSpy(_portfolio_fact(Decimal("123900.00")))
    _install_portfolio_resolver(success)
    service = _GoalPlanningServiceSpy()
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: _GoalReader(_goal())
    )
    app.dependency_overrides[planning_router.get_goal_planning_service] = lambda: service
    happy = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json={
            "initial_wealth": _portfolio_selector(),
            "assumptions": _assumptions_payload(),
            "target_value_basis": "NOMINAL",
        },
    )

    unavailable = _PortfolioResolverSpy(
        PlanningPortfolioSourceUnavailableError("no selected fact")
    )
    _install_portfolio_resolver(unavailable)
    failed = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json={
            "initial_wealth": _portfolio_selector(),
            "assumptions": _assumptions_payload(),
            "target_value_basis": "NOMINAL",
        },
    )

    assert happy.status_code == 200
    assert happy.json()["initial_wealth_fact"]["amount"] == "123900.00"
    assert success.calls[0][1:] == (USER_ID, date(2026, 9, 20))
    assert failed.status_code == 422
    assert unavailable.calls[0][1:] == (USER_ID, date(2026, 9, 20))
    assert service.calls == 1


def test_scenario_comparison_supports_mixed_sources_preserves_order_and_is_atomic(
    _authenticated_client,
):
    resolver = _PortfolioResolverSpy(_portfolio_fact(Decimal("200.00")))
    engine = _ComparisonSpy()
    _install_portfolio_resolver(resolver)
    app.dependency_overrides[planning_router.get_scenario_comparison_engine] = lambda: engine
    payload = {
        "scenarios": [
            {
                "scenario_id": "manual",
                "initial_wealth": _manual_selector("100.00"),
                "assumptions": _assumptions_payload(),
            },
            {
                "scenario_id": "portfolio",
                "initial_wealth": _portfolio_selector(),
                "assumptions": _assumptions_payload(),
            },
        ],
        "reference_scenario_id": "portfolio",
        "target_amount": None,
        "target_value_basis": None,
    }
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare", json=payload
    )

    assert response.status_code == 200
    assert engine.calls == 1
    assert [entry["scenario_id"] for entry in response.json()["entries"]] == [
        "manual",
        "portfolio",
    ]
    assert response.json()["entries"][1]["initial_wealth_fact"]["amount"] == "200.00"
    assert resolver.calls[0][1:] == (USER_ID, date(2026, 9, 20))

    atomic_resolver = _SequencePortfolioResolver(
        [
            _portfolio_fact(Decimal("200.00")),
            PlanningPortfolioSourceUnavailableError("unavailable second scope"),
        ]
    )
    atomic_engine = _ComparisonSpy()
    _install_portfolio_resolver(atomic_resolver)
    app.dependency_overrides[planning_router.get_scenario_comparison_engine] = lambda: atomic_engine
    atomic_payload = {
        **payload,
        "scenarios": [
            payload["scenarios"][0],
            payload["scenarios"][1],
            {
                "scenario_id": "portfolio-failure",
                "initial_wealth": _portfolio_selector(),
                "assumptions": _assumptions_payload(),
            },
        ],
    }
    failed = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare", json=atomic_payload
    )

    assert failed.status_code == 422
    assert atomic_engine.calls == 0
    assert len(atomic_resolver.calls) == 2


def test_openapi_exposes_source_only_portfolio_selector_for_all_five_requests():
    schema = app.openapi()
    serialized = str(schema)

    assert "INVESTMENT_PORTFOLIO_SNAPSHOT" in serialized
    assert "InvestmentPortfolioSnapshotInitialWealthRequestDTO" in serialized
    selector_schema = schema["components"]["schemas"][
        "InvestmentPortfolioSnapshotInitialWealthRequestDTO"
    ]
    assert set(selector_schema["properties"]) == {"source"}
    assert selector_schema["required"] == ["source"]
    for request_name in (
        "ProjectionRequestDTO",
        "TargetAchievementRequestDTO",
        "RequiredContributionRequestDTO",
        "GoalPlanningRequestDTO",
        "ScenarioComparisonRequestDTO",
    ):
        assert request_name in schema["components"]["schemas"]
