"""Internal R4-A proof surface over an explicitly supplied AI provider."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from backend.application.ai_runtime.contracts import (
    AIRequest,
    AIResponse,
    ExecutionMode,
    LifecycleStatus,
    ProviderLocality,
    require_identifier,
)
from backend.application.ai_runtime.errors import (
    AIContractError,
    AIErrorCode,
    AIErrorMetadata,
)
from backend.application.ai_runtime.registry import (
    ModelCapabilityRegistry,
    ProviderCapabilityRegistry,
)
from backend.application.ai_runtime.validation import CanonicalOutputValidator
from backend.application.ports.ai_provider import AIProvider


class ProviderNeutralAIService:
    """Validates and invokes one caller-selected provider; this is not a router."""

    def __init__(
        self,
        provider_registry: ProviderCapabilityRegistry,
        model_registry: ModelCapabilityRegistry,
        *,
        validator: CanonicalOutputValidator | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(provider_registry, ProviderCapabilityRegistry):
            raise TypeError("provider_registry must be ProviderCapabilityRegistry.")
        if not isinstance(model_registry, ModelCapabilityRegistry):
            raise TypeError("model_registry must be ModelCapabilityRegistry.")
        if validator is not None and not isinstance(validator, CanonicalOutputValidator):
            raise TypeError("validator must be CanonicalOutputValidator or None.")
        self._providers = provider_registry
        self._models = model_registry
        self._validator = validator or CanonicalOutputValidator()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    async def generate(
        self,
        request: AIRequest,
        *,
        provider: AIProvider,
        model_id: str,
    ) -> AIResponse:
        if not isinstance(request, AIRequest):
            raise TypeError("request must be AIRequest.")
        if not isinstance(provider, AIProvider):
            raise TypeError("provider must implement AIProvider.")

        provider_id = provider.identity.provider_id
        try:
            require_identifier(model_id, "model_id")
        except (TypeError, ValueError):
            raise AIContractError(
                AIErrorCode.INVALID_REQUEST,
                metadata=AIErrorMetadata(
                    request_id=request.request_id,
                    provider_id=provider_id,
                    field="model_id",
                ),
            ) from None
        metadata = AIErrorMetadata(
            request_id=request.request_id,
            provider_id=provider_id,
            model_id=model_id,
        )
        provider_contract = self._providers.require(provider_id)
        model_contract = self._models.require(provider_id, model_id)

        if provider.identity != provider_contract.identity:
            raise AIContractError(AIErrorCode.INVALID_REQUEST, metadata=metadata)
        if (
            provider_contract.lifecycle is not LifecycleStatus.AVAILABLE
            or model_contract.lifecycle is not LifecycleStatus.AVAILABLE
        ):
            code = (
                AIErrorCode.PROVIDER_UNAVAILABLE
                if provider_contract.lifecycle is not LifecycleStatus.AVAILABLE
                else AIErrorCode.MODEL_UNAVAILABLE
            )
            raise AIContractError(code, metadata=metadata)
        if model_contract.locality is not provider_contract.identity.locality:
            raise AIContractError(AIErrorCode.INVALID_REQUEST, metadata=metadata)

        required = request.required_capabilities
        if not required.issubset(provider_contract.capabilities) or not required.issubset(
            model_contract.capabilities
        ):
            raise AIContractError(AIErrorCode.CAPABILITY_UNSUPPORTED, metadata=metadata)
        if request.privacy_classification not in provider_contract.permitted_privacy:
            raise AIContractError(AIErrorCode.PRIVACY_POLICY_DENIED, metadata=metadata)

        locality = provider_contract.identity.locality
        if request.execution_mode is ExecutionMode.LOCAL_ONLY and locality is not ProviderLocality.LOCAL:
            raise AIContractError(AIErrorCode.PRIVACY_POLICY_DENIED, metadata=metadata)
        if request.execution_mode is ExecutionMode.REMOTE_ONLY and locality is not ProviderLocality.REMOTE:
            raise AIContractError(AIErrorCode.PROVIDER_UNAVAILABLE, metadata=metadata)
        if locality is ProviderLocality.REMOTE and not request.remote_processing_consent.granted:
            raise AIContractError(AIErrorCode.PRIVACY_POLICY_DENIED, metadata=metadata)

        now = self._clock()
        if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
            raise TypeError("clock must return a timezone-aware datetime.")
        if now.astimezone(timezone.utc) >= request.deadline_at:
            raise AIContractError(AIErrorCode.TIMEOUT, metadata=metadata)

        result = await provider.generate(request, model_id=model_id)
        return self._validator.validate(
            request,
            result,
            expected_provider_id=provider_id,
            expected_model_id=model_id,
        )
