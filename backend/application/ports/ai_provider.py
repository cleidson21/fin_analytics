"""SDK-free asynchronous provider port for the R4 AI runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.application.ai_runtime.contracts import (
    AIProviderHealth,
    AIProviderResult,
    AIRequest,
    CancellationResult,
    ModelCapabilities,
    ProviderIdentity,
)


class AIProvider(ABC):
    """Provider-neutral boundary; adapters own SDK and transport details."""

    @property
    @abstractmethod
    def identity(self) -> ProviderIdentity:
        """Return the stable identity advertised by this adapter."""
        ...

    @abstractmethod
    async def discover_models(self) -> tuple[ModelCapabilities, ...]:
        """Return an immutable exact-model capability snapshot."""
        ...

    @abstractmethod
    async def probe_health(self, model_id: str | None = None) -> AIProviderHealth:
        """Return bounded health evidence without generating model output."""
        ...

    @abstractmethod
    async def generate(self, request: AIRequest, *, model_id: str) -> AIProviderResult:
        """Generate an untrusted adapter result for canonical validation."""
        ...

    @abstractmethod
    async def cancel(self, request_id: str) -> CancellationResult:
        """Cancel a request when supported, or report NOT_SUPPORTED explicitly."""
        ...

    @abstractmethod
    async def aclose(self) -> None:
        """Release adapter resources idempotently."""
        ...
