
import sys, os
from datetime import date
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.domains.investments.application_factory import ApplicationFactory

def test_portfolio_app_instantiation():
    app = ApplicationFactory.get_portfolio_application_service()
    assert app is not None
    assert app.position_engine is not None
    assert app.valuation_engine is not None
