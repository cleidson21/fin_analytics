"""Safe structured error taxonomy for provider-neutral AI operations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.application.ai_runtime.contracts import require_identifier
from backend.domain.exceptions.base import FINAnalyticsError


class AIErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    PRIVACY_POLICY_DENIED = "PRIVACY_POLICY_DENIED"
    CAPABILITY_UNSUPPORTED = "CAPABILITY_UNSUPPORTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    RATE_LIMITED = "RATE_LIMITED"
    PROVIDER_OVERLOADED = "PROVIDER_OVERLOADED"
    TIMEOUT = "TIMEOUT"
    OUTPUT_SCHEMA_INVALID = "OUTPUT_SCHEMA_INVALID"
    OUTPUT_SOURCE_INVALID = "OUTPUT_SOURCE_INVALID"
    TOOL_DENIED = "TOOL_DENIED"
    TOKEN_BUDGET_EXCEEDED = "TOKEN_BUDGET_EXCEEDED"
    COST_BUDGET_EXCEEDED = "COST_BUDGET_EXCEEDED"
    CANCELLED = "CANCELLED"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"


_SAFE_MESSAGES = {
    AIErrorCode.INVALID_REQUEST: "The AI request contract is invalid.",
    AIErrorCode.AUTHORIZATION_DENIED: "The AI operation is not authorized.",
    AIErrorCode.PRIVACY_POLICY_DENIED: "The AI operation is not allowed by privacy policy.",
    AIErrorCode.CAPABILITY_UNSUPPORTED: "The required AI capability is unavailable.",
    AIErrorCode.PROVIDER_UNAVAILABLE: "The selected AI provider is unavailable.",
    AIErrorCode.MODEL_UNAVAILABLE: "The selected AI model is unavailable.",
    AIErrorCode.QUOTA_EXHAUSTED: "The AI provider quota is exhausted.",
    AIErrorCode.RATE_LIMITED: "The AI provider rate limit was reached.",
    AIErrorCode.PROVIDER_OVERLOADED: "The AI provider is overloaded.",
    AIErrorCode.TIMEOUT: "The AI operation exceeded its deadline.",
    AIErrorCode.OUTPUT_SCHEMA_INVALID: "The AI output failed structural validation.",
    AIErrorCode.OUTPUT_SOURCE_INVALID: "The AI output references an unauthorized source.",
    AIErrorCode.TOOL_DENIED: "The AI output references an unauthorized tool.",
    AIErrorCode.TOKEN_BUDGET_EXCEEDED: "The AI operation exceeded its token budget.",
    AIErrorCode.COST_BUDGET_EXCEEDED: "The AI operation exceeded its cost budget.",
    AIErrorCode.CANCELLED: "The AI operation was cancelled.",
    AIErrorCode.INTERNAL_FAILURE: "The AI operation failed safely.",
}


@dataclass(frozen=True)
class AIErrorMetadata:
    request_id: str | None = None
    provider_id: str | None = None
    model_id: str | None = None
    field: str | None = None
    transient: bool = False
    retry_after_seconds: int | None = None

    def __post_init__(self) -> None:
        for field_name in ("request_id", "provider_id", "model_id", "field"):
            value = getattr(self, field_name)
            if value is not None:
                require_identifier(value, field_name)
        if type(self.transient) is not bool:
            raise TypeError("transient must be a strict boolean.")
        if self.retry_after_seconds is not None and (
            type(self.retry_after_seconds) is not int or self.retry_after_seconds < 0
        ):
            raise ValueError("retry_after_seconds must be non-negative or None.")


class AIContractError(FINAnalyticsError):
    """Stable error with allowlisted metadata and no raw provider payload."""

    def __init__(
        self,
        code: AIErrorCode,
        *,
        metadata: AIErrorMetadata | None = None,
    ) -> None:
        if not isinstance(code, AIErrorCode):
            raise TypeError("code must be AIErrorCode.")
        if metadata is not None and not isinstance(metadata, AIErrorMetadata):
            raise TypeError("metadata must be AIErrorMetadata or None.")
        super().__init__(_SAFE_MESSAGES[code])
        self.code = code
        self.metadata = metadata or AIErrorMetadata()
