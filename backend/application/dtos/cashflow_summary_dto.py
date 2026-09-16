from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional


@dataclass(frozen=True)
class MonthlyCashflowDTO:
    """Certified monthly cashflow totals supplied by the Health read layer."""

    income: Decimal
    expense: Decimal


@dataclass(frozen=True)
class MonthlyCashflowPeriodDTO:
    """Certified cashflow totals for one reference month (YYYY-MM)."""

    reference_month: str
    income: Decimal
    expense: Decimal


@dataclass(frozen=True)
class MonthlyFinancialMetricsDTO:
    """Deterministic Financial Health metrics for one reference month."""

    reference_month: str
    total_income: Decimal
    total_expense: Decimal
    net_cashflow: Decimal
    savings_amount: Decimal
    savings_rate: Optional[Decimal]


@dataclass(frozen=True)
class CategoryExpenseTotalDTO:
    """Certified expense total for one governed category."""

    category: str
    expense_total: Decimal


@dataclass(frozen=True)
class CategoryExpenseMetricDTO:
    """Deterministic expense distribution metrics for one category."""

    category: str
    expense_total: Decimal
    share_of_expenses: Optional[Decimal]
    rank: int


@dataclass(frozen=True)
class CategoryExpenseSummaryDTO:
    """Deterministic expense distribution for a certified category collection."""

    total_expense: Decimal
    categories: list[CategoryExpenseMetricDTO]
    top_category: Optional[CategoryExpenseMetricDTO]


@dataclass(frozen=True)
class CategoryExpenseMonthDTO:
    """Certified, pre-consolidated category expense totals for one YYYY-MM month."""

    reference_month: str
    category_totals: list[CategoryExpenseTotalDTO]


class SpendingAnomalyStatus(str, Enum):
    """Approved category evaluation states from ADR-015."""

    NORMAL = "NORMAL"
    SPIKE = "SPIKE"
    NEW_EXPENSE = "NEW_EXPENSE"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    BELOW_BASELINE_FLOOR = "BELOW_BASELINE_FLOOR"
    NEW_EXPENSE_BELOW_THRESHOLD = "NEW_EXPENSE_BELOW_THRESHOLD"


class SpendingAnomalyGlobalStatus(str, Enum):
    """Approved global baseline availability states from ADR-015."""

    OK = "OK"
    INSUFFICIENT_BASELINE = "INSUFFICIENT_BASELINE"


@dataclass(frozen=True)
class SpendingAnomalyEvaluationDTO:
    """Explainable deterministic evaluation for one current-month category."""

    category: str
    status: SpendingAnomalyStatus
    current_expense: Decimal
    baseline_values: list[Decimal]
    baseline_months_used: list[str]
    baseline_reference: Optional[Decimal]
    ratio: Optional[Decimal]
    ratio_threshold: Optional[Decimal]
    baseline_floor: Optional[Decimal]
    new_expense_threshold: Optional[Decimal]


@dataclass(frozen=True)
class SpendingAnomalySummaryDTO:
    """Deterministic anomaly evaluations for a target month under ADR-015."""

    target_reference_month: str
    global_status: SpendingAnomalyGlobalStatus
    evaluations: list[SpendingAnomalyEvaluationDTO]
    anomalies: list[SpendingAnomalyEvaluationDTO]


class FinancialTrendMetric(str, Enum):
    """Approved global Financial Health metrics from ADR-018."""

    TOTAL_INCOME = "total_income"
    TOTAL_EXPENSE = "total_expense"
    NET_CASHFLOW = "net_cashflow"
    SAVINGS_RATE = "savings_rate"


class FinancialTrendDirection(str, Enum):
    """Exact mathematical directions for global trends from ADR-018."""

    INCREASED = "INCREASED"
    DECREASED = "DECREASED"
    UNCHANGED = "UNCHANGED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class CategoryTrendDirection(str, Enum):
    """Exact category-presence and value directions from ADR-018."""

    INCREASED = "INCREASED"
    DECREASED = "DECREASED"
    UNCHANGED = "UNCHANGED"
    NEW = "NEW"
    DISAPPEARED = "DISAPPEARED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class FinancialTrendSummaryStatus(str, Enum):
    """Availability of the required consecutive closed-month comparison."""

    OK = "OK"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class GlobalFinancialTrendMetricDTO:
    """Deterministic comparison for one certified global metric."""

    metric: FinancialTrendMetric
    current_value: Optional[Decimal]
    previous_value: Optional[Decimal]
    absolute_delta: Optional[Decimal]
    percentage_delta: Optional[Decimal]
    direction: FinancialTrendDirection


@dataclass(frozen=True)
class GlobalFinancialTrendSummaryDTO:
    """Global trend facts for two consecutive closed calendar months."""

    requested_reference_month: str
    trend_target_month: str
    comparison_month: str
    status: FinancialTrendSummaryStatus
    metrics: list[GlobalFinancialTrendMetricDTO]


@dataclass(frozen=True)
class CategoryFinancialTrendDTO:
    """Deterministic trend facts for one exact certified category label."""

    category: str
    current_expense: Optional[Decimal]
    previous_expense: Optional[Decimal]
    absolute_delta: Optional[Decimal]
    percentage_delta: Optional[Decimal]
    direction: CategoryTrendDirection


@dataclass(frozen=True)
class CategoryFinancialTrendSummaryDTO:
    """Category trend facts for two consecutive closed calendar months."""

    requested_reference_month: str
    trend_target_month: str
    comparison_month: str
    status: FinancialTrendSummaryStatus
    categories: list[CategoryFinancialTrendDTO]


@dataclass(frozen=True)
class CashflowSummaryDTO:
    """Deterministic cashflow metrics for a certified financial period."""

    total_income: Decimal
    total_expense: Decimal
    net_cashflow: Decimal
    savings_amount: Decimal
    savings_rate: Optional[Decimal]
    average_monthly_income: Optional[Decimal]
    average_monthly_expense: Optional[Decimal]
    average_monthly_net_cashflow: Optional[Decimal]
