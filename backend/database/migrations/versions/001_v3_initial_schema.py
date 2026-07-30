"""V3 initial schema — accounts, transactions, categories, sync_state, sync_history

Revision ID: 001_v3_initial_schema
Revises:
Create Date: 2026-07-30

Schema canônico da Sprint 4.4.1 (FINANALYTICS V3).
Referência: docs/03_DATABASE.md e docs/60_ARCHITECTURE_REVISION_V31.md

Tabelas criadas:
  - accounts      (PK composta: provider + external_id)
  - transactions  (PK composta: provider + external_id; FK composta → accounts)
  - categories    (PK composta: provider + name; SEM FK com transactions)
  - sync_state    (PK simples: provider)
  - sync_history  (PK: id AUTOINCREMENT)

Regras seguidas nesta migration:
  - Nenhuma coluna preventiva
  - Nenhuma tabela auxiliar
  - Nenhum índice não documentado
  - Tipos SQLite-compatíveis (TEXT, INTEGER, NUMERIC, BOOLEAN, DATETIME)
  - NULLability idêntica à documentação
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_v3_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria o schema canônico V3."""

    # ──────────────────────────────────────────────────────────────────────
    # accounts
    # PK composta: (provider, external_id)
    # Sem FK de saída nesta tabela
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "accounts",
        sa.Column("provider", sa.Text(), nullable=False, comment="'pierre' | 'myprofit'"),
        sa.Column("external_id", sa.Text(), nullable=False, comment="ID da conta no provider"),
        sa.Column("name", sa.Text(), nullable=False, comment="Ex: 'Nubank'"),
        sa.Column("type", sa.Text(), nullable=False, comment="BANK | CREDIT"),
        sa.Column("subtype", sa.Text(), nullable=True, comment="CHECKING_ACCOUNT | CREDIT_CARD"),
        sa.Column("bank", sa.Text(), nullable=True, comment="Ex: 'Nu Pagamentos S.A.'"),
        sa.Column("connector", sa.Text(), nullable=True, comment="Ex: 'Nubank'"),
        sa.Column(
            "credit_metadata_json",
            sa.Text(),
            nullable=True,
            comment="JSON com limites, fatura, etc. (estado volátil da conta)",
        ),
        sa.Column("last_sync", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("provider", "external_id", name="pk_accounts"),
    )

    # ──────────────────────────────────────────────────────────────────────
    # transactions
    # PK composta: (provider, external_id)
    # FK composta: (account_provider, account_external_id) → accounts(provider, external_id)
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "transactions",
        # Integração
        sa.Column("provider", sa.Text(), nullable=False, comment="'pierre'"),
        sa.Column("external_id", sa.Text(), nullable=False, comment="UUID da transação na Pierre"),
        sa.Column("account_provider", sa.Text(), nullable=False, comment="FK → accounts.provider"),
        sa.Column("account_external_id", sa.Text(), nullable=False, comment="FK → accounts.external_id"),
        # Dados canônicos
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("original_description", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True, comment="String como recebida da Pierre"),
        sa.Column("original_category", sa.Text(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False, comment="'BRL'"),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, comment="POSTED | PENDING"),
        sa.Column("type", sa.Text(), nullable=False, comment="DEBIT | CREDIT"),
        # Dados desnormalizados pesquisáveis
        sa.Column("merchant_name", sa.Text(), nullable=True),
        sa.Column("bill_id", sa.Text(), nullable=True, comment="credit_card_data.billId"),
        sa.Column("installment_number", sa.Integer(), nullable=True, comment="credit_card_data.installmentNumber"),
        sa.Column("total_installments", sa.Integer(), nullable=True, comment="credit_card_data.totalInstallments"),
        sa.Column("purchase_date", sa.DateTime(), nullable=True, comment="credit_card_data.purchaseDate"),
        sa.Column("receiver_name", sa.Text(), nullable=True, comment="payment_data.receiver.name"),
        sa.Column("payer_name", sa.Text(), nullable=True, comment="payment_data.payer.name"),
        # Flags
        sa.Column("manual_transaction", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        # Escape hatch
        sa.Column(
            "extra_json",
            sa.Text(),
            nullable=True,
            comment="JSON para campos não mapeados ou não utilizados. Nenhuma funcionalidade depende deste campo.",
        ),
        # Constraints
        sa.PrimaryKeyConstraint("provider", "external_id", name="pk_transactions"),
        sa.ForeignKeyConstraint(
            ["account_provider", "account_external_id"],
            ["accounts.provider", "accounts.external_id"],
            name="fk_transactions_accounts",
        ),
    )

    # ──────────────────────────────────────────────────────────────────────
    # categories
    # PK composta: (provider, name)
    # SEM FK com transactions — catálogo estatístico desacoplado
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False, comment="Ex: 'Compras online'"),
        sa.Column("normalized_name", sa.Text(), nullable=True, comment="Versão normalizada para buscas"),
        sa.PrimaryKeyConstraint("provider", "name", name="pk_categories"),
    )

    # ──────────────────────────────────────────────────────────────────────
    # sync_state
    # PK simples: provider
    # Um registro por provider — UPSERT ao final de cada sync bem-sucedida
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "sync_state",
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("last_success_sync", sa.DateTime(), nullable=True),
        sa.Column("last_attempt", sa.DateTime(), nullable=True),
        sa.Column("last_cursor", sa.Text(), nullable=True),
        sa.Column("last_period", sa.Text(), nullable=True),
        sa.Column("api_version", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("provider", name="pk_sync_state"),
    )

    # ──────────────────────────────────────────────────────────────────────
    # sync_history
    # PK: id AUTOINCREMENT
    # Somente INSERT — registros nunca editados (auditoria)
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "sync_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("received", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("inserted", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ignored", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.Text(), nullable=True, comment="SUCCESS | FAILED | PARTIAL"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_sync_history"),
    )


def downgrade() -> None:
    """Remove todas as tabelas do schema V3 na ordem correta (FK primeiro)."""
    # transactions depende de accounts → drop primeiro
    op.drop_table("transactions")
    op.drop_table("sync_history")
    op.drop_table("sync_state")
    op.drop_table("categories")
    op.drop_table("accounts")
