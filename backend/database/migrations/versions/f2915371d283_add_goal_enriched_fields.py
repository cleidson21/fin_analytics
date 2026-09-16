"""add_goal_enriched_fields

Revision ID: f2915371d283
Revises: 183e77495632
Create Date: 2026-09-09 18:37:00.000000

Lote 10.1 — Goal Domain Foundation
Adiciona colunas à tabela `goals` para suportar o módulo de Metas do Wealth Intelligence.

Colunas adicionadas:
  current_amount       — valor atual da meta (manual, nullable)
  priority             — prioridade da meta (1–5, nullable)
  monthly_contribution — aporte mensal planejado (nullable)
  linked_account_id    — referência textual a uma conta (sem FK, nullable)
  assumptions_json     — JSON de premissas para uso em 10.3 (nullable)

Não altera tabelas fora de `goals`.
Não modifica colunas existentes.
Possui downgrade completo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2915371d283'
down_revision: Union[str, Sequence[str], None] = '183e77495632'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona os campos enriquecidos ao módulo de Metas (Lote 10.1)."""
    with op.batch_alter_table('goals', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'current_amount',
            sa.Numeric(precision=18, scale=2),
            nullable=True,
            comment='Valor atual da meta, informado manualmente pelo usuário. NULL = não informado.'
        ))
        batch_op.add_column(sa.Column(
            'priority',
            sa.Integer(),
            nullable=True,
            comment='Prioridade da meta: 1 (mais alta) a 5 (mais baixa). NULL = não definida.'
        ))
        batch_op.add_column(sa.Column(
            'monthly_contribution',
            sa.Numeric(precision=18, scale=2),
            nullable=True,
            comment='Aporte mensal planejado para a meta. NULL = não informado.'
        ))
        batch_op.add_column(sa.Column(
            'linked_account_id',
            sa.String(length=255),
            nullable=True,
            comment='Referência textual a uma conta ou carteira. Sem FK formal. Preparação para 10.3/10.5.'
        ))
        batch_op.add_column(sa.Column(
            'assumptions_json',
            sa.Text(),
            nullable=True,
            comment='JSON com premissas para projeções futuras (Lote 10.3). Armazenado como string.'
        ))


def downgrade() -> None:
    """Remove os campos adicionados pelo Lote 10.1."""
    with op.batch_alter_table('goals', schema=None) as batch_op:
        batch_op.drop_column('assumptions_json')
        batch_op.drop_column('linked_account_id')
        batch_op.drop_column('monthly_contribution')
        batch_op.drop_column('priority')
        batch_op.drop_column('current_amount')
