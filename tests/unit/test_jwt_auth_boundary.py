"""Synthetic HTTP coverage of the real JWT dependency and production routers."""

import base64
import json
from dataclasses import fields
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from backend.api.dependencies import auth
from backend.api.dependencies.database import get_db_session
from backend.api.dependencies.financial_context import get_financial_context_read_session
from backend.api.dependencies.profile_context import get_profile_context_session
from backend.api.routers import financial_context, profile
from backend.application.dtos.auth_token_dto import AuthTokenDTO
from backend.application.services.income_candidate_service import IncomeCandidateCollection
from backend.core import container
from backend.database.session import get_db
from backend.domain.entities.user import User
from backend.domain.enums.user_role import UserRole
from backend.infrastructure.security.jwt_service import JWTService
from backend.main import app


SECRET = "synthetic-jwt-boundary-secret-only-for-tests"
USER_ID = UUID("00000000-0000-0000-0000-000000009101")
INVALID_CREDENTIALS = {"detail": "Não foi possível validar as credenciais"}


@pytest.fixture
def boundary(monkeypatch):
    user = User(
        id=USER_ID,
        email="jwt-boundary@example.test",
        name="Synthetic JWT User",
        hashed_password="synthetic-hash",
        is_active=True,
        is_verified=True,
        role=UserRole.VIEWER,
        created_at=datetime(2026, 1, 1),
    )
    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=user),
        get_by_email=AsyncMock(return_value=user),
        update_last_login=AsyncMock(),
    )
    settings = SimpleNamespace(JWT_SECRET=SECRET, JWT_EXPIRE_MINUTES=60)
    monkeypatch.setattr(auth, "settings", settings)
    monkeypatch.setattr(container, "settings", settings)
    monkeypatch.setattr(auth, "get_user_repository", lambda session: repository)
    monkeypatch.setattr(container, "get_user_repository", lambda session: repository)
    hasher = Mock()
    hasher.verify_password.return_value = True
    monkeypatch.setattr(container, "get_password_hasher", lambda: hasher)
    service = Mock()
    service.get_context.return_value = None
    income_service = Mock()
    income_service.list_candidates.return_value = IncomeCandidateCollection(
        as_of_date=date(2026, 10, 29), candidates=(),
    )
    session = object()
    # Restore any other suite's overrides on teardown; never inherit auth overrides.
    monkeypatch.setattr(app, "dependency_overrides", {})
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_profile_context_session] = lambda: session
    app.dependency_overrides[get_financial_context_read_session] = lambda: session
    app.dependency_overrides[profile.get_profile_declared_context_service] = lambda: service
    app.dependency_overrides[financial_context.get_income_candidate_service] = lambda: income_service
    # Authentication itself is never overridden, including on production routes.
    assert auth.get_current_user not in app.dependency_overrides
    with TestClient(app, raise_server_exceptions=False) as client:
        yield SimpleNamespace(
            client=client,
            repository=repository,
            user=user,
            service=service,
            income_service=income_service,
            hasher=hasher,
            session=session,
            issuer=JWTService(SECRET, 60, 7),
        )


def _request(boundary, token):
    return boundary.client.get(
        "/api/v1/profile/context", headers={"Authorization": f"Bearer {token}"}
    )


def _claims(**overrides):
    now = int(datetime.now(timezone.utc).timestamp())
    claims = {
        "sub": str(USER_ID),
        "exp": now + 3600,
        "iat": now,
        "jti": "synthetic-jti",
        "type": "access",
    }
    claims.update(overrides)
    return claims


def _signed(**overrides):
    return jwt.encode(_claims(**overrides), SECRET, algorithm="HS256")


def _assert_unauthorized(response):
    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS
    assert response.headers["www-authenticate"] == "Bearer"


def test_valid_access_token_is_allowed(boundary):
    response = _request(boundary, boundary.issuer.create_access_token(str(USER_ID)))

    assert response.status_code == 200
    assert response.json()["name"] == boundary.user.name
    boundary.repository.get_by_id.assert_awaited_once_with(USER_ID)
    boundary.service.get_context.assert_called_once_with(boundary.session, USER_ID)


def test_refresh_token_is_rejected_as_bearer(boundary):
    response = _request(boundary, boundary.issuer.create_refresh_token(str(USER_ID)))

    _assert_unauthorized(response)
    boundary.repository.get_by_id.assert_not_awaited()
    boundary.service.get_context.assert_not_called()


def test_malformed_uuid_is_unauthorized(boundary):
    response = _request(boundary, _signed(sub="not-a-uuid"))

    _assert_unauthorized(response)
    boundary.repository.get_by_id.assert_not_awaited()
    boundary.service.get_context.assert_not_called()


