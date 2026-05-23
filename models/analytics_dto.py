"""Typed DTOs for analytical responses exposed by the service layer."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class _AnalyticsDTO(BaseModel):
	"""Base configuration shared by all analytical DTOs."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class CashflowDTO(_AnalyticsDTO):
	"""Monthly or period cashflow summary."""

	receitas: Decimal = Field(..., description="Total income in the period.")
	gastos: Decimal = Field(..., description="Total expenses in the period.")
	saldo_liquido: Decimal = Field(..., description="Net cash balance in the period.")


class ExpenseByCategoryDTO(_AnalyticsDTO):
	"""Expense breakdown grouped by business category."""

	categoria: str = Field(..., min_length=1, description="Expense category name.")
	total: Decimal = Field(..., description="Total expense amount for the category.")
	percentual: Decimal = Field(..., description="Category share over total expenses.")


class SavingsMetricsDTO(_AnalyticsDTO):
	"""Savings-efficiency metrics for a given period."""

	receitas: Decimal = Field(..., description="Total income in the period.")
	gastos: Decimal = Field(..., description="Total expenses in the period.")
	investimentos: Decimal = Field(..., description="Total investments in the period.")
	taxa_poupanca_percentual: Decimal = Field(..., description="Savings rate as a percentage.")


class InvestmentSummaryDTO(_AnalyticsDTO):
	"""Aggregate investment summary."""

	aportes: Decimal = Field(..., description="Total investment contributions.")
	dividendos: Decimal = Field(..., description="Total dividend or income distributions.")
	total: Decimal = Field(..., description="Total investment amount.")
