from decimal import Decimal

from backend.application.dtos.cashflow_summary_dto import MonthlyCashflowDTO
from backend.domains.health.service import CashflowMetricsService


def _calculate(income, expense, monthly_totals=()):
    return CashflowMetricsService().calculate(
        {"income_total": income, "expense_total": expense},
        monthly_totals,
    )


def test_calculates_positive_cashflow_and_savings_rate():
    summary = _calculate(Decimal("1000"), Decimal("600"))

    assert summary.total_income == Decimal("1000")
    assert summary.total_expense == Decimal("600")
    assert summary.net_cashflow == Decimal("400")
    assert summary.savings_amount == Decimal("400")
    assert summary.savings_rate == Decimal("0.4")


def test_calculates_negative_cashflow_and_savings_rate():
    summary = _calculate(Decimal("1000"), Decimal("1200"))

    assert summary.net_cashflow == Decimal("-200")
    assert summary.savings_amount == Decimal("-200")
    assert summary.savings_rate == Decimal("-0.2")


def test_returns_none_savings_rate_when_income_is_zero_with_expense():
    summary = _calculate(Decimal("0"), Decimal("500"))

    assert summary.net_cashflow == Decimal("-500")
    assert summary.savings_amount == Decimal("-500")
    assert summary.savings_rate is None


def test_returns_none_savings_rate_when_income_and_expense_are_zero():
    summary = _calculate(Decimal("0"), Decimal("0"))

    assert summary.net_cashflow == Decimal("0")
    assert summary.savings_amount == Decimal("0")
    assert summary.savings_rate is None


def test_calculates_zero_cashflow_when_income_equals_expense():
    summary = _calculate(Decimal("1000"), Decimal("1000"))

    assert summary.net_cashflow == Decimal("0")
    assert summary.savings_amount == Decimal("0")
    assert summary.savings_rate == Decimal("0")


def test_calculates_averages_for_multiple_months():
    monthly_totals = (
        MonthlyCashflowDTO(income=Decimal("1000"), expense=Decimal("600")),
        MonthlyCashflowDTO(income=Decimal("500"), expense=Decimal("700")),
        MonthlyCashflowDTO(income=Decimal("1500"), expense=Decimal("900")),
    )

    summary = _calculate(Decimal("2200"), Decimal("1700"), monthly_totals)

    assert summary.average_monthly_income == Decimal("1000")
    assert summary.average_monthly_expense == Decimal("733.3333333333333333333333333")
    assert summary.average_monthly_net_cashflow == Decimal("266.6666666666666666666666667")


def test_uses_the_single_month_as_its_average():
    monthly_totals = (MonthlyCashflowDTO(income=Decimal("123.45"), expense=Decimal("67.89")),)

    summary = _calculate(Decimal("123.45"), Decimal("67.89"), monthly_totals)

    assert summary.average_monthly_income == Decimal("123.45")
    assert summary.average_monthly_expense == Decimal("67.89")
    assert summary.average_monthly_net_cashflow == Decimal("55.56")


def test_preserves_decimal_precision_without_float_conversion():
    monthly_totals = (
        MonthlyCashflowDTO(income=Decimal("0.10"), expense=Decimal("0.20")),
        MonthlyCashflowDTO(income=Decimal("0.20"), expense=Decimal("0.10")),
    )

    summary = _calculate(Decimal("0.30"), Decimal("0.10"), monthly_totals)

    assert summary.net_cashflow == Decimal("0.20")
    assert summary.savings_amount == summary.net_cashflow
    assert summary.savings_rate == Decimal("0.6666666666666666666666666667")
    assert summary.average_monthly_income == Decimal("0.15")
    assert summary.average_monthly_expense == Decimal("0.15")
    assert summary.average_monthly_net_cashflow == Decimal("0.00")


def test_returns_none_averages_for_empty_monthly_totals():
    summary = _calculate(Decimal("100"), Decimal("20"))

    assert summary.average_monthly_income is None
    assert summary.average_monthly_expense is None
    assert summary.average_monthly_net_cashflow is None
