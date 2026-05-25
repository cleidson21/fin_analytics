"""Service layer for direct file ingestion from the Streamlit frontend."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import tempfile
from typing import Any

from config.constants import FonteDados, StatusProcessamento
from config.settings import get_settings
from domain.categorization import Categorizer
from etl.extract import DataExtractor
from etl.load import DataLoader, LoadMetrics
from etl.transform import DataTransformer
from pydantic import ValidationError
from repositories.transacoes_repository import TransacoesRepository
from utils.logger import get_logger


@dataclass(frozen=True, slots=True)
class UploadedFileProcessingResult:
	"""Structured metrics returned after an uploaded file is processed."""

	file_name: str
	fonte: FonteDados
	execution_id: str
	rows_read: int
	rows_inserted: int
	rows_duplicated: int
	rows_quarantined: int
	status: StatusProcessamento
	parquet_paths: tuple[str, ...] = ()

	def to_dict(self) -> dict[str, Any]:
		"""Convert the result into a JSON-friendly mapping for Streamlit."""

		return {
			"file_name": self.file_name,
			"fonte": self.fonte.value,
			"execution_id": self.execution_id,
			"rows_read": self.rows_read,
			"rows_inserted": self.rows_inserted,
			"rows_duplicated": self.rows_duplicated,
			"rows_quarantined": self.rows_quarantined,
			"status": self.status.value,
			"parquet_paths": list(self.parquet_paths),
		}


class IngestionService:
	"""Bridge uploaded Streamlit files into the ETL pipeline."""

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

	def process_uploaded_file(self, file_bytes: bytes, file_name: str, fonte: FonteDados) -> UploadedFileProcessingResult:
		"""Process an uploaded file through extract, transform, and load stages."""

		if not file_name or not file_name.strip():
			raise ValueError("file_name must not be empty")

		if not isinstance(file_bytes, (bytes, bytearray, memoryview)):
			raise TypeError("file_bytes must be a bytes-like object")

		if not isinstance(fonte, FonteDados):
			try:
				fonte = FonteDados(str(fonte))
			except (TypeError, ValueError, ValidationError) as exc:
				raise ValueError(f"Unsupported source value: {fonte!r}") from exc

		payload = bytes(file_bytes)
		if not payload:
			raise ValueError("file_bytes must not be empty")

		provided_name = Path(file_name.strip()).name
		suffix = Path(provided_name).suffix or ".csv"
		temp_path: Path | None = None

		try:
			with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, prefix="uploaded_", dir=self._settings.STAGING_DIR, delete=False) as temp_file:
				temp_file.write(payload)
				temp_file.flush()
				temp_path = Path(temp_file.name)

			df_raw = self._extractor.read_bank_csv(temp_path, fonte)
			execution_id = self._build_execution_id(provided_name)
			df_transformed = self._transformer.process_raw_data(df_raw, fonte, provided_name)
			parquet_paths = self._loader.save_to_parquet(df_transformed)
			load_metrics = self._loader.load_to_database(df_transformed, execution_id)

			return self._build_result(
				file_name=provided_name,
				fonte=fonte,
				execution_id=load_metrics.execution_id,
				load_metrics=load_metrics,
				parquet_paths=parquet_paths,
			)
		except Exception as exc:
			self._logger.exception("Failed to process uploaded file=%s fonte=%s: %s", provided_name, fonte.value, exc)
			raise RuntimeError(f"Failed to process uploaded file {provided_name!r}") from exc
		finally:
			if temp_path is not None:
				try:
					temp_path.unlink(missing_ok=True)
				except Exception:
					self._logger.warning("Unable to remove temporary upload file: %s", temp_path)

	@staticmethod
	def _build_execution_id(file_name: str) -> str:
		"""Create a deterministic-friendly execution identifier for one upload."""

		return f"{Path(file_name).stem}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}"

	@staticmethod
	def _build_result(
		*,
		file_name: str,
		fonte: FonteDados,
		execution_id: str,
		load_metrics: LoadMetrics,
		parquet_paths: list[Path],
	) -> UploadedFileProcessingResult:
		"""Build a serializable result from the ETL load metrics."""

		return UploadedFileProcessingResult(
			file_name=file_name,
			fonte=fonte,
			execution_id=execution_id,
			rows_read=load_metrics.rows_read,
			rows_inserted=load_metrics.rows_inserted,
			rows_duplicated=load_metrics.rows_duplicated,
			rows_quarantined=load_metrics.rows_quarantined,
			status=load_metrics.status,
			parquet_paths=tuple(str(path) for path in parquet_paths),
		)