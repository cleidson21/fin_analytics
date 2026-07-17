import logging
from backend.domains.ai.events.event_models import Event
from backend.domains.ai.events.event_bus import event_bus
from backend.domains.ai.dashboard.dashboard_service import DashboardDeliveryService
from backend.domains.ai.dashboard.dashboard_repository import DashboardRepository
from sqlalchemy.orm import Session
from backend.shared.db import engine

logger = logging.getLogger(__name__)

def handle_workflow_completed(event: Event):
    """
    Quando o Workflow Engine completa sua orquestração,
    o DashboardDeliveryService é notificado para consolidar o painel.
    """
    logger.info(f"Dashboard received event: {event.event_type} from {event.source}")
    db_session = Session(engine)
    try:
        svc = DashboardDeliveryService(DashboardRepository())
        svc.get_dashboard_view_model(db_session)
        
        # Publish DashboardRefreshed
        event_bus.publish(Event(
            event_type="DashboardRefreshed",
            source="DashboardDeliveryService",
            payload={"workflow_id": event.payload.get("workflow_id")}
        ))
    except Exception as e:
        logger.error(f"Error in handle_workflow_completed: {e}", exc_info=True)
    finally:
        db_session.close()
