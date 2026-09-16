from decimal import Decimal

from backend.application.dtos.cashflow_summary_dto import (
    CategoryExpenseMonthDTO,
    CategoryExpenseTotalDTO,
    SpendingAnomalyGlobalStatus,
    SpendingAnomalyStatus,
)
from backend.domains.health.service import SpendingAnomalyService


def _total(category: str, amount: str) -> CategoryExpenseTotalDTO:
    return CategoryExpenseTotalDTO(category=category, expense_total=Decimal(amount))


def _month(reference_month: str, *totals: CategoryExpenseTotalDTO) -> CategoryExpenseMonthDTO:
    return CategoryExpenseMonthDTO(
        reference_month=reference_month,
        category_totals=list(totals),
    )


def _baseline(*months: tuple[CategoryExpenseTotalDTO, ...]) -> list[CategoryExpenseMonthDTO]:
    references = ["2026-06", "2026-07", "2026-08"]
    return [_month(reference, *totals) for reference, totals in zip(references, months)]


def _evaluation(summary, category: str):
    return next(item for item in summary.evaluations if item.category == category)


def test_normal_and_exact_multiplier_boundary_are_not_spikes():
    service = SpendingAnomalyService()
    baseline = _baseline(
        (_total("Normal", "100.00"), _total("Exact", "100.00")),
        (_total("Normal", "110.00"), _total("Exact", "100.00")),
        (_total("Normal", "90.00"), _total("Exact", "100.00")),
    )

    summary = service.evaluate(
        _month("2026-09", _total("Normal", "120.00"), _total("Exact", "150.00")),
        baseline,
    )

    assert _evaluation(summary, "Normal").status is SpendingAnomalyStatus.NORMAL
    exact = _evaluation(summary, "Exact")
    assert exact.status is SpendingAnomalyStatus.NORMAL
    assert exact.baseline_reference == Decimal("100.00")
    assert exact.ratio == Decimal("1.5")
    assert summary.anomalies == []


def test_above_multiplier_boundary_is_spike_with_explainability_values():
    summary = SpendingAnomalyService().evaluate(
        _month("2026-09", _total("Spike", "150.01")),
        _baseline(
            (_total("Spike", "100.00"),),
            (_total("Spike", "100.00"),),
            (_total("Spike", "100.00"),),
        ),
    )

    evaluation = summary.evaluations[0]
    assert evaluation.status is SpendingAnomalyStatus.SPIKE
    assert evaluation.baseline_values == [Decimal("100.00")] * 3
    assert evaluation.baseline_months_used == ["2026-06", "2026-07", "2026-08"]
    assert evaluation.baseline_reference == Decimal("100.00")
    assert evaluation.ratio == Decimal("150.01") / Decimal("100.00")
    assert evaluation.ratio_threshold == Decimal("1.5")
    assert evaluation.baseline_floor == Decimal("50.00")
    assert summary.anomalies == [evaluation]


def test_baseline_floor_is_inclusive_and_below_floor_is_not_anomaly():
    summary = SpendingAnomalyService().evaluate(
        _month("2026-09", _total("AtFloor", "75.01"), _total("BelowFloor", "100.00")),
        _baseline(
            (_total("AtFloor", "50.00"), _total("BelowFloor", "49.99")),
            (_total("AtFloor", "50.00"), _total("BelowFloor", "49.99")),
            (_total("AtFloor", "50.00"), _total("BelowFloor", "49.99")),
        ),
    )

    assert _evaluation(summary, "AtFloor").status is SpendingAnomalyStatus.SPIKE
    assert _evaluation(summary, "BelowFloor").status is SpendingAnomalyStatus.BELOW_BASELINE_FLOOR
    assert [item.category for item in summary.anomalies] == ["AtFloor"]


def test_two_month_history_uses_present_values_only_and_is_spike_eligible():
    summary = SpendingAnomalyService().evaluate(
        _month("2026-09", _total("TwoMonths", "250.00")),
        _baseline(
            (_total("TwoMonths", "100.00"),),
            (),
            (_total("TwoMonths", "200.00"),),
        ),
    )

    evaluation = summary.evaluations[0]
    assert evaluation.status is SpendingAnomalyStatus.SPIKE
    assert evaluation.baseline_values == [Decimal("100.00"), Decimal("200.00")]
    assert evaluation.baseline_months_used == ["2026-06", "2026-08"]
    assert evaluation.baseline_reference == Decimal("150.00")


def test_one_month_history_is_insufficient_and_not_an_anomaly():
    summary = SpendingAnomalyService().evaluate(
        _month("2026-09", _total("OneMonth", "500.00")),
        _baseline((_total("OneMonth", "100.00"),), (), ()),
    )

    evaluation = summary.evaluations[0]
    assert evaluation.status is SpendingAnomalyStatus.INSUFFICIENT_HISTORY
    assert evaluation.baseline_reference is None
    assert evaluation.ratio is None
    assert summary.anomalies == []


