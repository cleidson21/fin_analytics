from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class KpiItem(BaseModel):
    current: float
    previous: float
    delta_pct: float

class DashboardSummary(BaseModel):
    net_worth: str
    income: str
    expenses: str
    balance: str

class DashboardSummaryV2(BaseModel):
    month: str
    receitas: KpiItem
    despesas: KpiItem
    saldo_liquido: KpiItem
    patrimonio: KpiItem

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
    daily_data: List[DailyDataPoint]

class DailyHeatmap(BaseModel):
    date: date
    amount: str
    intensity: float

class CategoryBreakdown(BaseModel):
    category: str
    total: float

class CategoryComparison(BaseModel):
    category: str
    current_amount: str
    previous_amount: str
    delta_percentage: str
    severity: str
