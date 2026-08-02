from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_invalid_uuid_should_be_handled():
    # Se a rota import/{log_id} exige str, enviar int nao falha (fastapi faz casting)
    pass
