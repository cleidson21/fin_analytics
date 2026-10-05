from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from backend.application.services.single_tenant_user_scope import OwnedUserScope
from backend.domains.smart_context import (
    DeclaredFinancialContext,
    IncomeBasis,
    IncomeCurrency,
    IncomePeriod,
    RecurringIncomeDecision,
    RecurringIncomeDecisionState,
)
from backend.infrastructure.persistence.models.smart_context import (
    DeclaredFinancialContextModel,
    RecurringIncomeDecisionModel,
)


class DeclaredContextRepository:
    """Caller-transactional storage for the server-resolved current user."""

    def __init__(self, db: Session, owner: OwnedUserScope) -> None:
        self._db = db
        self._owner = owner

    def get(self) -> DeclaredFinancialContext | None:
        row = self._db.execute(
            select(DeclaredFinancialContextModel.__table__).where(
                DeclaredFinancialContextModel.user_id == self._owner.user_id
            )
        ).mappings().one_or_none()
        return self._to_domain(row) if row is not None else None

    def save(
        self,
        *,
        declared_monthly_gross_income: Decimal | None,
        income_as_of_date: date | None,
        at: datetime,
    ) -> DeclaredFinancialContext:
        if declared_monthly_gross_income is None:
            if income_as_of_date is not None:
                raise ValueError("A cleared declaration cannot retain an as-of date.")
            values = {
                "declared_monthly_gross_income": None,
                "currency": None,
                "income_period": None,
                "income_basis": None,
                "income_as_of_date": None,
                "declared_at": None,
            }
        else:
            candidate = DeclaredFinancialContext(
                user_id=self._owner.user_id,
                declared_monthly_gross_income=declared_monthly_gross_income,
                currency=IncomeCurrency.BRL,
                income_period=IncomePeriod.MONTHLY,
                income_basis=IncomeBasis.GROSS,
                income_as_of_date=income_as_of_date,
                declared_at=at,
                updated_at=at,
            )
            values = {
                "declared_monthly_gross_income": candidate.declared_monthly_gross_income,
                "currency": candidate.currency.value,
                "income_period": candidate.income_period.value,
                "income_basis": candidate.income_basis.value,
                "income_as_of_date": candidate.income_as_of_date,
                "declared_at": candidate.declared_at,
            }

        statement = sqlite_insert(DeclaredFinancialContextModel.__table__).values(
            user_id=self._owner.user_id,
            updated_at=at,
            **values,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[DeclaredFinancialContextModel.user_id],
            set_={**values, "updated_at": at},
        )
        self._db.execute(statement)
        persisted = self.get()
        if persisted is None:
            raise RuntimeError("Declared context write did not persist a row.")
        return persisted

    def clear(self, *, at: datetime) -> DeclaredFinancialContext:
        return self.save(
            declared_monthly_gross_income=None,
            income_as_of_date=None,
            at=at,
        )

    @staticmethod
    def _to_domain(row: object) -> DeclaredFinancialContext:
        return DeclaredFinancialContext(
            user_id=row["user_id"],
            declared_monthly_gross_income=row["declared_monthly_gross_income"],
            currency=IncomeCurrency(row["currency"]) if row["currency"] else None,
            income_period=IncomePeriod(row["income_period"]) if row["income_period"] else None,
            income_basis=IncomeBasis(row["income_basis"]) if row["income_basis"] else None,
            income_as_of_date=row["income_as_of_date"],
            declared_at=row["declared_at"],
            updated_at=row["updated_at"],
        )


class RecurringIncomeDecisionRepository:
    """Stores decisions only; candidate evidence remains computed on read."""

    def __init__(self, db: Session, owner: OwnedUserScope) -> None:
        self._db = db
        self._owner = owner

    def get(
        self,
        *,
        source_signature: str,
        signature_version: int,
    ) -> RecurringIncomeDecision | None:
        row = self._db.execute(
            select(RecurringIncomeDecisionModel.__table__).where(
                RecurringIncomeDecisionModel.user_id == self._owner.user_id,
                RecurringIncomeDecisionModel.source_signature == source_signature,
                RecurringIncomeDecisionModel.signature_version == signature_version,
            )
        ).mappings().one_or_none()
        return self._to_domain(row) if row is not None else None

    def list_all(self) -> tuple[RecurringIncomeDecision, ...]:
        rows = self._db.execute(
            select(RecurringIncomeDecisionModel.__table__)
            .where(RecurringIncomeDecisionModel.user_id == self._owner.user_id)
            .order_by(
                RecurringIncomeDecisionModel.updated_at.desc(),
                RecurringIncomeDecisionModel.source_signature.asc(),
                RecurringIncomeDecisionModel.signature_version.asc(),
            )
        ).mappings()
        return tuple(self._to_domain(row) for row in rows)

    def save(
        self,
        *,
        source_provider: str,
        source_account_scope: str,
        source_signature: str,
        signature_version: int,
        decision: RecurringIncomeDecisionState,
        label: str | None,
        at: datetime,
    ) -> RecurringIncomeDecision:
        existing = self.get(
            source_signature=source_signature,
            signature_version=signature_version,
        )
        if existing is not None and (
            existing.source_provider != source_provider
            or existing.source_account_scope != source_account_scope
        ):
            raise ValueError("A decision identity cannot change its resolved source scope.")

        candidate = RecurringIncomeDecision(
            id=existing.id if existing is not None else uuid4(),
            user_id=self._owner.user_id,
            source_provider=source_provider,
            source_account_scope=source_account_scope,
            source_signature=source_signature,
            signature_version=signature_version,
            decision=decision,
            label=label,
            decided_at=at,
            updated_at=at,
        )
        statement = sqlite_insert(RecurringIncomeDecisionModel.__table__).values(
            id=candidate.id,
            user_id=candidate.user_id,
            source_provider=candidate.source_provider,
            source_account_scope=candidate.source_account_scope,
            source_signature=candidate.source_signature,
            signature_version=candidate.signature_version,
            decision=candidate.decision.value,
            label=candidate.label,
            decided_at=candidate.decided_at,
            updated_at=candidate.updated_at,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[
                RecurringIncomeDecisionModel.user_id,
                RecurringIncomeDecisionModel.source_signature,
                RecurringIncomeDecisionModel.signature_version,
            ],
            set_={
                "decision": candidate.decision.value,
                "label": candidate.label,
                "decided_at": candidate.decided_at,
                "updated_at": candidate.updated_at,
            },
        )
        self._db.execute(statement)
        persisted = self.get(
            source_signature=source_signature,
            signature_version=signature_version,
        )
        if persisted is None:
            raise RuntimeError("Recurring-income decision write did not persist a row.")
        return persisted

    def reset(self, *, source_signature: str, signature_version: int) -> bool:
        result = self._db.execute(
            delete(RecurringIncomeDecisionModel.__table__).where(
                RecurringIncomeDecisionModel.user_id == self._owner.user_id,
                RecurringIncomeDecisionModel.source_signature == source_signature,
                RecurringIncomeDecisionModel.signature_version == signature_version,
            )
        )
        return bool(result.rowcount)

    @staticmethod
    def _to_domain(row: object) -> RecurringIncomeDecision:
        return RecurringIncomeDecision(
            id=row["id"],
            user_id=row["user_id"],
            source_provider=row["source_provider"],
            source_account_scope=row["source_account_scope"],
            source_signature=row["source_signature"],
            signature_version=row["signature_version"],
            decision=RecurringIncomeDecisionState(row["decision"]),
            label=row["label"],
            decided_at=row["decided_at"],
            updated_at=row["updated_at"],
        )
