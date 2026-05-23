"""Dependency factories for the Streamlit frontend.

The frontend should depend on factories instead of constructing repository and
service instances inline so Streamlit can reuse cached resources efficiently.
"""

from __future__ import annotations

from functools import lru_cache

from config.settings import get_settings
from repositories.transacoes_repository import TransacoesRepository
from services.finance_service import FinanceService


@lru_cache(maxsize=1)
def get_transacoes_repository() -> TransacoesRepository:
	"""Return a cached DuckDB repository instance.

	The repository is initialized once per process and reused by Streamlit
	across reruns to avoid reconnecting and recreating views repeatedly.
	"""

	settings = get_settings()
	repository = TransacoesRepository(database_path=settings.DATABASE_PATH)
	repository.init_tables()
	return repository


@lru_cache(maxsize=1)
def get_finance_service() -> FinanceService:
	"""Return a cached analytical service instance.

	Returns:
		A ready-to-use ``FinanceService`` backed by the shared repository.
	"""

	return FinanceService(get_transacoes_repository())
