from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_performance_endpoint():
    response = client.get("/api/v1/investments/dashboard/performance")
    assert response.status_code == 200
    data = response.json()
    assert "monthly_return" in data
    assert "rolling_returns" in data
