"""Extraction helpers for wealth and broker exports."""

from __future__ import annotations

from csv import DictReader
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
import logging

import polars as pl

from utils.parsers import clean_csv_cell, normalize_csv_header, parse_br_currency

LOGGER = logging.getLogger(__name__)


class WealthExtractor:
	"""Read wealth exports from NuInvest and MyProfit snapshots."""

	def extract_positions(self, file_obj: Path | BytesIO) -> pl.DataFrame:
		"""Backward-compatible wrapper that accepts a path or in-memory buffer."""

		return self.extract_nuinvest_positions(self._read_bytes(file_obj))

	def extract_nuinvest_positions(self, file_bytes: bytes) -> pl.DataFrame:
		"""Parse a NuInvest ``tableExport.csv`` payload into a canonical frame."""

		frame = self._read_csv_bytes(file_bytes, file_label="tableExport.csv")
		frame = self._standardize_columns(frame)
		self._ensure_columns(
			frame,
			{"ativo", "qtd", "preco_medio", "total_investido", "preco_atual"},
			file_label="tableExport.csv",
		)

		try:
			parsed = frame.with_columns(
				pl.col("ativo")
				.cast(pl.Utf8)
				.map_elements(clean_csv_cell, return_dtype=pl.Utf8)
				.str.strip_chars()
				.str.to_uppercase()
				.alias("ativo"),
				pl.col("qtd")
				.cast(pl.Utf8)
				.map_elements(parse_br_currency, return_dtype=pl.Decimal(18, 6))
				.alias("qtd"),
			)
		except Exception as exc:
			LOGGER.exception("Failed to normalize NuInvest position columns")
			raise ValueError(f"Falha ao processar colunas base da tableExport.csv: {exc}") from exc

		parsed = parsed.with_columns(pl.col("qtd").cast(pl.Decimal(18, 6), strict=False))
		parsed = parsed.with_columns(pl.col("qtd").fill_null(Decimal("0.000000")))

		for column_name in ("preco_medio", "total_investido", "preco_atual"):
			parsed = self._with_currency_column(parsed, column_name, file_label="tableExport.csv")

		if "valor_atual" in parsed.columns:
			parsed = self._with_currency_column(parsed, "valor_atual", file_label="tableExport.csv")

		return parsed.select(["ativo", "qtd", "preco_medio", "total_investido", "preco_atual"])

	def extract_dividends(self, file_obj: Path | BytesIO) -> pl.DataFrame:
		"""Read a ``proventos.csv`` export into a normalized frame."""

		frame = self._read_csv_bytes(self._read_bytes(file_obj), file_label="proventos.csv")
		frame = self._standardize_columns(frame)
		self._ensure_columns(frame, {"ativo", "recebido", "data_pgto"}, file_label="proventos.csv")

		parsed = frame.with_columns(
			pl.col("ativo")
			.cast(pl.Utf8)
			.map_elements(clean_csv_cell, return_dtype=pl.Utf8)
			.str.strip_chars()
			.str.to_uppercase()
			.alias("ativo"),
		)
		parsed = self._with_currency_column(parsed, "recebido", file_label="proventos.csv")
		parsed = parsed.with_columns(
			pl.col("data_pgto")
			.cast(pl.Utf8)
			.map_elements(clean_csv_cell, return_dtype=pl.Utf8)
			.str.strip_chars()
			.str.strptime(pl.Date, format="%d/%m/%Y", strict=False)
			.alias("data_pgto"),
		)
		return parsed.select(["ativo", "recebido", "data_pgto"])

	@staticmethod
	def _read_bytes(file_obj: Path | BytesIO) -> bytes:
		"""Load a CSV payload from disk or memory as raw bytes."""

		if isinstance(file_obj, Path):
			if not file_obj.exists():
				raise FileNotFoundError(file_obj)
			return file_obj.read_bytes()

		if hasattr(file_obj, "seek"):
			file_obj.seek(0)
		payload = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
		return bytes(payload)

	@staticmethod
	def _decode_bytes(file_bytes: bytes) -> str:
		"""Decode CSV bytes using the common encodings seen in exports."""

		for encoding in ("utf-8-sig", "utf-8", "latin1"):
			try:
				return file_bytes.decode(encoding)
			except UnicodeDecodeError:
				continue
		raise UnicodeDecodeError("utf-8", b"", 0, 1, "Unable to decode CSV payload")

	def _read_csv_bytes(self, file_bytes: bytes, *, file_label: str) -> pl.DataFrame:
		"""Parse raw CSV bytes using the stdlib reader before Polars."""

		text = self._decode_bytes(file_bytes)
		clean_text = "\n".join(line for line in text.splitlines() if line.strip())
		if not clean_text.strip():
			raise ValueError(f"CSV file is empty: {file_label}")

		delimiter = self._sniff_delimiter(clean_text)
		rows = list(DictReader(StringIO(clean_text), delimiter=delimiter))
		if not rows:
			raise ValueError(f"CSV file has no data rows: {file_label}")

		return pl.DataFrame(rows)

	@staticmethod
	def _sniff_delimiter(sample_text: str) -> str:
		"""Detect the most likely delimiter for broker CSV exports."""

		first_lines = [line for line in sample_text.splitlines() if line.strip()][:5]
		if not first_lines:
			return ";"

		semicolon_count = sum(line.count(";") for line in first_lines)
		comma_count = sum(line.count(",") for line in first_lines)
		return ";" if semicolon_count >= comma_count else ","

	@staticmethod
	def _standardize_columns(dataframe: pl.DataFrame) -> pl.DataFrame:
		"""Normalize and alias incoming CSV headers to canonical names."""

		aliases = {
			"ativo": "ativo",
			"ticker": "ativo",
			"codigo": "ativo",
			"codigo ativo": "ativo",
			"papel": "ativo",
			"quantidade": "qtd",
			"qtd": "qtd",
			"qtde": "qtd",
			"preco medio": "preco_medio",
			"preco medio unitario": "preco_medio",
			"preco_medio": "preco_medio",
			"preco atual": "preco_atual",
			"preco_atual": "preco_atual",
			"total investido": "total_investido",
			"total_investido": "total_investido",
			"valor investido": "total_investido",
			"valor atual": "valor_atual",
			"valor_atual": "valor_atual",
			"recebido": "recebido",
			"data pgto": "data_pgto",
			"data_pagamento": "data_pgto",
			"data": "data_pgto",
		}
		used_names: dict[str, int] = {}
		expressions: list[pl.Expr] = []
		for original_name in dataframe.columns:
			normalized = normalize_csv_header(original_name)
			canonical_name = aliases.get(normalized, normalized.replace(" ", "_"))
			occurrence = used_names.get(canonical_name, 0)
			used_names[canonical_name] = occurrence + 1
			final_name = canonical_name if occurrence == 0 else f"{canonical_name}_{occurrence + 1}"
			expressions.append(pl.col(original_name).alias(final_name))
		return dataframe.select(expressions)

	@staticmethod
	def _ensure_columns(dataframe: pl.DataFrame, required: set[str], *, file_label: str) -> None:
		"""Raise a readable error when expected columns are absent."""

		missing = sorted(required.difference(dataframe.columns))
		if missing:
			LOGGER.error(
				"Missing required columns in %s: %s (available=%s)",
				file_label,
				", ".join(missing),
				", ".join(dataframe.columns),
			)
			raise ValueError(f"CSV from {file_label} is missing essential columns: {', '.join(missing)}")

	@staticmethod
	def _with_currency_column(dataframe: pl.DataFrame, column_name: str, *, file_label: str) -> pl.DataFrame:
		"""Parse a monetary column with a clear, column-specific failure mode."""

		if column_name not in dataframe.columns:
			LOGGER.error(
				"Missing required monetary column in %s: %s (available=%s)",
				file_label,
				column_name,
				", ".join(dataframe.columns),
			)
			raise ValueError(f"CSV from {file_label} is missing essential column: {column_name}")

		try:
			return dataframe.with_columns(
				pl.col(column_name)
				.cast(pl.Utf8)
				.map_elements(parse_br_currency, return_dtype=pl.Decimal(18, 2))
				.alias(column_name),
			)
		except Exception as exc:
			LOGGER.exception("Failed to parse currency column %s in %s", column_name, file_label)
			raise ValueError(f"Falha ao processar a coluna {column_name} em {file_label}: {exc}") from exc
