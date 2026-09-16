from decimal import Decimal
from datetime import datetime
from typing import Any, Mapping, Sequence

from backend.application.dtos.cashflow_summary_dto import (
    CategoryFinancialTrendDTO,
    CategoryFinancialTrendSummaryDTO,
    CategoryExpenseMonthDTO,
    CategoryExpenseMetricDTO,
    CategoryExpenseSummaryDTO,
    CategoryExpenseTotalDTO,
    CategoryTrendDirection,
    CashflowSummaryDTO,
    FinancialTrendDirection,
    FinancialTrendMetric,
    FinancialTrendSummaryStatus,
    GlobalFinancialTrendMetricDTO,
    GlobalFinancialTrendSummaryDTO,
    MonthlyCashflowDTO,
    MonthlyCashflowPeriodDTO,
    MonthlyFinancialMetricsDTO,
    SpendingAnomalyEvaluationDTO,
    SpendingAnomalyGlobalStatus,
    SpendingAnomalyStatus,
    SpendingAnomalySummaryDTO,
)


class CashflowMetricsService:
    """Calculates deterministic metrics from certified Health query results."""

    def calculate(
        self,
        cashflow_totals: Mapping[str, Any],
        monthly_totals: Sequence[MonthlyCashflowDTO],
    ) -> CashflowSummaryDTO:
        total_income = self._as_decimal(cashflow_totals.get("income_total", Decimal("0")))
        total_expense = self._as_decimal(cashflow_totals.get("expense_total", Decimal("0")))
        net_cashflow = total_income - total_expense
        savings_amount = net_cashflow
        savings_rate = None if total_income == 0 else savings_amount / total_income

        monthly_income = [self._as_decimal(month.income) for month in monthly_totals]
        monthly_expense = [self._as_decimal(month.expense) for month in monthly_totals]
        monthly_net_cashflow = [
            income - expense
            for income, expense in zip(monthly_income, monthly_expense)
        ]

        return CashflowSummaryDTO(
            total_income=total_income,
            total_expense=total_expense,
            net_cashflow=net_cashflow,
            savings_amount=savings_amount,
            savings_rate=savings_rate,
            average_monthly_income=self._average(monthly_income),
            average_monthly_expense=self._average(monthly_expense),
            average_monthly_net_cashflow=self._average(monthly_net_cashflow),
        )

    @staticmethod
    def _as_decimal(value: Any) -> Decimal:
        return value if isinstance(value, Decimal) else Decimal(str(value))

    @staticmethod
    def _average(values: Sequence[Decimal]) -> Decimal | None:
        if not values:
            return None
        return sum(values, Decimal("0")) / Decimal(len(values))


class HistoricalFinancialMetricsService:
    """Builds chronological monthly Financial Health metrics from certified data."""

    def __init__(self, cashflow_metrics_service: CashflowMetricsService | None = None):
        self._cashflow_metrics_service = cashflow_metrics_service or CashflowMetricsService()

    def build(
        self,
        monthly_totals: Sequence[MonthlyCashflowPeriodDTO],
    ) -> list[MonthlyFinancialMetricsDTO]:
        """Return supplied months in ascending chronological order without filling gaps."""
        self._validate_unique_months(monthly_totals)

        return [
            self._to_monthly_metrics(month)
            for month in sorted(monthly_totals, key=lambda item: item.reference_month)
        ]

    def _to_monthly_metrics(
        self,
        month: MonthlyCashflowPeriodDTO,
    ) -> MonthlyFinancialMetricsDTO:
        summary = self._cashflow_metrics_service.calculate(
            {
                "income_total": month.income,
                "expense_total": month.expense,
            },
            [],
        )
        return MonthlyFinancialMetricsDTO(
            reference_month=month.reference_month,
            total_income=summary.total_income,
            total_expense=summary.total_expense,
            net_cashflow=summary.net_cashflow,
            savings_amount=summary.savings_amount,
            savings_rate=summary.savings_rate,
        )

    @staticmethod
    def _validate_unique_months(monthly_totals: Sequence[MonthlyCashflowPeriodDTO]) -> None:
        reference_months = [month.reference_month for month in monthly_totals]
        if len(reference_months) != len(set(reference_months)):
            raise ValueError("Duplicate reference_month values are not allowed")


