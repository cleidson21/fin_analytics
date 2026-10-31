"""Explicit SQLite boundary for test and development write paths.

The application does not call this module; its configured database remains usable.
"""

import os
import json
import sqlite3
import stat
import tempfile
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit
from uuid import UUID, uuid4

import aiosqlite
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker


ROOT_ENVIRONMENT_VARIABLE = "FINANALYTICS_DISPOSABLE_ROOT"
_WORKSPACE = Path(__file__).resolve().parents[2]
# Independent of TEMP/TMP and of the requested DATABASE_URL. Protect the whole
# operational checkout, including database, WAL/SHM, backups and private files.
_PROTECTED_TREES = (_WORKSPACE,)
_MARKER = ".finanalytics-disposable-root.json"
_ROOTS = []


def _system_disposable_parent() -> Path:
    """Use the Windows known folder, never TEMP/TMP or tempfile.gettempdir()."""
    if os.name != "nt":
        return Path("/tmp")
    import ctypes

    class GUID(ctypes.Structure):
        _fields_ = [("data1", ctypes.c_ulong), ("data2", ctypes.c_ushort),
                    ("data3", ctypes.c_ushort), ("data4", ctypes.c_ubyte * 8)]

    folder_id = GUID.from_buffer_copy(UUID("F1B32785-6FBA-4FCF-9D55-7B8E7F157091").bytes_le)
    result = ctypes.c_wchar_p()
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    shell.SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID), ctypes.c_uint32, ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p)]
    shell.SHGetKnownFolderPath.restype = ctypes.c_long
    if shell.SHGetKnownFolderPath(ctypes.byref(folder_id), 0, None, ctypes.byref(result)) != 0:
        raise RuntimeError("Cannot establish the system disposable location")
    try:
        return Path(result.value) / "Temp"
    finally:
        free = ctypes.WinDLL("ole32").CoTaskMemFree
        free.argtypes = [ctypes.c_void_p]
        free.restype = None
        free(ctypes.cast(result, ctypes.c_void_p))


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _deny_operational(path: Path, *, root: bool = False) -> None:
    for protected in _PROTECTED_TREES:
        if path.is_relative_to(protected) or (root and protected.is_relative_to(path)):
            raise RuntimeError("Refusing an operational location for disposable SQLite")


