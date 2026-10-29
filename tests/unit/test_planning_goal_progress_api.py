"""HTTP contract tests for the R6.2 owned-Goal progress read model."""

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
from backend.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000000711")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000712")
GOAL_ID = UUID("00000000-0000-0000-0000-000000000721")
OTHER_GOAL_ID = UUID("00000000-0000-0000-0000-000000000722")


def _current_user() -> UserResponseDTO:
    return UserResponseDTO(
        id=USER_ID,
        email="goal-progress@example.test",
        name="Goal Progress User",
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
        "name": "Reserva de emergência",
        "description": None,
        "goal_type": GoalType.EMERGENCY_RESERVE,
        "status": GoalStatus.ACTIVE,
        "target_amount": Decimal("50000.00"),
        "target_date": date(2028, 12, 31),
        "current_amount": Decimal("18500.00"),
        "goal_planned_monthly_contribution": Decimal("750.00"),
        "priority": 1,
        "linked_account_id": None,
        "created_at": datetime(2026, 1, 1, 10, 0),
        "updated_at": datetime(2026, 10, 27, 9, 30),
    }
    values.update(overrides)
    return GoalPlanningFact(**values)


class _NoWriteSession:
    def add(self, *_args, **_kwargs):
        raise AssertionError("Goal progress GET must not add records")

    def flush(self, *_args, **_kwargs):
        raise AssertionError("Goal progress GET must not flush")

    def commit(self, *_args, **_kwargs):
        raise AssertionError("Goal progress GET must not commit")


class _GoalReader:
    def __init__(self, goal: GoalPlanningFact | None):
        self.goal = goal
        self.calls: list[tuple[object, UUID, UUID]] = []

    def get_goal(self, db, goal_id, user_id):
        self.calls.append((db, goal_id, user_id))
        return self.goal


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client():
    session = _NoWriteSession()
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_db] = lambda: session
    with TestClient(app) as client:
        yield client, session


def _install_reader(goal: GoalPlanningFact | None) -> _GoalReader:
    reader = _GoalReader(goal)
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: reader
    )
    return reader


@pytest.mark.parametrize(
    ("target", "current", "expected_gap", "expected_percent"),
    [
        ("50000.00", "18500.00", "31500.00", "37.00"),
        ("50000.00", "50000.00", "0.00", "100.00"),
        ("50000.00", "60000.00", "-10000.00", "120.00"),
        ("50000.00", "0.00", "50000.00", "0.00"),
        ("3.00", "1.00", "2.00", "33.33"),
    ],
)
def test_owned_goal_returns_decimal_safe_signed_progress(
    authenticated_client,
    target,
    current,
    expected_gap,
    expected_percent,
):
    client, session = authenticated_client
    reader = _install_reader(
        _goal(target_amount=Decimal(target), current_amount=Decimal(current))
    )

    response = client.get(f"/api/v1/planning/goals/{GOAL_ID}/progress")

    assert response.status_code == 200
    assert response.json() == {
        "goal_id": str(GOAL_ID),
        "name": "Reserva de emergência",
        "target_amount": target,
        "current_amount": current,
        "gap_amount": expected_gap,
        "completion_percent": expected_percent,
    }
    assert reader.calls == [(session, GOAL_ID, USER_ID)]
    assert all(
        isinstance(response.json()[field], str)
        for field in (
            "target_amount",
            "current_amount",
            "gap_amount",
            "completion_percent",
        )
    )


@pytest.mark.parametrize(
    ("target", "current", "expected"),
    [
        (Decimal("50000.00"), None, ("50000.00", None, None, None)),
        (None, Decimal("10.00"), (None, "10.00", None, None)),
        (Decimal("0.00"), Decimal("10.00"), ("0.00", "10.00", "-10.00", None)),
        (Decimal("-5.00"), Decimal("10.00"), ("-5.00", "10.00", "-15.00", None)),
    ],
)
def test_progress_preserves_null_zero_and_nonpositive_target(
    authenticated_client,
    target,
    current,
    expected,
):
    client, _ = authenticated_client
    _install_reader(_goal(target_amount=target, current_amount=current))

    body = client.get(f"/api/v1/planning/goals/{GOAL_ID}/progress").json()

    assert (
        body["target_amount"],
        body["current_amount"],
        body["gap_amount"],
        body["completion_percent"],
    ) == expected


