import logging
from backend.domains.ai.events.event_bus import event_bus

logger = logging.getLogger(__name__)

class EventRegistry:
    _registered = False
    
    @classmethod
    def register_all(cls):
        if cls._registered:
            logger.info("Event handlers already registered. Skipping.")
            return
            
        logger.info("Registering all Internal Event Bus handlers...")
        
        from backend.domains.ai.events.event_router import handle_workflow_completed
        
        event_bus.subscribe("WorkflowCompleted", handle_workflow_completed)
        
        cls._registered = True
        logger.info("Internal Event Bus handlers registered successfully.")
