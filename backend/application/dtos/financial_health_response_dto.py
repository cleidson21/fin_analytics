from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CashflowSummaryResponseDTO(BaseModel):
    reference_month: str
    total_income: Decimal
    total_expense: Decimal
    net_cashflow: Decimal
    savings_amount: Decimal
    savings_rate: Optional[Decimal]
    average_monthly_income: Optional[Decimal]
    average_monthly_expense: Optional[Decimal]
    average_monthly_net_cashflow: Optional[Decimal]


class MonthlyFinancialMetricsResponseDTO(BaseModel):
    reference_month: str
    total_income: Decimal
    total_expense: Decimal
    net_cashflow: Decimal
    savings_amount: Decimal
    savings_rate: Optional[Decimal]


class CategoryExpenseMetricResponseDTO(BaseModel):
    category: str
    expense_total: Decimal
    share_of_expenses: Optional[Decimal]
    rank: int


class CategoryExpenseSummaryResponseDTO(BaseModel):
    reference_month: str
    total_expense: Decimal
    categories: list[CategoryExpenseMetricResponseDTO]
    top_category: Optional[CategoryExpenseMetricResponseDTO]


class SpendingAnomalyEvaluationResponseDTO(BaseModel):
    category: str
    status: str
    current_expense: Decimal
    baseline_values: list[Decimal]
    baseline_months_used: list[str]
    baseline_reference: Optional[Decimal]
    ratio: Optional[Decimal]
    ratio_threshold: Optional[Decimal]
    baseline_floor: Optional[Decimal]
    new_expense_threshold: Optional[Decimal]


class SpendingAnomalySummaryResponseDTO(BaseModel):
    target_reference_month: str
    global_status: str
    evaluations: list[SpendingAnomalyEvaluationResponseDTO]
    anomalies: list[SpendingAnomalyEvaluationResponseDTO]


class GlobalFinancialTrendMetricResponseDTO(BaseModel):
    metric: str
    current_value: Optional[Decimal]
    previous_value: Optional[Decimal]
    absolute_delta: Optional[Decimal]
    percentage_delta: Optional[Decimal]
    direction: str


class GlobalFinancialTrendResponseDTO(BaseModel):
    status: str
    metrics: list[GlobalFinancialTrendMetricResponseDTO]


class CategoryFinancialTrendResponseDTO(BaseModel):
    category: str
    current_expense: Optional[Decimal]
    previous_expense: Optional[Decimal]
    absolute_delta: Optional[Decimal]
    percentage_delta: Optional[Decimal]
    direction: str


class CategoryFinancialTrendSummaryResponseDTO(BaseModel):
    status: str
    items: list[CategoryFinancialTrendResponseDTO]


class FinancialTrendResponseDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    requested_reference_month: str
    trend_target_month: str
    comparison_month: str
    status: str
    global_: GlobalFinancialTrendResponseDTO = Field(alias="global")
    categories: CategoryFinancialTrendSummaryResponseDTO
