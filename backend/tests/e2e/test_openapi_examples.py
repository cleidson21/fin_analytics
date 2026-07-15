from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_openapi_has_examples():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    # Check if RiskDashboardDTO has example
    components = data.get("components", {}).get("schemas", {})
    risk_dto = components.get("RiskDashboardDTO", {})
    assert "example" in risk_dto, "RiskDashboardDTO should have an example"
