"""Repository-wide pytest database isolation.

Set the canonical database URL before test modules import ``backend.main`` or
database session globals. A caller may choose an explicit disposable database
through ``TEST_DATABASE_URL``; otherwise each pytest process gets a unique file
under the operating-system temporary directory.
"""

import os
import tempfile
from pathlib import Path

from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parent
ACTIVE_DATABASE_PATH = (PROJECT_ROOT / "database" / "fin_analytics.db").resolve()


def _isolated_test_database_url() -> str:
    configured = os.environ.get("TEST_DATABASE_URL")
    if configured:
        return configured

    path = Path(tempfile.gettempdir()) / f"finanalytics-pytest-{os.getpid()}.db"
    return f"sqlite+aiosqlite:///{path.as_posix()}"


def _assert_not_active_database(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        raise RuntimeError("Pytest DATABASE_URL must identify an isolated SQLite database")
    if url.database in {None, "", ":memory:"}:
        return

    database_path = Path(url.database)
    if not database_path.is_absolute():
        database_path = PROJECT_ROOT / database_path
    if database_path.resolve() == ACTIVE_DATABASE_PATH:
        raise RuntimeError("Refusing to run pytest against database/fin_analytics.db")


_test_database_url = _isolated_test_database_url()
_assert_not_active_database(_test_database_url)
os.environ["DATABASE_URL"] = _test_database_url
os.environ["TEST_DATABASE_URL"] = _test_database_url
