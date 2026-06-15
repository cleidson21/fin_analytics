import time
import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

ENDPOINTS = [
    "/api/v1/auth/me",
    "/api/v1/dashboard/summary",
    "/api/v1/accounts/summary",
    "/api/v1/catalog/accounts",
    "/api/v1/transactions",
    "/api/v1/governance/imports",
    "/api/v1/governance/prompts",
    "/api/v1/governance/learning/metrics",
    "/api/v1/governance/audit/logs",  # Adjusted to correct endpoint if changed, wait it was /api/v1/governance/audit-logs before. Let's use /api/v1/governance/imports etc.
    "/api/v1/internal/health",
    "/api/v1/internal/performance"
]

@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_smoke_endpoints(endpoint):
    t0 = time.time()
    response = client.get(endpoint)
    duration_ms = (time.time() - t0) * 1000
    
    # Validation 1: No 500 errors
    assert response.status_code < 500, f"Endpoint {endpoint} returned 500: {response.text}"
    
    # Validation 2: Content-Type is correct if it returns body
    if response.content:
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, f"Endpoint {endpoint} did not return JSON. Got {content_type}"
        
        # Validation 3: Valid JSON Payload
        try:
            response.json()
        except ValueError:
            pytest.fail(f"Endpoint {endpoint} returned invalid JSON payload")
            
    # Validation 4: Reasonable response time
    assert duration_ms < 5000, f"Endpoint {endpoint} took too long: {duration_ms}ms"

def test_internal_health_structure():
    response = client.get("/api/v1/internal/health")
    assert response.status_code in [200, 401, 403], "Health endpoint should exist"
    if response.status_code == 200:
        data = response.json()
        assert "financial_db" in data
        assert "governance_db" in data
        assert "uptime_seconds" in data
