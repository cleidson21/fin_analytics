"""Analytical service layer for financial KPIs.

The service owns business calculations and composes typed DTOs on top of the
repository layer, which remains responsible only for data access.
"""

from __future__ import annotations

from functools import lru_cache
from datetime import date
from decimal import Decimal
from typing import Final

import duckdb

from models.analytics_dto import (
	CashflowDTO,
	ExpenseByCategoryDTO,
	InvestmentSummaryDTO,
	SavingsMetricsDTO,
)
from repositories.transacoes_repository import TransacoesRepository

_ZERO: Final[Decimal] = Decimal("0.00")


class FinanceService:
	"""Provide analytical KPIs over curated transaction data."""

	def __init__(self, repository: TransacoesRepository) -> None:
		self._repository = repository

	def get_cashflow_summary(self, start_date: date, end_date: date) -> CashflowDTO:
		"""Return the cashflow summary for the requested period."""

		return self._cashflow_summary_cached(start_date, end_date)

	def get_expenses_breakdown(self, start_date: date, end_date: date) -> list[ExpenseByCategoryDTO]:
		"""Return the expense breakdown by category for the requested period."""

		return list(self._expenses_breakdown_cached(start_date, end_date))

	def get_savings_metrics(self, start_date: date, end_date: date) -> SavingsMetricsDTO:
		"""Return savings-related metrics for the requested period."""

		cashflow = self._cashflow_summary_cached(start_date, end_date)
		investment_summary = self._investment_summary_cached(start_date, end_date)
		receitas = cashflow.receitas
		gastos = cashflow.gastos
		investimentos = investment_summary.total

		if receitas == 0:
			taxa_poupanca = _ZERO
		else:
			taxa_poupanca = ((receitas - gastos) / receitas * Decimal("100")).quantize(Decimal("0.01"))

		return SavingsMetricsDTO(
			receitas=receitas,
			gastos=gastos,
			investimentos=investimentos,
			taxa_poupanca_percentual=taxa_poupanca,
		)

	def get_investment_summary(self, start_date: date, end_date: date) -> InvestmentSummaryDTO:
		"""Return the investment summary for the requested period."""

		return self._investment_summary_cached(start_date, end_date)

	@lru_cache(maxsize=256)
	def _cashflow_summary_cached(self, start_date: date, end_date: date) -> CashflowDTO:
		period_relation = self._period_relation(start_date, end_date)
		result = period_relation.query(
			"period",
			"""
			SELECT
				COALESCE(SUM(CASE WHEN Tipo = 'RECEITA' THEN Valor ELSE 0 END), 0) AS receitas,
				COALESCE(SUM(CASE WHEN Tipo = 'GASTO' THEN ABS(Valor) ELSE 0 END), 0) AS gastos,
				COALESCE(SUM(CASE WHEN Tipo = 'RECEITA' THEN Valor ELSE 0 END), 0)
				- COALESCE(SUM(CASE WHEN Tipo = 'GASTO' THEN ABS(Valor) ELSE 0 END), 0) AS saldo_liquido
			FROM period
			""",
		).fetchone()
		assert result is not None
		return CashflowDTO(
			receitas=self._as_decimal(result[0]),
			gastos=self._as_decimal(result[1]),
			saldo_liquido=self._as_decimal(result[2]),
		)

	@lru_cache(maxsize=256)
	def _expenses_breakdown_cached(
		self,
		start_date: date,
		end_date: date,
	) -> tuple[ExpenseByCategoryDTO, ...]:
		period_relation = self._period_relation(start_date, end_date)
		rows = period_relation.query(
			"period",
			"""
			WITH category_base AS (
				SELECT
					Categoria AS categoria,
					SUM(ABS(Valor)) AS total
				FROM period
				WHERE Tipo = 'GASTO'
				GROUP BY 1
			),
			category_totals AS (
				SELECT SUM(total) AS total_expenses FROM category_base
			)
			SELECT
				c.categoria,
				COALESCE(c.total, 0) AS total,
				CASE
					WHEN t.total_expenses IS NULL OR t.total_expenses = 0 THEN 0
					ELSE ROUND((c.total / t.total_expenses) * 100, 2)
				END AS percentual
			FROM category_base c
			CROSS JOIN category_totals t
			ORDER BY c.total DESC, c.categoria
			""",
		).fetchall()
		return tuple(
			ExpenseByCategoryDTO(
				categoria=str(row[0]),
				total=self._as_decimal(row[1]),
				percentual=self._as_decimal(row[2]),
			)
			for row in rows
		)

	@lru_cache(maxsize=256)
	def _investment_summary_cached(self, start_date: date, end_date: date) -> InvestmentSummaryDTO:
		period_relation = self._period_relation(start_date, end_date)
		result = period_relation.query(
			"period",
			"""
			SELECT
				COALESCE(SUM(CASE WHEN Tipo = 'INVESTIMENTO' AND NOT regexp_matches(lower(Descricao), '(dividend|provento|jcp)') THEN ABS(Valor) ELSE 0 END), 0) AS aportes,
				COALESCE(SUM(CASE WHEN regexp_matches(lower(Descricao), '(dividend|provento|jcp)') THEN ABS(Valor) ELSE 0 END), 0) AS dividendos,
				COALESCE(SUM(CASE WHEN Tipo = 'INVESTIMENTO' OR Categoria = 'INVESTIMENTOS' THEN ABS(Valor) ELSE 0 END), 0) AS total
			FROM period
			WHERE Tipo = 'INVESTIMENTO' OR Categoria = 'INVESTIMENTOS'
			""",
		).fetchone()
		assert result is not None
		return InvestmentSummaryDTO(
			aportes=self._as_decimal(result[0]),
			dividendos=self._as_decimal(result[1]),
			total=self._as_decimal(result[2]),
		)

	@lru_cache(maxsize=256)
	def _period_relation(self, start_date: date, end_date: date) -> duckdb.DuckDBPyRelation:
		"""Fetch and cache the relation for the requested period."""

		return self._repository.fetch_transactions_by_period(start_date, end_date)

	@staticmethod
	def _as_decimal(value: object) -> Decimal:
		"""Convert DuckDB numeric output into a fixed two-decimal ``Decimal``."""

		if isinstance(value, Decimal):
			return value.quantize(Decimal("0.01"))
		return Decimal(str(value)).quantize(Decimal("0.01"))
