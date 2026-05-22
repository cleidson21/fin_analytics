"""DuckDB repository for financial transactions and ETL observability."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
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
