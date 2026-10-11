from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.orm import sessionmaker

from backend.application.services.external_observation_store import (
    ExternalObservationStoreService,
    SQLiteImmediateUnitOfWork,
)
from backend.core.config import settings
from backend.domains.external_context import (
    DecimalNormalizationError,
    EXTERNAL_SERIES_REGISTRY_VERSION,
    ExternalContextPersistenceError,
    ExternalContextPersistenceErrorCode,
    ObservationWriteDisposition,
    PersistedObservationEvent,
    Provider,
    RegistryKey,
    build_content_fingerprint_v1,
    normalize_external_observation,
)
from backend.infrastructure.persistence.models.external_context import (
    ExternalObservationVersionModel,
    ExternalSeriesSyncStateModel,
)
from backend.infrastructure.persistence.repositories.external_context import (
    ExternalObservationRepository,
    ExternalSeriesSyncStateRepository,
)


R3D_REVISION = "4f9c2d7e1a6b"
PRE_R3D_REVISION = "2d6b4f8a9c1e"


def _config_for(database_path: Path, monkeypatch) -> Config:
    assert database_path.parent != Path("database")
    assert database_path.name != "fin_analytics.db"
    monkeypatch.setattr(
        settings,
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{database_path.as_posix()}",
    )
    return Config("alembic.ini")


def _prepare_previous_head(database_path: Path) -> None:
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": PRE_R3D_REVISION},
        )
    engine.dispose()


@pytest.fixture
def store_db(tmp_path, monkeypatch):
    database_path = tmp_path / "external_store.db"
    _prepare_previous_head(database_path)
    command.upgrade(_config_for(database_path, monkeypatch), R3D_REVISION)
    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine, sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


def _payload(value: str, *, day: str = "2026-10-09") -> dict[str, object]:
    return {
        "provider": "BCB_SGS",
        "series_id": "432",
        "reference_period_start": day,
        "reference_period_end": day,
        "semantic_class": "EXTERNAL_OBSERVATION",
        "frequency": "DAILY",
        "value_text": value,
        "value_scale": 2,
        "unit": "PERCENT_PER_YEAR",
        "currency": None,
        "scope": "BR",
    }


def _observation(
    value: str,
    *,
    retrieved_at: datetime,
    day: str = "2026-10-09",
):
    return normalize_external_observation(
        _payload(value, day=day),
        retrieved_at=retrieved_at,
    )


class _Clock:
    def __init__(self, *values: datetime) -> None:
        self._values = iter(values)

    def __call__(self) -> datetime:
        return next(self._values)


def test_begin_immediate_head_dedup_a_b_a_sequence_and_sync_are_atomic(store_db):
    engine, factory = store_db
    statements: list[str] = []

    @event.listens_for(engine, "before_cursor_execute")
    def _capture(_connection, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement.strip().upper())

    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    times = [retrieved + timedelta(seconds=value) for value in (1, 2, 3, 4)]
    session = factory()
    service = ExternalObservationStoreService(session, utc_clock=_Clock(*times))

    first = service.ingest(_observation("10.50", retrieved_at=retrieved))
    repeated = service.ingest(_observation("10.5", retrieved_at=retrieved))
    second = service.ingest(_observation("10.75", retrieved_at=retrieved))
    reverted = service.ingest(_observation("10.50", retrieved_at=retrieved))

    assert first.disposition is ObservationWriteDisposition.INSERTED
    assert repeated.disposition is ObservationWriteDisposition.RETRANSMISSION
    assert second.disposition is ObservationWriteDisposition.INSERTED
    assert reverted.disposition is ObservationWriteDisposition.INSERTED
    assert [first.event.knowledge_sequence, second.event.knowledge_sequence, reverted.event.knowledge_sequence] == [1, 2, 3]
    assert second.event.supersedes_event_id == first.event.observation_event_id
    assert reverted.event.supersedes_event_id == second.event.observation_event_id
    assert reverted.event.content_fingerprint == first.event.content_fingerprint
    assert reverted.event.observation_event_id != first.event.observation_event_id

    events = ExternalObservationRepository(session).list_identity(first.event.observation.economic_identity)
    assert len(events) == 3
    sync = ExternalSeriesSyncStateRepository(session).get(RegistryKey.BCB_SGS_SELIC_TARGET)
    assert sync is not None
    assert sync.last_valid_observation_event_id == reverted.event.observation_event_id
    assert sync.accepted_transitions == 3
    assert sync.observations_received == 4
    assert sync.consecutive_retransmissions == 0
    begin_positions = [index for index, statement in enumerate(statements) if statement == "BEGIN IMMEDIATE"]
    select_positions = [index for index, statement in enumerate(statements) if statement.startswith("SELECT")]
    assert len(begin_positions) == 4
    assert all(
        begin < next(position for position in select_positions if position > begin)
        for begin in begin_positions
    )
    session.close()


