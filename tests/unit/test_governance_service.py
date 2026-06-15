import pytest
from unittest.mock import MagicMock
from app.api.services.governance_service import GovernanceService

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def governance_service(mock_repo):
    service = GovernanceService()
    service.repo = mock_repo
    return service

def test_get_learning_metrics(governance_service, mock_repo):
    mock_repo.get_learning_metrics.return_value = {"total_hits": 100}
    result = governance_service.get_learning_metrics()
    assert result["total_hits"] == 100
    mock_repo.get_learning_metrics.assert_called_once()

def test_get_top_rules(governance_service, mock_repo):
    mock_repo.get_top_rules.return_value = []
    assert governance_service.get_top_rules(10) == []

def test_get_problematic_rules(governance_service, mock_repo):
    mock_repo.get_problematic_rules.return_value = []
    assert governance_service.get_problematic_rules(10) == []

def test_get_prompt_version_exists(governance_service, mock_repo):
    mock_repo.get_prompt_version_exists.return_value = True
    assert governance_service.get_prompt_version_exists("a", 1) is True

def test_insert_prompt_version(governance_service, mock_repo):
    mock_repo.insert_prompt_version.return_value = True
    assert governance_service.insert_prompt_version("a", "b", 1, "c", 1, "d") is True

def test_get_all_prompts_empty(governance_service, mock_repo):
    mock_repo.get_all_prompts.return_value = []
    result = governance_service.get_all_prompts(active_only=True)
    assert len(result) == 0
    mock_repo.get_all_prompts.assert_called_once_with(True)

def test_get_prompt_by_id(governance_service, mock_repo):
    mock_repo.get_prompt_by_id.return_value = {}
    assert governance_service.get_prompt_by_id("1") == {}

def test_get_rules_audit(governance_service, mock_repo):
    mock_repo.get_rules_audit.return_value = [{"rule": "test", "status": "active"}]
    result = governance_service.get_rules_audit(limit=10, offset=0, status="active")
    assert len(result) == 1
    mock_repo.get_rules_audit.assert_called_once_with(limit=10, offset=0, status="active")

def test_activate_prompt_version_success(governance_service, mock_repo):
    mock_repo.activate_prompt_version.return_value = True
    result = governance_service.activate_prompt_version("uuid-123")
    assert result is True
    mock_repo.activate_prompt_version.assert_called_once_with("uuid-123")

def test_get_audit_runs(governance_service, mock_repo):
    mock_repo.get_audit_runs.return_value = [{"run_id": "123", "status": "SUCCESS"}]
    result = governance_service.get_audit_runs(status_filter="SUCCESS")
    assert len(result) == 1
    mock_repo.get_audit_runs.assert_called_once_with("SUCCESS")

def test_get_audit_rollbacks(governance_service, mock_repo):
    mock_repo.get_audit_rollbacks.return_value = []
    assert governance_service.get_audit_rollbacks() == []

def test_get_database_path(governance_service, mock_repo):
    mock_repo.db_path = "gov.db"
    assert governance_service.get_database_path() == "gov.db"

def test_vacuum_database(governance_service, mock_repo):
    mock_conn = MagicMock()
    mock_repo._get_connection.return_value.__enter__.return_value = mock_conn
    governance_service.vacuum_database()
    mock_conn.execute.assert_called_with("VACUUM")

def test_analyze_database(governance_service, mock_repo):
    mock_conn = MagicMock()
    mock_repo._get_connection.return_value.__enter__.return_value = mock_conn
    governance_service.analyze_database()
    mock_conn.execute.assert_called_with("ANALYZE")

def test_get_admin_metrics(governance_service, mock_repo):
    mock_conn = MagicMock()
    mock_repo._get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.execute.return_value.fetchone.return_value = [10]
    res = governance_service.get_admin_metrics()
    assert res['total_import_runs'] == 10

def test_get_table_counts(governance_service, mock_repo):
    mock_conn = MagicMock()
    mock_repo._get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.execute.return_value.fetchone.return_value = [10]
    res = governance_service.get_table_counts()
    assert len(res) == 7

def test_get_integrity_metrics(governance_service, mock_repo):
    mock_conn = MagicMock()
    mock_repo._get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.execute.return_value.fetchone.return_value = [10]
    mock_conn.cursor.return_value.execute.return_value.fetchall.return_value = [("1",)]
    res = governance_service.get_integrity_metrics()
    assert res['gov_run_ids'] == {"1"}

def test_governance_service_exception_handling(governance_service, mock_repo):
    mock_repo.get_learning_metrics.side_effect = Exception("DB Timeout")
    with pytest.raises(Exception, match="DB Timeout"):
        governance_service.get_learning_metrics()
