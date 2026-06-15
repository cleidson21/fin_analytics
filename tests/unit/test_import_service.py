import pytest
from unittest.mock import MagicMock
from app.api.services.import_service import ImportService

@pytest.fixture
def mock_fin_repo():
    return MagicMock()

@pytest.fixture
def mock_gov_repo():
    return MagicMock()

@pytest.fixture
def import_service(mock_fin_repo, mock_gov_repo):
    service = ImportService()
    service.fin_repo = mock_fin_repo
    service.gov_repo = mock_gov_repo
    return service

def test_rollback_import_run_success(import_service, mock_fin_repo, mock_gov_repo):
    mock_fin_repo.rollback_financial_data.return_value = True
    mock_gov_repo.rollback_governance_data.return_value = True
    
    import_service.rollback_import_run("run-123")
    
    mock_fin_repo.rollback_financial_data.assert_called_once_with("run-123")
    mock_gov_repo.rollback_governance_data.assert_called_once_with("run-123")

def test_rollback_import_run_propagates_exception(import_service, mock_fin_repo, mock_gov_repo):
    mock_fin_repo.rollback_financial_data.side_effect = Exception("Financial DB error")
    
    with pytest.raises(Exception, match="Financial DB error"):
        import_service.rollback_import_run("run-123")

def test_promote_all_wealth_staging(import_service, mock_fin_repo, mock_gov_repo):
    mock_gov_repo.promote_all_wealth_staging.return_value = {"promoted": 10}
    
    result = import_service.promote_all_wealth_staging("run-123")
    
    mock_gov_repo.promote_all_wealth_staging.assert_called_once_with("run-123")
    assert result["promoted"] == 10
