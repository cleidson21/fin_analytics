from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_summary_endpoint():
    response = client.get("/api/v1/investments/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "current_wealth" in data
    assert "twr" in data
    assert "sharpe" in data
