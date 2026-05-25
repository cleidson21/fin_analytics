"""Session-state orchestration for the modular Streamlit frontend."""

from __future__ import annotations

from typing import Any

import streamlit as st

try:
	from app.dependencies import get_finance_service, get_transacoes_repository, get_wealth_repository
except ModuleNotFoundError:
	from dependencies import get_finance_service, get_transacoes_repository, get_wealth_repository
from services.market_service import MarketDataService
from services.wealth_service import WealthIntelligenceService

_STATE_BOOTSTRAPPED_KEY = "fin_analytics_ui_bootstrapped"
_STATE_MODAL_KEY = "fin_analytics_ui_modal_open"
_STATE_ACTIVE_TAB_KEY = "fin_analytics_ui_active_tab"
_STATE_EDIT_TARGET_KEY = "fin_analytics_ui_edit_target"
_STATE_FLASH_MESSAGE_KEY = "fin_analytics_ui_flash_message"

_STATE_WEALTH_INTELLIGENCE_SERVICE = "fin_analytics_wealth_intelligence_service"
_STATE_MARKET_SERVICE = "fin_analytics_market_data_service"


def initialize_session_state() -> None:
	"""Initialize service and UI-control keys only once per Streamlit session."""

	if st.session_state.get(_STATE_BOOTSTRAPPED_KEY):
		return

	st.session_state.setdefault(_STATE_MODAL_KEY, False)
	st.session_state.setdefault(_STATE_ACTIVE_TAB_KEY, "overview")
	st.session_state.setdefault(_STATE_EDIT_TARGET_KEY, None)
	st.session_state.setdefault(_STATE_FLASH_MESSAGE_KEY, None)

	st.session_state[_STATE_BOOTSTRAPPED_KEY] = True


def get_market_data_service() -> MarketDataService:
	"""Return the session-scoped market data service instance."""

	service = st.session_state.get(_STATE_MARKET_SERVICE)
	if isinstance(service, MarketDataService):
		return service

	service = MarketDataService()
	st.session_state[_STATE_MARKET_SERVICE] = service
	return service


def get_wealth_intelligence_service() -> WealthIntelligenceService:
	"""Return the session-scoped wealth intelligence service instance."""

	service = st.session_state.get(_STATE_WEALTH_INTELLIGENCE_SERVICE)
	if isinstance(service, WealthIntelligenceService):
		return service

	service = WealthIntelligenceService(
		wealth_repository=get_wealth_repository(),
		transactions_repository=get_transacoes_repository(),
		market_data_service=get_market_data_service(),
	)
	st.session_state[_STATE_WEALTH_INTELLIGENCE_SERVICE] = service
	return service


def get_ui_state() -> dict[str, Any]:
	"""Return a snapshot of the current UI control state."""

	initialize_session_state()
	return {
		"modal_open": bool(st.session_state.get(_STATE_MODAL_KEY, False)),
		"active_tab": str(st.session_state.get(_STATE_ACTIVE_TAB_KEY, "overview")),
		"edit_target": st.session_state.get(_STATE_EDIT_TARGET_KEY),
		"flash_message": st.session_state.get(_STATE_FLASH_MESSAGE_KEY),
	}


def set_modal_open(is_open: bool) -> None:
	"""Set the modal visibility state."""

	st.session_state[_STATE_MODAL_KEY] = bool(is_open)


def set_active_tab(tab_key: str) -> None:
	"""Set the currently active tab identifier."""

	st.session_state[_STATE_ACTIVE_TAB_KEY] = str(tab_key).strip() or "overview"


def set_edit_target(target: Any) -> None:
	"""Set the current target object used by edit forms/modals."""

	st.session_state[_STATE_EDIT_TARGET_KEY] = target


def set_flash_message(message: str | None) -> None:
	"""Set a one-shot flash message for UI feedback."""

	st.session_state[_STATE_FLASH_MESSAGE_KEY] = message


def pop_flash_message() -> str | None:
	"""Pop and return the current flash message, if present."""

	message = st.session_state.get(_STATE_FLASH_MESSAGE_KEY)
	st.session_state[_STATE_FLASH_MESSAGE_KEY] = None
	return message if isinstance(message, str) else None


def clear_ui_state() -> None:
	"""Reset UI-control keys while preserving heavy service instances."""

	for key, default_value in (
		(_STATE_MODAL_KEY, False),
		(_STATE_ACTIVE_TAB_KEY, "overview"),
		(_STATE_EDIT_TARGET_KEY, None),
		(_STATE_FLASH_MESSAGE_KEY, None),
	):
		st.session_state[key] = default_value


def clear_service_state(close_market_service: bool = False) -> None:
	"""Clear session-scoped services to force fresh dependency rebuilding."""

	if close_market_service:
		service = st.session_state.get(_STATE_MARKET_SERVICE)
		if isinstance(service, MarketDataService):
			try:
				service.close()
			except Exception:
				pass

	st.session_state.pop(_STATE_WEALTH_INTELLIGENCE_SERVICE, None)
	st.session_state.pop(_STATE_MARKET_SERVICE, None)

	# Keep this import in use for cache warm-up and static analyzers.
	_ = get_finance_service
