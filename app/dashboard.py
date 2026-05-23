"""Streamlit dashboard for the analytical layer of FinAnalytics.

The dashboard keeps presentation concerns isolated from the analytical
service and repository layers. It consumes DTOs from ``FinanceService`` and
uses Streamlit caching to reduce repeated I/O across reruns.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from app.dependencies import get_finance_service, get_transacoes_repository
from config.constants import StatusProcessamento
from models.analytics_dto import (
	CashflowDTO,
	ExpenseByCategoryDTO,
	InvestmentSummaryDTO,
	SavingsMetricsDTO,
)
from utils.formatters import format_currency_br, format_percentage


st.set_page_config(page_title="FinAnalytics", layout="wide")


@st.cache_data(ttl=300, show_spinner=False)
def load_cashflow_summary(start_date: date, end_date: date) -> CashflowDTO:
	"""Load the cashflow DTO for the selected period."""

	return get_finance_service().get_cashflow_summary(start_date, end_date)


@st.cache_data(ttl=300, show_spinner=False)
def load_expenses_breakdown(start_date: date, end_date: date) -> list[ExpenseByCategoryDTO]:
	"""Load the expense breakdown DTO list for the selected period."""

	return get_finance_service().get_expenses_breakdown(start_date, end_date)


@st.cache_data(ttl=300, show_spinner=False)
def load_savings_metrics(start_date: date, end_date: date) -> SavingsMetricsDTO:
	"""Load the savings metrics DTO for the selected period."""

	return get_finance_service().get_savings_metrics(start_date, end_date)


@st.cache_data(ttl=300, show_spinner=False)
def load_investment_summary(start_date: date, end_date: date) -> InvestmentSummaryDTO:
	"""Load the investment summary DTO for the selected period."""

	return get_finance_service().get_investment_summary(start_date, end_date)


@st.cache_data(ttl=300, show_spinner=False)
def load_daily_cashflow_series(start_date: date, end_date: date) -> list[dict[str, Any]]:
	"""Load a daily cashflow series for the overview chart.

	The query runs in DuckDB so the UI remains lightweight and does not perform
	row-by-row processing in Python.
	"""

	relation = get_transacoes_repository().fetch_transactions_by_period(start_date, end_date)
	series = relation.query(
		"period",
		"""
		SELECT
			Data,
			SUM(CASE WHEN Tipo = 'RECEITA' THEN Valor ELSE -ABS(Valor) END) AS fluxo_liquido
		FROM period
		GROUP BY 1
		ORDER BY 1
		""",
	)
	columns = series.columns
	return [dict(zip(columns, row, strict=True)) for row in series.fetchall()]


@st.cache_data(ttl=300, show_spinner=False)
def load_system_health() -> dict[str, Any]:
	"""Load observability metrics for the sidebar health panel."""

	repository = get_transacoes_repository()
	connection = repository._connection
	executions = connection.sql("SELECT COUNT(*) FROM ETL_EXECUTIONS").fetchone()[0]
	quarantine_rows = connection.sql("SELECT COUNT(*) FROM QUARANTINE_TRANSACTIONS").fetchone()[0]
	processed_files = connection.execute(
		"""
		SELECT COUNT(DISTINCT source_file)
		FROM ETL_EXECUTIONS
		WHERE status = ?
		""",
		[StatusProcessamento.SUCESSO.value],
	).fetchone()[0]
	latest_execution = connection.sql(
		"""
		SELECT status, source_file
		FROM ETL_EXECUTIONS
		ORDER BY finished_at DESC
		LIMIT 1
		""",
	).fetchone()
	return {
		"executions": int(executions or 0),
		"quarantine_rows": int(quarantine_rows or 0),
		"processed_files": int(processed_files or 0),
		"latest_execution": latest_execution,
	}


@st.cache_data(ttl=300)
def load_recent_transactions(limit: int = 10) -> list[dict[str, Any]]:
	"""Load the latest curated transactions for the interactive table."""

	relation = get_transacoes_repository().fetch_latest_transactions(limit)
	columns = relation.columns
	rows = []
	for row in relation.fetchall():
		record = dict(zip(columns, row, strict=True))
		record["Valor"] = format_currency_br(Decimal(str(record["Valor"])))
		processed_at = record.get("processed_at")
		if processed_at is not None:
			record["processed_at"] = processed_at.strftime("%Y-%m-%d %H:%M")
		rows.append(record)
	return rows


def _shift_previous_period(start_date: date, end_date: date) -> tuple[date, date]:
	"""Return the previous window with the same number of days."""

	period_days = max((end_date - start_date).days, 0) + 1
	previous_end = start_date - timedelta(days=1)
	previous_start = previous_end - timedelta(days=period_days - 1)
	return previous_start, previous_end


def _decimal_delta(current: Decimal, previous: Decimal) -> Decimal:
	"""Return the numeric delta between two decimal values."""

	return (current - previous).quantize(Decimal("0.01"))


def _render_metric_card(
	label: str,
	value: Decimal,
	*,
	delta: Decimal | None = None,
	delta_suffix: str = "",
	delta_color: str = "normal",
) -> None:
	"""Render a Streamlit metric with a formatted decimal value."""

	delta_text = None if delta is None else f"{format_currency_br(delta)}{delta_suffix}" if delta_suffix != "%" else f"{format_percentage(delta)}"
	st.metric(label=label, value=format_currency_br(value), delta=delta_text, delta_color=delta_color)


def _render_overview_chart(series: list[dict[str, Any]]) -> None:
	"""Render the liquidity evolution chart or an empty-state message."""

	if not series:
		st.info("Não há movimentações para o período selecionado.")
		return

	chart = px.line(
		series,
		x="Data",
		y="fluxo_liquido",
		markers=True,
		labels={"Data": "Data", "fluxo_liquido": "Fluxo líquido"},
		title="Evolução do fluxo líquido",
	)
	chart.update_layout(margin=dict(l=10, r=10, t=50, b=10), hovermode="x unified")
	st.plotly_chart(chart, use_container_width=True, theme="streamlit")


def _render_expenses_chart(expenses: list[ExpenseByCategoryDTO]) -> None:
	"""Render the expense breakdown chart or an empty-state message."""

	if not expenses:
		st.info("Não há despesas classificadas no período selecionado.")
		return

	records = [item.model_dump() for item in expenses]
	chart = px.bar(
		records,
		x="categoria",
		y="total",
		text="percentual",
		labels={"categoria": "Categoria", "total": "Total"},
		title="Despesas por categoria",
	)
	chart.update_layout(margin=dict(l=10, r=10, t=50, b=10), xaxis_title=None, yaxis_title=None)
	st.plotly_chart(chart, use_container_width=True, theme="streamlit")


def _render_investments_chart(investments: InvestmentSummaryDTO) -> None:
	"""Render a small investment summary chart."""

	records = [
		{"tipo": "Aportes", "valor": investments.aportes},
		{"tipo": "Dividendos", "valor": investments.dividendos},
	]
	chart = px.bar(
		records,
		x="tipo",
		y="valor",
		text="valor",
		labels={"tipo": "Tipo", "valor": "Valor"},
		title="Aportes vs proventos",
	)
	chart.update_layout(margin=dict(l=10, r=10, t=50, b=10), xaxis_title=None, yaxis_title=None)
	st.plotly_chart(chart, use_container_width=True, theme="streamlit")


def main() -> None:
	"""Render the FinAnalytics dashboard."""

	today = date.today()
	default_start = today - timedelta(days=29)

	st.sidebar.title("FinAnalytics")
	start_date = st.sidebar.date_input("Data inicial", value=default_start)
	end_date = st.sidebar.date_input("Data final", value=today)

	if start_date > end_date:
		st.sidebar.error("A data inicial deve ser anterior ou igual à data final.")
		st.stop()

	health = load_system_health()
	st.sidebar.subheader("Saúde do sistema")
	col_a, col_b = st.sidebar.columns(2)
	with col_a:
		st.metric("Execuções ETL", health["executions"])
		st.metric("Itens em quarentena", health["quarantine_rows"])
	with col_b:
		st.metric("Arquivos processados", health["processed_files"])
		latest_execution = health["latest_execution"]
		latest_status = latest_execution[0] if latest_execution else "Sem dados"
		st.metric("Último status", latest_status)

	with st.spinner("Carregando indicadores analíticos..."):
		cashflow = load_cashflow_summary(start_date, end_date)
		expenses = load_expenses_breakdown(start_date, end_date)
		savings = load_savings_metrics(start_date, end_date)
		investments = load_investment_summary(start_date, end_date)
		recent_transactions = load_recent_transactions(10)
		daily_series = load_daily_cashflow_series(start_date, end_date)
		previous_start, previous_end = _shift_previous_period(start_date, end_date)
		previous_cashflow = load_cashflow_summary(previous_start, previous_end)
		previous_investments = load_investment_summary(previous_start, previous_end)
		previous_savings = load_savings_metrics(previous_start, previous_end)

	if health["quarantine_rows"] > 0:
		st.warning(
			"Existem registos em quarentena. Revise os itens inválidos ou não classificados antes de tomar decisões operacionais.",
		)

	st.title("FinAnalytics")
	st.caption(f"Período selecionado: {start_date.isoformat()} a {end_date.isoformat()}")

	metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)
	with metric_col_1:
		_render_metric_card(
			"Receita Mensal",
			cashflow.receitas,
			delta=_decimal_delta(cashflow.receitas, previous_cashflow.receitas),
			delta_color="normal",
		)
	with metric_col_2:
		_render_metric_card(
			"Gasto Mensal",
			cashflow.gastos,
			delta=_decimal_delta(cashflow.gastos, previous_cashflow.gastos),
			delta_color="inverse",
		)
	with metric_col_3:
		_render_metric_card(
			"Total Investido",
			investments.total,
			delta=_decimal_delta(investments.total, previous_investments.total),
			delta_color="normal",
		)
	with metric_col_4:
		current_rate = savings.taxa_poupanca_percentual
		previous_rate = previous_savings.taxa_poupanca_percentual
		st.metric(
			"Taxa de Poupança",
			format_percentage(current_rate),
			delta=format_percentage(_decimal_delta(current_rate, previous_rate)),
			delta_color="normal",
		)

	tab_overview, tab_expenses, tab_investments, tab_recent = st.tabs(
		["Visão Geral", "Distribuição de Gastos", "Investimentos", "Transações Recentes"]
	)

	with tab_overview:
		_render_overview_chart(daily_series)

	with tab_expenses:
		_render_expenses_chart(expenses)
		if expenses:
			st.dataframe(
				[
					{
						"Categoria": item.categoria,
						"Total": format_currency_br(item.total),
						"Percentual": format_percentage(item.percentual),
					}
					for item in expenses
				],
				use_container_width=True,
				hide_index=True,
			)

	with tab_investments:
		st.metric("Aportes", format_currency_br(investments.aportes))
		st.metric("Dividendos", format_currency_br(investments.dividendos))
		st.metric("Total", format_currency_br(investments.total))
		_render_investments_chart(investments)

	with tab_recent:
		if not recent_transactions:
			st.info("Não há transações recentes para exibir.")
		else:
			st.dataframe(recent_transactions, use_container_width=True, hide_index=True)


if __name__ == "__main__":
	main()
