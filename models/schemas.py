"""Pydantic schemas for financial records.

The models in this module are used to validate normalized data produced by the
ingestion layer before it is persisted to the warehouse.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransacaoFinanceira(BaseModel):
	"""Validated representation of a financial transaction.

	Attributes:
		ID_Unico: Stable transaction identifier.
		Data: Business date associated with the transaction.
		Descricao: Original or normalized transaction description.
		Valor: Monetary amount of the transaction.
		Tipo: Transaction type classification.
		Categoria: Business category classification.
		ArquivoOrigem: Source file name or path used during ingestion.
		DataImportacao: UTC-aware timestamp when the record was imported.
	"""

	model_config = ConfigDict(extra="forbid")

	ID_Unico: str = Field(..., min_length=1)
	Data: date
	Descricao: str = Field(..., min_length=1)
	Valor: float
	Tipo: str = Field(..., min_length=1)
	Categoria: str = Field(..., min_length=1)
	ArquivoOrigem: str = Field(..., min_length=1)
	DataImportacao: datetime = Field(default_factory=lambda: datetime.now(UTC))

	@field_validator("DataImportacao")
	@classmethod
	def _ensure_utc_timestamp(cls, value: datetime) -> datetime:
		"""Ensure the import timestamp is timezone-aware in UTC.

		Args:
			value: Timestamp provided by the caller.

		Returns:
			A timezone-aware UTC ``datetime``.
		"""

		if value.tzinfo is None:
			return value.replace(tzinfo=UTC)

		return value.astimezone(UTC)
