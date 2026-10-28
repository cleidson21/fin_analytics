"""HTTP contract tests for the R6.4 Goal batch contribution preview."""

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
from backend.domains.planning.readers import PlanningGoalReadQuery
from backend.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000000951")
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000952")


def _current_user(user_id=USER_ID):
    return UserResponseDTO(
        id=user_id,
        email=f"{user_id}@example.test",
        name="Batch Goal User",
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _goal(sequence: int, **overrides):
    values = {
        "goal_id": UUID(f"00000000-0000-0000-0000-{sequence:012d}"),
        "user_id": USER_ID,
        "name": f"Goal {sequence}",
        "description": None,
        "goal_type": GoalType.WEALTH_TARGET,
        "status": GoalStatus.ACTIVE,
        "target_amount": Decimal("1200.00"),
        "target_date": None,
        "current_amount": Decimal("0.00"),
        "goal_planned_monthly_contribution": None,
        "priority": sequence,
        "linked_account_id": None,
        "created_at": datetime(2026, 1, 1),
        "updated_at": datetime(2026, 10, 27),
    }
    values.update(overrides)
    return GoalPlanningFact(**values)


def _payload(goal_ids, **assumption_overrides):
    assumptions = {
        "as_of_date": "2026-10-27",
        "expected_return_rate": "0",
        "return_type": "NOMINAL",
        "output_mode": "NOMINAL",
        "inflation_rate": None,
        "horizon_months": 12,
        "rate_basis": "EFFECTIVE_ANNUAL",
        "contribution_timing": "END_OF_MONTH",
    }
    assumptions.update(assumption_overrides)
    return {
        "goal_ids": [str(goal_id) for goal_id in goal_ids],
        "assumptions": assumptions,
        "target_value_basis": "NOMINAL",
    }


class _NoWriteSession:
    def add(self, *_args, **_kwargs):
        raise AssertionError("batch preview must not add")

    def flush(self, *_args, **_kwargs):
        raise AssertionError("batch preview must not flush")

    def commit(self, *_args, **_kwargs):
        raise AssertionError("batch preview must not commit")


class _Reader:
    def __init__(self, goals):
        self.goals = {goal.goal_id: goal for goal in goals}
        self.calls = []

    def get_goals_by_ids(self, db, goal_ids, user_id):
        self.calls.append((db, tuple(goal_ids), user_id))
        return tuple(
            goal
            for goal_id in goal_ids
            if (goal := self.goals.get(goal_id)) is not None
            and goal.user_id == user_id
        )

    current_amount_as_initial_wealth = staticmethod(
        PlanningGoalReadQuery.current_amount_as_initial_wealth
    )


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    app.openapi_schema = None
    yield
    app.dependency_overrides.clear()
    app.openapi_schema = None


def _client(reader, user_id=USER_ID):
    session = _NoWriteSession()
    app.dependency_overrides[get_current_user] = lambda: _current_user(user_id)
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: reader
    )
    return TestClient(app), session


def test_batch_returns_ordered_decimal_safe_results_and_unavailable_item():
    first = _goal(2, target_amount=Decimal("1200.00"))
    second = _goal(1, target_amount=Decimal("100.00"), current_amount=Decimal("100.00"))
    missing_current = _goal(3, current_amount=None)
    reader = _Reader((first, second, missing_current))
    client, session = _client(reader)

    with client:
        response = client.post(
            "/api/v1/planning/goals/batch-contribution-preview",
            json=_payload((first.goal_id, second.goal_id, missing_current.goal_id)),
        )

    assert response.status_code == 200
    results = response.json()["results"]
    assert [result["goal_id"] for result in results] == [
        str(first.goal_id),
        str(second.goal_id),
        str(missing_current.goal_id),
    ]
    assert results[0]["required_monthly_contribution"] == "100.00"
    assert results[0]["calculation_status"] == "SOLVED"
    assert results[1]["required_monthly_contribution"] == "0.00"
    assert results[1]["calculation_status"] == "ALREADY_ACHIEVED"
    assert results[2]["availability"] == "UNAVAILABLE"
    assert results[2]["impediment_code"] == "CURRENT_AMOUNT_MISSING"
    assert results[2]["required_monthly_contribution"] is None
    assert results[0]["assumptions"] == {
        "as_of_date": "2026-10-27",
        "expected_return_rate": "0",
        "return_type": "NOMINAL",
        "output_mode": "NOMINAL",
        "inflation_rate": None,
        "horizon_months": 12,
        "rate_basis": "EFFECTIVE_ANNUAL",
        "contribution_timing": "END_OF_MONTH",
    }
    assert reader.calls == [
        (session, (first.goal_id, second.goal_id, missing_current.goal_id), USER_ID)
    ]


