import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import Base
from app.models.governance import ImportRun, RawEvent
from app.services.governance.reconciliation import ReconciliationService

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

def test_reconciliation_exact_and_fuzzy_matches(db_session):
    run = ImportRun(id="run1", source_type="API")
    db_session.add(run)
    db_session.commit()

    # Target event
    t1 = RawEvent(
        id="evt_target", import_run_id="run1", source="PIERRE", event_type="EXPENSE",
        semantic_id="s1", amount_cents=10000, event_date=date(2026, 6, 10), match_status="NEW"
    )
    
    # Exact Match
    m_exact = RawEvent(
        id="evt_exact", import_run_id="run1", source="BANK", event_type="DEBIT",
        semantic_id="s2", amount_cents=-10000, event_date=date(2026, 6, 10), match_status="NEW"
    )
    
    # Fuzzy Match (+2 days)
    m_fuzzy = RawEvent(
        id="evt_fuzzy", import_run_id="run1", source="BANK", event_type="DEBIT",
        semantic_id="s3", amount_cents=-10000, event_date=date(2026, 6, 12), match_status="NEW"
    )
    
    # No Match (wrong amount)
    m_no_amount = RawEvent(
        id="evt_no1", import_run_id="run1", source="BANK", event_type="DEBIT",
        semantic_id="s4", amount_cents=-5000, event_date=date(2026, 6, 10), match_status="NEW"
    )
    
    # No Match (out of fuzzy window, +4 days)
    m_no_date = RawEvent(
        id="evt_no2", import_run_id="run1", source="BANK", event_type="DEBIT",
        semantic_id="s5", amount_cents=-10000, event_date=date(2026, 6, 14), match_status="NEW"
    )

    db_session.add_all([t1, m_exact, m_fuzzy, m_no_amount, m_no_date])
    db_session.commit()

    service = ReconciliationService(db_session)
    matches = service.find_matches(t1)

    # Should find EXACT and FUZZY
    assert len(matches) == 2
    matched_ids = [m.id for m in matches]
    assert "evt_exact" in matched_ids
    assert "evt_fuzzy" in matched_ids
    
    # Create EXACT link
    link_exact = service.create_link(t1, m_exact)
    assert link_exact.match_method == "EXACT"
    assert link_exact.confidence == 1.0
    assert t1.match_status == "MATCHED"
    
    # Let's pretend t1 wasn't matched to test fuzzy link
    t1.match_status = "NEW"
    m_fuzzy.match_status = "NEW"
    link_fuzzy = service.create_link(t1, m_fuzzy)
    assert link_fuzzy.match_method == "FUZZY"
    assert link_fuzzy.confidence == 0.8
