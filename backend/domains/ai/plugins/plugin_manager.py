import time
import logging
from typing import Any, Protocol, runtime_checkable
from datetime import datetime
from backend.domains.ai.plugins.plugin_models import PluginStatus
from backend.domains.ai.plugins.plugin_registry import PluginRegistry

logger = logging.getLogger(__name__)

@runtime_checkable
class PluginInterface(Protocol):
    def initialize(self) -> None:
        ...
        
    def execute(self) -> None:
        ...
        
    def shutdown(self) -> None:
        ...
        
    def health(self) -> bool:
        ...

class PluginManager:
    @classmethod
    def load_plugin(cls, plugin: Any) -> None:
        """Load a plugin into the registry and update its status."""
        PluginRegistry.register(plugin)
        if not hasattr(plugin, 'status'):
            plugin.status = PluginStatus()
        plugin.status.loaded = True
        logger.info(f"Loaded plugin: {plugin.metadata.name} ({plugin.metadata.plugin_id})")

    @classmethod
    def initialize_plugin(cls, plugin_id: str) -> None:
        """Initialize a specific plugin."""
        plugin = PluginRegistry.get(plugin_id)
        if not plugin:
            logger.error(f"Plugin {plugin_id} not found.")
            return

        if not isinstance(plugin, PluginInterface):
            logger.error(f"Plugin {plugin_id} does not implement PluginInterface.")
            return
            
        try:
            plugin.initialize()
            plugin.status.healthy = plugin.health()
            logger.info(f"Initialized plugin: {plugin.metadata.name}")
        except Exception as e:
            logger.error(f"Error initializing plugin {plugin_id}: {str(e)}")
            plugin.status.healthy = False
            plugin.status.errors.append(str(e))

    @classmethod
    def execute_plugin(cls, plugin_id: str) -> None:
        """Execute a specific plugin."""
        plugin = PluginRegistry.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found.")
            
        if not plugin.metadata.enabled:
            raise ValueError(f"Plugin {plugin_id} is disabled.")

        if not isinstance(plugin, PluginInterface):
            raise TypeError(f"Plugin {plugin_id} does not implement PluginInterface.")

        start_time = time.perf_counter()
        try:
            plugin.execute()
            plugin.status.healthy = True
        except Exception as e:
            plugin.status.healthy = False
            plugin.status.errors.append(str(e))
            logger.error(f"Error executing plugin {plugin_id}: {str(e)}")
            raise
        finally:
            end_time = time.perf_counter()
            plugin.status.last_execution = datetime.utcnow()
            plugin.status.execution_time_ms = int((end_time - start_time) * 1000)

    @classmethod
    def shutdown_plugin(cls, plugin_id: str) -> None:
        """Shutdown a specific plugin."""
        plugin = PluginRegistry.get(plugin_id)
        if not plugin:
            return

        if isinstance(plugin, PluginInterface):
            try:
                plugin.shutdown()
                plugin.status.loaded = False
                logger.info(f"Shutdown plugin: {plugin.metadata.name}")
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_id}: {str(e)}")
                plugin.status.errors.append(str(e))

    @classmethod
    def initialize_all(cls) -> None:
        """Initialize all enabled plugins registered in the system."""
        # For FINANALYTICS V3, the requested plugins are automatically instantiated and loaded here
        # AI Workflow, AI Dashboard, AI Orchestrator, Internal Event Bus
        
        from backend.domains.ai.plugins.internal_plugins import (
            AIWorkflowPlugin, 
            AIDashboardPlugin, 
            AIOrchestratorPlugin, 
            InternalEventBusPlugin
        )
        
        plugins = [
            AIWorkflowPlugin(),
            AIDashboardPlugin(),
            AIOrchestratorPlugin(),
            InternalEventBusPlugin()
        ]
        
        for plugin in plugins:
            cls.load_plugin(plugin)
            if plugin.metadata.enabled:
                cls.initialize_plugin(plugin.metadata.plugin_id)

    @classmethod
    def shutdown_all(cls) -> None:
        """Shutdown all registered plugins."""
        for plugin in PluginRegistry.list():
            cls.shutdown_plugin(plugin.metadata.plugin_id)
