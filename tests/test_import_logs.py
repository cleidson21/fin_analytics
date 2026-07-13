import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.domains.investments.repositories.import_log_repository import ImportLogRepository

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    # Initialize the tables required for testing
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE users (id TEXT PRIMARY KEY);
        """))
        conn.execute(text("""
        INSERT INTO users (id) VALUES ('SINGLE_USER');
        """))
        conn.execute(text("""
        CREATE TABLE import_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            checksum TEXT NOT NULL,
            parser TEXT NOT NULL,
            rows_read INTEGER DEFAULT 0,
            rows_imported INTEGER DEFAULT 0,
            rows_duplicated INTEGER DEFAULT 0,
            rows_failed INTEGER DEFAULT 0,
            processing_time_ms INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            error_message TEXT,
            metadata_json TEXT
        );
        """))
    session = Session(engine)
    yield session
    session.close()

def test_import_log_repository_create_and_read(db_session):
    repo = ImportLogRepository()
    
    log_data = {
        "filename": "test.csv",
        "file_type": "CSV",
        "file_size": 1024,
        "checksum": "abc123hash",
        "parser": "CSVTradeParser",
        "rows_read": 10,
        "rows_imported": 8,
        "rows_duplicated": 2,
        "rows_failed": 0,
        "processing_time_ms": 150,
        "status": "SUCCESS",
        "metadata_json": {"source": "CEI"}
    }
    
    log_id = repo.create(db_session, log_data)
    db_session.commit()
    
    assert log_id is not None
    
    # Test Read
    log = repo.get_by_id(db_session, log_id)
    assert log is not None
    assert log["filename"] == "test.csv"
    assert log["status"] == "SUCCESS"
    assert log["checksum"] == "abc123hash"
    assert log["rows_imported"] == 8

def test_import_log_repository_filters(db_session):
    repo = ImportLogRepository()
    
    repo.create(db_session, {"filename": "f1.csv", "status": "SUCCESS", "checksum": "hash1", "file_type": "CSV", "file_size": 1, "parser": "P1"})
    repo.create(db_session, {"filename": "f2.csv", "status": "FAILED", "checksum": "hash2", "file_type": "CSV", "file_size": 1, "parser": "P1"})
    repo.create(db_session, {"filename": "f3.csv", "status": "SUCCESS", "checksum": "hash3", "file_type": "CSV", "file_size": 1, "parser": "P2"})
    db_session.commit()
    
    # Filter by status
    success_logs = repo.list_history(db_session, {"status": "SUCCESS"})
    assert len(success_logs) == 2
    
    # Filter by parser
    p2_logs = repo.list_history(db_session, {"parser": "P2"})
    assert len(p2_logs) == 1
    
    # Filter by checksum
    hash1_logs = repo.list_history(db_session, {"checksum": "hash1"})
    assert len(hash1_logs) == 1
    assert hash1_logs[0]["filename"] == "f1.csv"
