from typing import Any, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.use_cases.authenticate_user import AuthenticateUserUseCase
from backend.core.container import get_authenticate_user_use_case
from backend.database.session import SessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma sessão de banco de dados por requisição."""
    async with SessionLocal() as session:
        yield session


def resolve_authenticate_user(session=Depends(get_db_session)) -> AuthenticateUserUseCase:
    """Resolve a injeção do caso de uso de autenticação para o FastAPI."""
    return get_authenticate_user_use_case(session)
