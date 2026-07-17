from fastapi import APIRouter, Depends
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.orchestrator.orchestrator_models import OrchestratorStatusDTO, UnifiedContextDTO
from backend.domains.ai.orchestrator.orchestrator_service import AIOrchestratorService
from backend.domains.ai.orchestrator.orchestrator_repository import OrchestratorRepository

router = APIRouter(prefix="/orchestrator", tags=["Artificial Intelligence"])

def get_orchestrator_service():
    repository = OrchestratorRepository()
    return AIOrchestratorService(repository)

@router.get("/status", response_model=OrchestratorStatusDTO)
def get_ai_orchestrator_status(
    db: Session = Depends(get_db_connection),
    service: AIOrchestratorService = Depends(get_orchestrator_service)
):
    """
    Retorna o Health Check global de todos os módulos de IA do sistema.
    """
    return service.get_orchestrator_status(db)

@router.get("/context", response_model=UnifiedContextDTO)
def get_ai_unified_context(
    db: Session = Depends(get_db_connection),
    service: AIOrchestratorService = Depends(get_orchestrator_service)
):
    """
    Retorna o DTO consolidado contendo toda a inteligência da plataforma.
    Este endpoint não aciona o LLM, ele apenas orquestra as leituras dos módulos.
    """
    return service.get_unified_context(db)
