"""Immutable provider-neutral contracts for the R4 AI runtime foundation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Mapping, TypeAlias


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_POLICY_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


CanonicalValue: TypeAlias = (
    str
    | int
    | bool
    | None
    | tuple["CanonicalValue", ...]
    | Mapping[str, "CanonicalValue"]
)


def require_identifier(value: object, field_name: str) -> str:
    if type(value) is not str or not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable identifier.")
    return value


def require_non_empty_text(value: object, field_name: str, *, limit: int = 256) -> str:
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise ValueError(f"{field_name} must be non-empty text up to {limit} characters.")
    return value


def normalize_utc(value: object, field_name: str) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be timezone-aware UTC.")
    return value.astimezone(timezone.utc)


def require_non_negative_int(value: object, field_name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative strict integer.")
    return value


def require_optional_non_negative_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return require_non_negative_int(value, field_name)


def require_non_negative_decimal(value: object, field_name: str) -> Decimal:
    if type(value) is not Decimal or not value.is_finite() or value < 0:
        raise ValueError(f"{field_name} must be a finite non-negative Decimal.")
    return value


def freeze_canonical_value(value: object, field_name: str) -> CanonicalValue:
    """Snapshot a JSON-like value while rejecting floats and mutable containers."""

    if value is None or type(value) in {str, int, bool}:
        return value  # type: ignore[return-value]
    if type(value) in {float, Decimal}:
        raise TypeError(
            f"{field_name} cannot contain float or Decimal; certified decimal values "
            "must remain strings."
        )
    if isinstance(value, Mapping):
        frozen: dict[str, CanonicalValue] = {}
        for key, item in value.items():
            if type(key) is not str or not key:
                raise TypeError(f"{field_name} mapping keys must be non-empty strings.")
            frozen[key] = freeze_canonical_value(item, f"{field_name}.{key}")
        return MappingProxyType(frozen)
    if type(value) in {list, tuple}:
        return tuple(
            freeze_canonical_value(item, f"{field_name}[{index}]")
            for index, item in enumerate(value)
        )
    raise TypeError(f"{field_name} contains an unsupported value type.")


class ExecutionMode(str, Enum):
    LOCAL_ONLY = "LOCAL_ONLY"
    REMOTE_ONLY = "REMOTE_ONLY"
    HYBRID = "HYBRID"


class ProviderLocality(str, Enum):
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"


class PrivacyClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    FINANCIAL = "FINANCIAL"
    SENSITIVE_PERSONAL = "SENSITIVE_PERSONAL"


class AICapability(str, Enum):
    TEXT_GENERATION = "TEXT_GENERATION"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    TOOL_CALLING = "TOOL_CALLING"
    CANCELLATION = "CANCELLATION"


class LifecycleStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    DEPRECATED = "DEPRECATED"
    DISABLED = "DISABLED"


class EvidenceOrigin(str, Enum):
    SYNTHETIC_TEST = "SYNTHETIC_TEST"
    PROVIDER_DISCOVERY = "PROVIDER_DISCOVERY"
    OFFICIAL_DOCUMENTATION = "OFFICIAL_DOCUMENTATION"
    ADMIN_CONFIGURATION = "ADMIN_CONFIGURATION"


class ProviderHealthStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class CancellationResult(str, Enum):
    CANCELLED = "CANCELLED"
    NOT_FOUND = "NOT_FOUND"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    ALREADY_COMPLETED = "ALREADY_COMPLETED"


class OutputValueType(str, Enum):
    STRING = "STRING"
    DECIMAL_STRING = "DECIMAL_STRING"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"
    OBJECT = "OBJECT"
    ARRAY = "ARRAY"


class FinishReason(str, Enum):
    COMPLETED = "COMPLETED"
    MAX_TOKENS = "MAX_TOKENS"
    TOOL_CALL = "TOOL_CALL"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class StructureValidationStatus(str, Enum):
    VALID = "VALID"


class FactualValidationStatus(str, Enum):
    NOT_PERFORMED = "NOT_PERFORMED"


class ToolCallStatus(str, Enum):
    REQUESTED = "REQUESTED"
    DENIED = "DENIED"


class AIWarningCode(str, Enum):
    MODEL_VERSION_UNKNOWN = "MODEL_VERSION_UNKNOWN"
    TOKEN_USAGE_UNKNOWN = "TOKEN_USAGE_UNKNOWN"
    COST_UNKNOWN = "COST_UNKNOWN"
    FACTUAL_VALIDATION_NOT_PERFORMED = "FACTUAL_VALIDATION_NOT_PERFORMED"
    QUALITY_LIMITATION = "QUALITY_LIMITATION"


@dataclass(frozen=True)
class ServerUserScope:
    """Opaque scope resolved by a trusted server boundary, never by model input."""

    subject_id: str
    authorization_context_id: str
    resolved_at: datetime

    def __post_init__(self) -> None:
        require_identifier(self.subject_id, "subject_id")
        require_identifier(self.authorization_context_id, "authorization_context_id")
        object.__setattr__(self, "resolved_at", normalize_utc(self.resolved_at, "resolved_at"))


@dataclass(frozen=True)
class RemoteProcessingConsent:
    granted: bool
    policy_version: str
    decision_reference: str
    resolved_at: datetime

    def __post_init__(self) -> None:
        if type(self.granted) is not bool:
            raise TypeError("granted must be a strict boolean.")
        require_non_empty_text(self.policy_version, "policy_version", limit=64)
        require_identifier(self.decision_reference, "decision_reference")
        object.__setattr__(self, "resolved_at", normalize_utc(self.resolved_at, "resolved_at"))


@dataclass(frozen=True)
class AITask:
    kind: str
    version: str

    def __post_init__(self) -> None:
        require_identifier(self.kind, "task.kind")
        require_non_empty_text(self.version, "task.version", limit=64)


@dataclass(frozen=True)
class PolicyVersion:
    name: str
    version: str

    def __post_init__(self) -> None:
        if type(self.name) is not str or not _POLICY_NAME_PATTERN.fullmatch(self.name):
            raise ValueError("policy name must be a stable identifier.")
        require_non_empty_text(self.version, "policy.version", limit=64)


@dataclass(frozen=True)
class CertifiedSourceReference:
    reference_id: str
    source_type: str
    owner: str
    version: str
    as_of_timestamp: datetime

    def __post_init__(self) -> None:
        require_identifier(self.reference_id, "reference_id")
        require_identifier(self.source_type, "source_type")
        require_identifier(self.owner, "owner")
        require_non_empty_text(self.version, "source.version", limit=64)
        object.__setattr__(
            self,
            "as_of_timestamp",
            normalize_utc(self.as_of_timestamp, "as_of_timestamp"),
        )


@dataclass(frozen=True)
class AIContextEntry:
    key: str
    value: CanonicalValue
    source_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        require_identifier(self.key, "context.key")
        if type(self.source_reference_ids) is not tuple:
            raise TypeError("source_reference_ids must be a tuple.")
        for reference_id in self.source_reference_ids:
            require_identifier(reference_id, "source_reference_id")
        if len(set(self.source_reference_ids)) != len(self.source_reference_ids):
            raise ValueError("source_reference_ids must be unique.")
        object.__setattr__(self, "value", freeze_canonical_value(self.value, "context.value"))


@dataclass(frozen=True)
class OutputProperty:
    name: str
    schema: "OutputSchemaNode"
    required: bool = True

    def __post_init__(self) -> None:
        require_identifier(self.name, "output property name")
        if not isinstance(self.schema, OutputSchemaNode):
            raise TypeError("output property schema must be OutputSchemaNode.")
        if type(self.required) is not bool:
            raise TypeError("output property required must be a strict boolean.")


@dataclass(frozen=True)
class OutputSchemaNode:
    value_type: OutputValueType
    properties: tuple[OutputProperty, ...] = ()
    item_schema: "OutputSchemaNode | None" = None

    def __post_init__(self) -> None:
        if not isinstance(self.value_type, OutputValueType):
            raise TypeError("value_type must be OutputValueType.")
        if type(self.properties) is not tuple or any(
            not isinstance(item, OutputProperty) for item in self.properties
        ):
            raise TypeError("properties must be a tuple of OutputProperty values.")
        property_names = tuple(item.name for item in self.properties)
        if len(set(property_names)) != len(property_names):
            raise ValueError("output object property names must be unique.")
        if self.value_type is OutputValueType.OBJECT:
            if self.item_schema is not None:
                raise ValueError("object schemas cannot define item_schema.")
        elif self.value_type is OutputValueType.ARRAY:
            if self.properties or not isinstance(self.item_schema, OutputSchemaNode):
                raise ValueError("array schemas require item_schema and no properties.")
        elif self.properties or self.item_schema is not None:
            raise ValueError("scalar schemas cannot define properties or item_schema.")


@dataclass(frozen=True)
class CanonicalOutputSchema:
    schema_id: str
    version: str
    root: OutputSchemaNode
    requires_source_references: bool

    def __post_init__(self) -> None:
        require_identifier(self.schema_id, "schema_id")
        require_non_empty_text(self.version, "schema.version", limit=64)
        if not isinstance(self.root, OutputSchemaNode):
            raise TypeError("root must be OutputSchemaNode.")
        if self.root.value_type is not OutputValueType.OBJECT:
            raise ValueError("canonical output root must be an object schema.")
        if type(self.requires_source_references) is not bool:
            raise TypeError("requires_source_references must be a strict boolean.")


@dataclass(frozen=True)
class ToolBudget:
    allowed_tool_ids: frozenset[str] = field(default_factory=frozenset)
    max_calls: int = 0

    def __post_init__(self) -> None:
        if type(self.allowed_tool_ids) is not frozenset:
            raise TypeError("allowed_tool_ids must be a frozenset.")
        for tool_id in self.allowed_tool_ids:
            require_identifier(tool_id, "tool_id")
        require_non_negative_int(self.max_calls, "max_calls")


@dataclass(frozen=True)
class TokenBudget:
    max_input_tokens: int
    max_output_tokens: int
    max_total_tokens: int

    def __post_init__(self) -> None:
        for field_name in (
            "max_input_tokens",
            "max_output_tokens",
            "max_total_tokens",
        ):
            require_non_negative_int(getattr(self, field_name), field_name)
        if self.max_total_tokens < max(self.max_input_tokens, self.max_output_tokens):
            raise ValueError("max_total_tokens cannot be below an individual token limit.")


@dataclass(frozen=True)
class CostBudget:
    maximum: Decimal
    currency: str

    def __post_init__(self) -> None:
        require_non_negative_decimal(self.maximum, "cost.maximum")
        if type(self.currency) is not str or not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError("cost currency must be a three-letter uppercase code.")


@dataclass(frozen=True)
class CapabilityEvidence:
    origin: EvidenceOrigin
    observed_at: datetime
    reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.origin, EvidenceOrigin):
            raise TypeError("origin must be EvidenceOrigin.")
        object.__setattr__(self, "observed_at", normalize_utc(self.observed_at, "observed_at"))
        require_non_empty_text(self.reference, "evidence.reference", limit=256)


@dataclass(frozen=True)
class ProviderIdentity:
    provider_id: str
    display_name: str
    locality: ProviderLocality

    def __post_init__(self) -> None:
        require_identifier(self.provider_id, "provider_id")
        require_non_empty_text(self.display_name, "display_name", limit=128)
        if not isinstance(self.locality, ProviderLocality):
            raise TypeError("locality must be ProviderLocality.")


@dataclass(frozen=True)
class ProviderCapabilities:
    identity: ProviderIdentity
    capabilities: frozenset[AICapability]
    permitted_privacy: frozenset[PrivacyClassification]
    lifecycle: LifecycleStatus
    evidence: CapabilityEvidence

    def __post_init__(self) -> None:
        if not isinstance(self.identity, ProviderIdentity):
            raise TypeError("identity must be ProviderIdentity.")
        if type(self.capabilities) is not frozenset or any(
            not isinstance(item, AICapability) for item in self.capabilities
        ):
            raise TypeError("capabilities must be a frozenset of AICapability values.")
        if type(self.permitted_privacy) is not frozenset or any(
            not isinstance(item, PrivacyClassification) for item in self.permitted_privacy
        ):
            raise TypeError(
                "permitted_privacy must be a frozenset of PrivacyClassification values."
            )
        if not isinstance(self.lifecycle, LifecycleStatus):
            raise TypeError("lifecycle must be LifecycleStatus.")
        if not isinstance(self.evidence, CapabilityEvidence):
            raise TypeError("evidence must be CapabilityEvidence.")

    def supports(self, capability: AICapability) -> bool:
        return capability in self.capabilities


@dataclass(frozen=True)
class ModelCapabilities:
    provider_id: str
    model_id: str
    model_version: str | None
    model_digest: str | None
    locality: ProviderLocality
    capabilities: frozenset[AICapability]
    context_window_tokens: int | None
    max_output_tokens: int | None
    lifecycle: LifecycleStatus
    evidence: CapabilityEvidence

    def __post_init__(self) -> None:
        require_identifier(self.provider_id, "provider_id")
        require_identifier(self.model_id, "model_id")
        if self.model_version is not None:
            require_non_empty_text(self.model_version, "model_version", limit=128)
        if self.model_digest is not None:
            require_non_empty_text(self.model_digest, "model_digest", limit=256)
        if not isinstance(self.locality, ProviderLocality):
            raise TypeError("locality must be ProviderLocality.")
        if type(self.capabilities) is not frozenset or any(
            not isinstance(item, AICapability) for item in self.capabilities
        ):
            raise TypeError("capabilities must be a frozenset of AICapability values.")
        for field_name in ("context_window_tokens", "max_output_tokens"):
            value = require_optional_non_negative_int(getattr(self, field_name), field_name)
            if value == 0:
                raise ValueError(f"{field_name} must be positive when known.")
        if not isinstance(self.lifecycle, LifecycleStatus):
            raise TypeError("lifecycle must be LifecycleStatus.")
        if not isinstance(self.evidence, CapabilityEvidence):
            raise TypeError("evidence must be CapabilityEvidence.")

    def supports(self, capability: AICapability) -> bool:
        return capability in self.capabilities


@dataclass(frozen=True)
class AIProviderHealth:
    provider_id: str
    model_id: str | None
    status: ProviderHealthStatus
    checked_at: datetime
    latency_ms: int | None = None
    reason_code: str | None = None

    def __post_init__(self) -> None:
        require_identifier(self.provider_id, "provider_id")
        if self.model_id is not None:
            require_identifier(self.model_id, "model_id")
        if not isinstance(self.status, ProviderHealthStatus):
            raise TypeError("status must be ProviderHealthStatus.")
        object.__setattr__(self, "checked_at", normalize_utc(self.checked_at, "checked_at"))
        require_optional_non_negative_int(self.latency_ms, "latency_ms")
        if self.reason_code is not None:
            require_identifier(self.reason_code, "reason_code")


@dataclass(frozen=True)
class AIRequest:
    request_id: str
    task: AITask
    user_scope: ServerUserScope
    privacy_classification: PrivacyClassification
    remote_processing_consent: RemoteProcessingConsent
    required_capabilities: frozenset[AICapability]
    context: tuple[AIContextEntry, ...]
    source_references: tuple[CertifiedSourceReference, ...]
    output_schema: CanonicalOutputSchema
    tool_budget: ToolBudget
    token_budget: TokenBudget
    cost_budget: CostBudget
    deadline_at: datetime
    policy_versions: tuple[PolicyVersion, ...]
    execution_mode: ExecutionMode = ExecutionMode.LOCAL_ONLY

    def __post_init__(self) -> None:
        require_identifier(self.request_id, "request_id")
        if not isinstance(self.task, AITask):
            raise TypeError("task must be AITask.")
        if not isinstance(self.user_scope, ServerUserScope):
            raise TypeError("user_scope must be a server-resolved ServerUserScope.")
        if not isinstance(self.privacy_classification, PrivacyClassification):
            raise TypeError("privacy_classification must be PrivacyClassification.")
        if not isinstance(self.remote_processing_consent, RemoteProcessingConsent):
            raise TypeError("remote_processing_consent must be RemoteProcessingConsent.")
        if type(self.required_capabilities) is not frozenset or any(
            not isinstance(item, AICapability) for item in self.required_capabilities
        ):
            raise TypeError(
                "required_capabilities must be a frozenset of AICapability values."
            )
        if AICapability.STRUCTURED_OUTPUT not in self.required_capabilities:
            raise ValueError("R4-A generation requires STRUCTURED_OUTPUT capability.")
        if type(self.context) is not tuple or any(
            not isinstance(item, AIContextEntry) for item in self.context
        ):
            raise TypeError("context must be a tuple of AIContextEntry values.")
        if type(self.source_references) is not tuple or any(
            not isinstance(item, CertifiedSourceReference)
            for item in self.source_references
        ):
            raise TypeError(
                "source_references must be a tuple of CertifiedSourceReference values."
            )
        if not isinstance(self.output_schema, CanonicalOutputSchema):
            raise TypeError("output_schema must be CanonicalOutputSchema.")
        if not isinstance(self.tool_budget, ToolBudget):
            raise TypeError("tool_budget must be ToolBudget.")
        if not isinstance(self.token_budget, TokenBudget):
            raise TypeError("token_budget must be TokenBudget.")
        if not isinstance(self.cost_budget, CostBudget):
            raise TypeError("cost_budget must be CostBudget.")
        object.__setattr__(
            self,
            "deadline_at",
            normalize_utc(self.deadline_at, "deadline_at"),
        )
        if type(self.policy_versions) is not tuple or any(
            not isinstance(item, PolicyVersion) for item in self.policy_versions
        ):
            raise TypeError("policy_versions must be a tuple of PolicyVersion values.")
        if not self.policy_versions:
            raise ValueError("at least one policy version is required.")
        if not isinstance(self.execution_mode, ExecutionMode):
            raise TypeError("execution_mode must be ExecutionMode.")
        if (
            self.execution_mode is ExecutionMode.REMOTE_ONLY
            and not self.remote_processing_consent.granted
        ):
            raise ValueError("REMOTE_ONLY requires resolved remote-processing consent.")

        context_keys = tuple(item.key for item in self.context)
        if len(set(context_keys)) != len(context_keys):
            raise ValueError("context keys must be unique.")
        source_ids = tuple(item.reference_id for item in self.source_references)
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("source reference IDs must be unique.")
        source_id_set = set(source_ids)
        for item in self.context:
            missing = set(item.source_reference_ids) - source_id_set
            if missing:
                raise ValueError("context contains an unknown source reference.")
        policy_names = tuple(item.name for item in self.policy_versions)
        if len(set(policy_names)) != len(policy_names):
            raise ValueError("policy version names must be unique.")


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def __post_init__(self) -> None:
        for field_name in ("input_tokens", "output_tokens", "total_tokens"):
            require_optional_non_negative_int(getattr(self, field_name), field_name)

    @property
    def is_known(self) -> bool:
        return self.total_tokens is not None


@dataclass(frozen=True)
class LatencyUsage:
    total_ms: int | None = None
    first_token_ms: int | None = None

    def __post_init__(self) -> None:
        require_optional_non_negative_int(self.total_ms, "total_ms")
        require_optional_non_negative_int(self.first_token_ms, "first_token_ms")
        if (
            self.total_ms is not None
            and self.first_token_ms is not None
            and self.first_token_ms > self.total_ms
        ):
            raise ValueError("first_token_ms cannot exceed total_ms.")


@dataclass(frozen=True)
class CostUsage:
    amount: Decimal | None = None
    currency: str | None = None
    estimated: bool | None = None

    def __post_init__(self) -> None:
        if self.amount is None:
            if self.currency is not None or self.estimated is not None:
                raise ValueError("unknown cost cannot include currency or estimate status.")
            return
        require_non_negative_decimal(self.amount, "cost.amount")
        if type(self.currency) is not str or not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError("known cost requires a three-letter uppercase currency.")
        if type(self.estimated) is not bool:
            raise TypeError("known cost requires a strict estimated boolean.")

    @property
    def is_known(self) -> bool:
        return self.amount is not None


@dataclass(frozen=True)
class ToolCallMetadata:
    call_id: str
    tool_id: str
    status: ToolCallStatus

    def __post_init__(self) -> None:
        require_identifier(self.call_id, "call_id")
        require_identifier(self.tool_id, "tool_id")
        if not isinstance(self.status, ToolCallStatus):
            raise TypeError("status must be ToolCallStatus.")


@dataclass(frozen=True)
class RetryMetadata:
    total_attempts: int = 1

    def __post_init__(self) -> None:
        if type(self.total_attempts) is not int or self.total_attempts < 1:
            raise ValueError("total_attempts must be a positive strict integer.")


@dataclass(frozen=True)
class FallbackMetadata:
    used: bool = False
    from_provider_id: str | None = None
    reason_code: str | None = None

    def __post_init__(self) -> None:
        if type(self.used) is not bool:
            raise TypeError("used must be a strict boolean.")
        if self.used:
            if self.from_provider_id is None or self.reason_code is None:
                raise ValueError("used fallback requires provider and reason metadata.")
            require_identifier(self.from_provider_id, "from_provider_id")
            require_identifier(self.reason_code, "fallback.reason_code")
        elif self.from_provider_id is not None or self.reason_code is not None:
            raise ValueError("unused fallback cannot include provider or reason metadata.")


@dataclass(frozen=True)
class ValidationSummary:
    structure: StructureValidationStatus = StructureValidationStatus.VALID
    factual: FactualValidationStatus = FactualValidationStatus.NOT_PERFORMED

    def __post_init__(self) -> None:
        if not isinstance(self.structure, StructureValidationStatus):
            raise TypeError("structure must be StructureValidationStatus.")
        if not isinstance(self.factual, FactualValidationStatus):
            raise TypeError("factual must be FactualValidationStatus.")


@dataclass(frozen=True)
class AIProviderResult:
    """Untrusted immutable adapter result, prior to canonical validation."""

    provider_id: str
    model_id: str
    model_version: str | None
    model_digest: str | None
    structured_output: Mapping[str, CanonicalValue]
    source_reference_ids: tuple[str, ...]
    tool_calls: tuple[ToolCallMetadata, ...]
    token_usage: TokenUsage
    latency: LatencyUsage
    cost: CostUsage
    finish_reason: FinishReason
    retry: RetryMetadata
    fallback: FallbackMetadata
    warnings: tuple[AIWarningCode, ...]
    completed_at: datetime

    def __post_init__(self) -> None:
        require_identifier(self.provider_id, "provider_id")
        require_identifier(self.model_id, "model_id")
        if self.model_version is not None:
            require_non_empty_text(self.model_version, "model_version", limit=128)
        if self.model_digest is not None:
            require_non_empty_text(self.model_digest, "model_digest", limit=256)
        frozen_output = freeze_canonical_value(self.structured_output, "structured_output")
        if not isinstance(frozen_output, Mapping):
            raise TypeError("structured_output must be a mapping.")
        object.__setattr__(self, "structured_output", frozen_output)
        if type(self.source_reference_ids) is not tuple:
            raise TypeError("source_reference_ids must be a tuple.")
        for reference_id in self.source_reference_ids:
            require_identifier(reference_id, "source_reference_id")
        if len(set(self.source_reference_ids)) != len(self.source_reference_ids):
            raise ValueError("source_reference_ids must be unique.")
        if type(self.tool_calls) is not tuple or any(
            not isinstance(item, ToolCallMetadata) for item in self.tool_calls
        ):
            raise TypeError("tool_calls must be a tuple of ToolCallMetadata values.")
        tool_call_ids = tuple(item.call_id for item in self.tool_calls)
        if len(set(tool_call_ids)) != len(tool_call_ids):
            raise ValueError("tool call IDs must be unique.")
        for expected_type, value, field_name in (
            (TokenUsage, self.token_usage, "token_usage"),
            (LatencyUsage, self.latency, "latency"),
            (CostUsage, self.cost, "cost"),
            (RetryMetadata, self.retry, "retry"),
            (FallbackMetadata, self.fallback, "fallback"),
        ):
            if not isinstance(value, expected_type):
                raise TypeError(f"{field_name} has an invalid contract type.")
        if not isinstance(self.finish_reason, FinishReason):
            raise TypeError("finish_reason must be FinishReason.")
        if type(self.warnings) is not tuple or any(
            not isinstance(item, AIWarningCode) for item in self.warnings
        ):
            raise TypeError("warnings must be a tuple of AIWarningCode values.")
        if len(set(self.warnings)) != len(self.warnings):
            raise ValueError("warnings must be unique.")
        object.__setattr__(
            self,
            "completed_at",
            normalize_utc(self.completed_at, "completed_at"),
        )


@dataclass(frozen=True)
class AIResponse:
    request_id: str
    provider_id: str
    model_id: str
    model_version: str | None
    model_digest: str | None
    structured_output: Mapping[str, CanonicalValue]
    source_references: tuple[CertifiedSourceReference, ...]
    tool_calls: tuple[ToolCallMetadata, ...]
    token_usage: TokenUsage
    latency: LatencyUsage
    cost: CostUsage
    finish_reason: FinishReason
    validation: ValidationSummary
    retry: RetryMetadata
    fallback: FallbackMetadata
    warnings: tuple[AIWarningCode, ...]
    completed_at: datetime

    def __post_init__(self) -> None:
        require_identifier(self.request_id, "request_id")
        require_identifier(self.provider_id, "provider_id")
        require_identifier(self.model_id, "model_id")
        if self.model_version is not None:
            require_non_empty_text(self.model_version, "model_version", limit=128)
        if self.model_digest is not None:
            require_non_empty_text(self.model_digest, "model_digest", limit=256)
        frozen_output = freeze_canonical_value(self.structured_output, "structured_output")
        if not isinstance(frozen_output, Mapping):
            raise TypeError("structured_output must be a mapping.")
        object.__setattr__(self, "structured_output", frozen_output)
        if type(self.source_references) is not tuple or any(
            not isinstance(item, CertifiedSourceReference)
            for item in self.source_references
        ):
            raise TypeError(
                "source_references must be a tuple of CertifiedSourceReference values."
            )
        source_ids = tuple(item.reference_id for item in self.source_references)
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("source reference IDs must be unique.")
        if type(self.tool_calls) is not tuple or any(
            not isinstance(item, ToolCallMetadata) for item in self.tool_calls
        ):
            raise TypeError("tool_calls must be a tuple of ToolCallMetadata values.")
        tool_call_ids = tuple(item.call_id for item in self.tool_calls)
        if len(set(tool_call_ids)) != len(tool_call_ids):
            raise ValueError("tool call IDs must be unique.")
        for expected_type, value, field_name in (
            (TokenUsage, self.token_usage, "token_usage"),
            (LatencyUsage, self.latency, "latency"),
            (CostUsage, self.cost, "cost"),
            (ValidationSummary, self.validation, "validation"),
            (RetryMetadata, self.retry, "retry"),
            (FallbackMetadata, self.fallback, "fallback"),
        ):
            if not isinstance(value, expected_type):
                raise TypeError(f"{field_name} has an invalid contract type.")
        if not isinstance(self.finish_reason, FinishReason):
            raise TypeError("finish_reason must be FinishReason.")
        if type(self.warnings) is not tuple or any(
            not isinstance(item, AIWarningCode) for item in self.warnings
        ):
            raise TypeError("warnings must be a tuple of AIWarningCode values.")
        if len(set(self.warnings)) != len(self.warnings):
            raise ValueError("warnings must be unique.")
        object.__setattr__(
            self,
            "completed_at",
            normalize_utc(self.completed_at, "completed_at"),
        )


def is_decimal_string(value: object) -> bool:
    if type(value) is not str or not _DECIMAL_PATTERN.fullmatch(value):
        return False
    try:
        parsed = Decimal(value)
    except Exception:
        return False
    return parsed.is_finite()
