"""Shared dependency annotations for future authenticated Planning endpoints."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.database.session import get_db


CurrentPlanningUser = Annotated[UserResponseDTO, Depends(get_current_user)]
"""Authenticated user resolved through the existing async auth boundary."""


PlanningReadSession = Annotated[Session, Depends(get_db)]
"""Synchronous request-scoped session required by certified Planning readers."""
