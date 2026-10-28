"""HTTP contract tests for the R6.3 consolidated Goal monitoring read model."""

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


USER_ID = UUID("00000000-0000-0000-0000-000000000811")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000812")


def _current_user(user_id=USER_ID) -> UserResponseDTO:
    return UserResponseDTO(
        id=user_id,
        email=f"{user_id}@example.test",
        name="Goal Overview User",
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _goal(sequence: int = 1, **overrides) -> GoalPlanningFact:
    values = {
        "goal_id": UUID(f"00000000-0000-0000-0000-{sequence:012d}"),
        "user_id": USER_ID,
        "name": f"Goal {sequence}",
        "description": None,
        "goal_type": GoalType.EMERGENCY_RESERVE,
        "status": GoalStatus.ACTIVE,
        "target_amount": Decimal("50000.00"),
        "target_date": date(2028, 12, 31),
        "current_amount": Decimal("35000.00"),
        "goal_planned_monthly_contribution": Decimal("750.00"),
        "priority": sequence,
        "linked_account_id": None,
        "created_at": datetime(2026, 1, sequence, 10, 0),
        "updated_at": datetime(2026, 10, 27, 9, 30),
    }
    values.update(overrides)
    return GoalPlanningFact(**values)


class _NoWriteSession:
    def add(self, *_args, **_kwargs):
        raise AssertionError("Goal overview GET must not add records")

    def flush(self, *_args, **_kwargs):
        raise AssertionError("Goal overview GET must not flush")

    def commit(self, *_args, **_kwargs):
        raise AssertionError("Goal overview GET must not commit")


class _GoalReader:
    def __init__(self, goals_by_user=None):
        self.goals_by_user = goals_by_user or {}
        self.calls = []

    def list_goals(self, db, user_id):
        self.calls.append((db, user_id))
        return tuple(self.goals_by_user.get(user_id, ()))


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _client(reader, user_id=USER_ID):
    session = _NoWriteSession()
    app.dependency_overrides[get_current_user] = lambda: _current_user(user_id)
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: reader
    )
    return TestClient(app), session


def test_empty_owned_collection_returns_zero_summary_and_no_synthetic_goals():
    reader = _GoalReader()
    client, session = _client(reader)

    with client:
        response = client.get("/api/v1/planning/goals/overview")

    assert response.status_code == 200
    assert response.json() == {
        "summary": {
            "total_goals": 0,
            "not_started": 0,
            "in_progress": 0,
            "achieved": 0,
            "exceeded": 0,
            "negative_current": 0,
            "unavailable": 0,
        },
        "goals": [],
    }
    assert reader.calls == [(session, USER_ID)]


def test_overview_serializes_context_progress_states_flags_and_order():
    goals = (
        _goal(1, current_amount=Decimal("0.00")),
        _goal(
            2,
            status=GoalStatus.PAUSED,
            current_amount=Decimal("60000.00"),
            goal_planned_monthly_contribution=Decimal("0.00"),
        ),
        _goal(
            3,
            target_amount=Decimal("0.00"),
            current_amount=None,
            goal_planned_monthly_contribution=None,
            target_date=None,
        ),
    )
    reader = _GoalReader({USER_ID: goals})
    client, _ = _client(reader)

    with client:
        body = client.get("/api/v1/planning/goals/overview").json()

    assert body["summary"] == {
        "total_goals": 3,
        "not_started": 1,
        "in_progress": 0,
        "achieved": 0,
        "exceeded": 1,
        "negative_current": 0,
        "unavailable": 1,
    }
    assert [goal["goal_id"] for goal in body["goals"]] == [
        str(goal.goal_id) for goal in goals
    ]
    assert body["goals"][0] == {
        "goal_id": str(goals[0].goal_id),
        "name": "Goal 1",
        "goal_type": "EMERGENCY_RESERVE",
        "status": "ACTIVE",
        "target_amount": "50000.00",
        "current_amount": "0.00",
        "planned_monthly_contribution": "750.00",
        "target_date": "2028-12-31",
        "gap_amount": "50000.00",
        "completion_percent": "0.00",
        "progress_state": "NOT_STARTED",
        "data_flags": [],
    }
    assert body["goals"][1]["completion_percent"] == "120.00"
    assert body["goals"][1]["gap_amount"] == "-10000.00"
    assert body["goals"][1]["progress_state"] == "EXCEEDED"
    assert body["goals"][1]["data_flags"] == ["MONTHLY_CONTRIBUTION_ZERO"]
    assert body["goals"][2]["progress_state"] == "UNAVAILABLE"
    assert body["goals"][2]["data_flags"] == [
        "TARGET_NONPOSITIVE",
        "CURRENT_MISSING",
        "MONTHLY_CONTRIBUTION_MISSING",
    ]
    assert body["goals"][2]["current_amount"] is None
    assert body["goals"][2]["gap_amount"] is None


