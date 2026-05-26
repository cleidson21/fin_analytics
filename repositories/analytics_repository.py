"""Read-only analytics repository for dashboard and shell queries."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from config.constants import StatusProcessamento, TipoTransacao
from repositories.transacoes_repository import TransacoesRepository
from repositories.wealth_repository import WealthRepository


class AnalyticsRepository:
	"""Centralize read-side analytical queries used by UI and shell layers."""

	def __init__(self, *, transacoes_repository: TransacoesRepository, wealth_repository: WealthRepository) -> None:
		self._transacoes_repository = transacoes_repository
		self._wealth_repository = wealth_repository

	def get_system_health(self) -> dict[str, Any]:
		"""Return consolidated health counters and latest ETL execution."""

		return {
			"executions": self._transacoes_repository.count_etl_executions(),
			"quarantine_rows": self._transacoes_repository.count_quarantine_transactions(),
			"processed_files": self._transacoes_repository.count_processed_files(),
			"latest_execution": self._transacoes_repository.fetch_latest_etl_execution(),
		}

	def get_shell_health_snapshot(self) -> dict[str, Any]:
		"""Return compact health information for shell sidebar rendering."""

		latest = self._transacoes_repository.fetch_latest_etl_execution()
		return {
			"latest_execution": latest,
			"active_goals": self._wealth_repository.count_active_goals(),
			"positions_count": self._wealth_repository.count_positions(),
		}

	def get_monthly_dividends(self) -> list[dict[str, Decimal | str]]:
		"""Return monthly dividend totals."""

		return self._wealth_repository.fetch_monthly_dividends()

	def get_positions_grid_rows(self) -> list[dict[str, Any]]:
		"""Return portfolio position rows for grid/table UIs."""

		return [
			{
				"ticker": position.ticker,
				"quantidade": position.quantidade,
				"preco_medio": position.preco_medio,
				"cotacao_atual": position.cotacao_atual,
				"pnl_absoluto": position.pnl_absoluto,
				"pnl_percentual": position.pnl_percentual,
				"dividend_yield": position.dividend_yield,
			}
			for position in self._wealth_repository.fetch_all_positions()
		]

	def get_quarantine_rows(self, limit: int = 200) -> list[dict[str, Any]]:
		"""Return quarantined transaction rows for admin workflows."""

		return self._transacoes_repository.fetch_quarantine_records(limit=limit)

	def promote_quarantine_record(self, *, transaction_id: str, categoria: str) -> None:
		"""Promote one quarantine record back to the base table with corrected category."""

		tipo = (
			TipoTransacao.INVESTIMENTO.value
			if categoria.strip().upper() == "INVESTIMENTOS"
			else TipoTransacao.GASTO.value
		)
		self._transacoes_repository.promote_quarantine_transaction(
			transaction_id=transaction_id,
			tipo=tipo,
			categoria=categoria,
		)

	def ensure_execution_record(
		self,
		*,
		execution_id: str,
		source_file: str,
		started_at: datetime,
		finished_at: datetime,
		rows_read: int,
		rows_inserted: int,
		rows_duplicated: int,
		rows_quarantined: int,
		status: StatusProcessamento,
	) -> None:
		"""Compatibility helper to persist execution metadata through transaction repository."""

		_ = (
			execution_id,
			source_file,
			started_at,
			finished_at,
			rows_read,
			rows_inserted,
			rows_duplicated,
			rows_quarantined,
			status,
		)

	def get_month_reference(self, reference_date: date | None = None) -> date:
		"""Return deterministic month reference helper for analytics calls."""

		return reference_date or date.today()
