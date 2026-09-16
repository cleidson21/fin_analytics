from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.dependencies.auth import get_current_user
from backend.api.routers import financial_health
from backend.domains.pierre.models import Account, LegacyBase, Transaction
from backend.main import app


def _add_transaction(db, external_id, date_value, amount, classification, category=None):
    db.add(Transaction(
        provider="test_provider",
        external_id=external_id,
        account_provider="test_provider",
        account_external_id="test_account",
        description="Health API test transaction",
        amount=Decimal(amount),
        currency="BRL",
        date=datetime.strptime(date_value, "%Y-%m-%d"),
        status="POSTED",
        type="CARD",
        governance_status="CLASSIFIED",
        economic_classification=classification,
        category=category,
    ))
    db.commit()


@pytest.fixture
def api_client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    LegacyBase.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    session.add(Account(
        provider="test_provider",
        external_id="test_account",
        name="Health API Test Account",
        type="CHECKING",
    ))
    session.commit()

    monkeypatch.setattr(financial_health, "SessionLocal", session_factory)
    app.dependency_overrides[get_current_user] = lambda: object()
    client = TestClient(app)
    yield client, session
    app.dependency_overrides.pop(get_current_user, None)
    session.close()
    engine.dispose()


def _seed_complete_history(session):
    _add_transaction(session, "old-expense", "2025-06-15", "-10.00", "SAIDA", "Old")
    for month, income in [("06", "100.00"), ("07", "110.00"), ("08", "90.00")]:
        _add_transaction(session, f"income-{month}", f"2026-{month}-05", income, "ENTRADA", "Salary")
        _add_transaction(session, f"services-{month}", f"2026-{month}-06", "-100.00", "SAIDA", "Services")
    _add_transaction(session, "sept-income", "2026-09-05", "1000.00", "ENTRADA", "Salary")
    _add_transaction(session, "sept-services", "2026-09-06", "-200.00", "SAIDA", "Services")
    _add_transaction(session, "sept-food", "2026-09-07", "-400.00", "SAIDA", "Food")


def _seed_trend_history(session):
    _add_transaction(session, "trend-july-income", "2026-07-05", "100.00", "ENTRADA", "Salary")
    _add_transaction(session, "trend-july-services", "2026-07-06", "-100.00", "SAIDA", "Services")
    _add_transaction(session, "trend-july-gone", "2026-07-07", "-30.00", "SAIDA", "Gone")
    _add_transaction(session, "trend-aug-income", "2026-08-05", "200.00", "ENTRADA", "Salary")
    _add_transaction(session, "trend-aug-services", "2026-08-06", "-100.00", "SAIDA", "Services")
    _add_transaction(session, "trend-aug-new", "2026-08-07", "-25.00", "SAIDA", "New")
    _add_transaction(session, "trend-sept-income", "2026-09-05", "999.00", "ENTRADA", "Salary")


def test_health_api_requires_authentication():
    app.dependency_overrides.pop(get_current_user, None)
    response = TestClient(app).get("/api/v1/financial-health/cashflow?reference_month=2026-09")
    assert response.status_code == 401

    trends = TestClient(app).get("/api/v1/financial-health/trends?reference_month=2026-09")
    assert trends.status_code == 401


def test_cashflow_response_serializes_decimal_without_float_artifacts(api_client):
    client, session = api_client
    _seed_complete_history(session)

    response = client.get("/api/v1/financial-health/cashflow?reference_month=2026-09")

    assert response.status_code == 200
    body = response.json()
    assert body["reference_month"] == "2026-09"
    assert body["total_income"] == "1000.00"
    assert body["total_expense"] == "600.00"
    assert body["net_cashflow"] == "400.00"
    assert body["savings_rate"] == "0.4"
    assert "13025.539999999999" not in response.text


def test_history_preserves_order_gap_and_null_rate(api_client):
    client, session = api_client
    _seed_complete_history(session)

    response = client.get("/api/v1/financial-health/history?reference_month=2026-09")

    assert response.status_code == 200
    body = response.json()
    assert [item["reference_month"] for item in body] == [
        "2025-06", "2026-06", "2026-07", "2026-08", "2026-09",
    ]
    assert body[0]["savings_rate"] is None
    assert "2025-07" not in [item["reference_month"] for item in body]


def test_categories_and_anomalies_return_valid_domain_results(api_client):
    client, session = api_client
    _seed_complete_history(session)

    categories = client.get("/api/v1/financial-health/categories?reference_month=2026-09")
    anomalies = client.get("/api/v1/financial-health/anomalies?reference_month=2026-09")

    assert categories.status_code == 200
    assert categories.json()["total_expense"] == "600.00"
    assert categories.json()["top_category"]["category"] == "Food"
    assert [item["rank"] for item in categories.json()["categories"]] == [1, 2]
    assert anomalies.status_code == 200
    assert anomalies.json()["global_status"] == "OK"
    assert {item["status"] for item in anomalies.json()["anomalies"]} == {"SPIKE", "NEW_EXPENSE"}
    assert all(item["baseline_reference"] is None or isinstance(item["baseline_reference"], str) for item in anomalies.json()["evaluations"])


