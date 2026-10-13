from __future__ import annotations

import calendar
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.orm import sessionmaker

from backend.application.ports.external_observation_provider import (
    ExternalObservationProvider,
    ExternalObservationProviderError,
    ProviderAcquisitionResult,
    ProviderAcquisitionStatus,
    ProviderChunkResult,
    ProviderChunkStatus,
    ProviderErrorCode,
    ProviderInterval,
)
from backend.application.services.external_observation_store import (
    ExternalObservationStoreService,
    ObservationIngestionMode,
)
from backend.application.services.governed_external_ingestion import (
    AcquisitionIntent,
    GovernedAcquisitionRequest,
    GovernedExternalIngestionService,
    GovernedIngestionError,
    GovernedIngestionErrorCode,
    GovernedIngestionStage,
    ordinary_revision_interval,
)
from backend.core.config import settings
from backend.domains.external_context import (
    ExternalContextPersistenceErrorCode,
    Frequency,
    ObservationWriteDisposition,
    RegistryKey,
    SyncAttemptResult,
    normalize_external_observation,
    resolve_series_by_key,
)
from backend.infrastructure.external.bcb_sgs_adapter import BCBSGSAdapter
from backend.infrastructure.external.bcb_sgs_client import BCBSGSClient
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
RETRIEVED = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)


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
def ingestion_db(tmp_path, monkeypatch):
    database_path = tmp_path / "governed_ingestion.db"
    assert database_path.resolve() != (Path("database") / "fin_analytics.db").resolve()
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


class _IncrementingClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class _SequenceClock:
    def __init__(self, *values: datetime) -> None:
        self._values = iter(values)

    def __call__(self) -> datetime:
        return next(self._values)


class _SimulatedCrash(BaseException):
    pass


