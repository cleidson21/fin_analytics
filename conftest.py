"""Repository-wide pytest database isolation.

Set the canonical database URL before test modules import ``backend.main`` or
database session globals. A caller may choose an explicit disposable database
through an inherited, verified disposable-root capability. Each pytest process
creates its own dedicated root and tmp_path tree, independent of TEMP/TMP.
"""

import os
import sys
from backend.database.disposable import (
    ROOT_ENVIRONMENT_VARIABLE,
    adopt_disposable_root,
    create_disposable_root,
    require_disposable_sqlite_path,
    require_disposable_sqlite_url,
)


if descriptor := os.environ.get(ROOT_ENVIRONMENT_VARIABLE):
    adopt_disposable_root(descriptor)
_pytest_root = create_disposable_root()


def _isolated_test_database_url() -> str:
    configured = os.environ.get("TEST_DATABASE_URL")
    if configured:
        return configured

    path = _pytest_root.path / "pytest.db"
    return f"sqlite+aiosqlite:///{path.as_posix()}"


def _guard_sqlite_connection(event: str, args: tuple[object, ...]) -> None:
    if event == "sqlite3.connect":
        require_disposable_sqlite_path(args[0])


_test_database_url = _isolated_test_database_url()
require_disposable_sqlite_url(_test_database_url)
os.environ["DATABASE_URL"] = _test_database_url
os.environ["TEST_DATABASE_URL"] = _test_database_url
os.environ[ROOT_ENVIRONMENT_VARIABLE] = _pytest_root.export()
sys.addaudithook(_guard_sqlite_connection)


def pytest_configure(config) -> None:
    basetemp = config.getoption("basetemp")
    if basetemp:
        # An arbitrary --basetemp never widens SQLite authority or permits pytest
        # to remove a root's creation marker. Previous .pytest_tmp is untouched.
        require_disposable_sqlite_path(basetemp)
    else:
        config.option.basetemp = str(_pytest_root.path / "pytest")
