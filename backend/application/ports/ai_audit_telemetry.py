"""Replaceable no-persistence ports for AI audit and optional telemetry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum

from backend.application.ai_runtime.audit import AIAuditEvent
from backend.application.ai_runtime.telemetry import AITelemetryMetric


class AuditGuarantee(IntEnum):
    VOLATILE = 1
    DURABLE = 2


class AIAuditSink(ABC):
    @property
    @abstractmethod
    def guarantee(self) -> AuditGuarantee:
        """Return the strongest guarantee actually supplied by this sink."""
        ...

    @abstractmethod
    def emit(self, event: AIAuditEvent) -> None:
        """Emit one mandatory audit event or raise without exposing payloads."""
        ...


class AITelemetrySink(ABC):
    @abstractmethod
    def emit(self, metric: AITelemetryMetric) -> None:
        """Emit one optional metric; callers decide how failures are isolated."""
        ...
