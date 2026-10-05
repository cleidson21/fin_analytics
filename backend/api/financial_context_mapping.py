from decimal import Decimal

from backend.application.dtos.income_candidate_dto import (
    IncomeCandidateCollectionResponseDTO,
    IncomeCandidateResponseDTO,
    MonthlyOccurrenceResponseDTO,
)
from backend.application.services.income_candidate_service import (
    IncomeCandidateCollection,
    IncomeCandidateView,
)


def _serialize_decimal(value: object | None) -> str | None:
    if value is None:
        return None
    if type(value) is not Decimal or not value.is_finite():
        raise TypeError("Income evidence must be a finite Decimal.")
    return str(value)


def map_income_candidate(candidate: IncomeCandidateView) -> IncomeCandidateResponseDTO:
    return IncomeCandidateResponseDTO(
        candidate_id=candidate.candidate_id,
        evidence_state=candidate.evidence_state,
        decision_state=candidate.decision_state,
        signature_version=candidate.signature_version,
        source=candidate.source,
        evidence_fingerprint=candidate.evidence_fingerprint,
        currency=candidate.currency,
        direction=candidate.direction,
        window_start=candidate.window_start,
        window_end=candidate.window_end,
        current_month_is_partial=candidate.current_month_is_partial,
        includes_current_month=candidate.includes_current_month,
        observed_months=candidate.observed_months,
        monthly_occurrences=tuple(
            MonthlyOccurrenceResponseDTO(
                reference_month=item.reference_month,
                occurrence_count=item.occurrence_count,
            )
            for item in candidate.monthly_occurrences
        ),
        occurrence_count=candidate.occurrence_count,
        distinct_month_count=candidate.distinct_month_count,
        first_occurrence_date=candidate.first_occurrence_date,
        latest_occurrence_date=candidate.latest_occurrence_date,
        latest_amount=_serialize_decimal(candidate.latest_amount),
        typical_received_amount=_serialize_decimal(
            candidate.typical_received_amount
        ),
        minimum_received_amount=_serialize_decimal(candidate.minimum_received_amount),
        maximum_received_amount=_serialize_decimal(candidate.maximum_received_amount),
        median_absolute_deviation=_serialize_decimal(
            candidate.median_absolute_deviation
        ),
        risk_flags=candidate.risk_flags,
        decided_at=candidate.decided_at,
        decision_updated_at=candidate.decision_updated_at,
    )


def map_income_candidate_collection(
    collection: IncomeCandidateCollection,
) -> IncomeCandidateCollectionResponseDTO:
    return IncomeCandidateCollectionResponseDTO(
        as_of_date=collection.as_of_date,
        candidates=tuple(map_income_candidate(item) for item in collection.candidates),
    )
