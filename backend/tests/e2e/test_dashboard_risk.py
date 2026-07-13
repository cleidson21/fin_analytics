from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_risk_endpoint():
    response = client.get("/api/v1/investments/dashboard/risk")
    assert response.status_code == 200
    data = response.json()
    assert "current_drawdown" in data
    assert "sharpe" in data
