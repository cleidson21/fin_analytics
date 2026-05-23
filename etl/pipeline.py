"""End-to-end ETL pipeline orchestration for raw financial files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from config.constants import FonteDados, StatusProcessamento
from config.settings import get_settings
from domain.categorization import Categorizer
from etl.extract import DataExtractor
from etl.load import DataLoader, LoadMetrics
from etl.transform import DataTransformer
from repositories.transacoes_repository import TransacoesRepository
from utils.logger import get_logger


@dataclass(frozen=True, slots=True)
class PipelineExecutionResult:
	"""Summary of the ETL pipeline execution."""

	files_seen: int
	files_processed: int
	files_skipped: int
	files_failed: int
	rows_read: int
	rows_inserted: int
	rows_duplicated: int
	rows_quarantined: int


class ETLPipeline:
	"""Orchestrate extraction, transformation, loading and audit logging."""

	def __init__(
		self,
		repository: TransacoesRepository | None = None,
		extractor: DataExtractor | None = None,
		transformer: DataTransformer | None = None,
		loader: DataLoader | None = None,
	) -> None:
		self._settings = get_settings()
		self._settings.ensure_directories()
		self._logger = get_logger(__name__)
		self._repository = repository or TransacoesRepository()
		self._repository.init_tables()
		self._extractor = extractor or DataExtractor()
		self._transformer = transformer or DataTransformer(Categorizer())
		self._loader = loader or DataLoader(self._repository)

	def run(self, raw_dir: Path | None = None) -> PipelineExecutionResult:
		"""Execute the pipeline over every CSV file found in ``raw_dir``."""

		input_dir = raw_dir or self._settings.RAW_DIR
		files = sorted(path for path in input_dir.rglob("*.csv") if path.is_file())

		summary = {
			"files_seen": len(files),
			"files_processed": 0,
			"files_skipped": 0,
			"files_failed": 0,
			"rows_read": 0,
			"rows_inserted": 0,
			"rows_duplicated": 0,
			"rows_quarantined": 0,
		}

		for file_path in files:
			if self._already_processed(file_path):
				self._logger.info("Skipping already processed file: %s", file_path)
				summary["files_skipped"] += 1
				continue

			execution_id = self._build_execution_id(file_path)
			start_time = datetime.now(UTC)
			try:
				fonte = self._infer_source(file_path)
				df_raw = self._extractor.read_bank_csv(file_path, fonte)
				df_transformed = self._transformer.process_raw_data(df_raw, fonte, file_path.name)
				parquet_paths = self._loader.save_to_parquet(df_transformed)
				load_metrics = self._loader.load_to_database(df_transformed, execution_id)

				summary["files_processed"] += 1
				summary["rows_read"] += load_metrics.rows_read
				summary["rows_inserted"] += load_metrics.rows_inserted
				summary["rows_duplicated"] += load_metrics.rows_duplicated
				summary["rows_quarantined"] += load_metrics.rows_quarantined

				self._logger.info(
					"Processed file=%s parquet_parts=%s rows_read=%s rows_inserted=%s rows_quarantined=%s",
					file_path.name,
					len(parquet_paths),
					load_metrics.rows_read,
					load_metrics.rows_inserted,
					load_metrics.rows_quarantined,
				)
			except Exception as exc:
				summary["files_failed"] += 1
				self._logger.exception("Failed processing file=%s: %s", file_path, exc)
				self._record_failed_execution(file_path, execution_id, start_time, exc)

		result = PipelineExecutionResult(**summary)
		print(result)
		self._logger.info("ETL summary: %s", result)
		return result

	def _already_processed(self, file_path: Path) -> bool:
		"""Return ``True`` when the file already has a successful execution."""

		self._repository.init_tables()
		query = """
			SELECT 1
			FROM ETL_EXECUTIONS
			WHERE source_file = ? AND status = ?
			LIMIT 1
		"""
		row = self._repository._connection.execute(
			query,
			[file_path.name, StatusProcessamento.SUCESSO.value],
		).fetchone()
		return row is not None

	@staticmethod
	def _build_execution_id(file_path: Path) -> str:
		"""Create a deterministic execution identifier for the run."""

		return f"{file_path.stem}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}"

	@staticmethod
	def _infer_source(file_path: Path) -> FonteDados:
		"""Infer the data source from the file path or name."""

		candidate = file_path.as_posix().lower()
		if "myprofit" in candidate:
			return FonteDados.MYPROFIT
		if "manual" in candidate:
			return FonteDados.MANUAL
		if "sistema" in candidate:
			return FonteDados.SISTEMA
		return FonteDados.NUBANK

	def _record_failed_execution(
		self,
		file_path: Path,
		execution_id: str,
		started_at: datetime,
		error: Exception,
	) -> None:
		"""Persist a failed execution row for observability and auditability."""

		try:
			self._repository.bulk_insert(
				pl.DataFrame(schema={
					"ID_Unico": pl.Utf8,
					"Data": pl.Date,
					"Descricao": pl.Utf8,
					"Valor": pl.Decimal(18, 2),
					"Tipo": pl.Utf8,
					"Categoria": pl.Utf8,
					"ArquivoOrigem": pl.Utf8,
					"Fonte": pl.Utf8,
					"processed_at": pl.Datetime("us", time_zone="UTC"),
				}),
				pl.DataFrame(schema={
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
				}),
				{
					"execution_id": execution_id,
					"started_at": started_at,
					"finished_at": datetime.now(UTC),
					"source_file": file_path.name,
					"rows_read": 0,
					"rows_inserted": 0,
					"rows_duplicated": 0,
					"rows_quarantined": 0,
					"status": StatusProcessamento.ERRO,
					"execution_time_ms": 0,
				},
			)
		except Exception:
			self._logger.exception("Unable to record failed execution for %s", file_path)

	def close(self) -> None:
		"""Close the underlying repository connection."""

		self._repository.close()


if __name__ == "__main__":
	pipeline = ETLPipeline()
	try:
		pipeline.run()
	finally:
		pipeline.close()
