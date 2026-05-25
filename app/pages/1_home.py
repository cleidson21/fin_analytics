"""Minimal home page for file ingestion and portfolio visibility."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

import streamlit as st

try:
	from app.dependencies import get_ingestion_service, get_wealth_repository
except ModuleNotFoundError:
	from dependencies import get_ingestion_service, get_wealth_repository

from config.constants import FonteDados, StatusProcessamento
from repositories.wealth_repository import WealthRepository
from services.portfolio_service import PortfolioService


def _format_currency(value: Decimal) -> str:
	"""Format a Decimal using Brazilian currency conventions."""

	quantized = value.quantize(Decimal("0.01"))
	formatted = f"{quantized:,.2f}"
	return f"R$ {formatted.replace(',', '_').replace('.', ',').replace('_', '.')}"


def _to_decimal(value: object) -> Decimal:
	"""Safely coerce numeric payloads into Decimal."""

	if isinstance(value, Decimal):
		return value
	if isinstance(value, int):
		return Decimal(value)
	if isinstance(value, float):
		return Decimal(str(value))
	if isinstance(value, str):
		try:
			return Decimal(value)
		except InvalidOperation:
			return Decimal("0")
	return Decimal("0")


def _infer_fonte(file_name: str) -> FonteDados:
	"""Infer the source system from the uploaded file name."""

	name = file_name.lower()
	if any(marker in name for marker in ("tableexport", "proventos", "myprofit")):
		return FonteDados.MYPROFIT
	if any(marker in name for marker in ("nubank", "bank", "extrato")):
		return FonteDados.NUBANK
	return FonteDados.MANUAL


def _format_portfolio_card(total_value: Decimal, pnl_value: Decimal) -> str:
	"""Render a large premium-style portfolio card."""

	return f"""
	<div class=\"hero-card\">
		<div class=\"hero-card__eyebrow\">Património Líquido</div>
		<div class=\"hero-card__value\">{_format_currency(total_value)}</div>
		<div class=\"hero-card__meta\">P/L total: {_format_currency(pnl_value)}</div>
	</div>
	"""


def _inject_home_css() -> None:
	"""Add the page-level styling for the upload surface and hero card."""

	st.markdown(
		"""
		<style>
			.hero-card {
				padding: 2.2rem 2rem;
				border-radius: 28px;
				background: linear-gradient(135deg, rgba(0, 229, 255, 0.08), rgba(0, 255, 163, 0.05)), rgba(255, 255, 255, 0.02);
				border: 1px solid rgba(0, 229, 255, 0.14);
				box-shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
			}
			.hero-card__eyebrow {
				text-transform: uppercase;
				letter-spacing: 0.18em;
				font-size: 0.74rem;
				color: rgba(245, 248, 255, 0.7);
				margin-bottom: 0.65rem;
			}
			.hero-card__value {
				font-size: clamp(2.6rem, 6vw, 5.5rem);
				font-weight: 800;
				line-height: 0.95;
				color: #F5F8FF;
			}
			.hero-card__meta {
				margin-top: 1rem;
				font-size: 1rem;
				color: rgba(245, 248, 255, 0.82);
			}
			div[data-testid="stFileUploader"] {
				border: 1px dashed rgba(0, 229, 255, 0.35);
				border-radius: 18px;
				padding: 0.5rem;
				background: rgba(255, 255, 255, 0.02);
			}
		</style>
		""",
		unsafe_allow_html=True,
	)


def _process_uploaded_file(file_name: str, file_bytes: bytes) -> None:
	"""Route the upload through the ingestion service with visible progress."""

	ingestion_service = get_ingestion_service()
	fonte = _infer_fonte(file_name)
	progress = st.progress(0, text="Preparando ingestão...")
	try:
		progress.progress(20, text="Lendo ficheiro...")
		process_method = getattr(ingestion_service, "process_bytes", ingestion_service.process_uploaded_file)
		progress.progress(45, text="Validando e roteando...")
		result = process_method(file_bytes=file_bytes, file_name=file_name, fonte=fonte)
		progress.progress(85, text="Persistindo dados...")
		progress.progress(100, text="Concluído")
		if result.status == StatusProcessamento.SUCESSO:
			st.success(f"Ingestão concluída: {result.rows_inserted} registos inseridos.")
		else:
			st.error(result.error_message or "Falha durante a ingestão.")
		st.caption(result.to_dict())
	except Exception as exc:
		progress.progress(100, text="Erro")
		st.error(f"Erro na ingestão: {exc}")
		st.exception(exc)


def main() -> None:
	"""Render the minimal wealth home screen."""

	st.title("Home")
	st.caption("Entrada híbrida para ingestão e visão rápida do património.")
	_inject_home_css()

	uploaded_file = st.file_uploader(
		"Carregar CSV",
		type=["csv"],
		accept_multiple_files=False,
		help="Aceita extratos bancários e ficheiros de investimentos em CSV.",
	)
	if uploaded_file is not None:
		_process_uploaded_file(uploaded_file.name, uploaded_file.getvalue())

	wealth_repository = get_wealth_repository()
	portfolio_service = PortfolioService(wealth_repository)
	try:
		summary = portfolio_service.get_portfolio_summary()
		patrimonio_total = _to_decimal(summary.get("patrimonio_total"))
		lucro_prejuizo_total = _to_decimal(summary.get("lucro_prejuizo_total"))
	except Exception as exc:
		st.error(f"Não foi possível carregar o património: {exc}")
		st.exception(exc)
		return

	st.markdown(_format_portfolio_card(patrimonio_total, lucro_prejuizo_total), unsafe_allow_html=True)


if __name__ == "__main__":
	main()