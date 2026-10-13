from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

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
)
from backend.application.services.governed_external_ingestion import (
    AcquisitionIntent,
    GovernedExternalIngestionService,
    GovernedIngestionError,
    GovernedIngestionErrorCode,
    GovernedIngestionStage,
    ordinary_revision_interval,
)
from backend.application.services.manual_external_refresh import (
    ManualExternalRefreshService,
    ManualRefreshEligibilityReason,
    ManualRefreshRequest,
    ManualRefreshStatus,
    evaluate_manual_refresh_eligibility,
)
from backend.core.config import settings
from backend.domains.external_context import (
    EXTERNAL_SERIES_REGISTRY_VERSION,
    ExternalSeriesSyncState,
    Frequency,
    RegistryKey,
    SyncAttemptResult,
    UTCCodecError,
    normalize_external_observation,
    resolve_series_by_key,
)
from backend.infrastructure.persistence.models.external_context import (
    ExternalObservationVersionModel,
    ExternalSeriesSyncStateModel,
)
from backend.infrastructure.persistence.repositories.external_context import (
    ExternalSeriesSyncStateRepository,
)


R3D_REVISION = "4f9c2d7e1a6b"
PRE_R3D_REVISION = "2d6b4f8a9c1e"
RETRIEVED = datetime(2026, 10, 12, 12, tzinfo=timezone.utc)
OPERATIONAL = RETRIEVED + timedelta(hours=1)


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
def manual_db(tmp_path, monkeypatch):
    database_path = tmp_path / "manual_refresh.db"
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
        self._lock = threading.Lock()

    def __call__(self) -> datetime:
        with self._lock:
            current = self.value
            self.value += timedelta(microseconds=1)
            return current


