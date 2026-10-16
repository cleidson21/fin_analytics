"""Typed, payload-minimized telemetry metrics for the R4-C boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TypeAlias

from backend.application.ai_runtime.audit import ToolExecutionOutcome
from backend.application.ai_runtime.contracts import (
    ExecutionMode,
    normalize_utc,
    require_identifier,
    require_non_empty_text,
    require_non_negative_decimal,
    require_non_negative_int,
)
from backend.application.ai_runtime.errors import AIErrorCode


TELEMETRY_METRIC_CONTRACT_VERSION = "1.0"


class RoutingOutcome(str, Enum):
    SELECTED = "SELECTED"
    FALLBACK_SELECTED = "FALLBACK_SELECTED"
    NO_ELIGIBLE_ROUTE = "NO_ELIGIBLE_ROUTE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class LatencyMetric:
    total_ms: int
    first_token_ms: int | None = None

    def __post_init__(self) -> None:
        require_non_negative_int(self.total_ms, "total_ms")
        if self.first_token_ms is not None:
            require_non_negative_int(self.first_token_ms, "first_token_ms")
            if self.first_token_ms > self.total_ms:
                raise ValueError("first_token_ms cannot exceed total_ms.")


@dataclass(frozen=True)
class TokenUsageMetric:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def __post_init__(self) -> None:
        values = (self.input_tokens, self.output_tokens, self.total_tokens)
        if all(value is None for value in values):
            raise ValueError("token usage metric requires at least one known value.")
        for field_name in ("input_tokens", "output_tokens", "total_tokens"):
            value = getattr(self, field_name)
            if value is not None:
                require_non_negative_int(value, field_name)


@dataclass(frozen=True)
class CostMetric:
    amount: Decimal
    currency: str
    estimated: bool

    def __post_init__(self) -> None:
        require_non_negative_decimal(self.amount, "amount")
        if type(self.currency) is not str or len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError("currency must be a three-letter uppercase code.")
        if type(self.estimated) is not bool:
            raise TypeError("estimated must be a strict boolean.")


@dataclass(frozen=True)
class ProviderModelMetric:
    provider_id: str
    model_id: str
    model_version: str | None = None
    model_digest: str | None = None

    def __post_init__(self) -> None:
        require_identifier(self.provider_id, "provider_id")
        require_identifier(self.model_id, "model_id")
        if self.model_version is not None:
            require_non_empty_text(self.model_version, "model_version", limit=128)
        if self.model_digest is not None:
            require_non_empty_text(self.model_digest, "model_digest", limit=256)


@dataclass(frozen=True)
class ErrorMetric:
    code: AIErrorCode
    transient: bool

    def __post_init__(self) -> None:
        if not isinstance(self.code, AIErrorCode):
            raise TypeError("code must be AIErrorCode.")
        if type(self.transient) is not bool:
            raise TypeError("transient must be a strict boolean.")


@dataclass(frozen=True)
class RetryMetric:
    total_attempts: int

    def __post_init__(self) -> None:
        if type(self.total_attempts) is not int or self.total_attempts < 1:
            raise ValueError("total_attempts must be a positive strict integer.")


@dataclass(frozen=True)
class RoutingFallbackMetric:
    execution_mode: ExecutionMode
    outcome: RoutingOutcome
    fallback_used: bool
    from_provider_id: str | None = None
    reason_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.execution_mode, ExecutionMode):
            raise TypeError("execution_mode must be ExecutionMode.")
        if not isinstance(self.outcome, RoutingOutcome):
            raise TypeError("outcome must be RoutingOutcome.")
        if type(self.fallback_used) is not bool:
            raise TypeError("fallback_used must be a strict boolean.")
        if self.outcome is RoutingOutcome.FALLBACK_SELECTED and not self.fallback_used:
            raise ValueError("fallback routing outcome requires fallback_used.")
        if self.fallback_used and self.outcome is not RoutingOutcome.FALLBACK_SELECTED:
            raise ValueError("fallback_used requires FALLBACK_SELECTED outcome.")
        if self.fallback_used:
            if self.from_provider_id is None or self.reason_code is None:
                raise ValueError("used fallback requires provider and reason metadata.")
            require_identifier(self.from_provider_id, "from_provider_id")
            require_identifier(self.reason_code, "reason_code")
        elif self.from_provider_id is not None or self.reason_code is not None:
            raise ValueError("unused fallback cannot include provider or reason metadata.")


@dataclass(frozen=True)
class ToolExecutionMetric:
    tool_id: str
    outcome: ToolExecutionOutcome
    latency_ms: int | None = None
    error_code: AIErrorCode | None = None

    def __post_init__(self) -> None:
        require_identifier(self.tool_id, "tool_id")
        if not isinstance(self.outcome, ToolExecutionOutcome):
            raise TypeError("outcome must be ToolExecutionOutcome.")
        if self.latency_ms is not None:
            require_non_negative_int(self.latency_ms, "latency_ms")
        if self.error_code is not None and not isinstance(self.error_code, AIErrorCode):
            raise TypeError("error_code must be AIErrorCode or None.")
        if self.outcome is ToolExecutionOutcome.SUCCEEDED and self.error_code is not None:
            raise ValueError("a successful tool metric cannot include an error code.")


TelemetryPayload: TypeAlias = (
    LatencyMetric
    | TokenUsageMetric
    | CostMetric
    | ProviderModelMetric
    | ErrorMetric
    | RetryMetric
    | RoutingFallbackMetric
    | ToolExecutionMetric
)


@dataclass(frozen=True, kw_only=True)
class AITelemetryMetric:
    metric_id: str
    request_id: str
    correlation_id: str
    observed_at: datetime
    payload: TelemetryPayload
    contract_version: str = TELEMETRY_METRIC_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.contract_version != TELEMETRY_METRIC_CONTRACT_VERSION:
            raise ValueError("unsupported telemetry metric contract version.")
        for field_name in ("metric_id", "request_id", "correlation_id"):
            require_identifier(getattr(self, field_name), field_name)
        object.__setattr__(
            self,
            "observed_at",
            normalize_utc(self.observed_at, "observed_at"),
        )
        if not isinstance(
            self.payload,
            (
                LatencyMetric,
                TokenUsageMetric,
                CostMetric,
                ProviderModelMetric,
                ErrorMetric,
                RetryMetric,
                RoutingFallbackMetric,
                ToolExecutionMetric,
            ),
        ):
            raise TypeError("payload must be an approved telemetry payload.")