def test_anomalies_returns_insufficient_baseline_as_valid_response(api_client):
    client, session = api_client
    _add_transaction(session, "sept-only", "2026-09-05", "-500.00", "SAIDA", "OnlyCurrent")

    response = client.get("/api/v1/financial-health/anomalies?reference_month=2026-09")

    assert response.status_code == 200
    assert response.json() == {
        "target_reference_month": "2026-09",
        "global_status": "INSUFFICIENT_BASELINE",
        "evaluations": [],
        "anomalies": [],
    }


@pytest.mark.parametrize("reference_month", ["2026-13", "2026-1", "invalid"])
def test_reference_month_validation_returns_422(api_client, reference_month):
    client, _ = api_client

    response = client.get(f"/api/v1/financial-health/cashflow?reference_month={reference_month}")

    assert response.status_code == 422


def test_trends_returns_authenticated_partial_month_contract(api_client, monkeypatch):
    client, session = api_client
    _seed_trend_history(session)
    monkeypatch.setattr(financial_health, "_current_reference_month", lambda: "2026-09")

    response = client.get("/api/v1/financial-health/trends?reference_month=2026-09")

    assert response.status_code == 200
    body = response.json()
    assert body["requested_reference_month"] == "2026-09"
    assert body["trend_target_month"] == "2026-08"
    assert body["comparison_month"] == "2026-07"
    assert body["status"] == "OK"
    assert body["global"]["status"] == "OK"
    income = next(item for item in body["global"]["metrics"] if item["metric"] == "total_income")
    assert income == {
        "metric": "total_income",
        "current_value": "200.00",
        "previous_value": "100.00",
        "absolute_delta": "100.00",
        "percentage_delta": "1",
        "direction": "INCREASED",
    }
    items = {item["category"]: item for item in body["categories"]["items"]}
    assert items["New"]["direction"] == "NEW"
    assert items["New"]["previous_expense"] is None
    assert items["New"]["percentage_delta"] is None
    assert items["Gone"]["direction"] == "DISAPPEARED"
    assert items["Gone"]["current_expense"] is None
    assert all(
        isinstance(value, str)
        for item in body["global"]["metrics"]
        for value in (item["current_value"], item["previous_value"], item["absolute_delta"])
        if value is not None
    )


def test_trends_keeps_closed_requested_month_as_target(api_client, monkeypatch):
    client, session = api_client
    _seed_trend_history(session)
    monkeypatch.setattr(financial_health, "_current_reference_month", lambda: "2026-09")

    response = client.get("/api/v1/financial-health/trends?reference_month=2026-08")

    assert response.status_code == 200
    assert response.json()["trend_target_month"] == "2026-08"
    assert response.json()["comparison_month"] == "2026-07"


def test_trends_preserves_null_percentage_and_undefined_rate(api_client, monkeypatch):
    client, session = api_client
    _add_transaction(session, "zero-income-expense", "2026-10-05", "-10.00", "SAIDA", "Zero")
    _add_transaction(session, "positive-income", "2026-11-05", "100.00", "ENTRADA", "Salary")
    _add_transaction(session, "positive-expense", "2026-11-06", "-10.00", "SAIDA", "Zero")
    monkeypatch.setattr(financial_health, "_current_reference_month", lambda: "2026-12")

    response = client.get("/api/v1/financial-health/trends?reference_month=2026-11")

    assert response.status_code == 200
    metrics = {item["metric"]: item for item in response.json()["global"]["metrics"]}
    assert metrics["total_income"]["percentage_delta"] is None
    assert metrics["savings_rate"]["direction"] == "INSUFFICIENT_DATA"
    assert metrics["savings_rate"]["absolute_delta"] is None


def test_trends_returns_insufficient_data_as_http_200(api_client, monkeypatch):
    client, _ = api_client
    monkeypatch.setattr(financial_health, "_current_reference_month", lambda: "2026-09")

    response = client.get("/api/v1/financial-health/trends?reference_month=2025-05")

    assert response.status_code == 200
    assert response.json() == {
        "requested_reference_month": "2025-05",
        "trend_target_month": "2025-05",
        "comparison_month": "2025-04",
        "status": "INSUFFICIENT_DATA",
        "global": {"status": "INSUFFICIENT_DATA", "metrics": []},
        "categories": {"status": "INSUFFICIENT_DATA", "items": []},
    }


@pytest.mark.parametrize("reference_month", ["2026-13", "2026-1", "invalid"])
def test_trends_reference_month_validation_returns_422(api_client, reference_month):
    client, _ = api_client

    response = client.get(f"/api/v1/financial-health/trends?reference_month={reference_month}")

    assert response.status_code == 422


def test_trends_appears_in_openapi(api_client):
    client, _ = api_client

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/financial-health/trends" in response.json()["paths"]
