from __future__ import annotations

import os
import asyncio
import sqlite3
import subprocess
import sys
import tempfile
import importlib
import hashlib
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.database.url import async_database_url, sync_database_url
from backend.database.disposable import (
    ROOT_ENVIRONMENT_VARIABLE,
    DisposableRoot,
    adopt_disposable_root,
    create_disposable_root,
    disposable_roots,
    require_disposable_sqlite_path,
    require_disposable_sqlite_url,
    require_explicit_disposable_script_database,
    disposable_script_session,
    disposable_script_async_session,
)
from backend.core.config import settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRE_SMART_CONTEXT_REVISION = "f2915371d283"
SMART_CONTEXT_TABLES = {
    "user_declared_financial_context",
    "recurring_income_decisions",
}


def _root_for(path: Path) -> DisposableRoot:
    return next(root for root in disposable_roots() if path.is_relative_to(root.path))


def _subprocess_environment(database_path: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = (
        f"sqlite+aiosqlite:///{database_path.as_posix()}"
    )
    environment["JWT_SECRET"] = "test-only-secret"
    environment[ROOT_ENVIRONMENT_VARIABLE] = _root_for(database_path).export()
    return environment


def _run_python(code: str, database_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", "-c", code],
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


def test_runtime_engines_enable_sqlite_foreign_keys(tmp_path: Path) -> None:
    database_path = tmp_path / "foreign-keys.db"
    result = _run_python(
        "from sqlalchemy import text; from backend.database.engine import engine; "
        "connection = engine.connect(); "
        "print(connection.execute(text('PRAGMA foreign_keys')).scalar_one()); "
        "connection.close(); engine.dispose()",
        database_path,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "1"


def test_pytest_configuration_never_targets_active_database() -> None:
    configured_path = Path(sync_database_url(settings.DATABASE_URL).database).resolve()
    _root_for(configured_path).verify()
    assert not configured_path.is_relative_to(PROJECT_ROOT)


def test_pytest_refuses_explicit_nondisposable_database_url() -> None:
    # The artificial target is never opened or created.
    unsafe_path = PROJECT_ROOT / "project" / "wealth-intelligence" / "synthetic-db-sentinel.db"
    environment = os.environ.copy()
    environment["TEST_DATABASE_URL"] = (
        f"sqlite+aiosqlite:///{unsafe_path.as_posix()}"
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
    assert "Refusing an operational location" in (
        result.stdout + result.stderr
    )
    assert not unsafe_path.exists()


def test_disposable_guard_rejects_path_and_url_outside_allowed_root(tmp_path: Path) -> None:
    root = create_disposable_root()
    safe_root = root.path
    unsafe = tmp_path / "synthetic-operational.db"
    assert require_disposable_sqlite_path(safe_root / "safe.db", roots=(root,)) == (safe_root / "safe.db")
    assert require_disposable_sqlite_path(
        (safe_root / "safe.db").as_uri() + "?mode=ro", roots=(root,)
    ) == safe_root / "safe.db"
    with pytest.raises(RuntimeError, match="outside disposable"):
        require_disposable_sqlite_path(unsafe, roots=(root,))
    with pytest.raises(RuntimeError, match="outside disposable"):
        require_disposable_sqlite_path(unsafe.as_uri() + "?mode=ro", roots=(root,))
    with pytest.raises(RuntimeError, match="outside disposable"):
        require_disposable_sqlite_url(f"sqlite+aiosqlite:///{unsafe.as_posix()}", roots=(root,))


def test_pytest_sqlite_audit_hook_rejects_direct_connection(tmp_path: Path) -> None:
    unsafe = PROJECT_ROOT / "project" / "wealth-intelligence" / "synthetic-db-sentinel.db"
    with pytest.raises(RuntimeError, match="operational location"):
        sqlite3.connect(unsafe)
    assert not unsafe.exists()


def test_pytest_sqlite_audit_hook_rejects_async_engine(tmp_path: Path) -> None:
    unsafe = PROJECT_ROOT / "project" / "wealth-intelligence" / "synthetic-db-sentinel.db"

    async def attempt() -> None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{unsafe.as_posix()}")
        try:
            async with engine.connect():
                pass
        finally:
            await engine.dispose()

    with pytest.raises(RuntimeError, match="operational location"):
        asyncio.run(attempt())
    assert not unsafe.exists()


def test_development_writer_requires_explicit_disposable_url(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "script.db"
    url = f"sqlite+aiosqlite:///{path.as_posix()}"
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="Set TEST_DATABASE_URL"):
        require_explicit_disposable_script_database(url)
    monkeypatch.setenv("TEST_DATABASE_URL", url)
    assert require_explicit_disposable_script_database(url) == path
    unsafe_url = f"sqlite+aiosqlite:///{(PROJECT_ROOT / 'project' / 'wealth-intelligence' / 'synthetic-db-sentinel.db').as_posix()}"
    monkeypatch.setenv("TEST_DATABASE_URL", unsafe_url)
    with pytest.raises(RuntimeError, match="operational location"):
        require_explicit_disposable_script_database(unsafe_url)


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


@pytest.mark.parametrize("url", ["sqlite://", "sqlite:///", "sqlite:///:memory:", "sqlite+aiosqlite:///:memory:"])
def test_disposable_exact_memory_urls(url):
    assert require_disposable_sqlite_url(url) is None
    assert require_disposable_sqlite_path(":memory:", roots=()) is None


@pytest.mark.parametrize("filename", [
    "file::memory:", "file::memory:?mode=memory", "file::memory:extended?mode=ro",
    "file::memory:/../synthetic-protected.db?mode=ro",
    "file::memory:\\..\\synthetic-protected.db?mode=ro",
    "file:%3Amemory%3A/../synthetic-protected.db?mode=rw",
    "file:relative.db?mode=ro", "file::memory:?cache=shared", "FILE::memory:",
    ":memory:extended", ":memory:/../synthetic-protected.db", ":memory:\\..\\synthetic-protected.db",
])
def test_disposable_memory_uri_bypass_is_refused_before_sqlite_open(filename):
    # The root conftest hook raises before SQLite interprets or opens the URI.
    with pytest.raises(RuntimeError):
        sqlite3.connect(filename, uri=True)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_disposable_memory_uri_bypass_is_refused_via_sqlalchemy(asynchronous):
    driver = "sqlite+aiosqlite" if asynchronous else "sqlite"
    url = f"{driver}:///file::memory:/../synthetic-protected.db?mode=rw&uri=true"
    if asynchronous:
        async def attempt():
            engine = create_async_engine(url)
            try:
                async with engine.connect():
                    pytest.fail("Ambiguous URI reached a live connection")
            finally:
                await engine.dispose()
        with pytest.raises(RuntimeError):
            asyncio.run(attempt())
    else:
        engine = create_engine(url)
        try:
            with pytest.raises(RuntimeError):
                with engine.connect():
                    pytest.fail("Ambiguous URI reached a live connection")
        finally:
            engine.dispose()


@pytest.mark.parametrize("suffix", ["?vfs=win32", "?mode=memory", "?mode=ro&mode=rw", "?mode=ro&cache=shared", "?unknown=1", "#fragment"])
def test_disposable_rejects_unexpected_uri_parameters(tmp_path, suffix):
    path = tmp_path / "never-opened.db"
    with pytest.raises(RuntimeError):
        sqlite3.connect(path.as_uri() + suffix, uri=True)
    assert not path.exists()


@pytest.mark.parametrize("driver", ["sqlite", "sqlite+aiosqlite"])
def test_disposable_file_url_forms_and_paths(tmp_path, monkeypatch, driver):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "memory-is-a-file.db"
    for value in (target, "./memory-is-a-file.db"):
        assert require_disposable_sqlite_path(value) == target
    assert require_disposable_sqlite_url(f"{driver}:///{target.as_posix()}") == target
    assert require_disposable_sqlite_url(f"{driver}:///./memory-is-a-file.db") == target
    if os.name == "nt":
        assert require_disposable_sqlite_path(str(target).swapcase()) == target
    for url in (f"{driver}:///{target.as_posix()}?uri=true", f"{driver}:///file:{target.as_posix()}?mode=ro&uri=true"):
        with pytest.raises(RuntimeError):
            require_disposable_sqlite_url(url)


def test_disposable_symlink_cannot_escape_explicit_root(tmp_path):
    root = create_disposable_root()
    allowed = root.path
    protected = tmp_path / "artificial-protected"
    protected.mkdir()
    link = allowed / "redirect"
    try:
        link.symlink_to(protected, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc.winerror if os.name == 'nt' else exc.errno}")
    with pytest.raises(RuntimeError):
        require_disposable_sqlite_path(link / "never-opened.db", roots=(root,))
    assert not (protected / "never-opened.db").exists()


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("redirected", [False, True])
def test_disposable_sessions_ignore_cached_runtime_engines(tmp_path, monkeypatch, asynchronous, redirected):
    runtime = importlib.import_module("backend.database.engine")
    runtime_sessions = importlib.import_module("backend.database.session")
    path_a, path_b = tmp_path / "cached-a.db", tmp_path / "validated-b.db"
    with sqlite3.connect(path_a) as db:
        db.execute("CREATE TABLE evidence (value TEXT)")
        db.execute("INSERT INTO evidence VALUES ('synthetic A')")
    before = hashlib.sha256(path_a.read_bytes()).digest()
    url_b = f"sqlite+aiosqlite:///{path_b.as_posix()}"
    old_url = f"sqlite:///{(path_b if redirected else path_a).as_posix()}"
    redirected_calls = []

    def cached_creator():
        redirected_calls.append(True)
        return sqlite3.connect(path_a)

    old_engine = create_engine(old_url, creator=cached_creator)
    async def cached_async_creator():
        import aiosqlite
        redirected_calls.append(True)
        return await aiosqlite.connect(path_a)

    old_async_engine = create_async_engine(old_url.replace("sqlite:", "sqlite+aiosqlite:", 1), async_creator=cached_async_creator)
    monkeypatch.setattr(runtime, "engine", old_engine)
    monkeypatch.setattr(runtime, "async_engine", old_async_engine)
    monkeypatch.setattr(runtime_sessions, "SessionLocal", sessionmaker(bind=old_engine))
    monkeypatch.setattr(runtime_sessions, "AsyncSessionLocal", async_sessionmaker(old_async_engine))
    monkeypatch.setattr(settings, "DATABASE_URL", url_b)
    monkeypatch.setenv("TEST_DATABASE_URL", url_b)

    async def write_async():
        async with disposable_script_async_session(settings.DATABASE_URL) as db:
            assert Path((await db.execute(text("PRAGMA database_list"))).first()[2]) == path_b
            assert (await db.execute(text("PRAGMA foreign_keys"))).scalar_one() == 1
            await db.execute(text("CREATE TABLE evidence (value TEXT)"))
            await db.execute(text("INSERT INTO evidence VALUES ('synthetic B')"))
            await db.commit()

    try:
        if asynchronous:
            asyncio.run(write_async())
        else:
            with disposable_script_session(settings.DATABASE_URL) as db:
                assert Path(db.execute(text("PRAGMA database_list")).first()[2]) == path_b
                assert db.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
                db.execute(text("CREATE TABLE evidence (value TEXT)"))
                db.execute(text("INSERT INTO evidence VALUES ('synthetic B')"))
                db.commit()
        assert redirected_calls == []
        assert hashlib.sha256(path_a.read_bytes()).digest() == before
        with sqlite3.connect(path_b) as db:
            assert db.execute("SELECT value FROM evidence").fetchall() == [("synthetic B",)]
    finally:
        old_engine.dispose()
        asyncio.run(old_async_engine.dispose())


@pytest.mark.parametrize("factory", [disposable_script_session, disposable_script_async_session])
@pytest.mark.parametrize("option", ["creator", "async_creator", "connect_args", "engine"])
def test_disposable_script_session_does_not_accept_redirecting_options(factory, option):
    with pytest.raises(TypeError):
        factory("sqlite:///:memory:", **{option: object()})


def test_disposable_script_configurations_fail_before_engine_creation(tmp_path, monkeypatch):
    module = importlib.import_module("backend.database.disposable")
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid configuration reached engine construction")
    monkeypatch.setattr(module, "create_engine", forbidden)
    monkeypatch.setattr(module, "create_async_engine", forbidden)
    safe = f"sqlite:///{(tmp_path / 'safe.db').as_posix()}"
    unsafe = f"sqlite:///{(PROJECT_ROOT / 'project' / 'synthetic-protected.db').as_posix()}"
    other_safe = f"sqlite:///{(tmp_path / 'other.db').as_posix()}"
    for configured, requested in [
        (None, safe), (safe, unsafe), (unsafe, unsafe), (safe, other_safe),
        (safe, safe + '?uri=true'), (safe, 'sqlite:///:memory:'),
        (safe, 'not-a-url'), ('not-a-url', safe), ('', safe),
    ]:
        if configured is None:
            monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
        else:
            monkeypatch.setenv("TEST_DATABASE_URL", configured)
        with pytest.raises(RuntimeError):
            with disposable_script_session(requested):
                pytest.fail("Invalid configuration yielded a session")
        async def attempt():
            with pytest.raises(RuntimeError):
                async with disposable_script_async_session(requested):
                    pytest.fail("Invalid configuration yielded a session")
        asyncio.run(attempt())


def test_disposable_script_equivalent_paths_are_accepted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TEST_DATABASE_URL", f"sqlite+aiosqlite:///{(tmp_path / 'same.db').as_posix()}")
    assert require_explicit_disposable_script_database("sqlite:///./same.db") == tmp_path / "same.db"


@pytest.mark.parametrize(("script", "canonical_fks"), [
    ("reset_db", False), ("seed_accounts", False), ("seed_transactions", False),
    ("seed_accounts", True), ("seed_transactions", True),
])
def test_disposable_scripts_write_b_without_using_cached_a(tmp_path, monkeypatch, script, canonical_fks):
    path_a, path_b = tmp_path / "old-a.db", tmp_path / "safe-b.db"
    with sqlite3.connect(path_a) as db:
        db.execute("CREATE TABLE evidence (value TEXT)")
        db.execute("INSERT INTO evidence VALUES ('preserve synthetic A')")
    before = hashlib.sha256(path_a.read_bytes()).digest()
    if script == "reset_db":
        with sqlite3.connect(path_b) as db:
            for table in ("import_artifacts", "import_runs", "position_snapshots", "portfolio_snapshots", "dividends", "transactions"):
                db.execute(f"CREATE TABLE {table} (id INTEGER)")
                db.execute(f"INSERT INTO {table} VALUES (1)")
    else:
        from backend.database.base import Base
        from backend.domain.enums.user_role import UserRole
        from backend.infrastructure.persistence.models.user import UserModel
        from backend.infrastructure.persistence.models.account import AccountModel
        from backend.infrastructure.persistence.models.institution import InstitutionModel
        from backend.infrastructure.persistence.models.category import CategoryModel
        from backend.infrastructure.persistence.models.transaction import TransactionModel
        schema_engine = create_engine(f"sqlite:///{path_b.as_posix()}")
        try:
            tables = [UserModel.__table__, InstitutionModel.__table__, AccountModel.__table__, CategoryModel.__table__, TransactionModel.__table__]
            if canonical_fks:
                Base.metadata.create_all(schema_engine, tables=tables)
            else:
                # Model the legacy-compatible schema expected by these old
                # scripts. Test the current canonical FK incompatibility
                # separately below; never disable the session's FK enforcement.
                legacy = MetaData()
                for table in tables:
                    clone = table.to_metadata(legacy)
                    for constraint in list(clone.foreign_key_constraints):
                        clone.constraints.remove(constraint)
                legacy.create_all(schema_engine)
            with sessionmaker(bind=schema_engine).begin() as db:
                db.add(UserModel(
                    id=UUID("00000000-0000-0000-0000-000000000001"), email="admin",
                    name="Synthetic admin", hashed_password="not-a-credential",
                    is_active=True, is_verified=True, role=UserRole.ADMIN,
                    created_at=datetime(2026, 1, 1),
                ))
        finally:
            schema_engine.dispose()

    runtime = importlib.import_module("backend.database.engine")
    runtime_sessions = importlib.import_module("backend.database.session")
    def forbidden(*args, **kwargs):
        pytest.fail("Script reused the previously configured engine/session")
    old_engine = create_engine(f"sqlite:///{path_b.as_posix()}", creator=forbidden)
    monkeypatch.setattr(runtime, "engine", old_engine)
    monkeypatch.setattr(runtime_sessions, "SessionLocal", forbidden)
    monkeypatch.setattr(runtime_sessions, "AsyncSessionLocal", forbidden)
    url_b = f"sqlite+aiosqlite:///{path_b.as_posix()}"
    monkeypatch.setattr(settings, "DATABASE_URL", url_b)
    monkeypatch.setenv("TEST_DATABASE_URL", url_b)
    module = importlib.import_module("scripts." + script)
    try:
        if script == "reset_db":
            module.reset_database()
        elif canonical_fks:
            with pytest.raises(IntegrityError, match="FOREIGN KEY"):
                asyncio.run(module.seed_accounts() if script == "seed_accounts" else module.seed())
        else:
            asyncio.run(module.seed_accounts() if script == "seed_accounts" else module.seed())
    finally:
        old_engine.dispose()
    assert hashlib.sha256(path_a.read_bytes()).digest() == before
    with sqlite3.connect(path_b) as db:
        if script == "reset_db":
            assert db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 0
        elif canonical_fks:
            assert db.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0
            assert db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0
        else:
            assert db.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == (2 if script == "seed_accounts" else 1)
            if script == "seed_transactions":
                assert db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 8


@pytest.mark.parametrize("asynchronous", [False, True])
def test_disposable_script_sessions_roll_back_on_failure(tmp_path, monkeypatch, asynchronous):
    path = tmp_path / "rollback.db"
    url = f"sqlite+aiosqlite:///{path.as_posix()}"
    monkeypatch.setenv("TEST_DATABASE_URL", url)
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE evidence (value TEXT)")

    async def fail_async():
        async with disposable_script_async_session(url) as db:
            await db.execute(text("INSERT INTO evidence VALUES ('rolled back')"))
            raise ValueError("synthetic failure")

    with pytest.raises(ValueError, match="synthetic failure"):
        if asynchronous:
            asyncio.run(fail_async())
        else:
            with disposable_script_session(url) as db:
                db.execute(text("INSERT INTO evidence VALUES ('rolled back')"))
                raise ValueError("synthetic failure")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == 0


def test_disposable_reset_failure_rolls_back_earlier_deletes(tmp_path, monkeypatch):
    path = tmp_path / "reset-rollback.db"
    url = f"sqlite+aiosqlite:///{path.as_posix()}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    monkeypatch.setenv("TEST_DATABASE_URL", url)
    with sqlite3.connect(path) as db:
        # The next table expected by reset is intentionally absent.
        db.execute("CREATE TABLE import_artifacts (id INTEGER)")
        db.execute("INSERT INTO import_artifacts VALUES (1)")
    importlib.import_module("scripts.reset_db").reset_database()
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM import_artifacts").fetchone()[0] == 1


@pytest.mark.parametrize("asynchronous", [False, True])
def test_disposable_sessions_work_without_pytest_hook(tmp_path, asynchronous):
    path_a, path_b = tmp_path / "subprocess-a.db", tmp_path / "subprocess-b.db"
    with sqlite3.connect(path_a) as db:
        db.execute("CREATE TABLE preserve_a (id INTEGER)")
        db.execute("INSERT INTO preserve_a VALUES (1)")
    before = hashlib.sha256(path_a.read_bytes()).digest()
    setup = f"""
import os, asyncio
from pathlib import Path
from sqlalchemy import text
from backend.database.session import SessionLocal, AsyncSessionLocal
from backend.core.config import settings
from backend.database.disposable import disposable_script_session, disposable_script_async_session
path_b = Path({str(path_b)!r})
settings.DATABASE_URL = 'sqlite+aiosqlite:///' + path_b.as_posix()
os.environ['TEST_DATABASE_URL'] = settings.DATABASE_URL
assert Path(SessionLocal.kw['bind'].url.database) != path_b
assert Path(AsyncSessionLocal.kw['bind'].url.database) != path_b
"""
    operation = """
async def run():
    async with disposable_script_async_session(settings.DATABASE_URL) as db:
        assert Path((await db.execute(text('PRAGMA database_list'))).first()[2]) == path_b
        await db.execute(text('CREATE TABLE only_b (id INTEGER)'))
        await db.commit()
asyncio.run(run())
""" if asynchronous else """
with disposable_script_session(settings.DATABASE_URL) as db:
    assert Path(db.execute(text('PRAGMA database_list')).first()[2]) == path_b
    db.execute(text('CREATE TABLE only_b (id INTEGER)'))
    db.commit()
"""
    result = _run_python(setup + operation, path_a)
    assert result.returncode == 0, result.stderr
    assert hashlib.sha256(path_a.read_bytes()).digest() == before
    with sqlite3.connect(path_b) as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE name='only_b'").fetchone() == ("only_b",)


@pytest.mark.parametrize("selection", ["created-root", "artificial-workspace", "operational-ancestor", "arbitrary", "system-parent"])
def test_root_policy_temp_variables_never_grant_authority(tmp_path, monkeypatch, selection):
    module = importlib.import_module("backend.database.disposable")
    root = create_disposable_root()
    native_parent = root.path.parent
    fake_workspace = tmp_path / "artificial-workspace"
    ancestor = tmp_path / "operational-ancestor"
    arbitrary = tmp_path / "arbitrary"
    for directory in (fake_workspace, ancestor / "database", arbitrary):
        directory.mkdir(parents=True)
    selected = {
        "created-root": root.path, "artificial-workspace": fake_workspace,
        "operational-ancestor": ancestor, "arbitrary": arbitrary,
        "system-parent": native_parent,
    }[selection]
    monkeypatch.setattr(module, "_ROOTS", [root])
    monkeypatch.setattr(module, "_PROTECTED_TREES", (*module._PROTECTED_TREES, fake_workspace, ancestor / "database"))
    monkeypatch.setenv("TEMP", str(selected))
    monkeypatch.setenv("TMP", str(selected))
    monkeypatch.setattr(tempfile, "tempdir", str(selected))
    def forbidden_temp():
        pytest.fail("TEMP/TMP was consulted as authorization")
    monkeypatch.setattr(tempfile, "gettempdir", forbidden_temp)

    assert require_disposable_sqlite_path(root.path / "safe.db") == root.path / "safe.db"
    candidate = selected / "synthetic-never-opened.db"
    if selection == "created-root":
        assert require_disposable_sqlite_path(candidate) == candidate
    else:
        with pytest.raises(RuntimeError):
            sqlite3.connect(candidate)
        assert not candidate.exists()
    # A second root still comes from the native system allocation location,
    # rather than from the newly changed environment/cached temporary path.
    another = create_disposable_root()
    assert another.path.parent == native_parent
    assert another.path != root.path


def test_root_policy_requires_creation_proof_not_a_path_or_environment(tmp_path, monkeypatch):
    module = importlib.import_module("backend.database.disposable")
    monkeypatch.setattr(module, "_ROOTS", [])
    monkeypatch.delenv(ROOT_ENVIRONMENT_VARIABLE, raising=False)
    monkeypatch.setenv("TEMP", str(tmp_path))
    monkeypatch.setenv("TMP", str(tmp_path))
    with pytest.raises(RuntimeError, match="No trusted"):
        sqlite3.connect(tmp_path / "never-opened.db")
    with pytest.raises(RuntimeError, match="capability"):
        require_disposable_sqlite_path(tmp_path / "never-opened.db", roots=(tmp_path,))
    assert require_disposable_sqlite_path(":memory:") is None
    assert require_disposable_sqlite_url("sqlite://") is None


def test_root_policy_arbitrary_directory_cannot_be_inherited_by_name(tmp_path, monkeypatch):
    module = importlib.import_module("backend.database.disposable")
    arbitrary = Path(tempfile.mkdtemp(prefix="finanalytics-disposable-unproven-", dir=module._system_disposable_parent()))
    identity = module._inspect(arbitrary, directory=True)
    descriptor = json.dumps({"version": 1, "path": str(arbitrary), "identity": list(identity), "nonce": "0" * 32})
    monkeypatch.setattr(module, "_ROOTS", [])
    monkeypatch.setenv(ROOT_ENVIRONMENT_VARIABLE, descriptor)
    with pytest.raises(RuntimeError, match="inherit"):
        sqlite3.connect(arbitrary / "never-opened.db")
    assert not (arbitrary / "never-opened.db").exists()


@pytest.mark.parametrize("protected", ["root", "child-database"])
def test_root_policy_independently_rejects_operational_roots_and_ancestors(monkeypatch, protected):
    module = importlib.import_module("backend.database.disposable")
    root = create_disposable_root()
    descriptor = root.export()
    artificial_protected = root.path if protected == "root" else root.path / "database-artificial"
    monkeypatch.setattr(module, "_PROTECTED_TREES", (*module._PROTECTED_TREES, artificial_protected))
    with pytest.raises(RuntimeError, match="operational location"):
        adopt_disposable_root(descriptor)
    with pytest.raises(RuntimeError, match="operational location"):
        root.verify()


def test_root_policy_rejects_bad_allocation_location_before_creating(tmp_path, monkeypatch):
    module = importlib.import_module("backend.database.disposable")
    fake_workspace = tmp_path / "artificial-workspace"
    fake_workspace.mkdir()
    monkeypatch.setattr(module, "_PROTECTED_TREES", (*module._PROTECTED_TREES, fake_workspace))
    monkeypatch.setattr(module, "_system_disposable_parent", lambda: fake_workspace)
    with pytest.raises(RuntimeError, match="operational location"):
        create_disposable_root()
    assert list(fake_workspace.iterdir()) == []


def test_root_policy_created_root_and_inherited_identity_are_real():
    root = create_disposable_root()
    inherited = adopt_disposable_root(root.export())
    assert inherited.path == root.path
    assert inherited.chain == root.chain
    assert inherited.marker_identity == root.marker_identity
    root.verify()
    inherited.verify()
    target = root.path / "real-synthetic.db"
    with sqlite3.connect(target) as db:
        db.execute("CREATE TABLE synthetic (id INTEGER)")
        db.execute("INSERT INTO synthetic VALUES (1)")
    with sqlite3.connect(target) as db:
        assert Path(db.execute("PRAGMA database_list").fetchone()[2]) == target
        assert db.execute("SELECT id FROM synthetic").fetchall() == [(1,)]


def test_root_policy_physical_replacement_is_refused_without_links():
    root = create_disposable_root()
    old_identity = root.chain[-1][1]
    moved = root.path.with_name(root.path.name + "-original")
    root.path.rename(moved)
    root.path.mkdir()
    module = importlib.import_module("backend.database.disposable")
    assert module._inspect(root.path, directory=True) != old_identity
    with pytest.raises(RuntimeError, match="identity"):
        sqlite3.connect(root.path / "never-opened.db")
    assert not (root.path / "never-opened.db").exists()


def test_root_policy_resolution_drift_cannot_widen_authority(tmp_path, monkeypatch):
    root = create_disposable_root()
    redirected = tmp_path / "artificial-protected"
    original = Path.resolve
    def changed(path, *args, **kwargs):
        return redirected if path == root.path else original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "resolve", changed)
    with pytest.raises(RuntimeError, match="identity or location"):
        sqlite3.connect(root.path / "never-opened.db")
    with pytest.raises(RuntimeError):
        require_disposable_sqlite_path(redirected / "never-opened.db", roots=(root,))


def test_root_policy_unknown_identity_is_fail_closed(monkeypatch):
    root = create_disposable_root()
    module = importlib.import_module("backend.database.disposable")
    original = module._inspect
    def unavailable(path, **kwargs):
        if path == root.path:
            raise PermissionError("synthetic identity unavailable")
        return original(path, **kwargs)
    monkeypatch.setattr(module, "_inspect", unavailable)
    with pytest.raises(RuntimeError, match="Cannot verify"):
        sqlite3.connect(root.path / "never-opened.db")


def test_root_policy_changed_marker_is_refused():
    root = create_disposable_root()
    module = importlib.import_module("backend.database.disposable")
    (root.path / module._MARKER).write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="proof changed"):
        sqlite3.connect(root.path / "never-opened.db")


def test_root_policy_file_escape_and_changed_component_are_refused(tmp_path, monkeypatch):
    root = create_disposable_root()
    with pytest.raises(RuntimeError):
        require_disposable_sqlite_path(root.path / ".." / "escape.db", roots=(root,))
    original = Path.resolve
    target = root.path / "redirected.db"
    def changed(path, *args, **kwargs):
        return tmp_path / "protected.db" if path == target else original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "resolve", changed)
    with pytest.raises(RuntimeError, match="redirected"):
        sqlite3.connect(target)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_root_policy_post_open_inconsistency_closes_connection(monkeypatch, asynchronous):
    module = importlib.import_module("backend.database.disposable")
    root = create_disposable_root()
    path = root.path / "post-check.db"
    url = f"sqlite+aiosqlite:///{path.as_posix()}"
    monkeypatch.setenv("TEST_DATABASE_URL", url)
    connections = []
    closed = []
    class ObservedConnection(sqlite3.Connection):
        def close(self):
            closed.append(self)
            return super().close()
    original = sqlite3.connect
    def record(*args, **kwargs):
        kwargs["factory"] = ObservedConnection
        connection = original(*args, **kwargs)
        connections.append(connection)
        return connection
    def changed(*args):
        raise RuntimeError("synthetic identity changed after open")
    monkeypatch.setattr(sqlite3, "connect", record)
    monkeypatch.setattr(module, "_after_script_open", changed)
    async def attempt():
        async with disposable_script_async_session(url) as db:
            await db.execute(text("SELECT 1"))
    with pytest.raises(RuntimeError, match="after open"):
        if asynchronous:
            asyncio.run(attempt())
        else:
            with disposable_script_session(url) as db:
                db.execute(text("SELECT 1"))
    assert len(connections) == 1
    assert closed == connections


def test_root_policy_windows_reparse_flag_is_refused(monkeypatch):
    from types import SimpleNamespace
    root = create_disposable_root()
    original = Path.lstat
    def reparse(path, *args, **kwargs):
        if path == root.path:
            info = original(path, *args, **kwargs)
            return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", reparse)
    with pytest.raises(RuntimeError, match="Reparse"):
        sqlite3.connect(root.path / "never-opened.db")


def test_root_policy_rejects_real_hard_links():
    root = create_disposable_root()
    first, second = root.path / "synthetic-file", root.path / "linked.db"
    first.write_bytes(b"synthetic data only")
    try:
        os.link(first, second)
    except OSError as exc:
        pytest.skip(f"Hard-link creation unavailable: {exc.errno}")
    assert second.stat().st_nlink == 2
    with pytest.raises(RuntimeError, match="one link"):
        sqlite3.connect(second)
