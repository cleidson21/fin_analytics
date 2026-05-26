"""Administrative command center for categories, goals, and quarantine review."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import streamlit as st

try:
	from app.core.shell import configure_page, render_sidebar
	from app.core.state import initialize_session_state, pop_flash_message, set_active_tab, set_flash_message
	from app.dependencies import get_analytics_repository, get_wealth_repository
except ModuleNotFoundError:
	from core.shell import configure_page, render_sidebar
	from core.state import initialize_session_state, pop_flash_message, set_active_tab, set_flash_message
	from dependencies import get_analytics_repository, get_wealth_repository

from models.wealth_schemas import CategoriaDimDTO, FinancialGoalDTO


def _to_decimal(value: object) -> Decimal:
	if isinstance(value, Decimal):
		return value
	if isinstance(value, int):
		return Decimal(value)
	if isinstance(value, float):
		return Decimal(str(value))
	if isinstance(value, str):
		try:
			return Decimal(value)
		except Exception:
			return Decimal("0")
	return Decimal("0")


def _to_date(value: object) -> date:
	if isinstance(value, date):
		return value
	if isinstance(value, str) and value.strip():
		return date.fromisoformat(value[:10])
	return date.today() + timedelta(days=90)


def _invalidate_cached_services() -> None:
	for key in (
		"fin_analytics_ingestion_service",
		"fin_analytics_wealth_intelligence_service",
		"fin_analytics_goals_service",
	):
		st.session_state.pop(key, None)


def _load_categories_df() -> pd.DataFrame:
	repository = get_wealth_repository()
	rows = repository.fetch_categories()
	if not rows:
		return pd.DataFrame(
			columns=["id", "macro_categoria", "subcategoria", "tipo_financeiro", "essencialidade", "cor_dashboard", "icone", "budget_default"],
		)

	return pd.DataFrame(
		[
			{
				"id": row.id,
				"macro_categoria": row.macro_categoria,
				"subcategoria": row.subcategoria,
				"tipo_financeiro": row.tipo_financeiro,
				"essencialidade": row.essencialidade,
				"cor_dashboard": row.cor_dashboard,
				"icone": row.icone,
				"budget_default": float(_to_decimal(row.budget_default)),
			}
			for row in rows
		]
	)


def _save_categories(edited_df: pd.DataFrame) -> int:
	if edited_df.empty:
		return 0

	repository = get_wealth_repository()
	updated_count = 0
	for row in edited_df.to_dict("records"):
		macro_categoria = str(row.get("macro_categoria", "")).strip()
		subcategoria = str(row.get("subcategoria", "")).strip()
		if not macro_categoria or not subcategoria:
			continue

		payload = {
			"id": str(row.get("id") or "").strip() or None,
			"macro_categoria": macro_categoria,
			"subcategoria": subcategoria,
			"tipo_financeiro": str(row.get("tipo_financeiro", "VARIAVEL")).strip() or "VARIAVEL",
			"essencialidade": str(row.get("essencialidade", "DISCRICIONARIO")).strip() or "DISCRICIONARIO",
			"cor_dashboard": str(row.get("cor_dashboard", "#6C7A89")).strip() or "#6C7A89",
			"icone": str(row.get("icone", "circle")).strip() or "circle",
			"budget_default": _to_decimal(row.get("budget_default", 0)),
		}
		repository.upsert_category(CategoriaDimDTO.model_validate(payload))
		updated_count += 1

	return updated_count


def _load_goals_df() -> pd.DataFrame:
	repository = get_wealth_repository()
	rows = repository.fetch_goals()
	if not rows:
		return pd.DataFrame(
			columns=[
				"goal_id",
				"nome",
				"tipo",
				"valor_meta",
				"valor_atual",
				"data_limite",
				"prioridade",
				"categoria_relacionada",
				"aporte_mensal_planejado",
				"status",
			],
		)

	return pd.DataFrame(
		[
			{
				"goal_id": row.get("goal_id") or row.get("id_meta") or "",
				"nome": row.get("nome", ""),
				"tipo": row.get("tipo", "OUTRA"),
				"valor_meta": float(_to_decimal(row.get("valor_meta", row.get("valor_alvo", 0)))),
				"valor_atual": float(_to_decimal(row.get("valor_atual", 0))),
				"data_limite": row.get("data_limite") or (date.today() + timedelta(days=90)),
				"prioridade": int(row.get("prioridade") or 1),
				"categoria_relacionada": row.get("categoria_relacionada") or "",
				"aporte_mensal_planejado": float(_to_decimal(row.get("aporte_mensal_planejado", row.get("aporte_mensal_sugerido", 0)))),
				"status": row.get("status", "ATIVA"),
			}
			for row in rows
		]
	)


def _save_goals(edited_df: pd.DataFrame) -> int:
	if edited_df.empty:
		return 0

	repository = get_wealth_repository()
	updated_count = 0
	for row in edited_df.to_dict("records"):
		nome = str(row.get("nome", "")).strip()
		if not nome:
			continue

		payload = {
			"goal_id": str(row.get("goal_id") or "").strip() or None,
			"nome": nome,
			"tipo": str(row.get("tipo", "OUTRA")).strip() or "OUTRA",
			"valor_meta": _to_decimal(row.get("valor_meta", 0)),
			"valor_atual": _to_decimal(row.get("valor_atual", 0)),
			"data_limite": _to_date(row.get("data_limite")),
			"prioridade": int(row.get("prioridade") or 1),
			"categoria_relacionada": str(row.get("categoria_relacionada", "")).strip() or None,
			"aporte_mensal_planejado": _to_decimal(row.get("aporte_mensal_planejado", 0)),
			"status": str(row.get("status", "ATIVA")).strip() or "ATIVA",
		}
		repository.upsert_goal(FinancialGoalDTO.model_validate(payload))
		updated_count += 1

	return updated_count


def _load_quarantine_df(limit: int = 200) -> pd.DataFrame:
	rows = get_analytics_repository().get_quarantine_rows(limit=limit)

	if not rows:
		return pd.DataFrame(
			columns=[
				"ID_Unico",
				"Data",
				"Descricao",
				"Valor",
				"Tipo",
				"Categoria",
				"ArquivoOrigem",
				"Fonte",
				"processed_at",
				"motivo_rejeicao",
				"Subcategoria Corrigida",
			],
		)

	return pd.DataFrame(
		[
			{
				"ID_Unico": row.get("ID_Unico"),
				"Data": row.get("Data"),
				"Descricao": row.get("Descricao"),
				"Valor": float(_to_decimal(row.get("Valor"))),
				"Tipo": row.get("Tipo"),
				"Categoria": row.get("Categoria"),
				"ArquivoOrigem": row.get("ArquivoOrigem"),
				"Fonte": row.get("Fonte"),
				"processed_at": row.get("processed_at"),
				"motivo_rejeicao": row.get("motivo_rejeicao"),
				"Subcategoria Corrigida": "",
			}
			for row in rows
		]
	)


def _render_categories_tab() -> None:
	st.markdown("### Gerenciar Categorias")
	st.caption("Edite a taxonomia financeira e persista a dimensao de categorias diretamente no DuckDB.")

	categories_df = _load_categories_df()
	edited_df = st.data_editor(
		categories_df,
		use_container_width=True,
		num_rows="dynamic",
		disabled=["id"],
		column_config={
			"id": st.column_config.TextColumn("ID", disabled=True),
			"macro_categoria": st.column_config.TextColumn("Macro Categoria"),
			"subcategoria": st.column_config.TextColumn("Subcategoria"),
			"tipo_financeiro": st.column_config.TextColumn("Tipo Financeiro"),
			"essencialidade": st.column_config.TextColumn("Essencialidade"),
			"cor_dashboard": st.column_config.TextColumn("Cor Dashboard"),
			"icone": st.column_config.TextColumn("Icone"),
			"budget_default": st.column_config.NumberColumn("Budget Default", min_value=0.0, step=50.0, format="%.2f"),
		},
		key="admin_categories_editor",
	)

	if st.button("Salvar Categorias", type="primary"):
		try:
			count = _save_categories(edited_df)
		except Exception as exc:
			set_flash_message(f"Falha ao salvar categorias: {exc}")
		else:
			_invalidate_cached_services()
			set_flash_message(f"{count} categorias atualizadas.")
		st.rerun()


def _render_goals_tab() -> None:
	st.markdown("### Metas Financeiras")
	st.caption("Crie e ajuste metas sem sair da interface. O salvamento atualiza o repositório imediatamente.")

	goals_df = _load_goals_df()
	edited_df = st.data_editor(
		goals_df,
		use_container_width=True,
		num_rows="dynamic",
		disabled=["goal_id"],
		column_config={
			"goal_id": st.column_config.TextColumn("Goal ID", disabled=True),
			"nome": st.column_config.TextColumn("Nome"),
			"tipo": st.column_config.SelectboxColumn("Tipo", options=["RESERVA_EMERGENCIA", "VIAGEM", "MOTO", "PC_GAMER", "APOSENTADORIA", "ENTRADA_IMOVEL", "OUTRA"]),
			"valor_meta": st.column_config.NumberColumn("Valor Meta", min_value=0.0, step=100.0, format="%.2f"),
			"valor_atual": st.column_config.NumberColumn("Valor Atual", min_value=0.0, step=50.0, format="%.2f"),
			"data_limite": st.column_config.DateColumn("Data Limite"),
			"prioridade": st.column_config.NumberColumn("Prioridade", min_value=1, step=1),
			"categoria_relacionada": st.column_config.TextColumn("Categoria Relacionada"),
			"aporte_mensal_planejado": st.column_config.NumberColumn("Aporte Mensal Planejado", min_value=0.0, step=50.0, format="%.2f"),
			"status": st.column_config.SelectboxColumn("Status", options=["ATIVA", "CONCLUIDA", "PAUSADA"]),
		},
		key="admin_goals_editor",
	)

	if st.button("Salvar Metas", type="primary"):
		try:
			count = _save_goals(edited_df)
		except Exception as exc:
			set_flash_message(f"Falha ao salvar metas: {exc}")
		else:
			_invalidate_cached_services()
			set_flash_message(f"{count} metas atualizadas.")
		st.rerun()


def _render_quarantine_tab() -> None:
	st.markdown("### Quarentena")
	st.caption("Classificacoes pendentes para correcao manual. Selecione a subcategoria correta e promova o registro.")

	quarantine_df = _load_quarantine_df()
	categories = get_wealth_repository().fetch_categories()
	subcategory_options = ["", *[category.subcategoria for category in categories]]

	if quarantine_df.empty:
		st.info("Nenhum item em quarentena no momento.")
		return

	edited_df = st.data_editor(
		quarantine_df,
		use_container_width=True,
		num_rows="fixed",
		disabled=["ID_Unico", "Data", "Descricao", "Valor", "Tipo", "Categoria", "ArquivoOrigem", "Fonte", "processed_at", "motivo_rejeicao"],
		column_config={
			"ID_Unico": st.column_config.TextColumn("ID", disabled=True),
			"Data": st.column_config.DateColumn("Data", disabled=True),
			"Descricao": st.column_config.TextColumn("Descricao", disabled=True),
			"Valor": st.column_config.NumberColumn("Valor", format="%.2f", disabled=True),
			"Tipo": st.column_config.TextColumn("Tipo", disabled=True),
			"Categoria": st.column_config.TextColumn("Categoria", disabled=True),
			"ArquivoOrigem": st.column_config.TextColumn("Arquivo Origem", disabled=True),
			"Fonte": st.column_config.TextColumn("Fonte", disabled=True),
			"processed_at": st.column_config.TextColumn("Processado Em", disabled=True),
			"motivo_rejeicao": st.column_config.TextColumn("Motivo", disabled=True),
			"Subcategoria Corrigida": st.column_config.SelectboxColumn("Subcategoria Corrigida", options=subcategory_options),
		},
		key="admin_quarantine_editor",
	)

	if st.button("Salvar Correcoes", type="primary"):
		promoted = 0
		try:
			for row in edited_df.to_dict("records"):
				subcategoria = str(row.get("Subcategoria Corrigida", "")).strip().upper()
				if not subcategoria:
					continue
				match = next((category for category in categories if category.subcategoria == subcategoria), None)
				if match is None:
					continue
				get_analytics_repository().promote_quarantine_record(
					transaction_id=str(row["ID_Unico"]),
					categoria=match.subcategoria,
				)
				promoted += 1
		except Exception as exc:
			set_flash_message(f"Falha ao corrigir quarentena: {exc}")
		else:
			_invalidate_cached_services()
			set_flash_message(f"{promoted} transacoes promovidas da quarentena.")
		st.rerun()


def main() -> None:
	configure_page(title="Admin", icon=":material/settings:")
	initialize_session_state()
	set_active_tab("admin")
	render_sidebar(active_tab="admin")

	st.markdown("## Command Center")
	st.caption("Controle a taxonomia, as metas e a quarentena sem tocar no código.")

	message = pop_flash_message()
	if message:
		if message.startswith("Falha"):
			st.error(message)
		else:
			st.success(message)

	tab_categories, tab_goals, tab_quarantine = st.tabs(["Gerenciar Categorias", "Metas Financeiras", "Quarentena"])
	with tab_categories:
		_render_categories_tab()
	with tab_goals:
		_render_goals_tab()
	with tab_quarantine:
		_render_quarantine_tab()


if __name__ == "__main__":
	main()