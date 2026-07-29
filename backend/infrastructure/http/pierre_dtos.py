"""
Pierre DTOs — Pydantic models para respostas da API Pierre Finance.

Camada: Infrastructure / HTTP

Regras:
  - A Application NUNCA consome dict cru; sempre instâncias destes DTOs.
  - Aliases mapeiam camelCase do Pierre para snake_case interno.
  - Todos os campos opcionais possuem default=None.
  - model_config usa populate_by_name=True para aceitar ambas as notações.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ===================================================================== #
#  Account DTOs
# ===================================================================== #


class PierreAccountDTO(BaseModel):
    """Representa uma conta financeira retornada pelo Pierre."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str = Field(..., description="ID externo da conta no Pierre")
    name: str = Field(..., description="Nome da conta/instituição")
    type: Optional[str] = Field(None, description="Tipo: BANK, CREDIT, INVESTMENT, LOAN")
    subtype: Optional[str] = Field(None, alias="accountSubtype", description="Subtipo da conta")
    currency_code: Optional[str] = Field("BRL", alias="currencyCode")
    institution_name: Optional[str] = Field(None, alias="institutionName")
    balance: Optional[Decimal] = Field(None)
    raw: Optional[Dict[str, Any]] = Field(None, exclude=True)  # payload original para debug

    @field_validator("balance", mode="before")
    @classmethod
    def coerce_balance(cls, v: Any) -> Optional[Decimal]:
        if v is None:
            return None
        try:
            return Decimal(str(v))
        except Exception:
            return None


class PierreAccountsResponseDTO(BaseModel):
    """Envelope de resposta do endpoint /tools/api/get-accounts."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    success: bool
    data: List[PierreAccountDTO] = Field(default_factory=list)
    count: Optional[int] = None
    timestamp: Optional[datetime] = None

    @field_validator("data", mode="before")
    @classmethod
    def coerce_data(cls, v: Any) -> List[Dict[str, Any]]:
        """Se 'data' for None ou não for lista, retorna lista vazia."""
        if not isinstance(v, list):
            return []
        return v


# ===================================================================== #
#  Transaction DTOs
# ===================================================================== #


class PierreInstallmentDTO(BaseModel):
    """Sub-modelo de parcelamento de uma transação Pierre."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    total: Optional[int] = Field(None, alias="installmentCount")
    current: Optional[int] = Field(None, alias="installmentNumber")
    purchase_id: Optional[str] = Field(None, alias="purchaseId")

    @field_validator("total", "current", mode="before")
    @classmethod
    def coerce_int(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        try:
            return int(v)
        except Exception:
            return None


class PierreTransactionDTO(BaseModel):
    """Representa uma transação financeira retornada pelo Pierre.

    Mapeamento camelCase → snake_case realizado via aliases.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Identidade
    id: str = Field(..., description="ID externo da transação no Pierre")
    account_id: str = Field(..., alias="accountId")

    # Valores
    amount: Decimal = Field(..., description="Valor absoluto da transação")
    currency_code: str = Field("BRL", alias="currencyCode")

    # Direção e tipo
    direction: Optional[str] = Field(
        None,
        description="CREDIT ou DEBIT",
    )
    type: Optional[str] = Field(None, description="PURCHASE, TRANSFER, PAYMENT, etc.")
    status: Optional[str] = Field(
        "POSTED", description="POSTED ou PENDING"
    )

    # Descrição
    description: str = Field(..., description="Descrição da transação")
    original_description: Optional[str] = Field(None, alias="originalDescription")
    category: Optional[str] = Field(None, description="Categoria original do Pierre")

    # Datas
    transaction_date: date = Field(..., alias="date")
    posted_date: Optional[date] = Field(None, alias="postedDate")

    # Recorrência
    is_recurring: bool = Field(False, alias="isRecurring")

    # Parcelamento (pode vir como sub-objeto ou campos planos)
    installments: Optional[PierreInstallmentDTO] = Field(None)
    installment_count: Optional[int] = Field(None, alias="installmentCount")
    installment_current: Optional[int] = Field(None, alias="installmentNumber")
    purchase_id: Optional[str] = Field(None, alias="purchaseId")

    @field_validator("amount", mode="before")
    @classmethod
    def coerce_amount(cls, v: Any) -> Decimal:
        """Garante que o valor seja positivo e do tipo Decimal."""
        try:
            return Decimal(str(v)).copy_abs()
        except Exception:
            return Decimal("0")

    @field_validator("direction", mode="before")
    @classmethod
    def normalize_direction(cls, v: Any) -> str:
        """Normaliza direction para CREDIT/DEBIT em maiúsculas."""
        if isinstance(v, str):
            upper = v.upper()
            if upper in ("CREDIT", "IN", "INCOME", "ENTRADA"):
                return "CREDIT"
            return "DEBIT"
        return "DEBIT"

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: Any) -> str:
        """Normaliza status para POSTED/PENDING."""
        if isinstance(v, str):
            upper = v.upper()
            if upper in ("PENDING", "PENDENTE"):
                return "PENDING"
        return "POSTED"

    @field_validator("transaction_date", "posted_date", mode="before")
    @classmethod
    def coerce_date(cls, v: Any) -> Optional[date]:
        """Aceita date, datetime ou string ISO."""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            try:
                return date.fromisoformat(v[:10])
            except ValueError:
                return None
        return None

    @field_validator("is_recurring", mode="before")
    @classmethod
    def coerce_bool(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "sim")
        return bool(v)

    def effective_installment_count(self) -> Optional[int]:
        """Retorna installment_count efetivo, priorizando sub-objeto."""
        if self.installments and self.installments.total:
            return self.installments.total
        return self.installment_count

    def effective_installment_current(self) -> Optional[int]:
        """Retorna installment_current efetivo, priorizando sub-objeto."""
        if self.installments and self.installments.current:
            return self.installments.current
        return self.installment_current

    def effective_purchase_id(self) -> Optional[str]:
        """Retorna purchase_id efetivo, priorizando sub-objeto."""
        if self.installments and self.installments.purchase_id:
            return self.installments.purchase_id
        return self.purchase_id


class PierreTransactionsResponseDTO(BaseModel):
    """Envelope de resposta do endpoint /tools/api/get-transactions."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    success: bool
    data: List[PierreTransactionDTO] = Field(default_factory=list)
    count: Optional[int] = None
    timestamp: Optional[datetime] = None

    @field_validator("data", mode="before")
    @classmethod
    def coerce_data(cls, v: Any) -> List[Dict[str, Any]]:
        """Se 'data' for None, None-like ou não lista, retorna vazio."""
        if not isinstance(v, list):
            return []
        return v


# ===================================================================== #
#  Import Result DTO  (retornado pela API interna)
# ===================================================================== #


class PierreImportResultDTO(BaseModel):
    """DTO de resultado de uma importação Pierre. Retornado para o frontend."""

    model_config = ConfigDict(populate_by_name=True)

    status: str = Field(..., description="'success' | 'partial' | 'failed'")
    imported: int = Field(0, description="Transações inseridas/atualizadas")
    skipped: int = Field(0, description="Transações ignoradas (duplicadas)")
    errors: int = Field(0, description="Registros com erro de conversão")
    accounts_synced: int = Field(0, description="Contas sincronizadas")
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
