import pytest
from datetime import date
from decimal import Decimal
from backend.domains.investments.repositories.market_data_repository import MarketDataRepository

def test_market_repository_load():
    repo = MarketDataRepository(data_dir="database/benchmarks")
    val = repo.get_by_date("ibov", date(2026, 1, 15))
    assert val == Decimal("1.2") # fallback to closest previous date
    
    val2 = repo.get_by_date("cdi", date(2026, 1, 1))
    assert val2 == Decimal("0.9")
    
    val_none = repo.get_by_date("ibov", date(2025, 12, 31))
    assert val_none == Decimal("0.0")

def test_market_repository_interval():
    repo = MarketDataRepository(data_dir="database/benchmarks")
    interval = repo.get_interval("ibov", date(2026, 1, 1), date(2026, 2, 1))
    assert len(interval) == 1
    assert interval[0][0] == date(2026, 1, 1)
    assert interval[0][1] == Decimal("1.2")
