from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from backend.database.url import async_database_url, sync_database_url
from backend.core.config import settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRE_SMART_CONTEXT_REVISION = "f2915371d283"
SMART_CONTEXT_TABLES = {
    "user_declared_financial_context",
    "recurring_income_decisions",
}


def _subprocess_environment(database_path: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = (
        f"sqlite+aiosqlite:///{database_path.as_posix()}"
    )
    environment.setdefault("JWT_SECRET", "test-only-secret")
    return environment


def _run_python(code: str, database_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=_subprocess_environment(database_path),
        capture_output=True,
        text=True,
        check=False,
    )


def _create_pre_smart_context_database(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "CREATE TABLE alembic_version "
            "(version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
        )
        connection.execute(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            (PRE_SMART_CONTEXT_REVISION,),
        )


def _schema_state(database_path: Path) -> tuple[set[str], str]:
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        revision = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]
    return tables, revision


@pytest.mark.parametrize(
    ("configured", "expected_sync", "expected_async"),
    [
        (
            "sqlite+aiosqlite:///./custom.db",
            "sqlite:///./custom.db",
            "sqlite+aiosqlite:///./custom.db",
        ),
        (
            "sqlite:///./custom.db",
            "sqlite:///./custom.db",
            "sqlite+aiosqlite:///./custom.db",
        ),
    ],
)
def test_sqlite_database_url_normalization(
    configured: str,
    expected_sync: str,
    expected_async: str,
) -> None:
    assert sync_database_url(configured).render_as_string(hide_password=False) == expected_sync
    assert async_database_url(configured).render_as_string(hide_password=False) == expected_async


def test_engine_uses_canonical_configured_database_url(tmp_path: Path) -> None:
    database_path = tmp_path / "configured.db"
    result = _run_python(
        "from backend.database.engine import engine, async_engine; "
        "print(engine.url.database); print(async_engine.url.database)",
        database_path,
    )

    assert result.returncode == 0, result.stderr
    reported_paths = [Path(line).resolve() for line in result.stdout.splitlines()]
    assert reported_paths == [database_path.resolve(), database_path.resolve()]
    assert not database_path.exists()


def test_pytest_configuration_never_targets_active_database() -> None:
    configured_path = Path(sync_database_url(settings.DATABASE_URL).database).resolve()
    active_path = (PROJECT_ROOT / "database" / "fin_analytics.db").resolve()

    assert configured_path != active_path


def test_pytest_refuses_explicit_active_database_url() -> None:
    active_path = (PROJECT_ROOT / "database" / "fin_analytics.db").resolve()
    environment = os.environ.copy()
    environment["TEST_DATABASE_URL"] = (
        f"sqlite+aiosqlite:///{active_path.as_posix()}"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "tests/unit/test_phase_1.py",
            "-q",
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Refusing to run pytest against database/fin_analytics.db" in (
        result.stdout + result.stderr
    )


def test_backend_main_import_does_not_mutate_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "behind-head.db"
    _create_pre_smart_context_database(database_path)
    before = _schema_state(database_path)

    result = _run_python("import backend.main", database_path)

    assert result.returncode == 0, result.stderr
    after = _schema_state(database_path)
    assert after == before
    assert SMART_CONTEXT_TABLES.isdisjoint(after[0])
    assert after[1] == PRE_SMART_CONTEXT_REVISION


def test_backend_main_import_never_calls_create_all(tmp_path: Path) -> None:
    database_path = tmp_path / "create-all-sentinel.db"
    result = _run_python(
        "from backend.database.base import Base; "
        "Base.metadata.create_all = lambda *args, **kwargs: "
        "(_ for _ in ()).throw(AssertionError('create_all called')); "
        "import backend.main",
        database_path,
    )

    assert result.returncode == 0, result.stderr
    assert not database_path.exists()
