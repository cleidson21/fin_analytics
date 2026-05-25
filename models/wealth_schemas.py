"""Pydantic DTOs for the wealth-management layer.

The file keeps the legacy DTOs used by the current services and adds the new
wealth-centric models required by the next product layer.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from config.constants import ClasseAtivo, StatusMeta
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _to_decimal(value: object) -> Decimal:
	if isinstance(value, Decimal):
		return value
	if isinstance(value, int):
		return Decimal(value)
	if isinstance(value, str):
		return Decimal(value)
	if isinstance(value, float):
		raise TypeError("Decimal fields must not be provided as float; use Decimal or str.")
	raise TypeError("Decimal fields must be compatible with Decimal.")


class _DecimalModel(BaseModel):
	"""Shared configuration and decimal normalization helpers."""

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
		return _to_decimal(value)

	@field_validator("ticker")
	@classmethod
	def _normalize_ticker(cls, value: str) -> str:
		return value.strip().upper()


class DividendoDTO(_DecimalModel):
	"""Validated cash dividend or provento record."""

	ticker: str = Field(..., min_length=1)
	data_pagamento: date
	valor_recebido: Decimal

	@field_validator("valor_recebido", mode="before")
	@classmethod
	def _coerce_decimal_fields(cls, value: object) -> object:
		return _to_decimal(value)

	@field_validator("ticker")
	@classmethod
	def _normalize_ticker(cls, value: str) -> str:
		return value.strip().upper()


class MetaFinanceiraDTO(_DecimalModel):
	"""Legacy validated representation of a financial goal."""

	nome: str = Field(..., min_length=1)
	valor_alvo: Decimal
	valor_atual: Decimal = Field(default=Decimal("0"))
	prazo_meses: int = Field(..., ge=0)
	prioridade: int = Field(..., ge=1)

	@field_validator("valor_alvo", "valor_atual", mode="before")
	@classmethod
	def _coerce_decimal_fields(cls, value: object) -> object:
		return _to_decimal(value)

	@field_validator("nome")
	@classmethod
	def _normalize_nome(cls, value: str) -> str:
		return value.strip()


class CategoriaDimDTO(_DecimalModel):
	"""Financial category taxonomy used by the governance layer."""

	id: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
	macro_categoria: str = Field(..., min_length=1)
	subcategoria: str = Field(..., min_length=1)
	tipo_financeiro: str = Field(..., min_length=1)
	essencialidade: str = Field(..., min_length=1)
	cor_dashboard: str = Field(default="#6C7A89", min_length=1)
	icone: str = Field(default="circle", min_length=1)
	budget_default: Decimal = Field(default=Decimal("0"))

	@field_validator("budget_default", mode="before")
	@classmethod
	def _coerce_budget_default(cls, value: object) -> object:
		return _to_decimal(value)

	@field_validator("id", "macro_categoria", "subcategoria", "tipo_financeiro", "essencialidade")
	@classmethod
	def _normalize_upper_text(cls, value: str) -> str:
		return value.strip().upper().replace(" ", "_")

	@field_validator("cor_dashboard", "icone")
	@classmethod
	def _normalize_text(cls, value: str) -> str:
		return value.strip()


class FinancialGoalDTO(_DecimalModel):
	"""Wealth-centric financial goal model used by the new product layer."""

	goal_id: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
	nome: str = Field(..., min_length=1)
	tipo: str = Field(default="OUTRA", min_length=1)
	valor_meta: Decimal
	valor_atual: Decimal = Field(default=Decimal("0"))
	data_limite: date
	prioridade: int = Field(default=1, ge=1)
	categoria_relacionada: str | None = None
	aporte_mensal_planejado: Decimal = Field(default=Decimal("0"))
	status: str = Field(default=StatusMeta.ATIVA.value, min_length=1)

	@field_validator("valor_meta", "valor_atual", "aporte_mensal_planejado", mode="before")
	@classmethod
	def _coerce_decimal_fields(cls, value: object) -> object:
		return _to_decimal(value)

	@field_validator("goal_id", "nome", "tipo", "status")
	@classmethod
	def _normalize_upper_text(cls, value: str) -> str:
		return value.strip().upper().replace(" ", "_")

	@field_validator("categoria_relacionada")
	@classmethod
	def _normalize_optional_category(cls, value: str | None) -> str | None:
		if value is None:
			return None
		return value.strip().upper().replace(" ", "_")


class PositionDTO(_DecimalModel):
	"""Portfolio position snapshot for the wealth dimension table."""

	ticker: str = Field(..., min_length=1)
	quantidade: Decimal
	preco_medio: Decimal
	classe_ativo: str = Field(..., min_length=1)
	corretora: str = Field(default="NAO_INFORMADA", min_length=1)

	@field_validator("quantidade", "preco_medio", mode="before")
	@classmethod
	def _coerce_decimal_fields(cls, value: object) -> object:
		return _to_decimal(value)

	@field_validator("ticker")
	@classmethod
	def _normalize_ticker(cls, value: str) -> str:
		return value.strip().upper()

	@field_validator("classe_ativo")
	@classmethod
	def _normalize_classe_ativo(cls, value: str) -> str:
		return value.strip().upper().replace(" ", "_")

	@field_validator("corretora")
	@classmethod
	def _normalize_corretora(cls, value: str) -> str:
		return value.strip().upper()