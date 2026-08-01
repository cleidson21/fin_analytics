import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import Base

from app.models.governance import ImportRun, StagingImport, StagingPosition
from app.models.core_finance import Transaction
from app.models.wealth import Position
from app.services.governance.approval import ApprovalService

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

def test_approval_promotion(db_session):
    run = ImportRun(id="run1", status="PENDING")
    db_session.add(run)
    
    stg_txn = StagingImport(import_run_id="run1", amount_cents=15000, description="Salary", date="2026-06-15")
    stg_pos = StagingPosition(import_run_id="run1", ticker="WEGE3", quantidade=100.0, data_snapshot=date(2026, 6, 15))
    
    db_session.add_all([stg_txn, stg_pos])
    db_session.commit()

    service = ApprovalService(db_session)
    confirmed_run = service.confirm_import("run1")
    
    assert confirmed_run.status == "COMPLETED"
    
    # Check ledger
    txn = db_session.query(Transaction).filter_by(import_run_id="run1").first()
    assert txn is not None
    assert txn.valor_cents == 15000
    assert txn.natureza == "INCOME" # > 0
    
    pos = db_session.query(Position).filter_by(import_run_id="run1").first()
    assert pos is not None
    assert pos.ticker == "WEGE3"

    # Check staging status
    db_session.refresh(stg_txn)
    assert stg_txn.status == "PROMOTED"

def test_approval_rejection(db_session):
    run = ImportRun(id="run2", status="PENDING")
    db_session.add(run)
    
    stg_txn = StagingImport(import_run_id="run2", amount_cents=-5000)
    db_session.add(stg_txn)
    db_session.commit()

    service = ApprovalService(db_session)
    rejected_run = service.reject_import("run2", "Found anomalies")
    
    assert rejected_run.status == "FAILED"
    assert rejected_run.error_log == "Found anomalies"
    
    # Check staging
    db_session.refresh(stg_txn)
    assert stg_txn.status == "FAILED"
    
    # Check ledger is empty
    assert db_session.query(Transaction).filter_by(import_run_id="run2").count() == 0
