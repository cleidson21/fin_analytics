from __future__ import annotations

from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.database.session import SessionLocal


def get_profile_context_session() -> Generator[Session, None, None]:
    """Own commit/rollback for one Profile context request."""

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


CurrentProfileUser = Annotated[UserResponseDTO, Depends(get_current_user)]
ProfileContextSession = Annotated[Session, Depends(get_profile_context_session)]
