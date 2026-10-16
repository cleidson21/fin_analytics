"""Fail-closed mandatory audit emission and isolated optional telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.application.ai_runtime.audit import AIAuditEvent
from backend.application.ai_runtime.contracts import ExecutionMode
from backend.application.ai_runtime.telemetry import AITelemetryMetric
from backend.application.ports.ai_audit_telemetry import (
    AIAuditSink,
    AITelemetrySink,
    AuditGuarantee,
)
from backend.domain.exceptions.base import FINAnalyticsError


class AuditEmissionErrorCode(str, Enum):
    REQUIRED_GUARANTEE_UNAVAILABLE = "REQUIRED_GUARANTEE_UNAVAILABLE"
    REQUIRED_AUDIT_EMISSION_FAILED = "REQUIRED_AUDIT_EMISSION_FAILED"


_SAFE_AUDIT_MESSAGES = {
    AuditEmissionErrorCode.REQUIRED_GUARANTEE_UNAVAILABLE: (
        "The required AI audit guarantee is unavailable."
    ),
    AuditEmissionErrorCode.REQUIRED_AUDIT_EMISSION_FAILED: (
        "The required AI audit event could not be recorded."
    ),
}


class RequiredAuditError(FINAnalyticsError):
    """Safe failure that never includes sink exceptions or event payloads."""

    def __init__(self, code: AuditEmissionErrorCode) -> None:
        if not isinstance(code, AuditEmissionErrorCode):
            raise TypeError("code must be AuditEmissionErrorCode.")
        super().__init__(_SAFE_AUDIT_MESSAGES[code])
        self.code = code


class TelemetryEmissionStatus(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    EMITTED = "EMITTED"
    FAILED_OPTIONAL = "FAILED_OPTIONAL"


@dataclass(frozen=True)
class AuditTelemetryEmissionResult:
    audit_emitted: bool
    telemetry_status: TelemetryEmissionStatus
    emitted_metric_count: int
    failed_metric_count: int

    def __post_init__(self) -> None:
        if type(self.audit_emitted) is not bool:
            raise TypeError("audit_emitted must be a strict boolean.")
        for field_name in ("emitted_metric_count", "failed_metric_count"):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field_name} must be a non-negative strict integer.")
        if not isinstance(self.telemetry_status, TelemetryEmissionStatus):
            raise TypeError("telemetry_status must be TelemetryEmissionStatus.")


def required_audit_guarantee(event: AIAuditEvent) -> AuditGuarantee:
    """Remote execution or effective tool use requires durability by contract."""

    if not isinstance(event, AIAuditEvent):
        raise TypeError("event must be AIAuditEvent.")
    if (
        event.execution_mode is not ExecutionMode.LOCAL_ONLY
        or event.authorized_tool_ids
        or event.tool_executions
    ):
        return AuditGuarantee.DURABLE
    return AuditGuarantee.VOLATILE


class AIAuditTelemetryEmitter:
    def __init__(
        self,
        *,
        audit_sink: AIAuditSink,
        telemetry_sink: AITelemetrySink | None = None,
    ) -> None:
        if not isinstance(audit_sink, AIAuditSink):
            raise TypeError("audit_sink must implement AIAuditSink.")
        if telemetry_sink is not None and not isinstance(telemetry_sink, AITelemetrySink):
            raise TypeError("telemetry_sink must implement AITelemetrySink.")
        self._audit_sink = audit_sink
        self._telemetry_sink = telemetry_sink

    def emit(
        self,
        event: AIAuditEvent,
        *,
        metrics: tuple[AITelemetryMetric, ...] = (),
    ) -> AuditTelemetryEmissionResult:
        if not isinstance(event, AIAuditEvent):
            raise TypeError("event must be AIAuditEvent.")
        if type(metrics) is not tuple or any(
            not isinstance(metric, AITelemetryMetric) for metric in metrics
        ):
            raise TypeError("metrics must contain AITelemetryMetric values.")
        for metric in metrics:
            if (
                metric.request_id != event.request_id
                or metric.correlation_id != event.correlation_id
            ):
                raise ValueError("telemetry correlation does not match the audit event.")

        try:
            supplied_guarantee = self._audit_sink.guarantee
        except Exception:
            raise RequiredAuditError(
                AuditEmissionErrorCode.REQUIRED_GUARANTEE_UNAVAILABLE
            ) from None
        if not isinstance(supplied_guarantee, AuditGuarantee):
            raise RequiredAuditError(
                AuditEmissionErrorCode.REQUIRED_GUARANTEE_UNAVAILABLE
            )
        if supplied_guarantee < required_audit_guarantee(event):
            raise RequiredAuditError(
                AuditEmissionErrorCode.REQUIRED_GUARANTEE_UNAVAILABLE
            )
        try:
            self._audit_sink.emit(event)
        except Exception:
            raise RequiredAuditError(
                AuditEmissionErrorCode.REQUIRED_AUDIT_EMISSION_FAILED
            ) from None

        if not metrics:
            return AuditTelemetryEmissionResult(
                audit_emitted=True,
                telemetry_status=TelemetryEmissionStatus.NOT_REQUESTED,
                emitted_metric_count=0,
                failed_metric_count=0,
            )

        emitted = 0
        failed = 0
        for metric in metrics:
            if self._telemetry_sink is None:
                failed += 1
                continue
            try:
                self._telemetry_sink.emit(metric)
            except Exception:
                failed += 1
            else:
                emitted += 1
        return AuditTelemetryEmissionResult(
            audit_emitted=True,
            telemetry_status=(
                TelemetryEmissionStatus.FAILED_OPTIONAL
                if failed
                else TelemetryEmissionStatus.EMITTED
            ),
            emitted_metric_count=emitted,
            failed_metric_count=failed,
        )
