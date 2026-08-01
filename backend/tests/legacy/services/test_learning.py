import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import Base
import app.models.governance
import app.models.core_finance
from app.models.core_finance import Transaction
from app.services.ai_layer.learning import LearningService

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

def test_learning_capture_and_few_shot(db_session):
    # Only USER or MANUAL should be captured
    t1 = Transaction(
        id_economico="t1", source="MANUAL", import_run_id="run1", data=date.today(),
        descricao_original="PGTO NETFLIX", descricao_normalizada="PGTO NETFLIX", valor=-50.0, valor_cents=-5000, natureza="EXPENSE",
        perfil="CASA", classificacao_fonte="USER", macro_categoria="Lazer", sub_categoria="Streaming"
    )
    t2 = Transaction(
        id_economico="t2", source="MANUAL", import_run_id="run1", data=date.today(),
        descricao_original="UBER", descricao_normalizada="UBER", valor=-20.0, valor_cents=-2000, natureza="EXPENSE",
        perfil="CASA", classificacao_fonte="MANUAL", macro_categoria="Transporte", sub_categoria="App"
    )
    t3 = Transaction(
        id_economico="t3", source="MANUAL", import_run_id="run1", data=date.today(),
        descricao_original="MERCADO", descricao_normalizada="MERCADO", valor=-100.0, valor_cents=-10000, natureza="EXPENSE",
        perfil="CASA", classificacao_fonte="AI", macro_categoria="Alimentacao", sub_categoria="Mercado"
    )
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    service = LearningService(db_session)
    dataset = service.capture_manual_classifications()
    
    # Should only capture t1 and t2
    assert len(dataset) == 2
    ids = [d["id_economico"] for d in dataset]
    assert "t1" in ids
    assert "t2" in ids

    # Few-shot generation
    few_shot = service.export_few_shot_examples(limit=2)
    assert "Input: PGTO NETFLIX -> Output: {\"macro_categoria\": \"Lazer\", \"sub_categoria\": \"Streaming\"}" in few_shot
    assert "Input: UBER -> Output: {\"macro_categoria\": \"Transporte\", \"sub_categoria\": \"App\"}" in few_shot
