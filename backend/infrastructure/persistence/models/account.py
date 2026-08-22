import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Numeric, ForeignKey, JSON
from backend.database.base import Base
from backend.infrastructure.persistence.models.institution import InstitutionModel

class AccountModel(Base):
    __tablename__ = "accounts"
    __table_args__ = {'keep_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String, nullable=True)
    provider = Column(String, nullable=False)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    subtype = Column(String, nullable=True)
    currency_code = Column(String, nullable=False)
    balance = Column(Numeric(12, 2), nullable=True)
    balance_updated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    provider_code = Column(String, nullable=True)
    provider_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
