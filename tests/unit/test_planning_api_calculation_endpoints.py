"""HTTP contract tests for the transient 10.3.8-C Planning endpoints."""

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
from backend.domains.planning.projection import ForwardProjectionEngine
from backend.domains.planning.readers import PlanningGoalReadQuery
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionSolver,
)
from backend.domains.planning.target_solver import TargetAchievementSolver
from backend.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000000111")
GOAL_ID = UUID("00000000-0000-0000-0000-000000000222")
OTHER_GOAL_ID = UUID("00000000-0000-0000-0000-000000000333")


def _current_user() -> UserResponseDTO:
    return UserResponseDTO(
        id=USER_ID,
        email="planning@example.test",
        name="Planning User",
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _goal(current_amount: Decimal | None = Decimal("900.00")) -> GoalPlanningFact:
    return GoalPlanningFact(
        goal_id=GOAL_ID,
        user_id=USER_ID,
        name="Planning Goal",
        description=None,
        goal_type=GoalType.CUSTOM,
        status=GoalStatus.ACTIVE,
        target_amount=Decimal("2000.00"),
        target_date=None,
        current_amount=current_amount,
        goal_planned_monthly_contribution=None,
        priority=None,
        linked_account_id=None,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 9, 20, 9, 30),
    )


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


class _ForwardSpy:
    def __init__(self):
        self.calls = 0
        self._engine = ForwardProjectionEngine()

    def project(self, initial_wealth_fact, assumptions):
        self.calls += 1
        return self._engine.project(initial_wealth_fact, assumptions)


class _TargetSpy:
    def __init__(self):
        self.calls = 0
        self._solver = TargetAchievementSolver()

    def solve(self, initial_wealth_fact, assumptions, target_amount):
        self.calls += 1
        return self._solver.solve(initial_wealth_fact, assumptions, target_amount)


