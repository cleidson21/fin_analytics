from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.application.services.single_tenant_user_scope import (
    OwnedUserScope,
    SingleTenantUserScopeGuard,
)
from backend.domains.pierre.models import Transaction
from backend.domains.smart_context.recurring_income import (
    RecurringIncomeDirection,
    RecurringIncomeObservation,
    RecurringIncomeRiskFlag,
    evidence_window_start,
)


_EXPLICIT_SAME_TITULARITY_CATEGORIES = frozenset(
    {"Transferência mesma titularidade"}
)
_GENERIC_TRANSFER_CATEGORIES = frozenset(
    {"Transferências", "Transferências para terceiros"}
)


def _opaque_key(namespace: str, *components: str) -> str:
    payload = json.dumps(
        [namespace, *components],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


class RecurringIncomeLedgerReader:
    """Bounded read adapter for eligible governed Pierre-ledger credits."""

    def __init__(
        self,
        ownership_guard: SingleTenantUserScopeGuard | None = None,
    ) -> None:
        self._ownership_guard = ownership_guard or SingleTenantUserScopeGuard()

    def read_eligible_observations(
        self,
        db: Session,
        current_user_id: UUID,
        *,
        as_of_date: date,
    ) -> tuple[RecurringIncomeObservation, ...]:
        owner = self._ownership_guard.resolve(db, current_user_id)
        return self.read_eligible_observations_for_scope(
            db,
            owner,
            as_of_date=as_of_date,
        )

    def read_eligible_observations_for_scope(
        self,
        db: Session,
        owner: OwnedUserScope,
        *,
        as_of_date: date,
    ) -> tuple[RecurringIncomeObservation, ...]:
        """Read only after the caller has resolved an owned server scope."""

        if not isinstance(owner, OwnedUserScope):
            raise TypeError("An owned user scope is required.")
        start_date = evidence_window_start(as_of_date)
        start_at = datetime.combine(start_date, time.min)
        end_at = datetime.combine(as_of_date + timedelta(days=1), time.min)

        rows = db.execute(
            select(
                Transaction.provider,
                Transaction.external_id,
                Transaction.account_provider,
                Transaction.account_external_id,
                Transaction.description,
                Transaction.amount,
                Transaction.currency,
                Transaction.date,
                Transaction.category,
            )
            .where(
                Transaction.governance_status == "CLASSIFIED",
                Transaction.economic_classification == "ENTRADA",
                Transaction.type == RecurringIncomeDirection.CREDIT.value,
                Transaction.amount > Decimal("0"),
                Transaction.date >= start_at,
                Transaction.date < end_at,
                Transaction.provider.is_not(None),
                Transaction.external_id.is_not(None),
                Transaction.account_provider.is_not(None),
                Transaction.account_external_id.is_not(None),
                Transaction.description.is_not(None),
                Transaction.currency.is_not(None),
                or_(
                    Transaction.investment_name.is_(None),
                    func.length(func.trim(Transaction.investment_name)) == 0,
                ),
                or_(
                    Transaction.category.is_(None),
                    Transaction.category.not_in(
                        _EXPLICIT_SAME_TITULARITY_CATEGORIES
                    ),
                ),
                func.length(func.trim(Transaction.provider)) > 0,
                func.length(func.trim(Transaction.external_id)) > 0,
                func.length(func.trim(Transaction.account_provider)) > 0,
                func.length(func.trim(Transaction.account_external_id)) > 0,
                func.length(func.trim(Transaction.description)) > 0,
                func.length(func.trim(Transaction.currency)) > 0,
            )
            .order_by(
                Transaction.date.asc(),
                Transaction.provider.asc(),
                Transaction.external_id.asc(),
            )
        ).all()

        observations = []
        for row in rows:
            risk_flags = (
                (RecurringIncomeRiskFlag.TRANSFER_AMBIGUITY,)
                if row.category in _GENERIC_TRANSFER_CATEGORIES
                else ()
            )
            observations.append(
                RecurringIncomeObservation(
                    source_record_key=_opaque_key(
                        "transaction",
                        row.provider,
                        row.external_id,
                    ),
                    provider=row.provider,
                    account_scope=_opaque_key(
                        "account",
                        row.account_provider,
                        row.account_external_id,
                    ),
                    currency=row.currency,
                    direction=RecurringIncomeDirection.CREDIT,
                    description=row.description,
                    amount=row.amount,
                    occurred_on=row.date.date(),
                    risk_flags=risk_flags,
                )
            )
        return tuple(observations)
