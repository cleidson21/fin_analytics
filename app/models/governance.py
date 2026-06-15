from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from app.core.db import Base
from datetime import datetime
import uuid

class ImportRun(Base):
    __tablename__ = "import_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type = Column(String, nullable=False, default='PIERRE')
    file_name = Column(String, nullable=False, default='')
    checksum = Column(String, nullable=False, default='')
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default='PENDING')
    rows_read = Column(Integer, nullable=False, default=0)
    rows_inserted = Column(Integer, nullable=False, default=0)
    rows_updated = Column(Integer, nullable=False, default=0)
    rows_failed = Column(Integer, nullable=False, default=0)
    error_log = Column(Text, nullable=True)
    preview_summary = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    rollback_timestamp = Column(DateTime, nullable=True)
    rollback_reason = Column(Text, nullable=True)
    rollback_user = Column(String, nullable=True)

    # Relationships are handled on the child side due to large amounts of children.

class ImportArtifact(Base):
    __tablename__ = "import_artifacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    artifact_type = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False, default=0)
    mime_type = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class RawEvent(Base):
    __tablename__ = "raw_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    source = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    source_line_no = Column(Integer, nullable=True)
    raw_content = Column(Text, nullable=True)
    event_date = Column(Date, nullable=True)
    reference_month = Column(Date, nullable=True)
    amount_cents = Column(Integer, nullable=True)
    currency = Column(String, nullable=False, default='BRL')
    semantic_id = Column(String, nullable=False, unique=True)
    cross_fingerprint = Column(String, nullable=True)
    external_id = Column(String, nullable=True)
    metadata_json = Column("metadata", Text, nullable=True) # renamed locally to avoid reserved words
    pipeline_status = Column(String, nullable=False, default='RAW')
    match_status = Column(String, nullable=False, default='NEW')
    promoted_entity_id = Column(String, nullable=True)
    promoted_table = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class EventLink(Base):
    __tablename__ = "event_links"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id_a = Column(String, ForeignKey("raw_events.id", ondelete="CASCADE"), nullable=False)
    event_id_b = Column(String, ForeignKey("raw_events.id", ondelete="CASCADE"), nullable=False)
    link_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    match_method = Column(String, nullable=False, default='EXACT')
    status = Column(String, nullable=False, default='AUTO_CONFIRMED')
    confirmed_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    field_changes = Column(Text, nullable=True)
    changed_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# STAGING TABLES
class StagingImport(Base):
    __tablename__ = "staging_imports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    source_line_no = Column(Integer, nullable=True)
    date = Column(String, nullable=True)
    description = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    amount_cents = Column(Integer, nullable=True)
    account = Column(String, nullable=True)
    category_inferred = Column(String, nullable=True)
    status = Column(String, default='PENDING')

class StagingPosition(Base):
    __tablename__ = "staging_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    source_line_no = Column(Integer, nullable=True)
    validation_status = Column(String, default='PENDING')
    validation_message = Column(Text, nullable=True)
    ticker = Column(String, nullable=True)
    data_snapshot = Column(Date, nullable=True)
    source = Column(String, nullable=True)
    quantidade = Column(Float, nullable=True)
    preco_medio = Column(Float, nullable=True)
    total_investido = Column(Float, nullable=True)
    preco_atual = Column(Float, nullable=True)
    total_atual = Column(Float, nullable=True)
    ganho = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StagingDividend(Base):
    __tablename__ = "staging_dividends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    source_line_no = Column(Integer, nullable=True)
    validation_status = Column(String, default='PENDING')
    validation_message = Column(Text, nullable=True)
    id_economico = Column(String, nullable=True)
    source = Column(String, nullable=True)
    ticker = Column(String, nullable=True)
    tipo_evento = Column(String, nullable=True)
    data_pagamento = Column(Date, nullable=True)
    valor_liquido = Column(Float, nullable=True)
    valor_liquido_cents = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StagingPortfolioEvolution(Base):
    __tablename__ = "staging_portfolio_evolution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    import_run_id = Column(String, ForeignKey("import_runs.id", ondelete="CASCADE"), nullable=False)
    source_line_no = Column(Integer, nullable=True)
    validation_status = Column(String, default='PENDING')
    validation_message = Column(Text, nullable=True)
    reference_month = Column(Date, nullable=True)
    rentabilidade_mensal_pct = Column(Float, nullable=True)
    rentabilidade_acumulada_pct = Column(Float, nullable=True)
    patrimonio_cents = Column(Integer, nullable=True) # sqlite bigint is int
    compras_cents = Column(Integer, nullable=True)
    vendas_cents = Column(Integer, nullable=True)
    op_finalizadas_cents = Column(Integer, nullable=True)
    proventos_cents = Column(Integer, nullable=True)
    ibov_mensal_pct = Column(Float, nullable=True)
    ibov_acumulado_pct = Column(Float, nullable=True)
    cdi_mensal_pct = Column(Float, nullable=True)
    cdi_acumulado_pct = Column(Float, nullable=True)
    ipca_mensal_pct = Column(Float, nullable=True)
    ipca_acumulado_pct = Column(Float, nullable=True)
    ifix_mensal_pct = Column(Float, nullable=True)
    ifix_acumulado_pct = Column(Float, nullable=True)
    sp500_mensal_pct = Column(Float, nullable=True)
    sp500_acumulado_pct = Column(Float, nullable=True)
    idiv_mensal_pct = Column(Float, nullable=True)
    idiv_acumulado_pct = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

