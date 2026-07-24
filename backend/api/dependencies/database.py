from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import SessionLocal

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma sessão de banco de dados por requisição."""
    async with SessionLocal() as session:
        yield session
