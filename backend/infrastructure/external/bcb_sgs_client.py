"""Bounded single-request HTTP client for the official BCB/SGS endpoint."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from backend.application.ports.external_observation_provider import (
    ExternalObservationProviderError,
    ProviderErrorCode,
    ProviderInterval,
    daily_interval_within_limit,
)
from backend.domains.external_context import Frequency, RegistryKey, resolve_series_by_key


logger = logging.getLogger(__name__)

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_CONNECT_TIMEOUT_SECONDS = 5.0
DEFAULT_READ_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_RESPONSE_BYTES = 1024 * 1024
DEFAULT_MAX_RECORDS = 5_000
DEFAULT_OPERATION_BUDGET_SECONDS = 60.0


@dataclass(frozen=True)
class BCBSGSHTTPResponse:
    registry_key: RegistryKey
    interval: ProviderInterval
    body: bytes
    retrieved_at: datetime
    http_status: int
    attempts: int

    def __post_init__(self) -> None:
        if not isinstance(self.registry_key, RegistryKey):
            raise TypeError("registry_key must be a RegistryKey.")
        if not isinstance(self.interval, ProviderInterval):
            raise TypeError("interval must be a ProviderInterval.")
        if type(self.body) is not bytes:
            raise TypeError("body must be bytes.")
        if type(self.retrieved_at) is not datetime:
            raise TypeError("retrieved_at must be a datetime.")
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware UTC.")
        if self.retrieved_at.utcoffset().total_seconds() != 0:
            raise ValueError("retrieved_at must use the UTC offset.")
        if type(self.http_status) is not int or not 200 <= self.http_status <= 299:
            raise ValueError("http_status must be a successful HTTP status.")
        if type(self.attempts) is not int or self.attempts < 1:
            raise ValueError("attempts must be a positive strict integer.")


def _default_jitter(upper_bound: float) -> float:
    return random.uniform(0.0, upper_bound)


class BCBSGSClient:
    """Execute one bounded BCB request; interval partitioning belongs upstream."""

    def __init__(
        self,
        *,
        http_client: httpx.Client | None = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        connect_timeout_seconds: float = DEFAULT_CONNECT_TIMEOUT_SECONDS,
        read_timeout_seconds: float = DEFAULT_READ_TIMEOUT_SECONDS,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        max_records: int = DEFAULT_MAX_RECORDS,
        operation_budget_seconds: float = DEFAULT_OPERATION_BUDGET_SECONDS,
        utc_clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        monotonic: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
        jitter: Callable[[float], float] = _default_jitter,
    ) -> None:
        if type(max_attempts) is not int or not 1 <= max_attempts <= 10:
            raise ValueError("max_attempts must be a strict integer from 1 to 10.")
        for name, value, maximum in (
            ("connect_timeout_seconds", connect_timeout_seconds, 30.0),
            ("read_timeout_seconds", read_timeout_seconds, 120.0),
            ("operation_budget_seconds", operation_budget_seconds, 300.0),
        ):
            if type(value) not in {int, float} or not 0 < value <= maximum:
                raise ValueError(f"{name} must be positive and at most {maximum}.")
        if type(max_response_bytes) is not int or not 1 <= max_response_bytes <= 8 * 1024 * 1024:
            raise ValueError("max_response_bytes must be from 1 byte through 8 MiB.")
        if type(max_records) is not int or not 1 <= max_records <= 25_000:
            raise ValueError("max_records must be a strict integer from 1 to 25000.")
        for name, callback in (
            ("utc_clock", utc_clock),
            ("monotonic", monotonic),
            ("sleeper", sleeper),
            ("jitter", jitter),
        ):
            if not callable(callback):
                raise TypeError(f"{name} must be callable.")

        self._max_attempts = max_attempts
        self._connect_timeout_seconds = float(connect_timeout_seconds)
        self._read_timeout_seconds = float(read_timeout_seconds)
        self._max_response_bytes = max_response_bytes
        self._max_records = max_records
        self._operation_budget_seconds = float(operation_budget_seconds)
        self._utc_clock = utc_clock
        self._monotonic = monotonic
        self._sleeper = sleeper
        self._jitter = jitter
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            verify=True,
            follow_redirects=False,
            timeout=self._timeout(self._operation_budget_seconds),
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
        )

    @property
    def max_records(self) -> int:
        return self._max_records

    @property
    def max_response_bytes(self) -> int:
        return self._max_response_bytes

    def __enter__(self) -> "BCBSGSClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def fetch(
        self,
        registry_key: RegistryKey,
        interval: ProviderInterval,
        *,
        correlation_id: str | None = None,
        deadline: float | None = None,
    ) -> BCBSGSHTTPResponse:
        if not isinstance(registry_key, RegistryKey):
            raise ExternalObservationProviderError(
                ProviderErrorCode.INVALID_REGISTRY_KEY,
                "The BCB client requires an allowlisted registry key.",
            )
        if not isinstance(interval, ProviderInterval):
            raise ExternalObservationProviderError(
                ProviderErrorCode.INVALID_INTERVAL,
                "The BCB client requires a typed provider interval.",
            )
        self._validate_correlation_id(correlation_id)
        definition = resolve_series_by_key(registry_key)
        if interval.start < definition.earliest_normalized_date:
            raise ExternalObservationProviderError(
                ProviderErrorCode.INTERVAL_BEFORE_FLOOR,
                "The request interval precedes the registry-normalized floor.",
            )
        if definition.frequency is Frequency.DAILY and not daily_interval_within_limit(interval):
            raise ExternalObservationProviderError(
                ProviderErrorCode.DAILY_INTERVAL_LIMIT_EXCEEDED,
                "One DAILY HTTP request cannot exceed the conservative ten-year limit.",
            )

        started = self._monotonic()
        operation_deadline = started + self._operation_budget_seconds
        if deadline is not None:
            if type(deadline) not in {int, float}:
                raise TypeError("deadline must be a monotonic numeric instant or None.")
            operation_deadline = min(operation_deadline, float(deadline))

        params = {
            "formato": "json",
            "dataInicial": interval.start.strftime("%d/%m/%Y"),
            "dataFinal": interval.end.strftime("%d/%m/%Y"),
        }
        url = definition.provenance.source_url

        for attempt in range(1, self._max_attempts + 1):
            remaining = operation_deadline - self._monotonic()
            if remaining <= 0:
                raise self._budget_error(attempts=attempt - 1)
            try:
                with self._client.stream(
                    "GET",
                    url,
                    params=params,
                    follow_redirects=False,
                    timeout=self._timeout(remaining),
                ) as response:
                    status = response.status_code
                    logger.info(
                        "bcb_sgs.http_attempt",
                        extra={
                            "registry_key": registry_key.value,
                            "start": interval.start.isoformat(),
                            "end": interval.end.isoformat(),
                            "status": status,
                            "attempt": attempt,
                            "correlation_id": correlation_id,
                        },
                    )
                    if 300 <= status <= 399:
                        raise ExternalObservationProviderError(
                            ProviderErrorCode.UNEXPECTED_REDIRECT,
                            "The governed BCB endpoint returned an unexpected redirect.",
                            http_status=status,
                            attempts=attempt,
                        )
                    if status in {408, 429} or 500 <= status <= 599:
                        if attempt == self._max_attempts:
                            raise ExternalObservationProviderError(
                                ProviderErrorCode.HTTP_TRANSIENT_FAILURE,
                                "The BCB request exhausted bounded transient retries.",
                                transient=True,
                                http_status=status,
                                attempts=attempt,
                            )
                        retry_after = self._retry_after_seconds(response)
                        self._bounded_wait(
                            attempt=attempt,
                            retry_after=retry_after,
                            deadline=operation_deadline,
                        )
                        continue
                    if status < 200 or status > 299:
                        raise ExternalObservationProviderError(
                            ProviderErrorCode.HTTP_PERMANENT_FAILURE,
                            "The BCB endpoint returned a permanent HTTP failure.",
                            http_status=status,
                            attempts=attempt,
                        )
                    self._validate_content_type(response)
                    body = self._read_bounded_body(response)
                    retrieved_at = self._utc_clock()
                    self._validate_utc_clock(retrieved_at)
                    return BCBSGSHTTPResponse(
                        registry_key=registry_key,
                        interval=interval,
                        body=body,
                        retrieved_at=retrieved_at,
                        http_status=status,
                        attempts=attempt,
                    )
            except ExternalObservationProviderError as exc:
                if exc.attempts == 0:
                    exc.attempts = attempt
                raise
            except httpx.TimeoutException as exc:
                if attempt == self._max_attempts:
                    raise ExternalObservationProviderError(
                        ProviderErrorCode.TIMEOUT,
                        "The BCB request timed out after bounded retries.",
                        transient=True,
                        attempts=attempt,
                    ) from exc
                self._bounded_wait(
                    attempt=attempt,
                    retry_after=None,
                    deadline=operation_deadline,
                )
            except httpx.RequestError as exc:
                if attempt == self._max_attempts:
                    raise ExternalObservationProviderError(
                        ProviderErrorCode.CONNECTION_ERROR,
                        "The BCB request failed to connect after bounded retries.",
                        transient=True,
                        attempts=attempt,
                    ) from exc
                self._bounded_wait(
                    attempt=attempt,
                    retry_after=None,
                    deadline=operation_deadline,
                )

        raise AssertionError("The bounded HTTP attempt loop must return or raise.")

    def _read_bounded_body(self, response: httpx.Response) -> bytes:
        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError as exc:
                raise ExternalObservationProviderError(
                    ProviderErrorCode.INVALID_RESPONSE_HEADER,
                    "The BCB response contained an invalid Content-Length header.",
                    http_status=response.status_code,
                ) from exc
            if declared_length < 0:
                raise ExternalObservationProviderError(
                    ProviderErrorCode.INVALID_RESPONSE_HEADER,
                    "The BCB response contained a negative Content-Length header.",
                    http_status=response.status_code,
                )
            if declared_length > self._max_response_bytes:
                raise ExternalObservationProviderError(
                    ProviderErrorCode.RESPONSE_TOO_LARGE,
                    "The BCB response exceeds the configured byte limit.",
                    http_status=response.status_code,
                )

        chunks: list[bytes] = []
        received = 0
        for chunk in response.iter_bytes():
            received += len(chunk)
            if received > self._max_response_bytes:
                raise ExternalObservationProviderError(
                    ProviderErrorCode.RESPONSE_TOO_LARGE,
                    "The streamed BCB response exceeds the configured byte limit.",
                    http_status=response.status_code,
                )
            chunks.append(chunk)
        return b"".join(chunks)

    @staticmethod
    def _validate_content_type(response: httpx.Response) -> None:
        raw_content_type = response.headers.get("content-type", "")
        media_type = raw_content_type.split(";", 1)[0].strip().lower()
        if media_type != "application/json":
            raise ExternalObservationProviderError(
                ProviderErrorCode.INVALID_CONTENT_TYPE,
                "The BCB response Content-Type is not application/json.",
                http_status=response.status_code,
            )

    def _retry_after_seconds(self, response: httpx.Response) -> float | None:
        value = response.headers.get("retry-after")
        if value is None:
            return None
        stripped = value.strip()
        if stripped.isascii() and stripped.isdigit():
            return float(int(stripped))
        try:
            parsed = parsedate_to_datetime(stripped)
        except (TypeError, ValueError, OverflowError):
            return None
        if parsed.tzinfo is None:
            return None
        now = self._utc_clock()
        self._validate_utc_clock(now)
        return max(0.0, (parsed.astimezone(timezone.utc) - now).total_seconds())

    def _bounded_wait(
        self,
        *,
        attempt: int,
        retry_after: float | None,
        deadline: float,
    ) -> None:
        base = min(0.5 * (2 ** (attempt - 1)), 8.0)
        jitter = self._jitter(base * 0.25)
        if type(jitter) not in {int, float} or jitter < 0:
            raise ValueError("Injected jitter must return a non-negative number.")
        wait = retry_after if retry_after is not None else base + float(jitter)
        remaining = deadline - self._monotonic()
        if wait > remaining:
            raise self._budget_error(
                retry_after=retry_after,
                attempts=attempt,
            )
        self._sleeper(wait)

    def _timeout(self, remaining: float) -> httpx.Timeout:
        bounded = max(0.001, remaining)
        return httpx.Timeout(
            connect=min(self._connect_timeout_seconds, bounded),
            read=min(self._read_timeout_seconds, bounded),
            write=min(self._connect_timeout_seconds, bounded),
            pool=min(self._connect_timeout_seconds, bounded),
        )

    @staticmethod
    def _validate_correlation_id(correlation_id: str | None) -> None:
        if correlation_id is None:
            return
        if type(correlation_id) is not str or not 1 <= len(correlation_id) <= 128:
            raise ValueError("correlation_id must contain between 1 and 128 characters.")
        if any(
            not (
                character.isascii()
                and (character.isalnum() or character in "-_.:")
            )
            for character in correlation_id
        ):
            raise ValueError("correlation_id contains unsafe characters.")

    @staticmethod
    def _validate_utc_clock(value: datetime) -> None:
        if type(value) is not datetime or value.tzinfo is None:
            raise ValueError("The injected UTC clock must return an aware datetime.")
        if value.utcoffset() is None or value.utcoffset().total_seconds() != 0:
            raise ValueError("The injected UTC clock must return a UTC datetime.")

    @staticmethod
    def _budget_error(
        *,
        retry_after: float | None = None,
        attempts: int = 0,
    ) -> ExternalObservationProviderError:
        return ExternalObservationProviderError(
            ProviderErrorCode.ACQUISITION_BUDGET_EXHAUSTED,
            "The bounded BCB request operation exhausted its elapsed-time budget.",
            transient=True,
            retry_after_seconds=retry_after,
            attempts=attempts,
        )
