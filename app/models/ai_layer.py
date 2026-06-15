from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.db import Base
from datetime import datetime
import uuid

class Rule(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_type = Column(String, nullable=False)
    pattern = Column(String, nullable=False)
    action = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=False, default=1.0)
    evidence_count = Column(Integer, nullable=False, default=1)
    hit_count = Column(Integer, nullable=False, default=1)
    miss_count = Column(Integer, nullable=False, default=0)
    active = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default='OBSERVING')
    version = Column(Integer, nullable=False, default=1)
    superseded_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    status_changed_at = Column(DateTime, default=datetime.utcnow)

class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    active = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

class AiRun(Base):
    __tablename__ = "ai_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="SET NULL"), nullable=True)
    prompt_version_id = Column(String, ForeignKey("prompt_versions.id", ondelete="RESTRICT"), nullable=False)
    model = Column(String, nullable=False)
    input_text = Column(Text, nullable=False)
    output_json = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    status = Column(String, nullable=False, default='SUCCESS')
    created_at = Column(DateTime, default=datetime.utcnow)
