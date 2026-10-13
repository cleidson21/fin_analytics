from __future__ import annotations

import inspect
from datetime import date, datetime, timezone

import httpx
import pytest

from backend.application.ports.external_observation_provider import (
    ExternalObservationProviderError,
    ProviderAcquisitionStatus,
    ProviderChunkStatus,
    ProviderErrorCode,
    ProviderInterval,
    daily_interval_within_limit,
    plan_provider_chunks,
)
from backend.domains.external_context import (
    EXTERNAL_SERIES_REGISTRY_VERSION,
    Frequency,
    RegistryKey,
    SeriesUse,
)
from backend.infrastructure.external import bcb_sgs_adapter as adapter_module
from backend.infrastructure.external import bcb_sgs_client as client_module
from backend.infrastructure.external.bcb_sgs_adapter import BCBSGSAdapter
from backend.infrastructure.external.bcb_sgs_client import BCBSGSClient


UTC_NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)


def _json_response(records: list[dict[str, object]]) -> httpx.Response:
    return httpx.Response(
        200,
        headers={"content-type": "application/json"},
        json=records,
    )


def _record_for_request(request: httpx.Request, value: str = "0.052788") -> dict[str, str]:
    return {"data": request.url.params["dataInicial"], "valor": value}


def _stack(
    handler,
    *,
    max_attempts: int = 1,
    max_records: int = 5_000,
    max_chunks: int = 100,
    utc_clock=lambda: UTC_NOW,
) -> tuple[BCBSGSAdapter, httpx.Client]:
    http_client = httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
    )
    client = BCBSGSClient(
        http_client=http_client,
        max_attempts=max_attempts,
        max_records=max_records,
        utc_clock=utc_clock,
        sleeper=lambda _: None,
        jitter=lambda _: 0.0,
    )
    return BCBSGSAdapter(client, max_chunks=max_chunks), http_client


@pytest.mark.parametrize(
    ("start", "end", "expected_count"),
    [
        (date(2026, 1, 1), date(2026, 1, 1), 1),
        (date(2026, 1, 1), date(2026, 3, 31), 1),
        (date(2000, 1, 1), date(2009, 12, 31), 1),
        (date(2000, 1, 1), date(2010, 1, 1), 2),
        (date(2000, 1, 1), date(2020, 1, 1), 3),
    ],
)
def test_daily_chunk_planning_is_deterministic_and_exact(
    start: date,
    end: date,
    expected_count: int,
) -> None:
    first = plan_provider_chunks(RegistryKey.BCB_SGS_SELIC_EFFECTIVE, start, end)
    second = plan_provider_chunks(RegistryKey.BCB_SGS_SELIC_EFFECTIVE, start, end)

    assert first == second
    assert len(first) == expected_count
    assert first[0].start == start
    assert first[-1].end == end
    assert all(daily_interval_within_limit(chunk) for chunk in first)
    assert all(
        current.end.toordinal() + 1 == following.start.toordinal()
        for current, following in zip(first, first[1:])
    )


def test_leap_day_partition_uses_conservative_civil_anniversary_without_gaps() -> None:
    chunks = plan_provider_chunks(
        RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
        date(2016, 2, 29),
        date(2026, 3, 1),
    )
    assert chunks == (
        ProviderInterval(date(2016, 2, 29), date(2026, 2, 27)),
        ProviderInterval(date(2026, 2, 28), date(2026, 3, 1)),
    )


def test_monthly_series_is_not_given_the_daily_ten_year_rule() -> None:
    chunks = plan_provider_chunks(
        RegistryKey.BCB_SGS_IPCA_MONTHLY,
        date(1980, 1, 1),
        date(2026, 10, 12),
    )
    assert chunks == (ProviderInterval(date(1980, 1, 1), date(2026, 10, 12)),)


def test_sgs_one_floor_is_enforced_before_any_http() -> None:
    with pytest.raises(ExternalObservationProviderError) as failure:
        plan_provider_chunks(
            RegistryKey.BCB_SGS_USD_SELL,
            date(1994, 6, 30),
            date(1994, 7, 1),
        )
    assert failure.value.code is ProviderErrorCode.INTERVAL_BEFORE_FLOOR


