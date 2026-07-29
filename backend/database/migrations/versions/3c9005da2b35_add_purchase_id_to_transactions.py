"""add_purchase_id_to_transactions

Revision ID: 3c9005da2b35
Revises: c0d10051bdcd
Create Date: 2026-07-25 00:48:27.833255
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3c9005da2b35'
down_revision = 'c0d10051bdcd'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('transactions', sa.Column('purchase_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_transactions_purchase_id'), 'transactions', ['purchase_id'], unique=False)

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_transactions_purchase_id'), table_name='transactions')
    op.drop_column('transactions', 'purchase_id')
