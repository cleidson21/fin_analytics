from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import httpx
import pytest

from backend.application.ports.external_observation_provider import (
    ExternalObservationProviderError,
    ProviderErrorCode,
    ProviderInterval,
)
from backend.domains.external_context import RegistryKey
from backend.infrastructure.external.bcb_sgs_client import BCBSGSClient


UTC_NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)


def _client(
    handler,
    **overrides: object,
) -> tuple[BCBSGSClient, httpx.Client]:
    http_client = httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
    )
    options: dict[str, object] = {
        "http_client": http_client,
        "max_attempts": 1,
        "utc_clock": lambda: UTC_NOW,
        "jitter": lambda _: 0.0,
        "sleeper": lambda _: None,
    }
    options.update(overrides)
    return BCBSGSClient(**options), http_client


@pytest.mark.parametrize(
    ("registry_key", "series_id"),
    [
        (RegistryKey.BCB_SGS_SELIC_TARGET, "432"),
        (RegistryKey.BCB_SGS_SELIC_EFFECTIVE, "11"),
        (RegistryKey.BCB_SGS_CDI, "12"),
        (RegistryKey.BCB_SGS_IPCA_MONTHLY, "433"),
        (RegistryKey.BCB_SGS_USD_SELL, "1"),
    ],
)
def test_client_uses_only_official_https_url_and_safe_query_params(
    registry_key: RegistryKey,
    series_id: str,
) -> None:
    received: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        received.append(request)
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json=[],
        )

    client, http_client = _client(handler)
    try:
        result = client.fetch(
            registry_key,
            ProviderInterval(date(2026, 10, 9), date(2026, 10, 9)),
            correlation_id="safe-correlation",
        )
    finally:
        http_client.close()

    assert result.retrieved_at == UTC_NOW
    assert len(received) == 1
    request = received[0]
    assert request.url.scheme == "https"
    assert request.url.host == "api.bcb.gov.br"
    assert request.url.path == f"/dados/serie/bcdata.sgs.{series_id}/dados"
    assert dict(request.url.params) == {
        "formato": "json",
        "dataInicial": "09/10/2026",
        "dataFinal": "09/10/2026",
    }


def test_client_rejects_non_allowlisted_registry_input_before_transport() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=[])

    client, http_client = _client(handler)
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                "ARBITRARY",  # type: ignore[arg-type]
                ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is ProviderErrorCode.INVALID_REGISTRY_KEY
    assert calls == 0


def test_client_refuses_daily_interval_above_one_request_limit() -> None:
    client, http_client = _client(lambda _: httpx.Response(200, json=[]))
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                RegistryKey.BCB_SGS_SELIC_EFFECTIVE,
                ProviderInterval(date(2000, 1, 1), date(2010, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is ProviderErrorCode.DAILY_INTERVAL_LIMIT_EXCEEDED


def test_redirect_is_not_followed() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(302, headers={"location": "https://example.invalid"})

    client, http_client = _client(handler)
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                RegistryKey.BCB_SGS_CDI,
                ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is ProviderErrorCode.UNEXPECTED_REDIRECT
    assert len(requests) == 1


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_permanent_http_errors_are_not_retried(status: int) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status)

    client, http_client = _client(handler, max_attempts=3)
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                RegistryKey.BCB_SGS_SELIC_TARGET,
                ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is ProviderErrorCode.HTTP_PERMANENT_FAILURE
    assert failure.value.http_status == status
    assert len(requests) == 1


@pytest.mark.parametrize("status", [408, 429, 500, 503])
def test_transient_http_errors_retry_with_a_hard_attempt_limit(status: int) -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(status)

    client, http_client = _client(handler, max_attempts=3)
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                RegistryKey.BCB_SGS_SELIC_TARGET,
                ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is ProviderErrorCode.HTTP_TRANSIENT_FAILURE
    assert failure.value.transient is True
    assert failure.value.attempts == 3
    assert attempts == 3


def test_transient_retry_can_recover_without_repeating_success() -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503)
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json=[],
        )

    client, http_client = _client(handler, max_attempts=3)
    try:
        response = client.fetch(
            RegistryKey.BCB_SGS_SELIC_TARGET,
            ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
        )
    finally:
        http_client.close()
    assert response.attempts == 2
    assert attempts == 2


def test_retry_after_delta_seconds_is_respected_within_budget() -> None:
    sleeps: list[float] = []
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"retry-after": "2"})
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json=[],
        )

    client, http_client = _client(
        handler,
        max_attempts=2,
        sleeper=sleeps.append,
    )
    try:
        client.fetch(
            RegistryKey.BCB_SGS_SELIC_TARGET,
            ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
        )
    finally:
        http_client.close()
    assert sleeps == [2.0]


