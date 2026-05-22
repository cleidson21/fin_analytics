"""Pydantic schemas for financial records.

The models in this module are used to validate normalized data produced by the
ingestion layer before it is persisted to the warehouse.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from config.constants import CategoriaFallback, TipoTransacao
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransacaoFinanceira(BaseModel):
	"""Validated representation of a financial transaction.

	Attributes:
		ID_Unico: Stable transaction identifier.
		Data: Business date associated with the transaction.
		Descricao: Original or normalized transaction description.
		Valor: Monetary amount of the transaction represented as Decimal.
		Tipo: Transaction type classification.
		Categoria: Business category classification.
		ArquivoOrigem: Source file name or path used during ingestion.
		Fonte: Data source identifier used for lineage tracking.
		processed_at: UTC-aware timestamp when the record was processed.
	"""

	model_config = ConfigDict(extra="forbid")

	ID_Unico: str = Field(..., min_length=1)
	Data: date
	Descricao: str = Field(..., min_length=1)
	Valor: Decimal
	Tipo: TipoTransacao | str = Field(..., min_length=1)
	Categoria: CategoriaFallback | str = Field(..., min_length=1)
	ArquivoOrigem: str = Field(..., min_length=1)
	Fonte: str = Field(..., min_length=1)
	processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

	@field_validator("Valor", mode="before")
	@classmethod
	def _ensure_decimal(cls, value: object) -> Decimal:
		"""Coerce monetary values to ``Decimal`` without introducing float drift.

		Args:
			value: Raw value supplied by the caller.

		Returns:
			A precise ``Decimal`` value.

		Raises:
			TypeError: If the value cannot be represented safely as ``Decimal``.
		"""

		if isinstance(value, Decimal):
			return value
		if isinstance(value, int):
			return Decimal(value)
		if isinstance(value, str):
			return Decimal(value)
		if isinstance(value, float):
			raise TypeError("Valor must not be provided as float; use Decimal or str.")
		raise TypeError("Valor must be a Decimal-compatible value.")

	@field_validator("processed_at")
	@classmethod
	def _ensure_utc_timestamp(cls, value: datetime) -> datetime:
		"""Ensure the processing timestamp is timezone-aware in UTC.

		Args:
			value: Timestamp provided by the caller.

		Returns:
			A timezone-aware UTC ``datetime``.
		"""

		if value.tzinfo is None:
			return value.replace(tzinfo=UTC)

		return value.astimezone(UTC)
