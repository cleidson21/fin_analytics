import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base, get_db
from app.models.core_finance import Transaction, Goal, Category
from app.models.governance import ImportRun
from app.services.core_finance.cashflow import CashflowService
from app.services.core_finance.goals import GoalService

# Import API router to test endpoints
from fastapi import FastAPI
from app.api.routes.dashboard import router

from sqlalchemy.pool import StaticPool

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

@pytest.fixture
def client(db_session):
    app = FastAPI()
    app.include_router(router)
    
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

def test_pacing_previous_month_zero(db_session):
    # Only transactions in current month, nothing in previous
    t1 = Transaction(
        id_economico="id1", source="MANUAL", import_run_id="run1",
        data=date(2026, 6, 15), descricao_original="Test", descricao_normalizada="Test",
        valor=100.0, valor_cents=10000, natureza="EXPENSE", perfil="CASA"
    )
    db_session.add(t1)
    db_session.commit()

    service = CashflowService(db_session)
    pacing = service.get_expense_pacing("2026-06")

    assert pacing.previous_expenses == "R$ 0,00"
    assert pacing.delta_percentage == "100,00" # When previous is 0 and current > 0, delta is 100%

def test_pacing_negative_revenues_handled(db_session):
    # What if there are income transactions? They shouldn't affect expense pacing
    # What if expense is negative (refund)?
    t_income = Transaction(
        id_economico="id2", source="MANUAL", import_run_id="run1",
        data=date(2026, 6, 15), descricao_original="Income", descricao_normalizada="Income",
        valor=500.0, valor_cents=50000, natureza="INCOME", perfil="CASA"
    )
    t_refund = Transaction(
        id_economico="id3", source="MANUAL", import_run_id="run1",
        data=date(2026, 6, 16), descricao_original="Refund", descricao_normalizada="Refund",
        valor=-50.0, valor_cents=-5000, natureza="EXPENSE", perfil="CASA" # Refund is negative expense
    )
    t_expense = Transaction(
        id_economico="id4", source="MANUAL", import_run_id="run1",
        data=date(2026, 6, 17), descricao_original="Expense", descricao_normalizada="Expense",
        valor=100.0, valor_cents=10000, natureza="EXPENSE", perfil="CASA"
    )
    db_session.add_all([t_income, t_refund, t_expense])
    db_session.commit()

    service = CashflowService(db_session)
    pacing = service.get_expense_pacing("2026-06")
    
    # Net expense = abs(100 - 50) = 50
    assert pacing.current_expenses == "R$ 50,00"

def test_goal_service_coverage(db_session):
    # Setup categories and goals
    cat_food = Category(id="cat1", name="Food", category_type="OUT")
    cat_leisure = Category(id="cat2", name="Leisure", category_type="OUT")
    db_session.add_all([cat_food, cat_leisure])

    goal_food = Goal(id="g1", category_id="cat1", limit_cents=100000, severity_level="WARNING", active=1) # 1000 limit
    db_session.add(goal_food)

    # Note: cat_leisure has no goal. It should not be processed by GoalService, covering "categorias sem meta".

    # Transactions
    t1 = Transaction(
        id_economico="id1", source="MANUAL", import_run_id="run1", category_id="cat1",
        data=date(2026, 6, 10), descricao_original="Supermarket", descricao_normalizada="Super",
        valor=800.0, valor_cents=80000, natureza="EXPENSE", perfil="CASA"
    )
    t2 = Transaction(
        id_economico="id2", source="MANUAL", import_run_id="run1", category_id="cat1",
        data=date(2026, 6, 11), descricao_original="Restaurant", descricao_normalizada="Rest",
        valor=250.0, valor_cents=25000, natureza="EXPENSE", perfil="CASA"
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    service = GoalService(db_session)
    results = service.check_goal_status(2026, 6)

    # Should only return one goal (cat1)
    assert len(results) == 1
    res = results[0]
    assert res["category_id"] == "cat1"
    assert res["limit_amount"] == 1000.0
    assert res["spent_amount"] == 1050.0 # 800 + 250
    assert res["percentage_used"] == 105.0
    assert res["status"] == "EXCEEDED"
    assert res["severity"] == "CRITICAL"

def test_dashboard_summary_endpoint(client, db_session):
    # Add some data to ensure summary returns correct sum
    t_income = Transaction(
        id_economico="id_inc", source="MANUAL", import_run_id="run1",
        data=date.today(), descricao_original="Income", descricao_normalizada="Income",
        valor=1500.0, valor_cents=150000, natureza="INCOME", perfil="CASA"
    )
    t_exp = Transaction(
        id_economico="id_exp", source="MANUAL", import_run_id="run1",
        data=date.today(), descricao_original="Expense", descricao_normalizada="Expense",
        valor=500.0, valor_cents=50000, natureza="EXPENSE", perfil="CASA"
    )
    db_session.add_all([t_income, t_exp])
    db_session.commit()

    month_str = date.today().strftime("%Y-%m")
    response = client.get(f"/dashboard/summary?month={month_str}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["income"] == "R$ 1.500,00"
    assert data["expenses"] == "R$ 500,00"
    assert data["balance"] == "R$ 1.000,00"
