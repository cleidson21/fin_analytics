from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies.auth import get_current_user
from backend.api.routers import fire as fire_router
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.exceptions.planning_portfolio_source_error import (
    PlanningPortfolioSourceUnavailableError,
)
from backend.application.services.fire_analysis_service import (
    FireAnalysisAssumptions,
    FireAnalysisResult,
    FireAnalysisType,
)
from backend.database.session import get_db
from backend.domain.enums.user_role import UserRole
from backend.domains.fire import FireSummaryCalculator, FireSummaryInput
from backend.domains.planning.assumptions import (
    ContributionTiming,
    OutputMode,
    ProjectionAssumptions,
    RateBasis,
    ReturnType,
)
from backend.domains.planning.facts import (
    InitialWealthFact,
    InitialWealthScope,
    InitialWealthSource,
    PlanningFactAsOf,
    PlanningFactProvenance,
)
from backend.domains.planning.required_contribution_solver import (
    RequiredContributionResult,
    RequiredContributionStatus,
)
from backend.domains.planning.target_basis import TargetValueBasis
from backend.domains.planning.target_solver import (
    TargetAchievementResult,
    TargetAchievementStatus,
)
from backend.main import app


USER_ID = UUID("00000000-0000-0000-0000-000000000401")
AS_OF_DATE = date(2026, 9, 30)


def _current_user() -> UserResponseDTO:
    return UserResponseDTO(
        id=USER_ID,
        email="fire@example.test",
        name="FIRE User",
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _manual_fact() -> InitialWealthFact:
    return InitialWealthFact(
        source=InitialWealthSource.USER_PROVIDED_SCENARIO,
        amount=Decimal("250000.00"),
        as_of=PlanningFactAsOf(
            observed_at=datetime(2026, 9, 30, 9, 30, tzinfo=timezone.utc)
        ),
        scope=InitialWealthScope.USER_PROVIDED_SCENARIO,
        provenance=PlanningFactProvenance(
            source_table="planning_request",
            source_type=InitialWealthSource.USER_PROVIDED_SCENARIO.value,
        ),
    )


def _planning_assumptions() -> ProjectionAssumptions:
    return ProjectionAssumptions(
        as_of_date=AS_OF_DATE,
        scenario_monthly_contribution=Decimal("1000.00"),
        expected_return_rate=Decimal("0.06"),
        return_type=ReturnType.REAL,
        output_mode=OutputMode.REAL,
        inflation_rate=None,
        horizon_months=120,
        target_date=None,
        rate_basis=RateBasis.EFFECTIVE_ANNUAL,
        contribution_timing=ContributionTiming.END_OF_MONTH,
    )


def _result(analysis_type: FireAnalysisType) -> FireAnalysisResult:
    fact = _manual_fact()
    summary = FireSummaryCalculator().calculate(
        FireSummaryInput(
            eligible_investment_wealth=fact.amount,
            monthly_retirement_spending=Decimal("5000.00"),
            assumed_annual_withdrawal_rate=Decimal("0.04"),
        )
    )
    assumptions = FireAnalysisAssumptions(
        monthly_retirement_spending=Decimal("5000.00"),
        assumed_annual_withdrawal_rate=Decimal("0.04"),
        expected_return_rate=(
            None if analysis_type is FireAnalysisType.SUMMARY else Decimal("0.06")
        ),
        return_type=(
            None if analysis_type is FireAnalysisType.SUMMARY else ReturnType.REAL
        ),
        inflation_rate=None,
        scenario_monthly_contribution=(
            Decimal("1000.00")
            if analysis_type is FireAnalysisType.PROJECTED_DATE
            else None
        ),
        horizon_months=(120 if analysis_type is FireAnalysisType.PROJECTED_DATE else None),
        desired_fire_date=(
            date(2036, 9, 30)
            if analysis_type is FireAnalysisType.REQUIRED_CONTRIBUTION
            else None
        ),
    )
    planning_assumptions = _planning_assumptions()
    projection = None
    required = None
    if analysis_type is FireAnalysisType.PROJECTED_DATE:
        projection = TargetAchievementResult(
            status=TargetAchievementStatus.NOT_REACHED_WITHIN_HORIZON,
            target_amount=summary.fire_target,
            initial_wealth_fact=fact,
            assumptions=planning_assumptions,
            achievement_period=None,
            achievement_date=None,
            months_required=None,
            achieved_wealth=None,
            projection_result=None,
        )
    if analysis_type is FireAnalysisType.REQUIRED_CONTRIBUTION:
        target_result = TargetAchievementResult(
            status=TargetAchievementStatus.NOT_REACHED_WITHIN_HORIZON,
            target_amount=summary.fire_target,
            initial_wealth_fact=fact,
            assumptions=planning_assumptions,
            achievement_period=None,
            achievement_date=None,
            months_required=None,
            achieved_wealth=None,
            projection_result=None,
        )
        required = RequiredContributionResult(
            status=RequiredContributionStatus.SOLVED,
            target_amount=summary.fire_target,
            initial_wealth_fact=fact,
            assumptions_template=planning_assumptions,
            required_monthly_contribution=Decimal("1234.56"),
            solved_assumptions=planning_assumptions,
            target_achievement_result=target_result,
        )
    return FireAnalysisResult(
        analysis_type=analysis_type,
        as_of_date=AS_OF_DATE,
        output_mode=OutputMode.REAL,
        target_value_basis=TargetValueBasis.REAL,
        summary=summary,
        initial_wealth_fact=fact,
        assumptions=assumptions,
        projection=projection,
        required_contribution=required,
    )


class _ServiceSpy:
    def __init__(self, result: FireAnalysisResult | Exception) -> None:
        self.result = result
        self.calls = []

    def analyze(self, command, db, current_user_id):
        self.calls.append((command, db, current_user_id))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def _authenticated_client():
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_db] = lambda: "read-session"
    with TestClient(app) as client:
        yield client


