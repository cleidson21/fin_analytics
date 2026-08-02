import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import Base
import app.models.governance
import app.models.core_finance
from app.models.ai_layer import PromptVersion
from app.services.ai_layer.prompt_versions import PromptVersionService

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

def test_prompt_version_activation(db_session):
    pv1 = PromptVersion(id="pv1", name="v1", version=1, content="You are AI", active=1)
    pv2 = PromptVersion(id="pv2", name="v2", version=2, content="You are better AI", active=0)
    db_session.add_all([pv1, pv2])
    db_session.commit()

    service = PromptVersionService(db_session)
    
    # Check active
    active = service.get_active_version()
    assert active.id == "pv1"
    
    # Activate v2 (should deactivate v1)
    service.activate_version("pv2")
    
    db_session.refresh(pv1)
    db_session.refresh(pv2)
    
    assert pv1.active == 0
    assert pv2.active == 1
    
    # Active should now be v2
    active_now = service.get_active_version()
    assert active_now.id == "pv2"
