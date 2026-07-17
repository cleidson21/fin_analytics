from fastapi import APIRouter, Depends
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.dashboard.dashboard_models import DashboardViewModelDTO
from backend.domains.ai.dashboard.dashboard_service import DashboardDeliveryService
from backend.domains.ai.dashboard.dashboard_repository import DashboardRepository

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def get_dashboard_service():
    repository = DashboardRepository()
    return DashboardDeliveryService(repository)

@router.get("", response_model=DashboardViewModelDTO)
def get_ai_dashboard(
    db: Session = Depends(get_db_connection),
    service: DashboardDeliveryService = Depends(get_dashboard_service)
):
    """
    Retorna a Payload consolidada do Dashboard lendo exclusivamente os 
    Read Models da Inteligência Artificial via Orchestrator.
    Não aciona LLMs, não grava dados.
    """
    return service.get_dashboard_view_model(db)
