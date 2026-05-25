"""Operational home page for consolidated wealth monitoring."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

try:
	from app.components.cards import draw_metric_card
	from app.components.charts import draw_goals_progress, draw_sankey_cashflow
	from app.core.shell import configure_page, render_sidebar
	from app.core.state import get_wealth_intelligence_service, initialize_session_state, set_active_tab
	from app.dependencies import get_transacoes_repository, get_wealth_repository
except ModuleNotFoundError:
	from components.cards import draw_metric_card
	from components.charts import draw_goals_progress, draw_sankey_cashflow
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


def _current_month_bounds(reference: date | None = None) -> tuple[date, date]:
	reference_date = reference or date.today()
	start = reference_date.replace(day=1)
	if reference_date.month == 12:
		end = reference_date.replace(year=reference_date.year + 1, month=1, day=1)
	else:
		end = reference_date.replace(month=reference_date.month + 1, day=1)
	return start, end


def _load_current_month_cashflow() -> dict[str, Decimal]:
	transacoes_repo = get_transacoes_repository()
	start_date, end_date = _current_month_bounds()

	row = transacoes_repo._connection.execute(  # noqa: SLF001
		"""
		WITH month_base AS (
			SELECT
				b.Tipo,
				b.Valor,
				b.Categoria,
				COALESCE(c.macro_categoria, '') AS macro_categoria,
				COALESCE(c.essencialidade, 'DISCRICIONARIO') AS essencialidade
			FROM BASE_GERAL b
			LEFT JOIN DIM_CATEGORIAS c
				ON UPPER(b.Categoria) = UPPER(c.subcategoria)
			WHERE b.Data BETWEEN ? AND ?
		)
		SELECT
			COALESCE(SUM(CASE WHEN Tipo = 'RECEITA' THEN Valor ELSE 0 END), 0) AS receitas,
			COALESCE(SUM(CASE WHEN Tipo = 'INVESTIMENTO' OR macro_categoria = 'INVESTIMENTOS' OR UPPER(Categoria) = 'APORTE' THEN ABS(Valor) ELSE 0 END), 0) AS investimentos,
			COALESCE(SUM(CASE WHEN essencialidade = 'ESSENCIAL' AND Tipo <> 'RECEITA' THEN ABS(Valor) ELSE 0 END), 0) AS gastos_essenciais,
			COALESCE(SUM(CASE WHEN essencialidade = 'DISCRICIONARIO' AND Tipo <> 'RECEITA' THEN ABS(Valor) ELSE 0 END), 0) AS gastos_discricionarios
		FROM month_base
		""",
		[start_date, end_date],
	).fetchone()

	return {
		"receitas": _to_decimal(row[0] if row else 0),
		"investimentos": _to_decimal(row[1] if row else 0),
		"gastos_essenciais": _to_decimal(row[2] if row else 0),
		"gastos_discricionarios": _to_decimal(row[3] if row else 0),
	}


def _compute_financial_health(cashflow: dict[str, Decimal], patrimonio_total: Decimal) -> dict[str, Decimal]:
	receitas = cashflow["receitas"]
	investimentos = cashflow["investimentos"]
	gastos_essenciais = cashflow["gastos_essenciais"]
	gastos_discricionarios = cashflow["gastos_discricionarios"]
	savings = receitas - investimentos - gastos_essenciais - gastos_discricionarios
	savings_rate = (savings / receitas * Decimal("100")) if receitas > 0 else Decimal("0")
	essential_ratio = (gastos_essenciais / receitas * Decimal("100")) if receitas > 0 else Decimal("0")
	discretionary_ratio = (gastos_discricionarios / receitas * Decimal("100")) if receitas > 0 else Decimal("0")
	return {
		"savings": savings,
		"savings_rate": savings_rate,
		"essential_ratio": essential_ratio,
		"discretionary_ratio": discretionary_ratio,
		"patrimonio_total": patrimonio_total,
	}


def _load_goal_rows() -> list[dict[str, object]]:
	wealth_repo = get_wealth_repository()
	return wealth_repo.fetch_goals()


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

	cashflow = _load_current_month_cashflow()
	health = _compute_financial_health(cashflow, patrimonio_total)
	goals = _load_goal_rows()

	st.markdown("## Wealth Operating System")
	st.caption("Patrimonio, fluxo de caixa, metas e disciplina financeira em uma interface unica.")

	st.markdown(
		f"<div style='font-size:0.82rem; letter-spacing:0.08em; text-transform:uppercase; color:#9FB0D0;'>Patrimonio Liquido</div>"
		f"<div style='font-size:3rem; font-weight:800; line-height:1.05; color:#F5F8FF; margin-top:0.2rem;'>{_format_currency(patrimonio_total)}</div>",
		unsafe_allow_html=True,
	)

	col_1, col_2, col_3 = st.columns(3)
	with col_1:
		draw_metric_card("Patrimonio Investido", _format_currency(patrimonio_investido), None, True)
	with col_2:
		draw_metric_card("Caixa Disponivel", _format_currency(caixa_total), None, None)
	with col_3:
		draw_metric_card("Savings Rate", f"{health['savings_rate'].quantize(Decimal('0.1'))}%", _format_currency(health["savings"]), health["savings"] >= 0)

	st.markdown("### Fluxo de Caixa do Mes")
	draw_sankey_cashflow(
		cashflow["receitas"],
		cashflow["investimentos"],
		cashflow["gastos_essenciais"],
		cashflow["gastos_discricionarios"],
	)

	health_col_1, health_col_2 = st.columns(2)
	with health_col_1:
		draw_metric_card(
			"Custo de Vida Essencial",
			f"{health['essential_ratio'].quantize(Decimal('0.1'))}%",
			_format_currency(cashflow["gastos_essenciais"]),
			False,
		)
	with health_col_2:
		draw_metric_card(
			"Custo Discricionario",
			f"{health['discretionary_ratio'].quantize(Decimal('0.1'))}%",
			_format_currency(cashflow["gastos_discricionarios"]),
			False,
		)

	st.markdown("### Metas Financeiras")
	draw_goals_progress(goals)


if __name__ == "__main__":
	main()