from __future__ import annotations

import socket
import sqlite3
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from backend.application.ai_runtime import (
    AICapability,
    AIContextEntry,
    AIErrorCode,
    AIProviderResult,
    AIRequest,
    AIResponse,
    AITask,
    AITelemetryMetric,
    AIAuditEvent,
    AIAuditEventFactory,
    AuditOutcome,
    AuditToolExecution,
    CanonicalOutputSchema,
    CertifiedSourceReference,
    CostBudget,
    CostMetric,
    CostUsage,
    DegradationState,
    ErrorMetric,
    ExecutionMode,
    FactualValidationStatus,
    FallbackMetadata,
    FinishReason,
    LatencyMetric,
    LatencyUsage,
    OutputProperty,
    OutputSchemaNode,
    OutputValueType,
    PolicyVersion,
    PrivacyClassification,
    ProviderModelMetric,
    RemoteProcessingConsent,
    RetryMetadata,
    RetryMetric,
    RoutingFallbackMetric,
    RoutingOutcome,
    ServerUserScope,
    StructureValidationStatus,
    TokenBudget,
    TokenUsage,
    TokenUsageMetric,
    ToolBudget,
    ToolExecutionMetric,
    ToolExecutionOutcome,
    ValidationSummary,
)
from backend.application.ai_runtime.errors import AIContractError, AIErrorMetadata
from backend.application.ports.ai_audit_telemetry import (
    AIAuditSink,
    AITelemetrySink,
    AuditGuarantee,
)
from backend.application.services.ai_audit_telemetry import (
    AIAuditTelemetryEmitter,
    AuditEmissionErrorCode,
    RequiredAuditError,
    TelemetryEmissionStatus,
    required_audit_guarantee,
)
from backend.integrations.ai.in_memory_audit_telemetry import (
    InMemoryAIAuditSink,
    InMemoryAITelemetrySink,
)


UTC = timezone.utc
STARTED_AT = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)
COMPLETED_AT = STARTED_AT + timedelta(milliseconds=40)
PSEUDONYMIZATION_KEY = b"r4-c-test-key-material-is-at-least-32-bytes"
SOURCE_ID = "certified.source-1"
R4C_FILES = (
    Path("backend/application/ai_runtime/audit.py"),
    Path("backend/application/ai_runtime/telemetry.py"),
    Path("backend/application/ports/ai_audit_telemetry.py"),
    Path("backend/application/services/ai_audit_telemetry.py"),
    Path("backend/integrations/ai/in_memory_audit_telemetry.py"),
)


def _request(
    *,
    execution_mode: ExecutionMode = ExecutionMode.LOCAL_ONLY,
    allowed_tools: frozenset[str] = frozenset(),
) -> AIRequest:
    source = CertifiedSourceReference(
        reference_id=SOURCE_ID,
        source_type="DETERMINISTIC_ENGINE",
        owner="synthetic.engine",
        version="1",
        as_of_timestamp=STARTED_AT,
    )
    return AIRequest(
        request_id="request-r4c-0001",
        task=AITask(kind="SYNTHETIC_EXPLANATION", version="1"),
        user_scope=ServerUserScope(
            subject_id="user-00000000-0000-0000-0000-000000000001",
            authorization_context_id="auth-context-r4c-0001",
            resolved_at=STARTED_AT,
        ),
        privacy_classification=PrivacyClassification.FINANCIAL,
        remote_processing_consent=RemoteProcessingConsent(
            granted=execution_mode is not ExecutionMode.LOCAL_ONLY,
            policy_version="privacy-v1",
            decision_reference="consent-r4c-0001",
            resolved_at=STARTED_AT,
        ),
        required_capabilities=frozenset(
            {AICapability.TEXT_GENERATION, AICapability.STRUCTURED_OUTPUT}
        ),
        context=(
            AIContextEntry(
                key="certified_fact",
                value={"amount": "0.00", "currency": "BRL"},
                source_reference_ids=(SOURCE_ID,),
            ),
        ),
        source_references=(source,),
        output_schema=CanonicalOutputSchema(
            schema_id="synthetic.answer",
            version="1",
            root=OutputSchemaNode(
                value_type=OutputValueType.OBJECT,
                properties=(
                    OutputProperty(
                        name="summary",
                        schema=OutputSchemaNode(OutputValueType.STRING),
                    ),
                ),
            ),
            requires_source_references=True,
        ),
        tool_budget=ToolBudget(allowed_tool_ids=allowed_tools, max_calls=len(allowed_tools)),
        token_budget=TokenBudget(
            max_input_tokens=256,
            max_output_tokens=128,
            max_total_tokens=384,
        ),
        cost_budget=CostBudget(maximum=Decimal("1.00"), currency="BRL"),
        deadline_at=STARTED_AT + timedelta(minutes=1),
        policy_versions=(
            PolicyVersion(name="runtime", version="r4-c"),
            PolicyVersion(name="privacy", version="privacy-v1"),
        ),
        execution_mode=execution_mode,
    )


