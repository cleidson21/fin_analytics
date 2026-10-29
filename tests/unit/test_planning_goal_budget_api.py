"""R6.5 JSON contract, ownership, certified reuse and read-only integration."""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.api.dependencies.auth import get_current_user
from backend.api.planning_mapping import map_scenario_comparison_result
from backend.api.routers import planning as planning_router
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.database.base import Base
from backend.database.session import get_db
from backend.domain.enums.user_role import UserRole
from backend.domains.planning.readers import (
    PlanningGoalReadQuery, PlanningHealthReadAdapter, PlanningPortfolioReadQuery,
)
from backend.domains.planning.required_contribution_solver import RequiredContributionSolver
from backend.domains.planning.scenario_comparison import ScenarioComparisonEngine
from backend.infrastructure.persistence.models.goal import GoalModel
from backend.infrastructure.persistence.models.user import UserModel
from backend.main import app

from tests.unit.test_goal_budget import CountingEngine, goal


URL = "/api/v1/planning/goals/budget-preview"
OWNER = UUID(int=901)
OTHER = UUID(int=902)


def payload(ids=(UUID(int=1),), a=None, b=None, **overrides):
    a = a if a is not None else ["100"] * len(ids)
    b = b if b is not None else a
    result = {
        "goal_ids": [str(identifier) for identifier in ids],
        "monthly_budget": "1000.00",
        "target_value_basis": "NOMINAL",
        "assumptions": {
            "as_of_date": "2026-10-28", "expected_return_rate": "0",
            "return_type": "NOMINAL", "output_mode": "NOMINAL", "horizon_months": 12,
            "rate_basis": "EFFECTIVE_ANNUAL", "contribution_timing": "END_OF_MONTH",
        },
        "scenarios": [
            {"scenario_id": scenario, "allocations": [
                {"goal_id": str(identifier), "scenario_monthly_contribution": amount}
                for identifier, amount in zip(ids, amounts)
            ]}
            for scenario, amounts in (("A", a), ("B", b))
        ],
    }
    result.update(overrides)
    return result


def user(identifier=OWNER):
    return UserResponseDTO(
        id=identifier, email=f"{identifier}@example.test", name="Budget user",
        role=UserRole.VIEWER, is_active=True, is_verified=True,
        created_at=datetime(2026, 1, 1), last_login_at=None,
    )


def forbidden(*_args, **_kwargs):
    raise AssertionError("R6.5 must not access this boundary")


class NoWriteSession:
    add = add_all = delete = execute = flush = commit = forbidden


class Reader:
    def __init__(self, goals):
        self.goals = tuple(goals)
        self.calls = []

    def get_goals_by_ids(self, db, ids, owner):
        self.calls.append((db, tuple(ids), owner))
        # Deliberately return a different order to exercise route normalization.
        return tuple(g for g in reversed(self.goals) if g.goal_id in ids and g.user_id == owner)

    current_amount_as_initial_wealth = staticmethod(
        PlanningGoalReadQuery.current_amount_as_initial_wealth
    )


@pytest.fixture(autouse=True)
def boundaries(monkeypatch):
    app.dependency_overrides.clear()
    app.openapi_schema = None
    monkeypatch.setattr(RequiredContributionSolver, "solve", forbidden)
    monkeypatch.setattr(PlanningPortfolioReadQuery, "get_latest_investment_wealth", forbidden)
    monkeypatch.setattr(PlanningHealthReadAdapter, "get_monthly_facts", forbidden)
    app.dependency_overrides[planning_router.get_planning_portfolio_source_resolver] = forbidden
    yield
    app.dependency_overrides.clear()
    app.openapi_schema = None


def client_for(reader=None, owner=OWNER, session=None, engine=None):
    session = session if session is not None else NoWriteSession()
    app.dependency_overrides[get_current_user] = lambda: user(owner)
    app.dependency_overrides[get_db] = lambda: session
    if reader is not None:
        app.dependency_overrides[planning_router.get_planning_goal_read_query] = lambda: reader
    if engine is not None:
        app.dependency_overrides[planning_router.get_scenario_comparison_engine] = lambda: engine
    return TestClient(app), session


