"""Goals and budgets operational page with direct user interaction."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

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
from models.wealth_dto import GoalDTO


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


def _load_budget_editor_df() -> pd.DataFrame:
	service = get_wealth_intelligence_service()
	budgets = service.get_budgets_intelligence(reference_date=date.today())
	if not budgets:
		return pd.DataFrame(columns=["Categoria", "Teto Mensal", "Valor Utilizado", "% Uso", "Status"])

	return pd.DataFrame(
		[
			{
				"Categoria": b.categoria,
				"Teto Mensal": float(_to_decimal(b.teto_mensal)),
				"Valor Utilizado": float(_to_decimal(b.valor_utilizado)),
				"% Uso": float(_to_decimal(b.percentual_uso)),
				"Status": b.status_alerta,
			}
			for b in budgets
		]
	)


def _save_budget_limits(edited_df: pd.DataFrame) -> int:
	if edited_df.empty:
		return 0

	wealth_repo = get_wealth_repository()
	updated_count = 0
	for row in edited_df.to_dict("records"):
		categoria = str(row.get("Categoria", "")).strip().upper()
		if not categoria:
			continue
		teto = _to_decimal(row.get("Teto Mensal", 0))
		wealth_repo._connection.execute(  # noqa: SLF001
			"""
			DELETE FROM BUDGETS
			WHERE categoria = ?
			""",
			[categoria],
		)
		wealth_repo._connection.execute(  # noqa: SLF001
			"""
			INSERT INTO BUDGETS (categoria, teto_mensal, valor_utilizado, percentual_uso, status_alerta, updated_at)
			VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
			""",
			[categoria, teto, Decimal("0"), Decimal("0"), "OK"],
		)
		updated_count += 1

	return updated_count


def _render_new_goal_form() -> None:
	with st.expander("Adicionar Nova Meta Financeira", expanded=False):
		with st.form("nova_meta_financeira_form", clear_on_submit=True):
			col_1, col_2 = st.columns(2)
			with col_1:
				nome = st.text_input("Nome da meta")
				valor_alvo = st.number_input("Valor alvo", min_value=0.01, step=100.0, format="%.2f")
			with col_2:
				valor_atual = st.number_input("Valor atual", min_value=0.0, step=50.0, format="%.2f")
				prazo_meses = st.number_input("Prazo (meses)", min_value=1, step=1, value=12)
			prioridade = st.select_slider("Prioridade", options=[1, 2, 3, 4, 5], value=3)
			submitted = st.form_submit_button("Salvar Meta", type="primary")

			if submitted:
				if not nome.strip():
					set_flash_message("Falha: informe um nome valido para a meta.")
					st.rerun()

				service = get_wealth_intelligence_service()
				try:
					goal = GoalDTO.model_validate(
						{
							"nome": nome.strip(),
							"valor_alvo": Decimal(str(valor_alvo)),
							"valor_atual": Decimal(str(valor_atual)),
							"prazo_meses": int(prazo_meses),
							"prioridade": int(prioridade),
						}
					)
					service._wealth_repository.upsert_goal(goal)  # noqa: SLF001
				except Exception as exc:
					set_flash_message(f"Falha ao salvar meta: {exc}")
				else:
					set_flash_message("Meta adicionada com sucesso.")
				st.rerun()


def _render_active_goals() -> None:
	service = get_wealth_intelligence_service()
	goals = service.get_goals_intelligence()

	st.markdown("### Metas Ativas")
	if not goals:
		st.info("Nenhuma meta ativa no momento.")
		return

	for goal in goals:
		percent = int(min(max(goal.percentual_conclusao, Decimal("0")), Decimal("100")))
		faltam = max(goal.valor_alvo - goal.valor_atual, Decimal("0"))
		forecast = date.today().replace(day=1)
		months = max(goal.prazo_meses, 1)
		year = forecast.year + ((forecast.month - 1 + months) // 12)
		month = ((forecast.month - 1 + months) % 12) + 1
		previsao = date(year=year, month=month, day=1).strftime("%b/%Y")

		st.markdown(f"**{goal.nome}**")
		st.progress(percent)
		st.caption(
			f"Faltam {_format_currency(faltam)} para {goal.nome} - Previsto: {previsao} | "
			f"Aporte sugerido: {_format_currency(goal.aporte_mensal_sugerido)}"
		)


def main() -> None:
	configure_page(title="Metas e Orcamentos", icon=":material/target:")
	initialize_session_state()
	set_active_tab("metas_orcamentos")
	render_sidebar(active_tab="metas_orcamentos")

	st.markdown("## Metas e Orcamentos")
	st.caption("Edite limites de gastos diretamente na tabela e acompanhe metas em tempo real.")

	message = pop_flash_message()
	if message:
		if message.startswith("Falha"):
			st.error(message)
		else:
			st.success(message)

	budget_df = _load_budget_editor_df()
	st.markdown("### Orcamentos por Categoria")
	edited = st.data_editor(
		budget_df,
		use_container_width=True,
		num_rows="dynamic",
		disabled=["Valor Utilizado", "% Uso", "Status"],
		column_config={
			"Categoria": st.column_config.TextColumn(required=True),
			"Teto Mensal": st.column_config.NumberColumn(min_value=0.0, step=50.0, format="%.2f"),
			"Valor Utilizado": st.column_config.NumberColumn(format="%.2f"),
			"% Uso": st.column_config.NumberColumn(format="%.2f"),
			"Status": st.column_config.TextColumn(),
		},
		key="budget_data_editor",
	)

	if st.button("Salvar Alteracoes de Orcamento", type="primary"):
		try:
			count = _save_budget_limits(edited)
		except Exception as exc:
			set_flash_message(f"Falha ao salvar orcamentos: {exc}")
		else:
			set_flash_message(f"{count} categorias de orcamento atualizadas.")
		st.rerun()

	_render_new_goal_form()
	_render_active_goals()


if __name__ == "__main__":
	main()