class _FakeProvider(ExternalObservationProvider):
    def __init__(
        self,
        *outcomes: ProviderAcquisitionResult | Exception,
        before_return: Callable[[], None] | None = None,
    ) -> None:
        self._outcomes = iter(outcomes)
        self.before_return = before_return
        self.calls: list[tuple[RegistryKey | str, date, date, str | None]] = []

    def acquire(
        self,
        registry_key: RegistryKey | str,
        start: date,
        end: date,
        *,
        correlation_id: str | None = None,
    ) -> ProviderAcquisitionResult:
        self.calls.append((registry_key, start, end, correlation_id))
        if self.before_return is not None:
            self.before_return()
        outcome = next(self._outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _value_for(registry_key: RegistryKey) -> str:
    return {
        RegistryKey.BCB_SGS_SELIC_TARGET: "10.50",
        RegistryKey.BCB_SGS_SELIC_EFFECTIVE: "0.052788",
        RegistryKey.BCB_SGS_CDI: "0.052788",
        RegistryKey.BCB_SGS_IPCA_MONTHLY: "0.42",
        RegistryKey.BCB_SGS_USD_SELL: "5.4321",
    }[registry_key]


def _observation(
    registry_key: RegistryKey,
    value: str,
    anchor: date,
    *,
    retrieved_at: datetime = RETRIEVED,
):
    definition = resolve_series_by_key(registry_key)
    if definition.frequency is Frequency.MONTHLY:
        start = anchor.replace(day=1)
        end = anchor.replace(day=calendar.monthrange(anchor.year, anchor.month)[1])
    else:
        start = end = anchor
    return normalize_external_observation(
        {
            "provider": definition.provider.value,
            "series_id": definition.series_id,
            "reference_period_start": start.isoformat(),
            "reference_period_end": end.isoformat(),
            "semantic_class": definition.semantic_class.value,
            "frequency": definition.frequency.value,
            "value_text": value,
            "value_scale": definition.normalization_scale,
            "unit": definition.unit.value,
            "currency": definition.currency,
            "scope": definition.scope.value,
        },
        retrieved_at=retrieved_at,
    )


def _success_chunk(
    registry_key: RegistryKey,
    interval: ProviderInterval,
    observations: tuple = (),
) -> ProviderChunkResult:
    if not observations:
        observations = (
            _observation(registry_key, _value_for(registry_key), interval.start),
        )
    return ProviderChunkResult(
        registry_key=registry_key,
        interval=interval,
        status=ProviderChunkStatus.SUCCESS,
        response_received=True,
        payload_validated=True,
        normalization_completed=True,
        observations=observations,
        empty_response=False,
        http_attempts=1,
        retrieved_at=RETRIEVED,
        http_status=200,
    )


def _empty_chunk(registry_key: RegistryKey, interval: ProviderInterval) -> ProviderChunkResult:
    return ProviderChunkResult(
        registry_key=registry_key,
        interval=interval,
        status=ProviderChunkStatus.EMPTY,
        response_received=True,
        payload_validated=True,
        normalization_completed=True,
        observations=(),
        empty_response=True,
        http_attempts=1,
        retrieved_at=RETRIEVED,
        http_status=200,
    )


def _failed_chunk(
    registry_key: RegistryKey,
    interval: ProviderInterval,
    *,
    error_code: ProviderErrorCode = ProviderErrorCode.TIMEOUT,
) -> ProviderChunkResult:
    return ProviderChunkResult(
        registry_key=registry_key,
        interval=interval,
        status=ProviderChunkStatus.FAILED,
        response_received=False,
        payload_validated=False,
        normalization_completed=False,
        observations=(),
        empty_response=False,
        http_attempts=1,
        error_code=error_code,
        terminal_failure=True,
    )


def _incomplete_chunk(
    registry_key: RegistryKey,
    interval: ProviderInterval,
) -> ProviderChunkResult:
    return ProviderChunkResult(
        registry_key=registry_key,
        interval=interval,
        status=ProviderChunkStatus.INCOMPLETE,
        response_received=False,
        payload_validated=False,
        normalization_completed=False,
        observations=(),
        empty_response=False,
        error_code=ProviderErrorCode.ACQUISITION_BUDGET_EXHAUSTED,
        terminal_failure=False,
    )


def _result(
    registry_key: RegistryKey,
    requested: ProviderInterval,
    chunks: tuple[ProviderChunkResult, ...],
) -> ProviderAcquisitionResult:
    observations = tuple(
        observation for chunk in chunks for observation in chunk.observations
    )
    complete_count = sum(chunk.is_complete for chunk in chunks)
    if complete_count == len(chunks):
        status = (
            ProviderAcquisitionStatus.SUCCESS
            if observations
            else ProviderAcquisitionStatus.EMPTY
        )
    elif complete_count:
        status = ProviderAcquisitionStatus.PARTIAL
    else:
        status = ProviderAcquisitionStatus.FAILED
    return ProviderAcquisitionResult(
        registry_key=registry_key,
        requested_interval=requested,
        planned_chunks=tuple(chunk.interval for chunk in chunks),
        chunk_results=chunks,
        observations=observations,
        status=status,
    )


def _historical_request(
    interval: ProviderInterval,
    *,
    registry_key: RegistryKey = RegistryKey.BCB_SGS_SELIC_TARGET,
    acquisition_id: str = "r3e3-test",
) -> GovernedAcquisitionRequest:
    return GovernedAcquisitionRequest(
        acquisition_id=acquisition_id,
        registry_key=registry_key,
        intent=AcquisitionIntent.HISTORICAL_RECONCILIATION,
        historical_interval=interval,
    )


def _service(
    session,
    provider: ExternalObservationProvider,
    *,
    operational_clock=lambda: RETRIEVED + timedelta(hours=1),
) -> tuple[GovernedExternalIngestionService, ExternalObservationStoreService]:
    store = ExternalObservationStoreService(
        session,
        utc_clock=_IncrementingClock(RETRIEVED + timedelta(seconds=1)),
    )
    return (
        GovernedExternalIngestionService(
            provider=provider,
            store=store,
            utc_clock=operational_clock,
        ),
        store,
    )


def test_locked_ordinary_revision_windows_and_floors() -> None:
    assert ordinary_revision_interval(
        RegistryKey.BCB_SGS_SELIC_TARGET,
        date(2026, 10, 12),
    ) == ProviderInterval(date(2026, 7, 15), date(2026, 10, 12))
    assert ordinary_revision_interval(
        RegistryKey.BCB_SGS_IPCA_MONTHLY,
        date(2026, 1, 15),
    ) == ProviderInterval(date(2024, 2, 1), date(2026, 1, 15))
    assert ordinary_revision_interval(
        RegistryKey.BCB_SGS_USD_SELL,
        date(1994, 7, 1),
    ) == ProviderInterval(date(1994, 7, 1), date(1994, 7, 1))
    with pytest.raises(ValueError, match="precedes"):
        ordinary_revision_interval(
            RegistryKey.BCB_SGS_USD_SELL,
            date(1994, 6, 30),
        )


def test_request_intent_is_explicit_and_deep_reconciliation_is_bounded() -> None:
    interval = ProviderInterval(date(2000, 1, 1), date(2020, 1, 1))
    request = _historical_request(interval)
    assert request.intent is AcquisitionIntent.HISTORICAL_RECONCILIATION
    assert request.requested_interval == interval
    with pytest.raises(ValueError, match="requires reference_date"):
        GovernedAcquisitionRequest(
            acquisition_id="invalid",
            registry_key=RegistryKey.BCB_SGS_CDI,
            intent=AcquisitionIntent.ORDINARY_REFRESH,
        )
    with pytest.raises(ValueError, match="requires one explicit interval"):
        GovernedAcquisitionRequest(
            acquisition_id="invalid",
            registry_key=RegistryKey.BCB_SGS_CDI,
            intent=AcquisitionIntent.HISTORICAL_RECONCILIATION,
            reference_date=date(2026, 10, 12),
        )


def test_service_construction_has_no_provider_or_store_side_effect(ingestion_db) -> None:
    _engine, factory = ingestion_db
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    provider = _FakeProvider(
        _result(
            RegistryKey.BCB_SGS_SELIC_TARGET,
            interval,
            (_empty_chunk(RegistryKey.BCB_SGS_SELIC_TARGET, interval),),
        )
    )
    session = factory()
    _service(session, provider)
    assert provider.calls == []
    assert session.scalar(select(func.count()).select_from(ExternalSeriesSyncStateModel)) == 0
    session.close()


@pytest.mark.parametrize("registry_key", tuple(RegistryKey))
def test_real_provider_stack_to_disposable_store_for_all_five_registry_keys(
    ingestion_db,
    registry_key: RegistryKey,
) -> None:
    _engine, factory = ingestion_db
    definition = resolve_series_by_key(registry_key)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json=[
                {
                    "data": request.url.params["dataInicial"],
                    "valor": _value_for(registry_key),
                }
            ],
        )

    http_client = httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
    )
    provider = BCBSGSAdapter(
        BCBSGSClient(
            http_client=http_client,
            max_attempts=1,
            utc_clock=lambda: RETRIEVED,
        )
    )
    session = factory()
    service, _store = _service(session, provider)
    request = GovernedAcquisitionRequest(
        acquisition_id=f"all-series-{definition.series_id}",
        registry_key=registry_key,
        intent=AcquisitionIntent.ORDINARY_REFRESH,
        reference_date=date(2026, 10, 12),
    )
    try:
        outcome = service.ingest(request)
    finally:
        http_client.close()

    assert outcome.provider_status is ProviderAcquisitionStatus.SUCCESS
    assert outcome.global_result is SyncAttemptResult.SUCCESS
    assert outcome.persistence_confirmed == 1
    assert outcome.inserted_transitions == 1
    assert outcome.sync_state.last_attempt_result is SyncAttemptResult.SUCCESS
    assert (outcome.sync_state.coverage_start, outcome.sync_state.coverage_end) == (
        request.requested_interval.start,
        request.requested_interval.end,
    )
    event_row = session.scalar(select(func.count()).select_from(ExternalObservationVersionModel))
    assert event_row == 1
    session.close()


