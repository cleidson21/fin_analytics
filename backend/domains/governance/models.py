from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from backend.shared.db import Base
from datetime import datetime
import uuid

class ImportRun(Base):
    __tablename__ = "import_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    source = Column(String, nullable=False)
    status = Column(String, nullable=False, default='PENDING')
    filename = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    rows_parsed = Column(Integer, default=0)
    rows_inserted = Column(Integer, default=0)
    rows_skipped = Column(Integer, default=0)
    rows_errored = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(String, default=lambda: datetime.utcnow().isoformat() + "Z")
    finished_at = Column(String, nullable=True)


class ImportArtifact(Base):
    __tablename__ = "import_artifacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    row_number = Column(Integer, nullable=False)
    raw_data = Column(Text, nullable=False)
    status = Column(String, nullable=False, default='PENDING')
    result_id = Column(String, nullable=True)
    error_msg = Column(Text, nullable=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat() + "Z")
