from datetime import date

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    net_worth: str
    income: str
    expenses: str
    balance: str


class KpiItem(BaseModel):
    current: float
    previous: float
    delta_pct: float


class DashboardSummaryV2(BaseModel):
    month: str
    receitas: KpiItem
    despesas: KpiItem
    saldo_liquido: KpiItem
    patrimonio: KpiItem


class SubscriptionItem(BaseModel):
    original_name: str
    date: str
    amount: float


class SubscriptionsSummary(BaseModel):
    month: str
    active_count: int
    monthly_total: float
    annual_projection: float
    average_per_service: float
    items: list[SubscriptionItem]


class InstallmentItem(BaseModel):
    base_name: str
    original_name: str
    date: str
    installment_amount: float
    current_installment: int
    total_installments: int
    total_estimated: float
    already_paid: float
    remaining: float


class InstallmentsSummary(BaseModel):
    month: str
    active_installments: int
    finished_installments: int
    global_estimated: float
    global_paid: float
    global_remaining: float
    last_installment_date: str | None
    items: list[InstallmentItem]


class PacingComparison(BaseModel):
    current_month: str
    previous_month: str
    current_expenses: str
    previous_expenses: str
    delta_percentage: str
    trend: str
    severity: str
    message: str


class DailyDataPoint(BaseModel):
    date: str
    current_amount: float
    previous_amount: float


class PacingV2(BaseModel):
    current_month: str
    previous_month: str
    current_expenses: float
    previous_expenses: float
    delta_percentage: float
    trend: str
    severity: str
    message: str
    daily_data: list[DailyDataPoint]


class DailyHeatmap(BaseModel):
    date: date
    amount: str
    intensity: float


class CategoryComparison(BaseModel):
    category: str
    current_amount: str
    previous_amount: str
    delta_percentage: str
    severity: str


class CategoryBreakdown(BaseModel):
    # Devolvemos float aqui em vez de string formatada (como noutros endpoints do dashboard) para permitir que o Frontend calcule percentagens visuais e formate para BRL localmente.
    category: str
    total: float