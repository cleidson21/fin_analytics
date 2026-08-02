import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import Base
import app.models.governance
import app.models.core_finance
from app.models.ai_layer import Rule
from app.services.ai_layer.rule_engine import RuleEngineService
import json

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

def test_rule_engine_exact_and_regex(db_session):
    rule1 = Rule(
        id="r1", rule_type="EXACT", pattern="^PGTO NETFLIX$", 
        action=json.dumps({"macro_categoria": "Lazer", "sub_categoria": "Streaming"}),
        confidence_score=1.0, active=1
    )
    rule2 = Rule(
        id="r2", rule_type="REGEX", pattern="UBER.*", 
        action=json.dumps({"macro_categoria": "Transporte", "sub_categoria": "App"}),
        confidence_score=0.9, active=1
    )
    db_session.add_all([rule1, rule2])
    db_session.commit()

    service = RuleEngineService(db_session)
    
    # Exact Match
    res_exact = service.evaluate_description("PGTO NETFLIX")
    assert res_exact["matched"] is True
    assert res_exact["macro_categoria"] == "Lazer"
    
    # Regex Match
    res_regex = service.evaluate_description("Uber Trip Sao Paulo")
    assert res_regex["matched"] is True
    assert res_regex["macro_categoria"] == "Transporte"
    
    # No Match
    res_none = service.evaluate_description("Pao de Acucar")
    assert res_none["matched"] is False

def test_rule_engine_priority_conflict(db_session):
    # Two rules matching "UBER", but one has higher confidence
    rule_high = Rule(
        id="r_high", rule_type="REGEX", pattern="UBER", 
        action=json.dumps({"macro_categoria": "Transporte"}),
        confidence_score=0.99, active=1
    )
    rule_low = Rule(
        id="r_low", rule_type="REGEX", pattern=".*UBER.*", 
        action=json.dumps({"macro_categoria": "Outros"}),
        confidence_score=0.5, active=1
    )
    db_session.add_all([rule_high, rule_low])
    db_session.commit()

    service = RuleEngineService(db_session)
    res = service.evaluate_description("UBER EATS")
    
    # Should resolve conflict by priority (confidence_score)
    assert res["matched"] is True
    assert res["macro_categoria"] == "Transporte"
    assert res["rule_id"] == "r_high"
