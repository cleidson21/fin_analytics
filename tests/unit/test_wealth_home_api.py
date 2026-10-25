from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.wealth_home import get_db
from backend.api.routers import wealth_home as wealth_home_router
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.exceptions.smart_context_ownership_error import (
    SmartContextOwnershipUnavailableError,
)
from backend.application.services.wealth_home_read_service import (
    GoalStatusCount,
    WealthHomeAvailability,
    WealthHomeCompleteness,
    WealthHomeData,
    WealthHomeFreshness,
    WealthHomeGoalsData,
    WealthHomeHealthData,
    WealthHomeInvestmentsData,
    WealthHomeSourceMetadata,
)
from backend.domain.enums.goal_status import GoalStatus
from backend.domain.enums.user_role import UserRole
from backend.main import app


OWNER_ID = UUID("00000000-0000-0000-0000-000000000711")
READ_AT = datetime(2026, 10, 22, 14, 30, tzinfo=timezone.utc)


def _current_user() -> UserResponseDTO:
    return UserResponseDTO(
        id=OWNER_ID,
        email="owner@example.test",
        name="Owner",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _data() -> WealthHomeData:
    health_source = WealthHomeSourceMetadata(
        authority="FINANCIAL_HEALTH",
        reader="PlanningHealthReadAdapter",
        version="10.2",
        scope="CONSOLIDATED_LOCAL_TENANT",
        read_at=READ_AT,
        updated_at=None,
        freshness=WealthHomeFreshness.PARTIAL_PERIOD,
        completeness=WealthHomeCompleteness.UNKNOWN,
    )
    goals_source = WealthHomeSourceMetadata(
        authority="GOALS",
        reader="PlanningGoalReadQuery",
        version="10.3.1",
        scope="AUTHENTICATED_USER_OWNED_GOALS",
        read_at=READ_AT,
        updated_at=datetime(2026, 10, 20, tzinfo=timezone.utc),
        freshness=WealthHomeFreshness.CURRENT,
        completeness=WealthHomeCompleteness.COMPLETE,
    )
    investments_source = WealthHomeSourceMetadata(
        authority="INVESTMENT_PORTFOLIO",
        reader="PlanningPortfolioSourceResolver",
        version="10.3.10B1",
        scope="AUTHENTICATED_CANONICAL_MYPROFIT_PORTFOLIO",
        read_at=READ_AT,
        updated_at=datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc),
        freshness=WealthHomeFreshness.PARTIAL_PERIOD,
        completeness=WealthHomeCompleteness.UNKNOWN,
    )
    return WealthHomeData(
        contract_version="wealth-home-v2",
        status=WealthHomeAvailability.AVAILABLE,
        reference_month="2026-10",
        scope="AUTHENTICATED_SINGLE_USER",
        generated_at=READ_AT,
        health=WealthHomeHealthData(
            status=WealthHomeAvailability.AVAILABLE,
            reference_month="2026-10",
            currency="BRL",
            net_cashflow=Decimal("3376.55"),
            reason=None,
            source=health_source,
        ),
        goals=WealthHomeGoalsData(
            status=WealthHomeAvailability.AVAILABLE,
            total_count=2,
            by_status=(
                GoalStatusCount(GoalStatus.ACTIVE, 1),
                GoalStatusCount(GoalStatus.ACHIEVED, 1),
                GoalStatusCount(GoalStatus.PAUSED, 0),
                GoalStatusCount(GoalStatus.CANCELLED, 0),
            ),
            reason=None,
            source=goals_source,
        ),
        investments=WealthHomeInvestmentsData(
            status=WealthHomeAvailability.AVAILABLE,
            requested_reference_month="2026-10",
            snapshot_reference_month="2026-10",
            currency="BRL",
            investment_wealth=Decimal("842450.00"),
            source_type="MYPROFIT_EVOLUCAO",
            portfolio_scope="portfolio-synthetic-01",
            run_id="run-synthetic-01",
            reason=None,
            source=investments_source,
        ),
    )


class ServiceFake:
    def __init__(self, *, data=None, error=None) -> None:
        self.data = data
        self.error = error
        self.calls = []

    def read(self, db, current_user_id, *, reference_month):
        self.calls.append((db, current_user_id, reference_month))
        if self.error is not None:
            raise self.error
        return self.data


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_endpoint_requires_authentication():
    with TestClient(app) as client:
        response = client.get("/api/v1/wealth-home?reference_month=2026-10")

    assert response.status_code == 401


def test_endpoint_exposes_minimum_contract_and_exact_decimal_string():
    db = object()
    service = ServiceFake(data=_data())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[
        wealth_home_router.get_wealth_home_read_service
    ] = lambda: service

    with TestClient(app) as client:
        response = client.get("/api/v1/wealth-home?reference_month=2026-10")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "contract_version",
        "status",
        "reference_month",
        "scope",
        "generated_at",
        "health",
        "goals",
        "investments",
    }
    assert body["health"]["net_cashflow"] == "3376.55"
    assert type(body["health"]["net_cashflow"]) is str
    assert body["health"]["source"]["authority"] == "FINANCIAL_HEALTH"
    assert body["goals"]["source"]["scope"] == "AUTHENTICATED_USER_OWNED_GOALS"
    assert body["contract_version"] == "wealth-home-v2"
    assert body["investments"]["investment_wealth"] == "842450.00"
    assert type(body["investments"]["investment_wealth"]) is str
    assert body["investments"]["requested_reference_month"] == "2026-10"
    assert body["investments"]["snapshot_reference_month"] == "2026-10"
    assert body["investments"]["source_type"] == "MYPROFIT_EVOLUCAO"
    assert body["investments"]["source"]["reader"] == "PlanningPortfolioSourceResolver"
    assert "user_id" not in response.text
    assert service.calls == [(db, OWNER_ID, "2026-10")]


def test_endpoint_maps_ownership_failure_without_disclosing_identifiers():
    service = ServiceFake(
        error=SmartContextOwnershipUnavailableError(str(OWNER_ID))
    )
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[
        wealth_home_router.get_wealth_home_read_service
    ] = lambda: service

    with TestClient(app) as client:
        response = client.get("/api/v1/wealth-home?reference_month=2026-10")

    assert response.status_code == 422
    assert response.json() == {"detail": "Wealth Home scope is unavailable."}
    assert str(OWNER_ID) not in response.text


def test_endpoint_keeps_unclassified_source_failure_generic():
    service = ServiceFake(error=RuntimeError("sensitive persistence detail"))
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[
        wealth_home_router.get_wealth_home_read_service
    ] = lambda: service

    with TestClient(app) as client:
        response = client.get("/api/v1/wealth-home?reference_month=2026-10")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Wealth Home error."}
    assert "sensitive persistence detail" not in response.text


def test_endpoint_rejects_malformed_reference_before_service_call():
    service = ServiceFake(data=_data())
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[
        wealth_home_router.get_wealth_home_read_service
    ] = lambda: service

    with TestClient(app) as client:
        response = client.get("/api/v1/wealth-home?reference_month=2026%2F10")

    assert response.status_code == 422
    assert service.calls == []
