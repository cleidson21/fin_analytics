from decimal import Decimal

import pytest

from backend.application.dtos.cashflow_summary_dto import MonthlyCashflowPeriodDTO
from backend.domains.health.service import HistoricalFinancialMetricsService


def _month(reference_month: str, income: str, expense: str) -> MonthlyCashflowPeriodDTO:
    return MonthlyCashflowPeriodDTO(
        reference_month=reference_month,
        income=Decimal(income),
        expense=Decimal(expense),
    )


def test_build_orders_months_chronologically_and_calculates_metrics():
    result = HistoricalFinancialMetricsService().build([
        _month("2026-08", "1000.00", "600.00"),
        _month("2026-06", "1000.00", "1200.00"),
        _month("2026-07", "500.00", "0.00"),
    ])

    assert [item.reference_month for item in result] == ["2026-06", "2026-07", "2026-08"]
    assert result[2].net_cashflow == Decimal("400.00")
    assert result[2].savings_amount == Decimal("400.00")
    assert result[2].savings_rate == Decimal("0.4")
    assert result[0].net_cashflow == Decimal("-200.00")
    assert result[0].savings_rate == Decimal("-0.2")


def test_build_returns_empty_history_without_synthesizing_months():
    assert HistoricalFinancialMetricsService().build([]) == []


def test_build_preserves_gaps_without_creating_intermediate_months():
    result = HistoricalFinancialMetricsService().build([
        _month("2026-06", "100.00", "10.00"),
        _month("2025-06", "50.00", "5.00"),
    ])

    assert [item.reference_month for item in result] == ["2025-06", "2026-06"]
    assert len(result) == 2


def test_build_preserves_an_explicit_zero_month_and_zero_income_rate():
    result = HistoricalFinancialMetricsService().build([
        _month("2026-05", "0.00", "0.00"),
        _month("2026-06", "0.00", "500.00"),
    ])

    assert result[0].total_income == Decimal("0.00")
    assert result[0].total_expense == Decimal("0.00")
    assert result[0].net_cashflow == Decimal("0.00")
    assert result[0].savings_rate is None
    assert result[1].net_cashflow == Decimal("-500.00")
    assert result[1].savings_amount == Decimal("-500.00")
    assert result[1].savings_rate is None


def test_build_preserves_decimal_values_without_float_conversion():
    result = HistoricalFinancialMetricsService().build([
        _month("2026-06", "0.10", "0.20"),
    ])

    metric = result[0]
    assert isinstance(metric.total_income, Decimal)
    assert isinstance(metric.total_expense, Decimal)
    assert isinstance(metric.net_cashflow, Decimal)
    assert isinstance(metric.savings_amount, Decimal)
    assert isinstance(metric.savings_rate, Decimal)
    assert metric.net_cashflow == Decimal("-0.10")


def test_build_rejects_duplicate_reference_months():
    duplicate_months = [
        _month("2026-06", "100.00", "10.00"),
        _month("2026-06", "200.00", "20.00"),
    ]

    with pytest.raises(ValueError, match="Duplicate reference_month"):
        HistoricalFinancialMetricsService().build(duplicate_months)