def test_as_of_uses_independent_economic_and_logical_cuts(store_db):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    t1, t2, t3 = (retrieved + timedelta(seconds=value) for value in (1, 2, 3))
    session = factory()
    service = ExternalObservationStoreService(session, utc_clock=_Clock(t1, t2, t3))
    a1 = service.ingest(_observation("10.50", retrieved_at=retrieved)).event
    b2 = service.ingest(_observation("10.75", retrieved_at=retrieved)).event
    a3 = service.ingest(_observation("10.50", retrieved_at=retrieved)).event
    identity = a1.observation.economic_identity

    assert service.get_identity_as_of(
        identity,
        consumer_as_of_date=date(2026, 10, 9),
        consumer_as_of_timestamp=t1 - timedelta(microseconds=1),
    ) is None
    assert service.get_identity_as_of(
        identity,
        consumer_as_of_date=date(2026, 10, 9),
        consumer_as_of_timestamp=t1,
    ).observation_event_id == a1.observation_event_id
    assert service.get_identity_as_of(
        identity,
        consumer_as_of_date=date(2026, 10, 9),
        consumer_as_of_timestamp=t2,
    ).observation_event_id == b2.observation_event_id
    assert service.get_identity_as_of(
        identity,
        consumer_as_of_date=date(2026, 10, 9),
        consumer_as_of_timestamp=t3,
    ).observation_event_id == a3.observation_event_id
    assert service.get_identity_as_of(
        identity,
        consumer_as_of_date=date(2026, 10, 8),
        consumer_as_of_timestamp=t3,
    ) is None
    session.close()


def test_latest_series_as_of_does_not_look_ahead_to_later_period_or_knowledge(store_db):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    t1, t2 = retrieved + timedelta(seconds=1), retrieved + timedelta(seconds=2)
    session = factory()
    service = ExternalObservationStoreService(session, utc_clock=_Clock(t1, t2))
    older = service.ingest(_observation("10.50", retrieved_at=retrieved, day="2026-10-08")).event
    later = service.ingest(_observation("10.75", retrieved_at=retrieved, day="2026-10-09")).event

    assert service.get_latest_series_as_of(
        provider=Provider.BCB_SGS,
        series_id="432",
        consumer_as_of_date=date(2026, 10, 8),
        consumer_as_of_timestamp=t2,
    ).observation_event_id == older.observation_event_id
    assert service.get_latest_series_as_of(
        provider=Provider.BCB_SGS,
        series_id="432",
        consumer_as_of_date=date(2026, 10, 9),
        consumer_as_of_timestamp=t1,
    ).observation_event_id == older.observation_event_id
    assert service.get_latest_series_as_of(
        provider=Provider.BCB_SGS,
        series_id="432",
        consumer_as_of_date=date(2026, 10, 9),
        consumer_as_of_timestamp=t2,
    ).observation_event_id == later.observation_event_id
    session.close()