def _windows_identity(path: Path) -> tuple[int, int]:
    """Some Windows ancestors report st_ino=0; query their native file ID."""
    import ctypes
    from ctypes import wintypes

    class FILE_ID_INFO(ctypes.Structure):
        _fields_ = [("volume", ctypes.c_ulonglong), ("file_id", ctypes.c_ubyte * 16)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateFileW(str(path), 0x80, 7, None, 3, 0x02200000, None)
    if handle == wintypes.HANDLE(-1).value:
        raise RuntimeError("Cannot open a directory for identity verification")
    try:
        identity = FILE_ID_INFO()
        if not kernel.GetFileInformationByHandleEx(handle, 18, ctypes.byref(identity), ctypes.sizeof(identity)):
            raise RuntimeError("Native filesystem identity is unavailable")
        file_id = int.from_bytes(bytes(identity.file_id), "little")
        if not file_id:
            raise RuntimeError("Native filesystem identity is unavailable")
        return identity.volume, file_id
    finally:
        kernel.CloseHandle(handle)


def _identity(info, path: Path | None = None) -> tuple[int, int, int | None]:
    if info.st_ino:
        device, inode = info.st_dev, info.st_ino
    elif os.name == "nt" and path is not None:
        device, inode = _windows_identity(path)
    else:
        raise RuntimeError("Filesystem identity is unavailable")
    return device, inode, getattr(info, "st_birthtime_ns", None)


def _inspect(path: Path, *, directory: bool, identity_required: bool = True):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise RuntimeError("Reparse points and symbolic links are not disposable authority")
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError("Disposable root component is not a directory")
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RuntimeError("Disposable SQLite files must be regular files with one link")
    if not identity_required and not info.st_ino:
        # Above the OS-known allocation directory, the OS namespace is trusted.
        # Reparse/type checks still apply; the allocation directory and every
        # component below it always require a physical identity.
        return None, None, None
    return _identity(info, path)


def _directory_chain(path: Path):
    anchor = _absolute(_system_disposable_parent())
    return tuple((component, _inspect(component, directory=True, identity_required=component.is_relative_to(anchor)))
                 for component in (*reversed(path.parents), path))


def _read_marker(path: Path):
    marker = path / _MARKER
    identity = _inspect(marker, directory=False)
    with marker.open("r", encoding="utf-8") as stream:
        if _identity(os.fstat(stream.fileno())) != identity:
            raise RuntimeError("Disposable root marker changed while opening")
        data = json.load(stream)
    return identity, data


@dataclass(frozen=True)
class DisposableRoot:
    """A created directory capability, not a caller-selected path allowlist.

    Checks are deliberately scoped to a controlled test/development process.
    They are not an atomic, hostile-filesystem open primitive. No other process
    may rename or populate these fresh directories while they are in use.
    """

    path: Path
    chain: tuple
    marker_identity: tuple
    descriptor: str

    def verify(self) -> None:
        try:
            _deny_operational(self.path, root=True)
            if self.path.parent != _absolute(_system_disposable_parent()):
                raise RuntimeError("Disposable root is outside the system allocation location")
            if _directory_chain(self.path) != self.chain or self.path.resolve(strict=True) != self.path:
                raise RuntimeError("Disposable root identity or location changed")
            marker_identity, data = _read_marker(self.path)
            if marker_identity != self.marker_identity or json.loads(self.descriptor) != data:
                raise RuntimeError("Disposable root creation proof changed")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise RuntimeError("Cannot verify disposable root identity") from exc

    def export(self) -> str:
        self.verify()
        return self.descriptor


def create_disposable_root() -> DisposableRoot:
    """Create an exclusive per-run root; merely choosing TEMP grants nothing."""
    try:
        parent = _absolute(_system_disposable_parent())
        _deny_operational(parent)
        _directory_chain(parent)
        if parent.resolve(strict=True) != parent:
            raise RuntimeError("System allocation location is redirected")
        path = Path(tempfile.mkdtemp(prefix="finanalytics-disposable-", dir=parent))
        _deny_operational(path, root=True)
        chain = _directory_chain(path)
        data = {"version": 1, "path": str(path), "identity": list(chain[-1][1]), "nonce": uuid4().hex}
        descriptor = json.dumps(data, sort_keys=True)
        with (path / _MARKER).open("x", encoding="utf-8") as stream:
            stream.write(descriptor)
        root = DisposableRoot(path, chain, _inspect(path / _MARKER, directory=False), descriptor)
        root.verify()
        _ROOTS.append(root)
        return root
    except (OSError, ValueError, TypeError) as exc:
        raise RuntimeError("Cannot create a verified disposable root") from exc


def adopt_disposable_root(descriptor: str) -> DisposableRoot:
    """Inherit a root only with its on-disk creation proof and physical identity.

    The descriptor alone, including one supplied through an environment
    variable, cannot authorize an arbitrary directory or operational location.
    """
    try:
        data = json.loads(descriptor)
        if set(data) != {"version", "path", "identity", "nonce"} or data["version"] != 1 or len(data["nonce"]) != 32:
            raise RuntimeError("Invalid disposable root descriptor")
        path = _absolute(Path(data["path"]))
        _deny_operational(path, root=True)
        if path.parent != _absolute(_system_disposable_parent()):
            raise RuntimeError("Disposable root is outside the system allocation location")
        chain = _directory_chain(path)
        marker_identity, marker_data = _read_marker(path)
        if list(chain[-1][1]) != data["identity"] or marker_data != data:
            raise RuntimeError("Disposable root creation proof does not match")
        root = DisposableRoot(path, chain, marker_identity, descriptor)
        root.verify()
        _ROOTS.append(root)
        return root
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise RuntimeError("Cannot inherit a verified disposable root") from exc


def disposable_roots() -> tuple[DisposableRoot, ...]:
    if not _ROOTS:
        descriptor = os.environ.get(ROOT_ENVIRONMENT_VARIABLE)
        if not descriptor:
            raise RuntimeError("No trusted disposable SQLite root is registered")
        adopt_disposable_root(descriptor)
    return tuple(_ROOTS)


def require_disposable_sqlite_path(
    database: os.PathLike[str] | str,
    *,
    roots: tuple[DisposableRoot, ...] | None = None,
    allow_memory: bool = True,
) -> Path | None:
    """Reject any SQLite target outside explicit disposable directories.

    Resolve links before comparing paths, so a symlink inside a temporary
    directory cannot redirect a connection to an operational database.
    """
    value = os.fspath(database)
    if value == ":memory:":
        if allow_memory:
            return None
        raise RuntimeError("A file-backed disposable SQLite database is required")
    if not isinstance(value, str) or not value or "\x00" in value or value.startswith(":"):
        raise RuntimeError("An unambiguous SQLite filename is required")
    if value.lower().startswith("file:"):
        uri = urlsplit(value)
        try:
            parameters = parse_qsl(uri.query, keep_blank_values=True, strict_parsing=True)
        except ValueError as exc:
            raise RuntimeError("Ambiguous SQLite file URI") from exc
        if (
            not value.startswith("file:")
            or uri.netloc not in {"", "localhost"}
            or "#" in value
            or (parameters and parameters not in [[("mode", "ro")], [("mode", "rw")], [("mode", "rwc")]])
        ):
            raise RuntimeError("Ambiguous SQLite file URI")
        value = unquote(uri.path)
        if os.name == "nt" and len(value) > 2 and value[0] == "/" and value[2] == ":":
            value = value[1:]
        # URI memory aliases and relative URI paths are deliberately unsupported.
        # In particular, :memory:/../... is a disk path to SQLite on Windows.
        if not Path(value).is_absolute() or "\x00" in value:
            raise RuntimeError("SQLite file URI must identify an absolute disposable file")
    target = _absolute(Path(value))
    _deny_operational(target)
    authorized = disposable_roots() if roots is None else roots
    for root in authorized:
        if not isinstance(root, DisposableRoot):
            raise RuntimeError("A verified disposable root capability is required")
        if not target.is_relative_to(root.path) or target == root.path:
            continue
        if target == root.path / _MARKER:
            raise RuntimeError("Disposable root proof is not a database target")
        root.verify()
        try:
            # Inspect existing components without granting authority to their
            # resolved destinations. Never resolve an allow-root into new scope.
            for component in reversed(target.parents):
                if component.is_relative_to(root.path) and component.exists():
                    _inspect(component, directory=True)
            if target.exists() or target.is_symlink():
                _inspect(target, directory=False)
            resolved = target.resolve()
            _deny_operational(resolved)
            if resolved != target or not resolved.is_relative_to(root.path):
                raise RuntimeError("Disposable SQLite destination was redirected")
            return target
        except OSError as exc:
            raise RuntimeError("Cannot verify disposable SQLite destination") from exc
    raise RuntimeError("Refusing SQLite access outside disposable test directories")


def require_disposable_sqlite_url(
    database_url: str,
    *,
    roots: tuple[DisposableRoot, ...] | None = None,
    allow_memory: bool = True,
) -> Path | None:
    try:
        url = make_url(database_url)
    except (ArgumentError, ValueError) as exc:
        raise RuntimeError("A disposable SQLite database URL is required") from exc
    if (
        url.drivername not in {"sqlite", "sqlite+aiosqlite"}
        or url.query
        or url.username is not None
        or url.password is not None
        or url.host is not None
        or url.port is not None
    ):
        raise RuntimeError("A disposable SQLite database URL is required")
    if url.database in {None, ""}:
        if allow_memory:
            return None
        raise RuntimeError("A file-backed disposable SQLite database is required")
    if url.database.lower().startswith("file:"):
        raise RuntimeError("SQLite URL URI options are not supported for disposable databases")
    return require_disposable_sqlite_path(
        url.database,
        roots=roots,
        allow_memory=allow_memory,
    )


def require_explicit_disposable_script_database(database_url: str) -> Path:
    """Seed/reset scripts require matching URLs inside a verified created root."""
    configured = os.environ.get("TEST_DATABASE_URL")
    if not configured:
        raise RuntimeError("Set TEST_DATABASE_URL and DATABASE_URL to the same disposable SQLite URL")
    path = require_disposable_sqlite_url(database_url, allow_memory=False)
    explicit_path = require_disposable_sqlite_url(configured, allow_memory=False)
    if path is None or explicit_path is None or path != explicit_path:
        raise RuntimeError("TEST_DATABASE_URL and DATABASE_URL must identify the same disposable file")
    return path


def _script_connection_path(path: Path) -> str:
    # Recheck at connection time; configuration changes cannot change the captured
    # target, and a newly introduced symlink cannot redirect it outside temp.
    if require_disposable_sqlite_path(path) != path:
        raise RuntimeError("Disposable database target changed before connection")
    return str(path)


def _before_script_open(path: Path):
    _script_connection_path(path)
    return _directory_chain(path.parent), _inspect(path, directory=False) if path.exists() else None


def _after_script_open(path: Path, before) -> None:
    # Detection/close after open is an extra consistency check, not a claim that
    # metadata verification and native SQLite open are one atomic operation.
    _script_connection_path(path)
    parents, previous_file = before
    if _directory_chain(path.parent) != parents or (previous_file is not None and _inspect(path, directory=False) != previous_file):
        raise RuntimeError("Disposable SQLite identity changed during connection")


@contextmanager
def disposable_script_session(database_url: str):
    """Own the engine/session; no caller engine, creator or connect_args accepted."""
    path = require_explicit_disposable_script_database(database_url)

    def connect():
        before = _before_script_open(path)
        connection = sqlite3.connect(_script_connection_path(path))
        try:
            _after_script_open(path, before)
            connection.execute("PRAGMA foreign_keys=ON")
        except BaseException:
            connection.close()
            raise
        return connection

    engine = create_engine(URL.create("sqlite", database=str(path)), creator=connect)
    try:
        with sessionmaker(bind=engine, autoflush=False)() as session:
            yield session
    finally:
        engine.dispose()


@asynccontextmanager
async def disposable_script_async_session(database_url: str):
    """Use a fixed internal async creator rather than a cached runtime engine."""
    path = require_explicit_disposable_script_database(database_url)

    async def connect():
        before = _before_script_open(path)
        connection = await aiosqlite.connect(_script_connection_path(path))
        try:
            _after_script_open(path, before)
            async with connection.execute("PRAGMA foreign_keys=ON"):
                pass
        except BaseException:
            await connection.close()
            raise
        return connection

    engine = create_async_engine(
        URL.create("sqlite+aiosqlite", database=str(path)), async_creator=connect,
    )
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            yield session
    finally:
        await engine.dispose()
