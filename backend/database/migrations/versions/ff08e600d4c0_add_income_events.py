"""add_income_events

Revision ID: ff08e600d4c0
Revises: 3040122bee4b
Create Date: 2026-08-30 20:32:48.740770

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff08e600d4c0'
down_revision: Union[str, Sequence[str], None] = '3040122bee4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'income_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('account_id', sa.String(length=36), nullable=False),
        sa.Column('asset_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('ex_date', sa.Date(), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('value_per_unit', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('gross_amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('yoc', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('dy', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'asset_id', 'event_type', 'payment_date', 'ex_date', 'gross_amount', name='uq_income_event_identity')
    )
    op.create_index(op.f('ix_income_events_account_id'), 'income_events', ['account_id'], unique=False)
    op.create_index(op.f('ix_income_events_asset_id'), 'income_events', ['asset_id'], unique=False)
    op.create_index(op.f('ix_income_events_id'), 'income_events', ['id'], unique=False)
    op.create_index(op.f('ix_income_events_payment_date'), 'income_events', ['payment_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_income_events_payment_date'), table_name='income_events')
    op.drop_index(op.f('ix_income_events_id'), table_name='income_events')
    op.drop_index(op.f('ix_income_events_asset_id'), table_name='income_events')
    op.drop_index(op.f('ix_income_events_account_id'), table_name='income_events')
    op.drop_table('income_events')
