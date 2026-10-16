from __future__ import annotations

import inspect
import socket
import sys
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from backend.application.ai_runtime import (
    AICapability,
    AIContextEntry,
    AIContractError,
    AIErrorCode,
    AIProviderResult,
    AIRequest,
    AITask,
    AIWarningCode,
    CancellationResult,
    CanonicalOutputSchema,
    CapabilityEvidence,
    CertifiedSourceReference,
    CostBudget,
    CostUsage,
    EvidenceOrigin,
    ExecutionMode,
    FactualValidationStatus,
    FallbackMetadata,
    FinishReason,
    LatencyUsage,
    LifecycleStatus,
    ModelCapabilities,
    ModelCapabilityRegistry,
    OutputProperty,
    OutputSchemaNode,
    OutputValueType,
    PolicyVersion,
    PrivacyClassification,
    ProviderCapabilities,
    ProviderCapabilityRegistry,
    ProviderIdentity,
    ProviderLocality,
    RemoteProcessingConsent,
    RetryMetadata,
    ServerUserScope,
    StructureValidationStatus,
    TokenBudget,
    TokenUsage,
    ToolBudget,
    ToolCallMetadata,
    ToolCallStatus,
)
from backend.application.ports.ai_provider import AIProvider
from backend.application.services.provider_neutral_ai import ProviderNeutralAIService
from backend.integrations.ai.fake_provider import (
    DeterministicFakeAIProvider,
    FakeProviderMode,
)


UTC = timezone.utc
NOW = datetime(2030, 1, 1, 12, tzinfo=UTC)
SOURCE_ID = "certified.source-1"
PROVIDER_ID = "synthetic.local"
MODEL_ID = "synthetic-model-v1"
RUNTIME_FILES = (
    Path("backend/application/ai_runtime/contracts.py"),
    Path("backend/application/ai_runtime/errors.py"),
    Path("backend/application/ai_runtime/registry.py"),
    Path("backend/application/ai_runtime/validation.py"),
    Path("backend/application/ports/ai_provider.py"),
    Path("backend/application/services/provider_neutral_ai.py"),
    Path("backend/integrations/ai/fake_provider.py"),
)


def _evidence() -> CapabilityEvidence:
    return CapabilityEvidence(
        origin=EvidenceOrigin.SYNTHETIC_TEST,
        observed_at=NOW,
        reference="R4-A synthetic contract fixture",
    )


def _identity(
    *,
    provider_id: str = PROVIDER_ID,
    locality: ProviderLocality = ProviderLocality.LOCAL,
) -> ProviderIdentity:
    return ProviderIdentity(
        provider_id=provider_id,
        display_name="Synthetic Provider",
        locality=locality,
    )


def _provider_contract(
    *,
    identity: ProviderIdentity | None = None,
    privacy: frozenset[PrivacyClassification] | None = None,
    lifecycle: LifecycleStatus = LifecycleStatus.AVAILABLE,
) -> ProviderCapabilities:
    return ProviderCapabilities(
        identity=identity or _identity(),
        capabilities=frozenset(
            {AICapability.TEXT_GENERATION, AICapability.STRUCTURED_OUTPUT}
        ),
        permitted_privacy=privacy
        or frozenset(
            {
                PrivacyClassification.PUBLIC,
                PrivacyClassification.INTERNAL,
                PrivacyClassification.FINANCIAL,
            }
        ),
        lifecycle=lifecycle,
        evidence=_evidence(),
    )


def _model_contract(
    *,
    identity: ProviderIdentity | None = None,
    model_id: str = MODEL_ID,
    model_version: str | None = "synthetic-version-1",
    model_digest: str | None = "sha256:synthetic",
    lifecycle: LifecycleStatus = LifecycleStatus.AVAILABLE,
) -> ModelCapabilities:
    selected_identity = identity or _identity()
    return ModelCapabilities(
        provider_id=selected_identity.provider_id,
        model_id=model_id,
        model_version=model_version,
        model_digest=model_digest,
        locality=selected_identity.locality,
        capabilities=frozenset(
            {AICapability.TEXT_GENERATION, AICapability.STRUCTURED_OUTPUT}
        ),
        context_window_tokens=4096,
        max_output_tokens=512,
        lifecycle=lifecycle,
        evidence=_evidence(),
    )


