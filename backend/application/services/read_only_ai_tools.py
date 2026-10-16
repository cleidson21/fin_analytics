"""Closed R4-B tool registry, certified handlers, and deny-by-default executor."""

from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic
from typing import Callable, Protocol

from backend.application.ai_runtime.contracts import AIRequest, PrivacyClassification
from backend.application.ai_runtime.errors import (
    AIContractError,
    AIErrorCode,
    AIErrorMetadata,
)
from backend.application.ai_runtime.tool_contracts import (
    FeatureContextToolArguments,
    OwnedGoalToolArguments,
    ReadOnlyToolDefinition,
    ReadOnlyToolRegistry,
    ToolArgumentContract,
    ToolArgumentKind,
    ToolAuthorizationRule,
    ToolExecutionResult,
    ToolExecutionState,
    ToolInvocation,
    ToolProvenanceContract,
    ToolResultContract,
)
from backend.application.dtos.user_response_dto import UserResponseDTO
from backend.application.exceptions.smart_context_ownership_error import (
    SmartContextOwnershipInconsistentError,
    SmartContextOwnershipUnavailableError,
)
from backend.application.services.ai_tool_authorization import (
    TrustedServerUserScopeResolver,
)
from backend.application.services.minimal_ai_context import MinimalAIContextBuilder
from backend.application.services.smart_context_consumer_foundation import (
    SmartContextConsumerFoundation,
)
from backend.domains.planning.facts import GoalPlanningFact
from backend.domains.planning.readers import PlanningGoalReadQuery
from backend.domains.smart_context import SmartContextFeature


class OwnedGoalReader(Protocol):
    def get_goal(self, db: object, goal_id, user_id) -> GoalPlanningFact | None: ...


class SmartContextReadOnlyToolHandler:
    def __init__(
        self,
        *,
        tool_id: str,
        tool_version: str,
        feature: SmartContextFeature,
        consumer: SmartContextConsumerFoundation,
        builder: MinimalAIContextBuilder,
        provenance: ToolProvenanceContract,
    ) -> None:
        self._tool_id = tool_id
        self._tool_version = tool_version
        self._feature = feature
        self._consumer = consumer
        self._builder = builder
        self._provenance = provenance

    def execute(self, invocation: ToolInvocation) -> ToolExecutionResult:
        if not isinstance(invocation.arguments, FeatureContextToolArguments):
            raise TypeError("feature context tool requires FeatureContextToolArguments.")
        call = {
            SmartContextFeature.HOME: self._consumer.get_home_context,
            SmartContextFeature.PLANNING: self._consumer.get_planning_context,
            SmartContextFeature.GOAL: self._consumer.get_goal_context,
            SmartContextFeature.FIRE: self._consumer.get_fire_context,
        }[self._feature]
        context = call(
            invocation.db,
            invocation.user_id,
            as_of_date=invocation.arguments.as_of_date,
        )
        return self._builder.build_smart_context(
            tool_id=self._tool_id,
            tool_version=self._tool_version,
            context=context,
            expected_feature=self._feature,
            resolved_at=invocation.resolved_at,
            provenance=self._provenance,
        )


class OwnedGoalReadOnlyToolHandler:
    def __init__(
        self,
        *,
        tool_id: str,
        tool_version: str,
        reader: OwnedGoalReader,
        builder: MinimalAIContextBuilder,
        provenance: ToolProvenanceContract,
    ) -> None:
        self._tool_id = tool_id
        self._tool_version = tool_version
        self._reader = reader
        self._builder = builder
        self._provenance = provenance

    def execute(self, invocation: ToolInvocation) -> ToolExecutionResult:
        if not isinstance(invocation.arguments, OwnedGoalToolArguments):
            raise TypeError("owned Goal tool requires OwnedGoalToolArguments.")
        goal = self._reader.get_goal(
            invocation.db,
            invocation.arguments.goal_id,
            invocation.user_id,
        )
        return self._builder.build_owned_goal(
            tool_id=self._tool_id,
            tool_version=self._tool_version,
            goal=goal,
            authenticated_user_id=invocation.user_id,
            resolved_at=invocation.resolved_at,
            provenance=self._provenance,
            request_id=invocation.request_id,
        )


