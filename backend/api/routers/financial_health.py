from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.cashflow_summary_dto import (
    CategoryExpenseMonthDTO,
    CategoryExpenseTotalDTO,
    MonthlyCashflowDTO,
    MonthlyCashflowPeriodDTO,
)
from backend.application.dtos.financial_health_response_dto import (
    CashflowSummaryResponseDTO,
    CategoryFinancialTrendResponseDTO,
    CategoryFinancialTrendSummaryResponseDTO,
    CategoryExpenseMetricResponseDTO,
    CategoryExpenseSummaryResponseDTO,
    FinancialTrendResponseDTO,
    GlobalFinancialTrendMetricResponseDTO,
    GlobalFinancialTrendResponseDTO,
    MonthlyFinancialMetricsResponseDTO,
    SpendingAnomalyEvaluationResponseDTO,
    SpendingAnomalySummaryResponseDTO,
)
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.database.session import SessionLocal
from backend.domains.health.repository import HealthFinancialQuery
from backend.domains.health.service import (
    CashflowMetricsService,
    CategoryExpenseIntelligenceService,
    HistoricalFinancialMetricsService,
    FinancialTrendService,
    SpendingAnomalyService,
)


router = APIRouter(prefix="/financial-health", tags=["Financial Health"])
ReferenceMonth = Annotated[
    str,
    Query(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Target reference month in YYYY-MM format.",
    ),
]


def _month_bounds(reference_month: str) -> tuple[datetime, datetime]:
    year, month = map(int, reference_month.split("-"))
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    return datetime(year, month, 1), datetime(next_year, next_month, 1)


def _preceding_months(reference_month: str) -> list[str]:
    year, month = map(int, reference_month.split("-"))
    months = []
    for _ in range(3):
        month -= 1
        if month == 0:
            year -= 1
            month = 12
        months.append(f"{year:04d}-{month:02d}")
    return list(reversed(months))


def _current_reference_month() -> str:
    """Resolve the application's local current calendar month at the API boundary."""
    return datetime.now().strftime("%Y-%m")


def _cashflow_response(reference_month: str, summary) -> CashflowSummaryResponseDTO:
    return CashflowSummaryResponseDTO(
        reference_month=reference_month,
        total_income=summary.total_income,
        total_expense=summary.total_expense,
        net_cashflow=summary.net_cashflow,
        savings_amount=summary.savings_amount,
        savings_rate=summary.savings_rate,
        average_monthly_income=summary.average_monthly_income,
        average_monthly_expense=summary.average_monthly_expense,
        average_monthly_net_cashflow=summary.average_monthly_net_cashflow,
    )


def _category_metric_response(metric) -> CategoryExpenseMetricResponseDTO:
    return CategoryExpenseMetricResponseDTO(
        category=metric.category,
        expense_total=metric.expense_total,
        share_of_expenses=metric.share_of_expenses,
        rank=metric.rank,
    )


def _anomaly_evaluation_response(evaluation) -> SpendingAnomalyEvaluationResponseDTO:
    return SpendingAnomalyEvaluationResponseDTO(
        category=evaluation.category,
        status=evaluation.status.value,
        current_expense=evaluation.current_expense,
        baseline_values=evaluation.baseline_values,
        baseline_months_used=evaluation.baseline_months_used,
        baseline_reference=evaluation.baseline_reference,
        ratio=evaluation.ratio,
        ratio_threshold=evaluation.ratio_threshold,
        baseline_floor=evaluation.baseline_floor,
        new_expense_threshold=evaluation.new_expense_threshold,
    )


def _category_month(query: HealthFinancialQuery, db, reference_month: str) -> CategoryExpenseMonthDTO:
    start_date, end_date = _month_bounds(reference_month)
    return CategoryExpenseMonthDTO(
        reference_month=reference_month,
        category_totals=[
            CategoryExpenseTotalDTO(**item)
            for item in query.get_category_expenses(db, start_date, end_date)
        ],
    )


def _trend_inputs(query: HealthFinancialQuery, db, reference_month: str):
    """Build certified, pre-consolidated trend inputs without trend arithmetic in the router."""
    _, target_end = _month_bounds(reference_month)
    rows = query.get_monthly_totals(db, datetime(1900, 1, 1), target_end)
    history = HistoricalFinancialMetricsService().build([
        MonthlyCashflowPeriodDTO(
            reference_month=row["month"],
            income=row["income"],
            expense=row["expense"],
        )
        for row in rows
    ])
    category_months = [
        _category_month(query, db, row["month"])
        for row in rows
    ]
    return history, category_months


def _global_trend_metric_response(metric) -> GlobalFinancialTrendMetricResponseDTO:
    return GlobalFinancialTrendMetricResponseDTO(
        metric=metric.metric.value,
        current_value=metric.current_value,
        previous_value=metric.previous_value,
        absolute_delta=metric.absolute_delta,
        percentage_delta=metric.percentage_delta,
        direction=metric.direction.value,
    )


def _category_trend_response(item) -> CategoryFinancialTrendResponseDTO:
    return CategoryFinancialTrendResponseDTO(
        category=item.category,
        current_expense=item.current_expense,
        previous_expense=item.previous_expense,
        absolute_delta=item.absolute_delta,
        percentage_delta=item.percentage_delta,
        direction=item.direction.value,
    )


