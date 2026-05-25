"""Portfolio holdings page powered by AgGrid."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

try:
	from app.core.shell import configure_page, render_sidebar
	from app.core.state import (
		get_wealth_intelligence_service,
		initialize_session_state,
		pop_flash_message,
		set_active_tab,
		set_flash_message,
	)
	from app.dependencies import get_wealth_repository
except ModuleNotFoundError:
	from core.shell import configure_page, render_sidebar
	from core.state import (
		get_wealth_intelligence_service,
		initialize_session_state,
		pop_flash_message,
		set_active_tab,
		set_flash_message,
	)
	from dependencies import get_wealth_repository


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


def _build_positions_df() -> pd.DataFrame:
	wealth_repo = get_wealth_repository()
	rows = wealth_repo._connection.execute(  # noqa: SLF001
		"""
		SELECT
			p.ticker,
			p.quantidade,
			p.preco_medio,
			p.cotacao_atual,
			p.pnl_absoluto,
			p.pnl_percentual,
			p.dividend_yield
		FROM FACT_POSITIONS p
		ORDER BY p.ticker
		"""
	).fetchall()

	if not rows:
		return pd.DataFrame(columns=["Ticker", "Qtde", "Preco Medio", "Cotacao", "PnL", "PnL %", "Yield %"])

	data = []
	for row in rows:
		data.append(
			{
				"Ticker": row[0],
				"Qtde": float(_to_decimal(row[1])),
				"Preco Medio": float(_to_decimal(row[2])),
				"Cotacao": float(_to_decimal(row[3])),
				"PnL": float(_to_decimal(row[4])),
				"PnL %": float(_to_decimal(row[5])),
				"Yield %": float(_to_decimal(row[6])),
			}
		)
	return pd.DataFrame(data)


def _render_aggrid(df: pd.DataFrame) -> None:
	if df.empty:
		st.info("Nenhuma posicao cadastrada para exibir.")
		return

	grid_builder = GridOptionsBuilder.from_dataframe(df)
	grid_builder.configure_default_column(
		filter=True,
		sortable=True,
		resizable=True,
		enablePivot=True,
		enableValue=True,
	)
	grid_builder.configure_column("Ticker", pinned="left")
	for col_name in ("Qtde", "Preco Medio", "Cotacao", "PnL", "PnL %", "Yield %"):
		grid_builder.configure_column(col_name, type=["numericColumn", "numberColumnFilter", "customNumericFormat"])

	grid_options = grid_builder.build()
	AgGrid(
		df,
		gridOptions=grid_options,
		height=520,
		fit_columns_on_grid_load=False,
		allow_unsafe_jscode=False,
		enable_enterprise_modules=False,
	)


def main() -> None:
	configure_page(title="Investimentos", icon=":material/trending_up:")
	initialize_session_state()
	set_active_tab("investimentos")
	render_sidebar(active_tab="investimentos")

	st.markdown("## Portfolio Holdings")
	st.caption("Grade profissional com filtros e ordenacao para monitorar posicoes em tempo real.")

	left_col, right_col = st.columns((1.2, 3.8))
	with left_col:
		if st.button("Sincronizar Cotacoes", type="primary", use_container_width=True):
			service = get_wealth_intelligence_service()
			try:
				quotes = service.sync_portfolio_prices()
			except Exception as exc:
				set_flash_message(f"Falha na sincronizacao: {exc}")
			else:
				set_flash_message(f"Sincronizacao concluida para {len(quotes)} ativos.")
			st.rerun()

	message = pop_flash_message()
	if message:
		if message.startswith("Falha"):
			st.error(message)
		else:
			st.success(message)

	positions_df = _build_positions_df()
	_render_aggrid(positions_df)


if __name__ == "__main__":
	main()
