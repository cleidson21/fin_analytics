"""Service layer for direct file ingestion from the Streamlit frontend."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any

from config.constants import ClasseAtivo, FonteDados, StatusProcessamento
from config.settings import get_settings
from domain.categorization import Categorizer
from etl.extract import DataExtractor
from etl.load import DataLoader, LoadMetrics
from etl.wealth_extract import WealthExtractor
from etl.transform import DataTransformer
from models.wealth_dto import AssetDTO, PositionDTO
from repositories.transacoes_repository import TransacoesRepository
from repositories.wealth_repository import WealthRepository
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
		wealth_repository: WealthRepository | None = None,
		extractor: DataExtractor | None = None,
		wealth_extractor: WealthExtractor | None = None,
		transformer: DataTransformer | None = None,
		loader: DataLoader | None = None,
	) -> None:
		self._settings = get_settings()
		self._settings.ensure_directories()
		self._logger = get_logger(__name__)
		self._repository = repository or TransacoesRepository()
		self._repository.init_tables()
		self._wealth_repository = wealth_repository or WealthRepository()
		self._wealth_repository.init_wealth_tables()
		self._extractor = extractor or DataExtractor()
		self._wealth_extractor = wealth_extractor or WealthExtractor()
		self._transformer = transformer or DataTransformer(Categorizer())
		self._loader = loader or DataLoader(self._repository)

	def process_uploaded_file(
		self,
		file_bytes: bytes | bytearray | memoryview | BytesIO,
		file_name: str,
		fonte: FonteDados | str,
	) -> UploadedFileProcessingResult:
		"""Process an uploaded file through extract, transform, and load stages."""

		if not file_name or not file_name.strip():
			raise ValueError("file_name must not be empty")

		payload = self._coerce_payload(file_bytes)
		if not payload:
			raise ValueError("file_bytes must not be empty")

		provided_name = Path(file_name.strip()).name
		file_kind = self._infer_upload_kind(provided_name, fonte)
		normalized_fonte = self._normalize_fonte(fonte, file_kind)

		try:
			if file_kind == "positions":
				return self._process_positions_upload(payload, provided_name, normalized_fonte)
			if file_kind == "dividends":
				return self._process_dividends_upload(payload, provided_name, normalized_fonte)

			df_raw = self._extractor.read_bank_csv(BytesIO(payload), normalized_fonte)
			execution_id = self._build_execution_id(provided_name)
			df_transformed = self._transformer.process_raw_data(df_raw, normalized_fonte, provided_name)
			parquet_paths = self._loader.save_to_parquet(df_transformed)
			load_metrics = self._loader.load_to_database(df_transformed, execution_id)

			return self._build_result(
				file_name=provided_name,
				fonte=normalized_fonte,
				execution_id=load_metrics.execution_id,
				load_metrics=load_metrics,
				parquet_paths=parquet_paths,
			)
		except Exception as exc:
			fonte_value = fonte.value if isinstance(fonte, FonteDados) else str(fonte)
			self._logger.exception(
				"Failed to process uploaded file=%s kind=%s fonte=%s: %s",
				provided_name,
				file_kind,
				fonte_value,
				exc,
			)
			raise RuntimeError(f"Failed to process uploaded file {provided_name!r}") from exc

	def _process_positions_upload(self, payload: bytes, file_name: str, fonte: FonteDados) -> UploadedFileProcessingResult:
		"""Persist a positions snapshot into the wealth layer."""

		frame = self._wealth_extractor.extract_positions(BytesIO(payload))
		rows_read = frame.height
		for row in frame.iter_rows(named=True):
			ticker = str(row["ativo"]).strip().upper()
			quantidade = self._to_decimal(row["qtd"])
			preco_medio = self._to_decimal(row["preco_medio"])
			cotacao_atual = self._to_decimal(row["preco_atual"])
			valor_base = preco_medio * quantidade
			pnl_absoluto = (cotacao_atual - preco_medio) * quantidade
			pnl_percentual = (pnl_absoluto / valor_base * Decimal("100")) if valor_base > 0 else Decimal("0")

			self._wealth_repository.upsert_asset(
				AssetDTO(
					ticker=ticker,
					nome=ticker,
					classe_ativo=self._infer_asset_class(ticker),
					setor="NAO_INFORMADO",
				),
			)
			self._wealth_repository.update_position(
				PositionDTO(
					ticker=ticker,
					quantidade=quantidade,
					preco_medio=preco_medio,
					cotacao_atual=cotacao_atual,
					pnl_absoluto=pnl_absoluto,
					pnl_percentual=pnl_percentual,
					dividend_yield=Decimal("0"),
				),
			)

		return UploadedFileProcessingResult(
			file_name=file_name,
			fonte=fonte,
			execution_id=self._build_execution_id(file_name),
			rows_read=rows_read,
			rows_inserted=rows_read,
			rows_duplicated=0,
			rows_quarantined=0,
			status=StatusProcessamento.SUCESSO,
			parquet_paths=(),
		)

	def _process_dividends_upload(self, payload: bytes, file_name: str, fonte: FonteDados) -> UploadedFileProcessingResult:
		"""Persist dividend rows into the wealth layer."""

		frame = self._wealth_extractor.extract_dividends(BytesIO(payload))
		rows_read = frame.height
		self._ensure_dividend_table()
		for index, row in enumerate(frame.iter_rows(named=True), start=1):
			ticker = str(row["ativo"]).strip().upper()
			valor_recebido = self._to_decimal(row["recebido"])
			data_pagamento = row["data_pgto"]
			dividend_id = self._build_dividend_id(file_name, ticker, data_pagamento.isoformat(), valor_recebido, index)
			self._wealth_repository.upsert_asset(
				AssetDTO(
					ticker=ticker,
					nome=ticker,
					classe_ativo=self._infer_asset_class(ticker),
					setor="NAO_INFORMADO",
				),
			)
			self._insert_dividend(dividend_id, ticker, data_pagamento, valor_recebido)

		return UploadedFileProcessingResult(
			file_name=file_name,
			fonte=fonte,
			execution_id=self._build_execution_id(file_name),
			rows_read=rows_read,
			rows_inserted=rows_read,
			rows_duplicated=0,
			rows_quarantined=0,
			status=StatusProcessamento.SUCESSO,
			parquet_paths=(),
		)

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

	@staticmethod
	def _coerce_payload(file_bytes: bytes | bytearray | memoryview | BytesIO) -> bytes:
		"""Normalize supported upload payloads into raw bytes."""

		if isinstance(file_bytes, BytesIO):
			return file_bytes.getvalue()
		if isinstance(file_bytes, (bytes, bytearray, memoryview)):
			return bytes(file_bytes)
		raise TypeError("file_bytes must be a bytes-like object or BytesIO")

	@staticmethod
	def _normalize_fonte(fonte: FonteDados | str, file_kind: str) -> FonteDados:
		"""Coerce the upload source into a supported enum value."""

		if isinstance(fonte, FonteDados):
			return fonte

		candidate = str(fonte).strip().upper()
		if candidate in {"POSIÇÕES/ACOES", "POSIÇÕES/AÇÕES", "POSICOES/ACOES", "POSICOES/AÇÕES", "PROVENTOS"}:
			return FonteDados.MYPROFIT
		if candidate in {"NUBANK", "MYPROFIT", "MANUAL", "SISTEMA"}:
			return FonteDados(candidate)
		if file_kind in {"positions", "dividends"}:
			return FonteDados.MYPROFIT
		raise ValueError(f"Unsupported source value: {fonte!r}")

	@staticmethod
	def _infer_upload_kind(file_name: str, fonte: FonteDados | str) -> str:
		"""Infer the upload family from the file name or source label."""

		normalized_name = file_name.lower()
		normalized_source = fonte.value if isinstance(fonte, FonteDados) else str(fonte).lower()
		combined = f"{normalized_name} {normalized_source}"
		if any(marker in combined for marker in ("proventos", "dividendo")):
			return "dividends"
		if any(marker in combined for marker in ("tableexport", "posi", "acoes", "ações")):
			return "positions"
		return "bank"

	@staticmethod
	def _infer_asset_class(ticker: str) -> ClasseAtivo:
		"""Infer a conservative asset class for broker snapshots."""

		upper_ticker = ticker.strip().upper()
		if upper_ticker.endswith(".SA"):
			return ClasseAtivo.ACAO_BR
		if upper_ticker.endswith("11"):
			return ClasseAtivo.FII
		return ClasseAtivo.CAIXA

	@staticmethod
	def _build_dividend_id(file_name: str, ticker: str, data_pagamento: str, valor_recebido: Decimal, row_number: int) -> str:
		"""Create a deterministic identifier for a dividend record."""

		payload = f"file={file_name}|ticker={ticker}|data={data_pagamento}|valor={valor_recebido}|row={row_number}"
		return sha256(payload.encode("utf-8")).hexdigest()

	def _ensure_dividend_table(self) -> None:
		"""Create the dividend fact table when it is missing."""

		self._wealth_repository._connection.execute(  # noqa: SLF001
			"""
			CREATE TABLE IF NOT EXISTS FACT_DIVIDENDS (
				id_dividendo VARCHAR PRIMARY KEY,
				ticker VARCHAR NOT NULL,
				data_pagamento DATE NOT NULL,
				valor_recebido DECIMAL(18, 2) NOT NULL,
				updated_at TIMESTAMP WITH TIME ZONE NOT NULL
			)
			""",
		)

	def _insert_dividend(self, dividend_id: str, ticker: str, data_pagamento: Any, valor_recebido: Decimal) -> None:
		"""Persist a dividend row with idempotent replacement semantics."""

		now = datetime.now(UTC)
		try:
			self._wealth_repository._connection.execute("BEGIN TRANSACTION")  # noqa: SLF001
			self._wealth_repository._connection.execute(  # noqa: SLF001
				"DELETE FROM FACT_DIVIDENDS WHERE id_dividendo = ?",
				[dividend_id],
			)
			self._wealth_repository._connection.execute(  # noqa: SLF001
				"""
				INSERT INTO FACT_DIVIDENDS (
					id_dividendo,
					ticker,
					data_pagamento,
					valor_recebido,
					updated_at
				)
				VALUES (?, ?, ?, ?, ?)
				""",
				[dividend_id, ticker, data_pagamento, valor_recebido, now],
			)
			self._wealth_repository._connection.execute("COMMIT")  # noqa: SLF001
		except Exception as exc:
			try:
				self._wealth_repository._connection.execute("ROLLBACK")  # noqa: SLF001
			except Exception:
				pass
			raise RuntimeError(f"Failed to persist dividend for {ticker} on {data_pagamento}: {exc}") from exc

	@staticmethod
	def _to_decimal(value: object) -> Decimal:
		"""Convert mixed numeric inputs to ``Decimal`` safely."""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			return Decimal(value)
		if isinstance(value, float):
			return Decimal(str(value))
		if value is None:
			return Decimal("0")
		return Decimal(str(value))