@router.get("/cashflow", response_model=CashflowSummaryResponseDTO)
def get_cashflow_summary(
    reference_month: ReferenceMonth,
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """Return target-month cashflow plus averages from supplied closed baseline months."""
    query = HealthFinancialQuery()
    db = SessionLocal()
    try:
        target_start, target_end = _month_bounds(reference_month)
        cashflow_totals = query.get_cashflow(db, target_start, target_end)
        baseline_start, _ = _month_bounds(_preceding_months(reference_month)[0])
        monthly_rows = query.get_monthly_totals(db, baseline_start, target_start)
        monthly_totals = [
            MonthlyCashflowDTO(income=row["income"], expense=row["expense"])
            for row in monthly_rows
        ]
        summary = CashflowMetricsService().calculate(cashflow_totals, monthly_totals)
        return _cashflow_response(reference_month, summary)
    finally:
        db.close()


@router.get("/history", response_model=list[MonthlyFinancialMetricsResponseDTO])
def get_historical_financial_metrics(
    reference_month: ReferenceMonth,
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """Return certified monthly history through the requested month without filling gaps."""
    query = HealthFinancialQuery()
    db = SessionLocal()
    try:
        _, target_end = _month_bounds(reference_month)
        rows = query.get_monthly_totals(db, datetime(1900, 1, 1), target_end)
        history = HistoricalFinancialMetricsService().build([
            MonthlyCashflowPeriodDTO(
                reference_month=row["month"],
                income=row["income"],
                expense=row["expense"],
            )
            for row in rows
        ])
        return [
            MonthlyFinancialMetricsResponseDTO(
                reference_month=item.reference_month,
                total_income=item.total_income,
                total_expense=item.total_expense,
                net_cashflow=item.net_cashflow,
                savings_amount=item.savings_amount,
                savings_rate=item.savings_rate,
            )
            for item in history
        ]
    finally:
        db.close()


@router.get("/categories", response_model=CategoryExpenseSummaryResponseDTO)
def get_category_expense_intelligence(
    reference_month: ReferenceMonth,
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """Return certified category totals, shares, ranking, and top category for one month."""
    query = HealthFinancialQuery()
    db = SessionLocal()
    try:
        summary = CategoryExpenseIntelligenceService().build(
            _category_month(query, db, reference_month).category_totals,
        )
        categories = [_category_metric_response(item) for item in summary.categories]
        return CategoryExpenseSummaryResponseDTO(
            reference_month=reference_month,
            total_expense=summary.total_expense,
            categories=categories,
            top_category=categories[0] if categories else None,
        )
    finally:
        db.close()


@router.get("/anomalies", response_model=SpendingAnomalySummaryResponseDTO)
def get_spending_anomalies(
    reference_month: ReferenceMonth,
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """Return ADR-015 evaluations and deterministic anomaly signals for one target month."""
    query = HealthFinancialQuery()
    db = SessionLocal()
    try:
        baseline_references = _preceding_months(reference_month)
        baseline_start, _ = _month_bounds(baseline_references[0])
        target_start, _ = _month_bounds(reference_month)
        available_months = {
            row["month"]
            for row in query.get_monthly_totals(db, baseline_start, target_start)
        }
        baseline_months = [
            _category_month(query, db, month)
            for month in baseline_references
            if month in available_months
        ]
        summary = SpendingAnomalyService().evaluate(
            _category_month(query, db, reference_month),
            baseline_months,
        )
        evaluations = [_anomaly_evaluation_response(item) for item in summary.evaluations]
        anomalies = [_anomaly_evaluation_response(item) for item in summary.anomalies]
        return SpendingAnomalySummaryResponseDTO(
            target_reference_month=summary.target_reference_month,
            global_status=summary.global_status.value,
            evaluations=evaluations,
            anomalies=anomalies,
        )
    finally:
        db.close()


@router.get("/trends", response_model=FinancialTrendResponseDTO, response_model_by_alias=True)
def get_financial_trends(
    reference_month: ReferenceMonth,
    current_user: UserResponseDTO = Depends(get_current_user),
):
    """Expose ADR-018 trend facts derived from certified Health query results."""
    query = HealthFinancialQuery()
    db = SessionLocal()
    try:
        monthly_metrics, category_months = _trend_inputs(query, db, reference_month)
        current_month = _current_reference_month()
        service = FinancialTrendService()
        global_summary = service.build_global(
            reference_month,
            current_month,
            monthly_metrics,
        )
        category_summary = service.build_categories(
            reference_month,
            current_month,
            category_months,
        )
        return FinancialTrendResponseDTO(
            requested_reference_month=global_summary.requested_reference_month,
            trend_target_month=global_summary.trend_target_month,
            comparison_month=global_summary.comparison_month,
            status=global_summary.status.value,
            global_=GlobalFinancialTrendResponseDTO(
                status=global_summary.status.value,
                metrics=[
                    _global_trend_metric_response(metric)
                    for metric in global_summary.metrics
                ],
            ),
            categories=CategoryFinancialTrendSummaryResponseDTO(
                status=category_summary.status.value,
                items=[
                    _category_trend_response(item)
                    for item in category_summary.categories
                ],
            ),
        )
    finally:
        db.close()
