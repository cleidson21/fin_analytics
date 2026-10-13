"""Registry-aware, persistence-free BCB/SGS multichunk provider adapter."""

from __future__ import annotations

import calendar
import json
import re
import time
from datetime import date, datetime

from backend.application.ports.external_observation_provider import (
    ExternalObservationProvider,
    ExternalObservationProviderError,
    ProviderAcquisitionResult,
    ProviderAcquisitionStatus,
    ProviderChunkResult,
    ProviderChunkStatus,
    ProviderErrorCode,
    ProviderInterval,
    plan_provider_chunks,
)
from backend.domains.external_context import (
    DecimalNormalizationError,
    ExternalContextDomainError,
    ExternalObservation,
    Frequency,
    ReferencePeriodError,
    RegistryKey,
    normalize_external_observation,
    resolve_series_by_key,
)
from backend.infrastructure.external.bcb_sgs_client import (
    BCBSGSClient,
    BCBSGSHTTPResponse,
)


_SGS_DATE_PATTERN = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", flags=re.ASCII)
DEFAULT_MAX_CHUNKS_PER_ACQUISITION = 100
DEFAULT_ACQUISITION_BUDGET_SECONDS = 300.0


class BCBSGSAdapter(ExternalObservationProvider):
    """Acquire, validate, certify, and consolidate official SGS observations."""

    def __init__(
        self,
        client: BCBSGSClient,
        *,
        max_chunks: int = DEFAULT_MAX_CHUNKS_PER_ACQUISITION,
        acquisition_budget_seconds: float = DEFAULT_ACQUISITION_BUDGET_SECONDS,
        monotonic=time.monotonic,
    ) -> None:
        if not isinstance(client, BCBSGSClient):
            raise TypeError("client must be a BCBSGSClient.")
        if type(max_chunks) is not int or not 1 <= max_chunks <= 1_000:
            raise ValueError("max_chunks must be a strict integer from 1 to 1000.")
        if (
            type(acquisition_budget_seconds) not in {int, float}
            or not 0 < acquisition_budget_seconds <= 3_600
        ):
            raise ValueError(
                "acquisition_budget_seconds must be positive and at most 3600."
            )
        if not callable(monotonic):
            raise TypeError("monotonic must be callable.")
        self._client = client
        self._max_chunks = max_chunks
        self._acquisition_budget_seconds = float(acquisition_budget_seconds)
        self._monotonic = monotonic

    def acquire(
        self,
        registry_key: RegistryKey | str,
        start: date,
        end: date,
        *,
        correlation_id: str | None = None,
    ) -> ProviderAcquisitionResult:
        planned = plan_provider_chunks(registry_key, start, end)
        definition = resolve_series_by_key(registry_key)
        deadline = self._monotonic() + self._acquisition_budget_seconds
        results: list[ProviderChunkResult] = []

        for index, interval in enumerate(planned):
            if index >= self._max_chunks or self._monotonic() >= deadline:
                results.extend(
                    self._incomplete_result(definition.registry_key, pending)
                    for pending in planned[index:]
                )
                break
            try:
                response = self._client.fetch(
                    definition.registry_key,
                    interval,
                    correlation_id=correlation_id,
                    deadline=deadline,
                )
                results.append(self._parse_and_certify(response))
            except ExternalObservationProviderError as exc:
                results.append(
                    ProviderChunkResult(
                        registry_key=definition.registry_key,
                        interval=interval,
                        status=ProviderChunkStatus.FAILED,
                        response_received=False,
                        payload_validated=False,
                        normalization_completed=False,
                        observations=(),
                        empty_response=False,
                        duplicate_records=0,
                        http_attempts=exc.attempts,
                        http_status=exc.http_status,
                        error_code=exc.code,
                        terminal_failure=True,
                    )
                )
                if exc.code is ProviderErrorCode.ACQUISITION_BUDGET_EXHAUSTED:
                    results.extend(
                        self._incomplete_result(definition.registry_key, pending)
                        for pending in planned[index + 1 :]
                    )
                    break

        chunk_results = tuple(results)
        observations = tuple(
            observation
            for result in chunk_results
            for observation in result.observations
        )
        status = self._derive_status(chunk_results, observations)
        return ProviderAcquisitionResult(
            registry_key=definition.registry_key,
            requested_interval=ProviderInterval(start, end),
            planned_chunks=planned,
            chunk_results=chunk_results,
            observations=observations,
            status=status,
        )

    def _parse_and_certify(
        self,
        response: BCBSGSHTTPResponse,
    ) -> ProviderChunkResult:
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self._received_failure(
                response,
                ProviderErrorCode.INVALID_JSON,
            )
        if type(payload) is not list:
            return self._received_failure(
                response,
                ProviderErrorCode.INVALID_SCHEMA,
            )
        if len(payload) > self._client.max_records:
            return self._received_failure(
                response,
                ProviderErrorCode.TOO_MANY_RECORDS,
            )

        definition = resolve_series_by_key(response.registry_key)
        normalized_by_period: dict[tuple[date, date], ExternalObservation] = {}
        duplicates = 0
        try:
            for raw_record in payload:
                if type(raw_record) is not dict or set(raw_record) != {"data", "valor"}:
                    raise ExternalObservationProviderError(
                        ProviderErrorCode.INVALID_SCHEMA,
                        "An SGS record does not match the exact data/valor schema.",
                    )
                raw_date = raw_record["data"]
                raw_value = raw_record["valor"]
                if type(raw_date) is not str or type(raw_value) is not str:
                    raise ExternalObservationProviderError(
                        ProviderErrorCode.INVALID_SCHEMA,
                        "SGS data and valor fields must be lexical strings.",
                    )
                economic_date = self._parse_sgs_date(raw_date)
                if not response.interval.start <= economic_date <= response.interval.end:
                    raise ExternalObservationProviderError(
                        ProviderErrorCode.INVALID_DATE,
                        "An SGS observation date lies outside its requested chunk.",
                    )
                if economic_date < definition.earliest_normalized_date:
                    raise ExternalObservationProviderError(
                        ProviderErrorCode.INVALID_DATE,
                        "An SGS observation precedes the registry-normalized floor.",
                    )
                if definition.frequency is Frequency.DAILY:
                    period_start = economic_date
                    period_end = economic_date
                else:
                    period_start = economic_date.replace(day=1)
                    period_end = economic_date.replace(
                        day=calendar.monthrange(economic_date.year, economic_date.month)[1]
                    )
                observation = normalize_external_observation(
                    {
                        "provider": definition.provider.value,
                        "series_id": definition.series_id,
                        "reference_period_start": period_start.isoformat(),
                        "reference_period_end": period_end.isoformat(),
                        "semantic_class": definition.semantic_class.value,
                        "frequency": definition.frequency.value,
                        "value_text": raw_value,
                        "value_scale": definition.normalization_scale,
                        "unit": definition.unit.value,
                        "currency": definition.currency,
                        "scope": definition.scope.value,
                    },
                    retrieved_at=response.retrieved_at,
                )
                period_key = (period_start, period_end)
                existing = normalized_by_period.get(period_key)
                if existing is None:
                    normalized_by_period[period_key] = observation
                elif existing.content.as_payload_v1() == observation.content.as_payload_v1():
                    duplicates += 1
                else:
                    raise ExternalObservationProviderError(
                        ProviderErrorCode.CONFLICTING_DUPLICATE,
                        "The SGS response contains conflicting values for one period.",
                    )
        except ExternalObservationProviderError as exc:
            return self._received_failure(response, exc.code)
        except DecimalNormalizationError:
            return self._received_failure(response, ProviderErrorCode.INVALID_VALUE)
        except ReferencePeriodError:
            return self._received_failure(response, ProviderErrorCode.INVALID_DATE)
        except ExternalContextDomainError:
            return self._received_failure(
                response,
                ProviderErrorCode.CERTIFICATION_REJECTED,
            )
        except (TypeError, ValueError):
            return self._received_failure(
                response,
                ProviderErrorCode.CERTIFICATION_REJECTED,
            )

        observations = tuple(
            normalized_by_period[key]
            for key in sorted(normalized_by_period)
        )
        is_empty = not observations
        return ProviderChunkResult(
            registry_key=response.registry_key,
            interval=response.interval,
            status=(ProviderChunkStatus.EMPTY if is_empty else ProviderChunkStatus.SUCCESS),
            response_received=True,
            payload_validated=True,
            normalization_completed=True,
            observations=observations,
            empty_response=is_empty,
            duplicate_records=duplicates,
            http_attempts=response.attempts,
            retrieved_at=response.retrieved_at,
            http_status=response.http_status,
            error_code=None,
            terminal_failure=False,
        )

    @staticmethod
    def _parse_sgs_date(raw_date: str) -> date:
        if _SGS_DATE_PATTERN.fullmatch(raw_date) is None:
            raise ExternalObservationProviderError(
                ProviderErrorCode.INVALID_DATE,
                "SGS dates must use strict dd/MM/yyyy text.",
            )
        try:
            parsed = datetime.strptime(raw_date, "%d/%m/%Y").date()
        except ValueError as exc:
            raise ExternalObservationProviderError(
                ProviderErrorCode.INVALID_DATE,
                "The SGS record contains a non-existent civil date.",
            ) from exc
        if parsed.strftime("%d/%m/%Y") != raw_date:
            raise ExternalObservationProviderError(
                ProviderErrorCode.INVALID_DATE,
                "The SGS date is not canonical dd/MM/yyyy text.",
            )
        return parsed

    @staticmethod
    def _received_failure(
        response: BCBSGSHTTPResponse,
        error_code: ProviderErrorCode,
    ) -> ProviderChunkResult:
        return ProviderChunkResult(
            registry_key=response.registry_key,
            interval=response.interval,
            status=ProviderChunkStatus.FAILED,
            response_received=True,
            payload_validated=False,
            normalization_completed=False,
            observations=(),
            empty_response=False,
            duplicate_records=0,
            http_attempts=response.attempts,
            retrieved_at=response.retrieved_at,
            http_status=response.http_status,
            error_code=error_code,
            terminal_failure=True,
        )

    @staticmethod
    def _incomplete_result(
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
            duplicate_records=0,
            http_attempts=0,
            error_code=ProviderErrorCode.ACQUISITION_BUDGET_EXHAUSTED,
            terminal_failure=False,
        )

    @staticmethod
    def _derive_status(
        results: tuple[ProviderChunkResult, ...],
        observations: tuple[ExternalObservation, ...],
    ) -> ProviderAcquisitionStatus:
        complete_count = sum(result.is_complete for result in results)
        if complete_count == len(results):
            return (
                ProviderAcquisitionStatus.SUCCESS
                if observations
                else ProviderAcquisitionStatus.EMPTY
            )
        if complete_count:
            return ProviderAcquisitionStatus.PARTIAL
        return ProviderAcquisitionStatus.FAILED
