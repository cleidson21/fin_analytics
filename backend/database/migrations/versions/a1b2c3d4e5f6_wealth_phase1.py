"""wealth_phase1_assets_and_position_snapshots

Revision ID: a1b2c3d4e5f6
Revises: 3c9005da2b35
Create Date: 2026-08-25 19:30:00.000000

Fase 1 — Persistência MyProfit Ativos
- Cria tabela `assets` (catálogo mestre de ativos investíveis)
- Cria tabela `position_snapshots` (snapshots patrimoniais por conta/ativo/data)
- Amplia coluna `sync_logs.provider` de VARCHAR(8) para VARCHAR(32)
  para acomodar os novos subtipos MYPROFIT_ATIVOS, MYPROFIT_EVOLUCAO, MYPROFIT_PROVENTOS
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3c9005da2b35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — Fase 1 Wealth (MYPROFIT_ATIVOS)."""

    # --------------------------------------------------------------------------
    # 1. Criar tabela `assets`
    # --------------------------------------------------------------------------
    op.create_table(
        'assets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('ticker', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('asset_class', sa.String(), nullable=False),
        sa.Column('sector', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('yfinance_ticker', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('is_active', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticker', name='uq_assets_ticker'),
    )
    op.create_index(op.f('ix_assets_ticker'), 'assets', ['ticker'], unique=True)
    op.create_index(op.f('ix_assets_asset_class'), 'assets', ['asset_class'], unique=False)

    # --------------------------------------------------------------------------
    # 2. Criar tabela `position_snapshots`
    # --------------------------------------------------------------------------
    op.create_table(
        'position_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('account_id', sa.String(length=36), nullable=False),
        sa.Column('asset_id', sa.String(length=36), nullable=False),
        sa.Column('reference_date', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('avg_price', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.Column('is_manual', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], name='fk_position_snapshots_asset_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'account_id', 'asset_id', 'reference_date',
            name='uq_position_snapshot_account_asset_date'
        ),
    )
    op.create_index(op.f('ix_position_snapshots_account_id'), 'position_snapshots', ['account_id'], unique=False)
    op.create_index(op.f('ix_position_snapshots_asset_id'), 'position_snapshots', ['asset_id'], unique=False)
    op.create_index(op.f('ix_position_snapshots_reference_date'), 'position_snapshots', ['reference_date'], unique=False)
    op.create_index(op.f('ix_position_snapshots_run_id'), 'position_snapshots', ['run_id'], unique=False)

    # --------------------------------------------------------------------------
    # 3. Ampliar sync_logs.provider para VARCHAR(32)
    # SQLite não suporta ALTER COLUMN diretamente — recriar a tabela.
    # Abordagem: renomear → recriar → migrar dados → dropar antiga.
    # --------------------------------------------------------------------------
    op.execute("ALTER TABLE sync_logs RENAME TO sync_logs_old")

    op.create_table(
        'sync_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),   # ampliado de 8 → 32
        sa.Column('status', sa.String(length=16), nullable=False),     # ampliado de 7 → 16
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('accounts_synced', sa.Integer(), nullable=True),
        sa.Column('transactions_synced', sa.Integer(), nullable=True),
        sa.Column('categories_synced', sa.Integer(), nullable=True),
        sa.Column('inserted', sa.Integer(), nullable=True),
        sa.Column('updated', sa.Integer(), nullable=True),
        sa.Column('ignored', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('provider_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.execute("""
        INSERT INTO sync_logs (
            id, user_id, provider, status, start_time, end_time,
            duration_seconds, accounts_synced, transactions_synced,
            categories_synced, inserted, updated, ignored,
            error_message, provider_metadata
        )
        SELECT
            id, user_id, provider, status, start_time, end_time,
            duration_seconds, accounts_synced, transactions_synced,
            categories_synced, inserted, updated, ignored,
            error_message, provider_metadata
        FROM sync_logs_old
    """)

    op.execute("DROP TABLE sync_logs_old")


def downgrade() -> None:
    """Downgrade schema — reverter Fase 1 Wealth."""

    # Remover position_snapshots
    op.drop_index(op.f('ix_position_snapshots_run_id'), table_name='position_snapshots')
    op.drop_index(op.f('ix_position_snapshots_reference_date'), table_name='position_snapshots')
    op.drop_index(op.f('ix_position_snapshots_asset_id'), table_name='position_snapshots')
    op.drop_index(op.f('ix_position_snapshots_account_id'), table_name='position_snapshots')
    op.drop_table('position_snapshots')

    # Remover assets
    op.drop_index(op.f('ix_assets_asset_class'), table_name='assets')
    op.drop_index(op.f('ix_assets_ticker'), table_name='assets')
    op.drop_table('assets')

    # Reverter sync_logs (recriar com VARCHAR(8) original)
    op.execute("ALTER TABLE sync_logs RENAME TO sync_logs_new")

    op.create_table(
        'sync_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=8), nullable=False),
        sa.Column('status', sa.String(length=7), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('accounts_synced', sa.Integer(), nullable=True),
        sa.Column('transactions_synced', sa.Integer(), nullable=True),
        sa.Column('categories_synced', sa.Integer(), nullable=True),
        sa.Column('inserted', sa.Integer(), nullable=True),
        sa.Column('updated', sa.Integer(), nullable=True),
        sa.Column('ignored', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('provider_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.execute("""
        INSERT INTO sync_logs
        SELECT * FROM sync_logs_new
        WHERE length(provider) <= 8 AND length(status) <= 7
    """)

    op.execute("DROP TABLE sync_logs_new")
