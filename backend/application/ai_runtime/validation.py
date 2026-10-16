"""Strict local validation from untrusted provider result to canonical response."""

from __future__ import annotations

from typing import Mapping

from backend.application.ai_runtime.contracts import (
    AIProviderResult,
    AIRequest,
    AIResponse,
    AIWarningCode,
    CanonicalValue,
    FactualValidationStatus,
    OutputSchemaNode,
    OutputValueType,
    StructureValidationStatus,
    ToolCallStatus,
    ValidationSummary,
    is_decimal_string,
)
from backend.application.ai_runtime.errors import (
    AIContractError,
    AIErrorCode,
    AIErrorMetadata,
)


class CanonicalOutputValidator:
    """Validates structure and citations; factual/tool validation remains R4-B."""

    def validate(
        self,
        request: AIRequest,
        result: AIProviderResult,
        *,
        expected_provider_id: str,
        expected_model_id: str,
    ) -> AIResponse:
        if not isinstance(request, AIRequest):
            raise TypeError("request must be AIRequest.")
        if not isinstance(result, AIProviderResult):
            raise TypeError("result must be AIProviderResult.")

        metadata = AIErrorMetadata(
            request_id=request.request_id,
            provider_id=expected_provider_id,
            model_id=expected_model_id,
        )
        if (
            result.provider_id != expected_provider_id
            or result.model_id != expected_model_id
        ):
            raise AIContractError(AIErrorCode.INVALID_REQUEST, metadata=metadata)

        self._validate_node(
            request.output_schema.root,
            result.structured_output,
            path="structured_output",
            metadata=metadata,
        )

        request_sources = {
            source.reference_id: source for source in request.source_references
        }
        unknown_sources = set(result.source_reference_ids) - set(request_sources)
        if unknown_sources:
            raise AIContractError(
                AIErrorCode.OUTPUT_SOURCE_INVALID,
                metadata=AIErrorMetadata(
                    request_id=request.request_id,
                    provider_id=expected_provider_id,
                    model_id=expected_model_id,
                    field="source_reference_ids",
                ),
            )
        if (
            request.output_schema.requires_source_references
            and not result.source_reference_ids
        ):
            raise AIContractError(
                AIErrorCode.OUTPUT_SOURCE_INVALID,
                metadata=AIErrorMetadata(
                    request_id=request.request_id,
                    provider_id=expected_provider_id,
                    model_id=expected_model_id,
                    field="source_reference_ids",
                ),
            )

        if len(result.tool_calls) > request.tool_budget.max_calls:
            raise AIContractError(AIErrorCode.TOOL_DENIED, metadata=metadata)
        for tool_call in result.tool_calls:
            if (
                tool_call.tool_id not in request.tool_budget.allowed_tool_ids
                or tool_call.status is not ToolCallStatus.REQUESTED
            ):
                raise AIContractError(
                    AIErrorCode.TOOL_DENIED,
                    metadata=AIErrorMetadata(
                        request_id=request.request_id,
                        provider_id=expected_provider_id,
                        model_id=expected_model_id,
                        field="tool_calls",
                    ),
                )

        usage = result.token_usage
        if (
            usage.input_tokens is not None
            and usage.input_tokens > request.token_budget.max_input_tokens
        ) or (
            usage.output_tokens is not None
            and usage.output_tokens > request.token_budget.max_output_tokens
        ) or (
            usage.total_tokens is not None
            and usage.total_tokens > request.token_budget.max_total_tokens
        ):
            raise AIContractError(AIErrorCode.TOKEN_BUDGET_EXCEEDED, metadata=metadata)

        if result.cost.amount is not None:
            if (
                result.cost.currency != request.cost_budget.currency
                or result.cost.amount > request.cost_budget.maximum
            ):
                raise AIContractError(
                    AIErrorCode.COST_BUDGET_EXCEEDED,
                    metadata=metadata,
                )

        warnings = list(result.warnings)
        for warning in (
            (
                AIWarningCode.MODEL_VERSION_UNKNOWN
                if result.model_version is None and result.model_digest is None
                else None
            ),
            AIWarningCode.TOKEN_USAGE_UNKNOWN if not usage.is_known else None,
            AIWarningCode.COST_UNKNOWN if not result.cost.is_known else None,
            AIWarningCode.FACTUAL_VALIDATION_NOT_PERFORMED,
        ):
            if warning is not None and warning not in warnings:
                warnings.append(warning)

        return AIResponse(
            request_id=request.request_id,
            provider_id=result.provider_id,
            model_id=result.model_id,
            model_version=result.model_version,
            model_digest=result.model_digest,
            structured_output=result.structured_output,
            source_references=tuple(
                request_sources[reference_id]
                for reference_id in result.source_reference_ids
            ),
            tool_calls=result.tool_calls,
            token_usage=result.token_usage,
            latency=result.latency,
            cost=result.cost,
            finish_reason=result.finish_reason,
            validation=ValidationSummary(
                structure=StructureValidationStatus.VALID,
                factual=FactualValidationStatus.NOT_PERFORMED,
            ),
            retry=result.retry,
            fallback=result.fallback,
            warnings=tuple(warnings),
            completed_at=result.completed_at,
        )

    def _validate_node(
        self,
        schema: OutputSchemaNode,
        value: CanonicalValue,
        *,
        path: str,
        metadata: AIErrorMetadata,
    ) -> None:
        try:
            self._validate_node_or_raise(schema, value, path=path)
        except (TypeError, ValueError):
            raise AIContractError(
                AIErrorCode.OUTPUT_SCHEMA_INVALID,
                metadata=AIErrorMetadata(
                    request_id=metadata.request_id,
                    provider_id=metadata.provider_id,
                    model_id=metadata.model_id,
                    field=path,
                ),
            ) from None

    def _validate_node_or_raise(
        self,
        schema: OutputSchemaNode,
        value: CanonicalValue,
        *,
        path: str,
    ) -> None:
        value_type = schema.value_type
        if value_type is OutputValueType.STRING:
            if type(value) is not str:
                raise TypeError(path)
            return
        if value_type is OutputValueType.DECIMAL_STRING:
            if not is_decimal_string(value):
                raise TypeError(path)
            return
        if value_type is OutputValueType.INTEGER:
            if type(value) is not int:
                raise TypeError(path)
            return
        if value_type is OutputValueType.BOOLEAN:
            if type(value) is not bool:
                raise TypeError(path)
            return
        if value_type is OutputValueType.NULL:
            if value is not None:
                raise TypeError(path)
            return
        if value_type is OutputValueType.ARRAY:
            if type(value) is not tuple or schema.item_schema is None:
                raise TypeError(path)
            for index, item in enumerate(value):
                self._validate_node_or_raise(
                    schema.item_schema,
                    item,
                    path=f"{path}[{index}]",
                )
            return
        if value_type is OutputValueType.OBJECT:
            if not isinstance(value, Mapping):
                raise TypeError(path)
            property_map = {item.name: item for item in schema.properties}
            if set(value) - set(property_map):
                raise ValueError(path)
            missing = {
                name
                for name, item in property_map.items()
                if item.required and name not in value
            }
            if missing:
                raise ValueError(path)
            for name, item in property_map.items():
                if name in value:
                    self._validate_node_or_raise(
                        item.schema,
                        value[name],
                        path=f"{path}.{name}",
                    )
            return
        raise TypeError(path)