def test_monthly_economic_period_is_preserved_through_persistence(ingestion_db) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_IPCA_MONTHLY
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 12))
    observation = _observation(key, "0.42", date(2026, 10, 1))
    provider = _FakeProvider(_result(key, interval, (_success_chunk(key, interval, (observation,)),)))
    session = factory()
    service, _store = _service(session, provider)
    outcome = service.ingest(_historical_request(interval, registry_key=key))
    event_value = ExternalObservationRepository(session).get_head(observation.economic_identity)
    assert outcome.global_result is SyncAttemptResult.SUCCESS
    assert event_value is not None
    assert event_value.observation.content.reference_period.start == date(2026, 10, 1)
    assert event_value.observation.content.reference_period.end == date(2026, 10, 31)
    assert event_value.observation.provenance.retrieved_at == RETRIEVED
    assert event_value.observation.provenance.published_at is None
    assert event_value.ingested_at == event_value.known_from
    assert event_value.known_from > RETRIEVED
    session.close()


@pytest.mark.parametrize(
    ("chunk_kinds", "provider_status", "global_result", "event_count"),
    [
        (("empty", "empty"), ProviderAcquisitionStatus.EMPTY, SyncAttemptResult.EMPTY, 0),
        (("success", "success"), ProviderAcquisitionStatus.SUCCESS, SyncAttemptResult.SUCCESS, 2),
        (("success", "empty"), ProviderAcquisitionStatus.SUCCESS, SyncAttemptResult.SUCCESS, 1),
        (("success", "failed"), ProviderAcquisitionStatus.PARTIAL, SyncAttemptResult.PARTIAL, 1),
        (("empty", "failed"), ProviderAcquisitionStatus.PARTIAL, SyncAttemptResult.PARTIAL, 0),
        (
            ("success", "empty", "failed"),
            ProviderAcquisitionStatus.PARTIAL,
            SyncAttemptResult.PARTIAL,
            1,
        ),
        (("failed", "failed"), ProviderAcquisitionStatus.FAILED, SyncAttemptResult.FAILED, 0),
        (("success", "incomplete"), ProviderAcquisitionStatus.PARTIAL, SyncAttemptResult.PARTIAL, 1),
    ],
)
def test_global_outcomes_follow_persistence_evidence_not_network_success(
    ingestion_db,
    chunk_kinds,
    provider_status,
    global_result,
    event_count,
) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    intervals = tuple(
        ProviderInterval(
            date(2026, 10, 1) + timedelta(days=index * 10),
            date(2026, 10, 10) + timedelta(days=index * 10),
        )
        for index in range(len(chunk_kinds))
    )
    makers = {
        "success": _success_chunk,
        "empty": _empty_chunk,
        "failed": _failed_chunk,
        "incomplete": _incomplete_chunk,
    }
    chunks = tuple(
        makers[kind](key, interval) for kind, interval in zip(chunk_kinds, intervals)
    )
    provider_result = _result(
        key,
        ProviderInterval(intervals[0].start, intervals[-1].end),
        chunks,
    )
    assert provider_result.status is provider_status
    session = factory()
    service, _store = _service(session, _FakeProvider(provider_result))
    outcome = service.ingest(_historical_request(provider_result.requested_interval))
    assert outcome.global_result is global_result
    assert outcome.sync_state.last_attempt_result is global_result
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == event_count
    if global_result in {SyncAttemptResult.PARTIAL, SyncAttemptResult.FAILED}:
        assert outcome.sync_state.coverage_start is None
        assert outcome.sync_state.coverage_end is None
        assert outcome.sync_state.last_success_at is None
    session.close()


