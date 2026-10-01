"""Safe FIRE API error translation without changing global behavior."""

from typing import NoReturn

from fastapi import HTTPException, status

from backend.application.exceptions.planning_portfolio_source_error import (
    PlanningPortfolioSourceAmbiguousError,
    PlanningPortfolioSourceInconsistentError,
    PlanningPortfolioSourceUnavailableError,
)


def raise_fire_error(error: Exception) -> NoReturn:
    if isinstance(
        error,
        (
            PlanningPortfolioSourceUnavailableError,
            PlanningPortfolioSourceAmbiguousError,
            PlanningPortfolioSourceInconsistentError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Selected certified portfolio source is unavailable.",
        ) from error
    if isinstance(error, (TypeError, ValueError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    if isinstance(error, ArithmeticError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FIRE calculation could not be completed.",
        ) from error
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal FIRE error.",
    ) from error