def test_complete_shape_order_provenance_and_certified_nested_parity():
    goals = (goal(2, target_amount=Decimal("600")), goal(1), goal(3, current_amount=None))
    before = deepcopy(goals)
    reader = Reader(goals)
    engine = CountingEngine()
    client, session = client_for(reader, engine=engine)
    request = payload(tuple(g.goal_id for g in goals), ["50", "100", "10"], ["100", "50", "10"])
    request["scenarios"][1]["allocations"].reverse()
    with client:
        response = client.post(URL, json=request)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"monthly_budget", "assumptions", "target_value_basis", "reference_scenario_id", "scenarios", "results"}
    assert body["monthly_budget"] == "1000.00"
    assert body["target_value_basis"] == "NOMINAL"
    assert body["reference_scenario_id"] == "A"
    assert body["assumptions"] == {**request["assumptions"], "inflation_rate": None}
    for scenario in body["scenarios"]:
        assert set(scenario) == {"scenario_id", "allocations", "allocated_total", "unallocated_amount", "exceeded_amount"}
        assert scenario["allocated_total"] == "160"
        assert scenario["unallocated_amount"] == "840.00"
        assert Decimal(scenario["exceeded_amount"]) == 0
        assert [a["goal_id"] for a in scenario["allocations"]] == request["goal_ids"]
    assert [r["goal_id"] for r in body["results"]] == request["goal_ids"]
    assert reader.calls == [(session, tuple(g.goal_id for g in goals), OWNER)]
    assert len(engine.calls) == 2
    for item, call in zip(body["results"], engine.calls):
        expected = map_scenario_comparison_result(ScenarioComparisonEngine().compare(**call))
        assert item["comparison"] == expected.model_dump(mode="json")
        assert set(item) == {"goal_id", "name", "target_amount", "current_amount", "source_type", "goal_updated_at", "initial_wealth_fact", "availability", "impediment_code", "comparison"}
        assert item["source_type"] == "USER_GOVERNED_GOAL"
        fact = item["initial_wealth_fact"]
        assert fact["source"] == "GOAL_CURRENT_AMOUNT" and fact["scope"] == "GOAL"
        assert fact["provenance"]["goal_id"] == item["goal_id"]
        assert "source_table" not in fact["provenance"]
        assert "user_id" not in item
    unavailable = body["results"][2]
    assert unavailable["current_amount"] is None
    assert unavailable["initial_wealth_fact"] is None
    assert unavailable["comparison"] is None
    assert unavailable["impediment_code"] == "CURRENT_AMOUNT_MISSING"
    assert goals == before


@pytest.mark.parametrize("target,current,code,fact_available", [
    (None, "0", "TARGET_MISSING", True),
    ("0", "0", "TARGET_NONPOSITIVE", True),
    ("-1", "-2", "TARGET_NONPOSITIVE", False),
    ("100", None, "CURRENT_AMOUNT_MISSING", False),
    ("100", "-0.01", "CURRENT_AMOUNT_NEGATIVE", False),
])
def test_unavailable_items_preserve_facts_and_budget(target, current, code, fact_available):
    chosen = goal(target_amount=None if target is None else Decimal(target),
                  current_amount=None if current is None else Decimal(current))
    engine = CountingEngine()
    client, _ = client_for(Reader((chosen,)), engine=engine)
    with client:
        response = client.post(URL, json=payload(monthly_budget="0"))
    assert response.status_code == 200
    body = response.json()
    item = body["results"][0]
    assert item["availability"] == "UNAVAILABLE"
    assert item["impediment_code"] == code and item["comparison"] is None
    assert (item["initial_wealth_fact"] is not None) == fact_available
    assert engine.calls == []
    assert body["scenarios"][0]["exceeded_amount"] == "100"


