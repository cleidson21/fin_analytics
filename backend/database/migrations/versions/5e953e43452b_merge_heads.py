"""Merge heads

Revision ID: 5e953e43452b
Revises: 08aabd3f3f30, 8a1fe46d6dcc
Create Date: 2026-08-30 11:02:26.332669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e953e43452b'
down_revision: Union[str, Sequence[str], None] = ('08aabd3f3f30', '8a1fe46d6dcc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
