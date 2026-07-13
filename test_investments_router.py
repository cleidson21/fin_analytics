import pytest
from fastapi.testclient import TestClient
from backend.main import app
from decimal import Decimal
import json

client = TestClient(app)

# Helper para comparar Decimals caso o JSON serialize como numérico/string
# No FastAPI o Pydantic pode converter Decimal para float ou string no JSON de saída
# Assumimos que está sendo serializado (float no json para leitura).

def test_router_portfolio_empty():
    response = client.get("/api/v1/investments/portfolio")
    assert response.status_code == 200
    data = response.json()
    assert data["total_market_value"] == '0' or data["total_market_value"] == 0.0
    assert data["asset_count"] == 0
    assert data["by_asset"] == []

def test_router_positions_empty():
    response = client.get("/api/v1/investments/positions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_router_performance_empty():
    response = client.get("/api/v1/investments/performance")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert data["metrics"]["cagr"] == '0' or data["metrics"]["cagr"] == 0.0

def test_router_allocation_empty():
    response = client.get("/api/v1/investments/allocation")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_router_institutions_empty():
    response = client.get("/api/v1/investments/institutions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

if __name__ == "__main__":
    pytest.main(["-v", __file__])
