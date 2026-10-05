from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from backend.application.services.single_tenant_user_scope import (
    SingleTenantUserScopeGuard,
)
from backend.domains.smart_context import DeclaredFinancialContext
from backend.infrastructure.persistence.repositories.smart_context import (
    DeclaredContextRepository,
)


class ProfileDeclaredContextService:
    """Authenticated application boundary for declared Profile context only."""

    def __init__(
        self,
        ownership_guard: SingleTenantUserScopeGuard | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._ownership_guard = ownership_guard or SingleTenantUserScopeGuard()
        self._clock = clock or datetime.utcnow

    def get_context(
        self,
        db: Session,
        current_user_id: UUID,
    ) -> DeclaredFinancialContext | None:
        owner = self._ownership_guard.resolve(db, current_user_id)
        return DeclaredContextRepository(db, owner).get()

    def update_context(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        declared_monthly_gross_income: Decimal | None,
        income_as_of_date: date | None,
    ) -> DeclaredFinancialContext:
        owner = self._ownership_guard.resolve(db, current_user_id)
        repository = DeclaredContextRepository(db, owner)
        changed_at = self._clock()
        if declared_monthly_gross_income is None:
            return repository.clear(at=changed_at)
        return repository.save(
            declared_monthly_gross_income=declared_monthly_gross_income,
            income_as_of_date=income_as_of_date,
            at=changed_at,
        )
