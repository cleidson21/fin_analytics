from sqlalchemy import Column, String, Integer, Float, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
import uuid

from backend.database.base import Base
from backend.domain.enums.provider_type import ProviderType

class SyncStatus(str, __import__("enum").Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    RUNNING = "RUNNING"

class SyncLogModel(Base):
    __tablename__ = "sync_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    provider = Column(SQLEnum(ProviderType), nullable=False)
    status = Column(SQLEnum(SyncStatus), nullable=False)
    
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    accounts_synced = Column(Integer, default=0)
    transactions_synced = Column(Integer, default=0)
    categories_synced = Column(Integer, default=0)
    
    inserted = Column(Integer, default=0)
    updated = Column(Integer, default=0)
    ignored = Column(Integer, default=0)
    
    error_message = Column(String, nullable=True)
    provider_metadata = Column(JSON, nullable=True)
