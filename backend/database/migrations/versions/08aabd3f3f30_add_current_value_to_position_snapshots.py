"""add_current_value_to_position_snapshots

Revision ID: 08aabd3f3f30
Revises: a1b2c3d4e5f6
Create Date: 2026-08-28 20:36:08.146991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08aabd3f3f30'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('position_snapshots', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_value', sa.Numeric(precision=18, scale=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('position_snapshots', schema=None) as batch_op:
        batch_op.drop_column('current_value')