def _response(
    request: AIRequest,
    *,
    token_usage: TokenUsage | None = None,
    cost: CostUsage | None = None,
) -> AIResponse:
    return AIResponse(
        request_id=request.request_id,
        provider_id="synthetic.local",
        model_id="synthetic-model-v1",
        model_version="synthetic-version-1",
        model_digest="sha256:synthetic",
        structured_output={"summary": "Synthetic output"},
        source_references=request.source_references,
        tool_calls=(),
        token_usage=token_usage or TokenUsage(),
        latency=LatencyUsage(total_ms=40, first_token_ms=None),
        cost=cost or CostUsage(),
        finish_reason=FinishReason.COMPLETED,
        validation=ValidationSummary(
            structure=StructureValidationStatus.VALID,
            factual=FactualValidationStatus.NOT_PERFORMED,
        ),
        retry=RetryMetadata(total_attempts=1),
        fallback=FallbackMetadata(),
        warnings=(),
        completed_at=COMPLETED_AT,
    )


def _factory() -> AIAuditEventFactory:
    return AIAuditEventFactory(
        pseudonymization_key=PSEUDONYMIZATION_KEY,
        key_id="audit-key-v1",
    )


def _event(
    *,
    request: AIRequest | None = None,
    response: AIResponse | None = None,
    tool_executions: tuple[AuditToolExecution, ...] = (),
) -> AIAuditEvent:
    request = request or _request()
    return _factory().from_response(
        request=request,
        response=response or _response(request),
        event_id="audit-event-r4c-0001",
        correlation_id="correlation-r4c-0001",
        started_at=STARTED_AT,
        tool_executions=tool_executions,
    )


def _metric(payload: object, *, metric_id: str = "metric-r4c-0001") -> AITelemetryMetric:
    return AITelemetryMetric(
        metric_id=metric_id,
        request_id="request-r4c-0001",
        correlation_id="correlation-r4c-0001",
        observed_at=COMPLETED_AT,
        payload=payload,  # type: ignore[arg-type]
    )


class _DurableAuditSink(AIAuditSink):
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.events: list[AIAuditEvent] = []

    @property
    def guarantee(self) -> AuditGuarantee:
        return AuditGuarantee.DURABLE

    def emit(self, event: AIAuditEvent) -> None:
        if self.fail:
            raise RuntimeError("raw sink failure with secret=never-expose")
        self.events.append(event)


class _FailingTelemetrySink(AITelemetrySink):
    def emit(self, metric: AITelemetryMetric) -> None:
        raise RuntimeError("raw telemetry failure with payload=never-expose")


def test_audit_contract_and_nested_metadata_are_immutable() -> None:
    event = _event()
    with pytest.raises(FrozenInstanceError):
        event.request_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        event.scope.scope_id = "changed"  # type: ignore[misc]
    assert isinstance(event.authorized_tool_ids, tuple)
    assert isinstance(event.policy_versions, tuple)


