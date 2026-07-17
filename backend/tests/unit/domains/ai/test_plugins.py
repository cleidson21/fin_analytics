import pytest
from backend.domains.ai.plugins.plugin_models import PluginMetadata
from backend.domains.ai.plugins.plugin_registry import PluginRegistry
from backend.domains.ai.plugins.plugin_manager import PluginManager
from backend.domains.ai.plugins.internal_plugins import BaseInternalPlugin

class DummyPlugin(BaseInternalPlugin):
    def __init__(self, plugin_id="dummy-1", enabled=True):
        super().__init__(PluginMetadata(
            plugin_id=plugin_id,
            name="Dummy Plugin",
            version="1.0.0",
            description="Dummy",
            author="Test",
            entrypoint="test",
            enabled=enabled
        ))
        self.executed = False

    def execute(self):
        self.executed = True
        
    def shutdown(self):
        self.executed = False

class ErrorPlugin(BaseInternalPlugin):
    def __init__(self):
        super().__init__(PluginMetadata(
            plugin_id="error-1",
            name="Error Plugin",
            version="1.0.0",
            description="Error",
            author="Test",
            entrypoint="test"
        ))

    def execute(self):
        raise ValueError("Simulated error")

@pytest.fixture(autouse=True)
def cleanup():
    PluginRegistry.clear()
    yield
    PluginRegistry.clear()

def test_plugin_registration():
    plugin = DummyPlugin()
    PluginRegistry.register(plugin)
    assert PluginRegistry.get("dummy-1") == plugin
    assert len(PluginRegistry.list()) == 1

def test_plugin_manager_load_and_initialize():
    plugin = DummyPlugin()
    PluginManager.load_plugin(plugin)
    assert plugin.status.loaded is True
    
    PluginManager.initialize_plugin("dummy-1")
    assert plugin.status.healthy is True

def test_plugin_execution():
    plugin = DummyPlugin()
    PluginManager.load_plugin(plugin)
    PluginManager.initialize_plugin("dummy-1")
    
    PluginManager.execute_plugin("dummy-1")
    assert plugin.executed is True
    assert plugin.status.last_execution is not None

def test_plugin_execution_error():
    plugin = ErrorPlugin()
    PluginManager.load_plugin(plugin)
    PluginManager.initialize_plugin("error-1")
    
    with pytest.raises(ValueError, match="Simulated error"):
        PluginManager.execute_plugin("error-1")
        
    assert plugin.status.healthy is False
    assert len(plugin.status.errors) == 1

def test_plugin_shutdown():
    plugin = DummyPlugin()
    PluginManager.load_plugin(plugin)
    PluginManager.initialize_plugin("dummy-1")
    PluginManager.execute_plugin("dummy-1")
    
    PluginManager.shutdown_plugin("dummy-1")
    assert plugin.status.loaded is False
    assert plugin.executed is False

def test_inexistent_plugin():
    with pytest.raises(ValueError, match="Plugin not-found not found."):
        PluginManager.execute_plugin("not-found")

def test_disabled_plugin():
    plugin = DummyPlugin(plugin_id="dummy-disabled", enabled=False)
    PluginManager.load_plugin(plugin)
    
    with pytest.raises(ValueError, match="Plugin dummy-disabled is disabled."):
        PluginManager.execute_plugin("dummy-disabled")