@pytest.mark.parametrize("goal_status", list(GoalStatus))
def test_every_goal_lifecycle_status_is_readable(authenticated_client, goal_status):
    client, _ = authenticated_client
    _install_reader(_goal(status=goal_status))

    response = client.get(f"/api/v1/planning/goals/{GOAL_ID}/progress")

    assert response.status_code == 200
    assert response.json()["completion_percent"] == "37.00"


def test_missing_wrong_owner_and_mismatched_return_are_non_enumerating(
    authenticated_client,
):
    client, _ = authenticated_client
    responses = []

    for goal_id, goal in (
        (GOAL_ID, None),
        (OTHER_GOAL_ID, None),
        (GOAL_ID, _goal(user_id=OTHER_USER_ID)),
    ):
        _install_reader(goal)
        responses.append(client.get(f"/api/v1/planning/goals/{goal_id}/progress"))

    assert [(response.status_code, response.json()) for response in responses] == [
        (404, {"detail": "Goal not found."}),
        (404, {"detail": "Goal not found."}),
        (404, {"detail": "Goal not found."}),
    ]


def test_invalid_uuid_is_fastapi_422_without_reader_call(authenticated_client):
    client, _ = authenticated_client
    reader = _install_reader(_goal())

    response = client.get("/api/v1/planning/goals/not-a-uuid/progress")

    assert response.status_code == 422
    assert reader.calls == []


def test_progress_requires_authentication_without_opening_financial_storage():
    app.dependency_overrides[get_db] = lambda: _NoWriteSession()
    with TestClient(app) as client:
        response = client.get(f"/api/v1/planning/goals/{GOAL_ID}/progress")

    assert response.status_code == 401


def test_unexpected_read_failure_is_generic_and_does_not_leak_details(
    authenticated_client,
):
    client, _ = authenticated_client

    class ExplodingReader:
        def get_goal(self, *_args):
            raise RuntimeError("private SQL and amount=987654.32")

    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: ExplodingReader()
    )

    response = client.get(f"/api/v1/planning/goals/{GOAL_ID}/progress")

    assert response.status_code == 500
    assert response.json() == {"detail": "Goal progress could not be loaded."}
    assert "987654.32" not in response.text
    assert "SQL" not in response.text


def test_progress_get_never_resolves_portfolio_or_executes_financial_engines(
    authenticated_client,
):
    client, _ = authenticated_client
    _install_reader(_goal())

    def forbidden_dependency():
        raise AssertionError("Goal progress must not resolve this dependency")

    app.dependency_overrides[
        planning_router.get_planning_portfolio_source_resolver
    ] = forbidden_dependency
    app.dependency_overrides[
        planning_router.get_forward_projection_engine
    ] = forbidden_dependency
    app.dependency_overrides[
        planning_router.get_goal_planning_service
    ] = forbidden_dependency

    response = client.get(f"/api/v1/planning/goals/{GOAL_ID}/progress")

    assert response.status_code == 200


def test_openapi_contract_and_existing_planning_operations_are_preserved():
    schema = app.openapi()
    planning_operations = {
        path: sorted(operations)
        for path, operations in schema["paths"].items()
        if path.startswith("/api/v1/planning")
    }

    assert planning_operations == {
        "/api/v1/planning/goals/overview": ["get"],
        "/api/v1/planning/goals/batch-contribution-preview": ["post"],
        "/api/v1/planning/goals/budget-preview": ["post"],
        "/api/v1/planning/goals/{goal_id}/context": ["get"],
        "/api/v1/planning/goals/{goal_id}/progress": ["get"],
        "/api/v1/planning/goals/{goal_id}/projection": ["post"],
        "/api/v1/planning/projection": ["post"],
        "/api/v1/planning/required-contribution": ["post"],
        "/api/v1/planning/scenarios/compare": ["post"],
        "/api/v1/planning/target-achievement": ["post"],
    }

    operation = schema["paths"]["/api/v1/planning/goals/{goal_id}/progress"]["get"]
    assert "requestBody" not in operation
    assert operation["security"] == [{"OAuth2PasswordBearer": []}]
    assert operation["parameters"] == [
        {
            "name": "goal_id",
            "in": "path",
            "required": True,
            "schema": {"type": "string", "format": "uuid", "title": "Goal Id"},
        }
    ]
    response_schema = schema["components"]["schemas"]["GoalProgressResponseDTO"]
    assert set(response_schema["properties"]) == {
        "goal_id",
        "name",
        "target_amount",
        "current_amount",
        "gap_amount",
        "completion_percent",
    }
    assert response_schema["properties"]["target_amount"]["anyOf"][0]["type"] == "string"
