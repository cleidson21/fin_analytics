"""Contain legacy financial routes until their data ownership is certified."""

from fastapi import Depends, HTTPException, status

from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO


async def require_certified_legacy_financial_scope(
    current_user: UserResponseDTO = Depends(get_current_user),
) -> None:
    """Authenticate first, then deny access without inventing ledger ownership.

    Pierre's raw accounts/categories/transactions and import pipeline have no
    certified user scope. ADR-023 and R2's guards authorize other specific
    consumers, not these routes. Reopening requires an explicit scope decision.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Legacy financial scope unavailable: ownership is not certified",
    )