def _schema(*, requires_sources: bool = True) -> CanonicalOutputSchema:
    return CanonicalOutputSchema(
        schema_id="synthetic.answer",
        version="1",
        root=OutputSchemaNode(
            value_type=OutputValueType.OBJECT,
            properties=(
                OutputProperty(
                    name="summary",
                    schema=OutputSchemaNode(OutputValueType.STRING),
                ),
                OutputProperty(
                    name="certified_amount",
                    schema=OutputSchemaNode(OutputValueType.DECIMAL_STRING),
                ),
            ),
        ),
        requires_source_references=requires_sources,
    )


def _consent(*, granted: bool = False) -> RemoteProcessingConsent:
    return RemoteProcessingConsent(
        granted=granted,
        policy_version="privacy-v1",
        decision_reference="consent-decision-1",
        resolved_at=NOW,
    )


def _request(
    *,
    execution_mode: ExecutionMode = ExecutionMode.LOCAL_ONLY,
    consent: RemoteProcessingConsent | None = None,
    privacy: PrivacyClassification = PrivacyClassification.FINANCIAL,
    schema: CanonicalOutputSchema | None = None,
) -> AIRequest:
    source = CertifiedSourceReference(
        reference_id=SOURCE_ID,
        source_type="DETERMINISTIC_ENGINE",
        owner="synthetic.engine",
        version="1",
        as_of_timestamp=NOW,
    )
    return AIRequest(
        request_id="request-0001",
        task=AITask(kind="SYNTHETIC_EXPLANATION", version="1"),
        user_scope=ServerUserScope(
            subject_id="subject-0001",
            authorization_context_id="auth-context-0001",
            resolved_at=NOW,
        ),
        privacy_classification=privacy,
        remote_processing_consent=consent or _consent(),
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
        output_schema=schema or _schema(),
        tool_budget=ToolBudget(),
        token_budget=TokenBudget(
            max_input_tokens=256,
            max_output_tokens=128,
            max_total_tokens=384,
        ),
        cost_budget=CostBudget(maximum=Decimal("0.50"), currency="BRL"),
        deadline_at=NOW + timedelta(minutes=1),
        policy_versions=(
            PolicyVersion(name="runtime", version="r4-a"),
            PolicyVersion(name="privacy", version="privacy-v1"),
        ),
        execution_mode=execution_mode,
    )


def _fake(
    *,
    identity: ProviderIdentity | None = None,
    model: ModelCapabilities | None = None,
    output: dict[str, object] | None = None,
    source_reference_ids: tuple[str, ...] = (SOURCE_ID,),
    mode: FakeProviderMode = FakeProviderMode.VALID,
    token_usage: TokenUsage | None = None,
    cost: CostUsage | None = None,
    tool_calls: tuple[ToolCallMetadata, ...] = (),
    supports_cancellation: bool = True,
) -> DeterministicFakeAIProvider:
    selected_identity = identity or _identity()
    selected_model = model or _model_contract(identity=selected_identity)
    return DeterministicFakeAIProvider(
        identity=selected_identity,
        models=(selected_model,),
        output=(
            output
            if output is not None
            else {"summary": "Synthetic explanation.", "certified_amount": "0.00"}
        ),
        source_reference_ids=source_reference_ids,
        mode=mode,
        token_usage=token_usage or TokenUsage(10, 5, 15),
        cost=cost or CostUsage(Decimal("0.00"), "BRL", False),
        tool_calls=tool_calls,
        completed_at=NOW,
        supports_cancellation=supports_cancellation,
    )


def _service(
    *,
    identity: ProviderIdentity | None = None,
    provider_contract: ProviderCapabilities | None = None,
    model: ModelCapabilities | None = None,
) -> ProviderNeutralAIService:
    selected_identity = identity or _identity()
    selected_provider = provider_contract or _provider_contract(identity=selected_identity)
    selected_model = model or _model_contract(identity=selected_identity)
    return ProviderNeutralAIService(
        ProviderCapabilityRegistry((selected_provider,)),
        ModelCapabilityRegistry((selected_model,)),
        clock=lambda: NOW,
    )


