import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import Base
from app.services.governance.import_service import ImportService
from app.models.governance import ImportArtifact

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

def test_import_run_lifecycle(db_session):
    service = ImportService(db_session)
    
    # 1. Start Run
    run = service.start_import_run(source_type="PIERRE", file_name="data.csv", checksum="abc")
    assert run.status == "PENDING"
    assert run.source_type == "PIERRE"
    
    # 2. Add Artifact
    artifact = service.add_artifact(run.id, "CSV", "/path/data.csv", "sha123", 1024)
    assert artifact.import_run_id == run.id
    
    # 3. Complete Run
    completed_run = service.complete_import_run(run.id, rows_read=10, rows_inserted=8, rows_updated=0, rows_failed=2)
    assert completed_run.status == "COMPLETED"
    assert completed_run.rows_read == 10
    assert completed_run.finished_at is not None

def test_import_run_failure(db_session):
    service = ImportService(db_session)
    run = service.start_import_run(source_type="API", file_name="api_sync", checksum="xyz")
    
    failed_run = service.fail_import_run(run.id, error_log="Connection timeout")
    assert failed_run.status == "FAILED"
    assert "timeout" in failed_run.error_log