class _FakeProvider(ExternalObservationProvider):
    def __init__(
        self,
        *outcomes: ProviderAcquisitionResult | Exception,
        before_return=None,
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


class _BarrierProvider(ExternalObservationProvider):
    def __init__(self, result: ProviderAcquisitionResult) -> None:
        self._result = result
        self._barrier = threading.Barrier(2)
        self._lock = threading.Lock()
        self.calls: list[str | None] = []

    def acquire(
        self,
        registry_key: RegistryKey | str,
        start: date,
        end: date,
        *,
        correlation_id: str | None = None,
    ) -> ProviderAcquisitionResult:
        assert registry_key is self._result.registry_key
        assert (start, end) == (
            self._result.requested_interval.start,
            self._result.requested_interval.end,
        )
        with self._lock:
            self.calls.append(correlation_id)
        self._barrier.wait(timeout=5)
        return self._result


def _observation(registry_key: RegistryKey, anchor: date):
    definition = resolve_series_by_key(registry_key)
    return normalize_external_observation(
        {
            "provider": definition.provider.value,
            "series_id": definition.series_id,
            "reference_period_start": anchor.isoformat(),
            "reference_period_end": anchor.isoformat(),
            "semantic_class": definition.semantic_class.value,
            "frequency": definition.frequency.value,
            "value_text": "10.50",
            "value_scale": definition.normalization_scale,
            "unit": definition.unit.value,
            "currency": definition.currency,
            "scope": definition.scope.value,
        },
        retrieved_at=RETRIEVED,
    )


def _complete_chunk(
    registry_key: RegistryKey,
    interval: ProviderInterval,
    *,
    empty: bool = False,
) -> ProviderChunkResult:
    observations = () if empty else (_observation(registry_key, interval.start),)
    return ProviderChunkResult(
        registry_key=registry_key,
        interval=interval,
        status=ProviderChunkStatus.EMPTY if empty else ProviderChunkStatus.SUCCESS,
        response_received=True,
        payload_validated=True,
        normalization_completed=True,
        observations=observations,
        empty_response=empty,
        http_attempts=1,
        retrieved_at=RETRIEVED,
        http_status=200,
    )


def _failed_chunk(
    registry_key: RegistryKey,
    interval: ProviderInterval,
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
        error_code=ProviderErrorCode.TIMEOUT,
        terminal_failure=True,
    )


def _provider_result(
    registry_key: RegistryKey,
    requested: ProviderInterval,
    chunks: tuple[ProviderChunkResult, ...],
) -> ProviderAcquisitionResult:
    observations = tuple(
        observation for chunk in chunks for observation in chunk.observations
    )
    completed = sum(chunk.is_complete for chunk in chunks)
    if completed == len(chunks):
        status = (
            ProviderAcquisitionStatus.SUCCESS
            if observations
            else ProviderAcquisitionStatus.EMPTY
        )
    elif completed:
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


def _state(
    registry_key: RegistryKey,
    *,
    last_attempt_at: datetime | None = RETRIEVED,
    last_success_at: datetime | None = RETRIEVED,
    next_eligible_at: datetime | None = None,
    result: SyncAttemptResult | None = SyncAttemptResult.SUCCESS,
    registry_version: int = EXTERNAL_SERIES_REGISTRY_VERSION,
) -> ExternalSeriesSyncState:
    definition = resolve_series_by_key(registry_key)
    return ExternalSeriesSyncState(
        registry_key=registry_key.value,
        provider=definition.provider.value,
        series_id=definition.series_id,
        registry_contract_version=registry_version,
        last_attempt_at=last_attempt_at,
        last_success_at=last_success_at,
        next_refresh_eligible_at=next_eligible_at,
        last_attempt_result=result,
    )


def _service(
    session,
    provider: ExternalObservationProvider,
    *,
    state_reader=None,
    evaluated_at: datetime = RETRIEVED,
    operational_at: datetime = OPERATIONAL,
) -> tuple[ManualExternalRefreshService, ExternalObservationStoreService]:
    store = ExternalObservationStoreService(
        session,
        utc_clock=_IncrementingClock(RETRIEVED + timedelta(seconds=1)),
    )
    ingestion = GovernedExternalIngestionService(
        provider=provider,
        store=store,
        utc_clock=lambda: operational_at,
    )
    if state_reader is None:
        def state_reader(registry_key):
            state = store.get_sync_state(registry_key)
            session.rollback()
            return state
    return (
        ManualExternalRefreshService(
            ingestion=ingestion,
            sync_state_reader=state_reader,
            utc_clock=lambda: evaluated_at,
        ),
        store,
    )


def _historical_request(
    interval: ProviderInterval,
    *,
    acquisition_id: str = "manual-historical",
) -> ManualRefreshRequest:
    return ManualRefreshRequest(
        acquisition_id=acquisition_id,
        registry_key=RegistryKey.BCB_SGS_SELIC_TARGET,
        intent=AcquisitionIntent.HISTORICAL_RECONCILIATION,
        historical_interval=interval,
    )


@pytest.mark.parametrize(
    ("registry_key", "expected_interval"),
    [
        (RegistryKey.BCB_SGS_SELIC_TARGET, timedelta(hours=6)),
        (RegistryKey.BCB_SGS_SELIC_EFFECTIVE, timedelta(hours=6)),
        (RegistryKey.BCB_SGS_CDI, timedelta(hours=6)),
        (RegistryKey.BCB_SGS_IPCA_MONTHLY, timedelta(hours=24)),
        (RegistryKey.BCB_SGS_USD_SELL, timedelta(hours=6)),
    ],
)
def test_all_registry_series_are_initially_eligible_without_manufactured_state(
    registry_key: RegistryKey,
    expected_interval: timedelta,
) -> None:
    decision = evaluate_manual_refresh_eligibility(
        definition=resolve_series_by_key(registry_key),
        state=None,
        at=RETRIEVED,
        intent=AcquisitionIntent.ORDINARY_REFRESH,
    )
    assert decision.eligible is True
    assert decision.reason is ManualRefreshEligibilityReason.INITIAL_REFRESH
    assert decision.refresh_interval == expected_interval
    assert decision.last_attempt_at is None
    assert decision.last_success_at is None
    assert decision.next_eligible_at is None


@pytest.mark.parametrize(
    ("offset", "eligible", "reason"),
    [
        (
            timedelta(hours=6) - timedelta(microseconds=1),
            False,
            ManualRefreshEligibilityReason.COOLDOWN_ACTIVE,
        ),
        (timedelta(hours=6), True, ManualRefreshEligibilityReason.COOLDOWN_ELAPSED),
        (
            timedelta(hours=6, microseconds=1),
            True,
            ManualRefreshEligibilityReason.COOLDOWN_ELAPSED,
        ),
    ],
)
def test_daily_cooldown_boundary(
    offset: timedelta,
    eligible: bool,
    reason: ManualRefreshEligibilityReason,
) -> None:
    key = RegistryKey.BCB_SGS_CDI
    decision = evaluate_manual_refresh_eligibility(
        definition=resolve_series_by_key(key),
        state=_state(key, next_eligible_at=RETRIEVED + timedelta(hours=6)),
        at=RETRIEVED + offset,
        intent=AcquisitionIntent.ORDINARY_REFRESH,
    )
    assert decision.eligible is eligible
    assert decision.reason is reason
    assert decision.next_eligible_at == RETRIEVED + timedelta(hours=6)


@pytest.mark.parametrize(
    ("offset", "eligible"),
    [
        (timedelta(hours=24) - timedelta(microseconds=1), False),
        (timedelta(hours=24), True),
        (timedelta(hours=24, microseconds=1), True),
    ],
)
def test_monthly_cooldown_boundary(offset: timedelta, eligible: bool) -> None:
    key = RegistryKey.BCB_SGS_IPCA_MONTHLY
    decision = evaluate_manual_refresh_eligibility(
        definition=resolve_series_by_key(key),
        state=_state(key, next_eligible_at=RETRIEVED + timedelta(hours=24)),
        at=RETRIEVED + offset,
        intent=AcquisitionIntent.ORDINARY_REFRESH,
    )
    assert decision.eligible is eligible
    assert decision.refresh_interval == timedelta(hours=24)


@pytest.mark.parametrize(
    ("result", "reason"),
    [
        (SyncAttemptResult.PARTIAL, ManualRefreshEligibilityReason.RETRY_AFTER_PARTIAL),
        (SyncAttemptResult.FAILED, ManualRefreshEligibilityReason.RETRY_AFTER_FAILED),
    ],
)
def test_partial_and_failed_without_success_are_retryable_without_invented_cooldown(
    result: SyncAttemptResult,
    reason: ManualRefreshEligibilityReason,
) -> None:
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    decision = evaluate_manual_refresh_eligibility(
        definition=resolve_series_by_key(key),
        state=_state(
            key,
            last_success_at=None,
            next_eligible_at=None,
            result=result,
        ),
        at=RETRIEVED + timedelta(minutes=1),
        intent=AcquisitionIntent.HISTORICAL_RECONCILIATION,
    )
    assert decision.eligible is True
    assert decision.reason is reason


def test_last_attempt_without_success_or_result_is_eligible_without_false_success() -> None:
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    decision = evaluate_manual_refresh_eligibility(
        definition=resolve_series_by_key(key),
        state=_state(
            key,
            last_success_at=None,
            next_eligible_at=None,
            result=None,
        ),
        at=RETRIEVED + timedelta(minutes=1),
        intent=AcquisitionIntent.ORDINARY_REFRESH,
    )
    assert decision.eligible is True
    assert decision.reason is ManualRefreshEligibilityReason.NO_SUCCESS_EVIDENCE


def test_empty_is_a_finalized_success_and_obeys_cooldown() -> None:
    key = RegistryKey.BCB_SGS_IPCA_MONTHLY
    decision = evaluate_manual_refresh_eligibility(
        definition=resolve_series_by_key(key),
        state=_state(
            key,
            result=SyncAttemptResult.EMPTY,
            next_eligible_at=RETRIEVED + timedelta(hours=24),
        ),
        at=RETRIEVED + timedelta(hours=12),
        intent=AcquisitionIntent.ORDINARY_REFRESH,
    )
    assert decision.eligible is False
    assert decision.reason is ManualRefreshEligibilityReason.COOLDOWN_ACTIVE


def test_regressive_clock_and_registry_mismatch_fail_closed() -> None:
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    regressive = evaluate_manual_refresh_eligibility(
        definition=resolve_series_by_key(key),
        state=_state(key, next_eligible_at=None),
        at=RETRIEVED - timedelta(microseconds=1),
        intent=AcquisitionIntent.ORDINARY_REFRESH,
    )
    mismatch = evaluate_manual_refresh_eligibility(
        definition=resolve_series_by_key(key),
        state=_state(key, registry_version=2, next_eligible_at=None),
        at=RETRIEVED + timedelta(days=1),
        intent=AcquisitionIntent.ORDINARY_REFRESH,
    )
    assert regressive.eligible is False
    assert regressive.reason is ManualRefreshEligibilityReason.CLOCK_REGRESSION
    assert mismatch.eligible is False
    assert mismatch.reason is ManualRefreshEligibilityReason.REGISTRY_VERSION_MISMATCH


@pytest.mark.parametrize(
    "at",
    [
        datetime(2026, 10, 12, 12),
        datetime(2026, 10, 12, 12, tzinfo=timezone(timedelta(hours=-3))),
    ],
)
def test_eligibility_requires_canonical_utc_clock(at: datetime) -> None:
    with pytest.raises(UTCCodecError):
        evaluate_manual_refresh_eligibility(
            definition=resolve_series_by_key(RegistryKey.BCB_SGS_CDI),
            state=None,
            at=at,
            intent=AcquisitionIntent.ORDINARY_REFRESH,
        )


def test_manual_request_reuses_r3e3_intent_and_interval_validation() -> None:
    with pytest.raises(TypeError):
        ManualRefreshRequest(
            acquisition_id="invalid-key",
            registry_key="432",  # type: ignore[arg-type]
            intent=AcquisitionIntent.ORDINARY_REFRESH,
            reference_date=date(2026, 10, 12),
        )
    with pytest.raises(TypeError):
        ManualRefreshRequest(
            acquisition_id="missing-intent",
            registry_key=RegistryKey.BCB_SGS_CDI,
            intent=None,  # type: ignore[arg-type]
            reference_date=date(2026, 10, 12),
        )
    with pytest.raises(ValueError):
        ManualRefreshRequest(
            acquisition_id="ordinary-with-range",
            registry_key=RegistryKey.BCB_SGS_CDI,
            intent=AcquisitionIntent.ORDINARY_REFRESH,
            reference_date=date(2026, 10, 12),
            historical_interval=ProviderInterval(date(2026, 1, 1), date(2026, 1, 2)),
        )
    with pytest.raises(ValueError):
        ManualRefreshRequest(
            acquisition_id="historical-without-range",
            registry_key=RegistryKey.BCB_SGS_CDI,
            intent=AcquisitionIntent.HISTORICAL_RECONCILIATION,
        )
    with pytest.raises(ValueError):
        ManualRefreshRequest(
            acquisition_id="before-floor",
            registry_key=RegistryKey.BCB_SGS_USD_SELL,
            intent=AcquisitionIntent.HISTORICAL_RECONCILIATION,
            historical_interval=ProviderInterval(date(1994, 6, 1), date(1994, 6, 30)),
        )


@pytest.mark.parametrize(
    ("chunks_factory", "expected_status"),
    [
        (
            lambda key, first, second: (
                _complete_chunk(key, ProviderInterval(first, second)),
            ),
            ManualRefreshStatus.SUCCESS,
        ),
        (
            lambda key, first, second: (
                _complete_chunk(key, ProviderInterval(first, second), empty=True),
            ),
            ManualRefreshStatus.EMPTY,
        ),
        (
            lambda key, first, second: (
                _complete_chunk(key, ProviderInterval(first, first)),
                _failed_chunk(key, ProviderInterval(second, second)),
            ),
            ManualRefreshStatus.PARTIAL,
        ),
        (
            lambda key, first, second: (
                _failed_chunk(key, ProviderInterval(first, first)),
                _failed_chunk(key, ProviderInterval(second, second)),
            ),
            ManualRefreshStatus.FAILED,
        ),
    ],
)
def test_manual_service_preserves_all_finalized_r3e3_results(
    manual_db,
    chunks_factory,
    expected_status: ManualRefreshStatus,
) -> None:
    _engine, factory = manual_db
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    requested = ProviderInterval(date(2026, 10, 1), date(2026, 10, 2))
    chunks = chunks_factory(key, requested.start, requested.end)
    provider = _FakeProvider(_provider_result(key, requested, chunks))
    session = factory()
    service, _store = _service(session, provider)

    result = service.refresh(_historical_request(requested))

    assert result.status is expected_status
    assert result.global_result is SyncAttemptResult(expected_status.value)
    assert result.ingestion is not None
    assert result.ingestion.requested_interval == requested
    assert len(provider.calls) == 1
    assert provider.calls[0][-1] == "manual-historical"
    assert result.sync_state is not None
    assert result.sync_state.last_attempt_result.value == expected_status.value
    session.close()


def test_sequential_success_then_cooldown_denial_has_no_provider_call_or_write(
    manual_db,
) -> None:
    engine, factory = manual_db
    key = RegistryKey.BCB_SGS_CDI
    reference_date = date(2026, 10, 12)
    requested = ordinary_revision_interval(key, reference_date)
    provider = _FakeProvider(
        _provider_result(key, requested, (_complete_chunk(key, requested, empty=True),))
    )
    writer = factory()
    first_service, _store = _service(
        writer,
        provider,
        evaluated_at=RETRIEVED,
        operational_at=OPERATIONAL,
    )
    first = first_service.refresh(
        ManualRefreshRequest(
            acquisition_id="ordinary-first",
            registry_key=key,
            intent=AcquisitionIntent.ORDINARY_REFRESH,
            reference_date=reference_date,
        )
    )
    assert first.status is ManualRefreshStatus.EMPTY
    writer.close()

    statements: list[str] = []

    @event.listens_for(engine, "before_cursor_execute")
    def _capture(_connection, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement.strip().upper())

    reader = factory()
    second_service, second_store = _service(
        reader,
        provider,
        evaluated_at=OPERATIONAL + timedelta(hours=1),
        operational_at=OPERATIONAL + timedelta(hours=1),
    )
    before = second_store.get_sync_state(key)
    statements.clear()
    second = second_service.refresh(
        ManualRefreshRequest(
            acquisition_id="ordinary-second",
            registry_key=key,
            intent=AcquisitionIntent.ORDINARY_REFRESH,
            reference_date=reference_date,
        )
    )
    after = second_store.get_sync_state(key)

    assert second.status is ManualRefreshStatus.NOT_ELIGIBLE
    assert second.global_result is None
    assert second.eligibility.reason is ManualRefreshEligibilityReason.COOLDOWN_ACTIVE
    assert len(provider.calls) == 1
    assert before == after
    assert statements
    assert all(statement.startswith("SELECT") for statement in statements)
    assert reader.scalar(select(func.count()).select_from(ExternalObservationVersionModel)) == 0
    reader.close()


def test_r3e3_typed_provider_error_is_preserved_without_sync_state(manual_db) -> None:
    _engine, factory = manual_db
    provider = _FakeProvider(
        ExternalObservationProviderError(
            ProviderErrorCode.TIMEOUT,
            "safe timeout",
            transient=True,
            attempts=3,
        )
    )
    session = factory()
    service, store = _service(session, provider)
    request = ManualRefreshRequest(
        acquisition_id="provider-timeout",
        registry_key=RegistryKey.BCB_SGS_CDI,
        intent=AcquisitionIntent.ORDINARY_REFRESH,
        reference_date=date(2026, 10, 12),
    )

    with pytest.raises(GovernedIngestionError) as failure:
        service.refresh(request)

    assert failure.value.stage is GovernedIngestionStage.PROVIDER
    assert failure.value.code == ProviderErrorCode.TIMEOUT.value
    assert store.get_sync_state(RegistryKey.BCB_SGS_CDI) is None
    assert session.scalar(select(func.count()).select_from(ExternalSeriesSyncStateModel)) == 0
    session.close()


def test_sync_state_read_transaction_is_released_before_provider_io(manual_db) -> None:
    _engine, factory = manual_db
    key = RegistryKey.BCB_SGS_CDI
    reference_date = date(2026, 10, 12)
    interval = ordinary_revision_interval(key, reference_date)
    session = factory()
    provider = _FakeProvider(
        _provider_result(key, interval, (_complete_chunk(key, interval, empty=True),)),
        before_return=lambda: (
            pytest.fail("Provider I/O ran with an open SQLite transaction")
            if session.in_transaction()
            else None
        ),
    )
    service, _store = _service(session, provider)

    result = service.refresh(
        ManualRefreshRequest(
            acquisition_id="read-boundary",
            registry_key=key,
            intent=AcquisitionIntent.ORDINARY_REFRESH,
            reference_date=reference_date,
        )
    )

    assert result.status is ManualRefreshStatus.EMPTY
    session.close()


def test_finalization_error_is_preserved_without_false_success(
    manual_db,
    monkeypatch,
) -> None:
    _engine, factory = manual_db
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    provider = _FakeProvider(
        _provider_result(key, interval, (_complete_chunk(key, interval),))
    )
    session = factory()
    service, store = _service(session, provider)

    monkeypatch.setattr(
        store,
        "finalize_acquisition",
        lambda _request: (_ for _ in ()).throw(RuntimeError("injected finalization failure")),
    )
    with pytest.raises(GovernedIngestionError) as failure:
        service.refresh(_historical_request(interval))

    assert failure.value.stage is GovernedIngestionStage.FINALIZATION
    assert failure.value.code == GovernedIngestionErrorCode.FINALIZATION_FAILED.value
    state = store.get_sync_state(key)
    assert state is not None
    assert state.last_success_at is None
    assert state.last_attempt_at is None
    assert state.coverage_start is None
    assert state.observations_received == 1
    session.close()


def test_manual_service_delegates_exactly_one_finalization(
    manual_db,
    monkeypatch,
) -> None:
    _engine, factory = manual_db
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    provider = _FakeProvider(
        _provider_result(key, interval, (_complete_chunk(key, interval, empty=True),))
    )
    session = factory()
    service, store = _service(session, provider)
    original = store.finalize_acquisition
    calls = 0

    def capture(request):
        nonlocal calls
        calls += 1
        return original(request)

    monkeypatch.setattr(store, "finalize_acquisition", capture)
    outcome = service.refresh(_historical_request(interval))

    assert outcome.status is ManualRefreshStatus.EMPTY
    assert calls == 1
    session.close()


def test_concurrent_eligible_requests_may_duplicate_provider_io_without_state_corruption(
    manual_db,
) -> None:
    _engine, factory = manual_db
    key = RegistryKey.BCB_SGS_CDI
    reference_date = date(2026, 10, 12)
    interval = ordinary_revision_interval(key, reference_date)
    provider = _BarrierProvider(
        _provider_result(key, interval, (_complete_chunk(key, interval, empty=True),))
    )

    def run(acquisition_id: str):
        session = factory()
        try:
            service, _store = _service(
                session,
                provider,
                evaluated_at=RETRIEVED,
                operational_at=OPERATIONAL,
            )
            return service.refresh(
                ManualRefreshRequest(
                    acquisition_id=acquisition_id,
                    registry_key=key,
                    intent=AcquisitionIntent.ORDINARY_REFRESH,
                    reference_date=reference_date,
                )
            )
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = tuple(executor.map(run, ("concurrent-a", "concurrent-b")))

    assert [outcome.status for outcome in outcomes] == [
        ManualRefreshStatus.EMPTY,
        ManualRefreshStatus.EMPTY,
    ]
    assert sorted(provider.calls) == ["concurrent-a", "concurrent-b"]
    reader = factory()
    state = ExternalSeriesSyncStateRepository(reader).get(key)
    assert state is not None
    assert state.last_attempt_result is SyncAttemptResult.EMPTY
    assert state.last_success_at == OPERATIONAL
    assert state.next_refresh_eligible_at == OPERATIONAL + timedelta(hours=6)
    assert state.coverage_start == interval.start
    assert state.coverage_end == interval.end
    assert state.observations_received == 0
    assert reader.scalar(select(func.count()).select_from(ExternalSeriesSyncStateModel)) == 1
    reader.close()


def test_safe_telemetry_contains_correlation_registry_intent_and_result(
    manual_db,
    caplog,
) -> None:
    _engine, factory = manual_db
    interval = ProviderInterval(date(2026, 10, 1), date(2026, 10, 1))
    key = RegistryKey.BCB_SGS_SELIC_TARGET
    provider = _FakeProvider(
        _provider_result(key, interval, (_complete_chunk(key, interval, empty=True),))
    )
    session = factory()
    service, _store = _service(session, provider)
    telemetry_logger = logging.getLogger(
        "backend.application.services.manual_external_refresh"
    )
    telemetry_logger.disabled = False

    with caplog.at_level(
        logging.INFO,
        logger=telemetry_logger.name,
    ):
        service.refresh(_historical_request(interval, acquisition_id="safe-correlation"))

    records = [
        record
        for record in caplog.records
        if record.name == "backend.application.services.manual_external_refresh"
    ]
    assert [record.message for record in records] == [
        "external_context.manual_refresh.evaluated",
        "external_context.manual_refresh.completed",
    ]
    assert all(record.correlation_id == "safe-correlation" for record in records)
    assert all(record.registry_key == key.value for record in records)
    assert all(
        record.refresh_intent == AcquisitionIntent.HISTORICAL_RECONCILIATION.value
        for record in records
    )
    assert records[-1].global_result == ManualRefreshStatus.EMPTY.value
    session.close()
