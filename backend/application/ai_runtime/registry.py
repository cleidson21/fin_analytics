"""Immutable, instance-scoped capability registries for R4-A."""

from __future__ import annotations

from types import MappingProxyType
from typing import Iterable, Iterator, Mapping

from backend.application.ai_runtime.contracts import (
    ModelCapabilities,
    ProviderCapabilities,
)
from backend.application.ai_runtime.errors import (
    AIContractError,
    AIErrorCode,
    AIErrorMetadata,
)


class ProviderCapabilityRegistry:
    """Read-only snapshot; no mutable process-global provider registry."""

    def __init__(self, providers: Iterable[ProviderCapabilities]) -> None:
        snapshot: dict[str, ProviderCapabilities] = {}
        for provider in providers:
            if not isinstance(provider, ProviderCapabilities):
                raise TypeError("providers must contain ProviderCapabilities values.")
            provider_id = provider.identity.provider_id
            if provider_id in snapshot:
                raise ValueError(f"duplicate provider_id: {provider_id}")
            snapshot[provider_id] = provider
        self._providers: Mapping[str, ProviderCapabilities] = MappingProxyType(snapshot)

    def __iter__(self) -> Iterator[ProviderCapabilities]:
        return iter(self._providers.values())

    def __len__(self) -> int:
        return len(self._providers)

    def get(self, provider_id: str) -> ProviderCapabilities | None:
        return self._providers.get(provider_id)

    def require(self, provider_id: str) -> ProviderCapabilities:
        provider = self.get(provider_id)
        if provider is None:
            raise AIContractError(
                AIErrorCode.PROVIDER_UNAVAILABLE,
                metadata=AIErrorMetadata(provider_id=provider_id),
            )
        return provider

    @property
    def providers(self) -> Mapping[str, ProviderCapabilities]:
        return self._providers


class ModelCapabilityRegistry:
    """Read-only exact-model snapshot with no default or alias resolution."""

    def __init__(self, models: Iterable[ModelCapabilities]) -> None:
        snapshot: dict[tuple[str, str], ModelCapabilities] = {}
        for model in models:
            if not isinstance(model, ModelCapabilities):
                raise TypeError("models must contain ModelCapabilities values.")
            key = (model.provider_id, model.model_id)
            if key in snapshot:
                raise ValueError(
                    f"duplicate provider/model identity: {model.provider_id}/{model.model_id}"
                )
            snapshot[key] = model
        self._models: Mapping[tuple[str, str], ModelCapabilities] = MappingProxyType(
            snapshot
        )

    def __iter__(self) -> Iterator[ModelCapabilities]:
        return iter(self._models.values())

    def __len__(self) -> int:
        return len(self._models)

    def get(self, provider_id: str, model_id: str) -> ModelCapabilities | None:
        return self._models.get((provider_id, model_id))

    def require(self, provider_id: str, model_id: str) -> ModelCapabilities:
        model = self.get(provider_id, model_id)
        if model is None:
            raise AIContractError(
                AIErrorCode.MODEL_UNAVAILABLE,
                metadata=AIErrorMetadata(
                    provider_id=provider_id,
                    model_id=model_id,
                ),
            )
        return model

    @property
    def models(self) -> Mapping[tuple[str, str], ModelCapabilities]:
        return self._models
