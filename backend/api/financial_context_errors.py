from typing import NoReturn

from fastapi import HTTPException, status

from backend.application.exceptions.income_candidate_error import (
    IncomeCandidateEvidenceConflictError,
    IncomeCandidateNotFoundError,
)
from backend.application.exceptions.smart_context_ownership_error import (
    SmartContextOwnershipInconsistentError,
    SmartContextOwnershipUnavailableError,
)


def raise_financial_context_error(error: Exception) -> NoReturn:
    if isinstance(error, IncomeCandidateNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Income candidate is unavailable.",
        ) from error
    if isinstance(error, IncomeCandidateEvidenceConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Income candidate evidence changed. Refresh and try again.",
        ) from error
    if isinstance(
        error,
        (
            SmartContextOwnershipUnavailableError,
            SmartContextOwnershipInconsistentError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Financial context is unavailable.",
        ) from error
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal financial context error.",
    ) from error
