from datetime import date

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    net_worth: str
    income: str
    expenses: str
    balance: str


class PacingComparison(BaseModel):
    current_month: str
    previous_month: str
    current_expenses: str
    previous_expenses: str
    delta_percentage: str
    trend: str
    severity: str
    message: str


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