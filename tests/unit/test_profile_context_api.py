from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.dependencies.auth import get_current_user
from backend.api.routers import profile as profile_router
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.services.profile_declared_context_service import (
    ProfileDeclaredContextService,
)
from backend.database.base import Base
from backend.domain.enums.user_role import UserRole
from backend.infrastructure.persistence.models.smart_context import (
    DeclaredFinancialContextModel,
)
from backend.infrastructure.persistence.models.user import UserModel
from backend.main import app


OWNER_ID = UUID("00000000-0000-0000-0000-000000000601")
OTHER_ID = UUID("00000000-0000-0000-0000-000000000602")
FIXED_NOW = datetime(2026, 10, 5, 12, 30, 0)
EXPECTED_RESPONSE_FIELDS = {
    "name",
    "email",
    "declared_monthly_gross_income",
    "semantic_type",
    "source",
    "currency",
    "income_period",
    "income_basis",
    "income_as_of_date",
    "declared_at",
    "updated_at",
}


def _user_model(user_id: UUID) -> UserModel:
    return UserModel(
        id=user_id,
        email=f"{user_id.hex}@example.test",
        name="Profile Owner",
        hashed_password="not-used",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


def _current_user(user_id: UUID = OWNER_ID) -> UserResponseDTO:
    return UserResponseDTO(
        id=user_id,
        email=f"{user_id.hex}@example.test",
        name="Profile Owner",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 1, 1),
        last_login_at=None,
    )


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def profile_api(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(
        engine,
        tables=[UserModel.__table__, DeclaredFinancialContextModel.__table__],
    )
    session_factory = sessionmaker(bind=engine)
    with session_factory.begin() as db:
        db.add(_user_model(OWNER_ID))

    from backend.api.dependencies import profile_context as profile_dependencies

    monkeypatch.setattr(profile_dependencies, "SessionLocal", session_factory)
    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[
        profile_router.get_profile_declared_context_service
    ] = lambda: ProfileDeclaredContextService(clock=lambda: FIXED_NOW)

    with TestClient(app) as client:
        yield client, session_factory

    engine.dispose()


def test_profile_context_requires_existing_authentication():
    with TestClient(app) as client:
        response = client.get("/api/v1/profile/context")

    assert response.status_code == 401


def test_get_empty_context_is_a_legitimate_null_state(profile_api):
    client, _ = profile_api

    response = client.get("/api/v1/profile/context")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == EXPECTED_RESPONSE_FIELDS
    assert body == {
        "name": "Profile Owner",
        "email": f"{OWNER_ID.hex}@example.test",
        "declared_monthly_gross_income": None,
        "semantic_type": "DECLARED",
        "source": "USER_PROFILE",
        "currency": None,
        "income_period": None,
        "income_basis": None,
        "income_as_of_date": None,
        "declared_at": None,
        "updated_at": None,
    }


def test_patch_persists_and_get_returns_exact_decimal_string(profile_api):
    client, session_factory = profile_api

    response = client.patch(
        "/api/v1/profile/context",
        json={
            "declared_monthly_gross_income": "5500.00",
            "income_as_of_date": "2026-10-01",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["declared_monthly_gross_income"] == "5500.00"
    assert type(body["declared_monthly_gross_income"]) is str
    assert body["currency"] == "BRL"
    assert body["income_period"] == "MONTHLY"
    assert body["income_basis"] == "GROSS"
    assert body["income_as_of_date"] == "2026-10-01"
    assert body["declared_at"] == "2026-10-05T12:30:00"
    assert body["updated_at"] == "2026-10-05T12:30:00"

    with session_factory() as db:
        stored = db.execute(select(DeclaredFinancialContextModel)).scalar_one()
        assert stored.user_id == OWNER_ID
        assert stored.declared_monthly_gross_income == Decimal("5500.00")
        assert type(stored.declared_monthly_gross_income) is Decimal

    read = client.get("/api/v1/profile/context")
    assert read.status_code == 200
    assert read.json() == body


@pytest.mark.parametrize(
    "invalid_amount",
    [
        5500,
        5500.0,
        "0",
        "0.00",
        "-1.00",
        "1.001",
        "1e3",
        "NaN",
        "Infinity",
        " 5500.00",
        "5500.00 ",
        "5.500,00",
        "",
    ],
)
def test_patch_rejects_non_string_or_invalid_declared_income(
    profile_api,
    invalid_amount,
):
    client, _ = profile_api

    response = client.patch(
        "/api/v1/profile/context",
        json={"declared_monthly_gross_income": invalid_amount},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid_date",
    ["2026-02-30", "2026-10-05T00:00:00", "05/10/2026", 20261005],
)
def test_patch_rejects_invalid_as_of_date(profile_api, invalid_date):
    client, _ = profile_api

    response = client.patch(
        "/api/v1/profile/context",
        json={
            "declared_monthly_gross_income": "5500.00",
            "income_as_of_date": invalid_date,
        },
    )

    assert response.status_code == 422


def test_clear_is_explicit_null_and_never_zero(profile_api):
    client, session_factory = profile_api
    client.patch(
        "/api/v1/profile/context",
        json={"declared_monthly_gross_income": "5500.00"},
    )

    response = client.patch(
        "/api/v1/profile/context",
        json={"declared_monthly_gross_income": None},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["declared_monthly_gross_income"] is None
    assert body["currency"] is None
    assert body["income_period"] is None
    assert body["income_basis"] is None
    assert body["income_as_of_date"] is None
    assert body["declared_at"] is None
    assert body["updated_at"] == "2026-10-05T12:30:00"
    with session_factory() as db:
        stored = db.execute(select(DeclaredFinancialContextModel)).scalar_one()
        assert stored.declared_monthly_gross_income is None


def test_clear_rejects_as_of_date_and_missing_mutation_field(profile_api):
    client, _ = profile_api

    with_date = client.patch(
        "/api/v1/profile/context",
        json={
            "declared_monthly_gross_income": None,
            "income_as_of_date": "2026-10-01",
        },
    )
    missing = client.patch("/api/v1/profile/context", json={})

    assert with_date.status_code == 422
    assert missing.status_code == 422


def test_repeated_update_and_clear_keep_exactly_one_row(profile_api):
    client, session_factory = profile_api
    payload = {
        "declared_monthly_gross_income": "5500.00",
        "income_as_of_date": "2026-10-01",
    }

    assert client.patch("/api/v1/profile/context", json=payload).status_code == 200
    assert client.patch("/api/v1/profile/context", json=payload).status_code == 200
    assert client.patch(
        "/api/v1/profile/context",
        json={"declared_monthly_gross_income": None},
    ).status_code == 200
    assert client.patch(
        "/api/v1/profile/context",
        json={"declared_monthly_gross_income": None},
    ).status_code == 200

    with session_factory() as db:
        count = db.execute(
            select(func.count()).select_from(DeclaredFinancialContextModel)
        ).scalar_one()
        assert count == 1


@pytest.mark.parametrize("forged_field", ["user_id", "account_id", "scope_id"])
def test_patch_rejects_forged_owner_or_scope_fields(profile_api, forged_field):
    client, _ = profile_api

    response = client.patch(
        "/api/v1/profile/context",
        json={
            "declared_monthly_gross_income": "5500.00",
            forged_field: str(uuid4()),
        },
    )

    assert response.status_code == 422


def test_wrong_authenticated_user_fails_closed_without_owner_disclosure(profile_api):
    client, _ = profile_api
    app.dependency_overrides[get_current_user] = lambda: _current_user(OTHER_ID)

    response = client.get("/api/v1/profile/context")

    assert response.status_code == 422
    assert response.json() == {"detail": "Declared Profile context is unavailable."}
    assert str(OWNER_ID) not in response.text
    assert OWNER_ID.hex not in response.text


def test_multiple_users_fail_closed_without_first_user_selection(profile_api):
    client, session_factory = profile_api
    with session_factory.begin() as db:
        db.add(_user_model(OTHER_ID))

    response = client.get("/api/v1/profile/context")

    assert response.status_code == 422
    assert response.json() == {"detail": "Declared Profile context is unavailable."}


def test_response_is_purpose_limited_and_excludes_internal_or_personal_fields(profile_api):
    client, _ = profile_api

    response = client.get("/api/v1/profile/context")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == EXPECTED_RESPONSE_FIELDS
    serialized = response.text.lower()
    for forbidden in (
        "user_id",
        "account_id",
        "scope",
        "cpf",
        "telephone",
        "phone",
        "birth_date",
        "employer",
        "occupation",
        "employment",
        "token",
        "secret",
    ):
        assert forbidden not in serialized


def test_mapping_failure_rolls_back_the_request_transaction(profile_api, monkeypatch):
    client, session_factory = profile_api

    def fail_mapping(*_args, **_kwargs):
        raise RuntimeError("mapping failed after write")

    monkeypatch.setattr(profile_router, "map_profile_context_response", fail_mapping)
    response = client.patch(
        "/api/v1/profile/context",
        json={"declared_monthly_gross_income": "5500.00"},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Profile context error."}
    with session_factory() as db:
        assert db.execute(
            select(func.count()).select_from(DeclaredFinancialContextModel)
        ).scalar_one() == 0


def test_openapi_keeps_the_authenticated_profile_surface_purpose_limited():
    schema = app.openapi()
    profile_paths = {
        path: sorted(operations)
        for path, operations in schema["paths"].items()
        if path.startswith("/api/v1/profile")
    }

    assert profile_paths == {"/api/v1/profile/context": ["get", "patch"]}
    for operation in schema["paths"]["/api/v1/profile/context"].values():
        assert operation["security"]
    financial_context_paths = {
        path
        for path in schema["paths"]
        if path.startswith("/api/v1/financial-context")
    }
    assert financial_context_paths == {
        "/api/v1/financial-context/income-candidates",
        "/api/v1/financial-context/income-candidates/{candidate_id}/confirm",
        "/api/v1/financial-context/income-candidates/{candidate_id}/reject",
        "/api/v1/financial-context/income-candidates/{candidate_id}/decision",
    }
    assert "/api/v1/financial-context" not in schema["paths"]

    patch = schema["paths"]["/api/v1/profile/context"]["patch"]
    request_ref = patch["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    request_schema = schema["components"]["schemas"][request_ref.rsplit("/", 1)[-1]]
    assert request_schema["additionalProperties"] is False
    assert set(request_schema["properties"]) == {
        "declared_monthly_gross_income",
        "income_as_of_date",
    }
    assert "declared_monthly_gross_income" in request_schema["required"]
    amount_schema = request_schema["properties"]["declared_monthly_gross_income"]
    assert {item.get("type") for item in amount_schema["anyOf"]} == {"string", "null"}


def test_openapi_keeps_planning_and_fire_routes_unchanged():
    paths = app.openapi()["paths"]
    planning = {
        path: sorted(operations)
        for path, operations in paths.items()
        if path.startswith("/api/v1/planning")
    }
    fire = {
        path: sorted(operations)
        for path, operations in paths.items()
        if path.startswith("/api/v1/fire")
    }

    assert planning == {
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
    assert fire == {"/api/v1/fire/analysis": ["post"]}
