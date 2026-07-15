import os

tests = {
    'test_pagination.py': """
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
""",
    'test_openapi_examples.py': """
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
"""
}

for filename, code in tests.items():
    with open(f"backend/tests/e2e/{filename}", "w", encoding="utf-8") as f:
        f.write(code.strip() + "\n")

print("Created 10.12 tests")