def build_r4b_tool_registry(
    *,
    smart_context: SmartContextConsumerFoundation | None = None,
    goal_reader: OwnedGoalReader | None = None,
    builder: MinimalAIContextBuilder | None = None,
) -> ReadOnlyToolRegistry:
    """Build the exact five-tool R4-B snapshot; no R3 or dynamic discovery."""

    consumer = smart_context or SmartContextConsumerFoundation()
    owned_goal_reader = goal_reader or PlanningGoalReadQuery()
    context_builder = builder or MinimalAIContextBuilder()
    version = "1.0"
    financial_only = frozenset({PrivacyClassification.FINANCIAL})
    context_args = ToolArgumentContract(
        kind=ToolArgumentKind.FEATURE_CONTEXT,
        fields=("as_of_date",),
    )
    goal_args = ToolArgumentContract(
        kind=ToolArgumentKind.OWNED_GOAL,
        fields=("goal_id",),
    )
    result_contract = ToolResultContract(
        contract_id="minimal-certified-context",
        version="1.0",
    )
    r2_provenance = ToolProvenanceContract(
        source_contract="r2-smart-context-b7",
        version="1.0",
    )
    goal_provenance = ToolProvenanceContract(
        source_contract="planning-owned-goal-reader",
        version="1.0",
    )

    definitions: list[ReadOnlyToolDefinition] = []
    for tool_id, purpose, feature in (
        ("read_home_context", "home.context", SmartContextFeature.HOME),
        ("read_planning_context", "planning.context", SmartContextFeature.PLANNING),
        ("read_goal_context", "goal.context", SmartContextFeature.GOAL),
        ("read_fire_context", "fire.context", SmartContextFeature.FIRE),
    ):
        definitions.append(
            ReadOnlyToolDefinition(
                tool_id=tool_id,
                version=version,
                purpose=purpose,
                argument_contract=context_args,
                result_contract=result_contract,
                handler=SmartContextReadOnlyToolHandler(
                    tool_id=tool_id,
                    tool_version=version,
                    feature=feature,
                    consumer=consumer,
                    builder=context_builder,
                    provenance=r2_provenance,
                ),
                authorization=ToolAuthorizationRule(
                    allowed_task_kinds=frozenset({purpose}),
                    allowed_privacy=financial_only,
                ),
                data_classification=PrivacyClassification.FINANCIAL,
                timeout_ms=1000,
                max_calls_per_request=1,
                provenance=r2_provenance,
            )
        )
    definitions.append(
        ReadOnlyToolDefinition(
            tool_id="read_owned_goal",
            version=version,
            purpose="goal.context",
            argument_contract=goal_args,
            result_contract=result_contract,
            handler=OwnedGoalReadOnlyToolHandler(
                tool_id="read_owned_goal",
                tool_version=version,
                reader=owned_goal_reader,
                builder=context_builder,
                provenance=goal_provenance,
            ),
            authorization=ToolAuthorizationRule(
                allowed_task_kinds=frozenset({"goal.context"}),
                allowed_privacy=financial_only,
            ),
            data_classification=PrivacyClassification.FINANCIAL,
            timeout_ms=1000,
            max_calls_per_request=1,
            provenance=goal_provenance,
        )
    )
    return ReadOnlyToolRegistry(tuple(definitions))


