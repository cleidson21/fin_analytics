import pytest
from unittest.mock import MagicMock, patch
from app.api.services.financial_service import FinancialService

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def financial_service(mock_repo):
    service = FinancialService()
    service.repo = mock_repo
    return service

def test_get_transactions(financial_service, mock_repo):
    mock_repo.get_transactions.return_value = [{"id_economico": "1", "valor": 100}]
    
    result = financial_service.get_transactions(limit=10, offset=0)
    assert len(result) == 1
    assert result[0]["id_economico"] == "1"
    mock_repo.get_transactions.assert_called_once_with(limit=10, offset=0)

def test_get_transactions_empty(financial_service, mock_repo):
    mock_repo.get_transactions.return_value = []
    result = financial_service.get_transactions(limit=10, offset=0)
    assert len(result) == 0

def test_get_transactions_summary(financial_service, mock_repo):
    mock_repo.get_transactions_summary.return_value = {"receitas": 100, "despesas": 50}
    result = financial_service.get_transactions_summary()
    assert result["receitas"] == 100
    mock_repo.get_transactions_summary.assert_called_once()

def test_get_accounts_summary(financial_service, mock_repo):
    mock_repo.get_accounts_summary.return_value = [{"account": "Bank", "balance": 1000}]
    result = financial_service.get_accounts_summary()
    assert len(result) == 1
    assert result[0]["balance"] == 1000

def test_get_cashflow_summary(financial_service, mock_repo):
    import pandas as pd
    mock_repo.get_cashflow_summary.return_value = pd.DataFrame([{"month": "2026-06", "inflow": 100}])
    result = financial_service.get_cashflow_summary()
    assert not result.empty
    assert result.iloc[0]["inflow"] == 100

def test_get_current_net_worth(financial_service, mock_repo):
    from decimal import Decimal
    mock_repo.get_current_net_worth.return_value = Decimal('15000.50')
    result = financial_service.get_current_net_worth()
    assert result == Decimal('15000.50')
    
def test_exceptions_propagated(financial_service, mock_repo):
    mock_repo.get_transactions.side_effect = Exception("DB Error")
    with pytest.raises(Exception, match="DB Error"):
        financial_service.get_transactions()

def test_get_database_path(financial_service, mock_repo):
    mock_repo.db_path = "test.db"
    assert financial_service.get_database_path() == "test.db"

def test_vacuum_database(financial_service, mock_repo):
    financial_service.vacuum_database()
    mock_repo.vacuum_database.assert_called_once()

def test_analyze_database(financial_service, mock_repo):
    financial_service.analyze_database()
    mock_repo.analyze_database.assert_called_once()

def test_get_admin_metrics(financial_service, mock_repo):
    mock_conn = MagicMock()
    mock_repo._get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.execute.return_value.fetchone.return_value = [10]
    res = financial_service.get_admin_metrics()
    assert res['total_transactions'] == 10

def test_get_table_counts(financial_service, mock_repo):
    mock_conn = MagicMock()
    mock_repo._get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.execute.return_value.fetchone.return_value = [10]
    res = financial_service.get_table_counts()
    assert len(res) == 4
    assert res[0]['row_count'] == 10

def test_get_integrity_metrics(financial_service, mock_repo):
    mock_conn = MagicMock()
    mock_repo._get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.execute.return_value.fetchall.return_value = [("1",)]
    mock_conn.cursor.return_value.execute.return_value.fetchone.return_value = [0]
    res = financial_service.get_integrity_metrics()
    assert res['fin_run_ids'] == {"1"}
    assert res['duplicate_transactions_suspects'] == 0

def test_get_transactions_total_pages(financial_service, mock_repo):
    mock_repo.get_transactions_total_pages.return_value = 5
    assert financial_service.get_transactions_total_pages() == 5

def test_update_transaction_category(financial_service, mock_repo):
    mock_repo.update_transaction_category.return_value = True
    assert financial_service.update_transaction_category() is True

def test_get_account_catalog(financial_service, mock_repo):
    mock_repo.get_account_catalog.return_value = []
    assert financial_service.get_account_catalog() == []

def test_get_expenses_by_category(financial_service, mock_repo):
    mock_repo.get_expenses_by_category.return_value = []
    assert financial_service.get_expenses_by_category() == []
