import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from datetime import date
from backend.domains.investments.repositories.trade_repository import TradeRepository
from backend.domains.investments.repositories.snapshot_repository import SnapshotRepository
from backend.domains.investments.engines.position_engine import PositionEngine
from backend.domains.investments.engines.valuation_engine import ValuationEngine
from backend.domains.investments.engines.wealth_engine import WealthEngine

# Test Database Connection (Using the local dev SQLite for simplicity in these integration tests, 
# or an in-memory db. Since we need the schema and seeded data, we will use a dummy in-memory schema)

@pytest.fixture
def db_session():
    # Setup an in-memory SQLite with the required schema
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    from sqlalchemy import text
    session.execute(text("CREATE TABLE accounts (id TEXT PRIMARY KEY, name TEXT);"))
    session.execute(text("CREATE TABLE assets (id TEXT PRIMARY KEY, ticker TEXT, asset_class TEXT);"))
    session.execute(text("CREATE TABLE broker_notes (id TEXT PRIMARY KEY, account_id TEXT);"))
    session.execute(text("""
        CREATE TABLE trades (
            id TEXT PRIMARY KEY, asset_id TEXT, account_id TEXT, 
            type TEXT, trade_date TEXT, quantity REAL, unit_price INTEGER, 
            gross_value INTEGER, source TEXT, created_at TEXT
        );
    """))
    session.execute(text("""
        CREATE TABLE position_snapshots (
            id TEXT PRIMARY KEY, account_id TEXT, asset_id TEXT, 
            reference_date TEXT, quantity REAL, unit_price INTEGER, 
            total_value INTEGER, source_system TEXT, metadata TEXT, created_at TEXT
        );
    """))
    session.execute(text("INSERT INTO accounts VALUES ('acc-1', 'NU INVEST');"))
    session.execute(text("INSERT INTO assets VALUES ('ast-1', 'BBAS3', 'STOCK');"))
    session.execute(text("INSERT INTO assets VALUES ('ast-2', 'MXRF11', 'FII');"))
    session.commit()
    yield session
    session.close()

def test_trade_repository_list_all(db_session):
    # Seed data
    db_session.execute(text("""
        INSERT INTO trades VALUES 
        ('t1', 'ast-1', 'acc-1', 'BUY', '2023-01-01', 100, 4500, 450000, 'B3', '2023-01-01T10:00:00Z'),
        ('t2', 'ast-2', 'acc-1', 'BUY', '2023-01-02', 200, 1000, 200000, 'B3', '2023-01-02T10:00:00Z')
    """))
    db_session.commit()
    
    repo = TradeRepository()
    trades = repo.list_all(db_session)
    assert len(trades) == 2
    assert trades[0].ticker == 'BBAS3'
    assert float(trades[0].quantity) == 100.0
    assert float(trades[0].unit_price) == 45.0
    
def test_trade_repository_list_by_asset(db_session):
    db_session.execute(text("""
        INSERT INTO trades VALUES 
        ('t3', 'ast-1', 'acc-1', 'SELL', '2023-02-01', 50, 5000, 250000, 'B3', '2023-02-01T10:00:00Z')
    """))
    db_session.commit()
    
    repo = TradeRepository()
    trades = repo.list_by_asset(db_session, 'BBAS3')
    assert len(trades) == 1
    assert trades[0].operation_type.value == 'SELL'

def test_trade_repository_list_by_account(db_session):
    db_session.execute(text("""
        INSERT INTO trades VALUES 
        ('t4', 'ast-1', 'acc-1', 'BUY', '2023-03-01', 10, 5000, 50000, 'B3', '2023-03-01T10:00:00Z')
    """))
    db_session.commit()
    repo = TradeRepository()
    # Mocking the alias resolver since we only have 'NU INVEST'
    repo._broker_resolver.resolve = lambda x: 'NU INVEST'
    trades = repo.list_by_account(db_session, 'NuInvest')
    assert len(trades) == 1

def test_snapshot_repository_read(db_session):
    db_session.execute(text("""
        INSERT INTO position_snapshots VALUES 
        ('s1', 'acc-1', 'ast-1', '2023-01-01', 100, 4500, 450000, 'B3', '{}', '2023-01-01T10:00:00Z'),
        ('s2', 'acc-1', 'ast-1', '2023-02-01', 150, 4600, 690000, 'B3', '{}', '2023-02-01T10:00:00Z')
    """))
    db_session.commit()
    
    repo = SnapshotRepository()
    all_snaps = repo.list_all(db_session)
    assert len(all_snaps) == 2
    
    latest_asset = repo.latest_by_asset(db_session, 'BBAS3')
    assert len(latest_asset) == 1
    assert float(latest_asset[0].quantity) == 150.0

    repo._broker_resolver.resolve = lambda x: 'NU INVEST'
    latest_account = repo.latest_by_account(db_session, 'NU INVEST')
    assert len(latest_account) == 1
    assert float(latest_account[0].quantity) == 150.0

def test_engine_integration_empty(db_session):
    repo = TradeRepository()
    snap_repo = SnapshotRepository()
    
    trades = repo.list_all(db_session) # Currently has 1 trade from earlier test
    # Wait, the db_session fixture yields a fresh in-memory db each time? 
    # Yes, because it's yielded per test. Wait! Let's check the scope. It is function scope by default.
    # So it should be empty for this test if we don't insert.
    assert len(trades) == 0
    
    pos_engine = PositionEngine()
    positions = pos_engine.calculate_position(trades, [])
    
    val_engine = ValuationEngine()
    valuations = val_engine.calculate_valuation(positions, {})
    
    wealth_engine = WealthEngine()
    wealth = wealth_engine.calculate(valuations)
    
    assert wealth.total_market_value == 0

if __name__ == "__main__":
    pytest.main(["-v", __file__])