def test_utc_is_mandatory_for_events_and_metrics() -> None:
    event = _event()
    with pytest.raises(ValueError, match="UTC"):
        replace(event, started_at=STARTED_AT.replace(tzinfo=None))
    with pytest.raises(ValueError, match="UTC"):
        replace(event, completed_at=COMPLETED_AT.astimezone(timezone(timedelta(hours=-3))))
    with pytest.raises(ValueError, match="UTC"):
        _metric(LatencyMetric(total_ms=1)).__class__(
            metric_id="metric-r4c-naive",
            request_id=event.request_id,
            correlation_id=event.correlation_id,
            observed_at=COMPLETED_AT.replace(tzinfo=None),
            payload=LatencyMetric(total_ms=1),
        )


def test_factory_correlates_request_event_and_uses_only_pseudonymous_scope() -> None:
    request = _request()
    event = _event(request=request)
    same_scope = _event(request=request).scope

    assert event.request_id == request.request_id
    assert event.correlation_id == "correlation-r4c-0001"
    assert event.scope == same_scope
    assert request.user_scope.subject_id not in event.scope.scope_id
    assert request.user_scope.authorization_context_id not in event.scope.scope_id
    assert PSEUDONYMIZATION_KEY.decode("ascii") not in repr(event)


def test_unknown_fields_and_arbitrary_malicious_metadata_are_rejected() -> None:
    event = _event()
    values = {field.name: getattr(event, field.name) for field in fields(AIAuditEvent)}
    values["api_key"] = "sk-malicious-secret"
    with pytest.raises(TypeError, match="unexpected keyword") as failure:
        AIAuditEvent(**values)  # type: ignore[arg-type]
    assert "sk-malicious-secret" not in str(failure.value)

    with pytest.raises(ValueError) as identifier_failure:
        replace(event, provider_id="Bearer malicious secret value")
    assert "malicious secret value" not in str(identifier_failure.value)


def test_event_shape_has_no_prompt_response_context_or_sensitive_payload_fields() -> None:
    field_names = {field.name for field in fields(AIAuditEvent)}
    forbidden = {
        "api_key",
        "jwt",
        "password",
        "prompt",
        "response",
        "context",
        "transaction_description",
        "tool_arguments",
        "headers",
        "provider_message",
    }
    assert field_names.isdisjoint(forbidden)
    event_repr = repr(_event()).lower()
    assert "certified_fact" not in event_repr
    assert "0.00" not in event_repr
    assert "synthetic output" not in event_repr


def test_unknown_token_usage_and_provider_cost_remain_absent() -> None:
    event = _event()
    assert event.token_usage is None
    assert event.cost is None


def test_decimal_zero_cost_is_known_and_preserved_exactly() -> None:
    request = _request()
    event = _event(
        request=request,
        response=_response(
            request,
            token_usage=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0),
            cost=CostUsage(amount=Decimal("0.000000"), currency="BRL", estimated=False),
        ),
    )
    assert event.token_usage == TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0)
    assert event.cost is not None
    assert event.cost.amount == Decimal("0.000000")
    assert event.cost.amount.as_tuple().exponent == -6


def test_error_event_preserves_typed_error_and_does_not_invent_provider_or_model() -> None:
    request = _request()
    error = AIContractError(
        AIErrorCode.PRIVACY_POLICY_DENIED,
        metadata=AIErrorMetadata(request_id=request.request_id, transient=False),
    )
    event = _factory().from_error(
        request=request,
        error=error,
        event_id="audit-event-r4c-error",
        correlation_id="correlation-r4c-error",
        started_at=STARTED_AT,
        completed_at=COMPLETED_AT,
    )

    assert event.outcome is AuditOutcome.FAILED
    assert event.error is not None
    assert event.error.code is AIErrorCode.PRIVACY_POLICY_DENIED
    assert event.provider_id is None
    assert event.model_id is None
    assert event.token_usage is None
    assert event.cost is None
    assert event.validation is None
    assert event.total_attempts is None
    assert event.degradation is DegradationState.UNKNOWN