@pytest.mark.parametrize(
    "token_type",
    ["refresh", "unknown", "", "ACCESS", None, True, False, 0, 1, 1.5, [], ["access"], {}, {"type": "access"}],
)
def test_explicit_non_access_types_are_unauthorized(boundary, token_type):
    _assert_unauthorized(_request(boundary, _signed(type=token_type)))
    boundary.repository.get_by_id.assert_not_awaited()
    boundary.service.get_context.assert_not_called()


def test_legacy_access_without_type_remains_valid(boundary):
    claims = _claims()
    del claims["type"]
    response = _request(boundary, jwt.encode(claims, SECRET, algorithm="HS256"))

    assert response.status_code == 200
    boundary.repository.get_by_id.assert_awaited_once_with(USER_ID)


@pytest.mark.parametrize("token_type", ["access", "refresh", "legacy"])
def test_expired_tokens_are_unauthorized(boundary, token_type):
    now = int(datetime.now(timezone.utc).timestamp())
    claims = _claims(type=token_type, iat=now - 7200, exp=now - 60)
    if token_type == "legacy":
        del claims["type"]
    _assert_unauthorized(_request(boundary, jwt.encode(claims, SECRET, algorithm="HS256")))
    boundary.repository.get_by_id.assert_not_awaited()


@pytest.mark.parametrize("token_type", ["access", "legacy"])
def test_expiration_is_required_even_for_legacy_tokens(boundary, token_type):
    claims = _claims()
    del claims["exp"]
    if token_type == "legacy":
        del claims["type"]
    _assert_unauthorized(_request(boundary, jwt.encode(claims, SECRET, algorithm="HS256")))
    boundary.repository.get_by_id.assert_not_awaited()


@pytest.mark.parametrize("subject", [None, "", "invalid-identity", 42, True, [], {}, [str(USER_ID)]])
def test_invalid_subject_types_are_unauthorized(boundary, subject):
    _assert_unauthorized(_request(boundary, _signed(sub=subject)))
    boundary.repository.get_by_id.assert_not_awaited()


def test_missing_subject_is_unauthorized(boundary):
    claims = _claims()
    del claims["sub"]
    _assert_unauthorized(_request(boundary, jwt.encode(claims, SECRET, algorithm="HS256")))
    boundary.repository.get_by_id.assert_not_awaited()


@pytest.mark.parametrize("token_type", ["access", "legacy"])
def test_signature_is_required_for_typed_and_legacy_tokens(boundary, token_type):
    claims = _claims()
    if token_type == "legacy":
        del claims["type"]
    token = jwt.encode(claims, "different-synthetic-secret", algorithm="HS256")
    _assert_unauthorized(_request(boundary, token))
    boundary.repository.get_by_id.assert_not_awaited()


def test_changing_refresh_payload_to_access_without_resigning_is_rejected(boundary):
    token = boundary.issuer.create_refresh_token(str(USER_ID))
    header, _, signature = token.split(".")
    payload = base64.urlsafe_b64encode(json.dumps(_claims()).encode()).rstrip(b"=").decode()
    _assert_unauthorized(_request(boundary, f"{header}.{payload}.{signature}"))
    boundary.repository.get_by_id.assert_not_awaited()


def test_wrong_algorithm_is_unauthorized(boundary):
    token = jwt.encode(_claims(), SECRET, algorithm="HS384")
    _assert_unauthorized(_request(boundary, token))
    boundary.repository.get_by_id.assert_not_awaited()


@pytest.mark.parametrize("token", ["not-a-jwt", "a.b.c", "", "null"])
def test_invalid_token_is_unauthorized(boundary, token):
    _assert_unauthorized(_request(boundary, token))
    boundary.repository.get_by_id.assert_not_awaited()


def test_missing_token_is_unauthorized(boundary):
    response = boundary.client.get("/api/v1/profile/context")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers["www-authenticate"] == "Bearer"
    boundary.repository.get_by_id.assert_not_awaited()


def test_nonexistent_user_is_unauthorized(boundary):
    boundary.repository.get_by_id.return_value = None
    _assert_unauthorized(_request(boundary, _signed()))
    boundary.repository.get_by_id.assert_awaited_once_with(USER_ID)
    boundary.service.get_context.assert_not_called()


def test_inactive_user_keeps_existing_policy(boundary):
    boundary.user.is_active = False
    response = _request(boundary, _signed())
    assert response.status_code == 400
    assert response.json() == {"detail": "Usuário inativo"}
    boundary.service.get_context.assert_not_called()


