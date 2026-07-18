import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.domains.identity.router import get_current_user

app.dependency_overrides[get_current_user] = lambda: {"sub": "admin", "email": "admin@example.com"}
client = TestClient(app)

def test_list_positions_returns_correct_dto():
    response = client.get("/api/v1/governance/positions?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    
    if data["total"] > 0:
        first_item = data["items"][0]
        # Check against PositionUIRepresentationDTO fields
        assert "ticker" in first_item
        assert "quantidade" in first_item
        assert "valor_investido" in first_item
        assert "valor_atual" in first_item
        assert "ganho" in first_item
        assert "peso" in first_item

def test_list_dividends_returns_correct_dto():
    response = client.get("/api/v1/governance/dividends?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    
    if data["total"] > 0:
        first_item = data["items"][0]
        assert "id_economico" in first_item
        assert "ticker" in first_item
        assert "valor" in first_item
        assert "data_pagamento" in first_item