def test_discontinuous_success_failed_success_preserves_events_without_coverage(
    ingestion_db,
) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    intervals = tuple(
        ProviderInterval(date(2026, 10, start), date(2026, 10, end))
        for start, end in ((1, 10), (11, 20), (21, 30))
    )
    chunks = (
        _success_chunk(key, intervals[0]),
        _failed_chunk(key, intervals[1]),
        _success_chunk(key, intervals[2]),
    )
    result = _result(key, ProviderInterval(date(2026, 10, 1), date(2026, 10, 30)), chunks)
    session = factory()
    service, _store = _service(session, _FakeProvider(result))
    outcome = service.ingest(_historical_request(result.requested_interval))
    assert outcome.global_result is SyncAttemptResult.PARTIAL
    assert [chunk.persistence_completed for chunk in outcome.chunk_results] == [True, False, True]
    assert outcome.finalization.queried_intervals == (
        type(outcome.finalization.requested_interval)(date(2026, 10, 1), date(2026, 10, 10)),
        type(outcome.finalization.requested_interval)(date(2026, 10, 21), date(2026, 10, 30)),
    )
    assert outcome.sync_state.coverage_start is None
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 2
    session.close()


def test_deferred_mode_is_used_for_every_observation(ingestion_db, monkeypatch) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 2))
    observations = (
        _observation(key, "10.50", date(2026, 10, 1)),
        _observation(key, "10.50", date(2026, 10, 2)),
    )
    result = _result(key, interval, (_success_chunk(key, interval, observations),))
    session = factory()
    service, store = _service(session, _FakeProvider(result))
    modes: list[ObservationIngestionMode] = []
    original = store.ingest

    def capture(observation, **kwargs):
        modes.append(kwargs["acquisition_mode"])
        return original(observation, **kwargs)

    monkeypatch.setattr(store, "ingest", capture)
    service.ingest(_historical_request(interval))
    assert modes == [ObservationIngestionMode.DEFERRED] * 2
    session.close()