def test_response_request_mismatch_is_rejected() -> None:
    request = _request()
    other_response = replace(_response(request), request_id="request-r4c-other")
    with pytest.raises(ValueError, match="does not match"):
        _event(request=request, response=other_response)


def test_in_memory_sinks_are_deterministic_and_explicitly_volatile() -> None:
    audit_sink = InMemoryAIAuditSink()
    telemetry_sink = InMemoryAITelemetrySink()
    first = _event()
    second = replace(first, event_id="audit-event-r4c-0002")
    metric_one = _metric(LatencyMetric(total_ms=40), metric_id="metric-r4c-0001")
    metric_two = _metric(RetryMetric(total_attempts=1), metric_id="metric-r4c-0002")

    audit_sink.emit(first)
    audit_sink.emit(second)
    telemetry_sink.emit(metric_one)
    telemetry_sink.emit(metric_two)

    assert audit_sink.guarantee is AuditGuarantee.VOLATILE
    assert audit_sink.events == (first, second)
    assert telemetry_sink.metrics == (metric_one, metric_two)


@pytest.mark.parametrize("mode", [ExecutionMode.REMOTE_ONLY, ExecutionMode.HYBRID])
def test_in_memory_audit_fails_closed_for_remote_execution(mode: ExecutionMode) -> None:
    event = _event(request=_request(execution_mode=mode))
    emitter = AIAuditTelemetryEmitter(audit_sink=InMemoryAIAuditSink())

    with pytest.raises(RequiredAuditError) as failure:
        emitter.emit(event)

    assert failure.value.code is AuditEmissionErrorCode.REQUIRED_GUARANTEE_UNAVAILABLE


def test_in_memory_audit_fails_closed_when_a_tool_was_effectively_invoked() -> None:
    request = _request(allowed_tools=frozenset({"read_home_context"}))
    execution = AuditToolExecution(
        call_id="tool-call-r4c-0001",
        tool_id="read_home_context",
        outcome=ToolExecutionOutcome.SUCCEEDED,
        latency_ms=4,
    )
    event = _event(request=request, tool_executions=(execution,))

    assert required_audit_guarantee(event) is AuditGuarantee.DURABLE
    with pytest.raises(RequiredAuditError) as failure:
        AIAuditTelemetryEmitter(audit_sink=InMemoryAIAuditSink()).emit(event)
    assert failure.value.code is AuditEmissionErrorCode.REQUIRED_GUARANTEE_UNAVAILABLE


def test_in_memory_audit_is_not_durable_proof_for_tool_enabled_execution() -> None:
    event = _event(
        request=_request(allowed_tools=frozenset({"read_home_context"})),
    )
    assert event.tool_executions == ()
    assert required_audit_guarantee(event) is AuditGuarantee.DURABLE
    with pytest.raises(RequiredAuditError):
        AIAuditTelemetryEmitter(audit_sink=InMemoryAIAuditSink()).emit(event)


def test_mandatory_audit_sink_failure_is_safe_and_fail_closed() -> None:
    emitter = AIAuditTelemetryEmitter(audit_sink=_DurableAuditSink(fail=True))
    with pytest.raises(RequiredAuditError) as failure:
        emitter.emit(_event())
    assert failure.value.code is AuditEmissionErrorCode.REQUIRED_AUDIT_EMISSION_FAILED
    assert "secret" not in str(failure.value).lower()


def test_optional_telemetry_failure_does_not_become_audit_success_or_failure() -> None:
    audit_sink = InMemoryAIAuditSink()
    emitter = AIAuditTelemetryEmitter(
        audit_sink=audit_sink,
        telemetry_sink=_FailingTelemetrySink(),
    )
    result = emitter.emit(_event(), metrics=(_metric(LatencyMetric(total_ms=40)),))

    assert result.audit_emitted is True
    assert result.telemetry_status is TelemetryEmissionStatus.FAILED_OPTIONAL
    assert result.emitted_metric_count == 0
    assert result.failed_metric_count == 1
    assert len(audit_sink.events) == 1


