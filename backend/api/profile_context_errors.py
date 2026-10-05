from typing import NoReturn

from fastapi import HTTPException, status

from backend.application.exceptions.smart_context_ownership_error import (
    SmartContextOwnershipInconsistentError,
    SmartContextOwnershipUnavailableError,
)


def raise_profile_context_error(error: Exception) -> NoReturn:
    """Translate B2 failures without revealing user or persistence details."""

    if isinstance(
        error,
        (
            SmartContextOwnershipUnavailableError,
            SmartContextOwnershipInconsistentError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Declared Profile context is unavailable.",
        ) from error
    if isinstance(error, (TypeError, ValueError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Declared Profile context is invalid.",
        ) from error
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal Profile context error.",
    ) from error
