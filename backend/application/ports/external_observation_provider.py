"""Typed application boundary for governed external-observation acquisition."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum

from backend.domains.external_context import (
    ExternalObservation,
    Frequency,
    RegistryKey,
    resolve_series_by_key,
)


DAILY_MAX_CALENDAR_YEARS = 10


class ProviderAcquisitionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    EMPTY = "EMPTY"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ProviderChunkStatus(str, Enum):
    SUCCESS = "SUCCESS"
    EMPTY = "EMPTY"
    FAILED = "FAILED"
    INCOMPLETE = "INCOMPLETE"


class ProviderErrorCode(str, Enum):
    INVALID_REGISTRY_KEY = "INVALID_REGISTRY_KEY"
    INVALID_INTERVAL = "INVALID_INTERVAL"
    INTERVAL_BEFORE_FLOOR = "INTERVAL_BEFORE_FLOOR"
    DAILY_INTERVAL_LIMIT_EXCEEDED = "DAILY_INTERVAL_LIMIT_EXCEEDED"
    CHUNK_PLANNING_FAILED = "CHUNK_PLANNING_FAILED"
    ACQUISITION_BUDGET_EXHAUSTED = "ACQUISITION_BUDGET_EXHAUSTED"
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    HTTP_TRANSIENT_FAILURE = "HTTP_TRANSIENT_FAILURE"
    HTTP_PERMANENT_FAILURE = "HTTP_PERMANENT_FAILURE"
    UNEXPECTED_REDIRECT = "UNEXPECTED_REDIRECT"
    INVALID_RESPONSE_HEADER = "INVALID_RESPONSE_HEADER"
    RESPONSE_TOO_LARGE = "RESPONSE_TOO_LARGE"
    TOO_MANY_RECORDS = "TOO_MANY_RECORDS"
    INVALID_CONTENT_TYPE = "INVALID_CONTENT_TYPE"
    INVALID_JSON = "INVALID_JSON"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    INVALID_DATE = "INVALID_DATE"
    INVALID_VALUE = "INVALID_VALUE"
    CONFLICTING_DUPLICATE = "CONFLICTING_DUPLICATE"
    CERTIFICATION_REJECTED = "CERTIFICATION_REJECTED"


class ExternalObservationProviderError(Exception):
    """Safe, typed failure at the external-provider boundary."""

    def __init__(
        self,
        code: ProviderErrorCode,
        message: str,
        *,
        transient: bool = False,
        http_status: int | None = None,
        retry_after_seconds: float | None = None,
        attempts: int = 0,
    ) -> None:
        super().__init__(message)
        if not isinstance(code, ProviderErrorCode):
            raise TypeError("code must be a ProviderErrorCode.")
        if type(transient) is not bool:
            raise TypeError("transient must be a strict boolean.")
        if http_status is not None and (
            type(http_status) is not int or not 100 <= http_status <= 599
        ):
            raise ValueError("http_status must be a valid HTTP status or None.")
        if retry_after_seconds is not None and (
            type(retry_after_seconds) not in {int, float}
            or retry_after_seconds < 0
        ):
            raise ValueError("retry_after_seconds must be non-negative or None.")
        if type(attempts) is not int or attempts < 0:
            raise ValueError("attempts must be a non-negative strict integer.")
        self.code = code
        self.transient = transient
        self.http_status = http_status
        self.retry_after_seconds = (
            float(retry_after_seconds)
            if retry_after_seconds is not None
            else None
        )
        self.attempts = attempts


@dataclass(frozen=True, order=True)
class ProviderInterval:
    start: date
    end: date

    def __post_init__(self) -> None:
        if type(self.start) is not date or type(self.end) is not date:
            raise TypeError("Provider interval boundaries must be strict civil dates.")
        if self.end < self.start:
            raise ValueError("Provider interval end cannot precede its start.")


@dataclass(frozen=True)
class ProviderChunkResult:
    registry_key: RegistryKey
    interval: ProviderInterval
    status: ProviderChunkStatus
    response_received: bool
    payload_validated: bool
    normalization_completed: bool
    observations: tuple[ExternalObservation, ...]
    empty_response: bool
    duplicate_records: int = 0
    http_attempts: int = 0
    retrieved_at: datetime | None = None
    http_status: int | None = None
    error_code: ProviderErrorCode | None = None
    terminal_failure: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.registry_key, RegistryKey):
            raise TypeError("registry_key must be a RegistryKey.")
        if not isinstance(self.interval, ProviderInterval):
            raise TypeError("interval must be a ProviderInterval.")
        if not isinstance(self.status, ProviderChunkStatus):
            raise TypeError("status must be a ProviderChunkStatus.")
        for field_name in (
            "response_received",
            "payload_validated",
            "normalization_completed",
            "empty_response",
            "terminal_failure",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise TypeError(f"{field_name} must be a strict boolean.")
        if type(self.observations) is not tuple or any(
            not isinstance(observation, ExternalObservation)
            for observation in self.observations
        ):
            raise TypeError("observations must be a tuple of ExternalObservation values.")
        if type(self.duplicate_records) is not int or self.duplicate_records < 0:
            raise ValueError("duplicate_records must be a non-negative strict integer.")
        if type(self.http_attempts) is not int or self.http_attempts < 0:
            raise ValueError("http_attempts must be a non-negative strict integer.")
        if self.payload_validated and not self.response_received:
            raise ValueError("A payload cannot be validated before receipt.")
        if self.normalization_completed and not self.payload_validated:
            raise ValueError("Normalization cannot complete before payload validation.")
        if self.empty_response and self.observations:
            raise ValueError("An empty response cannot contain observations.")
        if self.status is ProviderChunkStatus.SUCCESS:
            if not self.is_complete or not self.observations or self.empty_response:
                raise ValueError("SUCCESS requires complete non-empty certified content.")
        elif self.status is ProviderChunkStatus.EMPTY:
            if not self.is_complete or self.observations or not self.empty_response:
                raise ValueError("EMPTY requires a complete valid empty response.")
        elif self.status is ProviderChunkStatus.FAILED:
            if self.error_code is None or not self.terminal_failure:
                raise ValueError("FAILED requires a terminal typed error.")
            if self.observations:
                raise ValueError("A failed chunk cannot expose partially accepted observations.")
        elif self.status is ProviderChunkStatus.INCOMPLETE:
            if self.error_code is None or self.terminal_failure:
                raise ValueError("INCOMPLETE requires a non-terminal typed reason.")
            if self.observations or self.response_received:
                raise ValueError("An unexecuted incomplete chunk cannot contain response data.")
        if self.retrieved_at is not None:
            if type(self.retrieved_at) is not datetime:
                raise TypeError("retrieved_at must be a datetime or None.")
            if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() != timedelta(0):
                raise ValueError("retrieved_at must be timezone-aware UTC.")
        if self.response_received and self.retrieved_at is None:
            raise ValueError("A received complete response requires retrieved_at.")
        if self.response_received and self.http_attempts < 1:
            raise ValueError("A received response requires at least one HTTP attempt.")
        if self.status is ProviderChunkStatus.INCOMPLETE and self.http_attempts != 0:
            raise ValueError("An unexecuted incomplete chunk cannot report HTTP attempts.")
        if self.http_status is not None and (
            type(self.http_status) is not int or not 100 <= self.http_status <= 599
        ):
            raise ValueError("http_status must be a valid HTTP status or None.")

    @property
    def is_complete(self) -> bool:
        return (
            self.response_received
            and self.payload_validated
            and self.normalization_completed
        )

    @property
    def observation_count(self) -> int:
        return len(self.observations)


@dataclass(frozen=True)
class ProviderAcquisitionResult:
    registry_key: RegistryKey
    requested_interval: ProviderInterval
    planned_chunks: tuple[ProviderInterval, ...]
    chunk_results: tuple[ProviderChunkResult, ...]
    observations: tuple[ExternalObservation, ...]
    status: ProviderAcquisitionStatus

    def __post_init__(self) -> None:
        if not isinstance(self.registry_key, RegistryKey):
            raise TypeError("registry_key must be a RegistryKey.")
        if not isinstance(self.requested_interval, ProviderInterval):
            raise TypeError("requested_interval must be a ProviderInterval.")
        if type(self.planned_chunks) is not tuple or not self.planned_chunks:
            raise ValueError("planned_chunks must be a non-empty tuple.")
        if type(self.chunk_results) is not tuple:
            raise TypeError("chunk_results must be a tuple.")
        if len(self.planned_chunks) != len(self.chunk_results):
            raise ValueError("Every planned chunk must have exactly one result.")
        if tuple(result.interval for result in self.chunk_results) != self.planned_chunks:
            raise ValueError("Chunk results must preserve the complete ordered plan.")
        if any(result.registry_key is not self.registry_key for result in self.chunk_results):
            raise ValueError("Chunk results must use the acquisition registry key.")
        flattened = tuple(
            observation
            for result in self.chunk_results
            for observation in result.observations
        )
        if self.observations != flattened:
            raise ValueError("observations must exactly flatten the ordered chunk results.")
        if not isinstance(self.status, ProviderAcquisitionStatus):
            raise TypeError("status must be a ProviderAcquisitionStatus.")
        if self.status is not self.derived_status:
            raise ValueError("status is inconsistent with the chunk evidence.")

    @property
    def derived_status(self) -> ProviderAcquisitionStatus:
        completed = tuple(result for result in self.chunk_results if result.is_complete)
        if len(completed) == len(self.chunk_results):
            return (
                ProviderAcquisitionStatus.SUCCESS
                if self.observations
                else ProviderAcquisitionStatus.EMPTY
            )
        if completed:
            return ProviderAcquisitionStatus.PARTIAL
        return ProviderAcquisitionStatus.FAILED

    @property
    def completed_chunks(self) -> tuple[ProviderChunkResult, ...]:
        return tuple(result for result in self.chunk_results if result.is_complete)

    @property
    def failed_or_incomplete_chunks(self) -> tuple[ProviderChunkResult, ...]:
        return tuple(result for result in self.chunk_results if not result.is_complete)

    @property
    def queried_intervals(self) -> tuple[ProviderInterval, ...]:
        return tuple(result.interval for result in self.completed_chunks)

    @property
    def observed_periods(self) -> tuple[ProviderInterval, ...]:
        return tuple(
            ProviderInterval(
                observation.content.reference_period.start,
                observation.content.reference_period.end,
            )
            for observation in self.observations
        )

    @property
    def observation_count(self) -> int:
        return len(self.observations)

    @property
    def is_complete(self) -> bool:
        return len(self.completed_chunks) == len(self.chunk_results)


def _calendar_anniversary(value: date, *, years: int) -> date:
    target_year = value.year + years
    if target_year > date.max.year:
        return date.max
    try:
        return value.replace(year=target_year)
    except ValueError:
        # Conservative policy for 29 February: clamp to 28 February.  The
        # inclusive chunk ends one day before this anniversary, so it can never
        # exceed the provider's ten-civil-year maximum.
        return value.replace(year=target_year, day=28)


def maximum_daily_chunk_end(start: date) -> date:
    if type(start) is not date:
        raise TypeError("start must be a strict civil date.")
    anniversary = _calendar_anniversary(start, years=DAILY_MAX_CALENDAR_YEARS)
    return anniversary if anniversary == date.max else anniversary - timedelta(days=1)


def daily_interval_within_limit(interval: ProviderInterval) -> bool:
    if not isinstance(interval, ProviderInterval):
        raise TypeError("interval must be a ProviderInterval.")
    return interval.end <= maximum_daily_chunk_end(interval.start)


def plan_provider_chunks(
    registry_key: RegistryKey | str,
    start: date,
    end: date,
) -> tuple[ProviderInterval, ...]:
    """Return an exact, ordered, gap-free provider request plan."""

    try:
        definition = resolve_series_by_key(registry_key)
    except Exception as exc:
        raise ExternalObservationProviderError(
            ProviderErrorCode.INVALID_REGISTRY_KEY,
            "The requested external series is not allowlisted.",
        ) from exc
    if type(start) is not date or type(end) is not date or end < start:
        raise ExternalObservationProviderError(
            ProviderErrorCode.INVALID_INTERVAL,
            "The provider interval must contain ordered strict civil dates.",
        )
    if start < definition.earliest_normalized_date:
        raise ExternalObservationProviderError(
            ProviderErrorCode.INTERVAL_BEFORE_FLOOR,
            "The provider interval precedes the registry-normalized floor.",
        )
    requested = ProviderInterval(start, end)
    if definition.frequency is Frequency.MONTHLY:
        return (requested,)

    chunks: list[ProviderInterval] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(maximum_daily_chunk_end(cursor), end)
        chunks.append(ProviderInterval(cursor, chunk_end))
        if chunk_end == end:
            break
        cursor = chunk_end + timedelta(days=1)
    return tuple(chunks)


class ExternalObservationProvider(ABC):
    @abstractmethod
    def acquire(
        self,
        registry_key: RegistryKey | str,
        start: date,
        end: date,
        *,
        correlation_id: str | None = None,
    ) -> ProviderAcquisitionResult:
        """Acquire and certify external observations without persistence."""
