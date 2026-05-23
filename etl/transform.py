"""Vectorized transformation layer for standardized financial transactions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

import polars as pl

from config.constants import CategoriaFallback, FonteDados, TipoTransacao
from domain.categorization import Categorizer
from utils.hashing import generate_deterministic_hash
from utils.normalization import normalize_text

OUTPUT_COLUMNS: Final[tuple[str, ...]] = (
	"ID_Unico",
	"Data",
	"Descricao",
	"Valor",
	"Tipo",
	"Categoria",
	"ArquivoOrigem",
	"Fonte",
	"processed_at",
)

_DATE_PARSE_FORMATS: Final[tuple[str, ...]] = (
	"%Y-%m-%d",
	"%d/%m/%Y",
	"%d-%m-%Y",
)


class DataTransformer:
	"""Transform standardized raw data into the financial domain schema."""

	def __init__(self, categorizer: Categorizer) -> None:
		self._categorizer = categorizer

	def process_raw_data(self, df: pl.DataFrame, fonte: FonteDados, file_name: str) -> pl.DataFrame:
		"""Transform raw records into the ``TransacaoFinanceira`` shape.

		The method avoids row-by-row work for numeric and temporal transforms,
		and only calls Python-level helpers for description normalization,
		categorical assignment over unique values, and the final hash.
		"""

		if df.is_empty():
			return pl.DataFrame(schema=self._output_schema())

		standardized = self._standardize_input_columns(df)
		self._validate_required_columns(standardized)

		enriched = standardized.with_columns(
			pl.col("data").cast(pl.Utf8).alias("data_text"),
			pl.col("descricao").cast(pl.Utf8).map_elements(normalize_text, return_dtype=pl.Utf8).alias("descricao_normalizada"),
			self._normalize_amount_expression().alias("valor_numerico"),
		)

		enriched = enriched.with_columns(
			pl.col("descricao_normalizada").replace(self._category_mapping(enriched)).alias("Categoria"),
			pl.col("descricao_normalizada").replace(self._type_mapping(enriched)).alias("Tipo"),
		)

		enriched = enriched.with_columns(
			pl.col("valor_numerico").abs().alias("valor_abs"),
			pl.when(pl.col("Tipo") == TipoTransacao.RECEITA.value)
			.then(pl.col("valor_numerico").abs())
			.otherwise(-pl.col("valor_numerico").abs())
			.alias("Valor"),
			pl.lit(fonte.value).alias("Fonte"),
			pl.lit(file_name).alias("ArquivoOrigem"),
			pl.lit(datetime.now(UTC)).cast(pl.Datetime("us", time_zone="UTC")).alias("processed_at"),
		)

		enriched = enriched.with_columns(
			self._parse_date_expression().alias("Data"),
		)

		enriched = enriched.with_row_index(name="row_number")
		enriched = enriched.with_columns(
			pl.struct(
				[
					pl.col("Data").dt.strftime("%Y-%m-%d").alias("data_iso"),
					pl.col("valor_abs").round(2).cast(pl.Decimal(18, 2)).cast(pl.Utf8).alias("valor_abs_text"),
					pl.col("descricao_normalizada"),
					pl.col("Fonte"),
					pl.lit(file_name).alias("nome_arquivo"),
					pl.col("row_number").cast(pl.Utf8),
				]
			).map_elements(self._generate_hash_from_row, return_dtype=pl.Utf8).alias("ID_Unico")
		)

		return enriched.select(
			[
				pl.col("ID_Unico"),
				pl.col("Data"),
				pl.col("descricao_normalizada").alias("Descricao"),
				pl.col("Valor").cast(pl.Decimal(18, 2)),
				pl.col("Tipo"),
				pl.col("Categoria"),
				pl.col("ArquivoOrigem"),
				pl.col("Fonte"),
				pl.col("processed_at"),
			]
		)

	@staticmethod
	def _output_schema() -> dict[str, pl.DataType]:
		"""Return the empty-frame schema used by ``process_raw_data``."""

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
		}

	@staticmethod
	def _generate_hash_from_row(row: dict[str, object]) -> str:
		"""Generate the final deterministic hash from a prepared struct row."""

		return generate_deterministic_hash(
			data_iso=str(row["data_iso"]),
			valor_abs=str(row["valor_abs_text"]),
			descricao_normalizada=str(row["descricao_normalizada"]),
			fonte=str(row["Fonte"]),
			nome_arquivo=str(row["nome_arquivo"]),
			row_number=str(row["row_number"]),
		)

	def _standardize_input_columns(self, df: pl.DataFrame) -> pl.DataFrame:
		"""Normalize incoming column names into the canonical lower-case form."""

		aliases: dict[str, int] = {}
		expressions: list[pl.Expr] = []

		for original_name in df.columns:
			canonical_name = self._canonical_input_name(original_name)
			occurrence = aliases.get(canonical_name, 0)
			aliases[canonical_name] = occurrence + 1
			final_name = canonical_name if occurrence == 0 else f"{canonical_name}_{occurrence + 1}"
			expressions.append(pl.col(original_name).alias(final_name))

		return df.select(expressions)

	@staticmethod
	def _canonical_input_name(column_name: str) -> str:
		"""Normalize schema-drifted input names."""

		normalized = normalize_text(column_name).replace(" ", "_").lower()
		aliases = {
			"data": "data",
			"date": "data",
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
		}
		return aliases.get(normalized, normalized)

	@staticmethod
	def _validate_required_columns(df: pl.DataFrame) -> None:
		"""Validate the minimum raw schema required for transformation."""

		required_columns = {"data", "descricao", "valor"}
		missing = sorted(required_columns.difference(df.columns))
		if missing:
			message = ", ".join(missing)
			raise ValueError(f"Raw dataframe is missing required columns: {message}")

	def _parse_date_expression(self) -> pl.Expr:
		"""Parse the raw date column using the supported input formats."""

		date_text = pl.col("data_text")
		parsed_candidates = [
			date_text.str.strptime(pl.Date, format=format_string, strict=False)
			for format_string in _DATE_PARSE_FORMATS
		]
		return pl.coalesce(parsed_candidates)

	def _normalize_amount_expression(self) -> pl.Expr:
		"""Normalize monetary values while preserving numeric precision."""

		raw_amount = pl.col("valor").cast(pl.Utf8).str.replace_all(r"[^0-9,\.\-]", "")
		normalized_amount = (
			pl.when(raw_amount.str.contains(",") & raw_amount.str.contains(r"\."))
			.then(raw_amount.str.replace_all(r"\.", "").str.replace(",", "."))
			.otherwise(raw_amount.str.replace(",", "."))
		)
		return normalized_amount.cast(pl.Float64, strict=False)

	def _category_mapping(self, df: pl.DataFrame) -> dict[str, str]:
		"""Build a mapping from normalized descriptions to final categories."""

		unique_descriptions = df.get_column("descricao_normalizada").unique().to_list()
		mapping: dict[str, str] = {}
		for description in unique_descriptions:
			categoria, _ = self._categorizer.categorize(str(description))
			mapping[str(description)] = self._enum_value(categoria)

		return mapping

	def _type_mapping(self, df: pl.DataFrame) -> dict[str, str]:
		"""Build a mapping from normalized descriptions to final transaction types."""

		unique_descriptions = df.get_column("descricao_normalizada").unique().to_list()
		mapping: dict[str, str] = {}
		for description in unique_descriptions:
			_, tipo = self._categorizer.categorize(str(description))
			mapping[str(description)] = self._enum_value(tipo)

		return mapping

	@staticmethod
	def _enum_value(value: object) -> str:
		"""Return the string value for an Enum-like object."""

		if hasattr(value, "value"):
			return str(getattr(value, "value"))
		return str(value)
