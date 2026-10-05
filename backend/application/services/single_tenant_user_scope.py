from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.application.exceptions.smart_context_ownership_error import (
    SmartContextOwnershipInconsistentError,
    SmartContextOwnershipUnavailableError,
)
from backend.infrastructure.persistence.models.user import UserModel


@dataclass(frozen=True)
class OwnedUserScope:
    """Server-resolved ownership scope passed to user-owned repositories."""

    user_id: UUID


class SingleTenantUserScopeGuard:
    """Fail closed unless current_user is the database's exact single user."""

    def resolve(self, db: Session, current_user_id: UUID) -> OwnedUserScope:
        current_user = self._as_uuid(current_user_id, "current_user_id")
        stored_users = tuple(db.execute(select(UserModel.id)).scalars())

        if len(stored_users) != 1:
            raise SmartContextOwnershipUnavailableError(
                "The local single-user ownership invariant is not satisfied."
            )

        stored_user = self._as_uuid(stored_users[0], "stored_user_id")
        if stored_user != current_user:
            raise SmartContextOwnershipUnavailableError(
                "The authenticated user does not own the local financial scope."
            )

        return OwnedUserScope(user_id=stored_user)

    @staticmethod
    def _as_uuid(value: object, field_name: str) -> UUID:
        try:
            return value if isinstance(value, UUID) else UUID(str(value))
        except (AttributeError, TypeError, ValueError) as error:
            raise SmartContextOwnershipInconsistentError(
                f"{field_name} is not a valid UUID."
            ) from error