def test_clock_regression_rolls_back_event_and_sync(store_db):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    session = factory()
    service = ExternalObservationStoreService(
        session,
        utc_clock=_Clock(retrieved - timedelta(microseconds=1)),
    )
    with pytest.raises(ExternalContextPersistenceError) as failure:
        service.ingest(_observation("10.50", retrieved_at=retrieved))
    assert failure.value.code is ExternalContextPersistenceErrorCode.CLOCK_REGRESSION
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 0
    assert session.scalar(select(func.count()).select_from(ExternalSeriesSyncStateModel)) == 0
    session.close()


def test_failure_after_event_insert_before_sync_rolls_back_everything(store_db, monkeypatch):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    session = factory()
    service = ExternalObservationStoreService(
        session,
        utc_clock=_Clock(retrieved + timedelta(seconds=1)),
    )

    def _fail_save(_self, _state):
        raise RuntimeError("injected sync failure")

    monkeypatch.setattr(ExternalSeriesSyncStateRepository, "save", _fail_save)
    with pytest.raises(RuntimeError, match="injected sync failure"):
        service.ingest(_observation("10.50", retrieved_at=retrieved))
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 0
    assert session.scalar(select(func.count()).select_from(ExternalSeriesSyncStateModel)) == 0
    session.close()


def test_two_independent_writers_serialize_same_identity_without_sequence_race(store_db):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    barrier = Barrier(2)

    def _write():
        session = factory()
        try:
            barrier.wait(timeout=5)
            return ExternalObservationStoreService(
                session,
                utc_clock=lambda: retrieved + timedelta(seconds=1),
                busy_timeout_ms=1000,
                max_attempts=3,
            ).ingest(_observation("10.50", retrieved_at=retrieved))
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _value: _write(), range(2)))

    assert {result.disposition for result in results} == {
        ObservationWriteDisposition.INSERTED,
        ObservationWriteDisposition.RETRANSMISSION,
    }
    verify = factory()
    identity = results[0].event.observation.economic_identity
    events = ExternalObservationRepository(verify).list_identity(identity)
    assert len(events) == 1
    assert events[0].knowledge_sequence == 1
    sync = ExternalSeriesSyncStateRepository(verify).get(RegistryKey.BCB_SGS_SELIC_TARGET)
    assert sync.observations_received == 2
    assert sync.accepted_transitions == 1
    assert sync.consecutive_retransmissions == 1
    verify.close()


def test_uncommitted_event_is_invisible_but_logical_cut_inside_commit_window_replays_after_commit(store_db):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    known = retrieved + timedelta(seconds=1)
    observation = _observation("10.50", retrieved_at=retrieved)
    fingerprint = build_content_fingerprint_v1(observation.content.as_payload_v1())
    event_value = PersistedObservationEvent(
        observation_event_id="00000000-0000-0000-0000-000000000101",
        observation=observation,
        registry_contract_version=EXTERNAL_SERIES_REGISTRY_VERSION,
        content_fingerprint_version=fingerprint.content_fingerprint_version,
        content_fingerprint=fingerprint.content_fingerprint,
        ingested_at=known,
        known_from=known,
        knowledge_sequence=1,
        supersedes_event_id=None,
    )
    writer = factory()
    uow = SQLiteImmediateUnitOfWork(writer, busy_timeout_ms=250)
    uow.begin_immediate()
    ExternalObservationRepository(writer).insert(event_value)

    reader = factory()
    assert ExternalObservationRepository(reader).get_head(observation.economic_identity) is None
    reader.close()
    uow.commit()

    replay = factory()
    selected = ExternalObservationRepository(replay).get_identity_as_of(
        observation.economic_identity,
        consumer_as_of_date=date(2026, 10, 9),
        consumer_as_of_timestamp=known + timedelta(seconds=2),
    )
    assert selected.observation_event_id == event_value.observation_event_id
    replay.close()
    writer.close()