def test_optional_telemetry_without_sink_is_reported_not_silently_dropped() -> None:
    result = AIAuditTelemetryEmitter(audit_sink=InMemoryAIAuditSink()).emit(
        _event(),
        metrics=(_metric(RetryMetric(total_attempts=1)),),
    )
    assert result.telemetry_status is TelemetryEmissionStatus.FAILED_OPTIONAL
    assert result.failed_metric_count == 1


def test_telemetry_contracts_cover_optional_provider_metrics_without_fabrication() -> None:
    metrics = (
        _metric(LatencyMetric(total_ms=40, first_token_ms=None), metric_id="metric-latency"),
        _metric(
            TokenUsageMetric(input_tokens=10, output_tokens=None, total_tokens=None),
            metric_id="metric-tokens",
        ),
        _metric(
            CostMetric(amount=Decimal("0"), currency="BRL", estimated=True),
            metric_id="metric-cost",
        ),
        _metric(
            ErrorMetric(code=AIErrorCode.TIMEOUT, transient=True),
            metric_id="metric-error",
        ),
        _metric(
            ProviderModelMetric(
                provider_id="synthetic.local",
                model_id="synthetic-model-v1",
                model_version=None,
            ),
            metric_id="metric-provider",
        ),
        _metric(RetryMetric(total_attempts=2), metric_id="metric-retry"),
        _metric(
            RoutingFallbackMetric(
                execution_mode=ExecutionMode.LOCAL_ONLY,
                outcome=RoutingOutcome.SELECTED,
                fallback_used=False,
            ),
            metric_id="metric-routing",
        ),
        _metric(
            ToolExecutionMetric(
                tool_id="read_home_context",
                outcome=ToolExecutionOutcome.UNAVAILABLE,
                error_code=AIErrorCode.INTERNAL_FAILURE,
            ),
            metric_id="metric-tool",
        ),
    )
    sink = InMemoryAITelemetrySink()
    for metric in metrics:
        sink.emit(metric)
    assert sink.metrics == metrics
    assert any(isinstance(metric.payload, ProviderModelMetric) for metric in metrics)


def test_metric_correlation_must_match_required_audit_event() -> None:
    metric = replace(_metric(LatencyMetric(total_ms=40)), request_id="request-other")
    with pytest.raises(ValueError, match="correlation"):
        AIAuditTelemetryEmitter(audit_sink=InMemoryAIAuditSink()).emit(
            _event(),
            metrics=(metric,),
        )


def test_r4_a_provider_result_does_not_gain_audit_or_persistence_side_effects() -> None:
    result = AIProviderResult(
        provider_id="synthetic.local",
        model_id="synthetic-model-v1",
        model_version=None,
        model_digest=None,
        structured_output={"summary": "Synthetic output"},
        source_reference_ids=(SOURCE_ID,),
        tool_calls=(),
        token_usage=TokenUsage(),
        latency=LatencyUsage(),
        cost=CostUsage(),
        finish_reason=FinishReason.COMPLETED,
        retry=RetryMetadata(),
        fallback=FallbackMetadata(),
        warnings=(),
        completed_at=COMPLETED_AT,
    )
    assert result.provider_id == "synthetic.local"
    assert "audit" not in {field.name for field in fields(AIProviderResult)}


def test_r4_c_paths_make_no_database_or_network_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append(repr((args, kwargs)))
        raise AssertionError("database/network access is forbidden in R4-C")

    monkeypatch.setattr(sqlite3, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    event = _event()
    result = AIAuditTelemetryEmitter(audit_sink=InMemoryAIAuditSink()).emit(event)

    assert result.audit_emitted is True
    assert calls == []
    forbidden_fragments = (
        "ai_runs",
        "backend.database",
        "sqlalchemy",
        "httpx",
        "requests",
        "google.genai",
        "google.generativeai",
        "ollama",
    )
    for path in R4C_FILES:
        source = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_fragments:
            assert fragment not in source, f"{fragment!r} found in {path}"