def test_datetime_is_not_accidentally_accepted_as_civil_date() -> None:
    with pytest.raises(ExternalObservationProviderError) as failure:
        plan_provider_chunks(
            RegistryKey.BCB_SGS_CDI,
            datetime(2026, 1, 1),  # type: ignore[arg-type]
            date(2026, 1, 2),
        )
    assert failure.value.code is ProviderErrorCode.INVALID_INTERVAL


@pytest.mark.parametrize(
    ("outcomes", "expected_status", "expected_observations"),
    [
        (("success", "success", "success"), ProviderAcquisitionStatus.SUCCESS, 3),
        (("empty", "empty", "empty"), ProviderAcquisitionStatus.EMPTY, 0),
        (("success", "empty", "success"), ProviderAcquisitionStatus.SUCCESS, 2),
        (("success", 503, "success"), ProviderAcquisitionStatus.PARTIAL, 2),
        (("empty", 503, "empty"), ProviderAcquisitionStatus.PARTIAL, 0),
        ((503, 503, 503), ProviderAcquisitionStatus.FAILED, 0),
    ],
)
def test_multichunk_consolidation_preserves_external_completion_semantics(
    outcomes: tuple[object, ...],
    expected_status: ProviderAcquisitionStatus,
    expected_observations: int,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        outcome = outcomes[len(requests)]
        requests.append(request)
        if outcome == "success":
            return _json_response([_record_for_request(request)])
        if outcome == "empty":
            return _json_response([])
        return httpx.Response(int(outcome))

    adapter, http_client = _stack(handler)
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
            date(2000, 1, 1),
            date(2020, 1, 1),
        )
    finally:
        http_client.close()

    assert result.status is expected_status
    assert len(result.observations) == expected_observations
    assert len(result.planned_chunks) == 3
    assert len(requests) == 3
    assert all(
        request.url.params["dataInicial"]
        == chunk.start.strftime("%d/%m/%Y")
        and request.url.params["dataFinal"]
        == chunk.end.strftime("%d/%m/%Y")
        for request, chunk in zip(requests, result.planned_chunks)
    )
    assert all(not hasattr(chunk, "persistence_completed") for chunk in result.chunk_results)


def test_success_failed_success_is_partial_without_fabricated_continuity() -> None:
    outcomes: list[object] = ["success", 503, "success"]

    def handler(request: httpx.Request) -> httpx.Response:
        outcome = outcomes.pop(0)
        if outcome == "success":
            return _json_response([_record_for_request(request)])
        return httpx.Response(int(outcome))

    adapter, http_client = _stack(handler)
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
            date(2000, 1, 1),
            date(2020, 1, 1),
        )
    finally:
        http_client.close()

    assert result.status is ProviderAcquisitionStatus.PARTIAL
    assert [chunk.status for chunk in result.chunk_results] == [
        ProviderChunkStatus.SUCCESS,
        ProviderChunkStatus.FAILED,
        ProviderChunkStatus.SUCCESS,
    ]
    assert result.queried_intervals == (
        result.planned_chunks[0],
        result.planned_chunks[2],
    )
    assert result.failed_or_incomplete_chunks[0].interval == result.planned_chunks[1]
    assert len(result.observations) == 2


@pytest.mark.parametrize(
    ("middle_response", "expected_code"),
    [
        (
            lambda _: httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=b"not-json",
            ),
            ProviderErrorCode.INVALID_JSON,
        ),
        (
            lambda request: _json_response(
                [{"data": request.url.params["dataInicial"], "valor": "1e2"}]
            ),
            ProviderErrorCode.INVALID_VALUE,
        ),
    ],
)
def test_invalid_middle_chunk_is_atomic_and_does_not_discard_other_chunks(
    middle_response,
    expected_code: ProviderErrorCode,
) -> None:
    call = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call
        call += 1
        if call == 2:
            return middle_response(request)
        return _json_response([_record_for_request(request)])

    adapter, http_client = _stack(handler)
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
            date(2000, 1, 1),
            date(2020, 1, 1),
        )
    finally:
        http_client.close()

    assert result.status is ProviderAcquisitionStatus.PARTIAL
    assert len(result.observations) == 2
    assert result.chunk_results[1].observations == ()
    assert result.chunk_results[1].error_code is expected_code


