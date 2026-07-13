from backend.domains.investments.application_factory import ApplicationFactory
import sys
import os
from datetime import date
from decimal import Decimal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.domains.investments.engines.valuation_engine import ValuationEngine
from backend.domains.investments.engines.position_engine import PositionResult
from backend.domains.investments.repositories.historical_price_repository import HistoricalPriceRepository

def test_historical_valuation():
    """
    Testa se a ValuationEngine aciona corretamente a HistoricalPriceService
    quando processa uma data histórica e se utiliza o preço atual
    quando a data é recente.
    """
    HistoricalPriceRepository(data_dir="database/prices")
    
    positions = [
        PositionResult(
            ticker="PETR4",
            institution="XP",
            quantity=Decimal('100'),
            average_price=Decimal('25'),
            invested_value=Decimal('2500')
        )
    ]
    
    # Preços atuais mockados
    market_prices = {"PETR4": Decimal('40')}
    
    engine = ApplicationFactory.get_valuation_engine()
    
    # 1. Valuation Atual (reference_date = None)
    val_current = engine.calculate_valuation(positions, market_prices, reference_date=None)
    assert val_current[0].current_price == Decimal('40')
    assert val_current[0].market_value == Decimal('4000')
    
    # 2. Valuation Histórico (reference_date passado)
    # 2020-01-01 -> Preço simulado era ~30.00
    val_hist = engine.calculate_valuation(positions, market_prices, reference_date=date(2020, 1, 1))
    assert val_hist[0].current_price == Decimal('30.00')
    assert val_hist[0].market_value == Decimal('3000.00')
    
    # 3. Valuation Histórico Inexistente (fallback para custo de aquisição)
    val_hist_none = engine.calculate_valuation(positions, market_prices, reference_date=date(1990, 1, 1))
    assert val_hist_none[0].current_price == Decimal('25') # assume average_price
    
    print("\ntest_historical_valuation passed: ValuationEngine escolhe corretamente a fonte de preços baseada no reference_date.")