def test_invalid_retry_after_falls_back_to_bounded_backoff() -> None:
    sleeps: list[float] = []
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"retry-after": "invalid"})
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json=[],
        )

    client, http_client = _client(
        handler,
        max_attempts=2,
        sleeper=sleeps.append,
    )
    try:
        client.fetch(
            RegistryKey.BCB_SGS_SELIC_TARGET,
            ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
        )
    finally:
        http_client.close()
    assert sleeps == [0.5]


def test_retry_after_above_remaining_budget_fails_without_sleeping() -> None:
    sleeps: list[float] = []
    client, http_client = _client(
        lambda _: httpx.Response(429, headers={"retry-after": "61"}),
        max_attempts=2,
        sleeper=sleeps.append,
    )
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                RegistryKey.BCB_SGS_SELIC_TARGET,
                ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is ProviderErrorCode.ACQUISITION_BUDGET_EXHAUSTED
    assert failure.value.attempts == 1
    assert sleeps == []


@pytest.mark.parametrize(
    ("exception_factory", "expected_code"),
    [
        (
            lambda request: httpx.ReadTimeout("timeout", request=request),
            ProviderErrorCode.TIMEOUT,
        ),
        (
            lambda request: httpx.ConnectError("connection", request=request),
            ProviderErrorCode.CONNECTION_ERROR,
        ),
    ],
)
def test_transport_failures_are_retried_and_remain_typed(
    exception_factory,
    expected_code: ProviderErrorCode,
) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise exception_factory(request)

    client, http_client = _client(handler, max_attempts=3)
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                RegistryKey.BCB_SGS_SELIC_TARGET,
                ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is expected_code
    assert failure.value.attempts == 3
    assert attempts == 3


def test_invalid_content_type_is_rejected_without_payload_logging() -> None:
    client, http_client = _client(
        lambda _: httpx.Response(200, headers={"content-type": "text/html"}, text="secret")
    )
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                RegistryKey.BCB_SGS_SELIC_TARGET,
                ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is ProviderErrorCode.INVALID_CONTENT_TYPE
    assert "secret" not in str(failure.value)


def test_declared_oversized_body_is_rejected_before_reading() -> None:
    client, http_client = _client(
        lambda _: httpx.Response(
            200,
            headers={
                "content-type": "application/json",
                "content-length": "6",
            },
            content=b"123456",
        ),
        max_response_bytes=5,
    )
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                RegistryKey.BCB_SGS_SELIC_TARGET,
                ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is ProviderErrorCode.RESPONSE_TOO_LARGE


class _TrackingStream(httpx.SyncByteStream):
    def __init__(self) -> None:
        self.yielded = 0

    def __iter__(self):
        for chunk in (b"123", b"456", b"789"):
            self.yielded += 1
            yield chunk


def test_streaming_limit_stops_body_without_content_length() -> None:
    stream = _TrackingStream()
    client, http_client = _client(
        lambda _: httpx.Response(
            200,
            headers={"content-type": "application/json"},
            stream=stream,
        ),
        max_response_bytes=5,
    )
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                RegistryKey.BCB_SGS_SELIC_TARGET,
                ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is ProviderErrorCode.RESPONSE_TOO_LARGE
    assert stream.yielded == 2


def test_invalid_content_length_is_typed() -> None:
    client, http_client = _client(
        lambda _: httpx.Response(
            200,
            headers={
                "content-type": "application/json",
                "content-length": "not-a-number",
            },
            content=b"[]",
        )
    )
    try:
        with pytest.raises(ExternalObservationProviderError) as failure:
            client.fetch(
                RegistryKey.BCB_SGS_SELIC_TARGET,
                ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
            )
    finally:
        http_client.close()
    assert failure.value.code is ProviderErrorCode.INVALID_RESPONSE_HEADER


def test_http_date_retry_after_is_supported() -> None:
    sleeps: list[float] = []
    attempts = 0
    retry_time = (UTC_NOW + timedelta(seconds=3)).strftime("%a, %d %b %Y %H:%M:%S GMT")

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"retry-after": retry_time})
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json=[],
        )

    client, http_client = _client(handler, max_attempts=2, sleeper=sleeps.append)
    try:
        client.fetch(
            RegistryKey.BCB_SGS_SELIC_TARGET,
            ProviderInterval(date(2026, 1, 1), date(2026, 1, 1)),
        )
    finally:
        http_client.close()
    assert sleeps == [3.0]