def _install_service(result: FireAnalysisResult | Exception) -> _ServiceSpy:
    service = _ServiceSpy(result)
    app.dependency_overrides[fire_router.get_fire_analysis_service] = lambda: service
    return service


def _manual_source(**overrides):
    payload = {
        "source": "USER_PROVIDED_SCENARIO",
        "amount": "250000.00",
        "observed_at": "2026-09-30T09:30:00-03:00",
    }
    payload.update(overrides)
    return payload


def _portfolio_source(**overrides):
    payload = {"source": "INVESTMENT_PORTFOLIO_SNAPSHOT"}
    payload.update(overrides)
    return payload


def _summary_payload(**overrides):
    payload = {
        "analysis_type": "SUMMARY",
        "as_of_date": "2026-09-30",
        "initial_wealth": _manual_source(),
        "monthly_retirement_spending": "5000.00",
        "assumed_annual_withdrawal_rate": "0.04",
    }
    payload.update(overrides)
    return payload


def _projected_payload(**overrides):
    payload = {
        "analysis_type": "PROJECTED_DATE",
        "as_of_date": "2026-09-30",
        "initial_wealth": _portfolio_source(),
        "monthly_retirement_spending": "5000.00",
        "assumed_annual_withdrawal_rate": "0.04",
        "scenario_monthly_contribution": "1000.00",
        "expected_return_rate": "0.06",
        "return_type": "REAL",
        "horizon_months": 120,
    }
    payload.update(overrides)
    return payload


def _required_payload(**overrides):
    payload = {
        "analysis_type": "REQUIRED_CONTRIBUTION",
        "as_of_date": "2026-09-30",
        "initial_wealth": _portfolio_source(),
        "monthly_retirement_spending": "5000.00",
        "assumed_annual_withdrawal_rate": "0.04",
        "expected_return_rate": "0.06",
        "return_type": "REAL",
        "desired_fire_date": "2036-09-30",
    }
    payload.update(overrides)
    return payload


def test_summary_endpoint_is_authenticated_string_safe_and_calls_service_once(
    _authenticated_client,
):
    service = _install_service(_result(FireAnalysisType.SUMMARY))

    response = _authenticated_client.post("/api/v1/fire/analysis", json=_summary_payload())

    assert response.status_code == 200
    body = response.json()
    assert len(service.calls) == 1
    assert service.calls[0][2] == USER_ID
    assert body["analysis_type"] == "SUMMARY"
    assert body["basis"] == "REAL"
    assert body["projection"] is None
    assert body["required_contribution"] is None
    for field in (
        "monthly_retirement_spending",
        "annual_required_spending",
        "assumed_annual_withdrawal_rate",
        "fire_target",
        "eligible_investment_wealth",
        "gap_to_fire",
        "progress_ratio",
        "supported_annual_withdrawal",
        "supported_monthly_withdrawal",
    ):
        assert isinstance(body["summary"][field], str)
    assert body["provenance"]["initial_wealth_fact"]["source"] == "USER_PROVIDED_SCENARIO"


def test_projected_date_maps_to_one_service_call_and_preserves_valid_solver_status(
    _authenticated_client,
):
    service = _install_service(_result(FireAnalysisType.PROJECTED_DATE))

    response = _authenticated_client.post(
        "/api/v1/fire/analysis", json=_projected_payload()
    )

    assert response.status_code == 200
    assert len(service.calls) == 1
    command = service.calls[0][0]
    assert command.analysis_type is FireAnalysisType.PROJECTED_DATE
    assert command.initial_wealth.__class__.__name__ == "PortfolioInitialWealthSelection"
    assert response.json()["projection"]["status"] == "NOT_REACHED_WITHIN_HORIZON"
    assert response.json()["required_contribution"] is None


def test_required_contribution_maps_desired_date_and_nullability(_authenticated_client):
    service = _install_service(_result(FireAnalysisType.REQUIRED_CONTRIBUTION))

    response = _authenticated_client.post(
        "/api/v1/fire/analysis", json=_required_payload()
    )

    assert response.status_code == 200
    command = service.calls[0][0]
    assert command.desired_fire_date == date(2036, 9, 30)
    assert response.json()["projection"] is None
    assert response.json()["required_contribution"]["status"] == "SOLVED"
    assert response.json()["assumptions"]["scenario_monthly_contribution"] is None


