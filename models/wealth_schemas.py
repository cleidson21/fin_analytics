"""Pydantic DTOs for assets, dividends, and financial goals.

These models validate the wealth-management layer before data reaches DuckDB.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from config.constants import ClasseAtivo, StatusMeta
from pydantic import BaseModel, ConfigDict, Field, field_validator


class _DecimalModel(BaseModel):
	"""Shared decimal normalization for the wealth DTOs."""

	model_config = ConfigDict(extra="forbid")


class AtivoDTO(_DecimalModel):
	"""Validated snapshot of a portfolio asset."""

	ticker: str = Field(..., min_length=1)
	classe: ClasseAtivo
	quantidade: Decimal
	preco_medio: Decimal

	@field_validator("quantidade", "preco_medio", mode="before")
	@classmethod
	def _coerce_decimal_fields(cls, value: object) -> object:
		"""Convert numeric inputs to ``Decimal`` without float drift."""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			return Decimal(value)
		if isinstance(value, float):
			raise TypeError("Decimal fields must not be provided as float; use Decimal or str.")
		raise TypeError("Decimal fields must be compatible with Decimal.")

	@field_validator("ticker")
	@classmethod
	def _normalize_ticker(cls, value: str) -> str:
		"""Normalize tickers to uppercase canonical form."""

		return value.strip().upper()


class DividendoDTO(_DecimalModel):
	"""Validated cash dividend or provento record."""

	ticker: str = Field(..., min_length=1)
	data_pagamento: date
	valor_recebido: Decimal

	@field_validator("valor_recebido", mode="before")
	@classmethod
	def _coerce_decimal_fields(cls, value: object) -> object:
		"""Convert numeric inputs to ``Decimal`` without float drift."""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			return Decimal(value)
		if isinstance(value, float):
			raise TypeError("Decimal fields must not be provided as float; use Decimal or str.")
		raise TypeError("Decimal fields must be compatible with Decimal.")

	@field_validator("ticker")
	@classmethod
	def _normalize_ticker(cls, value: str) -> str:
		"""Normalize tickers to uppercase canonical form."""

		return value.strip().upper()


class MetaFinanceiraDTO(_DecimalModel):
	"""Validated representation of a financial goal."""

	nome: str = Field(..., min_length=1)
	valor_alvo: Decimal
	valor_atual: Decimal = Field(default=Decimal("0"))
	prazo_meses: int = Field(..., ge=0)
	prioridade: int = Field(..., ge=1)

	@field_validator("valor_alvo", "valor_atual", mode="before")
	@classmethod
	def _coerce_decimal_fields(cls, value: object) -> object:
		"""Convert numeric inputs to ``Decimal`` without float drift."""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			return Decimal(value)
		if isinstance(value, float):
			raise TypeError("Decimal fields must not be provided as float; use Decimal or str.")
		raise TypeError("Decimal fields must be compatible with Decimal.")

	@field_validator("nome")
	@classmethod
	def _normalize_nome(cls, value: str) -> str:
		"""Normalize goal names by trimming surrounding whitespace."""

		return value.strip()