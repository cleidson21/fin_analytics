from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_import_history_is_paginated():
    response = client.get("/api/v1/investments/import/history")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["items"], list)

def test_positions_is_paginated():
    response = client.get("/api/v1/investments/positions")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
