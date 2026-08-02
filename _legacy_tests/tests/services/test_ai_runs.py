import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import Base
import app.models.governance
import app.models.core_finance
from app.models.ai_layer import PromptVersion
from app.services.ai_layer.ai_runs import AIRunService

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

def test_ai_runs_registration_and_report(db_session):
    pv = PromptVersion(id="pv1", name="v1", version=1, content="prompt")
    db_session.add(pv)
    db_session.commit()

    service = AIRunService(db_session)
    
    service.register_run(
        prompt_version_id="pv1", import_run_id="run1", model="gpt-4",
        input_text="t1", tokens_input=100, tokens_output=50, estimated_cost=0.015
    )
    service.register_run(
        prompt_version_id="pv1", import_run_id="run1", model="gpt-4",
        input_text="t2", tokens_input=200, tokens_output=100, estimated_cost=0.030
    )
    
    report = service.get_aggregated_report()
    
    assert report["total_runs"] == 2
    assert report["total_tokens_input"] == 300
    assert report["total_tokens_output"] == 150
    assert abs(report["total_cost"] - 0.045) < 0.001
