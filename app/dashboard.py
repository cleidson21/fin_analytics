"""Streamlit dashboard for FinAnalytics with premium visual treatment and interactive services."""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from app.dependencies import (  # noqa: E402
	get_finance_service,
	get_goals_service,
	get_ingestion_service,
	get_transacoes_repository,
	get_wealth_repository,
)
from config.constants import FonteDados, StatusProcessamento
from repositories.wealth_repository import WealthRepository
from services.portfolio_service import PortfolioService
from utils.formatters import format_currency_br, format_percentage, inject_premium_css


@st.cache_resource(show_spinner=False)
def get_portfolio_service() -> PortfolioService:
	"""Return a cached portfolio service backed by the shared wealth repository."""

	return PortfolioService(get_wealth_repository())


@st.cache_data(ttl=300, show_spinner=False)
def load_daily_cashflow_series(start_date: date, end_date: date) -> list[dict[str, Any]]:
	"""Load the daily net cashflow series for the selected period."""

	relation = get_transacoes_repository().fetch_transactions_by_period(start_date, end_date)
	series = relation.query(
		"period",
		"""
		SELECT
			Data,
			SUM(CASE WHEN Tipo = 'RECEITA' THEN Valor ELSE -ABS(Valor) END) AS saldo_liquido
		FROM period
		GROUP BY 1
		ORDER BY 1
		""",
	)
	return [dict(zip(series.columns, row, strict=True)) for row in series.fetchall()]


@st.cache_data(ttl=300, show_spinner=False)
def load_monthly_dividends() -> list[dict[str, Any]]:
	"""Load monthly dividend totals from the wealth layer."""

	repository = get_wealth_repository()
	repository.init_wealth_tables()
	rows = repository._connection.execute(  # noqa: SLF001
		"""
		SELECT
			strftime(data_pagamento, '%Y-%m') AS mes,
			SUM(valor_recebido) AS valor_recebido
		FROM FACT_DIVIDENDS
		GROUP BY 1
		ORDER BY 1
		""",
	).fetchall()
	return [{"mes": row[0], "valor_recebido": Decimal(str(row[1] or 0))} for row in rows]


@st.cache_data(ttl=300, show_spinner=False)
def load_quarantine_transactions(limit: int = 200) -> list[dict[str, Any]]:
	"""Load quarantined transactions for diagnostic review."""

	relation = get_transacoes_repository().fetch_quarantine_transactions()
	frame = relation.limit(limit).df()
	rows: list[dict[str, Any]] = []
	for record in frame.to_dict(orient="records"):
		rows.append(
			{
				"ID_Unico": record.get("ID_Unico"),
				"Data": record.get("Data"),
				"Descricao": record.get("Descricao"),
				"Valor": record.get("Valor"),
				"Tipo": record.get("Tipo"),
				"Categoria": record.get("Categoria"),
				"ArquivoOrigem": record.get("ArquivoOrigem"),
				"Fonte": record.get("Fonte"),
				"processed_at": record.get("processed_at"),
				"motivo_rejeicao": record.get("motivo_rejeicao"),
			}
		)
	return rows


@st.cache_data(ttl=300, show_spinner=False)
def load_portfolio_summary() -> dict[str, Any]:
	"""Load the portfolio summary and keep market prices in sync."""

	service = get_portfolio_service()
	service.sync_market_prices()
	return service.get_portfolio_summary()


@st.cache_data(ttl=300, show_spinner=False)
def load_dividend_yield() -> dict[str, Any]:
	"""Load the dividend yield summary for the portfolio tab."""

	service = get_portfolio_service()
	service.sync_market_prices()
	return service.get_dividend_yield()


