from fastapi.testclient import TestClient
from backend.main import app
import uuid

client = TestClient(app)

def test_get_import_not_found_returns_404():
    response = client.get(f"/api/v1/investments/import/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Log não encontrado"

def test_delete_import_not_found_returns_404():
    response = client.delete(f"/api/v1/investments/import/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Log não encontrado"
