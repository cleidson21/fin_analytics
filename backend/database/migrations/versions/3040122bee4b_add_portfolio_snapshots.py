"""Add portfolio snapshots

Revision ID: 3040122bee4b
Revises: 5e953e43452b
Create Date: 2026-08-30 11:03:56.568651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3040122bee4b'
down_revision: Union[str, Sequence[str], None] = '5e953e43452b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'portfolio_snapshots',
        sa.Column('account_id', sa.String(length=36), nullable=False),
        sa.Column('reference_month', sa.String(length=7), nullable=False),
        sa.Column('patrimonio', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('pct_mensal', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('pct_acumulada', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('compras', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('vendas', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('op_finalizadas', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('proventos', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('ibov_mensal', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('ibov_acumulado', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('cdi_mensal', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('cdi_acumulado', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('ipca_mensal', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('ipca_acumulado', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('ifix_mensal', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('ifix_acumulado', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('sp_mensal', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('sp_acumulado', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('idiv_mensal', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('idiv_acumulado', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.Column('source_type', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('account_id', 'reference_month')
    )


def downgrade() -> None:
    op.drop_table('portfolio_snapshots')