@st.cache_data(ttl=300, show_spinner=False)
def load_system_health() -> dict[str, Any]:
	"""Collect light-weight health indicators from the transaction repository."""

	repository = get_transacoes_repository()
	executions = repository._connection.execute("SELECT COUNT(*) FROM ETL_EXECUTIONS").fetchone()[0]  # noqa: SLF001
	quarantine_rows = repository._connection.execute("SELECT COUNT(*) FROM QUARANTINE_TRANSACTIONS").fetchone()[0]  # noqa: SLF001
	processed_files = repository._connection.execute(  # noqa: SLF001
		"""
		SELECT COUNT(DISTINCT source_file)
		FROM ETL_EXECUTIONS
		WHERE status = ?
		""",
		[StatusProcessamento.SUCESSO.value],
	).fetchone()[0]
	latest_execution = repository._connection.execute(  # noqa: SLF001
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


@st.cache_data(ttl=300, show_spinner=False)
def load_goal_progress() -> list[dict[str, Any]]:
	"""Load financial goals with calculated progress metrics."""

	return get_goals_service().get_goals_progress()


@st.cache_data(ttl=300, show_spinner=False)
def load_cashflow_summary(start_date: date, end_date: date):
	"""Load the cashflow summary for the selected period."""

	return get_finance_service().get_cashflow_summary(start_date, end_date)


@st.cache_data(ttl=300, show_spinner=False)
def load_savings_metrics(start_date: date, end_date: date):
	"""Load the savings metrics for the selected period."""

	return get_finance_service().get_savings_metrics(start_date, end_date)


@st.cache_data(ttl=300, show_spinner=False)
def load_investment_summary(start_date: date, end_date: date):
	"""Load the investment summary for the selected period."""

	return get_finance_service().get_investment_summary(start_date, end_date)


@st.cache_data(ttl=300, show_spinner=False)
def load_expenses_breakdown(start_date: date, end_date: date) -> list[dict[str, Any]]:
	"""Load the expense breakdown as serializable dictionaries."""

	return [item.model_dump() for item in get_finance_service().get_expenses_breakdown(start_date, end_date)]


@st.cache_data(ttl=300, show_spinner=False)
def load_recent_transactions(limit: int = 12) -> list[dict[str, Any]]:
	"""Load the latest curated transactions for the overview tab."""

	relation = get_transacoes_repository().fetch_latest_transactions(limit)
	rows: list[dict[str, Any]] = []
	for row in relation.fetchall():
		record = dict(zip(relation.columns, row, strict=True))
		record["Valor"] = format_currency_br(_to_decimal(record["Valor"]))
		processed_at = record.get("processed_at")
		if processed_at is not None:
			record["processed_at"] = processed_at.strftime("%Y-%m-%d %H:%M")
		rows.append(record)
	return rows


def _to_decimal(value: object) -> Decimal:
	"""Convert common numeric inputs to ``Decimal`` safely."""

	if isinstance(value, Decimal):
		return value
	if isinstance(value, int):
		return Decimal(value)
	if isinstance(value, str):
		return Decimal(value)
	if isinstance(value, float):
		return Decimal(str(value))
	return Decimal("0")


def _format_money(value: object) -> str:
	"""Format a numeric value as BRL."""

	return format_currency_br(_to_decimal(value))


def _format_pct(value: object) -> str:
	"""Format a numeric value as percentage."""

	return format_percentage(_to_decimal(value))


def _render_hero(title: str, subtitle: str, chips: Iterable[str]) -> None:
	"""Render the dashboard hero region."""

	chip_markup = "".join(f"<span class='fa-chip'>{chip}</span>" for chip in chips)
	st.markdown(
		f"""
		<div class="fa-hero">
			<div class="fa-kicker">Terminal de comando financeiro</div>
			<h1 class="fa-title">{title}</h1>
			<div class="fa-subtitle">{subtitle}</div>
			<div class="fa-chip-row">{chip_markup}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def _render_metric_cards(items: list[dict[str, str]]) -> None:
	"""Render a compact grid of KPI cards."""

	columns = st.columns(len(items))
	for column, item in zip(columns, items, strict=True):
		with column:
			st.markdown(
				f"""
				<div class="fa-card">
					<div class="fa-card-label">{item['label']}</div>
					<div class="fa-card-value">{item['value']}</div>
					<div class="fa-card-note">{item.get('note', '')}</div>
				</div>
				""",
				unsafe_allow_html=True,
			)


def _build_sidebar_controls() -> tuple[date, date]:
	"""Render the operational sidebar and handle file ingestion."""

	st.sidebar.markdown("## Painel de Controle")
	st.sidebar.caption("Controle de período, upload direto e diagnóstico operacional.")

	today = date.today()
	default_start = today.replace(day=1)
	st.sidebar.markdown("### Filtro de datas")
	start_date = st.sidebar.date_input("Início", value=default_start)
	end_date = st.sidebar.date_input("Fim", value=today)
	if start_date > end_date:
		st.sidebar.error("A data inicial não pode ser maior que a data final.")
		start_date, end_date = end_date, start_date

	st.sidebar.markdown("### Importação direta")
	fonte = st.sidebar.selectbox(
		"Fonte",
		options=(FonteDados.NUBANK, FonteDados.MYPROFIT),
		format_func=lambda item: "Nubank" if item == FonteDados.NUBANK else "MyProfit",
	)
	uploaded_file = st.sidebar.file_uploader(
		"Arraste um CSV aqui",
		type=["csv"],
		help="Envie um CSV da fonte selecionada para processar instantaneamente.",
	)
	if uploaded_file is not None:
		_process_uploaded_file(uploaded_file, fonte)

	st.sidebar.markdown("### Sinais do sistema")
	health = load_system_health()
	latest_execution = health.get("latest_execution")
	latest_status = latest_execution[0] if latest_execution else "Sem dados"
	latest_file = latest_execution[1] if latest_execution else "Sem arquivo"
	st.sidebar.metric("Execuções ETL", health.get("executions", 0))
	st.sidebar.metric("Arquivos processados", health.get("processed_files", 0))
	st.sidebar.metric("Quarentena", health.get("quarantine_rows", 0))
	st.sidebar.caption(f"Último status: {latest_status}")
	st.sidebar.caption(f"Último arquivo: {latest_file}")

	return start_date, end_date


def _process_uploaded_file(uploaded_file: Any, fonte: FonteDados) -> None:
	"""Process an uploaded file once per unique payload and show live feedback."""

	file_name = getattr(uploaded_file, "name", "arquivo.csv")
	file_bytes = uploaded_file.getvalue()
	if not file_bytes:
		st.sidebar.error("O arquivo enviado está vazio.")
		return

	processed_token = hashlib.sha256(
		file_name.encode("utf-8") + b"|" + fonte.value.encode("utf-8") + b"|" + file_bytes
	).hexdigest()
	last_token = st.session_state.get("fin_analytics_last_upload_token")
	if processed_token == last_token:
		return

	service = get_ingestion_service()
	try:
		result = service.process_uploaded_file(file_bytes=file_bytes, file_name=file_name, fonte=fonte)
	except Exception as exc:
		st.sidebar.error(f"Falha ao processar {file_name}: {exc}")
		st.sidebar.exception(exc)
		return

	st.session_state["fin_analytics_last_upload_token"] = processed_token
	st.session_state["fin_analytics_upload_flash"] = f"{result.rows_inserted} linhas inseridas com sucesso em {result.file_name}."
	st.cache_data.clear()
	st.rerun()


def _render_overview_tab(start_date: date, end_date: date) -> None:
	"""Render the executive overview tab."""

	cashflow = load_cashflow_summary(start_date, end_date)
	savings = load_savings_metrics(start_date, end_date)
	daily_series = load_daily_cashflow_series(start_date, end_date)
	portfolio_summary = load_portfolio_summary()
	expenses = load_expenses_breakdown(start_date, end_date)

	_render_metric_cards(
		[
			{
				"label": "Patrimônio",
				"value": _format_money(portfolio_summary.get("patrimonio_total")),
				"note": "Visão consolidada da carteira investida.",
			},
			{
				"label": "Receitas",
				"value": _format_money(cashflow.receitas),
				"note": f"Período {start_date.isoformat()} a {end_date.isoformat()}",
			},
			{
				"label": "Despesas",
				"value": _format_money(cashflow.gastos),
				"note": f"Savings Rate: {_format_pct(savings.taxa_poupanca_percentual)}",
			},
			{
				"label": "Savings Rate",
				"value": _format_pct(savings.taxa_poupanca_percentual),
				"note": f"Saldo líquido: {_format_money(cashflow.saldo_liquido)}",
			},
		]
	)

	left, right = st.columns((1.2, 0.8))
	with left:
		st.markdown('<div class="fa-panel">', unsafe_allow_html=True)
		st.markdown("### Saldo Líquido ao Longo do Tempo")
		if daily_series:
			chart_frame = [{"Data": row["Data"], "Saldo Líquido": _to_decimal(row["saldo_liquido"])} for row in daily_series]
			fig = px.line(chart_frame, x="Data", y="Saldo Líquido", template="plotly_dark", markers=True, line_shape="spline")
			fig.update_traces(line=dict(width=3, color="#38bdf8"))
			fig.update_layout(
				margin=dict(l=0, r=0, t=8, b=0),
				paper_bgcolor="rgba(0,0,0,0)",
				plot_bgcolor="rgba(0,0,0,0)",
				height=390,
				showlegend=False,
			)
			st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
		else:
			st.info("Não há dados suficientes para o período selecionado.")
		st.markdown("</div>", unsafe_allow_html=True)

	with right:
		st.markdown('<div class="fa-panel">', unsafe_allow_html=True)
		st.markdown("### Gastos por Categoria")
		if expenses:
			expense_rows = [{"Categoria": row["categoria"], "Total": _to_decimal(row["total"])} for row in expenses]
			fig = px.bar(
				expense_rows,
				x="Categoria",
				y="Total",
				template="plotly_dark",
				color="Total",
				color_continuous_scale=["#38bdf8", "#8b5cf6"],
			)
			fig.update_layout(
				margin=dict(l=0, r=0, t=8, b=0),
				paper_bgcolor="rgba(0,0,0,0)",
				plot_bgcolor="rgba(0,0,0,0)",
				height=390,
				coloraxis_showscale=False,
			)
			st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
		else:
			st.info("Sem gastos classificados no período selecionado.")
		st.markdown("</div>", unsafe_allow_html=True)

	st.markdown('<div class="fa-panel">', unsafe_allow_html=True)
	st.markdown("### Últimas Transações")
	recent = load_recent_transactions(12)
	if recent:
		st.dataframe(recent, use_container_width=True, hide_index=True)
	else:
		st.info("Sem transações recentes para exibir.")
	st.markdown("</div>", unsafe_allow_html=True)


def _render_assets_tab() -> None:
	"""Render the asset management tab."""

	with st.spinner("Atualizando leitura da carteira..."):
		get_portfolio_service().sync_market_prices()

	summary = load_portfolio_summary()
	assets = summary.get("ativos", [])

	left, right = st.columns((1.05, 0.95))
	with left:
		st.markdown('<div class="fa-panel">', unsafe_allow_html=True)
		st.markdown("### Alocação da Carteira")
		allocation_rows = summary.get("distribuicao_por_classe", [])
		if allocation_rows:
			fig = px.pie(
				allocation_rows,
				values="valor",
				names="classe",
				hole=0.58,
				template="plotly_dark",
				color_discrete_sequence=["#38bdf8", "#f59e0b", "#8b5cf6", "#34d399", "#fb7185", "#c084fc"],
			)
			fig.update_traces(textposition="inside", textinfo="percent+label")
			fig.update_layout(
				margin=dict(l=0, r=0, t=8, b=0),
				paper_bgcolor="rgba(0,0,0,0)",
				plot_bgcolor="rgba(0,0,0,0)",
				height=410,
				legend_title_text="Classe",
			)
			st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
		else:
			st.info("Nenhum ativo cadastrado ainda.")
		st.markdown("</div>", unsafe_allow_html=True)

	with right:
		st.markdown('<div class="fa-panel">', unsafe_allow_html=True)
		st.markdown("### Evolução de Proventos")
		monthly_dividends = load_monthly_dividends()
		if monthly_dividends:
			fig = px.bar(
				monthly_dividends,
				x="mes",
				y="valor_recebido",
				template="plotly_dark",
				text_auto=".2s",
				color="valor_recebido",
				color_continuous_scale=["#1d4ed8", "#38bdf8"],
			)
			fig.update_layout(
				margin=dict(l=0, r=0, t=8, b=0),
				paper_bgcolor="rgba(0,0,0,0)",
				plot_bgcolor="rgba(0,0,0,0)",
				height=410,
				coloraxis_showscale=False,
			)
			st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
		else:
			st.info("Sem dividendos registrados ainda.")
		st.markdown("</div>", unsafe_allow_html=True)

	st.markdown('<div class="fa-panel">', unsafe_allow_html=True)
	st.markdown("### Posições em Carteira")
	if assets:
		st.dataframe(
			[
				{
					"ticker": asset.get("ticker"),
					"classe": asset.get("classe"),
					"quantidade": _to_decimal(asset.get("quantidade")),
					"preco_medio": _format_money(asset.get("preco_medio")),
					"preco_atual": _format_money(asset.get("preco_atual", asset.get("preco_medio"))),
					"valor_mercado": _format_money(
						_to_decimal(asset.get("quantidade")) * _to_decimal(asset.get("preco_atual", asset.get("preco_medio")))
					),
					"lucro_prejuizo": _format_money(
						(_to_decimal(asset.get("quantidade")) * _to_decimal(asset.get("preco_atual", asset.get("preco_medio"))))
						- (_to_decimal(asset.get("quantidade")) * _to_decimal(asset.get("preco_medio")))
					),
				}
				for asset in assets
			],
			use_container_width=True,
			hide_index=True,
		)
	else:
		st.info("Nenhum ativo cadastrado no momento.")
	st.markdown("</div>", unsafe_allow_html=True)


def _render_goal_card(goal: dict[str, Any]) -> None:
	"""Render a single goal progress card."""

	nome = str(goal.get("nome", "Meta"))
	valor_alvo = _to_decimal(goal.get("valor_alvo"))
	valor_atual = _to_decimal(goal.get("valor_atual"))
	valor_restante = _to_decimal(goal.get("valor_restante"))
	percentual = _to_decimal(goal.get("percentual_conclusao"))
	aporte = _to_decimal(goal.get("aporte_mensal_sugerido"))
	prazo_meses = int(goal.get("prazo_meses") or 0)
	status = str(goal.get("status", "ATIVA"))
	progress_value = max(0, min(int(percentual.quantize(Decimal("1"))), 100))
	priority = int(goal.get("prioridade") or 0)
	status_label = "Concluída" if status == "CONCLUIDA" else "Pausada" if status == "PAUSADA" else "Ativa"

	st.markdown(
		f"""
		<div class="fa-card">
			<div class="fa-card-label">Prioridade {priority} | {status_label}</div>
			<div class="fa-card-value" style="font-size: 1.35rem;">{nome}</div>
			<div class="fa-card-note">Alvo: {_format_money(valor_alvo)} | Atual: {_format_money(valor_atual)} | Restante: {_format_money(valor_restante)}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)
	st.progress(progress_value)
	st.caption(
		f"Conclusão: {_format_pct(percentual)} | Aporte mensal sugerido: {_format_money(aporte)} | Prazo: {prazo_meses} meses"
	)


def _reset_goal_form_state() -> None:
	"""Clear the goal form state after a successful submission."""

	for key in ("goal_nome", "goal_valor_alvo", "goal_prazo_meses", "goal_prioridade"):
		st.session_state.pop(key, None)


def _render_goals_tab() -> None:
	"""Render the goals and budgets tab."""

	goals_service = get_goals_service()
	flash_message = st.session_state.pop("fin_analytics_goal_flash", None)
	if flash_message:
		st.success(flash_message)

	with st.expander("🎯 Cadastrar Novo Objetivo Financeiro", expanded=False):
		with st.form("goal_create_form", clear_on_submit=False):
			col1, col2 = st.columns((1.6, 1.0))
			with col1:
				nome = st.text_input("Nome do objetivo", key="goal_nome")
				valor_alvo = st.number_input("Valor alvo", min_value=0.01, step=100.0, format="%.2f", key="goal_valor_alvo")
			with col2:
				prazo_meses = st.number_input("Prazo em meses", min_value=1, step=1, value=12, key="goal_prazo_meses")
				prioridade = st.selectbox(
					"Prioridade",
					options=(1, 2, 3, 4, 5),
					format_func=lambda value: f"Nível {value}",
					key="goal_prioridade",
				)
			submit = st.form_submit_button("Salvar objetivo")
			if submit:
				try:
					success = goals_service.create_goal(
						nome=nome,
						valor_alvo=Decimal(str(valor_alvo)),
						prazo_meses=int(prazo_meses),
						prioridade=int(prioridade),
					)
				except Exception as exc:
					st.error(f"Falha ao cadastrar objetivo: {exc}")
				else:
					if success:
						st.session_state["fin_analytics_goal_flash"] = f"Objetivo '{nome.strip()}' cadastrado com sucesso."
						_reset_goal_form_state()
						st.cache_data.clear()
						st.rerun()
					else:
						st.error("Não foi possível cadastrar o objetivo. Verifique os dados e tente novamente.")

	goals = [goal for goal in load_goal_progress() if str(goal.get("status", "ATIVA")) == "ATIVA"]
	if not goals:
		st.info("Nenhuma meta ativa cadastrada no momento.")
		return

	st.markdown('<div class="fa-panel">', unsafe_allow_html=True)
	st.markdown("### Metas Ativas")
	st.caption("Cards com progresso visual, aporte sugerido e leitura rápida do horizonte de execução.")
	st.markdown("</div>", unsafe_allow_html=True)

	for goal in goals:
		_render_goal_card(goal)


def _render_quarantine_tab() -> None:
	"""Render the quarantine and diagnostics tab."""

	rows = load_quarantine_transactions()
	st.markdown('<div class="fa-panel">', unsafe_allow_html=True)
	st.markdown("### Quarentena & Diagnóstico")
	st.caption("Revise registros rejeitados ou sem categoria clara para ajustar o arquivo categorias.csv.")
	if rows:
		st.dataframe(rows, use_container_width=True, hide_index=True)
		st.caption("Mostrando até 200 linhas mais recentes de quarentena.")
	else:
		st.info("Nenhuma linha em quarentena no momento.")
	st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
	"""Run the Streamlit application."""

	st.set_page_config(
		page_title="Terminal de Patrimônio",
		page_icon="",
		layout="wide",
		initial_sidebar_state="expanded",
	)
	inject_premium_css()
	start_date, end_date = _build_sidebar_controls()
	health = load_system_health()
	latest_execution = health.get("latest_execution")
	latest_status = latest_execution[0] if latest_execution else "Sem dados"
	latest_file = latest_execution[1] if latest_execution else "Sem arquivo"

	flash_message = st.session_state.pop("fin_analytics_upload_flash", None)
	if flash_message:
		st.success(flash_message)

	_render_hero(
		"Terminal de Gestão de Patrimônio",
		"Uma superfície operacional para acompanhar fluxo, carteira, metas e quarentena sem o aspecto padrão do Streamlit.",
		[
			f"Período {start_date.isoformat()} → {end_date.isoformat()}",
			f"ETL {health.get('executions', 0)} execuções",
			f"Quarentena {health.get('quarantine_rows', 0)} linhas",
			f"Último status {latest_status}",
			f"Último arquivo {latest_file}",
		],
	)

	tab_overview, tab_assets, tab_goals, tab_quarantine = st.tabs(
		[
			"Visão Geral",
			"Gestão de Ativos",
			"Metas & Orçamentos (Budget)",
			"Quarentena & Diagnóstico",
		]
	)

	with tab_overview:
		_render_overview_tab(start_date, end_date)

	with tab_assets:
		_render_assets_tab()

	with tab_goals:
		_render_goals_tab()

	with tab_quarantine:
		_render_quarantine_tab()


if __name__ == "__main__":
	main()
