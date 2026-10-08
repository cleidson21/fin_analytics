from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from backend.core.config import settings
from backend.database.url import async_database_url, sync_database_url


_sync_url = sync_database_url(settings.DATABASE_URL)
_async_url = async_database_url(settings.DATABASE_URL)

# Retained as public module constants for existing infrastructure callers.
DATABASE_URL = _sync_url.render_as_string(hide_password=False)
ASYNC_DATABASE_URL = _async_url.render_as_string(hide_password=False)

engine = create_engine(
    _sync_url,
    connect_args={"check_same_thread": False}
)

async_engine = create_async_engine(
    _async_url,
    connect_args={"check_same_thread": False}
)