def test_persistence_failure_after_commits_is_failed_chunk_with_durable_events(
    ingestion_db,
    monkeypatch,
) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 3))
    observations = tuple(
        _observation(key, "10.50", date(2026, 10, day)) for day in (1, 2, 3)
    )
    result = _result(key, interval, (_success_chunk(key, interval, observations),))
    session = factory()
    service, store = _service(session, _FakeProvider(result))
    original = store.ingest
    calls = 0

    def fail_third(observation, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("injected persistence failure")
        return original(observation, **kwargs)

    monkeypatch.setattr(store, "ingest", fail_third)
    outcome = service.ingest(_historical_request(interval))
    chunk = outcome.chunk_results[0]
    assert outcome.provider_status is ProviderAcquisitionStatus.SUCCESS
    assert outcome.global_result is SyncAttemptResult.FAILED
    assert chunk.persistence_attempted == 3
    assert chunk.persistence_confirmed == 2
    assert chunk.persistence_completed is False
    assert chunk.error_stage is GovernedIngestionStage.PERSISTENCE
    assert chunk.error_code == GovernedIngestionErrorCode.PERSISTENCE_FAILED.value
    assert outcome.sync_state.observations_received == 2
    assert outcome.sync_state.accepted_transitions == 2
    assert outcome.sync_state.last_valid_observation_event_id is not None
    assert outcome.sync_state.coverage_start is None
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 2
    session.close()


def test_failure_on_first_observation_finalizes_failed_without_event(ingestion_db, monkeypatch) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    result = _result(key, interval, (_success_chunk(key, interval),))
    session = factory()
    service, store = _service(session, _FakeProvider(result))
    monkeypatch.setattr(
        store,
        "ingest",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("first write failed")),
    )
    outcome = service.ingest(_historical_request(interval))
    assert outcome.global_result is SyncAttemptResult.FAILED
    assert outcome.chunk_results[0].persistence_attempted == 1
    assert outcome.chunk_results[0].persistence_confirmed == 0
    assert outcome.sync_state.last_attempt_result is SyncAttemptResult.FAILED
    assert outcome.sync_state.observations_received == 0
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 0
    session.close()


def test_failed_chunk_does_not_prevent_later_valid_chunk_persistence(
    ingestion_db,
    monkeypatch,
) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    first_interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 2))
    second_interval = ProviderInterval(date(2026, 10, 3), date(2026, 10, 3))
    first_observations = (
        _observation(key, "10.50", date(2026, 10, 1)),
        _observation(key, "10.50", date(2026, 10, 2)),
    )
    result = _result(
        key,
        ProviderInterval(date(2026, 10, 1), date(2026, 10, 3)),
        (
            _success_chunk(key, first_interval, first_observations),
            _success_chunk(key, second_interval),
        ),
    )
    session = factory()
    service, store = _service(session, _FakeProvider(result))
    original = store.ingest
    calls = 0

    def fail_second(observation, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected persistence failure")
        return original(observation, **kwargs)

    monkeypatch.setattr(store, "ingest", fail_second)
    outcome = service.ingest(_historical_request(result.requested_interval))
    assert outcome.global_result is SyncAttemptResult.PARTIAL
    assert [chunk.persistence_completed for chunk in outcome.chunk_results] == [False, True]
    assert outcome.persistence_confirmed == 2
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 2
    assert outcome.sync_state.coverage_start is None
    session.close()


def test_simulated_crash_between_chunks_preserves_only_committed_event_without_success(
    ingestion_db,
    monkeypatch,
) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    first_interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    second_interval = ProviderInterval(date(2026, 10, 2), date(2026, 10, 2))
    requested = ProviderInterval(first_interval.start, second_interval.end)
    result = _result(
        key,
        requested,
        (_success_chunk(key, first_interval), _success_chunk(key, second_interval)),
    )
    session = factory()
    service, store = _service(session, _FakeProvider(result))
    original = store.ingest
    calls = 0

    def crash_on_second(observation, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise _SimulatedCrash()
        return original(observation, **kwargs)

    monkeypatch.setattr(store, "ingest", crash_on_second)
    with pytest.raises(_SimulatedCrash):
        service.ingest(_historical_request(requested))
    state = ExternalSeriesSyncStateRepository(session).get(key)
    assert state is not None
    assert state.last_attempt_at is None
    assert state.last_success_at is None
    assert state.coverage_start is None
    assert state.observations_received == 1
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 1
    session.close()


def test_partial_acquisition_preserves_prior_finalized_coverage_and_refresh(ingestion_db) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    prior_interval = ProviderInterval(date(2026, 9, 30), date(2026, 9, 30))
    partial_interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 2))
    partial_chunks = (
        _success_chunk(key, ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))),
        _failed_chunk(key, ProviderInterval(date(2026, 10, 2), date(2026, 10, 2))),
    )
    provider = _FakeProvider(
        _result(key, prior_interval, (_success_chunk(key, prior_interval),)),
        _result(key, partial_interval, partial_chunks),
    )
    session = factory()
    service, _store = _service(
        session,
        provider,
        operational_clock=_SequenceClock(
            RETRIEVED + timedelta(hours=1),
            RETRIEVED + timedelta(hours=2),
        ),
    )
    prior = service.ingest(_historical_request(prior_interval, acquisition_id="prior"))
    partial = service.ingest(_historical_request(partial_interval, acquisition_id="partial"))
    assert partial.global_result is SyncAttemptResult.PARTIAL
    assert (partial.sync_state.coverage_start, partial.sync_state.coverage_end) == (
        prior.sync_state.coverage_start,
        prior.sync_state.coverage_end,
    )
    assert partial.sync_state.last_success_at == prior.sync_state.last_success_at
    assert partial.sync_state.next_refresh_eligible_at == prior.sync_state.next_refresh_eligible_at
    assert partial.sync_state.observations_received == prior.sync_state.observations_received + 1
    session.close()


