
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.domains.investments.engines.valuation_engine import ValuationEngine
from backend.domains.investments.services.history_service import HistoryService
import inspect

def test_valuation_engine_di():
    sig = inspect.signature(ValuationEngine.__init__)
    assert 'historical_price_service' in sig.parameters

def test_history_service_di():
    sig = inspect.signature(HistoryService.__init__)
    assert 'pos_engine' in sig.parameters
    assert 'val_engine' in sig.parameters
