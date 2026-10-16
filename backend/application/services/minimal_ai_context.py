"""Minimum certified context projection for approved R4-B read-only tools."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID

from backend.application.ai_runtime.contracts import (
    AIContextEntry,
    CertifiedSourceReference,
)
from backend.application.ai_runtime.errors import (
    AIContractError,
    AIErrorCode,
    AIErrorMetadata,
)
from backend.application.ai_runtime.tool_contracts import (
    ContextCompleteness,
    ToolExecutionResult,
    ToolProvenanceContract,
    ToolResultStatus,
)
from backend.domains.planning.facts import GoalPlanningFact
from backend.domains.smart_context import SmartFeatureContext, SmartValue


def _canonical_scalar(value: object) -> str | int | bool | None:
    if value is None or type(value) in {str, int, bool}:
        return value  # type: ignore[return-value]
    if type(value) is Decimal:
        return str(value)
    if type(value) in {date, datetime}:
        return value.isoformat()  # type: ignore[union-attr]
    if isinstance(value, Enum):
        return str(value.value)
    raise TypeError("certified context contains an unsupported scalar type.")


def _optional_scalar_field(target: dict[str, object], name: str, value: object) -> None:
    if value is not None:
        target[name] = _canonical_scalar(value)


class MinimalAIContextBuilder:
    """Project certified readers without raw records, recalculation, or inference."""

    SMART_CONTEXT_VERSION = "r2-b5"
    GOAL_READER_VERSION = "planning-goal-read-v1"

    def build_smart_context(
        self,
        *,
        tool_id: str,
        tool_version: str,
        context: SmartFeatureContext,
        expected_feature: object,
        resolved_at: datetime,
        provenance: ToolProvenanceContract,
    ) -> ToolExecutionResult:
        if not isinstance(context, SmartFeatureContext):
            raise TypeError("context must be SmartFeatureContext.")
        if context.feature is not expected_feature:
            raise AIContractError(AIErrorCode.INTERNAL_FAILURE)
        timestamp = self._require_utc(resolved_at)

        references = tuple(
            CertifiedSourceReference(
                reference_id=f"{tool_id}:source:{index}",
                source_type=value.source.value,
                owner=value.owner.value,
                version=self.SMART_CONTEXT_VERSION,
                as_of_timestamp=timestamp,
            )
            for index, value in enumerate(context.values)
        )
        payload = {
            "content_trust": "UNTRUSTED_DATA",
            "consumer": tool_id,
            "feature": context.feature.value,
            "as_of_date": context.as_of_date.isoformat(),
            "values": tuple(
                self._smart_value_payload(value) for value in context.values
            ),
        }
        entry = AIContextEntry(
            key=f"{tool_id}.result",
            value=payload,
            source_reference_ids=tuple(item.reference_id for item in references),
        )
        available_count = sum(value.value is not None for value in context.values)
        completeness = (
            ContextCompleteness.UNAVAILABLE
            if available_count == 0
            else ContextCompleteness.COMPLETE
            if available_count == len(context.values)
            else ContextCompleteness.PARTIAL
        )
        return ToolExecutionResult(
            tool_id=tool_id,
            tool_version=tool_version,
            status=ToolResultStatus.SUCCESS,
            completeness=completeness,
            context=(entry,),
            source_references=references,
            provenance=provenance,
        )

    def build_owned_goal(
        self,
        *,
        tool_id: str,
        tool_version: str,
        goal: GoalPlanningFact | None,
        authenticated_user_id: UUID,
        resolved_at: datetime,
        provenance: ToolProvenanceContract,
        request_id: str,
    ) -> ToolExecutionResult:
        if goal is None or goal.user_id != authenticated_user_id:
            raise AIContractError(
                AIErrorCode.AUTHORIZATION_DENIED,
                metadata=AIErrorMetadata(request_id=request_id),
            )
        timestamp = self._require_utc(resolved_at)
        reference = CertifiedSourceReference(
            reference_id=f"{tool_id}:source:0",
            source_type="GOAL",
            owner="GOALS",
            version=self.GOAL_READER_VERSION,
            as_of_timestamp=timestamp,
        )
        goal_payload: dict[str, object] = {
            "content_trust": "UNTRUSTED_DATA",
            "consumer": tool_id,
            "goal_id": str(goal.goal_id),
            "name": goal.name,
            "description": goal.description,
            "goal_type": goal.goal_type.value,
            "status": goal.status.value,
            "target_amount": str(goal.target_amount),
            "target_date": None if goal.target_date is None else goal.target_date.isoformat(),
            "current_amount": None if goal.current_amount is None else str(goal.current_amount),
            "planned_monthly_contribution": (
                None
                if goal.goal_planned_monthly_contribution is None
                else str(goal.goal_planned_monthly_contribution)
            ),
            "priority": goal.priority,
            "created_at": goal.created_at.isoformat(),
            "updated_at": goal.updated_at.isoformat(),
        }
        entry = AIContextEntry(
            key=f"{tool_id}.result",
            value=goal_payload,
            source_reference_ids=(reference.reference_id,),
        )
        return ToolExecutionResult(
            tool_id=tool_id,
            tool_version=tool_version,
            status=ToolResultStatus.SUCCESS,
            completeness=ContextCompleteness.COMPLETE,
            context=(entry,),
            source_references=(reference,),
            provenance=provenance,
        )

    @staticmethod
    def _smart_value_payload(value: SmartValue) -> dict[str, object]:
        payload: dict[str, object] = {
            "key": value.key.value,
            "value": _canonical_scalar(value.value),
            "value_type": value.value_type.value,
            "semantic_type": value.semantic_type.value,
            "owner": value.owner.value,
            "source": value.source.value,
            "source_label": value.source_label,
            "state": value.state.value,
            "override_policy": value.override_policy.value,
        }
        if value.scope is not None:
            payload["scope"] = {
                "kind": value.scope.kind,
                "reference": value.scope.reference,
            }
        for name, field_value in (
            ("observed_at", value.observed_at),
            ("declared_at", value.declared_at),
            ("reference_period", value.reference_period),
            ("freshness", value.freshness),
            ("confirmation_status", value.confirmation_status),
            ("unavailable_reason", value.unavailable_reason),
            ("reason", value.reason),
            ("offered_value", value.offered_value),
            ("effective_value", value.effective_value),
            ("override_reason", value.override_reason),
        ):
            _optional_scalar_field(payload, name, field_value)
        if value.evidence is not None:
            payload["evidence"] = {
                "window_start": value.evidence.window_start.isoformat(),
                "window_end": value.evidence.window_end.isoformat(),
                "first_occurrence_date": value.evidence.first_occurrence_date.isoformat(),
                "latest_occurrence_date": value.evidence.latest_occurrence_date.isoformat(),
                "occurrence_count": value.evidence.occurrence_count,
                "distinct_month_count": value.evidence.distinct_month_count,
                "typical_received_amount": str(value.evidence.typical_received_amount),
                "risk_flags": value.evidence.risk_flags,
            }
        return payload

    @staticmethod
    def _require_utc(value: datetime) -> datetime:
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise TypeError("resolved_at must be timezone-aware.")
        return value.astimezone(timezone.utc)
