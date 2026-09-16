from decimal import Decimal

import pytest

from backend.application.dtos.cashflow_summary_dto import CategoryExpenseTotalDTO
from backend.domains.health.service import CategoryExpenseIntelligenceService


def _category(name: str, amount: str) -> CategoryExpenseTotalDTO:
    return CategoryExpenseTotalDTO(category=name, expense_total=Decimal(amount))


def test_build_ranks_categories_calculates_shares_total_and_top_category():
    summary = CategoryExpenseIntelligenceService().build([
        _category("Transporte", "250.00"),
        _category("Moradia", "1000.00"),
        _category("Alimentação", "500.00"),
    ])

    assert summary.total_expense == Decimal("1750.00")
    assert [item.category for item in summary.categories] == [
        "Moradia", "Alimentação", "Transporte",
    ]
    assert [item.rank for item in summary.categories] == [1, 2, 3]
    assert summary.categories[0].share_of_expenses == Decimal("1000.00") / Decimal("1750.00")
    assert summary.categories[1].share_of_expenses == Decimal("500.00") / Decimal("1750.00")
    assert summary.categories[2].share_of_expenses == Decimal("250.00") / Decimal("1750.00")
    assert sum((item.expense_total for item in summary.categories), Decimal("0.00")) == summary.total_expense
    assert summary.top_category == summary.categories[0]


def test_build_uses_category_name_as_stable_tie_breaker():
    summary = CategoryExpenseIntelligenceService().build([
        _category("Zulu", "100.00"),
        _category("Alpha", "100.00"),
    ])

    assert [item.category for item in summary.categories] == ["Alpha", "Zulu"]
    assert [item.rank for item in summary.categories] == [1, 2]


def test_build_returns_empty_summary_for_empty_input():
    summary = CategoryExpenseIntelligenceService().build([])

    assert summary.total_expense == Decimal("0.00")
    assert summary.categories == []
    assert summary.top_category is None


def test_build_preserves_explicit_zero_categories_without_shares():
    summary = CategoryExpenseIntelligenceService().build([
        _category("Beta", "0.00"),
        _category("Alpha", "0.00"),
    ])

    assert summary.total_expense == Decimal("0.00")
    assert [item.category for item in summary.categories] == ["Alpha", "Beta"]
    assert [item.share_of_expenses for item in summary.categories] == [None, None]
    assert summary.top_category == summary.categories[0]


def test_build_preserves_decimal_precision_and_uncategorized_label():
    summary = CategoryExpenseIntelligenceService().build([
        _category("Uncategorized", "0.10"),
        _category("Serviços", "0.20"),
        _category("Streaming", "0.30"),
    ])

    assert summary.total_expense == Decimal("0.60")
    assert all(isinstance(item.expense_total, Decimal) for item in summary.categories)
    assert all(isinstance(item.share_of_expenses, Decimal) for item in summary.categories)
    assert sum((item.share_of_expenses for item in summary.categories), Decimal("0")) == Decimal("1.0")
    assert any(item.category == "Uncategorized" for item in summary.categories)


def test_build_rejects_duplicate_categories():
    with pytest.raises(ValueError, match="Duplicate category"):
        CategoryExpenseIntelligenceService().build([
            _category("Moradia", "100.00"),
            _category("Moradia", "200.00"),
        ])
