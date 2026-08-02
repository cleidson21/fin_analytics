import pytest
from app.services.core_finance.cashflow import CashflowService
from app.models.core_finance import Transaction
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base
from app.models.governance import ImportRun
from app.models.core_finance import Category, Goal, Subscription
from app.models.wealth import Position, Dividend, PortfolioEvolution, Benchmark
from app.models.ai_layer import Rule, PromptVersion, AiRun

# Setup an in-memory SQLite DB for testing
@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_expense_pacing_trend_down(db_session):
    # Setup data
    t1 = Transaction(
        id_economico="id1", source="MANUAL", import_run_id="run1",
        data=date(2026, 5, 15), descricao_original="Test 1", descricao_normalizada="Test",
        valor=200.0, valor_cents=20000, natureza="EXPENSE", perfil="CASA"
    )
    t2 = Transaction(
        id_economico="id2", source="MANUAL", import_run_id="run1",
        data=date(2026, 6, 15), descricao_original="Test 2", descricao_normalizada="Test",
        valor=100.0, valor_cents=10000, natureza="EXPENSE", perfil="CASA"
    )
    db_session.add(t1)
    db_session.add(t2)
    db_session.commit()

    service = CashflowService(db_session)
    pacing = service.get_expense_pacing("2026-06")
    
    assert pacing.current_month == "2026-06"
    assert pacing.previous_month == "2026-05"
    assert pacing.current_expenses == "R$ 100,00"
    assert pacing.previous_expenses == "R$ 200,00"
    assert pacing.trend == "down"
    assert pacing.severity == "good"
    assert "caíram 50,00%" in pacing.message

def test_expense_pacing_trend_up(db_session):
    t1 = Transaction(
        id_economico="id3", source="MANUAL", import_run_id="run2",
        data=date(2026, 5, 15), descricao_original="Test", descricao_normalizada="Test",
        valor=100.0, valor_cents=10000, natureza="EXPENSE", perfil="CASA"
    )
    t2 = Transaction(
        id_economico="id4", source="MANUAL", import_run_id="run2",
        data=date(2026, 6, 15), descricao_original="Test", descricao_normalizada="Test",
        valor=150.0, valor_cents=15000, natureza="EXPENSE", perfil="CASA"
    )
    db_session.add(t1)
    db_session.add(t2)
    db_session.commit()

    service = CashflowService(db_session)
    pacing = service.get_expense_pacing("2026-06")

    assert pacing.trend == "up"
    assert pacing.severity == "danger"
    assert "subiram 50,00%" in pacing.message
