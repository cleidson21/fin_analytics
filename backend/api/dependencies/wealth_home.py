from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.database.session import get_db


CurrentWealthHomeUser = Annotated[UserResponseDTO, Depends(get_current_user)]
WealthHomeReadSession = Annotated[Session, Depends(get_db)]
