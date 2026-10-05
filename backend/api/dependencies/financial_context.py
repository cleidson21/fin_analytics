from __future__ import annotations

from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.api.dependencies.auth import get_current_user
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.database.session import SessionLocal


def get_financial_context_read_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def get_financial_context_write_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


CurrentFinancialContextUser = Annotated[UserResponseDTO, Depends(get_current_user)]
FinancialContextReadSession = Annotated[
    Session,
    Depends(get_financial_context_read_session),
]
FinancialContextWriteSession = Annotated[
    Session,
    Depends(get_financial_context_write_session),
]
