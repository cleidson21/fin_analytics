"""Deterministic volatile sinks for R4-C tests; never durable audit evidence."""

from __future__ import annotations

from backend.application.ai_runtime.audit import AIAuditEvent
from backend.application.ai_runtime.telemetry import AITelemetryMetric
from backend.application.ports.ai_audit_telemetry import (
    AIAuditSink,
    AITelemetrySink,
    AuditGuarantee,
)


class InMemoryAIAuditSink(AIAuditSink):
    def __init__(self) -> None:
        self._events: list[AIAuditEvent] = []

    @property
    def guarantee(self) -> AuditGuarantee:
        return AuditGuarantee.VOLATILE

    def emit(self, event: AIAuditEvent) -> None:
        if not isinstance(event, AIAuditEvent):
            raise TypeError("event must be AIAuditEvent.")
        self._events.append(event)

    @property
    def events(self) -> tuple[AIAuditEvent, ...]:
        return tuple(self._events)


class InMemoryAITelemetrySink(AITelemetrySink):
    def __init__(self) -> None:
        self._metrics: list[AITelemetryMetric] = []

    def emit(self, metric: AITelemetryMetric) -> None:
        if not isinstance(metric, AITelemetryMetric):
            raise TypeError("metric must be AITelemetryMetric.")
        self._metrics.append(metric)

    @property
    def metrics(self) -> tuple[AITelemetryMetric, ...]:
        return tuple(self._metrics)
