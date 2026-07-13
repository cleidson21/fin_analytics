import pytest
from datetime import date
from decimal import Decimal
from backend.domains.investments.services.market_data_service import MarketDataService

def test_market_service_get_market_data():
    service = MarketDataService()
    pt = service.get_market_data(date(2026, 1, 15))
    
    assert pt.date == date(2026, 1, 15)
    assert pt.ibov == Decimal("1.2")
    assert pt.cdi == Decimal("0.9")
    assert pt.ifix == Decimal("0.5")
    assert pt.ipca == Decimal("0.4")
    assert pt.sp500 == Decimal("1.5")
    assert pt.idiv == Decimal("1.0")
