import os

tests = {
    'test_dashboard_summary.py': """
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
""",
    'test_dashboard_allocation.py': """
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_allocation_endpoint():
    response = client.get("/api/v1/investments/dashboard/allocation")
    assert response.status_code == 200
    data = response.json()
    assert "by_class" in data
    assert "by_institution" in data
""",
    'test_dashboard_risk.py': """
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_risk_endpoint():
    response = client.get("/api/v1/investments/dashboard/risk")
    assert response.status_code == 200
    data = response.json()
    assert "current_drawdown" in data
    assert "sharpe" in data
""",
    'test_dashboard_performance.py': """
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_performance_endpoint():
    response = client.get("/api/v1/investments/dashboard/performance")
    assert response.status_code == 200
    data = response.json()
    assert "monthly_return" in data
    assert "rolling_returns" in data
""",
    'test_dashboard_router.py': """
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_dashboard_full_endpoint():
    response = client.get("/api/v1/investments/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "allocation" in data
    assert "performance" in data
    assert "risk" in data
"""
}

for filename, code in tests.items():
    with open(f"backend/tests/e2e/{filename}", "w", encoding="utf-8") as f:
        f.write(code.strip() + "\n")

print("Created test files")
