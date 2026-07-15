from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_full_returns_models():
    response = client.get("/api/v1/investments/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "allocation" in data
    assert "performance" in data
    assert "risk" in data
