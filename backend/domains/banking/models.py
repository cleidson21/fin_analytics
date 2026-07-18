from sqlalchemy import Column, String, Integer, DateTime
from backend.shared.db import Base
from datetime import datetime
import uuid

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String, nullable=False)
    merchant_id = Column(String, nullable=True)
    category_id = Column(String, nullable=True)
    date = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    original_description = Column(String, nullable=False)
    normalized_desc = Column(String, nullable=True)
    source = Column(String, nullable=False)
    is_transfer = Column(Integer, nullable=False, default=0)
    is_investment = Column(Integer, nullable=False, default=0)
    is_ignored = Column(Integer, nullable=False, default=0)
    needs_review = Column(Integer, nullable=False, default=0)
    run_id = Column(String, nullable=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat() + "Z")