def test_retransmission_and_a_b_a_history_preserve_store_semantics(ingestion_db) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    interval = ProviderInterval(date(2026, 10, 9), date(2026, 10, 9))
    results = tuple(
        _result(
            key,
            interval,
            (
                _success_chunk(
                    key,
                    interval,
                    (_observation(key, value, interval.start),),
                ),
            ),
        )
        for value in ("10.50", "10.50", "10.75", "10.50")
    )
    provider = _FakeProvider(*results)
    session = factory()
    service, _store = _service(
        session,
        provider,
        operational_clock=_SequenceClock(
            RETRIEVED + timedelta(hours=1),
            RETRIEVED + timedelta(hours=2),
            RETRIEVED + timedelta(hours=3),
            RETRIEVED + timedelta(hours=4),
        ),
    )
    outcomes = tuple(
        service.ingest(_historical_request(interval, acquisition_id=f"history-{index}"))
        for index in range(4)
    )
    identity = results[0].observations[0].economic_identity
    events = ExternalObservationRepository(session).list_identity(identity)
    state = ExternalSeriesSyncStateRepository(session).get(key)
    assert [outcome.chunk_results[0].retransmissions for outcome in outcomes] == [0, 1, 0, 0]
    assert [event.knowledge_sequence for event in events] == [1, 2, 3]
    assert events[2].content_fingerprint == events[0].content_fingerprint
    assert state is not None
    assert state.observations_received == 4
    assert state.accepted_transitions == 3
    assert state.last_valid_observation_event_id == events[-1].observation_event_id
    session.close()


def test_provider_runs_without_an_open_sqlite_transaction(ingestion_db) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    result = _result(key, interval, (_empty_chunk(key, interval),))
    session = factory()
    provider = _FakeProvider(result, before_return=lambda: pytest.fail("placeholder"))
    provider.before_return = lambda: (
        None if not session.in_transaction() else pytest.fail("HTTP ran inside SQLite transaction")
    )
    service, _store = _service(session, provider)
    outcome = service.ingest(_historical_request(interval))
    assert outcome.global_result is SyncAttemptResult.EMPTY
    session.close()


