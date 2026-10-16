"""Deterministic no-I/O AI provider used only for R4-A contract verification."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Mapping

from backend.application.ai_runtime.contracts import (
    AIProviderHealth,
    AIProviderResult,
    AIRequest,
    CancellationResult,
    CanonicalValue,
    CostUsage,
    FallbackMetadata,
    FinishReason,
    LatencyUsage,
    ModelCapabilities,
    ProviderHealthStatus,
    ProviderIdentity,
    RetryMetadata,
    TokenUsage,
    ToolCallMetadata,
)
from backend.application.ai_runtime.errors import (
    AIContractError,
    AIErrorCode,
    AIErrorMetadata,
)
from backend.application.ports.ai_provider import AIProvider


class FakeProviderMode(str, Enum):
    VALID = "VALID"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    TIMEOUT = "TIMEOUT"
    UNAVAILABLE = "UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    CANCELLED = "CANCELLED"


class DeterministicFakeAIProvider(AIProvider):
    """Synthetic adapter with no SDK, socket, filesystem, environment, or database I/O."""

    def __init__(
        self,
        *,
        identity: ProviderIdentity,
        models: tuple[ModelCapabilities, ...],
        output: Mapping[str, CanonicalValue],
        source_reference_ids: tuple[str, ...] = (),
        mode: FakeProviderMode = FakeProviderMode.VALID,
        token_usage: TokenUsage | None = None,
        cost: CostUsage | None = None,
        tool_calls: tuple[ToolCallMetadata, ...] = (),
        completed_at: datetime | None = None,
        supports_cancellation: bool = True,
    ) -> None:
        if not isinstance(identity, ProviderIdentity):
            raise TypeError("identity must be ProviderIdentity.")
        if type(models) is not tuple or any(
            not isinstance(model, ModelCapabilities) for model in models
        ):
            raise TypeError("models must be a tuple of ModelCapabilities values.")
        if any(model.provider_id != identity.provider_id for model in models):
            raise ValueError("all fake models must belong to the fake provider.")
        if not isinstance(mode, FakeProviderMode):
            raise TypeError("mode must be FakeProviderMode.")
        if type(supports_cancellation) is not bool:
            raise TypeError("supports_cancellation must be a strict boolean.")
        self._identity = identity
        self._models = models
        self._output = output
        self._source_reference_ids = source_reference_ids
        self._mode = mode
        self._token_usage = token_usage or TokenUsage()
        self._cost = cost or CostUsage()
        self._tool_calls = tool_calls
        self._completed_at = completed_at or datetime(2030, 1, 1, tzinfo=timezone.utc)
        self._supports_cancellation = supports_cancellation
        self._cancelled_request_ids: set[str] = set()
        self._completed_request_ids: set[str] = set()
        self._closed = False
        self.generate_calls = 0

    @property
    def identity(self) -> ProviderIdentity:
        return self._identity

    async def discover_models(self) -> tuple[ModelCapabilities, ...]:
        return self._models

    async def probe_health(self, model_id: str | None = None) -> AIProviderHealth:
        status = (
            ProviderHealthStatus.UNAVAILABLE
            if self._closed or self._mode is FakeProviderMode.UNAVAILABLE
            else ProviderHealthStatus.HEALTHY
        )
        return AIProviderHealth(
            provider_id=self.identity.provider_id,
            model_id=model_id,
            status=status,
            checked_at=self._completed_at,
            latency_ms=0,
            reason_code=("FAKE_CLOSED" if self._closed else None),
        )

    async def generate(self, request: AIRequest, *, model_id: str) -> AIProviderResult:
        if not isinstance(request, AIRequest):
            raise TypeError("request must be AIRequest.")
        self.generate_calls += 1
        metadata = AIErrorMetadata(
            request_id=request.request_id,
            provider_id=self.identity.provider_id,
            model_id=model_id,
        )
        if self._closed:
            raise AIContractError(AIErrorCode.PROVIDER_UNAVAILABLE, metadata=metadata)
        if request.request_id in self._cancelled_request_ids:
            raise AIContractError(AIErrorCode.CANCELLED, metadata=metadata)
        if self._mode is FakeProviderMode.TIMEOUT:
            raise AIContractError(
                AIErrorCode.TIMEOUT,
                metadata=AIErrorMetadata(
                    request_id=request.request_id,
                    provider_id=self.identity.provider_id,
                    model_id=model_id,
                    transient=True,
                ),
            )
        if self._mode is FakeProviderMode.UNAVAILABLE:
            raise AIContractError(
                AIErrorCode.PROVIDER_UNAVAILABLE,
                metadata=AIErrorMetadata(
                    request_id=request.request_id,
                    provider_id=self.identity.provider_id,
                    model_id=model_id,
                    transient=True,
                ),
            )
        if self._mode is FakeProviderMode.RATE_LIMITED:
            raise AIContractError(
                AIErrorCode.RATE_LIMITED,
                metadata=AIErrorMetadata(
                    request_id=request.request_id,
                    provider_id=self.identity.provider_id,
                    model_id=model_id,
                    transient=True,
                    retry_after_seconds=1,
                ),
            )
        if self._mode is FakeProviderMode.CANCELLED:
            raise AIContractError(AIErrorCode.CANCELLED, metadata=metadata)

        model = next(
            (candidate for candidate in self._models if candidate.model_id == model_id),
            None,
        )
        if model is None:
            raise AIContractError(AIErrorCode.MODEL_UNAVAILABLE, metadata=metadata)

        output: Mapping[str, CanonicalValue]
        if self._mode is FakeProviderMode.INVALID_SCHEMA:
            output = {"unexpected": "synthetic-invalid-output"}
        else:
            output = self._output
        self._completed_request_ids.add(request.request_id)
        return AIProviderResult(
            provider_id=self.identity.provider_id,
            model_id=model_id,
            model_version=model.model_version,
            model_digest=model.model_digest,
            structured_output=output,
            source_reference_ids=self._source_reference_ids,
            tool_calls=self._tool_calls,
            token_usage=self._token_usage,
            latency=LatencyUsage(total_ms=0, first_token_ms=0),
            cost=self._cost,
            finish_reason=FinishReason.COMPLETED,
            retry=RetryMetadata(total_attempts=1),
            fallback=FallbackMetadata(),
            warnings=(),
            completed_at=self._completed_at,
        )

    async def cancel(self, request_id: str) -> CancellationResult:
        if not self._supports_cancellation:
            return CancellationResult.NOT_SUPPORTED
        if request_id in self._completed_request_ids:
            return CancellationResult.ALREADY_COMPLETED
        self._cancelled_request_ids.add(request_id)
        return CancellationResult.CANCELLED

    async def aclose(self) -> None:
        self._closed = True
