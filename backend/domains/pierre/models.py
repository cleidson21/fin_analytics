from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Integer, ForeignKeyConstraint, Text
from backend.database.base import Base

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
    __tablename__ = "transactions"

    provider = Column(String, primary_key=True)
    external_id = Column(String, primary_key=True)
    
    account_provider = Column(String, nullable=False)
    account_external_id = Column(String, nullable=False)

    description = Column(String, nullable=False)
    original_description = Column(String)
    category = Column(String)
    original_category = Column(String)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    type = Column(String, nullable=False)

    merchant_name = Column(String)
    bill_id = Column(String)
    installment_number = Column(Integer)
    total_installments = Column(Integer)
    purchase_date = Column(DateTime)
    receiver_name = Column(String)
    payer_name = Column(String)

    manual_transaction = Column(Boolean, nullable=False, default=False)
    extra_json = Column(Text)

    __table_args__ = (
        ForeignKeyConstraint(
            ['account_provider', 'account_external_id'],
            ['accounts.provider', 'accounts.external_id']
        ),
    )

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
