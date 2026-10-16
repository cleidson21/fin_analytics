"""Closed read-only tool contracts for the R4-B AI runtime boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Protocol, TypeAlias
from uuid import UUID

from backend.application.ai_runtime.contracts import (
    AIContextEntry,
    CertifiedSourceReference,
    PrivacyClassification,
    ServerUserScope,
    require_identifier,
    require_non_empty_text,
)


class ToolSideEffect(str, Enum):
    READ_ONLY = "READ_ONLY"


class ToolArgumentKind(str, Enum):
    FEATURE_CONTEXT = "FEATURE_CONTEXT"
    OWNED_GOAL = "OWNED_GOAL"


class ToolResultStatus(str, Enum):
    SUCCESS = "SUCCESS"


class ContextCompleteness(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class FeatureContextToolArguments:
    as_of_date: date

    def __post_init__(self) -> None:
        if type(self.as_of_date) is not date:
            raise TypeError("as_of_date must be a civil date.")


@dataclass(frozen=True)
class OwnedGoalToolArguments:
    goal_id: UUID

    def __post_init__(self) -> None:
        if type(self.goal_id) is not UUID:
            raise TypeError("goal_id must be a UUID.")


ToolArguments: TypeAlias = FeatureContextToolArguments | OwnedGoalToolArguments


@dataclass(frozen=True)
class ToolArgumentContract:
    kind: ToolArgumentKind
    fields: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ToolArgumentKind):
            raise TypeError("kind must be ToolArgumentKind.")
        if type(self.fields) is not tuple or any(type(item) is not str for item in self.fields):
            raise TypeError("fields must be an immutable tuple of strings.")
        expected = {
            ToolArgumentKind.FEATURE_CONTEXT: ("as_of_date",),
            ToolArgumentKind.OWNED_GOAL: ("goal_id",),
        }[self.kind]
        if self.fields != expected:
            raise ValueError("tool argument fields must match the closed contract.")

    def parse(self, raw_arguments: Mapping[str, object]) -> ToolArguments:
        if not isinstance(raw_arguments, Mapping):
            raise TypeError("tool arguments must be a mapping.")
        if any(type(key) is not str for key in raw_arguments):
            raise TypeError("tool argument names must be strings.")
        if set(raw_arguments) != set(self.fields):
            raise ValueError("tool arguments must contain exactly the contracted fields.")

        if self.kind is ToolArgumentKind.FEATURE_CONTEXT:
            raw_date = raw_arguments["as_of_date"]
            if type(raw_date) is not str:
                raise TypeError("as_of_date must be an ISO civil-date string.")
            try:
                parsed_date = date.fromisoformat(raw_date)
            except ValueError as error:
                raise ValueError("as_of_date must be an ISO civil-date string.") from error
            if parsed_date.isoformat() != raw_date:
                raise ValueError("as_of_date must use canonical YYYY-MM-DD form.")
            return FeatureContextToolArguments(as_of_date=parsed_date)

        raw_goal_id = raw_arguments["goal_id"]
        if type(raw_goal_id) is not str:
            raise TypeError("goal_id must be a UUID string.")
        try:
            return OwnedGoalToolArguments(goal_id=UUID(raw_goal_id))
        except ValueError as error:
            raise ValueError("goal_id must be a UUID string.") from error


@dataclass(frozen=True)
class ToolResultContract:
    contract_id: str
    version: str

    def __post_init__(self) -> None:
        require_identifier(self.contract_id, "result.contract_id")
        require_non_empty_text(self.version, "result.version", limit=64)


@dataclass(frozen=True)
class ToolAuthorizationRule:
    allowed_task_kinds: frozenset[str]
    allowed_privacy: frozenset[PrivacyClassification]

    def __post_init__(self) -> None:
        if type(self.allowed_task_kinds) is not frozenset or not self.allowed_task_kinds:
            raise TypeError("allowed_task_kinds must be a non-empty frozenset.")
        for task_kind in self.allowed_task_kinds:
            require_identifier(task_kind, "allowed_task_kind")
        if type(self.allowed_privacy) is not frozenset or not self.allowed_privacy:
            raise TypeError("allowed_privacy must be a non-empty frozenset.")
        if any(not isinstance(item, PrivacyClassification) for item in self.allowed_privacy):
            raise TypeError("allowed_privacy must contain PrivacyClassification values.")


@dataclass(frozen=True)
class ToolProvenanceContract:
    source_contract: str
    version: str

    def __post_init__(self) -> None:
        require_identifier(self.source_contract, "source_contract")
        require_non_empty_text(self.version, "provenance.version", limit=64)


@dataclass(frozen=True)
class ToolInvocation:
    request_id: str
    user_scope: ServerUserScope
    user_id: UUID
    arguments: ToolArguments
    db: object
    resolved_at: datetime

    def __post_init__(self) -> None:
        require_identifier(self.request_id, "request_id")
        if not isinstance(self.user_scope, ServerUserScope):
            raise TypeError("user_scope must be ServerUserScope.")
        if type(self.user_id) is not UUID:
            raise TypeError("user_id must be a UUID.")
        if not isinstance(
            self.arguments,
            (FeatureContextToolArguments, OwnedGoalToolArguments),
        ):
            raise TypeError("arguments must implement the closed tool contract.")
        if type(self.resolved_at) is not datetime or self.resolved_at.tzinfo is None:
            raise ValueError("resolved_at must be timezone-aware.")


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_id: str
    tool_version: str
    status: ToolResultStatus
    completeness: ContextCompleteness
    context: tuple[AIContextEntry, ...]
    source_references: tuple[CertifiedSourceReference, ...]
    provenance: ToolProvenanceContract

    def __post_init__(self) -> None:
        require_identifier(self.tool_id, "tool_id")
        require_non_empty_text(self.tool_version, "tool_version", limit=64)
        if not isinstance(self.status, ToolResultStatus):
            raise TypeError("status must be ToolResultStatus.")
        if not isinstance(self.completeness, ContextCompleteness):
            raise TypeError("completeness must be ContextCompleteness.")
        if type(self.context) is not tuple or any(
            not isinstance(item, AIContextEntry) for item in self.context
        ):
            raise TypeError("context must contain AIContextEntry values.")
        if type(self.source_references) is not tuple or any(
            not isinstance(item, CertifiedSourceReference)
            for item in self.source_references
        ):
            raise TypeError("source_references must contain certified references.")
        if not isinstance(self.provenance, ToolProvenanceContract):
            raise TypeError("provenance must be ToolProvenanceContract.")
        source_ids = {item.reference_id for item in self.source_references}
        if any(
            not set(item.source_reference_ids).issubset(source_ids)
            for item in self.context
        ):
            raise ValueError("tool context references an unknown certified source.")


class ReadOnlyToolHandler(Protocol):
    def execute(self, invocation: ToolInvocation) -> ToolExecutionResult: ...


@dataclass(frozen=True)
class ReadOnlyToolDefinition:
    tool_id: str
    version: str
    purpose: str
    argument_contract: ToolArgumentContract
    result_contract: ToolResultContract
    handler: ReadOnlyToolHandler
    authorization: ToolAuthorizationRule
    data_classification: PrivacyClassification
    timeout_ms: int
    max_calls_per_request: int
    provenance: ToolProvenanceContract
    side_effect: ToolSideEffect = ToolSideEffect.READ_ONLY

    def __post_init__(self) -> None:
        require_identifier(self.tool_id, "tool_id")
        require_non_empty_text(self.version, "tool.version", limit=64)
        require_identifier(self.purpose, "tool.purpose")
        if not isinstance(self.argument_contract, ToolArgumentContract):
            raise TypeError("argument_contract must be ToolArgumentContract.")
        if not isinstance(self.result_contract, ToolResultContract):
            raise TypeError("result_contract must be ToolResultContract.")
        if not callable(getattr(self.handler, "execute", None)):
            raise TypeError("handler must expose execute().")
        if not isinstance(self.authorization, ToolAuthorizationRule):
            raise TypeError("authorization must be ToolAuthorizationRule.")
        if not isinstance(self.data_classification, PrivacyClassification):
            raise TypeError("data_classification must be PrivacyClassification.")
        if type(self.timeout_ms) is not int or self.timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive strict integer.")
        if type(self.max_calls_per_request) is not int or self.max_calls_per_request <= 0:
            raise ValueError("max_calls_per_request must be a positive strict integer.")
        if not isinstance(self.provenance, ToolProvenanceContract):
            raise TypeError("provenance must be ToolProvenanceContract.")
        if self.side_effect is not ToolSideEffect.READ_ONLY:
            raise ValueError("R4-B admits read-only tools only.")


class ReadOnlyToolRegistry:
    """Immutable instance-scoped registry with no aliases or handler discovery."""

    def __init__(self, definitions: tuple[ReadOnlyToolDefinition, ...]) -> None:
        if type(definitions) is not tuple:
            raise TypeError("definitions must be a tuple.")
        snapshot: dict[str, ReadOnlyToolDefinition] = {}
        for definition in definitions:
            if not isinstance(definition, ReadOnlyToolDefinition):
                raise TypeError("definitions must contain ReadOnlyToolDefinition values.")
            if definition.tool_id in snapshot:
                raise ValueError(f"duplicate tool_id: {definition.tool_id}")
            snapshot[definition.tool_id] = definition
        self._definitions: Mapping[str, ReadOnlyToolDefinition] = MappingProxyType(snapshot)

    def get(self, tool_id: str) -> ReadOnlyToolDefinition | None:
        return self._definitions.get(tool_id)

    @property
    def definitions(self) -> Mapping[str, ReadOnlyToolDefinition]:
        return self._definitions

    def __len__(self) -> int:
        return len(self._definitions)


@dataclass
class ToolExecutionState:
    """Request-local call accounting; never a mutable global registry."""

    request_id: str
    _total_calls: int = 0
    _calls_by_tool: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_identifier(self.request_id, "request_id")

    @property
    def total_calls(self) -> int:
        return self._total_calls

    def calls_for(self, tool_id: str) -> int:
        return self._calls_by_tool.get(tool_id, 0)

    def record(self, tool_id: str) -> None:
        require_identifier(tool_id, "tool_id")
        self._total_calls += 1
        self._calls_by_tool[tool_id] = self.calls_for(tool_id) + 1

    @property
    def calls_by_tool(self) -> Mapping[str, int]:
        return MappingProxyType(dict(self._calls_by_tool))