def test_retry_recovery_keeps_the_whole_acquisition_successful() -> None:
    attempt = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt
        attempt += 1
        if attempt == 2:
            return httpx.Response(429, headers={"retry-after": "0"})
        return _json_response([_record_for_request(request)])

    adapter, http_client = _stack(handler, max_attempts=2)
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
            date(2000, 1, 1),
            date(2020, 1, 1),
        )
    finally:
        http_client.close()
    assert result.status is ProviderAcquisitionStatus.SUCCESS
    assert [chunk.http_attempts for chunk in result.chunk_results] == [1, 2, 1]


@pytest.mark.parametrize(
    ("failure_kind", "expected_code"),
    [
        ("timeout", ProviderErrorCode.TIMEOUT),
        ("rate_limit", ProviderErrorCode.HTTP_TRANSIENT_FAILURE),
    ],
)
def test_exhausted_intermediate_transport_failure_preserves_later_chunk(
    failure_kind: str,
    expected_code: ProviderErrorCode,
) -> None:
    call = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call
        call += 1
        if call in {2, 3}:
            if failure_kind == "timeout":
                raise httpx.ReadTimeout("timeout", request=request)
            return httpx.Response(429, headers={"retry-after": "0"})
        return _json_response([_record_for_request(request)])

    adapter, http_client = _stack(handler, max_attempts=2)
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
            date(2000, 1, 1),
            date(2020, 1, 1),
        )
    finally:
        http_client.close()

    assert result.status is ProviderAcquisitionStatus.PARTIAL
    assert [chunk.status for chunk in result.chunk_results] == [
        ProviderChunkStatus.SUCCESS,
        ProviderChunkStatus.FAILED,
        ProviderChunkStatus.SUCCESS,
    ]
    assert result.chunk_results[1].error_code is expected_code
    assert result.chunk_results[1].http_attempts == 2
    assert len(result.observations) == 2


def test_elapsed_acquisition_budget_marks_remaining_chunks_incomplete() -> None:
    timeline = iter([0.0, 0.0, 0.0, 0.0, 11.0])
    monotonic = timeline.__next__
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _json_response([_record_for_request(request)])

    http_client = httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
    )
    client = BCBSGSClient(
        http_client=http_client,
        max_attempts=1,
        utc_clock=lambda: UTC_NOW,
        monotonic=monotonic,
    )
    adapter = BCBSGSAdapter(
        client,
        acquisition_budget_seconds=10.0,
        monotonic=monotonic,
    )
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
            date(2000, 1, 1),
            date(2020, 1, 1),
        )
    finally:
        http_client.close()

    assert result.status is ProviderAcquisitionStatus.PARTIAL
    assert result.is_complete is False
    assert len(requests) == 1
    assert [chunk.status for chunk in result.chunk_results] == [
        ProviderChunkStatus.SUCCESS,
        ProviderChunkStatus.INCOMPLETE,
        ProviderChunkStatus.INCOMPLETE,
    ]


def test_max_chunk_budget_marks_unexecuted_plan_explicitly() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _json_response([_record_for_request(request)])

    adapter, http_client = _stack(handler, max_chunks=1)
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
            date(2000, 1, 1),
            date(2020, 1, 1),
        )
    finally:
        http_client.close()
    assert result.status is ProviderAcquisitionStatus.PARTIAL
    assert len(requests) == 1
    assert [chunk.status for chunk in result.chunk_results] == [
        ProviderChunkStatus.SUCCESS,
        ProviderChunkStatus.INCOMPLETE,
        ProviderChunkStatus.INCOMPLETE,
    ]
    assert all(
        chunk.error_code is ProviderErrorCode.ACQUISITION_BUDGET_EXHAUSTED
        for chunk in result.chunk_results[1:]
    )