def test_ai_provider_is_sdk_free_abstract_async_contract() -> None:
    with pytest.raises(TypeError):
        AIProvider()
    assert inspect.iscoroutinefunction(AIProvider.discover_models)
    assert inspect.iscoroutinefunction(AIProvider.probe_health)
    assert inspect.iscoroutinefunction(AIProvider.generate)
    assert inspect.iscoroutinefunction(AIProvider.cancel)
    assert inspect.iscoroutinefunction(AIProvider.aclose)


def test_request_is_immutable_and_local_only_by_default() -> None:
    request = _request()
    assert request.execution_mode is ExecutionMode.LOCAL_ONLY
    with pytest.raises(FrozenInstanceError):
        request.execution_mode = ExecutionMode.HYBRID
    with pytest.raises(TypeError):
        request.context[0].value["amount"] = "99.00"


def test_request_requires_server_scope_contract_not_free_user_argument() -> None:
    request = _request()
    with pytest.raises(TypeError, match="server-resolved"):
        replace(request, user_scope="user-supplied")


def test_utc_is_explicit_for_scope_consent_sources_deadline_and_response() -> None:
    with pytest.raises(ValueError, match="UTC"):
        replace(_request(), deadline_at=datetime(2030, 1, 1, 12))
    with pytest.raises(ValueError, match="UTC"):
        replace(_consent(), resolved_at=datetime(2030, 1, 1, 12))
    assert _request().deadline_at.tzinfo is UTC


def test_privacy_and_remote_consent_are_explicit_contract_data() -> None:
    request = _request()
    assert request.privacy_classification is PrivacyClassification.FINANCIAL
    assert request.remote_processing_consent.granted is False
    assert request.remote_processing_consent.policy_version == "privacy-v1"
    with pytest.raises(ValueError, match="REMOTE_ONLY"):
        replace(request, execution_mode=ExecutionMode.REMOTE_ONLY)


def test_context_rejects_float_and_preserves_certified_decimal_text() -> None:
    entry = _request().context[0]
    assert entry.value["amount"] == "0.00"
    with pytest.raises(TypeError, match="float or Decimal"):
        AIContextEntry(key="bad", value={"amount": 0.0}, source_reference_ids=())
    with pytest.raises(TypeError, match="float or Decimal"):
        AIContextEntry(
            key="bad",
            value={"amount": Decimal("0.00")},
            source_reference_ids=(),
        )


def test_context_rejects_nonexistent_certified_source_reference() -> None:
    request = _request()
    bad_context = (
        AIContextEntry(
            key="bad_source",
            value="fact",
            source_reference_ids=("missing.source",),
        ),
    )
    with pytest.raises(ValueError, match="unknown source"):
        replace(request, context=bad_context)


def test_provider_and_model_registries_are_immutable_exact_snapshots() -> None:
    provider_registry = ProviderCapabilityRegistry((_provider_contract(),))
    model_registry = ModelCapabilityRegistry((_model_contract(),))
    assert provider_registry.require(PROVIDER_ID).identity.provider_id == PROVIDER_ID
    assert model_registry.require(PROVIDER_ID, MODEL_ID).model_id == MODEL_ID
    with pytest.raises(TypeError):
        provider_registry.providers["other"] = _provider_contract()
    with pytest.raises(TypeError):
        model_registry.models[(PROVIDER_ID, "other")] = _model_contract()


def test_unregistered_provider_and_model_fail_with_typed_errors() -> None:
    provider_registry = ProviderCapabilityRegistry(())
    model_registry = ModelCapabilityRegistry(())
    with pytest.raises(AIContractError) as provider_failure:
        provider_registry.require("not-authorized")
    assert provider_failure.value.code is AIErrorCode.PROVIDER_UNAVAILABLE
    with pytest.raises(AIContractError) as model_failure:
        model_registry.require(PROVIDER_ID, "not-authorized")
    assert model_failure.value.code is AIErrorCode.MODEL_UNAVAILABLE


def test_model_version_and_digest_are_never_presumed() -> None:
    model = _model_contract(model_version=None, model_digest=None)
    assert model.model_version is None
    assert model.model_digest is None


