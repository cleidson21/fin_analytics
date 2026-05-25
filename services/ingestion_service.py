"""Service layer for direct file ingestion from the Streamlit frontend."""

from __future__ import annotations

from csv import DictReader
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

from config.constants import ClasseAtivo, FonteDados, StatusProcessamento
from config.settings import get_settings
from domain.categorization import Categorizer
from etl.extract import DataExtractor
from etl.load import DataLoader, LoadMetrics
from etl.transform import DataTransformer
from etl.wealth_extract import WealthExtractor
from models.wealth_dto import AssetDTO, PositionDTO
from repositories.transacoes_repository import TransacoesRepository
from repositories.wealth_repository import WealthRepository
from utils.logger import get_logger
from utils.parsers import clean_csv_cell, normalize_csv_header, parse_br_currency


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
	error_message: str | None = None

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
			"error_message": self.error_message,
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

		provided_name = Path(file_name.strip()).name if file_name and file_name.strip() else "uploaded.csv"
		execution_id = self._build_execution_id(provided_name)

		try:
			payload = self._coerce_payload(file_bytes)
			if not payload:
				raise ValueError("file_bytes must not be empty")

			resolved_fonte = self._normalize_fonte(fonte, payload, provided_name)
			file_kind = self._detect_file_kind(payload, provided_name)

			if file_kind == "bank":
				return self._process_bank_upload(payload, provided_name, resolved_fonte, execution_id)
			if file_kind == "positions":
				return self._process_positions_upload(payload, provided_name, resolved_fonte, execution_id)
			if file_kind == "dividends":
				return self._process_dividends_upload(payload, provided_name, resolved_fonte, execution_id)

			raise ValueError(f"Could not route uploaded file {provided_name!r} to a supported ingestion flow")
		except Exception as exc:
			self._logger.exception("Failed to process uploaded file=%s: %s", provided_name, exc)
			return self._error_result(
				file_name=provided_name,
				fonte=self._safe_fonte(fonte),
				execution_id=execution_id,
				error_message=str(exc),
			)

	def _process_bank_upload(
		self,
		payload: bytes,
		file_name: str,
		fonte: FonteDados,
		execution_id: str,
	) -> UploadedFileProcessingResult:
		"""Run the bank statement ETL using the existing extract/transform/load pipeline."""

		frame = self._extractor.read_bank_csv(BytesIO(payload), fonte)
		rows_read = frame.height
		transformed = self._transformer.process_raw_data(frame, fonte, file_name)
		parquet_paths = self._loader.save_to_parquet(transformed)
		load_metrics = self._loader.load_to_database(transformed, execution_id)
		return self._build_result(
			file_name=file_name,
			fonte=fonte,
			execution_id=load_metrics.execution_id,
			load_metrics=load_metrics,
			parquet_paths=parquet_paths,
		)

	def _process_positions_upload(
		self,
		payload: bytes,
		file_name: str,
		fonte: FonteDados,
		execution_id: str,
	) -> UploadedFileProcessingResult:
		"""Persist a positions snapshot into the wealth layer."""

		frame = self._wealth_extractor.extract_nuinvest_positions(payload)
		rows_read = frame.height
		inserted_rows = 0

		for row in frame.iter_rows(named=True):
			ticker = self._clean_ticker(row.get("ativo"))
			quantidade = self._to_decimal(row.get("qtd"))
			preco_medio = self._to_decimal(row.get("preco_medio"))
			preco_atual = self._to_decimal(row.get("preco_atual"))
			valor_investido = self._to_decimal(row.get("total_investido"))

			if valor_investido == Decimal("0") and quantidade > 0:
				valor_investido = preco_medio * quantidade

			pnl_absoluto = (preco_atual - preco_medio) * quantidade
			pnl_percentual = (pnl_absoluto / valor_investido * Decimal("100")) if valor_investido > 0 else Decimal("0")

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
					cotacao_atual=preco_atual,
					pnl_absoluto=pnl_absoluto,
					pnl_percentual=pnl_percentual,
					dividend_yield=Decimal("0"),
				),
			)
			inserted_rows += 1

		return UploadedFileProcessingResult(
			file_name=file_name,
			fonte=fonte,
			execution_id=execution_id,
			rows_read=rows_read,
			rows_inserted=inserted_rows,
			rows_duplicated=0,
			rows_quarantined=0,
			status=StatusProcessamento.SUCESSO,
			parquet_paths=(),
		)

	def _process_dividends_upload(
		self,
		payload: bytes,
		file_name: str,
		fonte: FonteDados,
		execution_id: str,
	) -> UploadedFileProcessingResult:
		"""Persist dividend rows into the wealth layer."""

		rows = self._read_dividend_rows(payload)
		rows_read = len(rows)
		inserted_rows = 0
		self._ensure_dividend_table()

		for index, row in enumerate(rows, start=1):
			ticker = self._clean_ticker(row.get("ativo"))
			valor_recebido = self._to_decimal(row.get("recebido"))
			data_pagamento = self._parse_br_date(row.get("data_pgto") or row.get("data_pagamento") or row.get("data"))
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
			inserted_rows += 1

		return UploadedFileProcessingResult(
			file_name=file_name,
			fonte=fonte,
			execution_id=execution_id,
			rows_read=rows_read,
			rows_inserted=inserted_rows,
			rows_duplicated=0,
			rows_quarantined=0,
			status=StatusProcessamento.SUCESSO,
			parquet_paths=(),
		)

	def _read_dividend_rows(self, payload: bytes) -> list[dict[str, str]]:
		"""Parse a proventos export into a list of normalized dictionaries."""

		text = self._decode_text(payload)
		clean_text = "\n".join(line for line in text.splitlines() if line.strip())
		if not clean_text.strip():
			raise ValueError("CSV file is empty: proventos.csv")

		delimiter = self._detect_delimiter(clean_text)
		reader = DictReader(StringIO(clean_text), delimiter=delimiter)
		rows: list[dict[str, str]] = []
		for raw_row in reader:
			normalized_row: dict[str, str] = {}
			for key, value in raw_row.items():
				normalized_row[normalize_csv_header(key).replace(" ", "_")] = clean_csv_cell(value)
			rows.append(normalized_row)

		if not rows:
			raise ValueError("CSV file has no data rows: proventos.csv")
		return rows

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
	def _error_result(
		*,
		file_name: str,
		fonte: FonteDados,
		execution_id: str,
		error_message: str,
	) -> UploadedFileProcessingResult:
		"""Build a failure result that the UI can surface immediately."""

		return UploadedFileProcessingResult(
			file_name=file_name,
			fonte=fonte,
			execution_id=execution_id,
			rows_read=0,
			rows_inserted=0,
			rows_duplicated=0,
			rows_quarantined=0,
			status=StatusProcessamento.ERRO,
			parquet_paths=(),
			error_message=error_message,
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
	def _decode_text(payload: bytes) -> str:
		"""Decode raw CSV bytes using the common encodings seen in exports."""

		for encoding in ("utf-8-sig", "utf-8", "latin1"):
			try:
				return payload.decode(encoding)
			except UnicodeDecodeError:
				continue
		raise UnicodeDecodeError("utf-8", b"", 0, 1, "Unable to decode CSV buffer")

	@staticmethod
	def _detect_delimiter(sample_text: str) -> str:
		"""Detect the most likely delimiter among comma and semicolon."""

		first_lines = [line for line in sample_text.splitlines() if line.strip()][:5]
		if not first_lines:
			return ";"

		semicolon_count = sum(line.count(";") for line in first_lines)
		comma_count = sum(line.count(",") for line in first_lines)
		return ";" if semicolon_count >= comma_count else ","

	def _detect_file_kind(self, payload: bytes, file_name: str) -> str:
		"""Route the upload based on the in-memory CSV header and file name."""

		headers = self._read_headers(payload)
		normalized_headers = {normalize_csv_header(header).replace(" ", "_") for header in headers if header}
		file_name_lower = file_name.lower()

		if {"data", "descricao", "valor"}.issubset(normalized_headers):
			return "bank"
		if {"ativo", "qtd", "preco_medio", "preco_atual"}.intersection(normalized_headers):
			return "positions"
		if {"ativo", "recebido", "data_pgto"}.intersection(normalized_headers):
			return "dividends"

		if any(marker in file_name_lower for marker in ("tableexport", "posicao", "positions", "carteira")):
			return "positions"
		if any(marker in file_name_lower for marker in ("proventos", "dividend", "jcp")):
			return "dividends"
		if any(marker in file_name_lower for marker in ("nubank", "bank", "extrato")):
			return "bank"

		return "bank"

	def _read_headers(self, payload: bytes) -> list[str]:
		"""Read the CSV header row without materializing the full file."""

		text = self._decode_text(payload)
		clean_text = "\n".join(line for line in text.splitlines() if line.strip())
		if not clean_text.strip():
			return []

		delimiter = self._detect_delimiter(clean_text)
		reader = DictReader(StringIO(clean_text), delimiter=delimiter)
		return list(reader.fieldnames or [])

	@staticmethod
	def _normalize_fonte(fonte: FonteDados | str, payload: bytes, file_name: str) -> FonteDados:
		"""Coerce the upload source into a supported enum value."""

		if isinstance(fonte, FonteDados):
			return fonte

		candidate = str(fonte).strip().upper()
		if candidate in {"NUBANK", "MYPROFIT", "MANUAL", "SISTEMA"}:
			return FonteDados(candidate)

		file_name_lower = file_name.lower()
		if any(marker in file_name_lower for marker in ("proventos", "tableexport")):
			return FonteDados.MYPROFIT
		if any(marker in file_name_lower for marker in ("nubank", "extrato")):
			return FonteDados.NUBANK
		return FonteDados.NUBANK if payload else FonteDados.MANUAL

	@staticmethod
	def _safe_fonte(fonte: FonteDados | str) -> FonteDados:
		"""Best-effort conversion used when a failure happens before routing."""

		if isinstance(fonte, FonteDados):
			return fonte
		candidate = str(fonte).strip().upper()
		return FonteDados(candidate) if candidate in {member.value for member in FonteDados} else FonteDados.MANUAL

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

	def _insert_dividend(self, dividend_id: str, ticker: str, data_pagamento: date, valor_recebido: Decimal) -> None:
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
	def _clean_ticker(value: Any) -> str:
		"""Normalize broker tickers to an uppercase business key."""

		text = clean_csv_cell(value)
		return text.strip().upper()

	@staticmethod
	def _parse_br_date(value: Any) -> date:
		"""Parse Brazilian date strings used by broker exports."""

		text = clean_csv_cell(value)
		if not text:
			raise ValueError("Dividend row is missing a payment date")

		for format_string in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
			try:
				return datetime.strptime(text, format_string).date()
			except ValueError:
				continue
		raise ValueError(f"Unable to parse Brazilian date value: {value!r}")

	@staticmethod
	def _to_decimal(value: object) -> Decimal:
		"""Convert mixed numeric inputs to ``Decimal`` safely."""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			try:
				return Decimal(value)
			except InvalidOperation:
				return parse_br_currency(value)
		if isinstance(value, float):
			return Decimal(str(value))
		if value is None:
			return Decimal("0")
		try:
			return Decimal(str(value))
		except InvalidOperation:
			return parse_br_currency(value)