@pytest.mark.parametrize("budget,contribution,unallocated,exceeded", [
    ("100", "0", "100", "0"), ("0", "0", "0", "0"),
    ("0", "0.01", "0", "0.01"), ("0.30", "0.30", "0", "0"),
    ("0.31", "0.30", "0.01", "0"), ("0.29", "0.30", "0", "0.01"),
])
def test_http_budget_limits_allow_excess(budget, contribution, unallocated, exceeded):
    client, _ = client_for(Reader((goal(),)))
    with client:
        response = client.post(URL, json=payload(a=[contribution], monthly_budget=budget))
    assert response.status_code == 200
    for summary in response.json()["scenarios"]:
        assert Decimal(summary["unallocated_amount"]) == Decimal(unallocated)
        assert Decimal(summary["exceeded_amount"]) == Decimal(exceeded)


def test_numeric_equal_totals_keep_each_allocation_scale():
    client, _ = client_for(Reader((goal(),)))
    with client:
        response = client.post(URL, json=payload(a=["100"], b=["100.00"]))
    assert response.status_code == 200
    a, b = response.json()["scenarios"]
    assert a["allocations"][0]["scenario_monthly_contribution"] == "100"
    assert b["allocations"][0]["scenario_monthly_contribution"] == "100.00"
    assert Decimal(a["allocated_total"]) == Decimal(b["allocated_total"])


@pytest.mark.parametrize("basis", ["REAL", None])
def test_target_basis_is_explicitly_nominal(basis):
    reader = Reader((goal(),))
    client, _ = client_for(reader)
    with client:
        assert client.post(URL, json=payload(target_value_basis=basis)).status_code == 422
    assert reader.calls == []


@pytest.mark.parametrize("rate", ["-0.05", "100"])
def test_valid_rate_domain_has_no_arbitrary_positive_ceiling(rate):
    client, _ = client_for(Reader((goal(),)))
    request = payload()
    request["assumptions"].update(expected_return_rate=rate, horizon_months=1)
    with client:
        response = client.post(URL, json=request)
    assert response.status_code == 200
    assert response.json()["assumptions"]["expected_return_rate"] == rate


@pytest.mark.parametrize("foreign_ids", [(UUID(int=2),), (UUID(int=1), UUID(int=2))])
def test_foreign_and_missing_are_same_atomic_404_without_engine(foreign_ids):
    engine = CountingEngine()
    reader = Reader((goal(1), goal(2, user_id=OTHER)))
    client, _ = client_for(reader, engine=engine)
    with client:
        foreign = client.post(URL, json=payload(foreign_ids))
        missing = client.post(URL, json=payload(tuple(UUID(int=999) if i.int == 2 else i for i in foreign_ids)))
    assert missing.status_code == foreign.status_code == 404
    assert missing.json() == foreign.json() == {"detail": "One or more Goals were not found."}
    assert engine.calls == []


def test_two_authenticated_identities_isolate_reads():
    reader = Reader((goal(1), goal(2, user_id=OTHER)))
    for owner, identifier in ((OWNER, UUID(int=1)), (OTHER, UUID(int=2))):
        client, _ = client_for(reader, owner=owner)
        with client:
            assert client.post(URL, json=payload((identifier,))).status_code == 200
            assert client.post(URL, json=payload((UUID(int=3 - identifier.int),))).status_code == 404
    assert [call[2] for call in reader.calls] == [OWNER, OWNER, OTHER, OTHER]


def test_authentication_is_required():
    app.dependency_overrides[get_db] = lambda: NoWriteSession()
    with TestClient(app) as client:
        response = client.post(URL, json=payload())
    assert response.status_code == 401