@pytest.mark.asyncio
async def test_free_form_invalid_model_id_becomes_safe_typed_request_error() -> None:
    fake = _fake()
    with pytest.raises(AIContractError) as failure:
        await _service().generate(_request(), provider=fake, model_id="model with spaces")
    assert failure.value.code is AIErrorCode.INVALID_REQUEST
    assert failure.value.metadata.field == "model_id"
    assert fake.generate_calls == 0


def test_error_taxonomy_is_closed_and_messages_are_safe() -> None:
    assert {code.value for code in AIErrorCode} == {
        "INVALID_REQUEST",
        "AUTHORIZATION_DENIED",
        "PRIVACY_POLICY_DENIED",
        "CAPABILITY_UNSUPPORTED",
        "PROVIDER_UNAVAILABLE",
        "MODEL_UNAVAILABLE",
        "QUOTA_EXHAUSTED",
        "RATE_LIMITED",
        "PROVIDER_OVERLOADED",
        "TIMEOUT",
        "OUTPUT_SCHEMA_INVALID",
        "OUTPUT_SOURCE_INVALID",
        "TOOL_DENIED",
        "TOKEN_BUDGET_EXCEEDED",
        "COST_BUDGET_EXCEEDED",
        "CANCELLED",
        "INTERNAL_FAILURE",
    }
    error = AIContractError(AIErrorCode.PROVIDER_UNAVAILABLE)
    assert "provider" in str(error).lower()
    assert "key" not in str(error).lower()
    assert not hasattr(error, "raw_response")


@pytest.mark.asyncio
async def test_valid_fake_response_is_strictly_validated_and_immutable() -> None:
    response = await _service().generate(
        _request(),
        provider=_fake(),
        model_id=MODEL_ID,
    )
    assert response.structured_output == {
        "summary": "Synthetic explanation.",
        "certified_amount": "0.00",
    }
    assert response.structured_output["certified_amount"] == "0.00"
    assert response.cost.amount == Decimal("0.00")
    assert response.validation.structure is StructureValidationStatus.VALID
    assert response.validation.factual is FactualValidationStatus.NOT_PERFORMED
    assert AIWarningCode.FACTUAL_VALIDATION_NOT_PERFORMED in response.warnings
    with pytest.raises(TypeError):
        response.structured_output["summary"] = "mutated"


@pytest.mark.asyncio
async def test_extra_output_field_is_rejected_integrally() -> None:
    fake = _fake(
        output={
            "summary": "Synthetic explanation.",
            "certified_amount": "0.00",
            "unauthorized": "extra",
        }
    )
    with pytest.raises(AIContractError) as failure:
        await _service().generate(_request(), provider=fake, model_id=MODEL_ID)
    assert failure.value.code is AIErrorCode.OUTPUT_SCHEMA_INVALID


@pytest.mark.asyncio
async def test_missing_required_field_and_wrong_type_are_rejected() -> None:
    for output in (
        {"summary": "Missing amount."},
        {"summary": "Wrong amount.", "certified_amount": 0},
    ):
        with pytest.raises(AIContractError) as failure:
            await _service().generate(
                _request(),
                provider=_fake(output=output),
                model_id=MODEL_ID,
            )
        assert failure.value.code is AIErrorCode.OUTPUT_SCHEMA_INVALID


@pytest.mark.asyncio
async def test_unknown_or_missing_output_source_reference_is_rejected() -> None:
    for source_ids in (("missing.source",), ()):
        with pytest.raises(AIContractError) as failure:
            await _service().generate(
                _request(),
                provider=_fake(source_reference_ids=source_ids),
                model_id=MODEL_ID,
            )
        assert failure.value.code is AIErrorCode.OUTPUT_SOURCE_INVALID


@pytest.mark.asyncio
async def test_fake_invalid_schema_mode_is_rejected_not_returned_partially() -> None:
    with pytest.raises(AIContractError) as failure:
        await _service().generate(
            _request(),
            provider=_fake(mode=FakeProviderMode.INVALID_SCHEMA),
            model_id=MODEL_ID,
        )
    assert failure.value.code is AIErrorCode.OUTPUT_SCHEMA_INVALID


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mode", "expected_code"),
    [
        (FakeProviderMode.TIMEOUT, AIErrorCode.TIMEOUT),
        (FakeProviderMode.UNAVAILABLE, AIErrorCode.PROVIDER_UNAVAILABLE),
        (FakeProviderMode.RATE_LIMITED, AIErrorCode.RATE_LIMITED),
        (FakeProviderMode.CANCELLED, AIErrorCode.CANCELLED),
    ],
)
async def test_fake_provider_simulates_typed_failures(
    mode: FakeProviderMode,
    expected_code: AIErrorCode,
) -> None:
    with pytest.raises(AIContractError) as failure:
        await _service().generate(
            _request(),
            provider=_fake(mode=mode),
            model_id=MODEL_ID,
        )
    assert failure.value.code is expected_code


