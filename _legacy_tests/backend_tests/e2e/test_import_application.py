
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.domains.investments.application_factory import ApplicationFactory

def test_import_app_instantiation():
    app = ApplicationFactory.get_import_application_service()
    assert app is not None
    assert app.import_service is not None
    assert app.import_service.parse_service is not None
