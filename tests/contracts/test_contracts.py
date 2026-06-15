import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.api.schemas.auth import UserInDB

client = TestClient(app)

def mock_admin():
    return UserInDB(id="1", username="admin", role="ADMIN", email="admin@test.com", password_hash="123", active=1)

def test_transactions_contract():
    response = client.get("/api/v1/transactions")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "summary" in data
    if len(data["items"]) > 0:
        item = data["items"][0]
        assert "id" in item
        assert "date" in item
        assert "amount" in item
        assert "category" in item

def test_accounts_summary_contract():
    response = client.get("/api/v1/accounts/summary")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "institution" in data[0]
        assert "balance" in data[0]

def test_dashboard_summary_contract():
    from app.api.deps import require_authenticated
    app.dependency_overrides[require_authenticated] = mock_admin
    
    response = client.get("/api/v1/dashboard/summary")
    
    app.dependency_overrides.pop(require_authenticated, None)
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert "expenses" in data
    assert "income" in data
    assert "net_worth" in data

def test_catalog_contract():
    response = client.get("/api/v1/catalog/accounts")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "value" in data[0]
            assert "label" in data[0]

from unittest.mock import patch

@patch("app.api.routes.governance.import_service")
def test_governance_imports_contract(mock_gov_service):
    mock_gov_service.get_import_runs.return_value = [{
        "id": "run-1",
        "source_type": "MYPROFIT",
        "file_name": "test.csv",
        "checksum": "abc",
        "started_at": "2026-06-13T00:00:00",
        "finished_at": None,
        "status": "PENDING",
        "rows_read": 10,
        "rows_inserted": 10,
        "rows_updated": 0,
        "rows_failed": 0,
        "created_by": "admin"
    }]
    
    from app.api.deps import require_authenticated
    app.dependency_overrides[require_authenticated] = mock_admin
    response = client.get("/api/v1/governance/imports")
    app.dependency_overrides.pop(require_authenticated, None)
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

@patch("app.api.routes.prompts.service")
def test_governance_prompts_contract(mock_service):
    mock_service.get_all_prompts.return_value = [{
        "id": "p1", 
        "name": "System", 
        "version": 1, 
        "active": True, 
        "content": "hello",
        "created_at": "2026-06-13T00:00:00",
        "notes": "initial version"
    }]
    
    from app.api.deps import require_authenticated
    app.dependency_overrides[require_authenticated] = mock_admin
    response = client.get("/api/v1/governance/prompts")
    app.dependency_overrides.pop(require_authenticated, None)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        assert "id" in item
        assert "name" in item
        assert "version" in item
        assert "active" in item
        assert "created_at" in item

def test_governance_learning_metrics_contract():
    from unittest.mock import MagicMock
    from app.api.routes.learning import get_db
    mock_db = MagicMock()
    mock_db.get_learning_metrics.return_value = {"total_rules": 10, "problematic_rules": 2}
    
    app.dependency_overrides[get_db] = lambda: mock_db
    from app.api.deps import require_authenticated
    app.dependency_overrides[require_authenticated] = mock_admin
    
    response = client.get("/api/v1/governance/learning/metrics")
    
    app.dependency_overrides.pop(require_authenticated, None)
    app.dependency_overrides.pop(get_db, None)
    
    assert response.status_code == 200
    data = response.json()
    assert "total_rules" in data
    assert "problematic_rules" in data

@patch("app.api.routes.audit.service")
def test_governance_audit_contract(mock_service):
    mock_service.get_audit_runs.return_value = [{
        "id": "r1",
        "file_name": "test.csv",
        "source_type": "MYPROFIT",
        "started_at": "2026-06-13T00:00:00",
        "status": "CONFIRMED",
        "created_by": "admin",
        "rows_read": 10,
        "rows_inserted": 10,
        "rows_updated": 0,
        "rows_failed": 0
    }]
    
    from app.api.deps import require_authenticated
    app.dependency_overrides[require_authenticated] = mock_admin
    response = client.get("/api/v1/governance/audit")
    app.dependency_overrides.pop(require_authenticated, None)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]

def test_internal_health_contract():
    response = client.get("/api/v1/internal/health")
    assert response.status_code in [200, 401, 403]
    if response.status_code == 200:
        data = response.json()
        assert "financial_db" in data
        assert "governance_db" in data
        assert "uptime_seconds" in data