@pytest.mark.asyncio
async def test_fake_provider_cancellation_and_close_are_explicit() -> None:
    request = _request()
    fake = _fake()
    assert await fake.cancel(request.request_id) is CancellationResult.CANCELLED
    with pytest.raises(AIContractError) as cancelled:
        await _service().generate(request, provider=fake, model_id=MODEL_ID)
    assert cancelled.value.code is AIErrorCode.CANCELLED

    unsupported = _fake(supports_cancellation=False)
    assert await unsupported.cancel(request.request_id) is CancellationResult.NOT_SUPPORTED
    await unsupported.aclose()
    health = await unsupported.probe_health(MODEL_ID)
    assert health.status.value == "UNAVAILABLE"


@pytest.mark.asyncio
async def test_fake_provider_reports_deterministic_usage_and_decimal_cost() -> None:
    fake = _fake(
        token_usage=TokenUsage(input_tokens=7, output_tokens=3, total_tokens=10),
        cost=CostUsage(amount=Decimal("0.1250"), currency="BRL", estimated=True),
    )
    response = await _service().generate(
        _request(), provider=fake, model_id=MODEL_ID
    )
    assert response.token_usage == TokenUsage(7, 3, 10)
    assert response.cost.amount == Decimal("0.1250")
    assert str(response.cost.amount) == "0.1250"
    assert response.retry == RetryMetadata(total_attempts=1)
    assert response.fallback == FallbackMetadata()


@pytest.mark.asyncio
async def test_unknown_provider_evidence_stays_optional_and_warned() -> None:
    model = _model_contract(model_version=None, model_digest=None)
    fake = DeterministicFakeAIProvider(
        identity=_identity(),
        models=(model,),
        output={"summary": "Synthetic explanation.", "certified_amount": "0.00"},
        source_reference_ids=(SOURCE_ID,),
        token_usage=TokenUsage(),
        cost=CostUsage(),
        completed_at=NOW,
    )
    response = await _service(model=model).generate(
        _request(), provider=fake, model_id=MODEL_ID
    )
    assert response.model_version is None
    assert response.model_digest is None
    assert response.token_usage.total_tokens is None
    assert response.cost.amount is None
    assert {
        AIWarningCode.MODEL_VERSION_UNKNOWN,
        AIWarningCode.TOKEN_USAGE_UNKNOWN,
        AIWarningCode.COST_UNKNOWN,
    }.issubset(response.warnings)


@pytest.mark.asyncio
async def test_unallowlisted_tool_metadata_is_rejected_without_execution() -> None:
    fake = _fake(
        tool_calls=(
            ToolCallMetadata(
                call_id="tool-call-1",
                tool_id="financial.write",
                status=ToolCallStatus.REQUESTED,
            ),
        )
    )
    with pytest.raises(AIContractError) as failure:
        await _service().generate(_request(), provider=fake, model_id=MODEL_ID)
    assert failure.value.code is AIErrorCode.TOOL_DENIED


@pytest.mark.asyncio
async def test_budget_overruns_fail_typed_without_retry_or_fallback() -> None:
    token_fake = _fake(token_usage=TokenUsage(257, 1, 258))
    with pytest.raises(AIContractError) as token_failure:
        await _service().generate(_request(), provider=token_fake, model_id=MODEL_ID)
    assert token_failure.value.code is AIErrorCode.TOKEN_BUDGET_EXCEEDED

    cost_fake = _fake(cost=CostUsage(Decimal("0.51"), "BRL", False))
    with pytest.raises(AIContractError) as cost_failure:
        await _service().generate(_request(), provider=cost_fake, model_id=MODEL_ID)
    assert cost_failure.value.code is AIErrorCode.COST_BUDGET_EXCEEDED