class FinancialTrendService:
    """Builds deterministic closed-month global and category trends under ADR-018."""

    _GLOBAL_METRICS = (
        FinancialTrendMetric.TOTAL_INCOME,
        FinancialTrendMetric.TOTAL_EXPENSE,
        FinancialTrendMetric.NET_CASHFLOW,
        FinancialTrendMetric.SAVINGS_RATE,
    )

    def build_global(
        self,
        requested_reference_month: str,
        current_reference_month: str,
        monthly_metrics: Sequence[MonthlyFinancialMetricsDTO],
    ) -> GlobalFinancialTrendSummaryDTO:
        """Compare certified global metrics for consecutive closed months."""
        trend_target_month, comparison_month = self._resolve_comparison_months(
            requested_reference_month,
            current_reference_month,
        )
        self._validate_unique_months(monthly_metrics)
        metrics_by_month = {item.reference_month: item for item in monthly_metrics}
        current = metrics_by_month.get(trend_target_month)
        previous = metrics_by_month.get(comparison_month)

        if current is None or previous is None:
            return GlobalFinancialTrendSummaryDTO(
                requested_reference_month=requested_reference_month,
                trend_target_month=trend_target_month,
                comparison_month=comparison_month,
                status=FinancialTrendSummaryStatus.INSUFFICIENT_DATA,
                metrics=[],
            )

        return GlobalFinancialTrendSummaryDTO(
            requested_reference_month=requested_reference_month,
            trend_target_month=trend_target_month,
            comparison_month=comparison_month,
            status=FinancialTrendSummaryStatus.OK,
            metrics=[
                self._build_global_metric(
                    metric,
                    getattr(current, metric.value),
                    getattr(previous, metric.value),
                )
                for metric in self._GLOBAL_METRICS
            ],
        )

    def build_categories(
        self,
        requested_reference_month: str,
        current_reference_month: str,
        monthly_categories: Sequence[CategoryExpenseMonthDTO],
    ) -> CategoryFinancialTrendSummaryDTO:
        """Compare the exact-label category union for consecutive closed months."""
        trend_target_month, comparison_month = self._resolve_comparison_months(
            requested_reference_month,
            current_reference_month,
        )
        self._validate_unique_months(monthly_categories)
        for month in monthly_categories:
            self._validate_unique_categories(month)
        categories_by_month = {
            item.reference_month: item for item in monthly_categories
        }
        current_month = categories_by_month.get(trend_target_month)
        previous_month = categories_by_month.get(comparison_month)

        if current_month is None or previous_month is None:
            return CategoryFinancialTrendSummaryDTO(
                requested_reference_month=requested_reference_month,
                trend_target_month=trend_target_month,
                comparison_month=comparison_month,
                status=FinancialTrendSummaryStatus.INSUFFICIENT_DATA,
                categories=[],
            )

        current_by_category = {
            item.category: item.expense_total
            for item in current_month.category_totals
        }
        previous_by_category = {
            item.category: item.expense_total
            for item in previous_month.category_totals
        }
        current_categories = sorted(
            current_by_category,
            key=lambda category: (-current_by_category[category], category),
        )
        disappeared_categories = sorted(
            previous_by_category.keys() - current_by_category.keys(),
            key=lambda category: (-previous_by_category[category], category),
        )

        categories = [
            self._build_current_category_metric(
                category,
                current_by_category[category],
                previous_by_category.get(category),
            )
            for category in current_categories
        ]
        categories.extend(
            CategoryFinancialTrendDTO(
                category=category,
                current_expense=None,
                previous_expense=previous_by_category[category],
                absolute_delta=None,
                percentage_delta=None,
                direction=CategoryTrendDirection.DISAPPEARED,
            )
            for category in disappeared_categories
        )

        return CategoryFinancialTrendSummaryDTO(
            requested_reference_month=requested_reference_month,
            trend_target_month=trend_target_month,
            comparison_month=comparison_month,
            status=FinancialTrendSummaryStatus.OK,
            categories=categories,
        )

    @classmethod
    def _build_global_metric(
        cls,
        metric: FinancialTrendMetric,
        current_value: Decimal | None,
        previous_value: Decimal | None,
    ) -> GlobalFinancialTrendMetricDTO:
        if current_value is None or previous_value is None:
            return GlobalFinancialTrendMetricDTO(
                metric=metric,
                current_value=current_value,
                previous_value=previous_value,
                absolute_delta=None,
                percentage_delta=None,
                direction=FinancialTrendDirection.INSUFFICIENT_DATA,
            )

        absolute_delta = current_value - previous_value
        return GlobalFinancialTrendMetricDTO(
            metric=metric,
            current_value=current_value,
            previous_value=previous_value,
            absolute_delta=absolute_delta,
            percentage_delta=cls._percentage_delta(absolute_delta, previous_value),
            direction=cls._global_direction(current_value, previous_value),
        )

    @classmethod
    def _build_current_category_metric(
        cls,
        category: str,
        current_expense: Decimal,
        previous_expense: Decimal | None,
    ) -> CategoryFinancialTrendDTO:
        if previous_expense is None:
            return CategoryFinancialTrendDTO(
                category=category,
                current_expense=current_expense,
                previous_expense=None,
                absolute_delta=None,
                percentage_delta=None,
                direction=CategoryTrendDirection.NEW,
            )

        absolute_delta = current_expense - previous_expense
        return CategoryFinancialTrendDTO(
            category=category,
            current_expense=current_expense,
            previous_expense=previous_expense,
            absolute_delta=absolute_delta,
            percentage_delta=cls._percentage_delta(absolute_delta, previous_expense),
            direction=CategoryTrendDirection(
                cls._global_direction(current_expense, previous_expense).value
            ),
        )

    @staticmethod
    def _percentage_delta(
        absolute_delta: Decimal,
        previous_value: Decimal,
    ) -> Decimal | None:
        if previous_value == 0:
            return None
        return absolute_delta / abs(previous_value)

    @staticmethod
    def _global_direction(
        current_value: Decimal,
        previous_value: Decimal,
    ) -> FinancialTrendDirection:
        if current_value > previous_value:
            return FinancialTrendDirection.INCREASED
        if current_value < previous_value:
            return FinancialTrendDirection.DECREASED
        return FinancialTrendDirection.UNCHANGED

    @classmethod
    def _resolve_comparison_months(
        cls,
        requested_reference_month: str,
        current_reference_month: str,
    ) -> tuple[str, str]:
        requested = cls._parse_reference_month(requested_reference_month)
        current = cls._parse_reference_month(current_reference_month)
        trend_target = (
            cls._previous_calendar_month(requested)
            if requested == current
            else requested
        )
        comparison = cls._previous_calendar_month(trend_target)
        return trend_target.strftime("%Y-%m"), comparison.strftime("%Y-%m")

    @staticmethod
    def _parse_reference_month(reference_month: str) -> datetime:
        try:
            parsed = datetime.strptime(reference_month, "%Y-%m")
        except ValueError as error:
            raise ValueError("reference_month must use YYYY-MM") from error
        if parsed.strftime("%Y-%m") != reference_month:
            raise ValueError("reference_month must use YYYY-MM")
        return parsed

    @staticmethod
    def _previous_calendar_month(month: datetime) -> datetime:
        year = month.year if month.month > 1 else month.year - 1
        previous_month = month.month - 1 if month.month > 1 else 12
        return month.replace(year=year, month=previous_month)

    @staticmethod
    def _validate_unique_months(months: Sequence[Any]) -> None:
        reference_months = [month.reference_month for month in months]
        if len(reference_months) != len(set(reference_months)):
            raise ValueError("Duplicate reference_month values are not allowed")

    @staticmethod
    def _validate_unique_categories(month: CategoryExpenseMonthDTO) -> None:
        categories = [item.category for item in month.category_totals]
        if len(categories) != len(set(categories)):
            raise ValueError("Duplicate category values are not allowed")


