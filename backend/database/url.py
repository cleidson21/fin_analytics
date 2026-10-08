"""Canonical database URL handling for runtime and Alembic.

The application currently supports SQLite with synchronous SQLAlchemy callers
and asynchronous API dependencies.  The configured URL may name either SQLite
driver; this module derives both forms without string replacement.
"""

from sqlalchemy.engine import URL, make_url


_SQLITE_SYNC_DRIVER = "sqlite"
_SQLITE_ASYNC_DRIVER = "sqlite+aiosqlite"


def _configured_url(database_url: str) -> URL:
    url = make_url(database_url)
    if url.drivername not in {_SQLITE_SYNC_DRIVER, _SQLITE_ASYNC_DRIVER}:
        raise ValueError(
            "Unsupported DATABASE_URL driver for the current SQLite runtime: "
            f"{url.drivername}"
        )
    return url


def sync_database_url(database_url: str) -> URL:
    """Return the configured SQLite URL with its synchronous driver."""

    return _configured_url(database_url).set(drivername=_SQLITE_SYNC_DRIVER)


def async_database_url(database_url: str) -> URL:
    """Return the configured SQLite URL with its asynchronous driver."""

    return _configured_url(database_url).set(drivername=_SQLITE_ASYNC_DRIVER)
