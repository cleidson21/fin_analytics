"""Extraction helpers for wealth and broker exports."""

from __future__ import annotations

import csv
from io import BytesIO, StringIO
from pathlib import Path

import polars as pl

from utils.normalization import normalize_text, parse_brazilian_currency


class WealthExtractor:
	"""Read wealth exports from MyProfit and broker snapshots."""

	def extract_positions(self, file_obj: Path | BytesIO) -> pl.DataFrame:
		"""Read a ``tableExport.csv`` snapshot into a normalized frame."""

		frame = self._read_csv(file_obj, file_label="tableExport.csv")
		frame = self._standardize_columns(frame)
		self._ensure_columns(frame, {"ativo", "qtd", "preco_medio", "total_investido", "preco_atual"}, file_label="tableExport.csv")

		parsed = frame.with_columns(
			pl.col("ativo").cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias("ativo"),
			pl.col("qtd").cast(pl.Utf8).str.replace_all(",", ".").cast(pl.Decimal(18, 6), strict=False).alias("qtd"),
		)
		parsed = self._with_currency_column(parsed, "preco_medio", file_label="tableExport.csv")
		parsed = self._with_currency_column(parsed, "total_investido", file_label="tableExport.csv")
		parsed = self._with_currency_column(parsed, "preco_atual", file_label="tableExport.csv")

		self._ensure_no_nulls(parsed, ["qtd", "preco_medio", "total_investido", "preco_atual"], file_label="tableExport.csv")
		return parsed.select(["ativo", "qtd", "preco_medio", "total_investido", "preco_atual"])

	def extract_dividends(self, file_obj: Path | BytesIO) -> pl.DataFrame:
		"""Read a ``proventos.csv`` export into a normalized frame."""

		frame = self._read_csv(file_obj, file_label="proventos.csv")
		frame = self._standardize_columns(frame)
		self._ensure_columns(frame, {"ativo", "recebido", "data_pgto"}, file_label="proventos.csv")

		parsed = frame.with_columns(
			pl.col("ativo").cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias("ativo"),
		)
		parsed = self._with_currency_column(parsed, "recebido", file_label="proventos.csv")
		try:
			parsed = parsed.with_columns(
				pl.col("data_pgto")
				.cast(pl.Utf8)
				.str.strip_chars()
				.str.strptime(pl.Date, format="%d/%m/%Y", strict=False)
				.alias("data_pgto"),
			)
		except Exception as exc:
			raise ValueError(f"Falha ao processar a coluna data_pgto em proventos.csv: {exc}") from exc

		self._ensure_no_nulls(parsed, ["recebido", "data_pgto"], file_label="proventos.csv")
		return parsed.select(["ativo", "recebido", "data_pgto"])

	def _read_csv(self, file_obj: Path | BytesIO, *, file_label: str) -> pl.DataFrame:
		"""Read a CSV from disk or memory with delimiter autodetection."""

		text = self._read_text(file_obj)
		cleaned = "\n".join(line for line in text.splitlines() if line.strip())
		if not cleaned.strip():
			raise ValueError(f"CSV file is empty: {file_label}")

		separator = self._detect_delimiter(cleaned)
		try:
			return pl.read_csv(
				StringIO(cleaned),
				separator=separator,
				infer_schema_length=0,
				ignore_errors=False,
				try_parse_dates=False,
				truncate_ragged_lines=True,
			)
		except Exception as exc:
			raise ValueError(f"Failed to parse CSV file {file_label}: {exc}") from exc

	@staticmethod
	def _read_text(file_obj: Path | BytesIO) -> str:
		"""Decode text from a path or in-memory buffer."""

		if isinstance(file_obj, Path):
			if not file_obj.exists():
				raise FileNotFoundError(file_obj)
			for encoding in ("utf-8-sig", "utf-8", "latin1"):
				try:
					return file_obj.read_text(encoding=encoding)
				except UnicodeDecodeError:
					continue
			raise UnicodeDecodeError("utf-8", b"", 0, 1, "Unable to decode CSV file")

		if hasattr(file_obj, "seek"):
			file_obj.seek(0)
		payload = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
		for encoding in ("utf-8-sig", "utf-8", "latin1"):
			try:
				return bytes(payload).decode(encoding)
			except UnicodeDecodeError:
				continue
		raise UnicodeDecodeError("utf-8", b"", 0, 1, "Unable to decode CSV buffer")

	@staticmethod
	def _detect_delimiter(sample_text: str) -> str:
		"""Detect the most likely delimiter among comma and semicolon."""

		sample_lines = [line for line in sample_text.splitlines() if line.strip()][:5]
		if not sample_lines:
			return ";"

		semicolon_count = sum(line.count(";") for line in sample_lines)
		comma_count = sum(line.count(",") for line in sample_lines)
		if semicolon_count == comma_count:
			try:
				dialect = csv.Sniffer().sniff("\n".join(sample_lines), delimiters=",;")
				return dialect.delimiter
			except csv.Error:
				return ";"

		return ";" if semicolon_count > comma_count else ","

	@staticmethod
	def _standardize_columns(dataframe: pl.DataFrame) -> pl.DataFrame:
		"""Normalize incoming column names to a lower-case canonical form."""

		aliases = {
			"ativo": "ativo",
			"asset": "ativo",
			"ticker": "ativo",
			"qtd": "qtd",
			"quantidade": "qtd",
			"preco_medio": "preco_medio",
			"precomedio": "preco_medio",
			"preco_atual": "preco_atual",
			"precoatual": "preco_atual",
			"total_investido": "total_investido",
			"totalinvestido": "total_investido",
			"recebido": "recebido",
			"data_pgto": "data_pgto",
			"data_pagamento": "data_pgto",
			"data": "data_pgto",
		}
		used_names: dict[str, int] = {}
		expressions: list[pl.Expr] = []
		for original_name in dataframe.columns:
			normalized = normalize_text(original_name).replace(" ", "_").lower()
			canonical_name = aliases.get(normalized, normalized)
			occurrence = used_names.get(canonical_name, 0)
			used_names[canonical_name] = occurrence + 1
			final_name = canonical_name if occurrence == 0 else f"{canonical_name}_{occurrence + 1}"
			expressions.append(pl.col(original_name).alias(final_name))
		return dataframe.select(expressions)

	@staticmethod
	def _ensure_columns(dataframe: pl.DataFrame, required: set[str], *, file_label: str) -> None:
		missing = sorted(required.difference(dataframe.columns))
		if missing:
			missing_columns = ", ".join(missing)
			raise ValueError(f"CSV from {file_label} is missing essential columns: {missing_columns}")

	@staticmethod
	def _ensure_no_nulls(dataframe: pl.DataFrame, columns: list[str], *, file_label: str) -> None:
		for column in columns:
			if dataframe.get_column(column).null_count() > 0:
				raise ValueError(f"Falha ao processar a coluna {column} em {file_label}")

	@staticmethod
	def _with_currency_column(dataframe: pl.DataFrame, column_name: str, *, file_label: str) -> pl.DataFrame:
		"""Parse one monetary column and keep the error message column-specific."""

		try:
			return dataframe.with_columns(
				pl.col(column_name)
				.cast(pl.Utf8)
				.map_elements(
					lambda value: parse_brazilian_currency(value),
					return_dtype=pl.Decimal(18, 2),
				)
				.alias(column_name)
			)
		except Exception as exc:
			raise ValueError(f"Falha ao processar a coluna {column_name} em {file_label}: {exc}") from exc