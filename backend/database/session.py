from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from backend.database.engine import engine

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)