def test_response_order_is_normalized_and_identical_duplicates_are_counted() -> None:
    records = [
        {"data": "03/01/2026", "valor": "0.052788"},
        {"data": "01/01/2026", "valor": "0.052788"},
        {"data": "01/01/2026", "valor": "0.052788"},
        {"data": "02/01/2026", "valor": "0.052788"},
    ]
    adapter, http_client = _stack(lambda _: _json_response(records))
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_CDI,
            date(2026, 1, 1),
            date(2026, 1, 3),
        )
    finally:
        http_client.close()
    assert result.status is ProviderAcquisitionStatus.SUCCESS
    assert [
        observation.content.reference_period.start
        for observation in result.observations
    ] == [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]
    assert result.chunk_results[0].duplicate_records == 1


def test_conflicting_duplicate_rejects_the_complete_chunk() -> None:
    adapter, http_client = _stack(
        lambda _: _json_response(
            [
                {"data": "01/01/2026", "valor": "0.052788"},
                {"data": "01/01/2026", "valor": "0.052789"},
            ]
        )
    )
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_CDI,
            date(2026, 1, 1),
            date(2026, 1, 1),
        )
    finally:
        http_client.close()
    assert result.status is ProviderAcquisitionStatus.FAILED
    assert result.observations == ()
    assert result.chunk_results[0].error_code is ProviderErrorCode.CONFLICTING_DUPLICATE


def test_monthly_observation_normalizes_to_complete_civil_month() -> None:
    adapter, http_client = _stack(
        lambda _: _json_response([{"data": "01/02/2024", "valor": "-0.40"}])
    )
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_IPCA_MONTHLY,
            date(2024, 2, 1),
            date(2024, 2, 29),
        )
    finally:
        http_client.close()
    observation = result.observations[0]
    assert observation.content.frequency is Frequency.MONTHLY
    assert observation.content.reference_period.start == date(2024, 2, 1)
    assert observation.content.reference_period.end == date(2024, 2, 29)
    assert observation.content.value_text == "-0.40"


@pytest.mark.parametrize(
    ("registry_key", "value", "expected_text", "expected_scale"),
    [
        (RegistryKey.BCB_SGS_SELIC_TARGET, "10.5", "10.50", 2),
        (RegistryKey.BCB_SGS_SELIC_EFFECTIVE, "0.052788", "0.052788", 6),
        (RegistryKey.BCB_SGS_CDI, "0.052788", "0.052788", 6),
        (RegistryKey.BCB_SGS_USD_SELL, "5.4321", "5.4321", 4),
    ],
)
def test_daily_series_reuse_registry_metadata_and_r3c_normalization(
    registry_key: RegistryKey,
    value: str,
    expected_text: str,
    expected_scale: int,
) -> None:
    adapter, http_client = _stack(
        lambda _: _json_response([{"data": "09/10/2026", "valor": value}])
    )
    try:
        result = adapter.acquire(
            registry_key,
            date(2026, 10, 9),
            date(2026, 10, 9),
        )
    finally:
        http_client.close()
    observation = result.observations[0]
    assert observation.content.value_text == expected_text
    assert observation.content.value_scale == expected_scale
    assert observation.provenance.retrieved_at == UTC_NOW
    assert observation.provenance.published_at is None
    assert observation.provenance.revised_at is None
    assert observation.provenance.provider_revision_id is None


def test_sgs_one_remains_reference_only_and_is_not_reinterpreted_as_valuation() -> None:
    adapter, http_client = _stack(
        lambda _: _json_response([{"data": "09/10/2026", "valor": "5.4321"}])
    )
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_USD_SELL,
            date(2026, 10, 9),
            date(2026, 10, 9),
        )
    finally:
        http_client.close()
    observation = result.observations[0]
    assert observation.content.currency == "BRL/USD"
    assert observation.registry_key is RegistryKey.BCB_SGS_USD_SELL
    assert SeriesUse.REFERENCE_ONLY.value == "REFERENCE_ONLY"
    assert EXTERNAL_SERIES_REGISTRY_VERSION == 1