def test_endpoint_requires_existing_authentication():
    with TestClient(app) as client:
        response = client.post("/api/v1/fire/analysis", json=_summary_payload())

    assert response.status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        _summary_payload(expected_return_rate="0.06"),
        _summary_payload(horizon_months=120),
        _projected_payload(desired_fire_date="2036-09-30"),
        _required_payload(scenario_monthly_contribution="1000.00"),
        _required_payload(horizon_months=120),
    ],
)
def test_mode_incompatible_fields_are_rejected(_authenticated_client, payload):
    response = _authenticated_client.post("/api/v1/fire/analysis", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        _projected_payload(scenario_monthly_contribution=None),
        _projected_payload(horizon_months=None),
        _required_payload(desired_fire_date=None),
    ],
)
def test_mode_required_fields_cannot_be_omitted_or_null(_authenticated_client, payload):
    response = _authenticated_client.post("/api/v1/fire/analysis", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        _projected_payload(inflation_rate="0.04"),
        _projected_payload(return_type="NOMINAL", inflation_rate=None),
        _required_payload(inflation_rate="0.04"),
        _required_payload(return_type="NOMINAL", inflation_rate=None),
    ],
)
def test_return_inflation_matrix_rejects_invalid_combinations(
    _authenticated_client,
    payload,
):
    response = _authenticated_client.post("/api/v1/fire/analysis", json=payload)

    assert response.status_code == 422


def test_nominal_with_explicit_inflation_is_accepted_structurally(_authenticated_client):
    service = _install_service(_result(FireAnalysisType.PROJECTED_DATE))

    response = _authenticated_client.post(
        "/api/v1/fire/analysis",
        json=_projected_payload(
            return_type="NOMINAL",
            expected_return_rate="0.10",
            inflation_rate="0.04",
        ),
    )

    assert response.status_code == 200
    command = service.calls[0][0]
    assert command.return_type is ReturnType.NOMINAL
    assert command.inflation_rate == Decimal("0.04")


def test_fire_wealth_union_rejects_goal_and_portfolio_client_governance_fields(
    _authenticated_client,
):
    goal = _authenticated_client.post(
        "/api/v1/fire/analysis",
        json=_summary_payload(
            initial_wealth={
                "source": "GOAL_CURRENT_AMOUNT",
                "goal_id": "00000000-0000-0000-0000-000000000402",
            }
        ),
    )
    forged_portfolio = _authenticated_client.post(
        "/api/v1/fire/analysis",
        json=_summary_payload(initial_wealth=_portfolio_source(account_id="forged")),
    )

    assert goal.status_code == 422
    assert forged_portfolio.status_code == 422


def test_manual_observed_at_is_required_and_manual_source_is_mapped(_authenticated_client):
    missing = _authenticated_client.post(
        "/api/v1/fire/analysis",
        json=_summary_payload(initial_wealth={"source": "USER_PROVIDED_SCENARIO", "amount": "1.00"}),
    )
    service = _install_service(_result(FireAnalysisType.SUMMARY))
    valid = _authenticated_client.post("/api/v1/fire/analysis", json=_summary_payload())

    assert missing.status_code == 422
    assert valid.status_code == 200
    command = service.calls[0][0]
    assert command.initial_wealth.amount == Decimal("250000.00")
    assert command.initial_wealth.observed_at == datetime.fromisoformat(
        "2026-09-30T09:30:00-03:00"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("monthly_retirement_spending", 5000.0),
        ("monthly_retirement_spending", "1e3"),
        ("monthly_retirement_spending", "5000.001"),
        ("monthly_retirement_spending", "0"),
        ("assumed_annual_withdrawal_rate", "0"),
        ("assumed_annual_withdrawal_rate", "1"),
        ("assumed_annual_withdrawal_rate", "NaN"),
        ("assumed_annual_withdrawal_rate", "Infinity"),
    ],
)
def test_financial_inputs_require_strict_plain_decimal_strings(
    _authenticated_client,
    field,
    value,
):
    response = _authenticated_client.post(
        "/api/v1/fire/analysis", json=_summary_payload(**{field: value})
    )

    assert response.status_code == 422


def test_source_failure_is_mapped_to_a_safe_422(_authenticated_client):
    _install_service(
        PlanningPortfolioSourceUnavailableError("private source implementation detail")
    )

    response = _authenticated_client.post(
        "/api/v1/fire/analysis", json=_projected_payload()
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Selected certified portfolio source is unavailable."
    }


def test_openapi_exposes_exactly_one_authenticated_fire_post_operation():
    schema = app.openapi()
    fire_paths = {
        path: sorted(operations)
        for path, operations in schema["paths"].items()
        if path.startswith("/api/v1/fire")
    }

    assert fire_paths == {"/api/v1/fire/analysis": ["post"]}
    operation = schema["paths"]["/api/v1/fire/analysis"]["post"]
    assert operation["security"]
    assert "oneOf" in operation["requestBody"]["content"]["application/json"]["schema"]
