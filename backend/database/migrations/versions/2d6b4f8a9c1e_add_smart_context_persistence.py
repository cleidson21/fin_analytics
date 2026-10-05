"""add_smart_context_persistence

Revision ID: 2d6b4f8a9c1e
Revises: f2915371d283
Create Date: 2026-10-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2d6b4f8a9c1e"
down_revision: Union[str, Sequence[str], None] = "f2915371d283"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_declared_financial_context",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "declared_monthly_gross_income",
            sa.Numeric(precision=18, scale=2),
            nullable=True,
        ),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("income_period", sa.String(length=16), nullable=True),
        sa.Column("income_basis", sa.String(length=16), nullable=True),
        sa.Column("income_as_of_date", sa.Date(), nullable=True),
        sa.Column("declared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "declared_monthly_gross_income IS NULL "
            "OR declared_monthly_gross_income > 0",
            name="ck_declared_context_positive_income",
        ),
        sa.CheckConstraint(
            "declared_monthly_gross_income IS NULL "
            "OR declared_monthly_gross_income = ROUND(declared_monthly_gross_income, 2)",
            name="ck_declared_context_cent_scale",
        ),
        sa.CheckConstraint(
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "recurring_income_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source_provider", sa.String(length=64), nullable=False),
        sa.Column("source_account_scope", sa.String(length=255), nullable=False),
        sa.Column("source_signature", sa.String(length=128), nullable=False),
        sa.Column("signature_version", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "signature_version > 0",
            name="ck_recurring_income_decision_signature_version",
        ),
        sa.CheckConstraint(
            "decision IN ('CONFIRMED_AS_INCOME', 'REJECTED')",
            name="ck_recurring_income_decision_state",
        ),
        sa.CheckConstraint(
            "LENGTH(TRIM(source_provider)) > 0",
            name="ck_recurring_income_decision_provider",
        ),
        sa.CheckConstraint(
            "LENGTH(TRIM(source_account_scope)) > 0",
            name="ck_recurring_income_decision_account_scope",
        ),
        sa.CheckConstraint(
            "LENGTH(TRIM(source_signature)) > 0",
            name="ck_recurring_income_decision_signature",
        ),
        sa.CheckConstraint(
            "label IS NULL OR LENGTH(label) <= 100",
            name="ck_recurring_income_decision_label_length",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "source_signature",
            "signature_version",
            name="uq_recurring_income_decision_identity",
        ),
    )
    op.create_index(
        "ix_recurring_income_decisions_user_id",
        "recurring_income_decisions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recurring_income_decisions_user_id",
        table_name="recurring_income_decisions",
    )
    op.drop_table("recurring_income_decisions")
    op.drop_table("user_declared_financial_context")
