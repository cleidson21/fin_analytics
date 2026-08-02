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
