from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.application.exceptions.smart_context_ownership_error import (
    SmartContextOwnershipUnavailableError,
)
from backend.application.services.single_tenant_user_scope import (
    SingleTenantUserScopeGuard,
)
from backend.database.base import Base
from backend.domain.enums.user_role import UserRole
from backend.infrastructure.persistence.models.user import UserModel


@pytest.fixture
def ownership_db():
    engine = create_engine("sqlite:///:memory:")
    event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine, tables=[UserModel.__table__])
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _user(user_id):
    return UserModel(
        id=user_id,
        email=f"{user_id.hex}@example.test",
        name="Context Owner",
        hashed_password="not-used",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime(2026, 10, 5, 9, 0, 0),
        last_login_at=None,
    )


def test_guard_resolves_the_authenticated_exact_single_user(ownership_db):
    owner = uuid4()
    ownership_db.add(_user(owner))
    ownership_db.commit()

    scope = SingleTenantUserScopeGuard().resolve(ownership_db, owner)

    assert scope.user_id == owner


def test_guard_rejects_wrong_authenticated_user_without_enumerating_owner(ownership_db):
    owner = uuid4()
    ownership_db.add(_user(owner))
    ownership_db.commit()

    with pytest.raises(SmartContextOwnershipUnavailableError):
        SingleTenantUserScopeGuard().resolve(ownership_db, uuid4())


@pytest.mark.parametrize("user_count", [0, 2])
def test_guard_fails_closed_for_zero_or_ambiguous_users(ownership_db, user_count):
    for _ in range(user_count):
        ownership_db.add(_user(uuid4()))
    ownership_db.commit()

    with pytest.raises(SmartContextOwnershipUnavailableError):
        SingleTenantUserScopeGuard().resolve(ownership_db, uuid4())