def test_missing_and_foreign_goal_are_indistinguishable_404s():
    owned = _goal(1)
    foreign = _goal(2, user_id=OTHER_USER_ID)
    reader = _Reader((owned, foreign))
    client, _ = _client(reader)

    with client:
        missing = client.post(
            "/api/v1/planning/goals/batch-contribution-preview",
            json=_payload((owned.goal_id, UUID(int=999))),
        )
        wrong_owner = client.post(
            "/api/v1/planning/goals/batch-contribution-preview",
            json=_payload((owned.goal_id, foreign.goal_id)),
        )

    assert missing.status_code == wrong_owner.status_code == 404
    assert missing.json() == wrong_owner.json() == {
        "detail": "One or more Goals were not found."
    }


def test_two_authenticated_identities_receive_only_their_owned_goal():
    owner_goal = _goal(1, user_id=USER_ID, name="Owner")
    other_goal = _goal(2, user_id=OTHER_USER_ID, name="Other")
    reader = _Reader((owner_goal, other_goal))

    owner_client, _ = _client(reader, USER_ID)
    with owner_client:
        owner_response = owner_client.post(
            "/api/v1/planning/goals/batch-contribution-preview",
            json=_payload((owner_goal.goal_id,)),
        )

    other_client, _ = _client(reader, OTHER_USER_ID)
    with other_client:
        other_response = other_client.post(
            "/api/v1/planning/goals/batch-contribution-preview",
            json=_payload((other_goal.goal_id,)),
        )

    assert owner_response.status_code == other_response.status_code == 200
    assert owner_response.json()["results"][0]["name"] == "Owner"
    assert other_response.json()["results"][0]["name"] == "Other"


def test_internal_reader_failure_is_generic_and_does_not_resolve_portfolio():
    class _ExplodingReader:
        def get_goals_by_ids(self, *_args):
            raise RuntimeError("private SQL amount=987654.32")

    client, _ = _client(_ExplodingReader())

    def forbidden_portfolio():
        raise AssertionError("batch Goal preview must not resolve MyProfit")

    app.dependency_overrides[
        planning_router.get_planning_portfolio_source_resolver
    ] = forbidden_portfolio
    with client:
        response = client.post(
            "/api/v1/planning/goals/batch-contribution-preview",
            json=_payload((UUID(int=1),)),
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Planning error."}
    assert "987654.32" not in response.text
    assert "SQL" not in response.text


@pytest.mark.parametrize(
    "goal_ids",
    [
        [],
        ["not-a-uuid"],
        [str(UUID(int=1)), str(UUID(int=1))],
        [str(UUID(int=value)) for value in range(1, 22)],
    ],
)
def test_collection_validation_rejects_empty_invalid_duplicate_and_over_limit(goal_ids):
    client, _ = _client(_Reader(()))
    payload = _payload(())
    payload["goal_ids"] = goal_ids

    with client:
        response = client.post(
            "/api/v1/planning/goals/batch-contribution-preview",
            json=payload,
        )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "overrides",
    [
        {"expected_return_rate": 0.1},
        {"expected_return_rate": "-1"},
        {"horizon_months": 0},
        {"horizon_months": 1201},
        {"horizon_months": "12"},
    ],
)
def test_invalid_rate_and_horizon_inputs_fail_without_financial_coercion(overrides):
    goal = _goal(1)
    client, _ = _client(_Reader((goal,)))

    with client:
        response = client.post(
            "/api/v1/planning/goals/batch-contribution-preview",
            json=_payload((goal.goal_id,), **overrides),
        )

    assert response.status_code == 422


def test_target_basis_must_match_output_mode():
    goal = _goal(1)
    client, _ = _client(_Reader((goal,)))
    payload = _payload((goal.goal_id,), output_mode="REAL", inflation_rate="0.04")

    with client:
        response = client.post(
            "/api/v1/planning/goals/batch-contribution-preview",
            json=payload,
        )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "target value basis must match projection output mode"
    )


def test_batch_requires_authentication_before_reading_storage():
    app.dependency_overrides[get_db] = lambda: _NoWriteSession()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/planning/goals/batch-contribution-preview",
            json=_payload((UUID(int=1),)),
        )

    assert response.status_code == 401


def test_openapi_adds_authenticated_batch_post_without_financial_numbers():
    schema = app.openapi()
    operation = schema["paths"][
        "/api/v1/planning/goals/batch-contribution-preview"
    ]["post"]
    assert operation["security"] == [{"OAuth2PasswordBearer": []}]
    request_schema = schema["components"]["schemas"][
        "GoalBatchContributionAssumptionsRequestDTO"
    ]
    assert request_schema["properties"]["expected_return_rate"]["type"] == "string"
    assert "scenario_monthly_contribution" not in request_schema["properties"]
    assert "target_date" not in request_schema["properties"]
    response_schema = schema["components"]["schemas"][
        "GoalBatchContributionItemResponseDTO"
    ]
    assert response_schema["properties"]["required_monthly_contribution"]["anyOf"][0]["type"] == "string"
