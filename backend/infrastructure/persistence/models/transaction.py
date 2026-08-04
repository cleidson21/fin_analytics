from sqlalchemy import Boolean, Column, DateTime, Numeric, String, ForeignKey, JSON, Date, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from backend.database.base import Base

class TransactionModel(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("external_id", "provider", name="uq_transaction_external_id_provider"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    direction = Column(String, nullable=False)
    currency_code = Column(String, nullable=False)
    description = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    is_recurring = Column(Boolean, nullable=False, default=False)
    hash = Column(String, nullable=False, unique=True, index=True)
    
    external_id = Column(String, nullable=True, index=True)
    original_description = Column(String, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True)
    posted_date = Column(Date, nullable=True)
    installment_count = Column(Integer, nullable=True)
    installment_current = Column(Integer, nullable=True)
    purchase_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # NEW – identifica compra originária
    provider_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
