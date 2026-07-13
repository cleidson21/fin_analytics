import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_import_cei_endpoint():
    """Testa o upload de um mock de arquivo CEI."""
    files = {'file': ('b3_negociacao_2024.csv', b'Ticker,Data,Qtd,Preco\nPETR4,2024-01-01,100,35.0', 'text/csv')}
    response = client.post("/api/v1/investments/import/cei", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "CEI"
    assert data["file_name"] == "b3_negociacao_2024.csv"
    assert data["success"] is True
    # Hashes and duplicates simulation verification
    assert data["duplicates_detected"] >= 0

def test_import_open_finance_endpoint():
    """Testa o upload de um payload de Open Finance."""
    files = {'file': ('nubank_payload.json', b'{"trades": []}', 'application/json')}
    response = client.post("/api/v1/investments/import/open-finance", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "OPEN_FINANCE"
    assert data["file_name"] == "nubank_payload.json"
    assert data["success"] is True

def test_import_history_endpoint():
    """Testa a leitura do histórico de importações."""
    response = client.get("/api/v1/investments/import/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
