from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from backend.api.dependencies.financial_context import (
    CurrentFinancialContextUser,
    FinancialContextReadSession,
    FinancialContextWriteSession,
)
from backend.api.financial_context_errors import raise_financial_context_error
from backend.api.financial_context_mapping import (
    map_income_candidate,
    map_income_candidate_collection,
)
from backend.application.dtos.income_candidate_dto import (
    IncomeCandidateCollectionResponseDTO,
    IncomeCandidateResponseDTO,
    IncomeDecisionRequestDTO,
)
from backend.application.services.income_candidate_service import (
    IncomeCandidateService,
)


router = APIRouter(prefix="/financial-context", tags=["Financial Context"])


def get_income_candidate_service() -> IncomeCandidateService:
    return IncomeCandidateService()


IncomeCandidateServiceDependency = Annotated[
    IncomeCandidateService,
    Depends(get_income_candidate_service),
]


@router.get(
    "/income-candidates",
    response_model=IncomeCandidateCollectionResponseDTO,
)
def list_income_candidates(
    current_user: CurrentFinancialContextUser,
    db: FinancialContextReadSession,
    service: IncomeCandidateServiceDependency,
) -> IncomeCandidateCollectionResponseDTO:
    try:
        result = service.list_candidates(db, current_user.id)
        return map_income_candidate_collection(result)
    except Exception as error:
        raise_financial_context_error(error)


@router.post(
    "/income-candidates/{candidate_id}/confirm",
    response_model=IncomeCandidateResponseDTO,
)
def confirm_income_candidate(
    candidate_id: str,
    request: IncomeDecisionRequestDTO,
    current_user: CurrentFinancialContextUser,
    db: FinancialContextWriteSession,
    service: IncomeCandidateServiceDependency,
) -> IncomeCandidateResponseDTO:
    try:
        result = service.confirm(
            db,
            current_user.id,
            candidate_id=candidate_id,
            evidence_fingerprint=request.evidence_fingerprint,
        )
        return map_income_candidate(result)
    except Exception as error:
        raise_financial_context_error(error)


@router.post(
    "/income-candidates/{candidate_id}/reject",
    response_model=IncomeCandidateResponseDTO,
)
def reject_income_candidate(
    candidate_id: str,
    request: IncomeDecisionRequestDTO,
    current_user: CurrentFinancialContextUser,
    db: FinancialContextWriteSession,
    service: IncomeCandidateServiceDependency,
) -> IncomeCandidateResponseDTO:
    try:
        result = service.reject(
            db,
            current_user.id,
            candidate_id=candidate_id,
            evidence_fingerprint=request.evidence_fingerprint,
        )
        return map_income_candidate(result)
    except Exception as error:
        raise_financial_context_error(error)


@router.delete(
    "/income-candidates/{candidate_id}/decision",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reset_income_candidate_decision(
    candidate_id: str,
    current_user: CurrentFinancialContextUser,
    db: FinancialContextWriteSession,
    service: IncomeCandidateServiceDependency,
) -> Response:
    try:
        service.reset(db, current_user.id, candidate_id=candidate_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as error:
        raise_financial_context_error(error)
