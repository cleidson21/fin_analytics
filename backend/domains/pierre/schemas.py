"""
schemas.py — Domínio Pierre

DTOs Pydantic para:
  1. Payload bruto recebido da API Pierre (validação de entrada)
  2. Respostas serializadas para o Frontend (contratos públicos)

Referência: docs/16_PIERRE_REFERENCE.md e docs/03_DATABASE.md

Política:
  - Campos desconhecidos NÃO causam falha (extra='allow' nos schemas de input)
  - Campos mapeados são extraídos e persistidos em colunas próprias
  - Campos não mapeados vão para extra_json (capturado no pipeline)
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# Schemas de INPUT — payload bruto da Pierre
# ─────────────────────────────────────────────────────────────────────────────

class PierrePaymentData(BaseModel):
    """payment_data.payer / receiver."""
    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    document: Optional[str] = None


class PierrePayer(BaseModel):
    model_config = ConfigDict(extra="allow")
    payer: Optional[PierrePaymentData] = None
    receiver: Optional[PierrePaymentData] = None
    sameOwnership: Optional[bool] = None


class PierreCreditCardData(BaseModel):
    model_config = ConfigDict(extra="allow")
    purchaseDate: Optional[datetime] = None
    installmentNumber: Optional[int] = None
    totalInstallments: Optional[int] = None
    totalAmount: Optional[float] = None
    billId: Optional[str] = None
    isFullInstallmentTransaction: Optional[bool] = None
    isIndividualInstallment: Optional[bool] = None


class PierreMerchant(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: Optional[str] = None


class PierreTransactionRaw(BaseModel):
    """
    Payload bruto de uma transação da Pierre.
    Campos extras (não mapeados) são aceitos sem falha.
    O pipeline captura os extras em extra_json.
    """
    model_config = ConfigDict(extra="allow")

    # Identificação
    id: str                                    # → external_id
    account_id: str                            # → account_external_id

    # Dados canônicos
    description: str
    original_description: Optional[str] = None
    category: Optional[str] = None
    original_category: Optional[str] = None
    currency_code: str = "BRL"                 # → currency
    amount: float
    date: datetime
    type: str                                  # DEBIT | CREDIT
    status: str                                # POSTED | PENDING
    manual_transaction: bool = False

    # Dados de conta (desnormalizados na transação, usados para upsert de account)
    account_name: Optional[str] = None
    account_type: Optional[str] = None        # BANK | CREDIT
    account_subtype: Optional[str] = None
    connector_name: Optional[str] = None
    item_bank_name: Optional[str] = None
    account_credit_data: Optional[Any] = None  # → credit_metadata_json na conta

    # Dados de cartão de crédito
    credit_card_data: Optional[PierreCreditCardData] = None

    # Dados de pagamento
    payment_data: Optional[PierrePayer] = None

    # Merchant
    merchant: Optional[PierreMerchant] = None

    # Fatura
    bill_id: Optional[str] = None
    bill_due_date: Optional[str] = None
    official_bill_amount: Optional[float] = None
    bill_period_start: Optional[str] = None
    bill_period_end: Optional[str] = None

    @property
    def merchant_name(self) -> Optional[str]:
        if self.merchant:
            return self.merchant.name
        return None

    @property
    def payer_name(self) -> Optional[str]:
        if self.payment_data and self.payment_data.payer:
            return self.payment_data.payer.name
        return None

    @property
    def receiver_name(self) -> Optional[str]:
        if self.payment_data and self.payment_data.receiver:
            return self.payment_data.receiver.name
        return None

    def build_extra_json(self) -> Optional[str]:
        """
        Captura campos que não foram mapeados para colunas próprias.
        Nenhuma funcionalidade do sistema poderá depender deste campo.
        """
        # Campos conhecidos que já têm coluna própria
        known_fields = {
            "id", "account_id", "description", "original_description",
            "category", "original_category", "currency_code", "amount",
            "date", "type", "status", "manual_transaction",
            "account_name", "account_type", "account_subtype",
            "connector_name", "item_bank_name", "account_credit_data",
            "credit_card_data", "payment_data", "merchant",
            "bill_id", "bill_due_date", "official_bill_amount",
            "bill_period_start", "bill_period_end",
            # campos opcionais frequentes que vão para extra
            "account_item_id", "connector_image_url",
            "installment_due_date", "amount_in_account_currency",
            "tr_confidence", "tr_reasoning",
        }
        extras = {
            k: v for k, v in self.model_extra.items()
            if k not in known_fields and v is not None
        }
        return json.dumps(extras, default=str) if extras else None


class PierreApiResponse(BaseModel):
    """Envelope da resposta da API Pierre."""
    model_config = ConfigDict(extra="allow")

    success: bool
    data: list[PierreTransactionRaw]


# ─────────────────────────────────────────────────────────────────────────────
# Schemas de saída (contratos públicos do domínio pierre)
# ─────────────────────────────────────────────────────────────────────────────

class SyncStatusResponse(BaseModel):
    """Resposta de GET /pierre/sync/status — estado atual do sync_state."""
    provider: str
    last_success_sync: Optional[datetime]
    last_attempt: Optional[datetime]
    last_cursor: Optional[str]
    last_period: Optional[str]
    api_version: Optional[str]


class SyncResultResponse(BaseModel):
    """Resposta de POST /pierre/sync — resultado da sincronização."""
    provider: str = "pierre"
    status: str                 # SUCCESS | FAILED | PARTIAL
    received: int
    inserted: int
    updated: int
    ignored: int
    started_at: datetime
    finished_at: datetime
    error: Optional[str] = None
    mode: str                   # PROD | DEV | REPLAY
    replay_file: Optional[str] = None
