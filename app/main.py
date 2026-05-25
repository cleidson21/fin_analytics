"""Streamlit shell/router for the financial cockpit."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
PAGE_LINKS = (
	("Home", "pages/1_home.py", "🏠"),
	("Investimentos", "pages/2_investimentos.py", "💼"),
	("Metas e orçamentos", "pages/3_metas_e_orcamentos.py", "🎯"),
	("Admin", "pages/4_admin.py", "⚙️"),
)


def _inject_global_css() -> None:
	"""Inject the global shell styling used across the app."""

	st.markdown(
		"""
		<style>
			#MainMenu {visibility: hidden;}
			footer {visibility: hidden;}
			header {visibility: hidden;}
			[data-testid="stAppViewContainer"] {
				background: radial-gradient(circle at top, rgba(0, 178, 255, 0.10), transparent 36%), #0E1117;
				color: #F5F8FF;
			}
			[data-testid="stSidebar"] {
				background: linear-gradient(180deg, rgba(8, 12, 24, 0.96), rgba(14, 17, 23, 0.98));
				border-right: 1px solid rgba(255, 255, 255, 0.08);
			}
			[data-testid="stSidebar"] * {
				color: #F5F8FF;
			}
			.stButton > button,
			button[kind="primary"],
			[data-testid="stDownloadButton"] button {
				background: linear-gradient(135deg, #00E5FF 0%, #00B8D9 45%, #00FFB3 100%);
				color: #061018;
				border: 0;
				border-radius: 999px;
				box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.18), 0 0 24px rgba(0, 229, 255, 0.25);
				font-weight: 700;
			}
			.stButton > button:hover,
			button[kind="primary"]:hover,
			[data-testid="stDownloadButton"] button:hover {
				transform: translateY(-1px);
				box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.28), 0 0 28px rgba(0, 229, 255, 0.42);
			}
			div[data-testid="stFileUploader"] {
				border: 1px dashed rgba(0, 229, 255, 0.35);
				border-radius: 18px;
				padding: 0.5rem;
				background: rgba(255, 255, 255, 0.02);
			}
			[data-testid="stSidebarNav"] {
				padding-top: 1rem;
			}
			[data-testid="stSidebarNav"] a {
				border-radius: 14px;
			}
		</style>
		""",
		unsafe_allow_html=True,
	)


def _render_shell_navigation() -> None:
	"""Render the native sidebar navigation for the app pages."""

	st.sidebar.markdown("### Fin Analytics")
	st.sidebar.caption("Shell visual. Lógica vive nas páginas.")
	for label, page_path, icon in PAGE_LINKS:
		st.sidebar.page_link(page_path, label=label, icon=icon)


def main() -> None:
	"""Bootstrap the Streamlit shell without any business logic."""

	st.set_page_config(
		page_title="Fin Analytics",
		page_icon=":material/monitoring:",
		layout="wide",
		initial_sidebar_state="expanded",
	)
	_inject_global_css()
	st.session_state.setdefault("active_section", "home")
	st.session_state.setdefault("upload_busy", False)
	_render_shell_navigation()
	st.title("Fin Analytics")
	st.caption("Shell/Router do Streamlit preparado para evoluir para uma API REST.")
	st.info("Escolha uma página na barra lateral. O backend e a ingestão ficam fora deste ficheiro.")


if __name__ == "__main__":
	main()
