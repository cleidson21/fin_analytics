"""Entry point for the modular financial cockpit."""

from __future__ import annotations

import streamlit as st

try:
	from app.core.shell import configure_page, render_sidebar
	from app.core.state import get_ui_state, initialize_session_state, set_active_tab
except ModuleNotFoundError:
	from core.shell import configure_page, render_sidebar
	from core.state import get_ui_state, initialize_session_state, set_active_tab


def main() -> None:
	"""Bootstrap the Streamlit financial cockpit shell."""

	configure_page(title="Cockpit Financeiro", icon=":material/insights:")
	initialize_session_state()
	set_active_tab("home")
	render_sidebar(active_tab="home")

	ui_state = get_ui_state()
	st.title("Command Center")
	st.caption("Use a barra lateral para navegar entre os modulos operacionais.")
	st.info(
		f"Sessao ativa | Aba: {ui_state['active_tab']} | Modal aberto: {'Sim' if ui_state['modal_open'] else 'Nao'}",
	)


if __name__ == "__main__":
	main()
