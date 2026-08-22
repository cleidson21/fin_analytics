from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import AsyncSessionLocal

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma sessão de banco de dados por requisição, gerenciando commit e rollback."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
