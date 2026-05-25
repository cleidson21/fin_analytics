"""High-resilience CSV extraction utilities for bank statement files."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Final

import pandas as pd
import polars as pl

from config.constants import FonteDados
from utils.normalization import normalize_text

ESSENTIAL_COLUMNS: Final[set[str]] = {"data", "descricao", "valor"}

_COLUMN_ALIASES: Final[dict[str, str]] = {
	"data": "data",
	"date": "data",
	"dt": "data",
	"descricao": "descricao",
	"description": "descricao",
	"desc": "descricao",
	"valor": "valor",
	"value": "valor",
	"amount": "valor",
	"tipo": "tipo",
	"type": "tipo",
	"categoria": "categoria",
	"category": "categoria",
	"id": "id_unico",
	"id_unico": "id_unico",
	"idunico": "id_unico",
	"processed_at": "processed_at",
	"processedat": "processed_at",
	"data_processamento": "processed_at",
	"arquivoorigem": "arquivo_origem",
	"arquivo_origem": "arquivo_origem",
	"source_file": "arquivo_origem",
	"fonte": "fonte",
	"source": "fonte",
}


class DataExtractor:
	"""Read bank CSV files into a standardized Polars DataFrame.

	The extractor tolerates common schema drift patterns, auto-detects the
	delimiter, and falls back from UTF-8 to latin1 when necessary.
	"""

	def read_bank_csv(self, file_path: Path, fonte: FonteDados) -> pl.DataFrame:
		"""Read a bank file and return a standardized Polars DataFrame.

		Args:
			file_path: Path to the source CSV file.
			fonte: Source system used for lineage and downstream routing.

		Returns:
			A Polars DataFrame with normalized, lower-case column names.

		Raises:
			FileNotFoundError: If the source file does not exist.
			ValueError: If the file is empty or misses essential columns.
		"""

		if not file_path.exists():
			raise FileNotFoundError(file_path)

		if file_path.suffix.lower() in {".xlsx", ".xls"}:
			try:
				dataframe = pl.from_pandas(pd.read_excel(file_path, engine="openpyxl"))
			except ImportError as exc:
				raise ImportError(
					"Reading Excel files requires the openpyxl package. Install it with `pip install openpyxl`."
				) from exc
			standardized = self._standardize_columns(dataframe)
			standardized = self._normalize_myprofit_frame(standardized, fonte=fonte, file_path=file_path)
			self._validate_essential_columns(standardized, file_path=file_path, fonte=fonte)
			return standardized

		raw_text = self._read_text_with_fallback(file_path)
		cleaned_text = self._remove_blank_lines(raw_text)
		if not cleaned_text.strip():
			raise ValueError(f"CSV file is empty: {file_path}")

		delimiter = self._detect_delimiter(cleaned_text)
		dataframe = pl.read_csv(
			StringIO(cleaned_text),
			separator=delimiter,
			infer_schema_length=0,
			ignore_errors=False,
			try_parse_dates=False,
			truncate_ragged_lines=True,
		)

		standardized = self._standardize_columns(dataframe)
		standardized = self._normalize_myprofit_frame(standardized, fonte=fonte, file_path=file_path)
		self._validate_essential_columns(standardized, file_path=file_path, fonte=fonte)
		return standardized

	@staticmethod
	def _read_text_with_fallback(file_path: Path) -> str:
		"""Read file text using UTF-8 first and latin1 as fallback."""

		for encoding in ("utf-8-sig", "utf-8", "latin1"):
			try:
				return file_path.read_text(encoding=encoding)
			except UnicodeDecodeError:
				continue

		raise UnicodeDecodeError("utf-8", b"", 0, 1, "Unable to decode CSV file")

	@staticmethod
	def _remove_blank_lines(raw_text: str) -> str:
		"""Remove empty lines so downstream parsing stays stable."""

		return "\n".join(line for line in raw_text.splitlines() if line.strip())

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
				dialect = csv.Sniffer().sniff("\n".join(sample_lines), delimiters=";,")
				return dialect.delimiter
			except csv.Error:
				return ";"

		return ";" if semicolon_count > comma_count else ","

	def _standardize_columns(self, dataframe: pl.DataFrame) -> pl.DataFrame:
		"""Normalize incoming column names and preserve the original order."""

		used_names: dict[str, int] = {}
		expressions: list[pl.Expr] = []

		for original_name in dataframe.columns:
			canonical_name = self._canonical_column_name(original_name)
			occurrence = used_names.get(canonical_name, 0)
			used_names[canonical_name] = occurrence + 1
			final_name = canonical_name if occurrence == 0 else f"{canonical_name}_{occurrence + 1}"
			expressions.append(pl.col(original_name).alias(final_name))

		return dataframe.select(expressions)

	def _normalize_myprofit_frame(self, dataframe: pl.DataFrame, *, fonte: FonteDados, file_path: Path) -> pl.DataFrame:
		"""Normalize MyProfit exports into the canonical transaction schema when possible."""

		if fonte != FonteDados.MYPROFIT or dataframe.is_empty():
			return dataframe

		columns = set(dataframe.columns)
		if {"ativo", "recebido", "data_pgto"}.issubset(columns):
			return dataframe.select(
				[
					pl.col("data_pgto").alias("data"),
					pl.concat_str([pl.lit("PROVENTO "), pl.col("ativo").cast(pl.Utf8)], separator="").alias("descricao"),
					pl.col("recebido").alias("valor"),
				]
			)

		portfolio_markers = {"total_investido", "total_atual", "ganho", "%_ganho", "%_patrimônio"}
		if portfolio_markers.intersection(columns):
			self._warn_ignored_myprofit_snapshot(file_path=file_path)
			return pl.DataFrame(schema={"data": pl.Utf8, "descricao": pl.Utf8, "valor": pl.Utf8})

		return dataframe

	@staticmethod
	def _warn_ignored_myprofit_snapshot(*, file_path: Path) -> None:
		"""Emit a lightweight hint for MyProfit files that are portfolio snapshots, not transactions."""

		print(f"Ignoring MyProfit portfolio snapshot (not a transaction feed): {file_path}")

	@staticmethod
	def _canonical_column_name(column_name: str) -> str:
		"""Return a lowercase canonical column name for schema drift handling."""

		normalized = normalize_text(column_name).replace(" ", "_").lower()
		return _COLUMN_ALIASES.get(normalized, normalized)

	@staticmethod
	def _validate_essential_columns(
		dataframe: pl.DataFrame,
		*,
		file_path: Path,
		fonte: FonteDados,
	) -> None:
		"""Ensure the CSV contains the minimum required business columns."""

		missing = sorted(ESSENTIAL_COLUMNS.difference(dataframe.columns))
		if missing:
			missing_columns = ", ".join(missing)
			raise ValueError(
				f"CSV from {fonte.value} at {file_path} is missing essential columns: {missing_columns}"
			)
