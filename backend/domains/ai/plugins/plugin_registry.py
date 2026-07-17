from typing import Dict, List, Optional, Any
from backend.domains.ai.plugins.plugin_models import PluginMetadata

class PluginRegistry:
    _plugins: Dict[str, Any] = {}

    @classmethod
    def register(cls, plugin: Any) -> None:
        """Register a plugin instance."""
        if not hasattr(plugin, 'metadata') or not isinstance(plugin.metadata, PluginMetadata):
            raise ValueError("Plugin must have a 'metadata' attribute of type PluginMetadata")
        cls._plugins[plugin.metadata.plugin_id] = plugin

    @classmethod
    def unregister(cls, plugin_id: str) -> None:
        """Unregister a plugin by its ID."""
        if plugin_id in cls._plugins:
            del cls._plugins[plugin_id]

    @classmethod
    def get(cls, plugin_id: str) -> Optional[Any]:
        """Get a plugin by its ID."""
        return cls._plugins.get(plugin_id)

    @classmethod
    def list(cls) -> List[Any]:
        """List all registered plugins."""
        return list(cls._plugins.values())

    @classmethod
    def enabled_plugins(cls) -> List[Any]:
        """List all enabled plugins."""
        return [p for p in cls._plugins.values() if p.metadata.enabled]
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered plugins (mainly for testing)."""
        cls._plugins.clear()
