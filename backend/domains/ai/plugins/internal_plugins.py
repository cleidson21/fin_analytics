from backend.domains.ai.plugins.plugin_models import PluginMetadata, PluginStatus
from backend.domains.ai.events.event_registry import EventRegistry

class BaseInternalPlugin:
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self.status = PluginStatus()

    def initialize(self) -> None:
        pass

    def execute(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def health(self) -> bool:
        return True

class InternalEventBusPlugin(BaseInternalPlugin):
    def __init__(self):
        super().__init__(PluginMetadata(
            plugin_id="internal-event-bus",
            name="Internal Event Bus",
            version="1.0.0",
            description="Barramento Interno de Eventos",
            author="System",
            entrypoint="backend.domains.ai.events.event_bus"
        ))

    def initialize(self) -> None:
        # Registra todos os eventos aqui, substituindo a chamada direta no main.py
        EventRegistry.register_all()

class AIWorkflowPlugin(BaseInternalPlugin):
    def __init__(self):
        super().__init__(PluginMetadata(
            plugin_id="ai-workflow",
            name="AI Workflow Engine",
            version="1.0.0",
            description="Orquestrador de Pipelines Internos",
            author="System",
            entrypoint="backend.domains.ai.workflow.workflow_service"
        ))

class AIDashboardPlugin(BaseInternalPlugin):
    def __init__(self):
        super().__init__(PluginMetadata(
            plugin_id="ai-dashboard",
            name="AI Dashboard Delivery Layer",
            version="1.0.0",
            description="Camada de entrega para o Dashboard",
            author="System",
            entrypoint="backend.domains.ai.dashboard.dashboard_service"
        ))

class AIOrchestratorPlugin(BaseInternalPlugin):
    def __init__(self):
        super().__init__(PluginMetadata(
            plugin_id="ai-orchestrator",
            name="AI Orchestrator Engine",
            version="1.0.0",
            description="Orquestrador Central da Inteligência Artificial",
            author="System",
            entrypoint="backend.domains.ai.orchestrator.orchestrator_service"
        ))
