import unittest
from unittest.mock import MagicMock, patch
from backend.domains.ai.events.event_models import Event
from backend.domains.ai.events.event_bus import event_bus, InternalEventBus
from backend.domains.ai.events.event_registry import EventRegistry
from backend.domains.ai.events.event_router import handle_workflow_completed

class TestInternalEventBus(unittest.TestCase):
    def setUp(self):
        # Limpar handlers antes de cada teste
        event_bus.handlers = {}
        EventRegistry._registered = False

    def test_publish_and_subscribe(self):
        handler = MagicMock()
        event_bus.subscribe("TestEvent", handler)
        
        event = Event(event_type="TestEvent", source="Test")
        event_bus.publish(event)
        
        handler.assert_called_once_with(event)

    def test_unsubscribe(self):
        handler = MagicMock()
        event_bus.subscribe("TestEvent", handler)
        event_bus.unsubscribe("TestEvent", handler)
        
        event = Event(event_type="TestEvent", source="Test")
        event_bus.publish(event)
        
        handler.assert_not_called()

    def test_multiple_subscribers(self):
        handler1 = MagicMock()
        handler2 = MagicMock()
        
        event_bus.subscribe("MultiEvent", handler1)
        event_bus.subscribe("MultiEvent", handler2)
        
        event = Event(event_type="MultiEvent", source="Test")
        event_bus.publish(event)
        
        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)

    def test_unknown_event(self):
        handler = MagicMock()
        event_bus.subscribe("KnownEvent", handler)
        
        event = Event(event_type="UnknownEvent", source="Test")
        event_bus.publish(event)
        
        handler.assert_not_called()

    def test_duplicate_registration(self):
        handler = MagicMock()
        event_bus.subscribe("DupEvent", handler)
        event_bus.subscribe("DupEvent", handler)
        
        self.assertEqual(len(event_bus.handlers["DupEvent"]), 1)
        
        event = Event(event_type="DupEvent", source="Test")
        event_bus.publish(event)
        
        handler.assert_called_once_with(event)

    def test_handler_error_does_not_break_bus(self):
        handler_fail = MagicMock(side_effect=Exception("Error"))
        handler_success = MagicMock()
        
        event_bus.subscribe("ErrorEvent", handler_fail)
        event_bus.subscribe("ErrorEvent", handler_success)
        
        event = Event(event_type="ErrorEvent", source="Test")
        
        try:
            event_bus.publish(event)
        except Exception:
            self.fail("EventBus.publish() raised Exception unexpectedly!")
            
        handler_fail.assert_called_once()
        handler_success.assert_called_once()

    def test_registry_registers_workflow_completed(self):
        EventRegistry.register_all()
        self.assertTrue(EventRegistry._registered)
        
        handlers = event_bus.handlers.get("WorkflowCompleted", [])
        self.assertIn(handle_workflow_completed, handlers)
        
    @patch('backend.domains.ai.events.event_router.DashboardDeliveryService')
    @patch('backend.domains.ai.events.event_router.DashboardRepository')
    @patch('backend.domains.ai.events.event_router.Session')
    def test_dashboard_receiving_workflow_completed(self, mock_session, mock_repo, mock_svc):
        mock_instance = MagicMock()
        mock_svc.return_value = mock_instance
        
        event = Event(
            event_type="WorkflowCompleted",
            source="WorkflowEngine",
            payload={"workflow_id": "123"}
        )
        
        # O handler chama DashboardDeliveryService
        handle_workflow_completed(event)
        
        mock_instance.get_dashboard_view_model.assert_called_once()
        
if __name__ == '__main__':
    unittest.main()