def test_new_expense_threshold_boundaries_and_exact_category_matching():
    summary = SpendingAnomalyService().evaluate(
        _month(
            "2026-09",
            _total("Below", "99.99"),
            _total("AtThreshold", "100.00"),
            _total("Transferências", "100.00"),
        ),
        _baseline(
            (_total("Transferencias", "200.00"),),
            (_total("Transferencias", "200.00"),),
            (_total("Transferencias", "200.00"),),
        ),
    )

    assert _evaluation(summary, "Below").status is SpendingAnomalyStatus.NEW_EXPENSE_BELOW_THRESHOLD
    assert _evaluation(summary, "AtThreshold").status is SpendingAnomalyStatus.NEW_EXPENSE
    assert _evaluation(summary, "Transferências").status is SpendingAnomalyStatus.NEW_EXPENSE
    assert {item.category for item in summary.anomalies} == {"AtThreshold", "Transferências"}


def test_explicit_zero_is_present_not_new_and_can_fall_below_baseline_floor():
    summary = SpendingAnomalyService().evaluate(
        _month("2026-09", _total("ExplicitZero", "100.00")),
        _baseline(
            (_total("ExplicitZero", "0.00"),),
            (_total("ExplicitZero", "0.00"),),
            (),
        ),
    )

    evaluation = summary.evaluations[0]
    assert evaluation.status is SpendingAnomalyStatus.BELOW_BASELINE_FLOOR
    assert evaluation.baseline_values == [Decimal("0.00"), Decimal("0.00")]
    assert evaluation.baseline_reference == Decimal("0.00")
    assert evaluation.ratio is None
    assert summary.anomalies == []


def test_mixed_categories_expose_only_spike_and_new_expense_as_anomalies():
    summary = SpendingAnomalyService().evaluate(
        _month(
            "2026-09",
            _total("Normal", "100.00"),
            _total("Spike", "200.00"),
            _total("New", "100.00"),
            _total("OneMonth", "500.00"),
            _total("BelowFloor", "100.00"),
            _total("SmallNew", "99.99"),
        ),
        _baseline(
            (_total("Normal", "100.00"), _total("Spike", "100.00"), _total("OneMonth", "100.00"), _total("BelowFloor", "40.00")),
            (_total("Normal", "100.00"), _total("Spike", "100.00"), _total("BelowFloor", "40.00")),
            (_total("Normal", "100.00"), _total("Spike", "100.00"), _total("BelowFloor", "40.00")),
        ),
    )

    statuses = {item.category: item.status for item in summary.evaluations}
    assert statuses == {
        "Normal": SpendingAnomalyStatus.NORMAL,
        "Spike": SpendingAnomalyStatus.SPIKE,
        "New": SpendingAnomalyStatus.NEW_EXPENSE,
        "OneMonth": SpendingAnomalyStatus.INSUFFICIENT_HISTORY,
        "BelowFloor": SpendingAnomalyStatus.BELOW_BASELINE_FLOOR,
        "SmallNew": SpendingAnomalyStatus.NEW_EXPENSE_BELOW_THRESHOLD,
    }
    assert {item.status for item in summary.anomalies} == {
        SpendingAnomalyStatus.SPIKE,
        SpendingAnomalyStatus.NEW_EXPENSE,
    }


def test_empty_current_month_is_ok_with_no_evaluations_or_anomalies():
    summary = SpendingAnomalyService().evaluate(
        _month("2026-09"),
        _baseline((), (), ()),
    )

    assert summary.global_status is SpendingAnomalyGlobalStatus.OK
    assert summary.evaluations == []
    assert summary.anomalies == []


def test_missing_or_non_continuous_global_baseline_is_insufficient_without_evaluations():
    service = SpendingAnomalyService()
    target = _month("2026-09", _total("New", "500.00"))

    missing = service.evaluate(target, _baseline((), (),)[:2])
    non_continuous = service.evaluate(
        target,
        [_month("2026-05"), _month("2026-07"), _month("2026-08")],
    )

    for summary in [missing, non_continuous]:
        assert summary.global_status is SpendingAnomalyGlobalStatus.INSUFFICIENT_BASELINE
        assert summary.evaluations == []
        assert summary.anomalies == []


def test_decimal_values_remain_decimal_end_to_end():
    summary = SpendingAnomalyService().evaluate(
        _month("2026-09", _total("Decimal", "0.30")),
        _baseline(
            (_total("Decimal", "0.10"),),
            (_total("Decimal", "0.20"),),
            (_total("Decimal", "0.30"),),
        ),
    )

    evaluation = summary.evaluations[0]
    assert all(isinstance(value, Decimal) for value in evaluation.baseline_values)
    assert isinstance(evaluation.current_expense, Decimal)
    assert isinstance(evaluation.baseline_reference, Decimal)
    assert isinstance(evaluation.ratio, Decimal)
    assert evaluation.baseline_reference == Decimal("0.20")
