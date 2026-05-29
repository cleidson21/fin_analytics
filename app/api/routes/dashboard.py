from fastapi import APIRouter, Query

from app.api.schemas.dashboard import CategoryComparison, DailyHeatmap, DashboardSummary, PacingComparison
from app.api.services.analytics import AnalyticsService
from app.core.formatters import format_money
from app.api.validators import validate_month
from database.queries import FinancialQueries


router = APIRouter()
queries = FinancialQueries()
analytics_service = AnalyticsService()


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(month: str | None = Query(None, description="Filtro de mês no formato YYYY-MM")):
    """Retorna os KPIs principais. Se o mês não for passado, retorna o acumulado de todo o histórico."""
    if month:
        validate_month(month)

    net_worth = queries.get_current_net_worth()
    df_cash = queries.get_cashflow_summary(month=month)

    receitas_val = df_cash.loc[df_cash["natureza"] == "INCOME", "total"].sum() if not df_cash.empty else 0
    gastos_val = df_cash.loc[df_cash["natureza"] == "EXPENSE", "total"].sum() if not df_cash.empty else 0

    income_fmt = format_money(receitas_val)
    expenses_fmt = format_money(abs(gastos_val))
    balance_fmt = format_money(receitas_val + gastos_val)

    return DashboardSummary(
        net_worth=format_money(net_worth),
        income=income_fmt,
        expenses=expenses_fmt,
        balance=balance_fmt,
    )


@router.get("/pacing", response_model=PacingComparison)
def get_expense_pacing(month: str = Query(..., description="Filtro de mês YYYY-MM")):
    """Retorna o Ritmo de Gastos inteligente (MoM) para o frontend."""
    valid_month = validate_month(month)
    return analytics_service.get_expense_pacing(valid_month)


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