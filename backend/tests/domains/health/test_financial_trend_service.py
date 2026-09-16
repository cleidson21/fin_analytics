from decimal import Decimal

import pytest

from backend.application.dtos.cashflow_summary_dto import (
    CategoryExpenseMonthDTO,
    CategoryExpenseTotalDTO,
    CategoryTrendDirection,
    FinancialTrendDirection,
    FinancialTrendMetric,
    FinancialTrendSummaryStatus,
    MonthlyFinancialMetricsDTO,
)
from backend.domains.health.service import FinancialTrendService


def _financial_month(
    reference_month: str,
    income: str,
    expense: str,
    net: str,
    savings_rate: str | None,
) -> MonthlyFinancialMetricsDTO:
    return MonthlyFinancialMetricsDTO(
        reference_month=reference_month,
        total_income=Decimal(income),
        total_expense=Decimal(expense),
        net_cashflow=Decimal(net),
        savings_amount=Decimal(net),
        savings_rate=None if savings_rate is None else Decimal(savings_rate),
    )


def _category(category: str, expense: str) -> CategoryExpenseTotalDTO:
    return CategoryExpenseTotalDTO(
        category=category,
        expense_total=Decimal(expense),
    )


def _category_month(
    reference_month: str,
    *categories: CategoryExpenseTotalDTO,
) -> CategoryExpenseMonthDTO:
    return CategoryExpenseMonthDTO(
        reference_month=reference_month,
        category_totals=list(categories),
    )


def _global_metric(summary, metric: FinancialTrendMetric):
    return next(item for item in summary.metrics if item.metric is metric)


def _category_metric(summary, category: str):
    return next(item for item in summary.categories if item.category == category)


def test_global_trend_resolves_partial_current_month_and_exact_directions():
    summary = FinancialTrendService().build_global(
        requested_reference_month="2026-09",
        current_reference_month="2026-09",
        monthly_metrics=[
            _financial_month("2026-09", "500", "400", "100", "0.2"),
            _financial_month("2026-07", "100", "100", "-500", "-0.50"),
            _financial_month("2026-08", "120", "80", "-200", "-0.20"),
        ],
    )

    assert summary.status is FinancialTrendSummaryStatus.OK
    assert summary.requested_reference_month == "2026-09"
    assert summary.trend_target_month == "2026-08"
    assert summary.comparison_month == "2026-07"

    income = _global_metric(summary, FinancialTrendMetric.TOTAL_INCOME)
    assert income.direction is FinancialTrendDirection.INCREASED
    assert income.absolute_delta == Decimal("20")
    assert income.percentage_delta == Decimal("0.2")

    expense = _global_metric(summary, FinancialTrendMetric.TOTAL_EXPENSE)
    assert expense.direction is FinancialTrendDirection.DECREASED
    assert expense.absolute_delta == Decimal("-20")
    assert expense.percentage_delta == Decimal("-0.2")

    net = _global_metric(summary, FinancialTrendMetric.NET_CASHFLOW)
    assert net.direction is FinancialTrendDirection.INCREASED
    assert net.absolute_delta == Decimal("300")
    assert net.percentage_delta == Decimal("0.6")

    rate = _global_metric(summary, FinancialTrendMetric.SAVINGS_RATE)
    assert rate.direction is FinancialTrendDirection.INCREASED
    assert rate.absolute_delta == Decimal("0.30")
    assert rate.percentage_delta == Decimal("0.6")


def test_global_trend_keeps_closed_requested_month_as_target():
    summary = FinancialTrendService().build_global(
        requested_reference_month="2026-08",
        current_reference_month="2026-09",
        monthly_metrics=[
            _financial_month("2026-07", "100", "50", "50", "0.5"),
            _financial_month("2026-08", "100", "50", "50", "0.5"),
        ],
    )

    assert summary.trend_target_month == "2026-08"
    assert summary.comparison_month == "2026-07"
    assert all(
        metric.direction is FinancialTrendDirection.UNCHANGED
        for metric in summary.metrics
    )
    assert all(metric.absolute_delta == 0 for metric in summary.metrics)
    assert all(metric.percentage_delta == 0 for metric in summary.metrics)


def test_global_trend_previous_zero_and_undefined_savings_rate():
    summary = FinancialTrendService().build_global(
        requested_reference_month="2026-08",
        current_reference_month="2026-09",
        monthly_metrics=[
            _financial_month("2026-07", "0", "0", "0", None),
            _financial_month("2026-08", "100", "100", "0", "0"),
        ],
    )

    income = _global_metric(summary, FinancialTrendMetric.TOTAL_INCOME)
    assert income.direction is FinancialTrendDirection.INCREASED
    assert income.absolute_delta == Decimal("100")
    assert income.percentage_delta is None

    net = _global_metric(summary, FinancialTrendMetric.NET_CASHFLOW)
    assert net.direction is FinancialTrendDirection.UNCHANGED
    assert net.absolute_delta == Decimal("0")
    assert net.percentage_delta is None

    rate = _global_metric(summary, FinancialTrendMetric.SAVINGS_RATE)
    assert rate.current_value == Decimal("0")
    assert rate.previous_value is None
    assert rate.direction is FinancialTrendDirection.INSUFFICIENT_DATA
    assert rate.absolute_delta is None
    assert rate.percentage_delta is None


def test_global_trend_handles_cross_year_continuity():
    summary = FinancialTrendService().build_global(
        requested_reference_month="2026-01",
        current_reference_month="2026-09",
        monthly_metrics=[
            _financial_month("2025-12", "100", "60", "40", "0.4"),
            _financial_month("2026-01", "120", "60", "60", "0.5"),
        ],
    )

    assert summary.status is FinancialTrendSummaryStatus.OK
    assert summary.trend_target_month == "2026-01"
    assert summary.comparison_month == "2025-12"


