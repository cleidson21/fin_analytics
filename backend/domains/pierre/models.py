"""
models.py — Domínio Pierre

SQLAlchemy models para as 5 tabelas canônicas da Sprint 4.4.

Regras aplicadas neste arquivo:
  - Nenhuma coluna além das definidas em docs/03_DATABASE.md
  - Nenhuma propriedade calculada ou híbrida
  - Nenhuma lógica de negócio
  - PKs compostas exatamente como documentadas
  - FK composta de transactions → accounts exatamente como documentada
  - NULLability idêntica à documentação
  - Sem índices não documentados

Referência canônica: docs/03_DATABASE.md e docs/60_ARCHITECTURE_REVISION_V31.md (árbitro)
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.domains.shared.db import Base


# ──────────────────────────────────────────────────────────────────────────────
# accounts
# PK composta: (provider, external_id)
# ──────────────────────────────────────────────────────────────────────────────
class Account(Base):
    """
    Cópia canônica das contas do Provider.

    Tabela: accounts
    Provider: 'pierre' | 'myprofit'

    Política:
      - Nunca editado manualmente após sync
      - UPSERT via ON CONFLICT (provider, external_id) DO UPDATE
      - credit_metadata_json: estado volátil da conta (limites, fatura) — JSON bruto
    """

    __tablename__ = "accounts"
    __table_args__ = (
        PrimaryKeyConstraint("provider", "external_id", name="pk_accounts"),
    )

    # Identificação
    provider: Mapped[str] = mapped_column(Text, nullable=False, comment="'pierre' | 'myprofit'")
    external_id: Mapped[str] = mapped_column(Text, nullable=False, comment="ID da conta no provider")

    # Dados canônicos
    name: Mapped[str] = mapped_column(Text, nullable=False, comment="Ex: 'Nubank'")
    type: Mapped[str] = mapped_column(Text, nullable=False, comment="BANK | CREDIT")
    subtype: Mapped[str | None] = mapped_column(Text, nullable=True, comment="CHECKING_ACCOUNT | CREDIT_CARD")
    bank: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Ex: 'Nu Pagamentos S.A.'")
    connector: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Ex: 'Nubank'")
    credit_metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON com limites, fatura, etc. (estado volátil da conta)",
    )
    last_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relacionamento reverso (sem FK da accounts → transactions, apenas inverso)
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="account",
        foreign_keys="[Transaction.account_provider, Transaction.account_external_id]",
    )

    def __repr__(self) -> str:
        return f"<Account provider={self.provider!r} external_id={self.external_id!r} name={self.name!r}>"


# ──────────────────────────────────────────────────────────────────────────────
# transactions
# PK composta: (provider, external_id)
# FK composta: (account_provider, account_external_id) → accounts(provider, external_id)
# ──────────────────────────────────────────────────────────────────────────────
class Transaction(Base):
    """
    Cópia canônica das transações do Provider Pierre.

    Tabela: transactions
    Provider: 'pierre' (única fonte de transações financeiras na V1.0)

    Política:
      - Imutabilidade: registros sincronizados nunca são editados diretamente
      - UPSERT via ON CONFLICT (provider, external_id) DO UPDATE
      - Campos eliminados explicitamente: hash, purchase_id, direction,
        is_recurring, category_id FK, user_id
      - extra_json: apenas campos desconhecidos — nenhuma funcionalidade depende dele
    """

    __tablename__ = "transactions"
    __table_args__ = (
        PrimaryKeyConstraint("provider", "external_id", name="pk_transactions"),
        ForeignKeyConstraint(
            ["account_provider", "account_external_id"],
            ["accounts.provider", "accounts.external_id"],
            name="fk_transactions_accounts",
        ),
    )

    # ── Integração ────────────────────────────────────────────────────────
    provider: Mapped[str] = mapped_column(Text, nullable=False, comment="'pierre'")
    external_id: Mapped[str] = mapped_column(Text, nullable=False, comment="UUID da transação na Pierre")
    account_provider: Mapped[str] = mapped_column(Text, nullable=False, comment="FK → accounts.provider")
    account_external_id: Mapped[str] = mapped_column(Text, nullable=False, comment="FK → accounts.external_id")

    # ── Dados canônicos ───────────────────────────────────────────────────
    description: Mapped[str] = mapped_column(Text, nullable=False)
    original_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(Text, nullable=True, comment="String como recebida da Pierre")
    original_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False, comment="'BRL'")
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, comment="POSTED | PENDING")
    type: Mapped[str] = mapped_column(Text, nullable=False, comment="DEBIT | CREDIT")

    # ── Dados desnormalizados pesquisáveis ────────────────────────────────
    merchant_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    bill_id: Mapped[str | None] = mapped_column(Text, nullable=True, comment="credit_card_data.billId")
    installment_number: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="credit_card_data.installmentNumber")
    total_installments: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="credit_card_data.totalInstallments")
    purchase_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="credit_card_data.purchaseDate")
    receiver_name: Mapped[str | None] = mapped_column(Text, nullable=True, comment="payment_data.receiver.name")
    payer_name: Mapped[str | None] = mapped_column(Text, nullable=True, comment="payment_data.payer.name")

    # ── Flags ─────────────────────────────────────────────────────────────
    manual_transaction: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Escape hatch ──────────────────────────────────────────────────────
    extra_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="JSON para campos não mapeados ou não utilizados. Nenhuma funcionalidade depende deste campo.",
    )

    # Relacionamento para a conta pai
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="transactions",
        foreign_keys=[account_provider, account_external_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction provider={self.provider!r} external_id={self.external_id!r} "
            f"amount={self.amount} date={self.date}>"
        )


# ──────────────────────────────────────────────────────────────────────────────
# categories
# PK composta: (provider, name)
# SEM FK com transactions (catálogo estatístico)
# ──────────────────────────────────────────────────────────────────────────────
class Category(Base):
    """
    Catálogo estatístico de categorias por provider.

    Tabela: categories

    Política:
      - Construído automaticamente via INSERT OR IGNORE durante UPSERT de transações
      - SEM Foreign Key com transactions — intencionalmente desacoplado
      - A Pierre pode criar novas categorias sem impactar o banco
      - normalized_name: versão lowercase sem acentos para busca
    """

    __tablename__ = "categories"
    __table_args__ = (
        PrimaryKeyConstraint("provider", "name", name="pk_categories"),
    )

    provider: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False, comment="Ex: 'Compras online'")
    normalized_name: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Versão normalizada para buscas")

    def __repr__(self) -> str:
        return f"<Category provider={self.provider!r} name={self.name!r}>"


# ──────────────────────────────────────────────────────────────────────────────
# sync_state
# PK simples: provider
# ──────────────────────────────────────────────────────────────────────────────
class SyncState(Base):
    """
    Estado atual da sincronização por provider.

    Tabela: sync_state

    Política:
      - Um único registro por provider ('pierre', 'myprofit')
      - Atualizado via UPSERT ao final de cada sincronização bem-sucedida
      - last_cursor: suporte futuro a sync incremental por cursor da API
    """

    __tablename__ = "sync_state"
    __table_args__ = (
        PrimaryKeyConstraint("provider", name="pk_sync_state"),
    )

    provider: Mapped[str] = mapped_column(Text, nullable=False)
    last_success_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_attempt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_cursor: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_period: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_version: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SyncState provider={self.provider!r} last_success={self.last_success_sync}>"


# ──────────────────────────────────────────────────────────────────────────────
# sync_history
# PK simples: id (AUTOINCREMENT)
# ──────────────────────────────────────────────────────────────────────────────
class SyncHistory(Base):
    """
    Auditoria imutável de cada execução de sincronização.

    Tabela: sync_history

    Política:
      - Apenas INSERT — registros nunca são editados
      - status: SUCCESS | FAILED | PARTIAL
      - received/inserted/updated/ignored: contadores da execução
      - error: mensagem de erro quando status != SUCCESS
    """

    __tablename__ = "sync_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ignored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str | None] = mapped_column(Text, nullable=True, comment="SUCCESS | FAILED | PARTIAL")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SyncHistory id={self.id} provider={self.provider!r} status={self.status!r}>"
