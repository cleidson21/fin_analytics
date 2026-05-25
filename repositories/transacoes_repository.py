"""DuckDB repository for financial transactions and ETL observability."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import duckdb
import polars as pl

from config.constants import StatusProcessamento
from config.settings import get_settings


class TransacoesRepository:
	"""Repository responsible for persisting transactions in DuckDB.

	The repository owns a single DuckDB connection and performs all writes
	inside explicit transactions to guarantee atomicity.
	"""

	def __init__(
		self,
		database_path: Path | str | None = None,
		*,
		read_only: bool = False,
	) -> None:
		settings = get_settings()
		resolved_path = Path(database_path) if database_path is not None else settings.DATABASE_PATH

		resolved_path.parent.mkdir(parents=True, exist_ok=True)
		self._connection: duckdb.DuckDBPyConnection = duckdb.connect(
			database=str(resolved_path),
			read_only=read_only,
		)

	def close(self) -> None:
		"""Close the underlying DuckDB connection."""

		self._connection.close()

	def clear_all_data(self) -> None:
		"""Remove all persisted rows so the warehouse can be rebuilt from scratch."""

		self.init_tables()
		self._connection.execute("DELETE FROM BASE_GERAL")
		self._connection.execute("DELETE FROM QUARANTINE_TRANSACTIONS")
		self._connection.execute("DELETE FROM ETL_EXECUTIONS")

	def init_tables(self) -> None:
		"""Create the repository tables if they do not already exist."""

		ddl_statements = (
			"""
			CREATE TABLE IF NOT EXISTS BASE_GERAL (
				ID_Unico VARCHAR NOT NULL,
				Data DATE NOT NULL,
				Descricao VARCHAR NOT NULL,
				Valor DECIMAL(18, 2) NOT NULL,
				Tipo VARCHAR NOT NULL,
				Categoria VARCHAR NOT NULL,
				ArquivoOrigem VARCHAR NOT NULL,
				Fonte VARCHAR NOT NULL,
				processed_at TIMESTAMP WITH TIME ZONE NOT NULL
			)
			""",
			"""
			CREATE TABLE IF NOT EXISTS QUARANTINE_TRANSACTIONS (
				ID_Unico VARCHAR NOT NULL,
				Data DATE NOT NULL,
				Descricao VARCHAR NOT NULL,
				Valor DECIMAL(18, 2) NOT NULL,
				Tipo VARCHAR NOT NULL,
				Categoria VARCHAR NOT NULL,
				ArquivoOrigem VARCHAR NOT NULL,
				Fonte VARCHAR NOT NULL,
				processed_at TIMESTAMP WITH TIME ZONE NOT NULL,
				motivo_rejeicao VARCHAR NOT NULL
			)
			""",
			"""
			CREATE TABLE IF NOT EXISTS ETL_EXECUTIONS (
				execution_id VARCHAR NOT NULL,
				started_at TIMESTAMP WITH TIME ZONE NOT NULL,
				finished_at TIMESTAMP WITH TIME ZONE NOT NULL,
				source_file VARCHAR NOT NULL,
				rows_read BIGINT NOT NULL,
				rows_inserted BIGINT NOT NULL,
				rows_duplicated BIGINT NOT NULL,
				rows_quarantined BIGINT NOT NULL,
				status VARCHAR NOT NULL,
				execution_time_ms BIGINT NOT NULL
			)
			""",
			"""
			CREATE OR REPLACE VIEW vw_monthly_cashflow AS
			WITH monthly_base AS (
				SELECT
					date_trunc('month', Data)::DATE AS period_start,
					strftime(Data, '%Y-%m') AS period_key,
					SUM(CASE WHEN Tipo = 'RECEITA' THEN Valor ELSE 0 END) AS receitas,
					SUM(CASE WHEN Tipo = 'GASTO' THEN ABS(Valor) ELSE 0 END) AS gastos
				FROM BASE_GERAL
				GROUP BY 1, 2
			)
			SELECT
				period_start,
				period_key,
				COALESCE(receitas, 0) AS receitas,
				COALESCE(gastos, 0) AS gastos,
				COALESCE(receitas, 0) - COALESCE(gastos, 0) AS saldo_liquido
			FROM monthly_base
			""",
			"""
			CREATE OR REPLACE VIEW vw_expenses_by_category AS
			WITH category_base AS (
				SELECT
					Categoria AS categoria,
					SUM(ABS(Valor)) AS total
				FROM BASE_GERAL
				WHERE Tipo = 'GASTO'
				GROUP BY 1
			),
			category_totals AS (
				SELECT SUM(total) AS total_expenses FROM category_base
			)
			SELECT
				c.categoria,
				c.total,
				CASE
					WHEN t.total_expenses IS NULL OR t.total_expenses = 0 THEN CAST(0 AS DECIMAL(18, 2))
					ELSE ROUND((c.total / t.total_expenses) * 100, 2)
				END AS percentual
			FROM category_base c
			CROSS JOIN category_totals t
			ORDER BY c.total DESC, c.categoria
			""",
			"""
			CREATE OR REPLACE VIEW vw_investments AS
			WITH investment_rows AS (
				SELECT
					Descricao,
					Valor,
					Tipo,
					Categoria
				FROM BASE_GERAL
				WHERE Tipo = 'INVESTIMENTO' OR Categoria = 'INVESTIMENTOS'
			),
			investment_summary AS (
				SELECT
					SUM(CASE WHEN regexp_matches(lower(Descricao), '(dividend|provento|jcp)') THEN ABS(Valor) ELSE 0 END) AS dividendos,
					SUM(CASE WHEN NOT regexp_matches(lower(Descricao), '(dividend|provento|jcp)') THEN ABS(Valor) ELSE 0 END) AS aportes
				FROM investment_rows
			)
			SELECT
				COALESCE(aportes, 0) AS aportes,
				COALESCE(dividendos, 0) AS dividendos,
				COALESCE(aportes, 0) + COALESCE(dividendos, 0) AS total
			FROM investment_summary
			""",
		)

		for statement in ddl_statements:
			self._connection.execute(statement)

	def filter_new_records(self, df_polars: pl.DataFrame) -> pl.DataFrame:
		"""Return records whose ``ID_Unico`` is not already persisted.

		The anti-join excludes identifiers already present in both the main and
		quarantine tables.
		"""

		if df_polars.is_empty():
			return df_polars.clone()

		self._validate_transaction_frame(df_polars)

		existing_ids = self._fetch_existing_ids()
		if not existing_ids:
			return df_polars.clone()

		return df_polars.filter(~pl.col("ID_Unico").is_in(existing_ids))

	def bulk_insert(
		self,
		df_polars: pl.DataFrame,
		df_quarantine: pl.DataFrame,
		execution_metrics: Mapping[str, Any],
	) -> None:
		"""Insert accepted and quarantined records atomically.

		The method writes transaction data, quarantine data, and the ETL
		execution record inside a single explicit DuckDB transaction. Any error
		triggers a rollback.
		"""

		self.init_tables()

		self._validate_transaction_frame(df_polars)
		if not df_quarantine.is_empty():
			self._validate_quarantine_frame(df_quarantine)

		normalized_metrics = self._normalize_execution_metrics(
			execution_metrics=execution_metrics,
			df_polars=df_polars,
			df_quarantine=df_quarantine,
		)

		self._connection.execute("BEGIN TRANSACTION")
		try:
			if not df_polars.is_empty():
				normalized_base = self._prepare_base_frame(df_polars)
				self._insert_rows(
					table_name="BASE_GERAL",
					columns=(
						"ID_Unico",
						"Data",
						"Descricao",
						"Valor",
						"Tipo",
						"Categoria",
						"ArquivoOrigem",
						"Fonte",
						"processed_at",
					),
					df=normalized_base,
				)

			if not df_quarantine.is_empty():
				normalized_quarantine = self._prepare_quarantine_frame(df_quarantine)
				self._insert_rows(
					table_name="QUARANTINE_TRANSACTIONS",
					columns=(
						"ID_Unico",
						"Data",
						"Descricao",
						"Valor",
						"Tipo",
						"Categoria",
						"ArquivoOrigem",
						"Fonte",
						"processed_at",
						"motivo_rejeicao",
					),
					df=normalized_quarantine,
				)

			self._connection.execute(
				"""
				INSERT INTO ETL_EXECUTIONS (
					execution_id,
					started_at,
					finished_at,
					source_file,
					rows_read,
					rows_inserted,
					rows_duplicated,
					rows_quarantined,
					status,
					execution_time_ms
				)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				[
					normalized_metrics["execution_id"],
					normalized_metrics["started_at"],
					normalized_metrics["finished_at"],
					normalized_metrics["source_file"],
					normalized_metrics["rows_read"],
					normalized_metrics["rows_inserted"],
					normalized_metrics["rows_duplicated"],
					normalized_metrics["rows_quarantined"],
					normalized_metrics["status"],
					normalized_metrics["execution_time_ms"],
				],
			)

			self._connection.execute("COMMIT")
		except Exception:
			self._connection.execute("ROLLBACK")
			raise

	def fetch_transactions_by_period(self, start_date: date, end_date: date) -> duckdb.DuckDBPyRelation:
		"""Fetch base transactions within an inclusive date range.

		The method returns a DuckDB relation so callers can keep the query lazy.
		"""

		query = f"""
			SELECT
				ID_Unico,
				Data,
				Descricao,
				Valor,
				Tipo,
				Categoria,
				ArquivoOrigem,
				Fonte,
				CAST(processed_at AS TIMESTAMP) AS processed_at
			FROM BASE_GERAL
			WHERE Data BETWEEN DATE '{start_date.isoformat()}' AND DATE '{end_date.isoformat()}'
			ORDER BY Data, ID_Unico
		"""
		return self._connection.sql(query)

	def fetch_quarantine_transactions(self) -> duckdb.DuckDBPyRelation:
		"""Fetch quarantined transactions without materializing them eagerly."""

		return self._connection.sql(
			"""
			SELECT
				ID_Unico,
				Data,
				Descricao,
				Valor,
				Tipo,
				Categoria,
				ArquivoOrigem,
				Fonte,
				CAST(processed_at AS TIMESTAMP) AS processed_at,
				motivo_rejeicao
			FROM QUARANTINE_TRANSACTIONS
			ORDER BY processed_at DESC, Data DESC, ID_Unico DESC
			"""
		)

	def fetch_latest_transactions(self, limit: int) -> duckdb.DuckDBPyRelation:
		"""Fetch the most recent transactions from the curated base table."""

		if limit <= 0:
			raise ValueError("limit must be greater than zero")

		query = f"""
			SELECT
				ID_Unico,
				Data,
				Descricao,
				Valor,
				Tipo,
				Categoria,
				ArquivoOrigem,
				Fonte,
				CAST(processed_at AS TIMESTAMP) AS processed_at
			FROM BASE_GERAL
			ORDER BY processed_at DESC, Data DESC, ID_Unico DESC
			LIMIT {int(limit)}
		"""
		return self._connection.sql(query)

	def fetch_monthly_expenses_by_category(self, start_date: date, end_date: date) -> duckdb.DuckDBPyRelation:
		"""Fetch monthly expense totals grouped by category for the given period."""

		query = f"""
			SELECT
				strftime(Data, '%Y-%m') AS periodo,
				Categoria AS categoria,
				SUM(ABS(Valor)) AS total
			FROM BASE_GERAL
			WHERE Tipo = 'GASTO'
				AND Data BETWEEN DATE '{start_date.isoformat()}' AND DATE '{end_date.isoformat()}'
			GROUP BY 1, 2
			ORDER BY 1, 3 DESC, 2
		"""
		return self._connection.sql(query)

	def _validate_transaction_frame(self, df_polars: pl.DataFrame) -> None:
		"""Ensure the accepted transaction frame contains the required columns."""

		required_columns = {
			"ID_Unico",
			"Data",
			"Descricao",
			"Valor",
			"Tipo",
			"Categoria",
			"ArquivoOrigem",
			"Fonte",
			"processed_at",
		}
		missing = required_columns.difference(df_polars.columns)
		if missing:
			message = ", ".join(sorted(missing))
			raise ValueError(f"df_polars is missing required columns: {message}")

	def _validate_quarantine_frame(self, df_quarantine: pl.DataFrame) -> None:
		"""Ensure the quarantine frame contains the required columns."""

		required_columns = {
			"ID_Unico",
			"Data",
			"Descricao",
			"Valor",
			"Tipo",
			"Categoria",
			"ArquivoOrigem",
			"Fonte",
			"processed_at",
			"motivo_rejeicao",
		}
		missing = required_columns.difference(df_quarantine.columns)
		if missing:
			message = ", ".join(sorted(missing))
			raise ValueError(f"df_quarantine is missing required columns: {message}")

	def _prepare_base_frame(self, df_polars: pl.DataFrame) -> pl.DataFrame:
		"""Normalize accepted rows before inserting them into DuckDB."""

		return df_polars.with_columns(
			pl.col("Tipo").cast(pl.Utf8),
			pl.col("Categoria").cast(pl.Utf8),
			pl.col("Fonte").cast(pl.Utf8),
			pl.col("ArquivoOrigem").cast(pl.Utf8),
			pl.col("Descricao").cast(pl.Utf8),
			pl.col("ID_Unico").cast(pl.Utf8),
			pl.col("processed_at").cast(pl.Utf8),
		)

	def _prepare_quarantine_frame(self, df_quarantine: pl.DataFrame) -> pl.DataFrame:
		"""Normalize quarantined rows before inserting them into DuckDB."""

		return df_quarantine.with_columns(
			pl.col("Tipo").cast(pl.Utf8),
			pl.col("Categoria").cast(pl.Utf8),
			pl.col("Fonte").cast(pl.Utf8),
			pl.col("ArquivoOrigem").cast(pl.Utf8),
			pl.col("Descricao").cast(pl.Utf8),
			pl.col("ID_Unico").cast(pl.Utf8),
			pl.col("motivo_rejeicao").cast(pl.Utf8),
			pl.col("processed_at").cast(pl.Utf8),
		)

	def _normalize_execution_metrics(
		self,
		*,
		execution_metrics: Mapping[str, Any],
		df_polars: pl.DataFrame,
		df_quarantine: pl.DataFrame,
	) -> dict[str, Any]:
		"""Normalize ETL execution metrics for persistence."""

		now = datetime.now(UTC)
		started_at = self._coerce_utc_datetime(execution_metrics.get("started_at"), default=now)
		finished_at = self._coerce_utc_datetime(execution_metrics.get("finished_at"), default=now)

		rows_inserted = self._coerce_int(execution_metrics.get("rows_inserted"), default=len(df_polars))
		rows_quarantined = self._coerce_int(
			execution_metrics.get("rows_quarantined"),
			default=len(df_quarantine),
		)
		rows_read = self._coerce_int(
			execution_metrics.get("rows_read"),
			default=rows_inserted + rows_quarantined + self._coerce_int(
				execution_metrics.get("rows_duplicated"),
				default=0,
			),
		)
		rows_duplicated = self._coerce_int(
			execution_metrics.get("rows_duplicated"),
			default=max(rows_read - rows_inserted - rows_quarantined, 0),
		)
		execution_time_ms = self._coerce_int(
			execution_metrics.get("execution_time_ms"),
			default=max(int((finished_at - started_at).total_seconds() * 1000), 0),
		)

		status_value = execution_metrics.get("status", StatusProcessamento.SUCESSO)
		if isinstance(status_value, StatusProcessamento):
			status = status_value.value
		else:
			status = str(status_value)

		execution_id = execution_metrics.get("execution_id")
		if execution_id is None or not str(execution_id).strip():
			execution_id = uuid4().hex

		source_file = execution_metrics.get("source_file")
		if source_file is None or not str(source_file).strip():
			source_file = self._infer_source_file(df_polars, df_quarantine)

		return {
			"execution_id": str(execution_id),
			"started_at": started_at,
			"finished_at": finished_at,
			"source_file": str(source_file),
			"rows_read": rows_read,
			"rows_inserted": rows_inserted,
			"rows_duplicated": rows_duplicated,
			"rows_quarantined": rows_quarantined,
			"status": status,
			"execution_time_ms": execution_time_ms,
		}

	@staticmethod
	def _infer_source_file(df_polars: pl.DataFrame, df_quarantine: pl.DataFrame) -> str:
		"""Infer a source file name from the provided data frames when needed."""

		for frame in (df_polars, df_quarantine):
			if frame.is_empty() or "ArquivoOrigem" not in frame.columns:
				continue

			first_value = frame.get_column("ArquivoOrigem").drop_nulls().head(1)
			if len(first_value) > 0:
				candidate = str(first_value.item())
				if candidate.strip():
					return candidate

		return "unknown"

	@staticmethod
	def _coerce_int(value: Any, *, default: int) -> int:
		"""Coerce a numeric value to ``int`` with a deterministic fallback."""

		if value is None:
			return default

		return int(value)

	@staticmethod
	def _coerce_utc_datetime(value: Any, *, default: datetime) -> datetime:
		"""Coerce datetime-like values to timezone-aware UTC datetimes."""

		if value is None:
			return default

		if not isinstance(value, datetime):
			raise TypeError("Execution timestamps must be datetime objects.")

		if value.tzinfo is None:
			return value.replace(tzinfo=UTC)

		return value.astimezone(UTC)

	def _fetch_existing_ids(self) -> set[str]:
		"""Fetch every persisted transaction identifier from both tables."""

		query = """
			SELECT ID_Unico FROM BASE_GERAL
			UNION
			SELECT ID_Unico FROM QUARANTINE_TRANSACTIONS
		"""
		return {str(row[0]) for row in self._connection.execute(query).fetchall()}

	def _insert_rows(self, *, table_name: str, columns: tuple[str, ...], df: pl.DataFrame) -> None:
		"""Insert a normalized frame using DuckDB executemany inside a transaction."""

		insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"
		self._connection.executemany(insert_sql, df.select(list(columns)).iter_rows())