@pytest.mark.parametrize("field", ["monthly_budget", "scenario_monthly_contribution"])
@pytest.mark.parametrize("value", [None, -1, 0, 0.1, True, "-0.01", "0.001", "1.000", "NaN", "Infinity", "1e2", "", " 1"])
def test_strict_money_validation_precedes_reads(field, value):
    reader = Reader((goal(),))
    client, _ = client_for(reader)
    request = payload()
    if field == "monthly_budget":
        request[field] = value
    else:
        request["scenarios"][0]["allocations"][0][field] = value
    with client:
        response = client.post(URL, json=request)
    assert response.status_code == 422
    assert reader.calls == []


@pytest.mark.parametrize("location,field", [
    ("root", "monthly_budget"), ("root", "goal_ids"), ("root", "assumptions"),
    ("root", "target_value_basis"), ("root", "scenarios"),
    ("assumptions", "expected_return_rate"), ("assumptions", "as_of_date"),
    ("assumptions", "horizon_months"), ("assumptions", "rate_basis"),
    ("assumptions", "contribution_timing"), ("assumptions", "return_type"),
    ("assumptions", "output_mode"),
    ("allocation", "scenario_monthly_contribution"), ("allocation", "goal_id"),
])
def test_required_fields_are_not_defaulted(location, field):
    reader = Reader((goal(),))
    client, _ = client_for(reader)
    request = payload()
    container = {"root": request, "assumptions": request["assumptions"],
                 "allocation": request["scenarios"][0]["allocations"][0]}[location]
    del container[field]
    with client:
        assert client.post(URL, json=request).status_code == 422
    assert reader.calls == []


@pytest.mark.parametrize("overrides", [
    {"horizon_months": 0}, {"horizon_months": 1201}, {"horizon_months": "12"},
    {"horizon_months": True}, {"expected_return_rate": "-1"},
    {"expected_return_rate": "-1.01"}, {"expected_return_rate": 0},
    {"expected_return_rate": "1e-2"}, {"return_type": "REAL"}, {"output_mode": "REAL"},
    {"inflation_rate": None}, {"inflation_rate": "0.04"}, {"target_date": None},
    {"as_of_date": "2026-10-28T00:00:00"}, {"as_of_date": "2026-02-30"},
    {"rate_basis": "MONTHLY"}, {"contribution_timing": "START_OF_MONTH"},
])
def test_premises_are_explicit_nominal_and_cannot_be_overridden(overrides):
    reader = Reader((goal(),))
    client, _ = client_for(reader)
    request = payload()
    request["assumptions"].update(overrides)
    with client:
        assert client.post(URL, json=request).status_code == 422
    assert reader.calls == []


@pytest.mark.parametrize("level", ["root", "assumptions", "scenario", "allocation"])
def test_unknown_fields_and_scenario_overrides_are_forbidden(level):
    reader = Reader((goal(),))
    client, _ = client_for(reader)
    request = payload()
    container = {"root": request, "assumptions": request["assumptions"],
                 "scenario": request["scenarios"][0],
                 "allocation": request["scenarios"][0]["allocations"][0]}[level]
    container["user_id" if level == "root" else "monthly_budget"] = "123"
    with client:
        assert client.post(URL, json=request).status_code == 422
    assert reader.calls == []


def invalid_collections():
    cases = []
    for ids in ((), ("bad-uuid",), (UUID(int=1), UUID(int=1)), tuple(UUID(int=i) for i in range(1, 22))):
        cases.append(payload(ids))
    for count in (0, 1, 3):
        request = payload()
        request["scenarios"] = (request["scenarios"] * 2)[:count]
        cases.append(request)
    request = payload()
    request["scenarios"].reverse()
    cases.append(request)
    for scenario_id in ("A", "C"):
        request = payload()
        request["scenarios"][1]["scenario_id"] = scenario_id
        cases.append(request)
    for mode in ("missing", "extra", "duplicate", "wrong", "invalid"):
        request = payload((UUID(int=1), UUID(int=2)))
        allocations = request["scenarios"][0]["allocations"]
        if mode == "missing":
            allocations.pop()
        elif mode == "extra":
            allocations.append({"goal_id": str(UUID(int=3)), "scenario_monthly_contribution": "1"})
        elif mode == "duplicate":
            allocations[1]["goal_id"] = allocations[0]["goal_id"]
        else:
            allocations[1]["goal_id"] = "bad" if mode == "invalid" else str(UUID(int=3))
        cases.append(request)
    return cases


