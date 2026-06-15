import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import Base
from app.models.wealth import Position, Dividend, PortfolioEvolution, Benchmark
from app.models.governance import ImportRun

from app.services.wealth.positions import PositionService
from app.services.wealth.dividends import DividendService
from app.services.wealth.allocation import AllocationService
from app.services.wealth.evolution import EvolutionService

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

def test_yoc_calculations(db_session):
    # Setup
    t1 = Position(
        ticker="WEGE3", data_snapshot=date.today(), source="B3", 
        quantidade=100.0, preco_medio=10.0, total_investido=1000.0, 
        preco_atual=20.0, total_atual=2000.0, ganho=1000.0, classe_ativo="Acoes",
        import_run_id="run1"
    )
    t2 = Position(
        ticker="ITUB4", data_snapshot=date.today(), source="B3", 
        quantidade=100.0, preco_medio=20.0, total_investido=2000.0, 
        preco_atual=25.0, total_atual=2500.0, ganho=500.0, classe_ativo="Acoes",
        import_run_id="run1"
    )
    # Ativo sem dividendos: WEGE3 has NO dividends.
    # Ativo com dividendos: ITUB4 has 200.0 dividends.
    d1 = Dividend(
        id_economico="d1", source="B3", ticker="ITUB4", tipo_evento="DIVIDENDO",
        data_pagamento=date.today(), valor_liquido=200.0, import_run_id="run1"
    )
    db_session.add_all([t1, t2, d1])
    db_session.commit()

    service = DividendService(db_session)
    yoc_data = service.calculate_yoc()

    # Portfolio YOC: (200 / 3000) * 100 = 6.666%
    assert abs(yoc_data["portfolio_yoc"] - 6.666) < 0.01

    assets = yoc_data["assets"]
    
    # Ativo sem dividendos
    assert assets["WEGE3"]["dividends_received"] == 0.0
    assert assets["WEGE3"]["yoc_pct"] == 0.0

    # Ativo com dividendos
    assert assets["ITUB4"]["dividends_received"] == 200.0
    assert assets["ITUB4"]["yoc_pct"] == 10.0 # 200/2000 * 100

def test_allocation_percentage(db_session):
    t1 = Position(
        ticker="WEGE3", data_snapshot=date.today(), source="B3", 
        quantidade=100.0, preco_medio=10.0, total_investido=1000.0, 
        preco_atual=20.0, total_atual=1000.0, ganho=0.0, classe_ativo="Acoes",
        import_run_id="run1"
    )
    t2 = Position(
        ticker="KNRI11", data_snapshot=date.today(), source="B3", 
        quantidade=10.0, preco_medio=100.0, total_investido=1000.0, 
        preco_atual=100.0, total_atual=3000.0, ganho=2000.0, classe_ativo="FIIs",
        import_run_id="run1"
    )
    t3 = Position(
        ticker="CASH3", data_snapshot=date.today(), source="B3", 
        quantidade=1000.0, preco_medio=1.0, total_investido=1000.0, 
        preco_atual=1.0, total_atual=1000.0, ganho=0.0, classe_ativo=None, # Classes vazias
        import_run_id="run1"
    )
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    service = AllocationService(db_session)
    alloc = service.get_allocation()

    assert alloc["total_portfolio"] == 5000.0
    classes = alloc["classes"]

    assert classes["Acoes"]["percentual"] == 20.0 # 1000 / 5000
    assert classes["FIIs"]["percentual"] == 60.0 # 3000 / 5000
    assert classes["NAO_CLASSIFICADO"]["percentual"] == 20.0 # 1000 / 5000 (classes vazias)

    # Soma deve fechar em 100%
    total_pct = sum(c["percentual"] for c in classes.values())
    assert abs(total_pct - 100.0) < 0.01

def test_alpha_benchmark_superior_inferior_igual(db_session):
    # Setup
    evo = PortfolioEvolution(
        reference_month=date(2026, 6, 1), rentabilidade_mensal_pct=1.5,
        patrimonio_cents=1000000, import_run_id="run1"
    )
    
    b_sup = Benchmark(reference_date=date(2026, 6, 1), type="IBOV", value_pct=2.0)
    b_inf = Benchmark(reference_date=date(2026, 6, 1), type="CDI", value_pct=1.0)
    b_igu = Benchmark(reference_date=date(2026, 6, 1), type="IPCA", value_pct=1.5)
    
    db_session.add_all([evo, b_sup, b_inf, b_igu])
    db_session.commit()

    service = EvolutionService(db_session)

    # Benchmark Superior
    alpha_sup = service.get_evolution_and_alpha("2026-06", "IBOV")
    assert alpha_sup["alpha"] == -0.5

    # Benchmark Inferior
    alpha_inf = service.get_evolution_and_alpha("2026-06", "CDI")
    assert alpha_inf["alpha"] == 0.5

    # Benchmark Igual
    alpha_igu = service.get_evolution_and_alpha("2026-06", "IPCA")
    assert alpha_igu["alpha"] == 0.0
