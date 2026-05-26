"""Shared visual shell for all Streamlit cockpit pages."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import streamlit as st

# Ensure repository root is importable in `streamlit run app/main.py` mode.
_APP_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _APP_DIR.parent
if str(_REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(_REPO_ROOT))

try:
	from app.dependencies import get_analytics_repository, get_transacoes_repository, get_wealth_repository
except ModuleNotFoundError:
	from dependencies import get_analytics_repository, get_transacoes_repository, get_wealth_repository

from etl.pipeline import ETLPipeline


_THEME_INJECTED_KEY = "fin_analytics_shell_theme_injected"


def configure_page(title: str, icon: str) -> None:
	"""Set standard page config and inject global shell styles once."""

	st.set_page_config(
		page_title=title,
		page_icon=icon,
		layout="wide",
		initial_sidebar_state="expanded",
	)
	inject_theme()


def inject_theme() -> None:
	"""Apply global dark styling and hide duplicated default navigation block."""

	if st.session_state.get(_THEME_INJECTED_KEY):
		return

	st.markdown(
		"""
		<style>
		.stApp {
			background: radial-gradient(140% 120% at 20% 0%, #10182a 0%, #0b111c 45%, #070b13 100%);
			color: #e8edf8;
		}

		section[data-testid="stSidebar"] {
			background: linear-gradient(180deg, rgba(8, 14, 25, 0.96), rgba(7, 11, 19, 0.98));
			border-right: 1px solid rgba(176, 193, 218, 0.12);
		}

		/* Hide Streamlit native page list to avoid duplicated navigation. */
		[data-testid="stSidebarNav"] {
			display: none;
		}

		[data-testid="stMetricValue"] {
			color: #f3f6ff;
		}
		</style>
		""",
		unsafe_allow_html=True,
	)
	st.session_state[_THEME_INJECTED_KEY] = True


def render_sidebar(active_tab: str) -> None:
	"""Render unified sidebar navigation, ETL actions, and health block."""

	with st.sidebar:
		st.markdown("## Cockpit Financeiro")
		st.caption("Navegacao rapida por workflow operacional")
		st.page_link("main.py", label="Command Center", icon=":material/dashboard:")
		st.page_link("pages/1_home.py", label="Home", icon=":material/home:")
		st.page_link("pages/2_investimentos.py", label="Investimentos", icon=":material/trending_up:")
		st.page_link("pages/3_metas_e_orcamentos.py", label="Metas e Orcamentos", icon=":material/target:")
		st.divider()

		if st.button("Processar Base Raw", use_container_width=True):
			_run_pipeline_and_refresh(rebuild=False)
		if st.button("Reprocessar Tudo", use_container_width=True):
			_run_pipeline_and_refresh(rebuild=True)
		st.divider()

	_render_health_status(active_tab=active_tab)


def _run_pipeline_and_refresh(*, rebuild: bool) -> None:
	"""Execute ETL pipeline from sidebar action and refresh UI state."""

	try:
		pipeline = ETLPipeline()
		if rebuild:
			result = pipeline.rebuild()
		else:
			result = pipeline.run()
	except Exception as exc:
		st.error(f"Falha no ETL: {exc}")
		return
	finally:
		try:
			pipeline.close()  # type: ignore[used-before-assignment]
		except Exception:
			pass

	st.success(
		f"ETL concluido | arquivos processados: {result.files_processed} | "
		f"linhas inseridas: {result.rows_inserted} | quarentena: {result.rows_quarantined}"
	)
	st.cache_data.clear()
	st.rerun()


def _render_health_status(*, active_tab: str) -> None:
	"""Render compact backend health indicators."""

	transacoes_repo = get_transacoes_repository()
	wealth_repo = get_wealth_repository()
	transacoes_repo.init_tables()
	wealth_repo.init_wealth_tables()
	health = get_analytics_repository().get_shell_health_snapshot()
	etl_row = health.get("latest_execution")
	status = str(etl_row[0]) if etl_row else "SEM_DADOS"
	status_color = "#5AF2B5" if status == "SUCESSO" else "#FFB347" if status == "SEM_DADOS" else "#FF8D96"

	with st.sidebar:
		st.markdown("### Health Status")
		st.caption(f"Aba ativa: {active_tab}")
		st.markdown(
			f"""
			<div style="padding:0.55rem 0.65rem;border:1px solid rgba(196,211,236,0.18);border-radius:10px;background:rgba(12,20,34,0.82);">
				<div style="font-size:0.78rem;color:#a9b7d0;text-transform:uppercase;letter-spacing:0.04em;">Pipeline</div>
				<div style="font-weight:700;color:{status_color};font-size:0.98rem;">{status}</div>
				<div style="font-size:0.75rem;color:#8f9cb5;">{etl_row[1] if etl_row else 'Nenhum arquivo processado'} | {etl_row[2].date() if etl_row else date.today()}</div>
			</div>
			""",
			unsafe_allow_html=True,
		)
		col_a, col_b = st.columns(2)
		col_a.metric("Ativos", f"{int(health.get('positions_count', 0) or 0)}")
		col_b.metric("Metas", f"{int(health.get('active_goals', 0) or 0)}")
