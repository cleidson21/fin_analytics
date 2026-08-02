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