def test_read_revalidation_rejects_wrong_fingerprint(store_db):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    session = factory()
    event_value = ExternalObservationStoreService(
        session,
        utc_clock=_Clock(retrieved + timedelta(seconds=1)),
    ).ingest(_observation("10.50", retrieved_at=retrieved)).event
    session.execute(
        text(
            "INSERT INTO external_observation_versions "
            "SELECT '00000000-0000-0000-0000-000000000202', registry_key, provider, series_id, "
            "series_concept, semantic_class, '2026-10-08', '2026-10-08', value_text, value_scale, "
            "unit, currency, frequency, scope, registry_contract_version, content_fingerprint_version, "
            "'sha256:' || :digest, provider_value_text, provider_decimal_places, source_url, license_id, "
            "attribution, retrieved_at, observed_at, published_at, provider_revision_id, revised_at, "
            "ingested_at, known_from, 1, NULL FROM external_observation_versions "
            "WHERE observation_event_id = :source"
        ),
        {"digest": "0" * 64, "source": event_value.observation_event_id},
    )
    session.commit()
    identity = _observation("10.50", retrieved_at=retrieved, day="2026-10-08").economic_identity
    with pytest.raises(ExternalContextPersistenceError) as failure:
        ExternalObservationRepository(session).get_head(identity)
    assert failure.value.code is ExternalContextPersistenceErrorCode.FINGERPRINT_MISMATCH
    session.close()


def test_failed_attempt_preserves_last_known_good_and_history(store_db):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    session = factory()
    service = ExternalObservationStoreService(
        session,
        utc_clock=_Clock(retrieved + timedelta(seconds=1)),
    )
    inserted = service.ingest(_observation("10.50", retrieved_at=retrieved)).event
    state = service.record_failed_attempt(
        registry_key=RegistryKey.BCB_SGS_SELIC_TARGET,
        attempted_at=retrieved + timedelta(hours=1),
        error_code="PROVIDER_TIMEOUT",
        http_status=None,
        next_retry_at=retrieved + timedelta(hours=1, minutes=5),
    )
    assert state.last_valid_observation_event_id == inserted.observation_event_id
    assert state.last_success_at == retrieved
    assert state.last_attempt_result.value == "FAILED"
    assert ExternalObservationRepository(session).get_head(inserted.observation.economic_identity).observation_event_id == inserted.observation_event_id
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 1
    session.close()


def test_sync_initialization_has_registry_version_without_acquisition_evidence(store_db):
    _engine, factory = store_db
    session = factory()
    uow = SQLiteImmediateUnitOfWork(session, busy_timeout_ms=250)
    uow.begin_immediate()
    state = ExternalSeriesSyncStateRepository(session).initialize(RegistryKey.BCB_SGS_CDI)
    uow.commit()
    assert state.registry_contract_version == EXTERNAL_SERIES_REGISTRY_VERSION
    assert state.last_attempt_at is None
    assert state.last_success_at is None
    assert state.last_valid_observation_event_id is None
    assert state.coverage_start is None
    assert state.last_attempt_result is None
    session.close()


def test_decimal_text_roundtrip_survives_close_reopen_and_float_is_rejected_before_write(store_db):
    engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    writer = factory()
    inserted = ExternalObservationStoreService(
        writer,
        utc_clock=_Clock(retrieved + timedelta(seconds=1)),
    ).ingest(_observation("10.5", retrieved_at=retrieved)).event
    writer.close()

    reopened = factory()
    loaded = ExternalObservationRepository(reopened).get_by_id(inserted.observation_event_id)
    assert loaded.observation.content.value_text == "10.50"
    assert str(loaded.observation.content.value) == "10.50"
    assert reopened.execute(
        text("SELECT typeof(value_text) FROM external_observation_versions")
    ).scalar_one() == "text"
    before = reopened.scalar(select(func.count()).select_from(ExternalObservationVersionModel))
    with pytest.raises(DecimalNormalizationError):
        normalize_external_observation(
            {**_payload("10.50"), "value_text": 10.5},
            retrieved_at=retrieved,
        )
    assert reopened.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == before
    reopened.close()