PROJECTION = {
    "initial_wealth": {
        "source": "USER_PROVIDED_SCENARIO",
        "amount": "900.00",
        "observed_at": "2026-10-29T09:30:00-03:00",
    },
    "assumptions": {
        "as_of_date": "2026-10-29",
        "scenario_monthly_contribution": "100.00",
        "expected_return_rate": "0",
        "return_type": "NOMINAL",
        "output_mode": "NOMINAL",
        "horizon_months": 2,
        "rate_basis": "EFFECTIVE_ANNUAL",
        "contribution_timing": "END_OF_MONTH",
    },
}


@pytest.mark.parametrize("token_type", ["access", "refresh", "legacy"])
@pytest.mark.parametrize("consumer", ["planning", "profile", "financial-context"])
def test_shared_consumers_enforce_real_jwt_boundary(boundary, token_type, consumer):
    claims = _claims(type=token_type)
    if token_type == "legacy":
        del claims["type"]
    token = jwt.encode(claims, SECRET, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    if consumer == "planning":
        response = boundary.client.post("/api/v1/planning/projection", headers=headers, json=PROJECTION)
    elif consumer == "profile":
        response = boundary.client.get("/api/v1/profile/context", headers=headers)
    else:
        response = boundary.client.get("/api/v1/financial-context/income-candidates", headers=headers)

    if token_type == "refresh":
        _assert_unauthorized(response)
        boundary.repository.get_by_id.assert_not_awaited()
        boundary.service.get_context.assert_not_called()
        boundary.income_service.list_candidates.assert_not_called()
    else:
        assert response.status_code == 200, response.text
        boundary.repository.get_by_id.assert_awaited_once_with(USER_ID)
        if consumer == "planning":
            assert response.json()["final_wealth"] == "1100.00"
        elif consumer == "financial-context":
            assert response.json() == {"as_of_date": "2026-10-29", "candidates": []}


def test_login_keeps_dto_and_issued_tokens_work_at_boundary(boundary, caplog):
    caplog.set_level("DEBUG")
    response = boundary.client.post(
        "/api/v1/auth/login",
        json={"email": boundary.user.email, "password": "synthetic-password"},
    )
    assert response.status_code == 200
    body = response.json()
    expected_fields = {"access_token", "refresh_token", "token_type", "expires_in", "user"}
    assert {field.name for field in fields(AuthTokenDTO)} == expected_fields
    assert set(body) == expected_fields
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600
    assert set(body["user"]) == {
        "id", "email", "name", "role", "is_active", "is_verified", "created_at", "last_login_at",
    }
    assert body["user"]["id"] == str(USER_ID)
    assert boundary.issuer.verify_token(body["access_token"])["type"] == "access"
    assert boundary.issuer.verify_token(body["refresh_token"])["type"] == "refresh"
    assert _request(boundary, body["access_token"]).status_code == 200
    _assert_unauthorized(_request(boundary, body["refresh_token"]))
    boundary.hasher.verify_password.assert_called_once_with(
        plain_password="synthetic-password", hashed_password=boundary.user.hashed_password,
    )
    boundary.repository.update_last_login.assert_awaited_once()
    for sensitive in (SECRET, "synthetic-password", boundary.user.hashed_password,
                      body["access_token"], body["refresh_token"]):
        assert sensitive not in caplog.text


@pytest.mark.parametrize("failure", ["wrong-password", "unknown-user", "inactive", "unverified"])
def test_login_failure_policies_are_preserved(boundary, failure):
    if failure == "wrong-password":
        boundary.hasher.verify_password.return_value = False
    elif failure == "unknown-user":
        boundary.repository.get_by_email.return_value = None
    elif failure == "inactive":
        boundary.user.is_active = False
    else:
        boundary.user.is_verified = False
    response = boundary.client.post(
        "/api/v1/auth/login", json={"email": boundary.user.email, "password": "synthetic-password"},
    )
    assert response.status_code == (401 if failure in {"wrong-password", "unknown-user"} else 403)
    assert set(response.json()) == {"detail"}
    boundary.repository.update_last_login.assert_not_awaited()


def test_auth_errors_do_not_expose_payload_or_secrets(boundary, caplog):
    caplog.set_level("DEBUG")
    token = _signed(sub="private-invalid-identity", financial_context="private-financial-canary")
    response = _request(boundary, token)
    _assert_unauthorized(response)
    for sensitive in (SECRET, token, "private-invalid-identity", "private-financial-canary",
                      boundary.user.hashed_password, boundary.user.email):
        assert sensitive not in response.text
        assert sensitive not in caplog.text
