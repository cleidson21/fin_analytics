from datetime import datetime

from fastapi import APIRouter, Query, Depends
from app.api.deps import require_authenticated

from app.api.schemas.dashboard import (
    CategoryBreakdown,
    CategoryComparison,
    DailyHeatmap,
    DashboardSummary,
    DashboardSummaryV2,
    InstallmentsSummary,
    PacingComparison,
    PacingV2,
    SubscriptionsSummary,
)
from app.api.services.analytics import AnalyticsService
from app.core.formatters import format_money
from app.api.validators import validate_month
from app.api.services.financial_service import FinancialService


router = APIRouter(dependencies=[Depends(require_authenticated)])
service = FinancialService()
analytics_service = AnalyticsService()


def get_current_month() -> str:
    return datetime.now().strftime("%Y-%m")


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(month: str | None = Query(None, description="Filtro de mês no formato YYYY-MM")):
    """Retorna os KPIs principais. Se o mês não for passado, retorna o acumulado de todo o histórico."""
    if month:
        validate_month(month)

    net_worth = service.get_current_net_worth()
    df_cash = service.get_cashflow_summary(month=month)

    receitas_val = df_cash.loc[df_cash["natureza"] == "INCOME", "total"].sum() if not df_cash.empty else 0
    gastos_val = df_cash.loc[df_cash["natureza"] == "EXPENSE", "total"].sum() if not df_cash.empty else 0

    income_fmt = format_money(receitas_val)
    expenses_fmt = format_money(abs(gastos_val))
    balance_fmt = format_money(receitas_val - gastos_val)

    return DashboardSummary(
        net_worth=format_money(net_worth),
        income=income_fmt,
        expenses=expenses_fmt,
        balance=balance_fmt,
    )


@router.get("/summary-v2", response_model=DashboardSummaryV2)
async def get_summary_v2(month: str | None = Query(None, description="Filtro opcional de mês YYYY-MM")):
    valid_month = validate_month(month) if month else get_current_month()
    return analytics_service.get_summary_v2(valid_month)


@router.get("/pacing", response_model=PacingComparison)
def get_expense_pacing(month: str = Query(..., description="Filtro de mês YYYY-MM")):
    """Retorna o Ritmo de Gastos inteligente (MoM) para o frontend."""
    valid_month = validate_month(month)
    return analytics_service.get_expense_pacing(valid_month)


@router.get("/pacing-v2", response_model=PacingV2)
async def get_pacing_v2(month: str | None = Query(None, description="Filtro opcional de mês YYYY-MM")):
    valid_month = validate_month(month) if month else get_current_month()
    return analytics_service.get_pacing_v2(valid_month)


@router.get("/subscriptions", response_model=SubscriptionsSummary)
def get_subscriptions_summary(month: str | None = Query(None, description="Filtro opcional de mês YYYY-MM")):
    valid_month = validate_month(month) if month else get_current_month()
    return analytics_service.get_subscriptions_summary(valid_month)


@router.get("/installments", response_model=InstallmentsSummary)
def get_installments_summary(month: str | None = Query(None, description="Filtro opcional de mês YYYY-MM")):
    valid_month = validate_month(month) if month else get_current_month()
    return analytics_service.get_installments_summary(valid_month)


@router.get("/heatmap", response_model=list[DailyHeatmap])
def get_monthly_heatmap(month: str = Query(..., description="Filtro de mês YYYY-MM")):
    """Retorna o mapa de calor mensal com intensidade pré-calculada."""
    valid_month = validate_month(month)
    return analytics_service.get_monthly_heatmap(valid_month)


@router.get("/categories/comparison", response_model=list[CategoryComparison])
def get_categories_comparison(month: str = Query(..., description="Filtro de mês YYYY-MM")):
    """Retorna a comparação de gastos por categoria entre meses consecutivos."""
    valid_month = validate_month(month)
    return analytics_service.get_categories_comparison(valid_month)


@router.get("/categories", response_model=list[CategoryBreakdown])
def get_categories_breakdown(month: str | None = Query(None, description="Filtro opcional de mês YYYY-MM")):
    """Retorna o total de gastos por categoria para o mês informado ou o mês corrente."""
    effective_month = month or datetime.now().strftime("%Y-%m")
    valid_month = validate_month(effective_month)
    df = service.get_expenses_by_category(month=valid_month)

    categories = [
        CategoryBreakdown(category=row["macro_categoria"], total=abs(float(row["total"])))
        for _, row in df.iterrows()
    ]
    categories.sort(key=lambda item: item.total, reverse=True)
    return categories