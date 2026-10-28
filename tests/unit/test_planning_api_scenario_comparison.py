"""HTTP contract tests for the transient 10.3.8-E Scenario Comparison endpoint."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies.auth import get_current_user
from backend.api.planning_mapping import map_scenario_comparison_result
from backend.api.routers import planning as planning_router
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.database.session import get_db
from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.goal_type import GoalType
from backend.domain.enums.user_role import UserRole
from backend.domains.planning.facts import GoalPlanningFact
from backend.domains.planning.readers import PlanningGoalReadQuery
from backend.domains.planning.scenario_comparison import ScenarioComparisonEngine
from backend.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000000411")
GOAL_A_ID = UUID("00000000-0000-0000-0000-000000000422")
GOAL_B_ID = UUID("00000000-0000-0000-0000-000000000433")
OTHER_GOAL_ID = UUID("00000000-0000-0000-0000-000000000444")


def _current_user() -> UserResponseDTO:
    return UserResponseDTO(
        id=USER_ID,
        email="comparison@example.test",
        name="Comparison User",
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _goal(
    goal_id: UUID,
    current_amount: Decimal | None,
    *,
    status: GoalStatus = GoalStatus.ACTIVE,
    goal_type: GoalType = GoalType.CUSTOM,
) -> GoalPlanningFact:
    return GoalPlanningFact(
        goal_id=goal_id,
        user_id=USER_ID,
        name="Source Goal",
        description=None,
        goal_type=goal_type,
        status=status,
        target_amount=Decimal("1000.00"),
        target_date=None,
        current_amount=current_amount,
        goal_planned_monthly_contribution=None,
        priority=None,
        linked_account_id=None,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 9, 20, 9, 30),
    )


class _GoalReader:
    def __init__(self, goals: dict[UUID, GoalPlanningFact]):
        self.goals = goals
        self.calls: list[tuple[object, object]] = []

    def get_goal(self, db, goal_id, user_id):
        self.calls.append((goal_id, user_id))
        return self.goals.get(goal_id) if user_id == USER_ID else None

    current_amount_as_initial_wealth = staticmethod(
        PlanningGoalReadQuery.current_amount_as_initial_wealth
    )


class _ComparisonSpy:
    def __init__(self, engine=None):
        self.calls = 0
        self.scenarios = None
        self.result = None
        self._engine = engine or ScenarioComparisonEngine()

    def compare(self, scenarios, reference_scenario_id, target_amount=None, target_value_basis=None):
        self.calls += 1
        self.scenarios = scenarios
        self.result = self._engine.compare(
            scenarios,
            reference_scenario_id,
            target_amount,
            target_value_basis,
        )
        return self.result


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
        "scenario_monthly_contribution": "10.00",
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


def _user_wealth(amount: str):
    return {
        "source": "USER_PROVIDED_SCENARIO",
        "amount": amount,
        "observed_at": "2026-09-20T09:30:00-03:00",
    }


def _scenario(scenario_id: str, amount: str, **overrides):
    payload = {
        "scenario_id": scenario_id,
        "initial_wealth": _user_wealth(amount),
        "assumptions": _assumptions_payload(),
        "label": None,
        "archetype": None,
    }
    payload.update(overrides)
    return payload


def _payload(scenarios=None, **overrides):
    resolved_scenarios = scenarios or [
        _scenario("reference", "100.00"),
        _scenario("candidate", "200.00"),
    ]
    payload = {
        "scenarios": resolved_scenarios,
        "reference_scenario_id": resolved_scenarios[0]["scenario_id"],
        "target_amount": None,
        "target_value_basis": None,
    }
    payload.update(overrides)
    return payload


def _install_reader(goals: dict[UUID, GoalPlanningFact]):
    reader = _GoalReader(goals)
    app.dependency_overrides[planning_router.get_planning_goal_read_query] = (
        lambda: reader
    )
    return reader


def _install_engine(engine=None):
    engine = _ComparisonSpy(engine)
    app.dependency_overrides[planning_router.get_scenario_comparison_engine] = (
        lambda: engine
    )
    return engine


def test_no_target_http_oracle_preserves_input_order_reference_and_certified_deltas(
    _authenticated_client,
):
    scenarios = [
        _scenario("c", "100.00", assumptions=_assumptions_payload(scenario_monthly_contribution="10.00")),
        _scenario("a", "200.00", assumptions=_assumptions_payload(scenario_monthly_contribution="20.00"), label="A", archetype="BASE"),
        _scenario("b", "300.00", assumptions=_assumptions_payload(scenario_monthly_contribution="30.00"), archetype="CONSERVATIVE"),
    ]
    spy = _install_engine()

    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(scenarios, reference_scenario_id="b"),
    )

    assert response.status_code == 200
    body = response.json()
    assert spy.calls == 1
    assert [entry["scenario_id"] for entry in body["entries"]] == ["c", "a", "b"]
    assert body["reference_scenario_id"] == "b"
    assert body["entries"][0]["projection_result"]["final_wealth"] == "120.00"
    assert body["entries"][1]["projection_result"]["final_wealth"] == "240.00"
    assert body["entries"][2]["projection_result"]["final_wealth"] == "360.00"
    assert body["entries"][0]["final_wealth_delta"] == "-240.00"
    assert body["entries"][1]["total_contributions_delta"] == "-20.00"
    assert body["entries"][2]["final_wealth_delta"] == "0.00"
    assert body["entries"][2]["total_projected_growth_delta"] == "0.00"
    assert body["entries"][0]["months_saved_or_lost"] is None
    assert body["entries"][1]["archetype"] == "BASE"


def test_target_http_oracle_preserves_month_delta_direction_and_nested_results(
    _authenticated_client,
):
    scenarios = [
        _scenario("slow", "0.00", assumptions=_assumptions_payload(scenario_monthly_contribution="100.00", horizon_months=3)),
        _scenario("fast", "0.00", assumptions=_assumptions_payload(scenario_monthly_contribution="200.00", horizon_months=3)),
    ]
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(scenarios, target_amount="200.00", target_value_basis="NOMINAL"),
    )

    assert response.status_code == 200
    slow, fast = response.json()["entries"]
    assert slow["target_achievement_result"]["status"] == "ACHIEVED"
    assert slow["target_achievement_result"]["months_required"] == 2
    assert fast["target_achievement_result"]["months_required"] == 1
    assert fast["months_saved_or_lost"] == 1
    assert fast["final_wealth_delta"] == "300.00"


def test_already_and_nonachievement_statuses_are_valid_comparison_outputs(
    _authenticated_client,
):
    already = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(
            [
                _scenario("reference", "100.00"),
                _scenario(
                    "later",
                    "0.00",
                    assumptions=_assumptions_payload(
                        scenario_monthly_contribution="100.00"
                    ),
                ),
            ],
            target_amount="100.00",
            target_value_basis="NOMINAL",
        ),
    )
    not_reached = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(
            [
                _scenario("reference", "0.00", assumptions=_assumptions_payload(scenario_monthly_contribution="0.00")),
                _scenario("candidate", "0.00", assumptions=_assumptions_payload(scenario_monthly_contribution="10.00")),
            ],
            target_amount="10000.00",
            target_value_basis="NOMINAL",
        ),
    )

    assert already.status_code == not_reached.status_code == 200
    assert already.json()["entries"][0]["target_achievement_result"]["status"] == "ALREADY_ACHIEVED"
    assert already.json()["entries"][0]["months_saved_or_lost"] == 0
    assert already.json()["entries"][1]["months_saved_or_lost"] == -1
    assert not_reached.json()["entries"][0]["target_achievement_result"]["status"] == "UNREACHABLE"
    assert all(entry["months_saved_or_lost"] is None for entry in not_reached.json()["entries"])


@pytest.mark.parametrize(
    "payload_overrides",
    [
        {"reference_scenario_id": "missing"},
        {"scenarios": [_scenario("same", "1.00"), _scenario("same", "2.00")]},
        {"scenarios": [_scenario("a", "1.00"), _scenario("b", "2.00", assumptions=_assumptions_payload(as_of_date="2026-09-21"))]},
        {"scenarios": [_scenario("a", "1.00"), _scenario("b", "2.00", assumptions=_assumptions_payload(output_mode="REAL", expected_return_rate="0.04", return_type="REAL"))]},
        {"target_amount": "100.00", "target_value_basis": None},
        {"target_amount": None, "target_value_basis": "NOMINAL"},
        {"target_amount": "100.00", "target_value_basis": "REAL"},
    ],
)
def test_domain_comparison_validation_is_422_without_financial_execution(
    _authenticated_client,
    payload_overrides,
):
    spy = _install_engine()
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare", json=_payload(**payload_overrides)
    )

    assert response.status_code == 422
    assert spy.calls == 1


def test_comparability_uses_resolved_horizon_and_does_not_require_return_type_equality(
    _authenticated_client,
):
    equivalent = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(
            [
                _scenario("months", "100.00", assumptions=_assumptions_payload(horizon_months=12)),
                _scenario("date", "100.00", assumptions=_assumptions_payload(horizon_months=None, target_date="2027-09-01")),
            ]
        ),
    )
    return_type_variation = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(
            [
                _scenario("nominal", "100.00", assumptions=_assumptions_payload(expected_return_rate="0.08", output_mode="REAL", inflation_rate="0.04", return_type="NOMINAL")),
                _scenario("real", "100.00", assumptions=_assumptions_payload(expected_return_rate="0.04", output_mode="REAL", inflation_rate=None, return_type="REAL")),
            ]
        ),
    )
    mismatch = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload([
            _scenario("a", "100.00"),
            _scenario("b", "100.00", assumptions=_assumptions_payload(horizon_months=3)),
        ]),
    )

    assert equivalent.status_code == 200
    assert return_type_variation.status_code == 200
    assert mismatch.status_code == 422


def test_goal_sources_are_server_resolved_atomically_and_preserve_provenance(
    _authenticated_client,
):
    reader = _install_reader({GOAL_A_ID: _goal(GOAL_A_ID, Decimal("123.45")), GOAL_B_ID: _goal(GOAL_B_ID, Decimal("456.78"))})
    spy = _install_engine()
    scenarios = [
        _scenario("goal-a", "0.00", initial_wealth={"source": "GOAL_CURRENT_AMOUNT", "goal_id": str(GOAL_A_ID)}),
        _scenario("goal-b", "0.00", initial_wealth={"source": "GOAL_CURRENT_AMOUNT", "goal_id": str(GOAL_B_ID)}),
    ]
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare", json=_payload(scenarios)
    )

    assert response.status_code == 200
    assert spy.calls == 1
    assert reader.calls == [(GOAL_A_ID, USER_ID), (GOAL_B_ID, USER_ID)]
    assert response.json()["entries"][0]["initial_wealth_fact"]["amount"] == "123.45"
    assert response.json()["entries"][1]["initial_wealth_fact"]["provenance"]["goal_id"] == str(GOAL_B_ID)


@pytest.mark.parametrize(
    "reader_goals, goal_id, expected_status, expected_detail",
    [
        ({}, GOAL_A_ID, 404, "Goal not found."),
        ({GOAL_A_ID: _goal(GOAL_A_ID, Decimal("1.00"))}, OTHER_GOAL_ID, 404, "Goal not found."),
        ({GOAL_A_ID: _goal(GOAL_A_ID, None)}, GOAL_A_ID, 422, "selected Goal current amount is unavailable"),
    ],
)
def test_goal_source_failures_are_atomic_and_non_enumerating(
    _authenticated_client,
    reader_goals,
    goal_id,
    expected_status,
    expected_detail,
):
    _install_reader(reader_goals)
    spy = _install_engine()
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload([
            _scenario("user", "1.00"),
            _scenario("goal", "1.00", initial_wealth={"source": "GOAL_CURRENT_AMOUNT", "goal_id": str(goal_id)}),
        ]),
    )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
    assert spy.calls == 0


@pytest.mark.parametrize(
    "selector",
    [
        {"source": "GOAL_CURRENT_AMOUNT", "goal_id": str(GOAL_A_ID), "amount": "999.00"},
        {"source": "GOAL_CURRENT_AMOUNT", "goal_id": str(GOAL_A_ID), "provenance": {"goal_id": str(GOAL_A_ID)}},
    ],
)
def test_http_rejects_forged_goal_facts(_authenticated_client, selector):
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload([_scenario("a", "1.00"), _scenario("b", "2.00", initial_wealth=selector)]),
    )

    assert response.status_code == 422


def test_http_rejects_financial_json_number_preserves_scale_and_maps_arithmetic_error(
    _authenticated_client,
):
    number = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload([_scenario("a", "1.00"), _scenario("b", "2.00", assumptions=_assumptions_payload(expected_return_rate=0.08))]),
    )
    scale = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload([_scenario("a", "1.000"), _scenario("b", "2.00")]),
    )

    class _ExplodingEngine:
        def compare(self, *args):
            raise ArithmeticError("private scenario-comparison detail")

    app.dependency_overrides[planning_router.get_scenario_comparison_engine] = lambda: _ExplodingEngine()
    exploding = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare", json=_payload()
    )

    assert number.status_code == 422
    assert scale.status_code == 422
    assert "at most two decimal places" in scale.json()["detail"]
    assert exploding.status_code == 500
    assert exploding.json() == {"detail": "Planning calculation could not be completed."}


def test_large_decimal_is_preserved_as_a_json_string_without_float_normalization(
    _authenticated_client,
):
    amount = "999999999999999999999999999.00"
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload([
            _scenario("reference", amount, assumptions=_assumptions_payload(scenario_monthly_contribution="0.00", horizon_months=1)),
            _scenario("candidate", "1000000000000000000000000000.00", assumptions=_assumptions_payload(scenario_monthly_contribution="0.00", horizon_months=1)),
        ]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["entries"][0]["projection_result"]["final_wealth"] == amount
    assert body["entries"][1]["final_wealth_delta"] == "1.00"
    assert isinstance(body["entries"][1]["final_wealth_delta"], str)


def test_endpoint_requires_authentication_and_openapi_exposes_only_approved_operations():
    with TestClient(app) as client:
        response = client.post("/api/v1/planning/scenarios/compare", json=_payload())
    assert response.status_code == 401

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
    request_schema = schema["components"]["schemas"]["ScenarioComparisonRequestDTO"]
    assert request_schema["properties"]["target_amount"]["anyOf"][0]["type"] == "string"
    scenario_schema = schema["components"]["schemas"]["ScenarioDefinitionRequestDTO"]
    assert "INVESTMENT_PORTFOLIO_SNAPSHOT" in str(scenario_schema)


def test_domain_prevalidation_aborts_before_any_financial_subengine_execution(
    _authenticated_client,
):
    class _ProjectionSpy:
        def __init__(self):
            self.calls = 0

        def project(self, *_args):
            self.calls += 1
            raise AssertionError("domain prevalidation must precede projection")

    class _TargetSpy:
        def __init__(self):
            self.calls = 0

        def solve(self, *_args):
            self.calls += 1
            raise AssertionError("domain prevalidation must precede target solving")

    projection = _ProjectionSpy()
    target = _TargetSpy()
    comparison = ScenarioComparisonEngine(projection, target)
    spy = _install_engine(comparison)

    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(
            [
                _scenario("duplicate", "1.00"),
                _scenario("duplicate", "2.00"),
            ]
        ),
    )

    assert response.status_code == 422
    assert spy.calls == 1
    assert projection.calls == 0
    assert target.calls == 0


@pytest.mark.parametrize(
    ("status", "goal_type"),
    [
        (GoalStatus.ACHIEVED, GoalType.CUSTOM),
        (GoalStatus.PAUSED, GoalType.CUSTOM),
        (GoalStatus.CANCELLED, GoalType.CUSTOM),
        (GoalStatus.ACTIVE, GoalType.RETIREMENT),
        (GoalStatus.ACTIVE, GoalType.FINANCIAL_INDEPENDENCE),
        (GoalStatus.ACTIVE, GoalType.DIVIDEND_INCOME),
    ],
)
def test_goal_current_amount_remains_available_without_goal_planning_applicability(
    _authenticated_client,
    status,
    goal_type,
):
    _install_reader(
        {
            GOAL_A_ID: _goal(
                GOAL_A_ID,
                Decimal("123.45"),
                status=status,
                goal_type=goal_type,
            )
        }
    )
    spy = _install_engine()
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(
            [
                _scenario(
                    "goal",
                    "0.00",
                    initial_wealth={
                        "source": "GOAL_CURRENT_AMOUNT",
                        "goal_id": str(GOAL_A_ID),
                    },
                ),
                _scenario("user", "10.00"),
            ]
        ),
    )

    assert response.status_code == 200
    assert spy.calls == 1
    assert response.json()["entries"][0]["initial_wealth_fact"]["amount"] == "123.45"


def test_mapper_copies_domain_certified_deltas_without_recalculation(
    _authenticated_client,
):
    spy = _install_engine()
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(),
    )

    assert response.status_code == 200
    assert spy.result is not None
    controlled_entry = replace(
        spy.result.entries[1],
        final_wealth_delta=Decimal("987.65"),
        total_contributions_delta=Decimal("-123.45"),
        total_projected_growth_delta=Decimal("0.0100"),
        months_saved_or_lost=777,
    )
    controlled_result = replace(
        spy.result,
        entries=(spy.result.entries[0], controlled_entry),
    )

    mapped = map_scenario_comparison_result(controlled_result)

    assert mapped.entries[1].final_wealth_delta == "987.65"
    assert mapped.entries[1].total_contributions_delta == "-123.45"
    assert mapped.entries[1].total_projected_growth_delta == "0.0100"
    assert mapped.entries[1].months_saved_or_lost == 777


@pytest.mark.parametrize(
    "payload_override",
    [
        {"score": 1},
        {"rank": 1},
        {"winner": "candidate"},
        {"recommendation": "candidate"},
    ],
)
def test_http_rejects_noncontractual_ranking_and_recommendation_fields(
    _authenticated_client,
    payload_override,
):
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(**payload_override),
    )

    assert response.status_code == 422


@pytest.mark.parametrize("target_amount", [1000, 0, -1, "NaN", "Infinity", "1e3"])
def test_target_amount_requires_approved_decimal_string_and_domain_money_contract(
    _authenticated_client,
    target_amount,
):
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(
            target_amount=target_amount,
            target_value_basis="NOMINAL",
        ),
    )

    assert response.status_code == 422


@pytest.mark.parametrize("reference_scenario_id", ["first", "middle", "last"])
def test_explicit_reference_accepts_first_middle_or_last_input_position(
    _authenticated_client,
    reference_scenario_id,
):
    scenarios = [
        _scenario("first", "100.00", archetype="BASE"),
        _scenario("middle", "200.00", archetype="OPTIMISTIC"),
        _scenario("last", "300.00", archetype="CONSERVATIVE"),
    ]
    response = _authenticated_client.post(
        "/api/v1/planning/scenarios/compare",
        json=_payload(scenarios, reference_scenario_id=reference_scenario_id),
    )

    assert response.status_code == 200
    entries = response.json()["entries"]
    reference_index = [entry["scenario_id"] for entry in entries].index(
        reference_scenario_id
    )
    assert response.json()["reference_scenario_id"] == reference_scenario_id
    assert [entry["scenario_id"] for entry in entries] == [
        "first",
        "middle",
        "last",
    ]
    assert entries[reference_index]["final_wealth_delta"] == "0.00"
