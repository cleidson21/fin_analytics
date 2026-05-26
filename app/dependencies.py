"""Dependency factories for the Streamlit frontend.

The frontend should depend on factories instead of constructing repository and
service instances inline so Streamlit can reuse cached resources efficiently.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import sys
from typing import TypeVar

import streamlit as st

# Ensure repository root is importable when running `streamlit run app/main.py`.
_APP_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _APP_DIR.parent
if str(_REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(_REPO_ROOT))

from config.settings import get_settings
from domain.categorization import Categorizer
from etl.extract import DataExtractor
from etl.load import DataLoader
from etl.transform import DataTransformer
from repositories.analytics_repository import AnalyticsRepository
from repositories.transacoes_repository import TransacoesRepository
from repositories.wealth_repository import WealthRepository
from services.ingestion_service import IngestionService
from services.finance_service import FinanceService
from services.goals_service import GoalsService

_T = TypeVar("_T")


def _get_session_resource(key: str, factory: Callable[[], _T]) -> _T:
	"""Return a Streamlit-session-scoped resource, with cache fallback outside Streamlit."""

	try:
		state = st.session_state
	except Exception:
		return factory()

	if key not in state:
		state[key] = factory()
	return state[key]


def get_transacoes_repository() -> TransacoesRepository:
	"""Return a cached DuckDB repository instance.

	The repository is initialized once per process and reused by Streamlit
	across reruns to avoid reconnecting and recreating views repeatedly.
	"""

	return _get_session_resource(
		"fin_analytics_transacoes_repository",
		lambda: _build_transacoes_repository(),
	)


def _build_transacoes_repository() -> TransacoesRepository:
	"""Create the shared transactions repository once."""

	settings = get_settings()
	repository = TransacoesRepository(database_path=settings.DATABASE_PATH)
	repository.init_tables()
	return repository


def get_finance_service() -> FinanceService:
	"""Return a cached analytical service instance.

	Returns:
		A ready-to-use ``FinanceService`` backed by the shared repository.
	"""

	return _get_session_resource(
		"fin_analytics_finance_service",
		lambda: FinanceService(get_transacoes_repository()),
	)


def get_goals_service() -> GoalsService:
	"""Return a cached GoalsService instance backed by the shared repository."""

	return _get_session_resource(
		"fin_analytics_goals_service",
		lambda: GoalsService(get_wealth_repository()),
	)


def get_ingestion_service() -> IngestionService:
	"""Return a session-safe ingestion service for uploaded files."""

	return _get_session_resource(
		"fin_analytics_ingestion_service",
		lambda: IngestionService(
			repository=get_transacoes_repository(),
			extractor=DataExtractor(),
			transformer=DataTransformer(Categorizer()),
			loader=DataLoader(get_transacoes_repository()),
		),
	)


def get_wealth_repository() -> WealthRepository:
	"""Return a cached wealth repository instance backed by the shared DuckDB file."""

	return _get_session_resource(
		"fin_analytics_wealth_repository",
		lambda: _build_wealth_repository(),
	)


def _build_wealth_repository() -> WealthRepository:
	"""Create the shared wealth repository once per Streamlit session."""

	settings = get_settings()
	repository = WealthRepository(database_path=settings.DATABASE_PATH)
	repository.init_wealth_tables()
	return repository


def get_analytics_repository() -> AnalyticsRepository:
	"""Return a cached analytics read repository."""

	return _get_session_resource(
		"fin_analytics_analytics_repository",
		lambda: AnalyticsRepository(
			transacoes_repository=get_transacoes_repository(),
			wealth_repository=get_wealth_repository(),
		),
	)