def test_reader_is_called_with_each_authenticated_identity_and_never_crosses_data():
    owner_goal = _goal(1, user_id=USER_ID, name="Owner")
    other_goal = _goal(2, user_id=OTHER_USER_ID, name="Other")
    reader = _GoalReader(
        {USER_ID: (owner_goal,), OTHER_USER_ID: (other_goal,)}
    )

    owner_client, _ = _client(reader, USER_ID)
    with owner_client:
        owner_body = owner_client.get("/api/v1/planning/goals/overview").json()

    other_client, _ = _client(reader, OTHER_USER_ID)
    with other_client:
        other_body = other_client.get("/api/v1/planning/goals/overview").json()

    assert [item["name"] for item in owner_body["goals"]] == ["Owner"]
    assert [item["name"] for item in other_body["goals"]] == ["Other"]
    assert [user_id for _db, user_id in reader.calls] == [USER_ID, OTHER_USER_ID]


def test_defensive_owner_mismatch_and_internal_errors_are_generic():
    mismatched = _GoalReader({USER_ID: (_goal(user_id=OTHER_USER_ID),)})
    client, _ = _client(mismatched)
    with client:
        mismatch_response = client.get("/api/v1/planning/goals/overview")

    class ExplodingReader:
        def list_goals(self, *_args):
            raise RuntimeError("private SQL amount=987654.32")

    exploding_client, _ = _client(ExplodingReader())
    with exploding_client:
        error_response = exploding_client.get("/api/v1/planning/goals/overview")

    for response in (mismatch_response, error_response):
        assert response.status_code == 500
        assert response.json() == {"detail": "Goal overview could not be loaded."}
        assert "987654.32" not in response.text
        assert "SQL" not in response.text


def test_overview_requires_authentication_before_opening_financial_storage():
    app.dependency_overrides[get_db] = lambda: _NoWriteSession()
    with TestClient(app) as client:
        response = client.get("/api/v1/planning/goals/overview")

    assert response.status_code == 401


def test_overview_does_not_resolve_portfolio_or_execute_financial_engines():
    reader = _GoalReader({USER_ID: (_goal(),)})
    client, _ = _client(reader)

    def forbidden_dependency():
        raise AssertionError("Goal overview must not resolve this dependency")

    app.dependency_overrides[
        planning_router.get_planning_portfolio_source_resolver
    ] = forbidden_dependency
    app.dependency_overrides[
        planning_router.get_forward_projection_engine
    ] = forbidden_dependency
    app.dependency_overrides[
        planning_router.get_goal_planning_service
    ] = forbidden_dependency

    with client:
        response = client.get("/api/v1/planning/goals/overview")

    assert response.status_code == 200


def test_static_route_and_openapi_preserve_r61_r62_and_five_posts():
    reader = _GoalReader()
    client, _ = _client(reader)
    with client:
        response = client.get("/api/v1/planning/goals/overview")

    assert response.status_code == 200
    schema = app.openapi()
    planning_operations = {
        path: sorted(operations)
        for path, operations in schema["paths"].items()
        if path.startswith("/api/v1/planning")
    }
    assert planning_operations == {
        "/api/v1/planning/goals/overview": ["get"],
        "/api/v1/planning/goals/batch-contribution-preview": ["post"],
        "/api/v1/planning/goals/{goal_id}/context": ["get"],
        "/api/v1/planning/goals/{goal_id}/progress": ["get"],
        "/api/v1/planning/goals/{goal_id}/projection": ["post"],
        "/api/v1/planning/projection": ["post"],
        "/api/v1/planning/required-contribution": ["post"],
        "/api/v1/planning/scenarios/compare": ["post"],
        "/api/v1/planning/target-achievement": ["post"],
    }

    operation = schema["paths"]["/api/v1/planning/goals/overview"]["get"]
    assert "requestBody" not in operation
    assert operation["security"] == [{"OAuth2PasswordBearer": []}]
    assert operation.get("parameters", []) == []
    response_schema = schema["components"]["schemas"][
        "GoalMonitoringItemResponseDTO"
    ]
    assert set(response_schema["properties"]) == {
        "goal_id",
        "name",
        "goal_type",
        "status",
        "target_amount",
        "current_amount",
        "planned_monthly_contribution",
        "target_date",
        "gap_amount",
        "completion_percent",
        "progress_state",
        "data_flags",
    }
