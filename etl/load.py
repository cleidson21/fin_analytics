"""Loading layer for persisted curated transactions and quarantine data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from config.constants import CategoriaFallback, StatusProcessamento, TipoTransacao
from config.settings import get_settings
from repositories.transacoes_repository import TransacoesRepository


@dataclass(frozen=True, slots=True)
class LoadMetrics:
	"""Structured metrics returned by the loading stage."""

	rows_read: int
	rows_inserted: int
	rows_duplicated: int
	rows_quarantined: int
	status: StatusProcessamento
	execution_id: str


class DataLoader:
	"""Persist transformed transactions to both Parquet and DuckDB."""

	def __init__(self, repository: TransacoesRepository) -> None:
		self._repository = repository
		self._settings = get_settings()
		self._settings.ensure_directories()

	def save_to_parquet(self, df: pl.DataFrame) -> list[Path]:
		"""Persist a dataframe into year/month partitioned Parquet files.

		Returns:
			The list of written Parquet file paths.
		"""

		if df.is_empty():
			return []

		required_columns = {"Data"}
		missing = required_columns.difference(df.columns)
		if missing:
			raise ValueError(f"Dataframe missing required columns for Parquet export: {', '.join(sorted(missing))}")

		prepared = df.with_columns(
			pl.col("Data").cast(pl.Date),
			pl.col("Data").dt.year().alias("ano"),
			pl.col("Data").dt.month().alias("mes"),
		)

		written_paths: list[Path] = []
		for year_month, group in prepared.partition_by(["ano", "mes"], as_dict=True).items():
			ano, mes = year_month
			destination_dir = self._settings.PROCESSED_DIR / f"ano={ano:04d}" / f"mes={mes:02d}"
			destination_dir.mkdir(parents=True, exist_ok=True)

			output_file = destination_dir / f"transactions_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}.parquet"
			group.drop(["ano", "mes"]).write_parquet(output_file)
			written_paths.append(output_file)

		return written_paths

	def load_to_database(self, df: pl.DataFrame, execution_id: str) -> LoadMetrics:
		"""Split valid and quarantined rows and persist them via the repository."""

		self._repository.init_tables()
		rows_read = df.height
		if rows_read == 0:
			self._repository.bulk_insert(
				pl.DataFrame(schema=df.schema),
				pl.DataFrame(schema=self._quarantine_schema()),
				self._metrics_payload(
					execution_id=execution_id,
					rows_read=0,
					rows_inserted=0,
					rows_duplicated=0,
					rows_quarantined=0,
					status=StatusProcessamento.IGNORADO,
					source_file="unknown",
				),
			)
			return LoadMetrics(0, 0, 0, 0, StatusProcessamento.IGNORADO, execution_id)

		self._validate_required_columns(df)
		quarantine_mask = self._build_quarantine_mask(df)
		df_quarantine_source = df.filter(quarantine_mask)
		df_valid_source = df.filter(~quarantine_mask)

		df_valid = self._prepare_for_database(df_valid_source, quarantine=False)
		df_quarantine = self._prepare_for_database(df_quarantine_source, quarantine=True)

		filtered_valid = self._repository.filter_new_records(df_valid)
		rows_inserted = filtered_valid.height
		rows_duplicated = max(df_valid.height - rows_inserted, 0)
		rows_quarantined = df_quarantine.height

		source_file = self._infer_source_file(df)
		status = StatusProcessamento.SUCESSO
		self._repository.bulk_insert(
			filtered_valid,
			df_quarantine,
			self._metrics_payload(
				execution_id=execution_id,
				rows_read=rows_read,
				rows_inserted=rows_inserted,
				rows_duplicated=rows_duplicated,
				rows_quarantined=rows_quarantined,
				status=status,
				source_file=source_file,
			),
		)
		return LoadMetrics(rows_read, rows_inserted, rows_duplicated, rows_quarantined, status, execution_id)

	def _build_quarantine_mask(self, df: pl.DataFrame) -> pl.Series:
		"""Identify rows that must be routed to quarantine."""

		category = pl.col("Categoria").cast(pl.Utf8).fill_null("")
		tipo = pl.col("Tipo").cast(pl.Utf8).fill_null("")
		return df.select(
			((category == CategoriaFallback.NAO_CLASSIFICADO.value) | (tipo == TipoTransacao.REVISAO_MANUAL.value)).alias("quarantine")
		).to_series()

	def _prepare_for_database(self, df: pl.DataFrame, *, quarantine: bool) -> pl.DataFrame:
		"""Normalize the dataframe columns before database insertion."""

		if df.is_empty():
			return df

		if quarantine:
			return df.with_columns(
				pl.when(pl.col("Categoria") == CategoriaFallback.NAO_CLASSIFICADO.value)
				.then(pl.lit("motivo_regra_quarentena"))
				.otherwise(pl.lit("motivo_regra_quarentena"))
				.alias("motivo_rejeicao")
			)

		return df

	@staticmethod
	def _validate_required_columns(df: pl.DataFrame) -> None:
		"""Validate the columns required by the loading stage."""

		required_columns = {"ID_Unico", "Data", "Descricao", "Valor", "Tipo", "Categoria", "ArquivoOrigem", "Fonte", "processed_at"}
		missing = sorted(required_columns.difference(df.columns))
		if missing:
			raise ValueError(f"Dataframe missing required load columns: {', '.join(missing)}")

	@staticmethod
	def _infer_source_file(df: pl.DataFrame) -> str:
		"""Infer a source file name from the incoming frame when available."""

		if "ArquivoOrigem" not in df.columns or df.is_empty():
			return "unknown"

		first_value = df.get_column("ArquivoOrigem").drop_nulls().head(1)
		if len(first_value) == 0:
			return "unknown"

		candidate = str(first_value.item())
		return candidate if candidate.strip() else "unknown"

	@staticmethod
	def _quarantine_schema() -> dict[str, pl.DataType]:
		"""Return the quarantine schema used for empty-frame inserts."""

		return {
			"ID_Unico": pl.Utf8,
			"Data": pl.Date,
			"Descricao": pl.Utf8,
			"Valor": pl.Decimal(18, 2),
			"Tipo": pl.Utf8,
			"Categoria": pl.Utf8,
			"ArquivoOrigem": pl.Utf8,
			"Fonte": pl.Utf8,
			"processed_at": pl.Datetime("us", time_zone="UTC"),
			"motivo_rejeicao": pl.Utf8,
		}

	@staticmethod
	def _metrics_payload(
		*,
		execution_id: str,
		rows_read: int,
		rows_inserted: int,
		rows_duplicated: int,
		rows_quarantined: int,
		status: StatusProcessamento,
		source_file: str,
	) -> dict[str, Any]:
		"""Build the payload expected by the repository execution audit."""

		return {
			"execution_id": execution_id,
			"started_at": datetime.now(UTC),
			"finished_at": datetime.now(UTC),
			"source_file": source_file,
			"rows_read": rows_read,
			"rows_inserted": rows_inserted,
			"rows_duplicated": rows_duplicated,
			"rows_quarantined": rows_quarantined,
			"status": status,
			"execution_time_ms": 0,
		}
