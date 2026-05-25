"""Typed Pydantic DTOs for the wealth-centric domain.

These models represent the richer personal-wealth layer used by the UI and
service layer. They keep database identifiers out of the presentation layer
while still allowing the repository to persist stable domain records.
"""

from __future__ import annotations

from decimal import Decimal
from typing import ClassVar
from uuid import uuid4

from config.constants import ClasseAtivo
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class _WealthDTO(BaseModel):
	"""Base configuration and numeric coercion shared by wealth DTOs."""

	model_config = ConfigDict(extra="forbid", frozen=True)
	_DECIMAL_FIELDS: ClassVar[frozenset[str]] = frozenset()

	@field_validator("*", mode="before")
	@classmethod
	def _coerce_decimal_like_fields(cls, value: object, info: ValidationInfo) -> object:
		"""Convert numeric payloads to ``Decimal`` when a field expects it."""

		if info.field_name not in cls._DECIMAL_FIELDS:
			return value

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			return Decimal(value)
		if isinstance(value, float):
			raise TypeError("Decimal fields must not be provided as float; use Decimal or str.")
		return value


class AssetDTO(_WealthDTO):
	"""Canonical metadata for a financial asset.

	Attributes:
		ticker: Market symbol used as the business key.
		nome: Friendly display name for the asset.
		classe_ativo: Investment class used for allocation and filtering.
		setor: Business sector or thematic bucket.
	"""

	ticker: str = Field(..., min_length=1)
	nome: str = Field(..., min_length=1)
	classe_ativo: ClasseAtivo
	setor: str = Field(..., min_length=1)

	@field_validator("ticker", "nome", "setor")
	@classmethod
	def _normalize_text_fields(cls, value: str) -> str:
		"""Trim surrounding whitespace and canonicalize empty-like payloads."""

		return value.strip()

	@field_validator("ticker")
	@classmethod
	def _normalize_ticker(cls, value: str) -> str:
		"""Store tickers in uppercase canonical form."""

		return value.strip().upper()


class PositionDTO(_WealthDTO):
	"""Current position snapshot for a portfolio holding."""

	_DECIMAL_FIELDS: ClassVar[frozenset[str]] = frozenset(
		{
			"quantidade",
			"preco_medio",
			"cotacao_atual",
			"pnl_absoluto",
			"pnl_percentual",
			"dividend_yield",
		},
	)

	ticker: str = Field(..., min_length=1)
	quantidade: Decimal
	preco_medio: Decimal
	cotacao_atual: Decimal
	pnl_absoluto: Decimal
	pnl_percentual: Decimal
	dividend_yield: Decimal

	@field_validator("ticker")
	@classmethod
	def _normalize_ticker(cls, value: str) -> str:
		"""Store tickers in uppercase canonical form."""

		return value.strip().upper()


class GoalDTO(_WealthDTO):
	"""Financial goal enriched with progress and contribution guidance."""

	_DECIMAL_FIELDS: ClassVar[frozenset[str]] = frozenset(
		{
			"valor_alvo",
			"valor_atual",
			"aporte_mensal_sugerido",
			"percentual_conclusao",
		},
	)

	id_meta: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
	nome: str = Field(..., min_length=1)
	valor_alvo: Decimal
	valor_atual: Decimal = Field(default=Decimal("0"))
	prazo_meses: int = Field(..., ge=0)
	aporte_mensal_sugerido: Decimal = Field(default=Decimal("0"))
	percentual_conclusao: Decimal = Field(default=Decimal("0"))
	prioridade: int = Field(default=1, ge=1)
	status: str = Field(default="ATIVA", min_length=1)

	@field_validator("nome", "status")
	@classmethod
	def _normalize_text_fields(cls, value: str) -> str:
		"""Trim whitespace from human-readable fields."""

		return value.strip()

	@field_validator("id_meta")
	@classmethod
	def _normalize_id_meta(cls, value: str) -> str:
		"""Store the domain identifier in a stable string form."""

		return value.strip()


class BudgetDTO(_WealthDTO):
	"""Monthly budget snapshot for a spending category."""

	_DECIMAL_FIELDS: ClassVar[frozenset[str]] = frozenset({"teto_mensal", "valor_utilizado", "percentual_uso"})

	categoria: str = Field(..., min_length=1)
	teto_mensal: Decimal
	valor_utilizado: Decimal = Field(default=Decimal("0"))
	percentual_uso: Decimal = Field(default=Decimal("0"))
	status_alerta: str = Field(default="OK", min_length=1)

	@field_validator("categoria", "status_alerta")
	@classmethod
	def _normalize_text_fields(cls, value: str) -> str:
		"""Trim whitespace and keep labels presentation-ready."""

		return value.strip()