@pytest.mark.parametrize("invalid_payload", invalid_collections())
def test_invalid_selection_and_coverage_fail_before_sql(invalid_payload):
    reader = Reader((goal(),))
    engine = CountingEngine()
    client, _ = client_for(reader, engine=engine)
    with client:
        assert client.post(URL, json=invalid_payload).status_code == 422
    assert reader.calls == engine.calls == []


@pytest.mark.parametrize("a,b", [
    (["100"], ["100.01"]),
    (["100.001"], ["100.002"]),
    (["999999999999999999999999999999.99", "0.01"],
     ["999999999999999999999999999999.99", "0.02"]),
])
def test_unequal_totals_are_rejected_exactly_without_reads_or_private_detail(a, b):
    reader = Reader(())
    engine = CountingEngine()
    client, _ = client_for(reader, engine=engine)
    with client:
        response = client.post(URL, json=payload(tuple(UUID(int=i + 1) for i in range(len(a))), a, b))
    assert response.status_code == 422
    assert reader.calls == engine.calls == []
    if len(a) == 2 or a == ["100"]:
        assert response.json() == {"detail": "Scenario allocated totals must be exactly equal."}


def test_large_money_and_rate_precision_have_no_float_conversion():
    huge = "99999999999999999999999999999999.99"
    reader = Reader((goal(), goal(2)))
    client, _ = client_for(reader)
    request = payload((UUID(int=1), UUID(int=2)), [huge, "0.01"], ["0.01", huge], monthly_budget="0")
    request["assumptions"]["horizon_months"] = 1
    request["assumptions"]["expected_return_rate"] = "0.05000000000000000000000000001"
    with client:
        response = client.post(URL, json=request)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scenarios"][0]["allocated_total"] == "100000000000000000000000000000000.00"
    assert body["assumptions"]["expected_return_rate"] == request["assumptions"]["expected_return_rate"]
    assert body["scenarios"][0]["exceeded_amount"] == "100000000000000000000000000000000.00"


@pytest.mark.parametrize("failure", [RuntimeError, TypeError, ValueError, ArithmeticError])
@pytest.mark.parametrize("boundary", ["reader", "engine", "mapper"])
def test_internal_failures_are_generic_including_broken_type_invariants(failure, boundary, monkeypatch):
    reader = Reader((goal(),))
    engine = CountingEngine()
    def explode(*args, **kwargs):
        raise failure("private SQL secret amount=987654.32")
    if boundary == "reader":
        monkeypatch.setattr(reader, "get_goals_by_ids", explode)
    elif boundary == "engine":
        monkeypatch.setattr(engine, "compare", explode)
    else:
        monkeypatch.setattr(planning_router, "map_goal_budget_preview", explode)
    client, _ = client_for(reader, engine=engine)
    with client:
        response = client.post(URL, json=payload())
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Planning error."}


def test_complete_id_correspondence_and_owner_guard_precede_engine(monkeypatch):
    engine = CountingEngine()
    reader = Reader(())
    client, _ = client_for(reader, engine=engine)
    for returned in ((goal(2),), (goal(1, user_id=OTHER),), (goal(), goal())):
        monkeypatch.setattr(reader, "get_goals_by_ids", lambda *args: returned)
        with client:
            assert client.post(URL, json=payload()).status_code == 404
    assert engine.calls == []