def test_received_fingerprint_mismatch_fails_before_begin_immediate(store_db):
    engine, factory = store_db
    statements: list[str] = []

    @event.listens_for(engine, "before_cursor_execute")
    def _capture(_connection, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement.strip().upper())

    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    session = factory()
    with pytest.raises(ExternalContextPersistenceError) as failure:
        ExternalObservationStoreService(
            session,
            utc_clock=lambda: retrieved + timedelta(seconds=1),
        ).ingest(
            _observation("10.50", retrieved_at=retrieved),
            expected_content_fingerprint="sha256:" + "0" * 64,
        )
    assert failure.value.code is ExternalContextPersistenceErrorCode.FINGERPRINT_MISMATCH
    assert "BEGIN IMMEDIATE" not in statements
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 0
    session.close()


def test_empty_success_updates_operational_state_without_creating_observation(store_db):
    _engine, factory = store_db
    attempted = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    session = factory()
    state = ExternalObservationStoreService(
        session,
        utc_clock=lambda: attempted,
    ).record_empty_success(
        registry_key=RegistryKey.BCB_SGS_IPCA_MONTHLY,
        attempted_at=attempted,
    )
    assert state.last_attempt_at == attempted
    assert state.last_success_at == attempted
    assert state.last_attempt_result.value == "EMPTY"
    assert state.last_valid_observation_event_id is None
    assert state.coverage_start is None
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 0
    session.close()


def test_busy_retry_rereads_after_writer_reservation_becomes_available(store_db):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    holder = factory()
    SQLiteImmediateUnitOfWork(holder, busy_timeout_ms=1).begin_immediate()
    contender = factory()
    sleep_calls: list[float] = []

    def _release(delay: float) -> None:
        sleep_calls.append(delay)
        holder.rollback()

    result = ExternalObservationStoreService(
        contender,
        utc_clock=lambda: retrieved + timedelta(seconds=1),
        max_attempts=2,
        busy_timeout_ms=1,
        retry_delay_seconds=0,
        sleeper=_release,
    ).ingest(_observation("10.50", retrieved_at=retrieved))
    assert result.disposition is ObservationWriteDisposition.INSERTED
    assert sleep_calls == [0]
    contender.close()
    holder.close()


def test_ambiguous_commit_is_typed_and_never_retried(store_db, monkeypatch):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    session = factory()
    calls = {"clock": 0, "commit": 0}

    def _clock() -> datetime:
        calls["clock"] += 1
        return retrieved + timedelta(seconds=1)

    def _ambiguous(_self) -> None:
        calls["commit"] += 1
        raise RuntimeError("injected ambiguous commit")

    monkeypatch.setattr(SQLiteImmediateUnitOfWork, "commit", _ambiguous)
    with pytest.raises(ExternalContextPersistenceError) as failure:
        ExternalObservationStoreService(
            session,
            utc_clock=_clock,
            max_attempts=3,
        ).ingest(_observation("10.50", retrieved_at=retrieved))
    assert failure.value.code is ExternalContextPersistenceErrorCode.COMMIT_OUTCOME_UNKNOWN
    assert calls == {"clock": 1, "commit": 1}
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 0
    session.close()


def test_two_writers_for_different_identities_are_serialized_without_cross_identity_sequence(store_db):
    _engine, factory = store_db
    retrieved = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
    barrier = Barrier(2)

    def _write(day: str):
        session = factory()
        try:
            barrier.wait(timeout=5)
            return ExternalObservationStoreService(
                session,
                utc_clock=lambda: retrieved + timedelta(seconds=1),
                busy_timeout_ms=1000,
            ).ingest(_observation("10.50", retrieved_at=retrieved, day=day))
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(_write, ("2026-10-08", "2026-10-09")))
    assert all(result.disposition is ObservationWriteDisposition.INSERTED for result in results)
    assert [result.event.knowledge_sequence for result in results] == [1, 1]
    assert len({result.event.observation_event_id for result in results}) == 2
