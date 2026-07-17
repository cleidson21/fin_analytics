import pytest
import requests

def test_backend_health():
    response = requests.get("http://localhost:8000/api/v1/health")
    assert response.status_code == 200

def test_openapi_docs():
    response = requests.get("http://localhost:8000/openapi.json")
    assert response.status_code == 200

def test_plugins_status():
    response = requests.get("http://localhost:8000/api/v1/plugins/status")
    assert response.status_code == 200
    data = response.json()
    assert data["system_status"] == "healthy"