def test_real_sql_batch_is_owner_filtered_read_only_and_has_no_n_plus_one(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[UserModel.__table__, GoalModel.__table__])
    with Session(engine, expire_on_commit=False, autoflush=False) as session:
        models = []
        for i in range(1, 22):
            values = asdict(goal(i, user_id=OTHER if i == 21 else OWNER))
            values["id"] = values.pop("goal_id")
            values["monthly_contribution"] = values.pop("goal_planned_monthly_contribution")
            models.append(GoalModel(**values))
        session.add_all(models)
        session.commit()
        before = [tuple(row) for row in session.execute(select(GoalModel.__table__)).all()]
        statements = []
        @event.listens_for(engine, "before_cursor_execute")
        def capture(_conn, _cursor, statement, parameters, _context, _many):
            statements.append((statement, parameters))
        for method in ("add", "add_all", "delete", "flush", "commit"):
            monkeypatch.setattr(session, method, forbidden)
        client, _ = client_for(session=session)
        with client:
            request = payload(tuple(UUID(int=i) for i in range(20, 0, -1)))
            request["assumptions"]["horizon_months"] = 1
            response = client.post(URL, json=request)
            assert response.status_code == 200, response.text
            assert [item["goal_id"] for item in response.json()["results"]] == request["goal_ids"]
            assert len(statements) == 1
            sql, parameters = statements[0]
            assert sql.lstrip().upper().startswith("SELECT")
            assert "goals.user_id =" in sql and "goals.id IN" in sql
            assert OWNER.hex in parameters and OTHER.hex not in parameters
            statements.clear()
            assert client.post(URL, json=payload((UUID(int=21),))).status_code == 404
            assert len(statements) == 1
        event.remove(engine, "before_cursor_execute", capture)
        after = [tuple(row) for row in session.execute(select(GoalModel.__table__)).all()]
        assert before == after
        assert not session.new and not session.dirty and not session.deleted
    engine.dispose()


def test_openapi_exact_addition_and_strict_nested_schema():
    schema = app.openapi()
    paths = schema["paths"]
    expected = {
        "/api/v1/planning/projection": "post",
        "/api/v1/planning/target-achievement": "post",
        "/api/v1/planning/required-contribution": "post",
        "/api/v1/planning/goals/{goal_id}/projection": "post",
        "/api/v1/planning/scenarios/compare": "post",
        "/api/v1/planning/goals/{goal_id}/context": "get",
        "/api/v1/planning/goals/{goal_id}/progress": "get",
        "/api/v1/planning/goals/overview": "get",
        "/api/v1/planning/goals/batch-contribution-preview": "post",
        URL: "post",
    }
    assert {p: next(iter(v)) for p, v in paths.items() if p.startswith("/api/v1/planning/")} == expected
    assert paths[URL]["post"]["security"] == [{"OAuth2PasswordBearer": []}]
    assert not paths[URL]["post"].get("parameters")
    schemas = schema["components"]["schemas"]
    for name in ("GoalBudgetPreviewRequestDTO", "GoalBudgetScenarioRequestDTO", "GoalBudgetAllocationRequestDTO", "GoalBudgetAssumptionsRequestDTO"):
        assert schemas[name]["additionalProperties"] is False
    request = schemas["GoalBudgetPreviewRequestDTO"]
    assert request["properties"]["monthly_budget"]["type"] == "string"
    assert request["properties"]["goal_ids"]["maxItems"] == 20
    assert request["properties"]["scenarios"]["minItems"] == request["properties"]["scenarios"]["maxItems"] == 2
    common = schemas["GoalBudgetAssumptionsRequestDTO"]
    assert "inflation_rate" not in common["properties"] and "target_date" not in common["properties"]
    assert common["properties"]["return_type"]["const"] == "NOMINAL"
    assert common["properties"]["horizon_months"]["maximum"] == 1200
    assert schemas["GoalBudgetItemResponseDTO"]["properties"]["comparison"]["anyOf"][0]["$ref"].endswith("ScenarioComparisonResponseDTO")