@pytest.mark.parametrize("mutation", ["gap", "outside", "aggregate", "registry"])
def test_inconsistent_provider_evidence_is_rejected_before_any_write(
    ingestion_db,
    mutation: str,
) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    requested = ProviderInterval(date(2026, 10, 1), date(2026, 10, 3))
    if mutation == "gap":
        chunks = (
            _success_chunk(key, ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))),
            _success_chunk(key, ProviderInterval(date(2026, 10, 3), date(2026, 10, 3))),
        )
        provider_result = _result(key, requested, chunks)
    else:
        observation = _observation(
            key,
            "10.50",
            date(2026, 10, 4) if mutation == "outside" else date(2026, 10, 1),
        )
        chunk = _success_chunk(
            key,
            ProviderInterval(date(2026, 10, 1), date(2026, 10, 3)),
            (observation,),
        )
        provider_result = _result(key, requested, (chunk,))
        if mutation == "aggregate":
            object.__setattr__(provider_result, "observations", ())
        elif mutation == "registry":
            object.__setattr__(provider_result, "registry_key", RegistryKey.BCB_SGS_CDI)
    session = factory()
    service, _store = _service(session, _FakeProvider(provider_result))
    with pytest.raises(GovernedIngestionError) as failure:
        service.ingest(_historical_request(requested))
    assert failure.value.stage is GovernedIngestionStage.PROVIDER
    assert failure.value.code == GovernedIngestionErrorCode.PROVIDER_RESULT_INVALID.value
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 0
    assert session.scalar(select(func.count()).select_from(ExternalSeriesSyncStateModel)) == 0
    session.close()


def test_provider_exception_is_separate_and_does_not_finalize(ingestion_db) -> None:
    _engine, factory = ingestion_db
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    provider = _FakeProvider(
        ExternalObservationProviderError(
            ProviderErrorCode.TIMEOUT,
            "safe timeout",
            transient=True,
            attempts=3,
        )
    )
    session = factory()
    service, _store = _service(session, provider)
    with pytest.raises(GovernedIngestionError) as failure:
        service.ingest(_historical_request(interval))
    assert failure.value.stage is GovernedIngestionStage.PROVIDER
    assert failure.value.code == ProviderErrorCode.TIMEOUT.value
    assert session.scalar(select(func.count()).select_from(ExternalSeriesSyncStateModel)) == 0
    session.close()


def test_regressive_finalization_is_identified_after_event_commit(ingestion_db) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    result = _result(key, interval, (_success_chunk(key, interval),))
    session = factory()
    service, _store = _service(
        session,
        _FakeProvider(result),
        operational_clock=lambda: RETRIEVED,
    )
    with pytest.raises(GovernedIngestionError) as failure:
        service.ingest(_historical_request(interval))
    assert failure.value.stage is GovernedIngestionStage.FINALIZATION
    assert failure.value.code == ExternalContextPersistenceErrorCode.STALE_ACQUISITION_FINALIZATION.value
    assert failure.value.chunk_results[0].persistence_completed is True
    state = ExternalSeriesSyncStateRepository(session).get(key)
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 1
    assert state is not None
    assert state.last_attempt_at is None
    assert state.coverage_start is None
    assert state.observations_received == 1
    session.close()


def test_finalization_failure_preserves_events_without_false_global_success(
    ingestion_db,
    monkeypatch,
) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    result = _result(key, interval, (_success_chunk(key, interval),))
    session = factory()
    service, store = _service(session, _FakeProvider(result))

    def fail_finalization(_request):
        raise RuntimeError("injected finalization failure")

    monkeypatch.setattr(store, "finalize_acquisition", fail_finalization)
    with pytest.raises(GovernedIngestionError) as failure:
        service.ingest(_historical_request(interval))
    assert failure.value.stage is GovernedIngestionStage.FINALIZATION
    assert failure.value.code == GovernedIngestionErrorCode.FINALIZATION_FAILED.value
    assert failure.value.chunk_results[0].persistence_completed is True
    state = ExternalSeriesSyncStateRepository(session).get(key)
    assert state is not None
    assert state.last_attempt_at is None
    assert state.last_success_at is None
    assert state.coverage_start is None
    assert state.observations_received == 1
    assert session.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 1
    session.close()


def test_finalized_result_is_visible_to_an_independent_reader(ingestion_db) -> None:
    _engine, factory = ingestion_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    result = _result(key, interval, (_success_chunk(key, interval),))
    writer = factory()
    service, _store = _service(writer, _FakeProvider(result))
    returned = service.ingest(_historical_request(interval))
    reader = factory()
    persisted = ExternalSeriesSyncStateRepository(reader).get(key)
    assert returned.global_result is SyncAttemptResult.SUCCESS
    assert persisted == returned.sync_state
    reader.close()
    writer.close()