class _RequiredSpy:
    def __init__(self):
        self.calls = 0
        self._solver = RequiredContributionSolver()

    def solve(self, initial_wealth_fact, assumptions_template, target_amount):
        self.calls += 1
        return self._solver.solve(
            initial_wealth_fact,
            assumptions_template,
            target_amount,
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


def _user_initial_wealth(amount: str = "900.00"):
    return {
        "source": "USER_PROVIDED_SCENARIO",
        "amount": amount,
        "observed_at": "2026-09-20T09:30:00-03:00",
    }


def _projection_payload(**overrides):
    payload = {
        "initial_wealth": _user_initial_wealth(),
        "assumptions": _assumptions_payload(),
    }
    payload.update(overrides)
    return payload


def _target_payload(target_amount: str = "1000.00", **overrides):
    payload = _projection_payload()
    payload.update(
        {
            "target_amount": target_amount,
            "target_value_basis": "NOMINAL",
        }
    )
    payload.update(overrides)
    return payload


def test_projection_user_source_returns_certified_timeline_decimal_strings_and_one_call(
    _authenticated_client,
):
    engine = _ForwardSpy()
    app.dependency_overrides[planning_router.get_forward_projection_engine] = (
        lambda: engine
    )

    response = _authenticated_client.post(
        "/api/v1/planning/projection",
        json=_projection_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert engine.calls == 1
    assert body["initial_wealth_fact"]["source"] == "USER_PROVIDED_SCENARIO"
    assert body["initial_wealth_fact"]["amount"] == "900.00"
    assert body["periods"][0]["ending_wealth"] == "1000.00"
    assert body["periods"][1]["ending_wealth"] == "1100.00"
    assert body["final_wealth"] == "1100.00"
    assert body["total_contributions"] == "200.00"
    assert isinstance(body["monthly_equivalent_rate"], str)
    assert "source_table" not in body["initial_wealth_fact"]["provenance"]


def test_projection_http_preserves_declared_rate_precision_and_is_deterministic(
    _authenticated_client,
):
    payload = _projection_payload(
        assumptions=_assumptions_payload(expected_return_rate="0.080000")
    )

    first = _authenticated_client.post("/api/v1/planning/projection", json=payload)
    second = _authenticated_client.post("/api/v1/planning/projection", json=payload)

    assert first.status_code == second.status_code == 200
    assert first.content == second.content
    assert first.json()["assumptions"]["expected_return_rate"] == "0.080000"


def test_projection_goal_source_is_server_resolved_and_preserves_goal_provenance(
    _authenticated_client,
):
    reader = _GoalReader(_goal())
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: reader
    )
    payload = _projection_payload(
        initial_wealth={"source": "GOAL_CURRENT_AMOUNT", "goal_id": str(GOAL_ID)}
    )

    response = _authenticated_client.post("/api/v1/planning/projection", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert reader.calls == [(GOAL_ID, USER_ID)]
    assert body["initial_wealth_fact"]["amount"] == "900.00"
    assert body["initial_wealth_fact"]["source"] == "GOAL_CURRENT_AMOUNT"
    assert body["initial_wealth_fact"]["provenance"]["goal_id"] == str(GOAL_ID)


@pytest.mark.parametrize("goal", [None, _goal()])
def test_goal_source_missing_or_other_owner_is_non_enumerating_404(
    _authenticated_client,
    goal,
):
    reader = _GoalReader(goal)
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: reader
    )
    goal_id = GOAL_ID if goal is None else OTHER_GOAL_ID
    payload = _projection_payload(
        initial_wealth={"source": "GOAL_CURRENT_AMOUNT", "goal_id": str(goal_id)}
    )

    response = _authenticated_client.post("/api/v1/planning/projection", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": "Goal not found."}


def test_goal_source_with_missing_current_amount_is_422_without_zero_fallback(
    _authenticated_client,
):
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: _GoalReader(_goal(None))
    )
    payload = _projection_payload(
        initial_wealth={"source": "GOAL_CURRENT_AMOUNT", "goal_id": str(GOAL_ID)}
    )

    response = _authenticated_client.post("/api/v1/planning/projection", json=payload)

    assert response.status_code == 422
    assert response.json() == {"detail": "selected Goal current amount is unavailable"}


def test_goal_resolution_failure_prevents_forward_engine_execution(
    _authenticated_client,
):
    engine = _ForwardSpy()
    app.dependency_overrides[planning_router.get_forward_projection_engine] = (
        lambda: engine
    )
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: _GoalReader(None)
    )

    response = _authenticated_client.post(
        "/api/v1/planning/projection",
        json=_projection_payload(
            initial_wealth={
                "source": "GOAL_CURRENT_AMOUNT",
                "goal_id": str(GOAL_ID),
            }
        ),
    )

    assert response.status_code == 404
    assert engine.calls == 0


def test_target_endpoint_preserves_achieved_and_already_achieved_domain_semantics(
    _authenticated_client,
):
    spy = _TargetSpy()
    app.dependency_overrides[planning_router.get_target_achievement_solver] = (
        lambda: spy
    )

    achieved = _authenticated_client.post(
        "/api/v1/planning/target-achievement",
        json=_target_payload(),
    )
    already = _authenticated_client.post(
        "/api/v1/planning/target-achievement",
        json=_target_payload(
            target_amount="900.00",
            initial_wealth=_user_initial_wealth("900.00"),
        ),
    )

    assert achieved.status_code == 200
    assert achieved.json()["status"] == "ACHIEVED"
    assert achieved.json()["achievement_period"] == 1
    assert achieved.json()["achievement_date"] == "2026-10-31"
    assert achieved.json()["projection_result"]["final_wealth"] == "1100.00"
    assert already.status_code == 200
    assert already.json()["status"] == "ALREADY_ACHIEVED"
    assert already.json()["achievement_period"] == 0
    assert already.json()["projection_result"] is None
    assert spy.calls == 2


