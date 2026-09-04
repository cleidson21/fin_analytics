from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.database.base import Base

class IncomeEventModel(Base):
    __tablename__ = "income_events"
    __table_args__ = (
        UniqueConstraint(
            "account_id", 
            "asset_id", 
            "event_type", 
            "payment_date", 
            "ex_date", 
            "gross_amount", 
            name="uq_income_event_identity"
        ),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    account_id = Column(String(36), nullable=False, index=True) # Workaround for Pierre accounts table collision
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    
    event_type = Column(String, nullable=False) # DIVIDENDO, JCP, etc.
    payment_date = Column(Date, nullable=False, index=True)
    ex_date = Column(Date, nullable=True) # Data COM
    
    quantity = Column(Numeric(18, 8), nullable=False)
    value_per_unit = Column(Numeric(18, 8), nullable=False)
    gross_amount = Column(Numeric(18, 2), nullable=False) # Recebido
    
    yoc = Column(Numeric(10, 4), nullable=True) # YOC (Optional)
    dy = Column(Numeric(10, 4), nullable=True) # DY (Optional)
    
    run_id = Column(String(36), nullable=True)
    source_type = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
