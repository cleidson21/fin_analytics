"""HTTP containment on mounted legacy routes; disposable SQLite, no provider I/O."""

import sqlite3
import socket
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.api.dependencies import auth
from backend.api.dependencies.database import get_db_session
from backend.domain.enums.user_role import UserRole
from backend.domains.pierre import read_router, router as import_router, service
from backend.domains.pierre.models import Account, Category, LegacyBase, Transaction
from backend.infrastructure.persistence.models.user import UserModel
from backend.infrastructure.security.jwt_service import JWTService
from backend.main import app


SECRET = "synthetic-legacy-route-secret-no-production-value"
USER_A = UUID("00000000-0000-0000-0000-000000008101")
USER_B = UUID("00000000-0000-0000-0000-000000008102")
INACTIVE = UUID("00000000-0000-0000-0000-000000008103")
MISSING = UUID("00000000-0000-0000-0000-000000008199")
OPERATIONS = [
    ("GET", "/api/v1/accounts"),
    ("GET", "/api/v1/transactions"),
    ("GET", "/api/v1/categories"),
    ("GET", "/api/v1/dashboard"),
    ("POST", "/api/v1/pierre/import"),
]
DENIED = {"detail": "Legacy financial scope unavailable: ownership is not certified"}


@pytest.fixture
def boundary(tmp_path, monkeypatch, request):
    path = tmp_path / "synthetic-legacy.db"
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    LegacyBase.metadata.create_all(engine)
    UserModel.__table__.create(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as session:
        users = ((USER_A, True),) if getattr(request, "param", None) == 1 else (
            (USER_A, True), (USER_B, True), (INACTIVE, False)
        )
        for uid, active in users:
            session.add(UserModel(
                id=uid, email=f"synthetic-{uid.int}@example.test", name="Synthetic User",
                hashed_password="synthetic-unusable-hash", is_active=active,
                is_verified=True, role=UserRole.VIEWER, created_at=datetime(2026, 1, 1),
            ))
        # These scopes are intentionally NOT attributed to users: the schema cannot do so.
        for suffix in ("a", "b"):
            session.add(Account(provider="synthetic", external_id=f"account-{suffix}",
                                name=f"Private synthetic account {suffix}", type="CHECKING"))
            session.add(Category(provider="synthetic", name=f"Private category {suffix}"))
        session.flush()
        for suffix in ("a", "b"):
            session.add(Transaction(
                provider="synthetic", external_id=f"transaction-{suffix}",
                account_provider="synthetic", account_external_id=f"account-{suffix}",
                description=f"Private synthetic transaction {suffix}", amount=Decimal("12.34"),
                currency="BRL", date=datetime(2026, 1, 1), status="POSTED", type="DEBIT",
                manual_transaction=False,
            ))
        session.commit()

    def snapshot():
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
            return tuple(db.iterdump())

    before = snapshot()
    engine.dispose()
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{path.as_posix()}")
    async_sessions = async_sessionmaker(async_engine, expire_on_commit=False)
    statements = []

    def read_only_connection(connection, _record):
        connection.execute("PRAGMA query_only=ON")

    def track_sql(_conn, _cursor, statement, _params, _context, _many):
        statements.append(statement)
        assert statement.lstrip().split()[0].upper() in {"SELECT", "PRAGMA"}

    for target in (engine, async_engine.sync_engine):
        event.listen(target, "connect", read_only_connection)
        event.listen(target, "before_cursor_execute", track_sql)

    async def isolated_auth_session():
        async with async_sessions() as session:
            yield session

    monkeypatch.setattr(app, "dependency_overrides", {get_db_session: isolated_auth_session})
    monkeypatch.setattr(auth, "settings", SimpleNamespace(JWT_SECRET=SECRET))
    monkeypatch.setattr(service, "SessionLocal", sessions)
    monkeypatch.setattr(read_router, "SessionLocal", sessions)
    account_factory = Mock(wraps=read_router.AccountService)
    transaction_factory = Mock(wraps=read_router.TransactionService)
    category_factory = Mock(wraps=read_router.CategoryService)
    monkeypatch.setattr(read_router, "AccountService", account_factory)
    monkeypatch.setattr(read_router, "TransactionService", transaction_factory)
    monkeypatch.setattr(read_router, "CategoryService", category_factory)
    pipeline = SimpleNamespace(run=AsyncMock(return_value={}))
    pipeline_factory = Mock(return_value=pipeline)
    monkeypatch.setattr(import_router, "PierreImportPipeline", pipeline_factory)
    # A second tripwire prevents real connector construction, including through future wiring.
    monkeypatch.setattr("backend.domains.pierre.pipeline.PierreConnector",
                        Mock(side_effect=AssertionError("Real Pierre connector is forbidden")))
    monkeypatch.setattr(socket, "create_connection",
                        Mock(side_effect=AssertionError("External connections are forbidden")))
    assert auth.get_current_user not in app.dependency_overrides
    with TestClient(app, raise_server_exceptions=False) as client:
        yield SimpleNamespace(
            client=client, issuer=JWTService(SECRET, 60, 7), statements=statements,
            factories=(account_factory, transaction_factory, category_factory, pipeline_factory),
            pipeline=pipeline,
        )
        # Dispose async resources on the same event loop as the HTTP auth session.
        client.portal.call(async_engine.dispose)
    assert snapshot() == before, "HTTP tests must not modify synthetic financial or user rows"
    engine.dispose()


def request(boundary, operation, token=None, **kwargs):
    method, path = operation
    headers = {} if token is None else {"Authorization": f"Bearer {token}"}
    if method == "POST":
        kwargs.setdefault("json", {})
    return boundary.client.request(method, path, headers=headers, **kwargs)


def assert_no_financial_execution(boundary):
    for factory in boundary.factories:
        factory.assert_not_called()
    boundary.pipeline.run.assert_not_awaited()
    assert all("users" in sql.lower() for sql in boundary.statements)


@pytest.mark.parametrize("operation", OPERATIONS, ids=[p for _, p in OPERATIONS])
@pytest.mark.parametrize("credential", ["missing", "invalid", "refresh", "unknown-user", "inactive"])
def test_credential_gate(boundary, operation, credential):
    tokens = {
        "missing": None,
        "invalid": "synthetic-invalid-token",
        "refresh": boundary.issuer.create_refresh_token(str(USER_A)),
        "unknown-user": boundary.issuer.create_access_token(str(MISSING)),
        "inactive": boundary.issuer.create_access_token(str(INACTIVE)),
    }
    response = request(boundary, operation, tokens[credential])
    assert response.status_code == (400 if credential == "inactive" else 401)
    if credential != "inactive":
        assert response.headers["www-authenticate"] == "Bearer"
    assert_no_financial_execution(boundary)


@pytest.mark.parametrize("operation", OPERATIONS, ids=[p for _, p in OPERATIONS])
@pytest.mark.parametrize("user_id", [USER_A, USER_B])
@pytest.mark.parametrize("legacy", [False, True], ids=["access", "legacy-access"])
def test_authenticated_users_cannot_access_unowned_ledger(boundary, operation, user_id, legacy):
    if legacy:
        token = jwt.encode({"sub": str(user_id), "exp": int(datetime.now(timezone.utc).timestamp()) + 3600},
                           SECRET, algorithm="HS256")
    else:
        token = boundary.issuer.create_access_token(str(user_id))
    response = request(boundary, operation, token)
    assert response.status_code == 403
    assert response.json() == DENIED
    assert_no_financial_execution(boundary)


@pytest.mark.parametrize("operation", OPERATIONS, ids=[p for _, p in OPERATIONS])
@pytest.mark.parametrize("boundary", [1], indirect=True)
def test_one_user_is_not_automatically_owner(boundary, operation):
    response = request(boundary, operation, boundary.issuer.create_access_token(str(USER_A)))
    assert response.status_code == 403
    assert response.json() == DENIED
    assert_no_financial_execution(boundary)


@pytest.mark.parametrize("payload", [{}, {"start_date": "2026-01-01", "end_date": "2026-01-31"}, None])
def test_import_denial_precedes_pipeline_even_with_invalid_body(boundary, payload):
    response = request(boundary, OPERATIONS[-1], json=payload)
    assert response.status_code == 401
    assert_no_financial_execution(boundary)


def test_openapi_declares_existing_oauth_scheme_for_all_five_operations():
    schema = app.openapi()
    for method, path in OPERATIONS:
        assert schema["paths"][path][method.lower()]["security"] == [{"OAuth2PasswordBearer": []}]
    assert schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["type"] == "oauth2"
