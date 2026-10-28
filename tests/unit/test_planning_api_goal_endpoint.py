"""HTTP contract tests for the owned 10.3.8-D Goal Planning endpoint."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies.auth import get_current_user
from backend.api.routers import planning as planning_router
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.database.session import get_db
from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domain.enums.user_role import UserRole
from backend.domains.planning.facts import GoalPlanningFact
from backend.domains.planning.goal_planning import GoalPlanningService
from backend.domains.planning.readers import PlanningGoalReadQuery
from backend.domains.planning.target_solver import TargetAchievementSolver
from backend.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000000411")
GOAL_ID = UUID("00000000-0000-0000-0000-000000000422")
OTHER_GOAL_ID = UUID("00000000-0000-0000-0000-000000000433")


def _current_user() -> UserResponseDTO:
    return UserResponseDTO(
        id=USER_ID,
        email="goal-planning@example.test",
        name="Goal Planning User",
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _goal(**overrides) -> GoalPlanningFact:
    values = {
        "goal_id": GOAL_ID,
        "user_id": USER_ID,
        "name": "Goal Planning Goal",
        "description": None,
        "goal_type": GoalType.CUSTOM,
        "status": GoalStatus.ACTIVE,
        "target_amount": Decimal("1000.00"),
        "target_date": date(2026, 10, 1),
        "current_amount": Decimal("900.00"),
        "goal_planned_monthly_contribution": Decimal("999.99"),
        "priority": 1,
        "linked_account_id": None,
        "created_at": datetime(2026, 1, 1),
        "updated_at": datetime(2026, 9, 20, 9, 30),
    }
    values.update(overrides)
    return GoalPlanningFact(**values)


class _GoalReader:
    def __init__(self, goal: GoalPlanningFact | None):
        self.goal = goal
        self.calls: list[tuple[object, object]] = []

    def get_goal(self, db, goal_id, user_id):
        self.calls.append((goal_id, user_id))
        return self.goal if goal_id == GOAL_ID and user_id == USER_ID else None

    current_amount_as_initial_wealth = staticmethod(
        PlanningGoalReadQuery.current_amount_as_initial_wealth
    )


class _CountingTargetSolver(TargetAchievementSolver):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def solve(self, initial_wealth_fact, assumptions, target_amount):
        self.calls += 1
        return super().solve(initial_wealth_fact, assumptions, target_amount)


class _GoalPlanningServiceSpy:
    def __init__(self):
        self.target_solver = _CountingTargetSolver()
        self.service = GoalPlanningService(self.target_solver)
        self.preflight_calls = 0
        self.calls = 0
        self.last_goal = None
        self.last_initial = None
        self.last_assumptions = None
        self.last_basis = None

    def preflight_applicability(
        self,
        goal_fact,
        assumptions,
        target_value_basis,
        initial_wealth_fact=None,
    ):
        self.preflight_calls += 1
        return self.service.preflight_applicability(
            goal_fact,
            assumptions,
            target_value_basis,
            initial_wealth_fact,
        )

    def evaluate(self, goal_fact, initial_wealth_fact, assumptions, target_value_basis):
        self.calls += 1
        self.last_goal = goal_fact
        self.last_initial = initial_wealth_fact
        self.last_assumptions = assumptions
        self.last_basis = target_value_basis
        return self.service.evaluate(
            goal_fact,
            initial_wealth_fact,
            assumptions,
            target_value_basis,
        )


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


def _user_initial_wealth(amount="900.00"):
    return {
        "source": "USER_PROVIDED_SCENARIO",
        "amount": amount,
        "observed_at": "2026-09-20T09:30:00-03:00",
    }


def _payload(**overrides):
    payload = {
        "initial_wealth": _user_initial_wealth(),
        "assumptions": _assumptions_payload(),
        "target_value_basis": "NOMINAL",
    }
    payload.update(overrides)
    return payload


def _install_goal_reader(goal):
    reader = _GoalReader(goal)
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: reader
    )
    return reader


def _install_service():
    service = _GoalPlanningServiceSpy()
    app.dependency_overrides[planning_router.get_goal_planning_service] = (
        lambda: service
    )
    return service


def test_owned_active_goal_uses_server_fact_and_service_once(_authenticated_client):
    reader = _install_goal_reader(_goal())
    service = _install_service()

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert reader.calls == [(GOAL_ID, USER_ID)]
    assert service.preflight_calls == 1
    assert service.calls == 1
    assert service.target_solver.calls == 1
    assert body["status"] == "PROJECTED_ON_TIME"
    assert body["goal_fact"]["target_amount"] == "1000.00"
    assert body["goal_fact"]["goal_planned_monthly_contribution"] == "999.99"
    assert body["initial_wealth_fact"]["source"] == "USER_PROVIDED_SCENARIO"
    assert body["initial_wealth_fact"]["amount"] == "900.00"
    assert body["target_achievement_result"]["achievement_date"] == "2026-10-31"


def test_path_goal_current_amount_has_no_second_goal_identity_and_preserves_provenance(
    _authenticated_client,
):
    _install_goal_reader(_goal(current_amount=Decimal("900.00")))
    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth={"source": "GOAL_CURRENT_AMOUNT"}),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["initial_wealth_fact"]["source"] == "GOAL_CURRENT_AMOUNT"
    assert body["initial_wealth_fact"]["amount"] == "900.00"
    assert body["initial_wealth_fact"]["provenance"]["goal_id"] == str(GOAL_ID)


def test_goal_missing_and_wrong_owner_are_non_enumerating(_authenticated_client):
    for reader_goal, path_goal_id in ((None, GOAL_ID), (_goal(), OTHER_GOAL_ID)):
        reader = _install_goal_reader(reader_goal)
        response = _authenticated_client.post(
            f"/api/v1/planning/goals/{path_goal_id}/projection",
            json=_payload(),
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Goal not found."}
        assert reader.calls == [(path_goal_id, USER_ID)]


def test_goal_current_amount_unavailable_is_422_structural_fact_error(
    _authenticated_client,
):
    service = _install_service()
    _install_goal_reader(_goal(current_amount=None))

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth={"source": "GOAL_CURRENT_AMOUNT"}),
    )

    assert response.status_code == 422
    assert service.preflight_calls == 1
    assert service.calls == 0


@pytest.mark.parametrize(
    "goal_overrides",
    [
        {"status": GoalStatus.ACHIEVED},
        {"status": GoalStatus.PAUSED},
        {"status": GoalStatus.CANCELLED},
        {"goal_type": GoalType.RETIREMENT},
        {"goal_type": GoalType.FINANCIAL_INDEPENDENCE},
        {"goal_type": GoalType.DIVIDEND_INCOME},
    ],
)
def test_nonprojectable_goal_does_not_resolve_unavailable_current_amount(
    _authenticated_client,
    goal_overrides,
):
    service = _install_service()
    _install_goal_reader(_goal(current_amount=None, **goal_overrides))

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth={"source": "GOAL_CURRENT_AMOUNT"}),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "NOT_APPLICABLE"
    assert body["initial_wealth_fact"] is None
    assert body["target_achievement_result"] is None
    assert service.preflight_calls == 1
    assert service.calls == 0
    assert service.target_solver.calls == 0


def test_goal_endpoint_preflights_before_goal_current_amount_resolution(
    _authenticated_client,
):
    events: list[str] = []

    def install_ordered(goal):
        reader = _GoalReader(goal)
        get_goal = reader.get_goal

        def ordered_get_goal(db, goal_id, user_id):
            events.append("goal_lookup")
            return get_goal(db, goal_id, user_id)

        def ordered_current_amount(goal_fact):
            events.append("source_resolution")
            return PlanningGoalReadQuery.current_amount_as_initial_wealth(goal_fact)

        reader.get_goal = ordered_get_goal
        reader.current_amount_as_initial_wealth = ordered_current_amount
        app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
            lambda: reader
        )

        service = _GoalPlanningServiceSpy()
        preflight = service.preflight_applicability
        evaluate = service.evaluate

        def ordered_preflight(*args, **kwargs):
            events.append("preflight")
            return preflight(*args, **kwargs)

        def ordered_evaluate(*args, **kwargs):
            events.append("evaluate")
            return evaluate(*args, **kwargs)

        service.preflight_applicability = ordered_preflight
        service.evaluate = ordered_evaluate
        app.dependency_overrides[planning_router.get_goal_planning_service] = (
            lambda: service
        )
        return service

    active_service = install_ordered(_goal(current_amount=Decimal("900.00")))
    active = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth={"source": "GOAL_CURRENT_AMOUNT"}),
    )

    assert active.status_code == 200
    assert events == ["goal_lookup", "preflight", "source_resolution", "evaluate"]
    assert active_service.target_solver.calls == 1

    events.clear()
    nonprojectable_service = install_ordered(
        _goal(status=GoalStatus.ACHIEVED, current_amount=Decimal("900.00"))
    )
    nonprojectable = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth={"source": "GOAL_CURRENT_AMOUNT"}),
    )

    assert nonprojectable.status_code == 200
    assert nonprojectable.json()["status"] == "NOT_APPLICABLE"
    assert events == ["goal_lookup", "preflight"]
    assert nonprojectable_service.target_solver.calls == 0


def test_user_provided_wealth_is_not_replaced_by_goal_current_amount(
    _authenticated_client,
):
    service = _install_service()
    _install_goal_reader(_goal(current_amount=Decimal("900.00")))

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth=_user_initial_wealth("1000.00")),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ALREADY_ACHIEVED"
    assert service.last_initial.amount == Decimal("1000.00")
    assert service.last_initial.source.value == "USER_PROVIDED_SCENARIO"


def test_active_mathematical_already_is_not_goal_lifecycle_mutation(
    _authenticated_client,
):
    _install_goal_reader(_goal(target_date=None))
    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth=_user_initial_wealth("1000.00")),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ALREADY_ACHIEVED"
    assert body["goal_fact"]["status"] == "ACTIVE"
    assert body["target_achievement_result"]["status"] == "ALREADY_ACHIEVED"


@pytest.mark.parametrize("amount", ["900.00", "1000.00", "1100.00"])
def test_lifecycle_achieved_never_becomes_mathematical_already(
    _authenticated_client,
    amount,
):
    service = _install_service()
    _install_goal_reader(_goal(status=GoalStatus.ACHIEVED))

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth=_user_initial_wealth(amount)),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "NOT_APPLICABLE"
    assert response.json()["target_achievement_result"] is None
    assert service.target_solver.calls == 0


@pytest.mark.parametrize("goal_status", [GoalStatus.PAUSED, GoalStatus.CANCELLED])
def test_paused_and_cancelled_goals_are_not_applicable_without_solver(
    _authenticated_client,
    goal_status,
):
    service = _install_service()
    _install_goal_reader(_goal(status=goal_status))

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "NOT_APPLICABLE"
    assert service.target_solver.calls == 0


@pytest.mark.parametrize(
    "goal_type",
    [
        GoalType.RETIREMENT,
        GoalType.FINANCIAL_INDEPENDENCE,
        GoalType.DIVIDEND_INCOME,
    ],
)
def test_reserved_goal_types_are_not_applicable_without_solver(
    _authenticated_client,
    goal_type,
):
    service = _install_service()
    _install_goal_reader(_goal(goal_type=goal_type))

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "NOT_APPLICABLE"
    assert service.target_solver.calls == 0


def test_missing_basis_remains_domain_insufficient_or_not_applicable(
    _authenticated_client,
):
    active_service = _install_service()
    _install_goal_reader(_goal())
    active = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(target_value_basis=None),
    )

    assert active.status_code == 200
    assert active.json()["status"] == "INSUFFICIENT_DATA"
    assert active_service.target_solver.calls == 0

    nonprojectable_service = _install_service()
    _install_goal_reader(_goal(status=GoalStatus.ACHIEVED))
    nonprojectable = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(target_value_basis=None),
    )

    assert nonprojectable.status_code == 200
    assert nonprojectable.json()["status"] == "NOT_APPLICABLE"
    assert nonprojectable_service.target_solver.calls == 0


def test_nonprojectable_goal_ignores_basis_mismatch_before_solver(
    _authenticated_client,
):
    service = _install_service()
    _install_goal_reader(_goal(status=GoalStatus.ACHIEVED))

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(target_value_basis="REAL"),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "NOT_APPLICABLE"
    assert service.target_solver.calls == 0


def test_active_basis_mismatch_is_422_before_target_solver(_authenticated_client):
    service = _install_service()
    _install_goal_reader(_goal())
    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(
            target_value_basis="REAL",
            assumptions=_assumptions_payload(
                output_mode="REAL",
                inflation_rate="0.04",
            ),
        ),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PROJECTED_LATE"
    assert service.target_solver.calls == 1

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(target_value_basis="REAL"),
    )
    assert response.status_code == 422
    assert service.target_solver.calls == 1


def test_deadline_and_horizon_remain_separate_domain_inputs(_authenticated_client):
    _install_goal_reader(_goal(target_date=None))
    missing_deadline = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(),
    )
    already = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth=_user_initial_wealth("1000.00")),
    )

    assert missing_deadline.status_code == 200
    assert missing_deadline.json()["status"] == "INSUFFICIENT_DATA"
    assert already.status_code == 200
    assert already.json()["status"] == "ALREADY_ACHIEVED"


@pytest.mark.parametrize(
    "target_date,expected_status",
    [
        (date(2026, 11, 1), "PROJECTED_EARLY"),
        (date(2026, 10, 1), "PROJECTED_ON_TIME"),
        (date(2026, 9, 1), "PROJECTED_LATE"),
    ],
)
def test_goal_timing_statuses_are_certified_by_the_service(
    _authenticated_client,
    target_date,
    expected_status,
):
    _install_goal_reader(_goal(target_date=target_date))
    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == expected_status


def test_not_reached_preserves_nested_target_result(_authenticated_client):
    _install_goal_reader(_goal(target_amount=Decimal("10000.00")))
    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "NOT_REACHED_WITHIN_HORIZON"
    assert body["target_achievement_result"]["status"] == "NOT_REACHED_WITHIN_HORIZON"


def test_unreachable_preserves_nested_target_result(_authenticated_client):
    _install_goal_reader(_goal(target_amount=Decimal("1000.00")))
    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(
            initial_wealth=_user_initial_wealth("900.00"),
            assumptions=_assumptions_payload(scenario_monthly_contribution="0.00"),
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "NOT_REACHED_WITHIN_HORIZON"
    assert body["target_achievement_result"]["status"] == "UNREACHABLE"


def test_goal_planned_contribution_never_replaces_scenario_contribution(
    _authenticated_client,
):
    service = _install_service()
    _install_goal_reader(_goal(goal_planned_monthly_contribution=Decimal("999.99")))
    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(
            assumptions=_assumptions_payload(scenario_monthly_contribution="1.23")
        ),
    )

    assert response.status_code == 200
    assert response.json()["goal_fact"]["goal_planned_monthly_contribution"] == "999.99"
    assert response.json()["assumptions"]["scenario_monthly_contribution"] == "1.23"
    assert service.last_assumptions.scenario_monthly_contribution == Decimal("1.23")


@pytest.mark.parametrize(
    "initial_wealth",
    [
        {"source": "GOAL_CURRENT_AMOUNT", "goal_id": str(OTHER_GOAL_ID)},
        {"source": "GOAL_CURRENT_AMOUNT", "amount": "999.00"},
    ],
)
def test_goal_endpoint_rejects_second_goal_identity_and_forged_fields(
    _authenticated_client,
    initial_wealth,
):
    _install_goal_reader(_goal())
    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth=initial_wealth),
    )

    assert response.status_code == 422


def test_goal_endpoint_rejects_forged_server_owned_goal_fields_and_decimal_numbers(
    _authenticated_client,
):
    _install_goal_reader(_goal())
    forged = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(goal_status="ACHIEVED", goal_target_amount="1.00"),
    )
    numeric = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth=_user_initial_wealth(900.00)),
    )

    assert forged.status_code == 422
    assert numeric.status_code == 422


def test_nonprojectable_goal_still_rejects_malformed_user_provided_amount(
    _authenticated_client,
):
    service = _install_service()
    _install_goal_reader(_goal(status=GoalStatus.ACHIEVED, current_amount=None))

    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(initial_wealth=_user_initial_wealth(900.00)),
    )

    assert response.status_code == 422
    assert service.preflight_calls == 0
    assert service.calls == 0
    assert service.target_solver.calls == 0


def test_goal_endpoint_maps_arithmetic_errors_to_generic_500(_authenticated_client):
    class ExplodingService:
        def preflight_applicability(self, *args):
            return None

        def evaluate(self, *args):
            raise ArithmeticError("private goal-planning arithmetic detail")

    _install_goal_reader(_goal())
    app.dependency_overrides[planning_router.get_goal_planning_service] = (
        lambda: ExplodingService()
    )
    response = _authenticated_client.post(
        f"/api/v1/planning/goals/{GOAL_ID}/projection",
        json=_payload(),
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Planning calculation could not be completed."
    }


def test_goal_endpoint_requires_authentication():
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/planning/goals/{GOAL_ID}/projection",
            json=_payload(),
        )

    assert response.status_code == 401


def test_openapi_exposes_goal_endpoint_without_scenario_comparison():
    schema = app.openapi()
    planning_paths = {
        path: sorted(operations)
        for path, operations in schema["paths"].items()
        if path.startswith("/api/v1/planning")
    }

    assert planning_paths == {
        "/api/v1/planning/goals/{goal_id}/context": ["get"],
        "/api/v1/planning/goals/{goal_id}/progress": ["get"],
        "/api/v1/planning/goals/{goal_id}/projection": ["post"],
        "/api/v1/planning/projection": ["post"],
        "/api/v1/planning/required-contribution": ["post"],
        "/api/v1/planning/scenarios/compare": ["post"],
        "/api/v1/planning/target-achievement": ["post"],
    }
    request_schema = schema["components"]["schemas"]["GoalPlanningRequestDTO"]
    serialized = str(request_schema)
    assert "INVESTMENT_PORTFOLIO_SNAPSHOT" in serialized
    assert "goal_status" not in serialized
    assert "goal_target_amount" not in serialized