class ReadOnlyToolExecutor:
    """Authorize, validate, account, and invoke one closed read-only handler."""

    def __init__(
        self,
        registry: ReadOnlyToolRegistry,
        *,
        scope_resolver: TrustedServerUserScopeResolver | None = None,
        clock: Callable[[], datetime] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
    ) -> None:
        if not isinstance(registry, ReadOnlyToolRegistry):
            raise TypeError("registry must be ReadOnlyToolRegistry.")
        self._registry = registry
        self._scope_resolver = scope_resolver or TrustedServerUserScopeResolver()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._monotonic = monotonic_clock or monotonic

    def execute(
        self,
        *,
        request: AIRequest,
        principal: UserResponseDTO,
        tool_id: str,
        raw_arguments: object,
        db: object,
        state: ToolExecutionState,
    ) -> ToolExecutionResult:
        if not isinstance(request, AIRequest):
            raise TypeError("request must be AIRequest.")
        if not isinstance(state, ToolExecutionState) or state.request_id != request.request_id:
            raise AIContractError(
                AIErrorCode.INVALID_REQUEST,
                metadata=AIErrorMetadata(request_id=request.request_id, field="tool_state"),
            )
        if type(tool_id) is not str:
            raise AIContractError(
                AIErrorCode.TOOL_DENIED,
                metadata=AIErrorMetadata(request_id=request.request_id),
            )
        definition = self._registry.get(tool_id)
        if definition is None:
            raise AIContractError(
                AIErrorCode.TOOL_DENIED,
                metadata=AIErrorMetadata(request_id=request.request_id),
            )

        user_id = self._scope_resolver.require_matches(
            request.user_scope,
            principal,
            request_id=request.request_id,
        )
        trusted_scope = self._scope_resolver.resolve(principal)
        self._authorize(request, definition, state)
        state.record(definition.tool_id)
        try:
            arguments = definition.argument_contract.parse(raw_arguments)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise AIContractError(
                AIErrorCode.INVALID_REQUEST,
                metadata=AIErrorMetadata(
                    request_id=request.request_id,
                    field="tool_arguments",
                ),
            ) from None

        started_at = self._utc_now()
        started_monotonic = self._monotonic()
        if started_at >= request.deadline_at:
            raise AIContractError(
                AIErrorCode.TIMEOUT,
                metadata=AIErrorMetadata(request_id=request.request_id),
            )
        invocation = ToolInvocation(
            request_id=request.request_id,
            user_scope=trusted_scope,
            user_id=user_id,
            arguments=arguments,
            db=db,
            resolved_at=started_at,
        )
        try:
            result = definition.handler.execute(invocation)
        except (SmartContextOwnershipUnavailableError, SmartContextOwnershipInconsistentError):
            raise AIContractError(
                AIErrorCode.AUTHORIZATION_DENIED,
                metadata=AIErrorMetadata(request_id=request.request_id),
            ) from None
        except AIContractError:
            raise
        except Exception:
            raise AIContractError(
                AIErrorCode.INTERNAL_FAILURE,
                metadata=AIErrorMetadata(request_id=request.request_id),
            ) from None
        elapsed_ms = (self._monotonic() - started_monotonic) * 1000
        if self._utc_now() >= request.deadline_at or elapsed_ms >= definition.timeout_ms:
            raise AIContractError(
                AIErrorCode.TIMEOUT,
                metadata=AIErrorMetadata(request_id=request.request_id),
            )
        if (
            not isinstance(result, ToolExecutionResult)
            or result.tool_id != definition.tool_id
            or result.tool_version != definition.version
            or result.provenance != definition.provenance
        ):
            raise AIContractError(
                AIErrorCode.INTERNAL_FAILURE,
                metadata=AIErrorMetadata(request_id=request.request_id),
            )
        return result

    @staticmethod
    def _authorize(
        request: AIRequest,
        definition: ReadOnlyToolDefinition,
        state: ToolExecutionState,
    ) -> None:
        if (
            definition.tool_id not in request.tool_budget.allowed_tool_ids
            or request.task.kind not in definition.authorization.allowed_task_kinds
            or request.privacy_classification not in definition.authorization.allowed_privacy
        ):
            raise AIContractError(
                AIErrorCode.TOOL_DENIED,
                metadata=AIErrorMetadata(request_id=request.request_id),
            )
        if (
            state.total_calls >= request.tool_budget.max_calls
            or state.calls_for(definition.tool_id) >= definition.max_calls_per_request
        ):
            raise AIContractError(
                AIErrorCode.TOOL_DENIED,
                metadata=AIErrorMetadata(request_id=request.request_id),
            )

    def _utc_now(self) -> datetime:
        value = self._clock()
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise TypeError("clock must return a timezone-aware datetime.")
        return value.astimezone(timezone.utc)