@pytest.mark.parametrize(
    ("records", "expected_code"),
    [
        ({"data": "01/01/2026", "valor": "1.00"}, ProviderErrorCode.INVALID_SCHEMA),
        ([{"data": None, "valor": "1.00"}], ProviderErrorCode.INVALID_SCHEMA),
        ([{"data": "31/02/2026", "valor": "1.00"}], ProviderErrorCode.INVALID_DATE),
        ([{"data": "01/01/2026", "valor": 1.0}], ProviderErrorCode.INVALID_SCHEMA),
        ([{"data": "01/01/2026", "valor": " NaN"}], ProviderErrorCode.INVALID_VALUE),
        ([{"data": "01/01/2026", "valor": "1,00"}], ProviderErrorCode.INVALID_VALUE),
        ([{"data": "01/01/2026", "valor": "1e2"}], ProviderErrorCode.INVALID_VALUE),
        (
            [{"data": "01/01/2026", "valor": "1.00", "extra": "x"}],
            ProviderErrorCode.INVALID_SCHEMA,
        ),
    ],
)
def test_invalid_payload_is_rejected_atomically(records, expected_code: ProviderErrorCode) -> None:
    adapter, http_client = _stack(lambda _: _json_response(records))
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_TARGET,
            date(2026, 1, 1),
            date(2026, 1, 1),
        )
    finally:
        http_client.close()
    assert result.status is ProviderAcquisitionStatus.FAILED
    assert result.observations == ()
    assert result.chunk_results[0].error_code is expected_code


def test_record_limit_is_enforced_before_normalization() -> None:
    adapter, http_client = _stack(
        lambda _: _json_response(
            [
                {"data": "01/01/2026", "valor": "10.50"},
                {"data": "02/01/2026", "valor": "10.50"},
            ]
        ),
        max_records=1,
    )
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_TARGET,
            date(2026, 1, 1),
            date(2026, 1, 2),
        )
    finally:
        http_client.close()
    assert result.chunk_results[0].error_code is ProviderErrorCode.TOO_MANY_RECORDS


def test_empty_json_is_completed_query_not_synthetic_zero() -> None:
    adapter, http_client = _stack(lambda _: _json_response([]))
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_TARGET,
            date(2026, 1, 1),
            date(2026, 1, 31),
        )
    finally:
        http_client.close()
    chunk = result.chunk_results[0]
    assert result.status is ProviderAcquisitionStatus.EMPTY
    assert chunk.status is ProviderChunkStatus.EMPTY
    assert chunk.empty_response is True
    assert chunk.observations == ()
    assert result.observed_periods == ()


def test_each_completed_response_receives_its_own_injected_utc_timestamp() -> None:
    timestamps = iter(
        [
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
            datetime(2026, 1, 3, tzinfo=timezone.utc),
        ]
    )
    adapter, http_client = _stack(
        lambda request: _json_response([_record_for_request(request)]),
        utc_clock=lambda: next(timestamps),
    )
    try:
        result = adapter.acquire(
            RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
            date(2000, 1, 1),
            date(2020, 1, 1),
        )
    finally:
        http_client.close()
    assert [chunk.retrieved_at.day for chunk in result.chunk_results] == [1, 2, 3]
    assert [observation.provenance.retrieved_at.day for observation in result.observations] == [1, 2, 3]


def test_provider_modules_have_no_store_sqlalchemy_scheduler_or_endpoint_dependency() -> None:
    source = inspect.getsource(adapter_module) + inspect.getsource(client_module)
    forbidden = (
        "sqlalchemy",
        "ExternalObservationStoreService",
        "finalize_acquisition",
        "apscheduler",
        "fastapi",
        "backend.database",
        "pierre",
    )
    assert all(token not in source for token in forbidden)
