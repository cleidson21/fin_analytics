from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer, ForeignKeyConstraint, Text
from backend.database.base import Base


# ==========================================================================
# RAW LAYER — dados originais da API
# ==========================================================================

class Account(Base):
    __tablename__ = "accounts"

    provider = Column(String, primary_key=True)
    external_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    subtype = Column(String)
    bank = Column(String)
    connector = Column(String)
    credit_metadata_json = Column(Text)
    last_sync = Column(DateTime)


class Transaction(Base):
    """
    Tabela principal com duas camadas bem separadas:

    IDENTITY (imutável — jamais alterado por sync, governança ou edição):
        provider, external_id

    RAW (propriedade da API — pode ser atualizado pelo upsert de sync):
        account_provider, account_external_id, description, original_description,
        category, original_category, amount, currency, date, status, type,
        merchant_name, bill_id, installment_number, total_installments,
        purchase_date, receiver_name, payer_name, manual_transaction, extra_json

    GOVERNANCE (propriedade do usuário — jamais tocado pelo upsert da API):
        governance_status, economic_classification, investment_name, notes, governed_at
    """
    __tablename__ = "transactions"

    # -- IDENTITY --
    provider = Column(String, primary_key=True)
    external_id = Column(String, primary_key=True)

    # -- RAW: atributos de conta (atualizáveis pela API — não são identidade da transação) --
    account_provider = Column(String, nullable=False)
    account_external_id = Column(String, nullable=False)

    # -- RAW: dados da transação --
    description = Column(String, nullable=False)
    original_description = Column(String)
    category = Column(String)
    original_category = Column(String)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    type = Column(String, nullable=False)

    # -- RAW: metadados adicionais --
    merchant_name = Column(String)
    bill_id = Column(String)
    installment_number = Column(Integer)
    total_installments = Column(Integer)
    purchase_date = Column(DateTime)
    receiver_name = Column(String)
    payer_name = Column(String)
    manual_transaction = Column(Boolean, nullable=False, default=False)
    extra_json = Column(Text)

    # -- GOVERNANCE: propriedade exclusiva do usuário --
    # governance_status: PENDING | CLASSIFIED
    #   PENDING    = transação recém-chegada, sem decisão do usuário
    #   CLASSIFIED = usuário registrou uma decisão (qualquer uma, inclusive IGNORAR)
    governance_status = Column(String, nullable=False, default='PENDING')

    # economic_classification: NULL | ENTRADA | SAIDA | IGNORAR
    #   NULL    = sem decisão (apenas quando PENDING)
    #   ENTRADA = entra no cálculo de receitas
    #   SAIDA   = entra no cálculo de despesas
    #   IGNORAR = excluída dos cálculos; mantida no histórico; reclassificável
    economic_classification = Column(String, nullable=True)

    # investment_name: texto livre, sem validação de ativo
    # Válido com qualquer economic_classification (inclusive IGNORAR)
    # Ex: ENTRADA + KNCR11 = rendimento; IGNORAR + RDB 120% CDI = aplicação
    investment_name = Column(String, nullable=True)

    # notes: observação livre do usuário
    notes = Column(String, nullable=True)

    # governed_at: timestamp da última alteração de governança
    governed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ['account_provider', 'account_external_id'],
            ['accounts.provider', 'accounts.external_id']
        ),
    )


# ==========================================================================
# AUDIT LAYER — histórico imutável de decisões de governança
# INSERT-only. Nunca UPDATE ou DELETE.
# ==========================================================================

class GovernanceAuditLog(Base):
    """
    Registro imutável de cada transição de estado de governança.

    Cada linha representa um evento completo com snapshot antes e depois.
    Isso permite rollback para qualquer estado anterior sem ambiguidade.

    action:
        CREATE_CLASSIFICATION  = primeira classificação (PENDING → CLASSIFIED)
        UPDATE_CLASSIFICATION  = alteração de classificação existente
        ROLLBACK               = restauração de estado anterior via rollback

    Rollback também gera uma nova linha nesta tabela (action=ROLLBACK),
    garantindo rastreabilidade completa de todas as decisões, incluindo reversões.
    """
    __tablename__ = "governance_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Referência à transação (chave lógica — não FK para evitar cascata)
    provider = Column(String, nullable=False)
    external_id = Column(String, nullable=False)

    # Tipo do evento
    action = Column(String, nullable=False)  # CREATE_CLASSIFICATION | UPDATE_CLASSIFICATION | ROLLBACK

    # Snapshots completos do estado de governança (JSON serializado)
    # before_json = None na primeira classificação (CREATE_CLASSIFICATION de PENDING)
    before_json = Column(Text, nullable=True)
    after_json = Column(Text, nullable=True)

    # Metadados do evento
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    changed_by = Column(String, nullable=True)   # reservado: futura autenticação multi-usuário
    reason = Column(String, nullable=True)       # motivo informado pelo usuário


class Category(Base):
    __tablename__ = "categories"

    provider = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    normalized_name = Column(String)


class SyncState(Base):
    __tablename__ = "sync_state"

    provider = Column(String, primary_key=True)
    last_success_sync = Column(DateTime)
    last_attempt = Column(DateTime)
    last_cursor = Column(String)
    last_period = Column(String)
    api_version = Column(String)


class SyncHistory(Base):
    __tablename__ = "sync_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    received = Column(Integer, default=0)
    inserted = Column(Integer, default=0)
    updated = Column(Integer, default=0)
    ignored = Column(Integer, default=0)
    status = Column(String)
    error = Column(String)