def test_global_trend_returns_insufficient_data_without_skipping_gap():
    summary = FinancialTrendService().build_global(
        requested_reference_month="2026-06",
        current_reference_month="2026-09",
        monthly_metrics=[
            _financial_month("2025-06", "100", "50", "50", "0.5"),
            _financial_month("2026-06", "120", "60", "60", "0.5"),
        ],
    )

    assert summary.status is FinancialTrendSummaryStatus.INSUFFICIENT_DATA
    assert summary.trend_target_month == "2026-06"
    assert summary.comparison_month == "2026-05"
    assert summary.metrics == []


def test_category_trend_builds_exact_union_directions_and_ordering():
    summary = FinancialTrendService().build_categories(
        requested_reference_month="2026-09",
        current_reference_month="2026-09",
        monthly_categories=[
            _category_month(
                "2026-07",
                _category("Increase", "100"),
                _category("Decrease", "100"),
                _category("Same", "50"),
                _category("Gone", "300"),
                _category("Zero", "0.00"),
                _category("Serviços", "20"),
            ),
            _category_month(
                "2026-08",
                _category("New", "200"),
                _category("Increase", "150"),
                _category("Decrease", "80"),
                _category("Same", "50"),
                _category("Zero", "50"),
                _category("Servicos", "20"),
            ),
        ],
    )

    assert summary.status is FinancialTrendSummaryStatus.OK
    assert summary.trend_target_month == "2026-08"
    assert summary.comparison_month == "2026-07"
    assert [item.category for item in summary.categories] == [
        "New",
        "Increase",
        "Decrease",
        "Same",
        "Zero",
        "Servicos",
        "Gone",
        "Serviços",
    ]

    assert _category_metric(summary, "Increase").direction is CategoryTrendDirection.INCREASED
    assert _category_metric(summary, "Decrease").direction is CategoryTrendDirection.DECREASED
    assert _category_metric(summary, "Same").direction is CategoryTrendDirection.UNCHANGED

    new = _category_metric(summary, "New")
    assert new.direction is CategoryTrendDirection.NEW
    assert new.previous_expense is None
    assert new.absolute_delta is None
    assert new.percentage_delta is None

    disappeared = _category_metric(summary, "Gone")
    assert disappeared.direction is CategoryTrendDirection.DISAPPEARED
    assert disappeared.current_expense is None
    assert disappeared.absolute_delta is None
    assert disappeared.percentage_delta is None


def test_category_trend_preserves_explicit_zero_and_decimal_precision():
    summary = FinancialTrendService().build_categories(
        requested_reference_month="2026-08",
        current_reference_month="2026-09",
        monthly_categories=[
            _category_month("2026-07", _category("Exact", "0.00")),
            _category_month("2026-08", _category("Exact", "0.10")),
        ],
    )

    metric = summary.categories[0]
    assert metric.direction is CategoryTrendDirection.INCREASED
    assert metric.previous_expense == Decimal("0.00")
    assert metric.current_expense == Decimal("0.10")
    assert metric.absolute_delta == Decimal("0.10")
    assert metric.percentage_delta is None
    assert isinstance(metric.current_expense, Decimal)
    assert isinstance(metric.previous_expense, Decimal)
    assert isinstance(metric.absolute_delta, Decimal)


def test_category_trend_exact_label_matching_does_not_normalize():
    summary = FinancialTrendService().build_categories(
        requested_reference_month="2026-08",
        current_reference_month="2026-09",
        monthly_categories=[
            _category_month("2026-07", _category("Serviços", "100")),
            _category_month("2026-08", _category("Servicos", "100")),
        ],
    )

    assert _category_metric(summary, "Servicos").direction is CategoryTrendDirection.NEW
    assert _category_metric(summary, "Serviços").direction is CategoryTrendDirection.DISAPPEARED


def test_category_trend_returns_insufficient_data_without_artificial_evaluations():
    summary = FinancialTrendService().build_categories(
        requested_reference_month="2025-05",
        current_reference_month="2026-09",
        monthly_categories=[
            _category_month("2025-05", _category("Only", "100")),
        ],
    )

    assert summary.status is FinancialTrendSummaryStatus.INSUFFICIENT_DATA
    assert summary.trend_target_month == "2025-05"
    assert summary.comparison_month == "2025-04"
    assert summary.categories == []


def test_trend_service_rejects_duplicate_months_and_categories():
    service = FinancialTrendService()
    duplicate_metrics = [
        _financial_month("2026-07", "100", "50", "50", "0.5"),
        _financial_month("2026-07", "100", "50", "50", "0.5"),
    ]
    with pytest.raises(ValueError, match="Duplicate reference_month"):
        service.build_global("2026-08", "2026-09", duplicate_metrics)

    duplicate_categories = [
        _category_month(
            "2026-07",
            _category("Same", "10"),
            _category("Same", "20"),
        ),
        _category_month("2026-08"),
    ]
    with pytest.raises(ValueError, match="Duplicate category"):
        service.build_categories("2026-08", "2026-09", duplicate_categories)


@pytest.mark.parametrize("reference_month", ["2026-1", "2026-13", "invalid"])
def test_trend_service_rejects_invalid_reference_month(reference_month):
    with pytest.raises(ValueError, match="reference_month must use YYYY-MM"):
        FinancialTrendService().build_global(reference_month, "2026-09", [])
