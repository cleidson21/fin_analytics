"""
db.py — Shared Infrastructure

Engine e SessionFactory SQLAlchemy para o FINANALYTICS V3.

Decisões técnicas:
  - SQLite com aiosqlite para I/O assíncrono
  - PRAGMA foreign_keys=ON: FK compostas são aplicadas (accounts ← transactions)
  - PRAGMA journal_mode=WAL: suporte a leituras concorrentes sem lock
  - check_same_thread=False: necessário para SQLite em contexto async

Esta é a única fonte de conexão com o banco. Todos os domínios
obtêm sua sessão através de get_session() ou SessionFactory.
"""

import os
import sqlite3

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# ── Base declarativa compartilhada por todos os models do projeto ──────────
Base = declarative_base()


def _build_database_url() -> str:
    """Resolve a DATABASE_URL a partir do ambiente."""
    url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./fin_analytics_v3.db")
    return url


DATABASE_URL: str = _build_database_url()

# ── Engine ─────────────────────────────────────────────────────────────────
_engine_kwargs: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    """Ativa foreign keys e WAL mode para todas as conexões SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


# ── Session factory ────────────────────────────────────────────────────────
SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:  # type: ignore[return]
    """
    Dependency injection para FastAPI.
    Uso: db: AsyncSession = Depends(get_session)
    """
    async with SessionFactory() as session:
        yield session
