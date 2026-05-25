"""High-performance Plotly chart components for the wealth dashboard."""

from __future__ import annotations

from typing import Any

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_PLOTLY_TRANSPARENT = "rgba(0,0,0,0)"
_PLOTLY_TEXT = "#E8EDF8"
_PLOTLY_MUTED_TEXT = "#A8B4CC"
_PLOTLY_GRID = "rgba(178, 190, 215, 0.14)"

_ALLOCATION_COLORS = [
	"#5DA9FF",
	"#3ED598",
	"#FFD166",
	"#FF8FA3",
	"#C3A6FF",
	"#7BE0FF",
]


def draw_allocation_donut(df: Any) -> None:
	"""Render a dark-mode allocation donut chart with transparent background.

	Expected columns:
	- classe (str): allocation bucket label.
	- valor (numeric): absolute value allocated to the bucket.
	"""

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

	st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def draw_net_worth_evolution(df: Any) -> None:
	"""Render a dark-mode area chart for net-worth evolution over time.

	Expected columns:
	- data (datetime/date/str): timeline axis.
	- patrimonio_total (numeric): total net worth at each point.
	"""

	if df is None or getattr(df, "empty", False):
		st.info("Sem historico patrimonial para exibir.")
		return

	figure = px.area(
		df,
		x="data",
		y="patrimonio_total",
		line_shape="spline",
	)

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
	)

	figure.add_trace(
		go.Scatter(
			x=df["data"],
			y=df["patrimonio_total"],
			mode="lines",
			line={"width": 0},
			showlegend=False,
			hoverinfo="skip",
		)
	)

	st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
