from sqlalchemy import create_engine, event
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


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


event.listen(engine, "connect", _enable_sqlite_foreign_keys)
event.listen(async_engine.sync_engine, "connect", _enable_sqlite_foreign_keys)
