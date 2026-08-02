
import sys, os
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.domains.investments.application_factory import ApplicationFactory

def test_market_app_instantiation():
    app = ApplicationFactory.get_market_application_service()
    assert app is not None
    assert app.historical_price_service is not None