@pytest.mark.asyncio
async def test_expired_deadline_stops_before_provider_generation() -> None:
    fake = _fake()
    request = replace(_request(), deadline_at=NOW)
    with pytest.raises(AIContractError) as failure:
        await _service().generate(request, provider=fake, model_id=MODEL_ID)
    assert failure.value.code is AIErrorCode.TIMEOUT
    assert fake.generate_calls == 0


@pytest.mark.asyncio
async def test_local_only_never_invokes_remote_provider() -> None:
    identity = _identity(provider_id="synthetic.remote", locality=ProviderLocality.REMOTE)
    model = _model_contract(identity=identity)
    provider_contract = _provider_contract(identity=identity)
    fake = _fake(identity=identity, model=model)
    with pytest.raises(AIContractError) as failure:
        await _service(
            identity=identity,
            provider_contract=provider_contract,
            model=model,
        ).generate(_request(), provider=fake, model_id=MODEL_ID)
    assert failure.value.code is AIErrorCode.PRIVACY_POLICY_DENIED
    assert fake.generate_calls == 0


@pytest.mark.asyncio
async def test_remote_provider_requires_resolved_consent_and_permitted_privacy() -> None:
    identity = _identity(provider_id="synthetic.remote", locality=ProviderLocality.REMOTE)
    model = _model_contract(identity=identity)
    public_only = _provider_contract(
        identity=identity,
        privacy=frozenset({PrivacyClassification.PUBLIC}),
    )
    fake = _fake(identity=identity, model=model)
    request = _request(
        execution_mode=ExecutionMode.REMOTE_ONLY,
        consent=_consent(granted=True),
        privacy=PrivacyClassification.FINANCIAL,
    )
    with pytest.raises(AIContractError) as failure:
        await _service(
            identity=identity,
            provider_contract=public_only,
            model=model,
        ).generate(request, provider=fake, model_id=MODEL_ID)
    assert failure.value.code is AIErrorCode.PRIVACY_POLICY_DENIED
    assert fake.generate_calls == 0


@pytest.mark.asyncio
async def test_unavailable_model_and_unsupported_capability_stop_before_generate() -> None:
    unavailable = _model_contract(lifecycle=LifecycleStatus.UNAVAILABLE)
    fake = _fake(model=unavailable)
    with pytest.raises(AIContractError) as unavailable_failure:
        await _service(model=unavailable).generate(
            _request(), provider=fake, model_id=MODEL_ID
        )
    assert unavailable_failure.value.code is AIErrorCode.MODEL_UNAVAILABLE
    assert fake.generate_calls == 0

    request = replace(
        _request(),
        required_capabilities=frozenset(
            {
                AICapability.TEXT_GENERATION,
                AICapability.STRUCTURED_OUTPUT,
                AICapability.TOOL_CALLING,
            }
        ),
    )
    capable_fake = _fake()
    with pytest.raises(AIContractError) as capability_failure:
        await _service().generate(request, provider=capable_fake, model_id=MODEL_ID)
    assert capability_failure.value.code is AIErrorCode.CAPABILITY_UNSUPPORTED
    assert capable_fake.generate_calls == 0


@pytest.mark.asyncio
async def test_fake_provider_performs_no_network_call(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def forbidden_connect(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("network access is forbidden in R4-A")

    monkeypatch.setattr(socket.socket, "connect", forbidden_connect)
    response = await _service().generate(
        _request(), provider=_fake(), model_id=MODEL_ID
    )
    assert response.finish_reason is FinishReason.COMPLETED
    assert calls == []


def test_r4_a_runtime_has_no_provider_sdk_or_database_write_imports() -> None:
    forbidden_fragments = (
        "google.genai",
        "google.generativeai",
        "import ollama",
        "from ollama",
        "backend.database",
        "sqlalchemy",
        "backend.core.config",
        "os.environ",
        "httpx",
        "requests",
        "ai_runs",
    )
    for path in RUNTIME_FILES:
        source = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_fragments:
            assert fragment not in source, f"{fragment!r} found in {path}"
    assert "google.genai" not in sys.modules
    assert "google.generativeai" not in sys.modules
    assert "ollama" not in sys.modules
