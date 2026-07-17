from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.domains.ai.plugins.plugin_manager import PluginManager
from backend.domains.ai.plugins.plugin_registry import PluginRegistry

router = APIRouter(prefix="/plugins", tags=["Plugins"])

@router.get("", response_model=List[Dict[str, Any]])
def list_plugins():
    """List all registered plugins."""
    plugins = PluginRegistry.list()
    return [
        {
            "metadata": plugin.metadata.model_dump(),
            "status": plugin.status.model_dump() if hasattr(plugin, 'status') else None
        }
        for plugin in plugins
    ]

@router.get("/status", response_model=Dict[str, Any])
def plugins_status():
    """Get the overall status of the plugin system."""
    plugins = PluginRegistry.list()
    total = len(plugins)
    healthy = sum(1 for p in plugins if hasattr(p, 'status') and p.status.healthy)
    
    return {
        "total_plugins": total,
        "healthy_plugins": healthy,
        "system_status": "healthy" if total == healthy else "degraded"
    }

@router.post("/{plugin_id}/execute")
def execute_plugin(plugin_id: str):
    """Execute a specific plugin manually."""
    try:
        PluginManager.execute_plugin(plugin_id)
        return {"message": f"Plugin {plugin_id} executed successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
