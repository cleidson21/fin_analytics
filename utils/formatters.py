"""Formatting helpers for the Streamlit user interface.

These utilities keep presentation logic isolated from the service and
repository layers.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import streamlit as st


def format_currency_br(value: Decimal) -> str:
	"""Format a decimal value as Brazilian currency.

	Args:
		value: Monetary value to format.

	Returns:
		A string in the Brazilian currency format, for example
		``R$ 1.500,50`` or ``-R$ 1.500,50``.
	"""

	quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
	absolute_text = f"{abs(quantized):,.2f}"
	formatted = absolute_text.replace(",", "X").replace(".", ",").replace("X", ".")
	prefix = "-" if quantized < 0 else ""
	return f"{prefix}R$ {formatted}"


def format_percentage(value: Decimal) -> str:
	"""Format a decimal value as a percentage string.

	Args:
		value: Percentage value to format.

	Returns:
		A string formatted with a decimal comma, for example ``15,4%``.
	"""

	quantized = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
	absolute_text = f"{abs(quantized):.1f}".replace(".", ",")
	prefix = "-" if quantized < 0 else ""
	return f"{prefix}{absolute_text}%"


def inject_premium_css() -> None:
	"""Inject a refined dark visual system for the Streamlit app."""

	st.markdown(
		"""
		<style>
			:root {
				--fa-bg: #05070d;
				--fa-surface: rgba(16, 20, 31, 0.92);
				--fa-surface-strong: rgba(20, 25, 38, 0.98);
				--fa-surface-soft: rgba(255, 255, 255, 0.03);
				--fa-border: rgba(255, 255, 255, 0.08);
				--fa-text: #eef2ff;
				--fa-muted: #9ba7c3;
				--fa-accent: #7dd3fc;
				--fa-accent-strong: #38bdf8;
				--fa-progress-track: rgba(255, 255, 255, 0.08);
				--fa-progress-fill: linear-gradient(90deg, #38bdf8 0%, #60a5fa 50%, #22c55e 100%);
			}

			.stApp {
				background:
					radial-gradient(circle at top left, rgba(56, 189, 248, 0.14), transparent 30%),
					radial-gradient(circle at top right, rgba(34, 197, 94, 0.08), transparent 24%),
					linear-gradient(180deg, #04060b 0%, #09111d 100%);
				color: var(--fa-text);
			}

			html, body, [class*="css"] {
				font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
			}

			head, footer, #MainMenu {
				visibility: hidden;
				height: 0;
			}

			div[data-testid="stAppViewContainer"] {
				background: transparent;
			}

			section[data-testid="stSidebar"] {
				background: linear-gradient(180deg, rgba(8, 11, 18, 0.98), rgba(12, 16, 26, 0.98));
				border-right: 1px solid var(--fa-border);
			}

			section[data-testid="stSidebar"] * {
				color: var(--fa-text);
			}

			div.block-container {
				padding-top: 1rem;
				padding-bottom: 1.5rem;
				max-width: 100%;
			}

			main > div {
				padding-left: 0.75rem;
				padding-right: 0.75rem;
			}

			[data-testid="stHorizontalBlock"] {
				gap: 0.85rem;
			}

			[data-testid="stMetric"] {
				background: linear-gradient(180deg, var(--fa-surface), var(--fa-surface-strong));
				border: 1px solid var(--fa-border);
				border-radius: 22px;
				padding: 1rem 1rem 0.9rem 1rem;
				box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
			}

			[data-testid="stMetricLabel"] p {
				color: var(--fa-muted);
				font-size: 0.78rem;
				letter-spacing: 0.08em;
				text-transform: uppercase;
			}

			[data-testid="stMetricValue"] {
				color: var(--fa-text);
				font-weight: 800;
			}

			[data-testid="stMetricDelta"] {
				color: var(--fa-muted);
			}

			.fa-card,
			[data-testid="stContainer"]:has(.fa-card) {
				background: linear-gradient(180deg, rgba(20, 25, 38, 0.92), rgba(14, 19, 32, 0.96));
				border: 1px solid var(--fa-border);
				border-radius: 24px;
				box-shadow: 0 20px 50px rgba(0, 0, 0, 0.16);
			}

			.fa-card {
				padding: 1rem 1.05rem;
			}

			.fa-card h1,
			.fa-card h2,
			.fa-card h3,
			.fa-card h4,
			.fa-card p {
				margin-top: 0;
			}

			[data-testid="stProgress"] > div {
				background: var(--fa-progress-track);
				border-radius: 999px;
				height: 0.85rem;
				overflow: hidden;
			}

			[data-testid="stProgress"] > div > div {
				background: var(--fa-progress-fill);
				border-radius: 999px;
				box-shadow: 0 0 18px rgba(56, 189, 248, 0.35);
			}

			[data-testid="stProgress"] label,
			[data-testid="stProgress"] span {
				color: var(--fa-muted);
			}

			[data-testid="stExpander"] {
				border: 1px solid var(--fa-border);
				border-radius: 18px;
				background: rgba(255, 255, 255, 0.02);
			}

			button[kind="primary"],
			button[kind="secondary"] {
				border-radius: 999px;
				border: 1px solid rgba(125, 211, 252, 0.24);
			}

			button[kind="primary"] {
				background: linear-gradient(135deg, #38bdf8, #2563eb);
				color: white;
			}

			button[kind="secondary"] {
				background: rgba(255, 255, 255, 0.03);
				color: var(--fa-text);
			}

			input, textarea, select {
				background: rgba(255, 255, 255, 0.03) !important;
				color: var(--fa-text) !important;
				border-color: var(--fa-border) !important;
			}
		</style>
		""",
		unsafe_allow_html=True,
	)
