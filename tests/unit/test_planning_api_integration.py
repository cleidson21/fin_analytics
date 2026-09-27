"""Cross-endpoint integration invariants for the transient Planning API."""

from datetime import datetime
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
from backend.domains.planning.readers import PlanningGoalReadQuery
from backend.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000000811")
GOAL_ID = UUID("00000000-0000-0000-0000-000000000822")


def _current_user() -> UserResponseDTO:
    return UserResponseDTO(
        id=USER_ID,
        email="planning-integration@example.test",
        name="Planning Integration User",
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _assumptions(**overrides):
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


def _user_wealth(amount="900.00"):
    return {
        "source": "USER_PROVIDED_SCENARIO",
        "amount": amount,
        "observed_at": "2026-09-20T09:30:00-03:00",
    }


def _generic_payload(**overrides):
    payload = {"initial_wealth": _user_wealth(), "assumptions": _assumptions()}
    payload.update(overrides)
    return payload


def _target_payload(**overrides):
    payload = _generic_payload(
        target_amount="1000.00", target_value_basis="NOMINAL"
    )
    payload.update(overrides)
    return payload


def _goal_payload(**overrides):
    payload = _generic_payload(target_value_basis="NOMINAL")
    payload.update(overrides)
    return payload


def _scenario_payload(**overrides):
    payload = {
        "scenarios": [
            {
                "scenario_id": "reference",
                "initial_wealth": _user_wealth("100.00"),
                "assumptions": _assumptions(),
                "label": None,
                "archetype": "BASE",
            },
            {
                "scenario_id": "candidate",
                "initial_wealth": _user_wealth("200.00"),
                "assumptions": _assumptions(),
                "label": None,
                "archetype": "CONSERVATIVE",
            },
        ],
        "reference_scenario_id": "reference",
        "target_amount": None,
        "target_value_basis": None,
    }
    payload.update(overrides)
    return payload


class _GoalReader:
    def __init__(self, goal: GoalPlanningFact | None):
        self.goal = goal

    def get_goal(self, _db, goal_id, user_id):
        if self.goal is not None and goal_id == GOAL_ID and user_id == USER_ID:
            return self.goal
        return None

    current_amount_as_initial_wealth = staticmethod(
        PlanningGoalReadQuery.current_amount_as_initial_wealth
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


def _install_reader(goal=None):
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: _GoalReader(goal)
    )


def test_openapi_has_exactly_five_authenticated_planning_operations():
    schema = app.openapi()
    planning_operations = {
        path: operations["post"]
        for path, operations in schema["paths"].items()
        if path.startswith("/api/v1/planning") and "post" in operations
    }

    assert set(planning_operations) == {
        "/api/v1/planning/projection",
        "/api/v1/planning/target-achievement",
        "/api/v1/planning/required-contribution",
        "/api/v1/planning/goals/{goal_id}/projection",
        "/api/v1/planning/scenarios/compare",
    }
    operation_ids = [operation["operationId"] for operation in planning_operations.values()]
    assert len(operation_ids) == len(set(operation_ids))
    assert all(operation.get("security") for operation in planning_operations.values())
    request_schema_names = (
        "ProjectionRequestDTO",
        "TargetAchievementRequestDTO",
        "RequiredContributionRequestDTO",
        "GoalPlanningRequestDTO",
        "ScenarioComparisonRequestDTO",
    )
    assert all(
        "initial_wealth" in str(schema["components"]["schemas"][schema_name])
        or schema_name == "ScenarioComparisonRequestDTO"
        for schema_name in request_schema_names
    )
    assert "INVESTMENT_PORTFOLIO_SNAPSHOT" in str(schema)


def test_all_five_endpoints_reject_financial_json_numbers_and_portfolio_source(
    _authenticated_client,
):
    _install_reader()
    numeric_requests = [
        ("/api/v1/planning/projection", _generic_payload(assumptions=_assumptions(expected_return_rate=0.08))),
        ("/api/v1/planning/target-achievement", _target_payload(assumptions=_assumptions(expected_return_rate=0.08))),
        ("/api/v1/planning/required-contribution", _target_payload(assumptions=_assumptions(expected_return_rate=0.08))),
        (f"/api/v1/planning/goals/{GOAL_ID}/projection", _goal_payload(assumptions=_assumptions(expected_return_rate=0.08))),
        ("/api/v1/planning/scenarios/compare", _scenario_payload(scenarios=[
            {"scenario_id": "a", "initial_wealth": _user_wealth(), "assumptions": _assumptions(expected_return_rate=0.08), "label": None, "archetype": None},
            {"scenario_id": "b", "initial_wealth": _user_wealth(), "assumptions": _assumptions(), "label": None, "archetype": None},
        ])),
    ]
    portfolio_requests = [
        ("/api/v1/planning/projection", _generic_payload(initial_wealth={"source": "INVESTMENT_PORTFOLIO_SNAPSHOT", "account_id": "x"})),
        ("/api/v1/planning/target-achievement", _target_payload(initial_wealth={"source": "INVESTMENT_PORTFOLIO_SNAPSHOT", "account_id": "x"})),
        ("/api/v1/planning/required-contribution", _target_payload(initial_wealth={"source": "INVESTMENT_PORTFOLIO_SNAPSHOT", "account_id": "x"})),
        (f"/api/v1/planning/goals/{GOAL_ID}/projection", _goal_payload(initial_wealth={"source": "INVESTMENT_PORTFOLIO_SNAPSHOT", "account_id": "x"})),
        ("/api/v1/planning/scenarios/compare", _scenario_payload(scenarios=[
            {"scenario_id": "a", "initial_wealth": {"source": "INVESTMENT_PORTFOLIO_SNAPSHOT", "account_id": "x"}, "assumptions": _assumptions(), "label": None, "archetype": None},
            {"scenario_id": "b", "initial_wealth": _user_wealth(), "assumptions": _assumptions(), "label": None, "archetype": None},
        ])),
    ]

    for path, payload in numeric_requests + portfolio_requests:
        assert _authenticated_client.post(path, json=payload).status_code == 422


def test_goal_ownership_failure_is_non_enumerating_across_every_goal_capable_route(
    _authenticated_client,
):
    _install_reader()
    goal_selector = {"source": "GOAL_CURRENT_AMOUNT", "goal_id": str(GOAL_ID)}
    requests = [
        ("/api/v1/planning/projection", _generic_payload(initial_wealth=goal_selector)),
        ("/api/v1/planning/target-achievement", _target_payload(initial_wealth=goal_selector)),
        ("/api/v1/planning/required-contribution", _target_payload(initial_wealth=goal_selector)),
        (f"/api/v1/planning/goals/{GOAL_ID}/projection", _goal_payload()),
        ("/api/v1/planning/scenarios/compare", _scenario_payload(scenarios=[
            {"scenario_id": "goal", "initial_wealth": goal_selector, "assumptions": _assumptions(), "label": None, "archetype": None},
            {"scenario_id": "user", "initial_wealth": _user_wealth(), "assumptions": _assumptions(), "label": None, "archetype": None},
        ])),
    ]

    responses = [_authenticated_client.post(path, json=payload) for path, payload in requests]

    assert all(response.status_code == 404 for response in responses)
    assert {response.content for response in responses} == {b'{"detail":"Goal not found."}'}


def test_projection_max_horizon_serializes_all_periods_and_is_deterministic(
    _authenticated_client,
):
    payload = _generic_payload(
        initial_wealth=_user_wealth("100.00"),
        assumptions=_assumptions(
            scenario_monthly_contribution="0.00",
            horizon_months=1200,
        ),
    )

    first = _authenticated_client.post("/api/v1/planning/projection", json=payload)
    second = _authenticated_client.post("/api/v1/planning/projection", json=payload)

    assert first.status_code == second.status_code == 200
    assert first.content == second.content
    body = first.json()
    assert len(body["periods"]) == 1200
    assert body["final_wealth"] == "100.00"
    assert isinstance(body["periods"][-1]["ending_wealth"], str)


def test_all_planning_routes_require_existing_authentication():
    requests = [
        ("/api/v1/planning/projection", _generic_payload()),
        ("/api/v1/planning/target-achievement", _target_payload()),
        ("/api/v1/planning/required-contribution", _target_payload()),
        (f"/api/v1/planning/goals/{GOAL_ID}/projection", _goal_payload()),
        ("/api/v1/planning/scenarios/compare", _scenario_payload()),
    ]
    with TestClient(app) as client:
        responses = [client.post(path, json=payload) for path, payload in requests]

    assert all(response.status_code == 401 for response in responses)
