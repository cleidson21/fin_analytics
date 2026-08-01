import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import Base
import app.models.governance
import app.models.core_finance
from app.models.ai_layer import Rule
from app.services.ai_layer.classification import ClassificationEngineService

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

def test_classification_flow(db_session):
    # Setup Rule for Netflix
    rule = Rule(
        id="r1", rule_type="REGEX", pattern="NETFLIX", 
        action=json.dumps({"macro_categoria": "Lazer"}),
        confidence_score=1.0, active=1
    )
    db_session.add(rule)
    db_session.commit()

    service = ClassificationEngineService(db_session)

    # 1. Reconciliation Priority
    res_recon = service.classify_transaction("Qualquer", is_reconciled=True)
    assert res_recon["source"] == "RECONCILIATION"

    # 2. Rule Match
    res_rule = service.classify_transaction("PAGAMENTO NETFLIX")
    assert res_rule["source"] == "RULES"
    assert res_rule["macro_categoria"] == "Lazer"

    # 3. AI Mock Match (MockProvider matches "uber" or "99")
    res_ai = service.classify_transaction("Viagem Uber")
    assert res_ai["source"] == "AI"
    assert res_ai["macro_categoria"] == "Transporte"

    # 4. Fallback (No rule, no AI match)
    res_fallback = service.classify_transaction("Padaria do Zé")
    assert res_fallback["source"] == "FALLBACK"
    assert res_fallback["macro_categoria"] == "Outros"
