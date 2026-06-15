import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import Base

from app.services.governance.audit import AuditService

@pytest.fixture
def db_session():
    engine = create_engine(
        'sqlite:///:memory:', 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_audit_logging_and_retrieval(db_session):
    service = AuditService(db_session)
    
    log1 = service.log_event(
        entity_type="ImportRun", 
        entity_id="run_123", 
        action="CREATED", 
        user="admin"
    )
    
    log2 = service.log_event(
        entity_type="ImportRun", 
        entity_id="run_123", 
        action="STATUS_CHANGED", 
        field_changes={"old": "PENDING", "new": "COMPLETED"},
        user="system"
    )

    assert log1.id is not None
    assert log2.field_changes is not None
    assert "COMPLETED" in log2.field_changes

    history = service.get_history("ImportRun", "run_123")
    assert len(history) == 2
    assert history[0].action == "CREATED"
    assert history[1].action == "STATUS_CHANGED"

def test_audit_trace_import_run(db_session):
    service = AuditService(db_session)
    service.log_event("ImportRun", "run_999", "STARTED")
    service.log_event("ImportRun", "run_999", "MATCHING_DONE")
    
    trace = service.trace_import_run("run_999")
    assert len(trace) == 2
    assert trace[0].action == "STARTED"
    assert trace[1].action == "MATCHING_DONE"
