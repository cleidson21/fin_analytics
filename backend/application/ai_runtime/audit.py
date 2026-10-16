"""Minimized immutable audit contracts for the R4-C AI runtime boundary."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backend.application.ai_runtime.contracts import (
    AIRequest,
    AIResponse,
    AIWarningCode,
    CostUsage,
    ExecutionMode,
    FinishReason,
    LatencyUsage,
    PolicyVersion,
    ServerUserScope,
    TokenUsage,
    ValidationSummary,
    normalize_utc,
    require_identifier,
    require_non_empty_text,
    require_non_negative_int,
)
from backend.application.ai_runtime.errors import (
    AIContractError,
    AIErrorCode,
)


AUDIT_EVENT_CONTRACT_VERSION = "1.0"
_PSEUDONYM_DOMAIN = b"finanalytics.ai-audit-scope.v1\x00"


class AuditOutcome(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class DegradationState(str, Enum):
    DEGRADED = "DEGRADED"
    NOT_DEGRADED = "NOT_DEGRADED"
    UNKNOWN = "UNKNOWN"


class ToolExecutionOutcome(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    DENIED = "DENIED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PseudonymousScopeIdentity:
    """Non-reversible technical scope reference; never a raw user identifier."""

    scope_id: str
    key_id: str
    scheme: str = "HMAC-SHA256"

    def __post_init__(self) -> None:
        require_identifier(self.scope_id, "scope_id")
        require_identifier(self.key_id, "key_id")
        if self.scheme != "HMAC-SHA256":
            raise ValueError("unsupported scope pseudonymization scheme.")


def pseudonymize_server_user_scope(
    scope: ServerUserScope,
    *,
    key: bytes,
    key_id: str,
) -> PseudonymousScopeIdentity:
    """Create a stable scoped pseudonym without retaining the key or raw scope."""

    if not isinstance(scope, ServerUserScope):
        raise TypeError("scope must be ServerUserScope.")
    if type(key) is not bytes or len(key) < 32:
        raise ValueError("pseudonymization key must contain at least 32 bytes.")
    require_identifier(key_id, "key_id")
    material = (
        _PSEUDONYM_DOMAIN
        + scope.subject_id.encode("utf-8")
        + b"\x00"
        + scope.authorization_context_id.encode("utf-8")
    )
    digest = hmac.new(key, material, hashlib.sha256).hexdigest()
    return PseudonymousScopeIdentity(
        scope_id=f"scope.hmac-sha256.{digest}",
        key_id=key_id,
    )


@dataclass(frozen=True)
class AuditToolExecution:
    call_id: str
    tool_id: str
    outcome: ToolExecutionOutcome
    latency_ms: int | None = None
    error_code: AIErrorCode | None = None

    def __post_init__(self) -> None:
        require_identifier(self.call_id, "call_id")
        require_identifier(self.tool_id, "tool_id")
        if not isinstance(self.outcome, ToolExecutionOutcome):
            raise TypeError("outcome must be ToolExecutionOutcome.")
        if self.latency_ms is not None:
            require_non_negative_int(self.latency_ms, "latency_ms")
        if self.error_code is not None and not isinstance(self.error_code, AIErrorCode):
            raise TypeError("error_code must be AIErrorCode or None.")
        if self.outcome is ToolExecutionOutcome.SUCCEEDED and self.error_code is not None:
            raise ValueError("a successful tool execution cannot include an error code.")


@dataclass(frozen=True)
class AuditError:
    code: AIErrorCode
    transient: bool

    def __post_init__(self) -> None:
        if not isinstance(self.code, AIErrorCode):
            raise TypeError("code must be AIErrorCode.")
        if type(self.transient) is not bool:
            raise TypeError("transient must be a strict boolean.")


@dataclass(frozen=True)
class AuditFallback:
    from_provider_id: str
    reason_code: str

    def __post_init__(self) -> None:
        require_identifier(self.from_provider_id, "from_provider_id")
        require_identifier(self.reason_code, "reason_code")


@dataclass(frozen=True, kw_only=True)
class AIAuditEvent:
    """Allowlisted metadata only; prompts, responses, context, and tool args cannot fit."""

    event_id: str
    request_id: str
    correlation_id: str
    scope: PseudonymousScopeIdentity
    task_kind: str
    task_version: str
    execution_mode: ExecutionMode
    policy_versions: tuple[PolicyVersion, ...]
    output_schema_id: str
    output_schema_version: str
    authorized_tool_ids: tuple[str, ...]
    tool_executions: tuple[AuditToolExecution, ...]
    technical_reference_ids: tuple[str, ...]
    started_at: datetime
    completed_at: datetime
    latency: LatencyUsage
    total_attempts: int | None
    outcome: AuditOutcome
    degradation: DegradationState
    provider_id: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    model_digest: str | None = None
    token_usage: TokenUsage | None = None
    cost: CostUsage | None = None
    error: AuditError | None = None
    fallback: AuditFallback | None = None
    validation: ValidationSummary | None = None
    contract_version: str = AUDIT_EVENT_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.contract_version != AUDIT_EVENT_CONTRACT_VERSION:
            raise ValueError("unsupported audit event contract version.")
        for field_name in ("event_id", "request_id", "correlation_id", "task_kind"):
            require_identifier(getattr(self, field_name), field_name)
        require_non_empty_text(self.task_version, "task_version", limit=64)
        if not isinstance(self.scope, PseudonymousScopeIdentity):
            raise TypeError("scope must be PseudonymousScopeIdentity.")
        if not isinstance(self.execution_mode, ExecutionMode):
            raise TypeError("execution_mode must be ExecutionMode.")
        if type(self.policy_versions) is not tuple or any(
            not isinstance(item, PolicyVersion) for item in self.policy_versions
        ):
            raise TypeError("policy_versions must contain PolicyVersion values.")
        if not self.policy_versions:
            raise ValueError("at least one policy version is required.")
        if len({item.name for item in self.policy_versions}) != len(self.policy_versions):
            raise ValueError("policy version names must be unique.")
        require_identifier(self.output_schema_id, "output_schema_id")
        require_non_empty_text(
            self.output_schema_version,
            "output_schema_version",
            limit=64,
        )
        self._validate_identifier_tuple(self.authorized_tool_ids, "authorized_tool_ids")
        self._validate_identifier_tuple(
            self.technical_reference_ids,
            "technical_reference_ids",
        )
        if tuple(sorted(self.authorized_tool_ids)) != self.authorized_tool_ids:
            raise ValueError("authorized_tool_ids must use canonical sorted order.")
        if tuple(sorted(self.technical_reference_ids)) != self.technical_reference_ids:
            raise ValueError("technical_reference_ids must use canonical sorted order.")
        if type(self.tool_executions) is not tuple or any(
            not isinstance(item, AuditToolExecution) for item in self.tool_executions
        ):
            raise TypeError("tool_executions must contain AuditToolExecution values.")
        call_ids = tuple(item.call_id for item in self.tool_executions)
        if len(set(call_ids)) != len(call_ids):
            raise ValueError("tool execution call IDs must be unique.")
        allowed = set(self.authorized_tool_ids)
        if any(item.tool_id not in allowed for item in self.tool_executions):
            raise ValueError("tool execution is not present in the request allowlist.")
        object.__setattr__(self, "started_at", normalize_utc(self.started_at, "started_at"))
        object.__setattr__(
            self,
            "completed_at",
            normalize_utc(self.completed_at, "completed_at"),
        )
        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at.")
        if not isinstance(self.latency, LatencyUsage):
            raise TypeError("latency must be LatencyUsage.")
        if self.total_attempts is not None:
            require_non_negative_int(self.total_attempts, "total_attempts")
        if not isinstance(self.outcome, AuditOutcome):
            raise TypeError("outcome must be AuditOutcome.")
        if not isinstance(self.degradation, DegradationState):
            raise TypeError("degradation must be DegradationState.")
        self._validate_provider_identity()
        if self.token_usage is not None and not isinstance(self.token_usage, TokenUsage):
            raise TypeError("token_usage must be TokenUsage or None.")
        if self.cost is not None:
            if not isinstance(self.cost, CostUsage) or not self.cost.is_known:
                raise ValueError("cost must be known CostUsage or None.")
        if self.error is not None and not isinstance(self.error, AuditError):
            raise TypeError("error must be AuditError or None.")
        if self.outcome is AuditOutcome.FAILED and self.error is None:
            raise ValueError("failed audit outcomes require a typed error.")
        if self.outcome is AuditOutcome.SUCCEEDED and self.error is not None:
            raise ValueError("successful audit outcomes cannot include an error.")
        if self.fallback is not None and not isinstance(self.fallback, AuditFallback):
            raise TypeError("fallback must be AuditFallback or None.")
        if self.validation is not None and not isinstance(
            self.validation,
            ValidationSummary,
        ):
            raise TypeError("validation must be ValidationSummary or None.")

    @staticmethod
    def _validate_identifier_tuple(values: object, field_name: str) -> None:
        if type(values) is not tuple:
            raise TypeError(f"{field_name} must be a tuple.")
        for value in values:
            require_identifier(value, field_name)
        if len(set(values)) != len(values):
            raise ValueError(f"{field_name} must contain unique values.")

    def _validate_provider_identity(self) -> None:
        if self.provider_id is not None:
            require_identifier(self.provider_id, "provider_id")
        if self.model_id is not None:
            require_identifier(self.model_id, "model_id")
            if self.provider_id is None:
                raise ValueError("model_id requires provider_id.")
        for field_name in ("model_version", "model_digest"):
            value = getattr(self, field_name)
            if value is not None:
                if self.model_id is None:
                    raise ValueError(f"{field_name} requires model_id.")
                require_non_empty_text(value, field_name, limit=256)


class AIAuditEventFactory:
    """Build events only from R4-A contracts plus explicit execution evidence."""

    def __init__(self, *, pseudonymization_key: bytes, key_id: str) -> None:
        if type(pseudonymization_key) is not bytes or len(pseudonymization_key) < 32:
            raise ValueError("pseudonymization key must contain at least 32 bytes.")
        require_identifier(key_id, "key_id")
        self._pseudonymization_key = pseudonymization_key
        self._key_id = key_id

    def from_response(
        self,
        *,
        request: AIRequest,
        response: AIResponse,
        event_id: str,
        correlation_id: str,
        started_at: datetime,
        tool_executions: tuple[AuditToolExecution, ...] = (),
        degradation: DegradationState = DegradationState.UNKNOWN,
    ) -> AIAuditEvent:
        if not isinstance(request, AIRequest) or not isinstance(response, AIResponse):
            raise TypeError("request and response must use R4-A contracts.")
        if response.request_id != request.request_id:
            raise ValueError("response request_id does not match the audit request.")
        outcome = {
            FinishReason.COMPLETED: AuditOutcome.SUCCEEDED,
            FinishReason.MAX_TOKENS: AuditOutcome.DEGRADED,
            FinishReason.TOOL_CALL: AuditOutcome.UNKNOWN,
            FinishReason.CANCELLED: AuditOutcome.CANCELLED,
            FinishReason.UNKNOWN: AuditOutcome.UNKNOWN,
        }[response.finish_reason]
        if (
            response.finish_reason is FinishReason.MAX_TOKENS
            or AIWarningCode.QUALITY_LIMITATION in response.warnings
        ):
            degradation = DegradationState.DEGRADED
        fallback = None
        if response.fallback.used:
            if (
                response.fallback.from_provider_id is None
                or response.fallback.reason_code is None
            ):
                raise ValueError("used fallback is missing contracted metadata.")
            fallback = AuditFallback(
                from_provider_id=response.fallback.from_provider_id,
                reason_code=response.fallback.reason_code,
            )
        token_usage = response.token_usage
        if all(
            value is None
            for value in (
                token_usage.input_tokens,
                token_usage.output_tokens,
                token_usage.total_tokens,
            )
        ):
            token_usage = None
        return self._base_event(
            request=request,
            event_id=event_id,
            correlation_id=correlation_id,
            started_at=started_at,
            completed_at=response.completed_at,
            tool_executions=tool_executions,
            latency=response.latency,
            total_attempts=response.retry.total_attempts,
            outcome=outcome,
            degradation=degradation,
            provider_id=response.provider_id,
            model_id=response.model_id,
            model_version=response.model_version,
            model_digest=response.model_digest,
            token_usage=token_usage,
            cost=response.cost if response.cost.is_known else None,
            fallback=fallback,
            validation=response.validation,
        )

    def from_error(
        self,
        *,
        request: AIRequest,
        error: AIContractError,
        event_id: str,
        correlation_id: str,
        started_at: datetime,
        completed_at: datetime,
        latency: LatencyUsage | None = None,
        total_attempts: int | None = None,
        tool_executions: tuple[AuditToolExecution, ...] = (),
        degradation: DegradationState = DegradationState.UNKNOWN,
    ) -> AIAuditEvent:
        if not isinstance(request, AIRequest):
            raise TypeError("request must use the R4-A contract.")
        if not isinstance(error, AIContractError):
            raise TypeError("error must be AIContractError.")
        metadata = error.metadata
        if metadata.request_id is not None and metadata.request_id != request.request_id:
            raise ValueError("error request_id does not match the audit request.")
        outcome = (
            AuditOutcome.CANCELLED
            if error.code is AIErrorCode.CANCELLED
            else AuditOutcome.FAILED
        )
        return self._base_event(
            request=request,
            event_id=event_id,
            correlation_id=correlation_id,
            started_at=started_at,
            completed_at=completed_at,
            tool_executions=tool_executions,
            latency=latency or LatencyUsage(),
            total_attempts=total_attempts,
            outcome=outcome,
            degradation=degradation,
            provider_id=metadata.provider_id,
            model_id=metadata.model_id,
            error=AuditError(code=error.code, transient=metadata.transient),
        )

    def _base_event(
        self,
        *,
        request: AIRequest,
        event_id: str,
        correlation_id: str,
        started_at: datetime,
        completed_at: datetime,
        tool_executions: tuple[AuditToolExecution, ...],
        latency: LatencyUsage,
        total_attempts: int | None,
        outcome: AuditOutcome,
        degradation: DegradationState,
        provider_id: str | None = None,
        model_id: str | None = None,
        model_version: str | None = None,
        model_digest: str | None = None,
        token_usage: TokenUsage | None = None,
        cost: CostUsage | None = None,
        error: AuditError | None = None,
        fallback: AuditFallback | None = None,
        validation: ValidationSummary | None = None,
    ) -> AIAuditEvent:
        return AIAuditEvent(
            event_id=event_id,
            request_id=request.request_id,
            correlation_id=correlation_id,
            scope=pseudonymize_server_user_scope(
                request.user_scope,
                key=self._pseudonymization_key,
                key_id=self._key_id,
            ),
            task_kind=request.task.kind,
            task_version=request.task.version,
            execution_mode=request.execution_mode,
            policy_versions=request.policy_versions,
            output_schema_id=request.output_schema.schema_id,
            output_schema_version=request.output_schema.version,
            authorized_tool_ids=tuple(sorted(request.tool_budget.allowed_tool_ids)),
            tool_executions=tool_executions,
            technical_reference_ids=tuple(
                sorted(item.reference_id for item in request.source_references)
            ),
            started_at=started_at,
            completed_at=completed_at,
            latency=latency,
            total_attempts=total_attempts,
            outcome=outcome,
            degradation=degradation,
            provider_id=provider_id,
            model_id=model_id,
            model_version=model_version,
            model_digest=model_digest,
            token_usage=token_usage,
            cost=cost,
            error=error,
            fallback=fallback,
            validation=validation,
        )
