import sys
import os
from datetime import date
from decimal import Decimal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.domains.investments.repositories.historical_price_repository import HistoricalPriceRepository

def test_historical_price_repository_loading():
    """
    Testa se o HistoricalPriceRepository carrega corretamente
    os arquivos CSV em memória no formato de série temporal ordenada.
    """
    # Forçar recarregamento garantindo que usamos a pasta de banco local
    repo = HistoricalPriceRepository(data_dir="database/prices")
    
    # Testa Ticker que existe
    series_petr4 = repo.get_price_series("PETR4")
    assert series_petr4 is not None
    assert len(series_petr4) > 0
    
    # Valida formato e ordenação
    first_date, first_price = series_petr4[0]
    last_date, last_price = series_petr4[-1]
    
    assert isinstance(first_date, date)
    assert isinstance(first_price, Decimal)
    assert first_date < last_date
    
    # Testa Ticker Inexistente
    series_unknown = repo.get_price_series("UNKNOWN3")
    assert series_unknown == []

    print("\ntest_historical_price_repository_loading passed: CSVs carregados e parseados em Decimal com sucesso.")
