from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


class IncomeCurrency(str, Enum):
    BRL = "BRL"


class IncomePeriod(str, Enum):
    MONTHLY = "MONTHLY"


class IncomeBasis(str, Enum):
    GROSS = "GROSS"


class RecurringIncomeDecisionState(str, Enum):
    CONFIRMED_AS_INCOME = "CONFIRMED_AS_INCOME"
    REJECTED = "REJECTED"


def _require_cent_scale(value: Decimal) -> None:
    if type(value) is not Decimal:
        raise TypeError("Financial values must be Decimal.")
    if not value.is_finite() or value <= Decimal("0"):
        raise ValueError("Declared monthly gross income must be positive and finite.")
    if value.as_tuple().exponent < -2:
        raise ValueError("Declared monthly gross income must use cent scale.")


@dataclass(frozen=True)
class DeclaredFinancialContext:
    user_id: UUID
    declared_monthly_gross_income: Decimal | None
    currency: IncomeCurrency | None
    income_period: IncomePeriod | None
    income_basis: IncomeBasis | None
    income_as_of_date: date | None
    declared_at: datetime | None
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.declared_monthly_gross_income is None:
            semantic_values = (
                self.currency,
                self.income_period,
                self.income_basis,
                self.income_as_of_date,
                self.declared_at,
            )
            if any(value is not None for value in semantic_values):
                raise ValueError("A cleared declaration cannot retain semantic metadata.")
            return

        _require_cent_scale(self.declared_monthly_gross_income)
        if self.currency is not IncomeCurrency.BRL:
            raise ValueError("Declared income currency must be BRL.")
        if self.income_period is not IncomePeriod.MONTHLY:
            raise ValueError("Declared income period must be MONTHLY.")
        if self.income_basis is not IncomeBasis.GROSS:
            raise ValueError("Declared income basis must be GROSS.")
        if self.declared_at is None:
            raise ValueError("A declared income value requires declared_at provenance.")


@dataclass(frozen=True)
class RecurringIncomeDecision:
    id: UUID
    user_id: UUID
    source_provider: str
    source_account_scope: str
    source_signature: str
    signature_version: int
    decision: RecurringIncomeDecisionState
    label: str | None
    decided_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.source_provider.strip():
            raise ValueError("Source provider is required.")
        if not self.source_account_scope.strip():
            raise ValueError("Source account scope is required.")
        if not self.source_signature.strip():
            raise ValueError("Source signature is required.")
        if self.signature_version < 1:
            raise ValueError("Signature version must be positive.")
        if self.label is not None and len(self.label) > 100:
            raise ValueError("Decision label must contain at most 100 characters.")
