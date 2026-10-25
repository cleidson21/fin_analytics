from __future__ import annotations

from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.dependencies.wealth_home import (
    CurrentWealthHomeUser,
    WealthHomeReadSession,
)
from backend.api.wealth_home_mapping import map_wealth_home
from backend.application.dtos.wealth_home_dto import WealthHomeReadModel
from backend.application.exceptions.smart_context_ownership_error import (
    SmartContextOwnershipInconsistentError,
    SmartContextOwnershipUnavailableError,
)
from backend.application.services.wealth_home_read_service import WealthHomeReadService


router = APIRouter(prefix="/wealth-home", tags=["Wealth Home"])


def get_wealth_home_read_service() -> WealthHomeReadService:
    return WealthHomeReadService()


WealthHomeReadServiceDependency = Annotated[
    WealthHomeReadService,
    Depends(get_wealth_home_read_service),
]


def _raise_wealth_home_error(error: Exception) -> NoReturn:
    if isinstance(
        error,
        (
            SmartContextOwnershipUnavailableError,
            SmartContextOwnershipInconsistentError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Wealth Home scope is unavailable.",
        ) from error
    if isinstance(error, (TypeError, ValueError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Wealth Home request is invalid.",
        ) from error
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal Wealth Home error.",
    ) from error


@router.get("", response_model=WealthHomeReadModel)
def get_wealth_home(
    current_user: CurrentWealthHomeUser,
    db: WealthHomeReadSession,
    service: WealthHomeReadServiceDependency,
    reference_month: str = Query(pattern=r"^\d{4}-\d{2}$"),
) -> WealthHomeReadModel:
    try:
        data = service.read(
            db,
            current_user.id,
            reference_month=reference_month,
        )
        return map_wealth_home(data)
    except Exception as error:
        _raise_wealth_home_error(error)
