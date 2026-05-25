"""Premium KPI card components for the wealth dashboard UI."""

from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import Any

import streamlit as st

_CARD_CSS_INJECTED_KEY = "fin_analytics_metric_card_css_injected"


def _inject_card_styles() -> None:
	"""Inject component CSS only once per Streamlit session."""

	if st.session_state.get(_CARD_CSS_INJECTED_KEY):
		return

	st.markdown(
		"""
		<style>
		.fa-kpi-card {
			position: relative;
			overflow: hidden;
			padding: 1rem 1.05rem 0.95rem 1.05rem;
			border-radius: 16px;
			border: 1px solid rgba(255, 255, 255, 0.08);
			background:
				radial-gradient(140% 120% at 90% -20%, rgba(61, 177, 255, 0.14), rgba(61, 177, 255, 0.01) 48%, rgba(0, 0, 0, 0) 70%),
				linear-gradient(175deg, rgba(20, 23, 31, 0.96), rgba(10, 12, 17, 0.98));
			box-shadow:
				inset 0 1px 0 rgba(255, 255, 255, 0.04),
				0 10px 30px rgba(0, 0, 0, 0.35);
		}

		.fa-kpi-card::after {
			content: "";
			position: absolute;
			inset: 0;
			pointer-events: none;
			background: linear-gradient(130deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0));
			opacity: 0.55;
		}

		.fa-kpi-header {
			font-size: 0.72rem;
			letter-spacing: 0.07em;
			text-transform: uppercase;
			color: rgba(189, 198, 216, 0.92);
			font-weight: 600;
			margin-bottom: 0.5rem;
			font-family: "Avenir Next", "Segoe UI", sans-serif;
		}

		.fa-kpi-value {
			font-size: 1.6rem;
			line-height: 1.2;
			font-weight: 700;
			color: #F4F7FF;
			font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
			margin-bottom: 0.42rem;
		}

		.fa-kpi-delta {
			display: inline-flex;
			align-items: center;
			gap: 0.3rem;
			font-size: 0.85rem;
			font-weight: 600;
			padding: 0.18rem 0.52rem;
			border-radius: 999px;
			font-family: "Avenir Next", "Segoe UI", sans-serif;
		}

		.fa-kpi-delta-positive {
			color: #5AF2B5;
			background: rgba(15, 177, 102, 0.16);
			border: 1px solid rgba(90, 242, 181, 0.2);
		}

		.fa-kpi-delta-negative {
			color: #FF8D96;
			background: rgba(189, 57, 73, 0.2);
			border: 1px solid rgba(255, 141, 150, 0.25);
		}

		.fa-kpi-delta-neutral {
			color: #BFC9DF;
			background: rgba(112, 126, 161, 0.2);
			border: 1px solid rgba(191, 201, 223, 0.2);
		}
		</style>
		""",
		unsafe_allow_html=True,
	)
	st.session_state[_CARD_CSS_INJECTED_KEY] = True


def draw_metric_card(
	title: str,
	value: Any,
	delta: Any | None = None,
	is_positive: bool | None = None,
) -> None:
	"""Render a premium KPI card with optional delta chip."""

	_inject_card_styles()

	title_text = escape(str(title).strip() or "Metrica")
	value_text = escape(_format_value(value))

	delta_html = ""
	if delta is not None:
		delta_text = escape(_format_delta(delta, is_positive))
		if is_positive is True:
			delta_class = "fa-kpi-delta-positive"
			icon = "&#9650;"
		elif is_positive is False:
			delta_class = "fa-kpi-delta-negative"
			icon = "&#9660;"
		else:
			delta_class = "fa-kpi-delta-neutral"
			icon = "&#9679;"

		delta_html = f'<span class="fa-kpi-delta {delta_class}">{icon} {delta_text}</span>'

	st.markdown(
		f"""
		<div class="fa-kpi-card">
			<div class="fa-kpi-header">{title_text}</div>
			<div class="fa-kpi-value">{value_text}</div>
			{delta_html}
		</div>
		""",
		unsafe_allow_html=True,
	)


def _format_value(value: Any) -> str:
	"""Format numeric values for compact and readable KPI cards."""

	if isinstance(value, Decimal):
		return _format_decimal(value)
	if isinstance(value, (int, float)):
		return _format_decimal(Decimal(str(value)))
	if value is None:
		return "-"
	return str(value)


def _format_delta(delta: Any, is_positive: bool | None) -> str:
	"""Format delta values with explicit sign when possible."""

	if isinstance(delta, Decimal):
		base = _format_decimal(delta.copy_abs())
	elif isinstance(delta, (int, float)):
		base = _format_decimal(Decimal(str(abs(delta))))
	else:
		return str(delta)

	if is_positive is True:
		return f"+ {base}"
	if is_positive is False:
		return f"- {base}"
	return base


def _format_decimal(value: Decimal) -> str:
	"""Format decimals in pt-BR style for money-like metrics."""

	quantized = value.quantize(Decimal("0.01"))
	formatted = f"{quantized:,.2f}"
	return formatted.replace(",", "_").replace(".", ",").replace("_", ".")