def test_target_unreachable_is_a_valid_200_domain_outcome(_authenticated_client):
    response = _authenticated_client.post(
        "/api/v1/planning/target-achievement",
        json=_target_payload(
            "1000.00",
            assumptions=_assumptions_payload(scenario_monthly_contribution="0.00"),
        ),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "UNREACHABLE"


def test_target_not_reached_and_real_target_basis_are_valid_http_outcomes(
    _authenticated_client,
):
    not_reached = _authenticated_client.post(
        "/api/v1/planning/target-achievement",
        json=_target_payload(
            "10000.00",
            assumptions=_assumptions_payload(scenario_monthly_contribution="1.00"),
        ),
    )
    real = _authenticated_client.post(
        "/api/v1/planning/target-achievement",
        json=_target_payload(
            "1000.00",
            target_value_basis="REAL",
            assumptions=_assumptions_payload(
                expected_return_rate="0.08",
                output_mode="REAL",
                inflation_rate="0.04",
            ),
        ),
    )

    assert not_reached.status_code == 200
    assert not_reached.json()["status"] == "NOT_REACHED_WITHIN_HORIZON"
    assert real.status_code == 200
    assert real.json()["target_value_basis"] == "REAL"
    assert real.json()["status"] == "ACHIEVED"


def test_required_contribution_endpoint_delegates_one_solver_call_and_preserves_result(
    _authenticated_client,
):
    spy = _RequiredSpy()
    app.dependency_overrides[planning_router.get_required_contribution_solver] = (
        lambda: spy
    )

    response = _authenticated_client.post(
        "/api/v1/planning/required-contribution",
        json=_target_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert spy.calls == 1
    assert body["status"] == "SOLVED"
    assert body["required_monthly_contribution"] == "50.00"
    assert body["target_achievement_result"]["status"] == "ACHIEVED"


def test_required_contribution_preserves_template_contribution_for_the_solver(
    _authenticated_client,
):
    class CapturingRequiredSpy(_RequiredSpy):
        def __init__(self):
            super().__init__()
            self.template_contribution = None

        def solve(self, initial_wealth_fact, assumptions_template, target_amount):
            self.template_contribution = assumptions_template.scenario_monthly_contribution
            return super().solve(initial_wealth_fact, assumptions_template, target_amount)

    spy = CapturingRequiredSpy()
    app.dependency_overrides[planning_router.get_required_contribution_solver] = (
        lambda: spy
    )
    response = _authenticated_client.post(
        "/api/v1/planning/required-contribution",
        json=_target_payload(
            assumptions=_assumptions_payload(scenario_monthly_contribution="777.77")
        ),
    )

    assert response.status_code == 200
    assert spy.calls == 1
    assert spy.template_contribution == Decimal("777.77")
    assert response.json()["assumptions_template"]["scenario_monthly_contribution"] == "777.77"


def test_required_contribution_already_and_zero_contribution_required_are_200(
    _authenticated_client,
):
    already = _authenticated_client.post(
        "/api/v1/planning/required-contribution",
        json=_target_payload(
            "900.00",
            initial_wealth=_user_initial_wealth("900.00"),
        ),
    )
    zero = _authenticated_client.post(
        "/api/v1/planning/required-contribution",
        json=_target_payload(
            "950.00",
            assumptions=_assumptions_payload(
                scenario_monthly_contribution="999.99",
                expected_return_rate="1",
                horizon_months=1,
            ),
        ),
    )

    assert already.status_code == 200
    assert already.json()["status"] == "ALREADY_ACHIEVED"
    assert already.json()["required_monthly_contribution"] == "0.00"
    assert zero.status_code == 200
    assert zero.json()["status"] == "ZERO_CONTRIBUTION_REQUIRED"
    assert zero.json()["required_monthly_contribution"] == "0.00"


def test_target_basis_mismatch_is_422_before_the_target_engine_is_called(
    _authenticated_client,
):
    spy = _TargetSpy()
    app.dependency_overrides[planning_router.get_target_achievement_solver] = (
        lambda: spy
    )

    response = _authenticated_client.post(
        "/api/v1/planning/target-achievement",
        json=_target_payload(target_value_basis="REAL"),
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "target value basis must match projection output mode"
    }
    assert spy.calls == 0


def test_required_basis_mismatch_is_422_before_the_required_engine_is_called(
    _authenticated_client,
):
    spy = _RequiredSpy()
    app.dependency_overrides[planning_router.get_required_contribution_solver] = (
        lambda: spy
    )

    response = _authenticated_client.post(
        "/api/v1/planning/required-contribution",
        json=_target_payload(target_value_basis="REAL"),
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "target value basis must match projection output mode"
    }
    assert spy.calls == 0


@pytest.mark.parametrize(
    "initial_wealth",
    [
        {
            "source": "GOAL_CURRENT_AMOUNT",
            "goal_id": str(GOAL_ID),
            "amount": "999999.00",
        },
        {
            "source": "GOAL_CURRENT_AMOUNT",
            "goal_id": str(GOAL_ID),
            "provenance": {"source_table": "goals"},
        },
    ],
)
def test_http_rejects_forged_goal_fields(
    _authenticated_client,
    initial_wealth,
):
    response = _authenticated_client.post(
        "/api/v1/planning/projection",
        json=_projection_payload(initial_wealth=initial_wealth),
    )

    assert response.status_code == 422


def test_http_rejects_financial_json_numbers_and_preserves_declared_scale_to_domain(
    _authenticated_client,
):
    number = _authenticated_client.post(
        "/api/v1/planning/projection",
        json=_projection_payload(
            assumptions=_assumptions_payload(expected_return_rate=0.08)
        ),
    )
    scale = _authenticated_client.post(
        "/api/v1/planning/projection",
        json=_projection_payload(
            assumptions=_assumptions_payload(scenario_monthly_contribution="1.000")
        ),
    )

    assert number.status_code == 422
    assert scale.status_code == 422
    assert "at most two decimal places" in scale.json()["detail"]


@pytest.mark.parametrize(
    "path,payload",
    [
        (
            "/api/v1/planning/projection",
            _projection_payload(
                assumptions=_assumptions_payload(expected_return_rate=0.08)
            ),
        ),
        (
            "/api/v1/planning/target-achievement",
            _target_payload(target_amount=1000.00),
        ),
        (
            "/api/v1/planning/required-contribution",
            _target_payload(target_amount=1000.00),
        ),
    ],
)
def test_all_calculation_endpoints_reject_financial_json_numbers(
    _authenticated_client,
    path,
    payload,
):
    response = _authenticated_client.post(path, json=payload)

    assert response.status_code == 422


def test_arithmetic_error_maps_to_generic_500_without_internal_detail(
    _authenticated_client,
):
    class ExplodingEngine:
        def project(self, initial_wealth_fact, assumptions):
            raise ArithmeticError("private arithmetic implementation detail")

    app.dependency_overrides[planning_router.get_forward_projection_engine] = (
        lambda: ExplodingEngine()
    )

    response = _authenticated_client.post(
        "/api/v1/planning/projection",
        json=_projection_payload(),
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Planning calculation could not be completed."
    }


def test_all_three_calculation_endpoints_require_existing_authentication():
    with TestClient(app) as client:
        for path, payload in (
            ("/api/v1/planning/projection", _projection_payload()),
            ("/api/v1/planning/target-achievement", _target_payload()),
            ("/api/v1/planning/required-contribution", _target_payload()),
        ):
            response = client.post(path, json=payload)
            assert response.status_code == 401


def test_openapi_exposes_calculation_posts_and_the_approved_goal_post_only():
    schema = app.openapi()
    planning_paths = {
        path: sorted(operations)
        for path, operations in schema["paths"].items()
        if path.startswith("/api/v1/planning")
    }

    assert planning_paths == {
        "/api/v1/planning/goals/overview": ["get"],
        "/api/v1/planning/goals/{goal_id}/context": ["get"],
        "/api/v1/planning/goals/{goal_id}/progress": ["get"],
        "/api/v1/planning/goals/{goal_id}/projection": ["post"],
        "/api/v1/planning/projection": ["post"],
        "/api/v1/planning/required-contribution": ["post"],
        "/api/v1/planning/scenarios/compare": ["post"],
        "/api/v1/planning/target-achievement": ["post"],
    }
    projection_schema = schema["components"]["schemas"]["ProjectionRequestDTO"]
    serialized_request_schema = str(projection_schema)
    assert "INVESTMENT_PORTFOLIO_SNAPSHOT" in serialized_request_schema
    assert "ScenarioComparison" not in serialized_request_schema
