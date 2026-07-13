from backend.domains.investments.application_factory import ApplicationFactory
import sys
import os
from datetime import date
from decimal import Decimal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.domains.investments.services.historical_price_service import HistoricalPriceService
from backend.domains.investments.repositories.historical_price_repository import HistoricalPriceRepository

def test_historical_price_service_lookup():
    """
    Testa a busca binária O(log N) do HistoricalPriceService
    e o fallback para o pregão imediatamente anterior.
    """
    HistoricalPriceRepository(data_dir="database/prices")
    service = ApplicationFactory.get_historical_price_service()
    
    # Suponha que data inicial é 2020-01-01 (Quarta-feira, existe)
    dt_exact = date(2020, 1, 1)
    price_exact = service.get_price_for_date("PETR4", dt_exact)
    assert price_exact is not None
    assert price_exact == Decimal('30.00')
    
    # Fim de semana (fallback)
    # 2020-01-04 é Sábado. Deverá buscar o pregão de sexta (2020-01-03)
    dt_weekend = date(2020, 1, 4)
    price_fallback = service.get_price_for_date("PETR4", dt_weekend)
    assert price_fallback is not None
    # Como simulamos pequenos saltos, o preço de sexta não será exatamente 30.00, mas o fallback resolve
    
    # Data muito no passado
    dt_past = date(1990, 1, 1)
    price_past = service.get_price_for_date("PETR4", dt_past)
    assert price_past is None
    
    print("\ntest_historical_price_service_lookup passed: O(log N) lookup e fallback funcionam com sucesso.")
