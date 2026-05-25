"""Operational home page for consolidated wealth monitoring."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

try:
	from app.components.cards import draw_metric_card
	from app.components.charts import draw_allocation_donut, draw_net_worth_evolution
	from app.core.shell import configure_page, render_sidebar
	from app.core.state import get_wealth_intelligence_service, initialize_session_state, set_active_tab
	from app.dependencies import get_transacoes_repository, get_wealth_repository
except ModuleNotFoundError:
	from components.cards import draw_metric_card
	from components.charts import draw_allocation_donut, draw_net_worth_evolution
	from core.shell import configure_page, render_sidebar
	from core.state import get_wealth_intelligence_service, initialize_session_state, set_active_tab
	from dependencies import get_transacoes_repository, get_wealth_repository


def _to_decimal(value: object) -> Decimal:
	if isinstance(value, Decimal):
		return value
	if isinstance(value, int):
		return Decimal(value)
	if isinstance(value, float):
		return Decimal(str(value))
	if isinstance(value, str):
		return Decimal(value)
	return Decimal("0")


def _format_currency(value: Decimal) -> str:
	formatted = f"{value.quantize(Decimal('0.01')):,.2f}"
	return f"R$ {formatted.replace(',', '_').replace('.', ',').replace('_', '.')}"


def _load_allocation_df() -> pd.DataFrame:
	wealth_repo = get_wealth_repository()
	portfolio = wealth_repo.fetch_portfolio()
	if not portfolio:
		return pd.DataFrame(columns=["classe", "valor"])

	grouped: dict[str, Decimal] = {}
	for asset in portfolio:
		classe = str(asset.get("classe", "CAIXA"))
		quantidade = _to_decimal(asset.get("quantidade"))
		preco_medio = _to_decimal(asset.get("preco_medio"))
		valor = quantidade * preco_medio
		grouped[classe] = grouped.get(classe, Decimal("0")) + valor

	rows = [{"classe": classe, "valor": float(valor)} for classe, valor in grouped.items()]
	return pd.DataFrame(rows)


def _load_net_worth_evolution_df() -> pd.DataFrame:
	transacoes_repo = get_transacoes_repository()
	wealth_repo = get_wealth_repository()

	rows = transacoes_repo._connection.execute(  # noqa: SLF001
		"""
		WITH monthly AS (
			SELECT
				date_trunc('month', Data)::DATE AS data,
				SUM(CASE WHEN Tipo = 'RECEITA' THEN Valor ELSE 0 END)
				- SUM(CASE WHEN Tipo IN ('GASTO', 'INVESTIMENTO') THEN ABS(Valor) ELSE 0 END) AS variacao_caixa
			FROM BASE_GERAL
			GROUP BY 1
		)
		SELECT data, SUM(variacao_caixa) OVER (ORDER BY data) AS caixa_acumulado
		FROM monthly
		ORDER BY data
		"""
	).fetchall()

	invested = wealth_repo._connection.execute(  # noqa: SLF001
		"""
		SELECT COALESCE(SUM(quantidade * cotacao_atual), 0)
		FROM FACT_POSITIONS
		"""
	).fetchone()
	invested_total = _to_decimal(invested[0] if invested else 0)

	if not rows:
		return pd.DataFrame(
			[
				{
					"data": date.today(),
					"patrimonio_total": float(invested_total),
				}
			],
		)

	data = [
		{
			"data": row[0],
			"patrimonio_total": float(_to_decimal(row[1]) + invested_total),
		}
		for row in rows
	]
	return pd.DataFrame(data)


def _compute_emergency_months() -> tuple[Decimal, Decimal, Decimal]:
	transacoes_repo = get_transacoes_repository()
	wealth_service = get_wealth_intelligence_service()

	net_worth = wealth_service.get_consolidated_net_worth()
	caixa_total = _to_decimal(net_worth.get("caixa_total", Decimal("0")))

	avg_row = transacoes_repo._connection.execute(  # noqa: SLF001
		"""
		WITH monthly_spending AS (
			SELECT
				date_trunc('month', Data)::DATE AS month_ref,
				SUM(ABS(Valor)) AS total_gasto
			FROM BASE_GERAL
			WHERE Tipo = 'GASTO'
			GROUP BY 1
			ORDER BY month_ref DESC
			LIMIT 6
		)
		SELECT COALESCE(AVG(total_gasto), 0)
		FROM monthly_spending
		"""
	).fetchone()

	gasto_medio = _to_decimal(avg_row[0] if avg_row else 0)
	if gasto_medio <= 0:
		months = Decimal("0")
	else:
		months = caixa_total / gasto_medio
	return caixa_total, gasto_medio, months


def main() -> None:
	configure_page(title="Home", icon=":material/home:")
	initialize_session_state()
	set_active_tab("home")
	render_sidebar(active_tab="home")

	wealth_service = get_wealth_intelligence_service()
	consolidated = wealth_service.get_consolidated_net_worth()
	patrimonio_total = _to_decimal(consolidated.get("patrimonio_total", Decimal("0")))
	patrimonio_investido = _to_decimal(consolidated.get("patrimonio_investido", Decimal("0")))
	caixa_total = _to_decimal(consolidated.get("caixa_total", Decimal("0")))

	st.markdown("## Visao Geral Patrimonial")
	col_head_1, col_head_2, col_head_3 = st.columns((2.2, 1.2, 1.2))
	with col_head_1:
		draw_metric_card("Patrimonio Total", _format_currency(patrimonio_total), None, None)
	with col_head_2:
		draw_metric_card("Investido", _format_currency(patrimonio_investido), None, True)
	with col_head_3:
		draw_metric_card("Caixa", _format_currency(caixa_total), None, None)

	allocation_df = _load_allocation_df()
	evolution_df = _load_net_worth_evolution_df()

	col_chart_1, col_chart_2 = st.columns((1.55, 1.0))
	with col_chart_1:
		st.markdown("### Evolucao Patrimonial")
		draw_net_worth_evolution(evolution_df)
	with col_chart_2:
		st.markdown("### Asset Allocation")
		draw_allocation_donut(allocation_df)

	reserva_caixa, gasto_medio, meses_reserva = _compute_emergency_months()
	st.markdown("### Reserva de Emergencia")
	status_positive = meses_reserva >= Decimal("6")
	draw_metric_card(
		title="Meses de Sobrevivencia",
		value=f"{meses_reserva.quantize(Decimal('0.1'))} meses",
		delta=f"Caixa: {_format_currency(reserva_caixa)} | Gasto medio: {_format_currency(gasto_medio)}",
		is_positive=status_positive,
	)


if __name__ == "__main__":
	main()
