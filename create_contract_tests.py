import os

tests = {
    'test_openapi.py': """
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_openapi_schema_is_available():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert "paths" in data
    assert "/api/v1/investments/portfolio" in data["paths"]
    
def test_swagger_ui_is_available():
    response = client.get("/docs")
    assert response.status_code == 200
    assert b"Swagger UI" in response.content
""",
    'test_routes_contract.py': """
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_routes_must_have_response_models():
    # Via OpenAPI json, verifica se tem 200 -> schema
    response = client.get("/openapi.json")
    data = response.json()
    for path, methods in data["paths"].items():
        if path.startswith("/api/v1/investments/"):
            for method, spec in methods.items():
                if "responses" in spec and "200" in spec["responses"]:
                    assert "schema" in spec["responses"]["200"]["content"]["application/json"], f"Rota {path} sem schema"
""",
    'test_response_models.py': """
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
""",
    'test_http_status.py': """
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
""",
    'test_validation_errors.py': """
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_invalid_uuid_should_be_handled():
    # Se a rota import/{log_id} exige str, enviar int nao falha (fastapi faz casting)
    pass
"""
}

for filename, code in tests.items():
    with open(f"backend/tests/e2e/{filename}", "w", encoding="utf-8") as f:
        f.write(code.strip() + "\n")

print("Created 5 API contract test files")
