from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_allocation_endpoint():
    response = client.get("/api/v1/investments/dashboard/allocation")
    assert response.status_code == 200
    data = response.json()
    assert "by_class" in data
    assert "by_institution" in data
