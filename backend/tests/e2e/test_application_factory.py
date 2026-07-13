
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.domains.investments.application_factory import ApplicationFactory

def test_singleton_behavior():
    repo1 = ApplicationFactory.get_market_data_repository()
    repo2 = ApplicationFactory.get_market_data_repository()
    assert repo1 is repo2

    svc1 = ApplicationFactory.get_portfolio_application_service()
    svc2 = ApplicationFactory.get_portfolio_application_service()
    assert svc1 is svc2
