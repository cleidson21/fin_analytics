from fastapi import APIRouter, Depends
from typing import List
from backend.shared.db import get_db_connection
from sqlalchemy.orm import Session
from backend.domains.ai.planning.planning_models import GoalDTO, SimulationRequestDTO, SimulationResponseDTO
from backend.domains.ai.planning.planning_service import AIPlanningService
from backend.domains.ai.planning.planning_repository import PlanningRepository
from backend.domains.ai.providers.gemini_provider import GeminiProvider

router = APIRouter(prefix="/planning", tags=["Artificial Intelligence"])

def get_planning_service():
    provider = GeminiProvider()
    repository = PlanningRepository()
    return AIPlanningService(provider, repository)

@router.get("/goals", response_model=List[GoalDTO])
def get_goals(
    db: Session = Depends(get_db_connection),
    service: AIPlanningService = Depends(get_planning_service)
):
    service.repository.ensure_tables_exist(db)
    return service.repository.get_goals(db)

@router.post("/goals", response_model=GoalDTO)
def create_goal(
    goal: GoalDTO,
    db: Session = Depends(get_db_connection),
    service: AIPlanningService = Depends(get_planning_service)
):
    service.repository.ensure_tables_exist(db)
    return service.repository.create_goal(db, goal)

@router.post("/simulate", response_model=SimulationResponseDTO)
def simulate_goal(
    request: SimulationRequestDTO,
    db: Session = Depends(get_db_connection),
    service: AIPlanningService = Depends(get_planning_service)
):
    """
    Executa a simulação atuarial da meta solicitada e evoca o Gemini 
    apenas para interpretação textual sem permitir que ele manipule os cálculos.
    """
    return service.simulate_goal(db, request)
