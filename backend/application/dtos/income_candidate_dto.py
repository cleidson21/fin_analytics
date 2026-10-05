from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from backend.domains.smart_context import (
    RecurringIncomeDecisionState,
    RecurringIncomeDirection,
    RecurringIncomeEvidenceState,
    RecurringIncomeRiskFlag,
)


EvidenceFingerprint = Annotated[
    str,
    StringConstraints(strict=True, pattern=r"^sha256:[0-9a-f]{64}$"),
]


class IncomeDecisionRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_fingerprint: EvidenceFingerprint


class MonthlyOccurrenceResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_month: str
    occurrence_count: int


class IncomeCandidateResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    evidence_state: RecurringIncomeEvidenceState
    decision_state: RecurringIncomeDecisionState | None
    signature_version: int
    source: Literal["GOVERNED_TRANSACTIONS"]
    evidence_fingerprint: EvidenceFingerprint | None
    currency: str | None
    direction: RecurringIncomeDirection | None
    window_start: date | None
    window_end: date | None
    current_month_is_partial: bool | None
    includes_current_month: bool | None
    observed_months: tuple[str, ...]
    monthly_occurrences: tuple[MonthlyOccurrenceResponseDTO, ...]
    occurrence_count: int | None
    distinct_month_count: int | None
    first_occurrence_date: date | None
    latest_occurrence_date: date | None
    latest_amount: str | None
    typical_received_amount: str | None
    minimum_received_amount: str | None
    maximum_received_amount: str | None
    median_absolute_deviation: str | None
    risk_flags: tuple[RecurringIncomeRiskFlag, ...]
    decided_at: datetime | None
    decision_updated_at: datetime | None


class IncomeCandidateCollectionResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    as_of_date: date
    candidates: tuple[IncomeCandidateResponseDTO, ...]
