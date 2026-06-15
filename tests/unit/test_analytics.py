import pytest
import pandas as pd
from datetime import date
from unittest.mock import patch, MagicMock
from app.api.services.analytics import AnalyticsService

@pytest.fixture
def mock_queries():
    mock = MagicMock()
    mock.get_cashflow_summary.return_value = pd.DataFrame([{"natureza": "EXPENSE", "total": 100}, {"natureza": "INCOME", "total": 200}])
    mock.get_daily_expenses.return_value = pd.DataFrame([{"data": "2026-06-01", "total": 50}, {"data": "2026-06-02", "total": 50}])
    mock.get_expenses_by_category.return_value = pd.DataFrame([{"macro_categoria": "Alimentação", "total": 100}])
    mock.get_current_net_worth.return_value = 1000.0
    mock.get_portfolio_evolution_summary.return_value = {"rentabilidade_acumulada": 5.0}
    return mock

@patch("app.api.services.analytics.FinancialRepository")
def test_analytics_methods(mock_repo_cls, mock_queries):
    mock_repo_cls.return_value = mock_queries
    analytics = AnalyticsService()
    
    # get_expense_pacing
    pacing = analytics.get_expense_pacing("2026-06")
    assert pacing is not None

    # get_monthly_heatmap
    heatmap = analytics.get_monthly_heatmap("2026-06")
    assert heatmap is not None

    # get_categories_comparison
    comparison = analytics.get_categories_comparison("2026-06")
    assert comparison is not None

    # get_summary_v2
    summary_v2 = analytics.get_summary_v2("2026-06")
    assert summary_v2 is not None

    # get_pacing_v2
    pacing_v2 = analytics.get_pacing_v2("2026-06")
    assert pacing_v2 is not None

    # get_subscriptions_summary
    with patch.object(analytics, "_fetch_expense_rows") as mock_fetch:
        mock_fetch.return_value = [{"descricao_original": "Netflix", "data": "2026-06-01", "valor_cents": 5000}]
        subs = analytics.get_subscriptions_summary("2026-06")
        assert subs is not None

    # get_installments_summary
    with patch.object(analytics, "_fetch_expense_rows") as mock_fetch:
        mock_fetch.return_value = [{"descricao_original": "iPhone 1/12", "data": "2026-06-01", "valor_cents": 100000}]
        installments = analytics.get_installments_summary("2026-06")
        assert installments is not None
