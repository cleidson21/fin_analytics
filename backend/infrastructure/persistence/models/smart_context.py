from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class DeclaredFinancialContextModel(Base):
    __tablename__ = "user_declared_financial_context"
    __table_args__ = (
        CheckConstraint(
            "declared_monthly_gross_income IS NULL "
            "OR declared_monthly_gross_income > 0",
            name="ck_declared_context_positive_income",
        ),
        CheckConstraint(
            "declared_monthly_gross_income IS NULL "
            "OR declared_monthly_gross_income = ROUND(declared_monthly_gross_income, 2)",
            name="ck_declared_context_cent_scale",
        ),
        CheckConstraint(
            "(declared_monthly_gross_income IS NULL "
            "AND currency IS NULL "
            "AND income_period IS NULL "
            "AND income_basis IS NULL "
            "AND income_as_of_date IS NULL "
            "AND declared_at IS NULL) "
            "OR (declared_monthly_gross_income IS NOT NULL "
            "AND currency = 'BRL' "
            "AND income_period = 'MONTHLY' "
            "AND income_basis = 'GROSS' "
            "AND declared_at IS NOT NULL)",
            name="ck_declared_context_semantics",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        primary_key=True,
    )
    declared_monthly_gross_income: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    income_period: Mapped[str | None] = mapped_column(String(16), nullable=True)
    income_basis: Mapped[str | None] = mapped_column(String(16), nullable=True)
    income_as_of_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    declared_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class RecurringIncomeDecisionModel(Base):
    __tablename__ = "recurring_income_decisions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "source_signature",
            "signature_version",
            name="uq_recurring_income_decision_identity",
        ),
        CheckConstraint(
            "signature_version > 0",
            name="ck_recurring_income_decision_signature_version",
        ),
        CheckConstraint(
            "decision IN ('CONFIRMED_AS_INCOME', 'REJECTED')",
            name="ck_recurring_income_decision_state",
        ),
        CheckConstraint(
            "LENGTH(TRIM(source_provider)) > 0",
            name="ck_recurring_income_decision_provider",
        ),
        CheckConstraint(
            "LENGTH(TRIM(source_account_scope)) > 0",
            name="ck_recurring_income_decision_account_scope",
        ),
        CheckConstraint(
            "LENGTH(TRIM(source_signature)) > 0",
            name="ck_recurring_income_decision_signature",
        ),
        CheckConstraint(
            "label IS NULL OR LENGTH(label) <= 100",
            name="ck_recurring_income_decision_label_length",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    source_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    source_account_scope: Mapped[str] = mapped_column(String(255), nullable=False)
    source_signature: Mapped[str] = mapped_column(String(128), nullable=False)
    signature_version: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