class CategoryExpenseIntelligenceService:
    """Builds deterministic expense-distribution metrics from certified categories."""

    def build(
        self,
        category_totals: Sequence[CategoryExpenseTotalDTO],
    ) -> CategoryExpenseSummaryDTO:
        self._validate_unique_categories(category_totals)
        total_expense = sum(
            (item.expense_total for item in category_totals),
            Decimal("0.00"),
        )
        ordered_totals = sorted(
            category_totals,
            key=lambda item: (-item.expense_total, item.category),
        )
        categories = [
            CategoryExpenseMetricDTO(
                category=item.category,
                expense_total=item.expense_total,
                share_of_expenses=(
                    None
                    if total_expense == 0
                    else item.expense_total / total_expense
                ),
                rank=index,
            )
            for index, item in enumerate(ordered_totals, start=1)
        ]
        return CategoryExpenseSummaryDTO(
            total_expense=total_expense,
            categories=categories,
            top_category=categories[0] if categories else None,
        )

    @staticmethod
    def _validate_unique_categories(
        category_totals: Sequence[CategoryExpenseTotalDTO],
    ) -> None:
        categories = [item.category for item in category_totals]
        if len(categories) != len(set(categories)):
            raise ValueError("Duplicate category values are not allowed")


class SpendingAnomalyService:
    """Evaluates certified category totals according to the approved ADR-015 contract."""

    _BASELINE_MONTH_COUNT = 3
    _MINIMUM_HISTORY_MONTHS = 2
    _BASELINE_FLOOR = Decimal("50.00")
    _SPIKE_MULTIPLIER = Decimal("1.5")
    _NEW_EXPENSE_THRESHOLD = Decimal("100.00")

    def evaluate(
        self,
        target_month: CategoryExpenseMonthDTO,
        baseline_months: Sequence[CategoryExpenseMonthDTO],
    ) -> SpendingAnomalySummaryDTO:
        """Evaluate only categories certified in the target month; never synthesize data."""
        self._validate_unique_categories(target_month)
        if not self._has_required_continuous_baseline(
            target_month.reference_month,
            baseline_months,
        ):
            return SpendingAnomalySummaryDTO(
                target_reference_month=target_month.reference_month,
                global_status=SpendingAnomalyGlobalStatus.INSUFFICIENT_BASELINE,
                evaluations=[],
                anomalies=[],
            )

        ordered_baseline_months = sorted(baseline_months, key=lambda item: item.reference_month)
        for month in ordered_baseline_months:
            self._validate_unique_categories(month)

        evaluations = [
            self._evaluate_category(
                current_total,
                ordered_baseline_months,
            )
            for current_total in target_month.category_totals
        ]
        anomalies = [
            evaluation
            for evaluation in evaluations
            if evaluation.status in {
                SpendingAnomalyStatus.SPIKE,
                SpendingAnomalyStatus.NEW_EXPENSE,
            }
        ]
        return SpendingAnomalySummaryDTO(
            target_reference_month=target_month.reference_month,
            global_status=SpendingAnomalyGlobalStatus.OK,
            evaluations=evaluations,
            anomalies=anomalies,
        )

    def _evaluate_category(
        self,
        current_total: CategoryExpenseTotalDTO,
        baseline_months: Sequence[CategoryExpenseMonthDTO],
    ) -> SpendingAnomalyEvaluationDTO:
        historical_values = []
        historical_months = []
        for month in baseline_months:
            matching_total = next(
                (
                    total
                    for total in month.category_totals
                    if total.category == current_total.category
                ),
                None,
            )
            if matching_total is not None:
                historical_values.append(matching_total.expense_total)
                historical_months.append(month.reference_month)

        history_count = len(historical_values)
        if history_count == 0:
            return self._new_expense_evaluation(current_total)
        if history_count < self._MINIMUM_HISTORY_MONTHS:
            return SpendingAnomalyEvaluationDTO(
                category=current_total.category,
                status=SpendingAnomalyStatus.INSUFFICIENT_HISTORY,
                current_expense=current_total.expense_total,
                baseline_values=historical_values,
                baseline_months_used=historical_months,
                baseline_reference=None,
                ratio=None,
                ratio_threshold=None,
                baseline_floor=None,
                new_expense_threshold=None,
            )

        baseline_reference = sum(historical_values, Decimal("0")) / Decimal(history_count)
        ratio = (
            current_total.expense_total / baseline_reference
            if baseline_reference > 0
            else None
        )
        if baseline_reference < self._BASELINE_FLOOR:
            status = SpendingAnomalyStatus.BELOW_BASELINE_FLOOR
        elif current_total.expense_total > baseline_reference * self._SPIKE_MULTIPLIER:
            status = SpendingAnomalyStatus.SPIKE
        else:
            status = SpendingAnomalyStatus.NORMAL

        return SpendingAnomalyEvaluationDTO(
            category=current_total.category,
            status=status,
            current_expense=current_total.expense_total,
            baseline_values=historical_values,
            baseline_months_used=historical_months,
            baseline_reference=baseline_reference,
            ratio=ratio,
            ratio_threshold=self._SPIKE_MULTIPLIER,
            baseline_floor=self._BASELINE_FLOOR,
            new_expense_threshold=None,
        )

    def _new_expense_evaluation(
        self,
        current_total: CategoryExpenseTotalDTO,
    ) -> SpendingAnomalyEvaluationDTO:
        status = (
            SpendingAnomalyStatus.NEW_EXPENSE
            if current_total.expense_total >= self._NEW_EXPENSE_THRESHOLD
            else SpendingAnomalyStatus.NEW_EXPENSE_BELOW_THRESHOLD
        )
        return SpendingAnomalyEvaluationDTO(
            category=current_total.category,
            status=status,
            current_expense=current_total.expense_total,
            baseline_values=[],
            baseline_months_used=[],
            baseline_reference=None,
            ratio=None,
            ratio_threshold=None,
            baseline_floor=None,
            new_expense_threshold=self._NEW_EXPENSE_THRESHOLD,
        )

    @classmethod
    def _has_required_continuous_baseline(
        cls,
        target_reference_month: str,
        baseline_months: Sequence[CategoryExpenseMonthDTO],
    ) -> bool:
        if len(baseline_months) != cls._BASELINE_MONTH_COUNT:
            return False
        reference_months = [month.reference_month for month in baseline_months]
        if len(reference_months) != len(set(reference_months)):
            return False
        expected_months = cls._preceding_months(target_reference_month)
        return set(reference_months) == set(expected_months)

    @classmethod
    def _preceding_months(cls, target_reference_month: str) -> list[str]:
        try:
            target = datetime.strptime(target_reference_month, "%Y-%m")
        except ValueError as error:
            raise ValueError("reference_month must use YYYY-MM") from error

        months = []
        year, month = target.year, target.month
        for _ in range(cls._BASELINE_MONTH_COUNT):
            month -= 1
            if month == 0:
                year -= 1
                month = 12
            months.append(f"{year:04d}-{month:02d}")
        return list(reversed(months))

    @staticmethod
    def _validate_unique_categories(month: CategoryExpenseMonthDTO) -> None:
        categories = [total.category for total in month.category_totals]
        if len(categories) != len(set(categories)):
            raise ValueError("Duplicate category values are not allowed")
