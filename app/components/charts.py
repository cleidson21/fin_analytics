"""High-performance Plotly chart components for the wealth dashboard."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from models.wealth_schemas import FinancialGoalDTO

_PLOTLY_TRANSPARENT = "rgba(0,0,0,0)"
_PLOTLY_TEXT = "#E8EDF8"
_PLOTLY_MUTED_TEXT = "#A8B4CC"
_PLOTLY_GRID = "rgba(178, 190, 215, 0.14)"
_PLOTLY_TEMPLATE = "plotly_dark"

_ALLOCATION_COLORS = [
	"#5DA9FF",
	"#3ED598",
	"#FFD166",
	"#FF8FA3",
	"#C3A6FF",
	"#7BE0FF",
]

_SANKEY_COLORS = ["#5DA9FF", "#FF8FA3", "#FFD166", "#3ED598", "#C3A6FF"]


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


def _format_currency(value: Decimal) -> str:
	formatted = f"{value.quantize(Decimal('0.01')):,.2f}"
	return f"R$ {formatted.replace(',', '_').replace('.', ',').replace('_', '.')}"


def _apply_dark_layout(figure: go.Figure, *, margin: dict[str, int] | None = None) -> go.Figure:
	figure.update_layout(
		template=_PLOTLY_TEMPLATE,
		paper_bgcolor=_PLOTLY_TRANSPARENT,
		plot_bgcolor=_PLOTLY_TRANSPARENT,
		font={"family": "Avenir Next, Segoe UI, sans-serif", "color": _PLOTLY_TEXT},
		margin=margin or {"l": 8, "r": 8, "t": 8, "b": 8},
	)
	return figure


def draw_allocation_donut(df: Any) -> None:
	"""Render a dark-mode allocation donut chart with transparent background."""

	if df is None or getattr(df, "empty", False):
		st.info("Sem dados de alocacao para exibir.")
		return

	figure = px.pie(
		df,
		names="classe",
		values="valor",
		hole=0.62,
		color="classe",
		color_discrete_sequence=_ALLOCATION_COLORS,
	)

	figure.update_traces(
		sort=False,
		textposition="inside",
		texttemplate="%{percent}",
		insidetextfont={"size": 12, "color": "#F5F8FF"},
		hovertemplate="<b>%{label}</b><br>Valor: %{value:,.2f}<br>Participacao: %{percent}<extra></extra>",
		marker={"line": {"color": "rgba(18, 23, 34, 0.95)", "width": 1.1}},
	)

	figure.update_layout(
		showlegend=True,
		legend={
			"orientation": "h",
			"yanchor": "bottom",
			"y": -0.08,
			"xanchor": "center",
			"x": 0.5,
			"font": {"size": 11, "color": _PLOTLY_MUTED_TEXT},
		},
		paper_bgcolor=_PLOTLY_TRANSPARENT,
		plot_bgcolor=_PLOTLY_TRANSPARENT,
		margin={"l": 8, "r": 8, "t": 8, "b": 8},
		font={"family": "Avenir Next, Segoe UI, sans-serif", "color": _PLOTLY_TEXT},
	)

	_apply_dark_layout(figure)
	st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def draw_net_worth_evolution(df: Any) -> None:
	"""Render a dark-mode area chart for net-worth evolution over time."""

	if df is None or getattr(df, "empty", False):
		st.info("Sem historico patrimonial para exibir.")
		return

	figure = px.area(df, x="data", y="patrimonio_total", line_shape="spline")
	figure.update_traces(
		line={"width": 2.4, "color": "#5DA9FF"},
		fill="tozeroy",
		fillcolor="rgba(93, 169, 255, 0.26)",
		hovertemplate="<b>%{x}</b><br>Patrimonio: %{y:,.2f}<extra></extra>",
	)
	figure.update_layout(
		xaxis={
			"title": None,
			"showgrid": False,
			"showline": False,
			"tickfont": {"size": 11, "color": _PLOTLY_MUTED_TEXT},
		},
		yaxis={
			"title": None,
			"showgrid": True,
			"gridcolor": _PLOTLY_GRID,
			"zeroline": False,
			"tickfont": {"size": 11, "color": _PLOTLY_MUTED_TEXT},
		},
		paper_bgcolor=_PLOTLY_TRANSPARENT,
		plot_bgcolor=_PLOTLY_TRANSPARENT,
		margin={"l": 8, "r": 8, "t": 12, "b": 8},
		font={"family": "Avenir Next, Segoe UI, sans-serif", "color": _PLOTLY_TEXT},
		hoverlabel={"bgcolor": "#111827", "font": {"color": "#F8FAFF"}},
		template=_PLOTLY_TEMPLATE,
	)
	figure.add_trace(
		go.Scatter(
			x=df["data"],
			y=df["patrimonio_total"],
			mode="lines",
			line={"width": 0},
			showlegend=False,
			hoverinfo="skip",
		),
	)
	st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def draw_sankey_cashflow(
	receitas: object,
	investimentos: object,
	gastos_essenciais: object,
	gastos_discricionarios: object,
) -> None:
	"""Render a Sankey diagram for the current cashflow split."""

	receitas_decimal = _to_decimal(receitas)
	investimentos_decimal = max(_to_decimal(investimentos), Decimal("0"))
	essenciais_decimal = max(_to_decimal(gastos_essenciais), Decimal("0"))
	discricionarios_decimal = max(_to_decimal(gastos_discricionarios), Decimal("0"))
	savings_decimal = max(
		receitas_decimal - investimentos_decimal - essenciais_decimal - discricionarios_decimal,
		Decimal("0"),
	)

	if receitas_decimal <= 0 and investimentos_decimal <= 0 and essenciais_decimal <= 0 and discricionarios_decimal <= 0:
		st.info("Sem fluxo de caixa suficiente para exibir o Sankey deste periodo.")
		return

	figure = go.Figure(
		data=[
			go.Sankey(
				node={
					"pad": 22,
					"thickness": 18,
					"line": {"color": "rgba(255,255,255,0.1)", "width": 0.8},
					"label": ["Receitas", "Gastos Essenciais", "Gastos Discricionarios", "Investimentos", "Patrimonio"],
					"color": _SANKEY_COLORS,
				},
				link={
					"source": [0, 0, 0, 0],
					"target": [1, 2, 3, 4],
					"value": [
						float(essenciais_decimal),
						float(discricionarios_decimal),
						float(investimentos_decimal),
						float(savings_decimal),
					],
					"color": [
						"rgba(255, 143, 163, 0.42)",
						"rgba(255, 209, 102, 0.42)",
						"rgba(62, 213, 152, 0.42)",
						"rgba(93, 169, 255, 0.42)",
					],
				},
				arrangement="snap",
				valueformat=",.2f",
			),
		]
	)
	figure.update_layout(title={"text": "Fluxo de Caixa", "x": 0.01, "xanchor": "left"}, height=420)
	_apply_dark_layout(figure, margin={"l": 10, "r": 10, "t": 48, "b": 10})
	st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def draw_treemap_expenses(df_despesas: Any) -> None:
	"""Render a hierarchical treemap from macro category to subcategory."""

	if df_despesas is None or getattr(df_despesas, "empty", False):
		st.info("Sem despesas para exibir no treemap.")
		return

	df = pd.DataFrame(df_despesas).copy()
	if df.empty:
		st.info("Sem despesas para exibir no treemap.")
		return

	column_aliases = {
		"MacroCategoria": "macro_categoria",
		"macro_categoria": "macro_categoria",
		"Categoria": "subcategoria",
		"categoria": "subcategoria",
		"Subcategoria": "subcategoria",
		"subcategoria": "subcategoria",
		"Valor": "valor",
		"valor": "valor",
		"Total": "valor",
		"total": "valor",
	}
	for source_name, target_name in column_aliases.items():
		if source_name in df.columns and source_name != target_name:
			df = df.rename(columns={source_name: target_name})

	if "valor" not in df.columns:
		st.info("A estrutura de despesas nao contem coluna de valor reconhecivel.")
		return

	if "subcategoria" not in df.columns:
		st.info("As despesas precisam de uma coluna de subcategoria para o treemap.")
		return

	if "macro_categoria" not in df.columns:
		df["macro_categoria"] = df["subcategoria"]

	df["macro_categoria"] = df["macro_categoria"].astype(str).str.upper().str.strip()
	df["subcategoria"] = df["subcategoria"].astype(str).str.upper().str.strip()
	df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
	grouped = (
		df.groupby(["macro_categoria", "subcategoria"], dropna=False, as_index=False)["valor"].sum().sort_values("valor", ascending=False)
	)

	if grouped.empty:
		st.info("Sem dados consolidados para exibir o treemap.")
		return

	figure = px.treemap(
		grouped,
		path=[px.Constant("Despesas"), "macro_categoria", "subcategoria"],
		values="valor",
		color="macro_categoria",
		color_discrete_sequence=_ALLOCATION_COLORS,
	)
	figure.update_traces(
		root_color="rgba(255,255,255,0.04)",
		textinfo="label+value+percent parent",
		hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Participacao: %{percentParent}<extra></extra>",
		marker={"line": {"color": "rgba(18, 23, 34, 0.92)", "width": 1.0}},
	)
	figure.update_layout(title={"text": "Despesas por Macro Categoria", "x": 0.01, "xanchor": "left"}, height=520)
	_apply_dark_layout(figure, margin={"l": 8, "r": 8, "t": 48, "b": 8})
	st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def draw_goals_progress(goals: Sequence[FinancialGoalDTO | dict[str, Any]]) -> None:
	"""Render a premium horizontal progress view for financial goals."""

	if not goals:
		st.info("Nenhuma meta financeira cadastrada.")
		return

	normalized_goals = [_normalize_goal(goal) for goal in goals]
	normalized_goals.sort(key=lambda item: (item["prioridade"], item["data_limite"] or "9999-12-31", item["nome"]))

	labels = [goal["nome"] for goal in normalized_goals]
	targets = [float(goal["valor_meta"]) for goal in normalized_goals]
	current_values = [float(goal["valor_atual"]) for goal in normalized_goals]
	progress_text = [f"{goal['percentual']:.0f}%" for goal in normalized_goals]
	colors = [
		"#3ED598" if goal["percentual"] >= 100 else "#5DA9FF" if goal["percentual"] >= 60 else "#FFD166"
		for goal in normalized_goals
	]

	figure = go.Figure()
	figure.add_trace(
		go.Bar(
			y=labels,
			x=targets,
			orientation="h",
			marker={"color": "rgba(255,255,255,0.08)", "line": {"color": "rgba(255,255,255,0.08)", "width": 1}},
			width=0.56,
			hoverinfo="skip",
			showlegend=False,
		),
	)
	figure.add_trace(
		go.Bar(
			y=labels,
			x=current_values,
			orientation="h",
			marker={"color": colors, "line": {"color": "rgba(255,255,255,0.12)", "width": 0.8}},
			width=0.56,
			text=progress_text,
			textposition="inside",
			insidetextanchor="middle",
			customdata=[[ _format_currency(_to_decimal(goal["valor_meta"])) ] for goal in normalized_goals],
			hovertemplate=(
				"<b>%{y}</b><br>Atual: R$ %{x:,.2f}<br>Meta: %{customdata[0]}<br>Concluido: %{text}<extra></extra>"
			),
			showlegend=False,
		),
	)

	max_value = max(max(targets), 1.0)
	figure.update_layout(
		barmode="overlay",
		height=max(280, 110 + len(labels) * 58),
		title={"text": "Metas Financeiras", "x": 0.01, "xanchor": "left"},
		xaxis={
			"title": None,
			"range": [0, max_value * 1.12],
			"showgrid": True,
			"gridcolor": _PLOTLY_GRID,
			"tickfont": {"size": 11, "color": _PLOTLY_MUTED_TEXT},
		},
		yaxis={
			"title": None,
			"autorange": "reversed",
			"tickfont": {"size": 12, "color": _PLOTLY_TEXT},
		},
		margin={"l": 8, "r": 18, "t": 48, "b": 8},
	)
	_apply_dark_layout(figure)
	for goal in normalized_goals:
		figure.add_annotation(
			x=float(goal["valor_meta"]),
			y=goal["nome"],
			text=f"{_format_currency(goal['valor_atual'])} / {_format_currency(goal['valor_meta'])}",
			showarrow=False,
			xanchor="right",
			yanchor="middle",
			font={"size": 11, "color": _PLOTLY_MUTED_TEXT},
			bgcolor="rgba(0,0,0,0)",
		)

	st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def _normalize_goal(goal: FinancialGoalDTO | dict[str, Any]) -> dict[str, Any]:
	if isinstance(goal, FinancialGoalDTO):
		goal_dict = goal.model_dump()
	else:
		goal_dict = dict(goal)

	valor_meta = _to_decimal(goal_dict.get("valor_meta", goal_dict.get("valor_alvo", 0)))
	valor_atual = _to_decimal(goal_dict.get("valor_atual", 0))
	percentual = goal_dict.get("percentual_conclusao")
	if percentual is None:
		percentual = (valor_atual / valor_meta * Decimal("100")) if valor_meta > 0 else Decimal("0")
	else:
		percentual = _to_decimal(percentual)

	return {
		"nome": str(goal_dict.get("nome", "Meta")).strip() or "Meta",
		"valor_meta": valor_meta,
		"valor_atual": valor_atual,
		"percentual": float(min(percentual, Decimal("100"))),
		"prioridade": int(goal_dict.get("prioridade") or 1),
		"data_limite": str(goal_dict.get("data_limite")) if goal_dict.get("data_limite") else None,
	}