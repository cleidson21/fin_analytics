import logging
import time
from typing import Callable, Dict, List, Any
from backend.domains.ai.events.event_models import Event

logger = logging.getLogger(__name__)

class InternalEventBus:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InternalEventBus, cls).__new__(cls)
            cls._instance.handlers = {} # type: Dict[str, List[Callable[[Event], Any]]]
        return cls._instance

    def subscribe(self, event_type: str, handler: Callable[[Event], Any]):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        if handler not in self.handlers[event_type]:
            self.handlers[event_type].append(handler)
            name = getattr(handler, '__name__', str(handler))
            logger.info(f"Handler {name} subscribed to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Any]):
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
            name = getattr(handler, '__name__', str(handler))
            logger.info(f"Handler {name} unsubscribed from {event_type}")

    def publish(self, event: Event):
        start_time = time.perf_counter()
        
        event_handlers = self.handlers.get(event.event_type, [])
        handler_count = len(event_handlers)
        
        for handler in event_handlers:
            try:
                handler(event)
            except Exception as e:
                name = getattr(handler, '__name__', str(handler))
                logger.error(f"Error in handler {name} for event {event.event_type}: {e}", exc_info=True)
                
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            f"Event Published: event_type={event.event_type}, source={event.source}, "
            f"timestamp={event.created_at}, handler_count={handler_count}, processing_time_ms={processing_time_ms:.2f}"
        )

event_bus = InternalEventBus()
